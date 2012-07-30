import datetime
import logging
import threading
import time

from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import func

from trpycore.alg.grouping import group
from trpycore.thread.util import join
from trpycore.thread.threadpool import ThreadPool
from trsvcscore.models import Chat, ChatRegistration, ChatScheduleJob, ChatSession, ChatUser

import settings


class ChatPersisterThreadPool(ThreadPool):
    """Persist chat sessions.

    Given a work item (chat_id), scheduler will create the necessary
    chat sessions for the chat based on the existing chat registrations
    with checked_in == True.

    Additionally, the scheduler will create the necessary chat users
    and link existing registrations to their assigned chat sessions.
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
    
    def create_db_session(self):
        """Create  new sqlalchemy db session.

        Returns:
            sqlalchemy db session
        """
        return self.db_session_factory()

    def process(self, job_id):
        """Worker thread process method.

        This method will be invoked by each worker thread when
        a new work item (job_id) is put on the queue.
        """
        try:
            self._start_chat_persist_job(job_id)
            self._create_chat_entities(job_id)
            self._end_chat_persist_job(job_id)
        except Exception as error:
            self.log.exception(error)
            self._abort_chat_persist_job(job_id)


    def _start_chat_persist_job(self, job_id, session=None):
        """Start ChatPersistJob.

        Mark the current job record as started, by updating the start
        field with the current timestamp.
        """
        self.log.info("Starting chat persist job for job_id=%d ..." % job_id)
        session = session or self.create_db_session()
        job = session.query(ChatPersistJob).filter(ChatPersistJob.job_id==job_id).first()
        job.start = func.current_timestamp()
        session.commit()

    def _end_chat_persist_job(self, job_id, session=None):
        """End ChatPersistJob.
        
        Mark the current job record finished, by updating the end
        field with the current timestamp.
        """
        self.log.info("Ending chat persist job for job_id=%d ..." % job_id)
        session = session or self.create_db_session()
        job = session.query(ChatPersistJob).filter(ChatPersistJob.job_id==job_id).first()
        job.end = func.current_timestamp()
        session.commit()

    def _abort_chat_persist_job(self, job_id, session=None):
        """Abort ChatPersitJob.

        Abort the current persist job, by...
        """
        self.log.error("Aborting chat persist job for job_id=%d ..." % job_id)
        # TODO I think we should unwind any created minutes and tags and set the job owner as null

    def _create_chat_entities(self, job_id, session=None):
        """Create chat tags and chat minutes.

        Given a work item (job_id), this method will create the necessary
        chat tags and minutes for the chat based on the existing chat messages
        that were created by the chat service.
        """
        self.log.info("Persisting chat for job_id=%d" % job_id)

        try:
            session = session or self.create_db_session()

            # Retrieve the chat session id
            job = session.query(ChatPersistJob).filter(ChatPersistJob.job_id==job_id).first()
            chat_session_id = job.chat_session.id

            # Retrieve all messages with the specified chat session ID
            chat_messages = session.query(ChatMessage).\
                filter(ChatMessage.chat_session == chat_session_id).\
                all()
            self.log.info("Found %d messages for chat_session_id=%d" % (len(messages), chat_session_id))

            # Iterate through messages, filtering based upon biz rules
            chat_messages_to_persist = self._filter_chat_messages(chat_messages)

            # Create chatTags and chatMinutes entries in db
            for message in chat_messages_to_persist:
                self.log.info("Persisting messages")
                # if messageType is X, create db ojbect
                # if messageType is Y, create db object
                # Write all message to db

        except Exception:
            session.rollback()
            raise

    def _filter_chat_messages(self, chat_messages):
        """Apply business rules to filter which chat messages will be persisted.

        Given a collection of chat messages associated with a chat, this method will
        filter the messages down to only those we want to persist.
        """
        self.log.info("Filtering chat messages based upon business rules")


class ChatPersister(object):
    """Chat Persister creates and delegates work items to the ChatPersisterThreadPool.
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
        self.poll_seconds = poll_seconds #TODO remove
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
                self.log.info("ChatPersister is running")

                #Look for ChatPersistJobs with no owner.
                #This indicates a job which
                #needs to be processed.
                for job in session.query(ChatPersistJob).\
                        filter(ChatPersistJob.owner == None):

                    #delegate chats to threadpool for processing
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
