import datetime
import logging
import threading
import time

from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import func

from trpycore.alg.grouping import group
from trpycore.timezone import tz
from trpycore.thread.util import join
from trpycore.thread.threadpool import ThreadPool
from trsvcscore.models import Chat, ChatRegistration, \
    ChatScheduleJob, ChatSession, ChatUser,\
    ChatPersistJob, ChatMessage, ChatMessageType, \
    ChatMinute, ChatTag

from cache import ChatMessageCache
from mapper import ChatMessageMapper
import settings

class DuplicatePersistJobException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.__class__.__name__ + ": " + self.message


class ChatPersister(object):
    """
        Responsible for persisting all chat messages that we
        are interested in storing in the database.

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
        self.chat_message_cache = None

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
            self._persist_chat_data(db_session)

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

        Mark the ChatPersistJob record in the db as started by updating the start
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

    def _end_chat_persist_job(self):
        """End processing of the ChatPersistJob.

        Mark the ChatPersistJob record as finished by updating the end
        field with the current time.
        """
        self.log.info("Ending chat persist job with job_id=%d ..." % self.job_id)
        db_session = self.create_db_session()
        job = db_session.query(ChatPersistJob).filter(ChatPersistJob.id==self.job_id).one()
        job.end = func.current_timestamp()
        db_session.commit()

    def _abort_chat_persist_job(self, db_session):
        """Abort the ChatPersistJob.

        Abort the current persist job. Reset the start column and
        owner columns to NULL.
        """
        self.log.error("Aborting chat persist job with job_id=%d ..." % self.job_id)
        db_session = self.create_db_session()
        job = db_session.query(ChatPersistJob).filter(ChatPersistJob.id==self.job_id).one()
        job.start = None
        job.owner = None
        db_session.commit()

    def _persist_chat_data(self, db_session):
        """Create chat tags and chat minutes.

        This method will create the necessary chat tags and
        minutes for the chat based on the existing chat messages
        that were created by the chat service.
        """
        try:
            self.log.info("Starting processing of persist job with job_id=%d" % self.job_id)

            # Retrieve the chat session id
            job = db_session.query(ChatPersistJob).filter(ChatPersistJob.id==self.job_id).one()
            self.chat_session_id = job.chat_session.id

            # Cache all chat messages
            self._cache_chat_messages(db_session)

            # Find all chat minute messages and store them in the db
            # This data has to be processed first so that we can assign other data
            # to its associated chat minute.
            #self._persist_chat_minutes(db_session)

            # Find all speaking marker messages and store them in the db
            # self._persist_chat_speaking_markers(chat_session_id)

            # Find all tag messages and store them in the db
            # self._persist_chat_tags(db_session, chat_session_id)

            # commit all db changes
            db_session.commit()

        except Exception:
            db_session.rollback()
            raise

    def _cache_chat_messages(self, db_session):
        """
            Cache chat messages.

            Private method to cache chat messages so that the chat
            persist service can access this data without having to
            hit the database.
        """

        # Set message type IDs within cache so that the
        # cache can sort messages by type
        chat_marker_type = db_session.query(ChatMessageType).filter(ChatMessageType.name=='MARKER_CREATE').one()
        chat_minute_type = db_session.query(ChatMessageType).filter(ChatMessageType.name=='MINUTE_UPDATE').one()
        chat_tag_type = db_session.query(ChatMessageType).filter(ChatMessageType.name=='TAG_CREATE').one()
        self.chat_message_cache = ChatMessageCache(
            chat_marker_type.id,
            chat_minute_type.id,
            chat_tag_type.id
        )

        # Add all chat messages to cache
        chat_messages = db_session.query(ChatMessage).\
            filter(ChatMessage.chat_session_id == self.chat_session_id).\
            order_by(ChatMessage.timestamp).\
            all()

        for message in chat_messages:
            self.chat_message_cache.add(message)

    def _persist_chat_minutes(self, db_session):
        """
            Creates ChatMinute entries in the db

            Read all chat messages, pull out the chat minute messages,
            and store them in the db.
        """

        # Retrieve all Minute messages
        chat_minute_messages = self.chat_message_cache.get_chat_minutes()
        self.log.info("Found %d messages of type 'Minute' for chat_session_id=%d" %
                      (len(chat_minute_messages),
                       self.chat_session_id))

        # Create chat minute objects from chat messages
        chat_id_map = {}
        for message in chat_minute_messages:
            chat_minute = ChatMessageMapper.chatMessage_to_ChatMinute(message)
            chat_id_map[message] = chat_minute
            db_session.add(chat_minute)

        # Explicit flush so that we can reference chat_minute.id
        db_session.flush()

    def _persist_chat_speaking_markers(self, db_session):
        """ Read all chat messages, find the speaking marker messages,
            and store them in the db.
        """

        #TODO this is not filtering out speaking markers yet

        # Retrieve all speaking marker messages
        chat_marker_messages = self.chat_message_cache.get_chat_markers()
        self.log.info("Found %d message of type 'Marker' for chat_session_id=%d" %
                      (len(chat_marker_messages),
                       self.chat_session_id))

        # Create chat marker objects from chat messages
        for message in chat_marker_messages:
            chat_speaking_marker = ChatMessageMapper.chatMessage_to_ChatSpeakingMarker(
                message,
                self.chat_message_cache.get_chat_minutes())
            db_session.add(chat_speaking_marker)

    def _persist_chat_tags(self, db_session):
        """ Read all chat messages, find tag messages,
            and store them in the db.
        """
        # Retrieve all chat tag messages
        chat_tag_messages = self.chat_message_cache.get_chat_tags()
        self.log.info("Found %d messages of type 'Tag' for chat_session_id=%d" % (len(chat_tag_messages), self.chat_session_id))

        # Create chatTags entries in db
        for message in filtered_chat_tag_messages:
            chat_tag = ChatMessageMapper.chatMessage_to_ChatTag(message)
            db_session.add(chat_tag)

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
