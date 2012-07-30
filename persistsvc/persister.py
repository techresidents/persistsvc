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

    def process(self, chat_id):
        """Worker thread process method.

        This method will be invoked by each worker thread when
        a new work item (chat_id) is put on the queue.
        """
        created = self._create_chat_persist_job(chat_id)
        if not created:
            return
        
        try:
            self._create_chat_sessions(chat_id)
            self._end_chat_persist_job(chat_id)
        except Exception as error:
            self.log.exception(error)
            self._abort_chat_persist_job(chat_id)


    def _create_chat_persist_job(self, chat_id, session=None):
        """Create ChatScheduleJob db record.

        In order to coordinate across threads, and other instances
        of this service on other machines, the ChatScheduleJob
        database table is used. When a thread detects a chat
        with a closed check_in, and no corresponding ChatScheduleJob
        record, it will attempt to create one.

        The thread which successfully creates the job record is
        responsible for processing the item, and must delete
        the record on exception.

        Returns:
            True if job created, False otherwise.
        """
        self.log.info("Attempting to create chat persist job for chat_id=%d ..." % chat_id)
        result = False
        try:
            self.log.info("Created chat persist job for chat_id=%d" % chat_id)
            result = True
        except IntegrityError:
            self.log.warning("Unable to create chat persist job for chat_id=%d, job already exists." % chat_id)
        except Exception as error:
            self.log.error("Unable to create chat persist job for chat_id=%d, %s" % (chat_id, str(error)))
            raise

        return result

    def _end_chat_persist_job(self, chat_id, session=None):
        """End ChatScheduleJob.
        
        Mark the current job record finished, by updating the end
        field with the current timestamp.
        """
        self.log.info("Ending chat persist job for chat_id=%d ..." % chat_id)

    def _abort_chat_persist_job(self, chat_id, session=None):
        """Abort ChatScheduleJob.

        Abort the current schedule job, by deleting the job record.
        """
        self.log.error("Aborting chat persist job for chat_id=%d ..." % chat_id)

    def _create_chat_sessions(self, chat_id, session=None):
        """Create chat sessions and associated entities.

        Given a work item (chat_id), this method will create the necessary
        chat sessions for the chat based on the existing chat registrations
        with checked_in == True.

        Additionally, it will create the necessary chat users
        and link existing registrations to their assigned chat sessions.
        """
        self.log.info("Persisting chat for chat_id=%d" % chat_id)

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
                #Look for chats with closed check_in and no
                #existings ChatScheduleJob record.
                #This combination indicates a chat which
                #needs to be processed.
                self.log.info("ChatPersister is running")

            except Exception as error:
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
