import datetime
import logging
import threading
import time

from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import func

from trchatsvc.gen.ttypes import Message
from trpycore.alg.grouping import group
from trpycore.thrift.serialization import deserialize
from trpycore.timezone import tz
from trpycore.thread.util import join
from trpycore.thread.threadpool import ThreadPool
from trsvcscore.db.models import ChatPersistJob, ChatMessage, ChatMessageFormatType

from cache import ChatMessageCache
from mapper import ChatMessageMapper
from message_handler import ChatMessageHandler
from topic_data_manager import TopicDataManager

import settings

class DuplicatePersistJobException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.__class__.__name__ + ": " + self.message


class ChatPersister(object):
    """
        Responsible for persisting all chat messages that are stored in the database.

        This class is responsible for reading all the ChatMessages
        that the Chat Service has persisted and creating new entities
        in the db according to the details of the chat message.

        Currently creates ChatMinute, ChatMarker, and ChatTag entities.
    """

    def __init__(self, db_session_factory, job_id):
        self.log = logging.getLogger(__name__)
        self.db_session_factory = db_session_factory
        self.job_id = job_id
        self.chat_session_id = None

    def create_db_session(self):
        """Create  new sqlalchemy db session.

        Returns:
            sqlalchemy db session
        """
        return self.db_session_factory()

    def persist(self):
        """ This method is responsible for persisting
            chat message data

            Only data we plan on consuming is being persisted.
        """
        try:
            self._start_chat_persist_job()

            db_session = self.create_db_session()
            self._persist_data(db_session)

            self._end_chat_persist_job()
        except DuplicatePersistJobException as warning:
            self.log.warning(warning)
            # This means that the PersistJob was claimed just before
            # this thread claimed it. Stop processing the job. There's
            # no need to abort the job since no processing of the job
            # has occurred.
        except Exception as error:
            db_session.rollback()
            self.log.exception(error)
            self._abort_chat_persist_job()

    def _start_chat_persist_job(self):
        """Start processing the chat persist job.

        Mark the ChatPersistJob record in the db as started by updating the 'start'
        field with the current timestamp.
        """
        self.log.info("Starting chat persist job with job_id=%d ..." % self.job_id)

        db_session = self.create_db_session()

        # This query.update generates the following sql:
        # UPDATE chat_persist_job SET owner='persistsvc' WHERE
        # chat_persist_job.id = 1 AND chat_persist_job.owner IS NULL
        num_rows_updated = db_session.query(ChatPersistJob).\
            filter(ChatPersistJob.id==self.job_id).\
            filter(ChatPersistJob.owner==None).\
            update({
                ChatPersistJob.owner: 'persistsvc',
                ChatPersistJob.start: tz.utcnow()
            })

        if (not num_rows_updated):
            raise DuplicatePersistJobException(message="Chat persist job with job_id=%d already claimed. Stopping processing." % self.job_id)

        db_session.commit()
        # db_session.close() TODO

    def _end_chat_persist_job(self):
        """End processing of the ChatPersistJob.

        Mark the ChatPersistJob record as finished by updating the 'end'
        field with the current time.
        """
        self.log.info("Ending chat persist job with job_id=%d ..." % self.job_id)
        db_session = self.create_db_session()
        job = db_session.query(ChatPersistJob).filter(ChatPersistJob.id==self.job_id).one()
        job.end = func.current_timestamp()
        db_session.commit()
        # db_session.close() TODO

    def _abort_chat_persist_job(self):
        """Abort the ChatPersistJob.

        Abort the current persist job. Reset the 'start' column and
        'owner' column to NULL.
        """
        self.log.error("Aborting chat persist job with job_id=%d ..." % self.job_id)
        db_session = self.create_db_session()
        job = db_session.query(ChatPersistJob).filter(ChatPersistJob.id==self.job_id).one()
        job.start = None
        job.owner = None
        db_session.commit()
        # db_session.close() TODO
        # TODO: Monitor thread is stopping after abort is called.
        # TODO: What happens if this function throws?

    def _persist_data(self, db_session):
        """Persist chat data to the db

        This method will create the necessary chat minutes, tags,
        and other entities for the chat based on the chat messages
        that were created by the chat service.
        """
        try:
            # Retrieve the chat session id
            job = db_session.query(ChatPersistJob).filter(ChatPersistJob.id==self.job_id).one()
            self.chat_session_id = job.chat_session.id

            thrift_b64_format_id = db_session.query(ChatMessageFormatType).\
                filter(ChatMessageFormatType.name=='THRIFT_BINARY_B64').\
                one().\
                id

            # Read all chat messages that were stored by the chat svc.
            # It's important that the messages be consumed in chronological
            # order so that ordering dependencies between messages can be
            # properly handled.
            # (e.g. ChatTags needing a reference to a ChatMinute)
            chat_messages = db_session.query(ChatMessage).\
                filter(ChatMessage.chat_session_id == self.chat_session_id).\
                filter(ChatMessage.format_type_id == thrift_b64_format_id).\
                order_by(ChatMessage.timestamp).\
                all()

            self.log.info("Persist job_id=%d found %d messages to process for chat_session_id=%d" %
                          (self.job_id, len(chat_messages), self.chat_session_id))

            # Deserialize all chat message data
            deserialized_chat_msgs = []
            for chat_message in chat_messages:
                deserialized_msg = Message()
                deserialize(deserialized_msg, chat_message.data)
                deserialized_chat_msgs.append(deserialized_msg)

            # Generate topics collection for this chat
            topics_manager = TopicDataManager()
            topic_id = topics_manager.get_root_topic_id(db_session, self.chat_session_id)
            topics_collection = topics_manager.get_collection(db_session, topic_id)

            # Process the deserialized chat messages
            handler = ChatMessageHandler(self.chat_session_id, topics_collection)
            for message in deserialized_chat_msgs:
                if message.minuteCreateMessage is not None or message.minuteUpdateMessage is not None or message.tagCreateMessage is not None or message.tagDeleteMessage is not None:
                    ret = handler.process(message)
                    if ret is not None:
                        for addModel, model in ret:
                            if addModel:
                                db_session.add(model)
                            else:
                                db_session.expunge(model)

            # commit all db changes
            db_session.commit()
            # db_session.close() TODO

        except Exception:
            db_session.rollback()
            raise

class ChatPersisterThreadPool(ThreadPool):
    """Thread pool used to process chat persist jobs.

    Given a work item (job_id), this class will process the
    job and delegate the work to persist the associated chat data to the db.
    """
    def __init__(self, num_threads, db_session_factory):
        """Constructor.

        Arguments:
            num_threads: number of worker threads
            db_session_factory: callable returning new sqlalchemy
                db session.
        """
        self.log = logging.getLogger(__name__)
        self.db_session_factory = db_session_factory
        super(ChatPersisterThreadPool, self).__init__(num_threads)

    def process(self, job_id):
        """Worker thread process method.

        This method will be invoked by each worker thread when
        a new work item (job_id) is put on the queue.
        """

        persister = ChatPersister(self.db_session_factory, job_id)
        persister.persist()

class ChatPersistJobMonitor(object):
    """
    ChatPersistJobMonitor monitors for new chat persist jobs, and delegates
     work items to the ChatPersisterThreadPool.
    """
    def __init__(self, num_threads, db_session_factory, poll_seconds=60):
        """Constructor.

        Arguments:
            num_threads: number of worker threads
            db_session_factory: callable returning a new sqlalchemy db session
            poll_seconds: number of seconds between db queries to detect
                chat requiring scheduling.
        """
        self.log = logging.getLogger(__name__)
        self.num_threads = num_threads
        self.db_session_factory = db_session_factory
        self.poll_seconds = poll_seconds
        self.monitorThread = threading.Thread(target=self.run)
        self.threadpool = ChatPersisterThreadPool(num_threads, db_session_factory)

        #conditional variable allowing speedy wakeup on exit.
        self.exit = threading.Condition()

        self.running = False
    
    def create_db_session(self):
        """Create new sqlalchemy db session.

        Returns:
            sqlachemy db session.
        """
        return self.db_session_factory()

    def start(self):
        """Start persister."""
        if not self.running:
           self.running = True
           self.threadpool.start()
           self.monitorThread.start()
    
    def run(self):
        """Monitor thread run method."""
        session = self.create_db_session()

        while self.running:
            try:
                self.log.info("ChatPersistJobMonitor is checking for new jobs to process...")

                #Look for ChatPersistJobs with no owner.
                #This indicates a job which
                #needs to be processed.
                for job in session.query(ChatPersistJob).\
                        filter(ChatPersistJob.owner == None):

                    #delegate jobs to threadpool for processing
                    self.threadpool.put(job.id)

                #commit is required so changes to db will be
                #reflected (MVCC).
                session.commit()

            except Exception as error:
                session.rollback()
                self.log.exception(error)
            
            #Acquire exit conditional variable
            #and call wait on this to sleep the
            #necessary time between db checks.
            #waiting on a cv, allows the wait to be
            #interuppted when stop() is called.
            with self.exit:
                end = time.time() + self.poll_seconds
                #wait in loop, rechecking condition,
                #to combate spurious wakeups.
                while self.running and (time.time() < end):
                    remaining_wait = end - time.time()
                    self.exit.wait(remaining_wait)

    def stop(self):
        """Stop persister."""
        if self.running:
            self.running = False
            #acquire cv and wake up monitorThread run method.
            with self.exit:
                self.exit.notify_all()
            self.threadpool.stop()
    
    def join(self, timeout):
        """Join persister."""
        join([self.threadpool, self.monitorThread], timeout)
