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
        job = session.query(ChatPersistJob).filter(ChatPersistJob.id==job_id).first()
        job.start = func.current_timestamp()
        job.owner = 'persistsvc' #TODO what do we want to name this?
        session.commit()

    def _end_chat_persist_job(self, job_id, session=None):
        """End ChatPersistJob.
        
        Mark the current job record finished, by updating the end
        field with the current timestamp.
        """
        self.log.info("Ending chat persist job for job_id=%d ..." % job_id)
        session = session or self.create_db_session()
        job = session.query(ChatPersistJob).filter(ChatPersistJob.id==job_id).first()
        job.end = func.current_timestamp()
        session.commit()

    def _abort_chat_persist_job(self, job_id, session=None):
        """Abort ChatPersitJob.

        Abort the current persist job, by...
        """
        self.log.error("Aborting chat persist job for job_id=%d ..." % job_id)
        # TODO How do weant to handle aborting?
        # Need to unwind who owns the job and who started the job.


    def _create_chat_entities(self, job_id, session=None):
        """Create chat tags and chat minutes.

        Given a work item (job_id), this method will create the necessary
        chat tags and minutes for the chat based on the existing chat messages
        that were created by the chat service.
        """
        self.log.info("Persisting chat for job_id=%d" % job_id)

        # TODO Need to be sure to handle time zones properly.  Need to make
        # certain that Django and the service layer don't conflict in how
        # timestamps and other time data is stored in the db.

        try:
            db_session = session or self.create_db_session()

            # Retrieve the chat session id
            job = session.query(ChatPersistJob).filter(ChatPersistJob.id==job_id).first()
            chat_session_id = job.chat_session.id

            # Find all chat minute messages and store them in the db
            self._persist_chat_minutes(db_session, chat_session_id)

            # Find all speaking marker messages and store them in the db
            self._persist_chat_speaking_markers(db_session, chat_session_id)

            # Find all tag messages and store them in the db
            self._persist_chat_tags(db_session, chat_session_id)

        except Exception:
            session.rollback()
            raise

    def _persist_chat_minutes(self, db_session, chat_session_id):
        """ Read all chat messages, pull out the chat minute messages,
            and store them in the db.
        """

        # Retrieve all Minute messages
        chat_minute_messages = db_session.query(ChatMessage).\
            filter(ChatMessage.chat_session == chat_session_id).\
            filter(ChatMessage.type == 'minuteUpdate').\
            all()
            #order by timestamp
        self.log.info("Found %d minute messages for chat_session_id=%d" % (len(chat_minute_messages), chat_session_id))

        #TODO need to check for duplicate chat minute messages
        #_filter_chat_minutes

        # Create chatMinutes entries in db
        # for message in chat_minute_messages:
            # deserialize data blob of message
            # Write Minute to db

    def _persist_chat_speaking_markers(self, db_session, chat_session_id):
        """ Read all chat messages, find the speaking marker messages,
            and store them in the db.
        """
        # Retrieve all speaking marker messages
        chat_marker_messages = db_session.query(ChatMessage).\
            filter(ChatMessage.chat_session == chat_session_id).\
            filter(ChatMessage.type == 'createMarker').\
            all()
            #order by timestamp
        self.log.info("Found %d marker messages for chat_session_id=%d" % (len(chat_marker_messages), chat_session_id))

        # Deserialize actual chat message data
        # Pull out only the speaking markers
        # Apply biz rules / validation to remove any unneeded markers
        # Persist

    def _persist_chat_tags(self, db_session, chat_session_id):
        """ Read all chat messages, find tag messages,
            and store them in the db.
        """
        # Retrieve all tag messages
        chat_tag_messages = db_session.query(ChatMessage).\
            filter(ChatMessage.chat_session == chat_session_id).\
            filter(ChatMessage.type == 'createTag').\
            all()
            #order by timestamp
        self.log.info("Found %d marker messages for chat_session_id=%d" % (len(chat_marker_messages), chat_session_id))

        # Deserialize actual chat message data
        # Pull out only the speaking markers
        # Apply biz rules / validation to remove any unneeded markers
        # Persist

        # Iterate through messages, filtering based using biz rules
        filtered_chat_tag_messages = self._filter_chat_tags(chat_tag_messages, chat_minute_messages)

        # Create chatTags entries in db
        for message in filtered_chat_tag_messages:
            self.log.info("Persisting tag messages")
            # deserialize data blob of message
            # Write Tag to db


    def _filter_chat_tags(self, chat_tag_messages, chat_minute_messages):
        """Apply business rules to filter down which chat messages will be persisted.

        Given a collection of chat messages associated with a chat, this method will
        filter the messages down to only those we want to persist.

        Removes duplicate tags that occur within the same chat minute.
        Removes tags that were added and then deleted within the same chat minute.
        """
        for message in chat_tag_messages:
            self.log.info("Filtering chat messages based upon business rules")

        return chat_messages




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
