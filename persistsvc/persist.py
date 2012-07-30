import datetime
import logging
import threading
import time

import OpenTokSDK

from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import func

from trpycore.alg.grouping import group
from trpycore.thread.util import join
from trpycore.thread.threadpool import ThreadPool
from trsvcscore.models import Chat, ChatRegistration, ChatScheduleJob, ChatSession, ChatUser

import settings

MIN_GROUP_SIZE = settings.SCHEDULER_MIN_GROUP_SIZE
MAX_GROUP_SIZE = settings.SCHEDULER_MAX_GROUP_SIZE

class ChatSchedulerThreadPool(ThreadPool):
    """Schedule chat sessions.

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
        super(ChatSchedulerThreadPool, self).__init__(num_threads)
    
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
        created = self._create_chat_schedule_job(chat_id)
        if not created:
            return
        
        try:
            self._create_chat_sessions(chat_id)
            self._end_chat_schedule_job(chat_id)
        except Exception as error:
            self.log.exception(error)
            self._abort_chat_schedule_job(chat_id)

    def _create_tokbox_session(self):
        """Create tokbox session through Tokbox API.

        Returns:
            Tokbox session object.
        """
        #Create the tokbox session
        opentok = OpenTokSDK.OpenTokSDK(
                settings.TOKBOX_API_KEY,
                settings.TOKBOX_API_SECRET, 
                settings.TOKBOX_IS_STAGING) 
        
        #IP passed to tokbox when session is created will be used to determine
        #tokbox server location for chat session. Note that tokboxchat sessions
        #never expire. But tokbox user chat tokens can be set to expire.
        session = opentok.create_session('127.0.0.1')

        return session

    def _create_chat_schedule_job(self, chat_id, session=None):
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
        self.log.info("Attempting to create chat schedule job for chat_id=%d ..." % chat_id)
        result = False
        try:
            session = session or self.create_db_session()
            job = ChatScheduleJob(chat_id=chat_id, start=func.current_timestamp())
            session.add(job)
            session.commit()
            self.log.info("Created chat schedule job for chat_id=%d" % chat_id)
            result = True
        except IntegrityError:           
            session.rollback()
            self.log.warning("Unable to create chat schedule job for chat_id=%d, job already exists." % chat_id)
        except Exception as error:
            session.rollback()
            self.log.error("Unable to create chat schedule job for chat_id=%d, %s" % (chat_id, str(error)))
            raise

        return result

    def _end_chat_schedule_job(self, chat_id, session=None):
        """End ChatScheduleJob.
        
        Mark the current job record finished, by updating the end
        field with the current timestamp.
        """
        self.log.info("Ending chat schedule job for chat_id=%d ..." % chat_id)
        session = session or self.create_db_session()
        job = session.query(ChatScheduleJob).filter(ChatScheduleJob.chat_id==chat_id).first()
        job.end = func.current_timestamp()
        session.commit()

    def _abort_chat_schedule_job(self, chat_id, session=None):
        """Abort ChatScheduleJob.

        Abort the current schedule job, by deleting the job record.
        """
        self.log.error("Aborting chat schedule job for chat_id=%d ..." % chat_id)
        session = session or self.create_db_session()
        session.query(ChatScheduleJob).filter(ChatScheduleJob.chat_id==chat_id).delete()
        session.commit()

    def _create_chat_sessions(self, chat_id, session=None):
        """Create chat sessions and associated entities.

        Given a work item (chat_id), this method will create the necessary
        chat sessions for the chat based on the existing chat registrations
        with checked_in == True.

        Additionally, it will create the necessary chat users
        and link existing registrations to their assigned chat sessions.
        """
        self.log.info("Creating chat session for chat_id=%d" % chat_id)
        try:
            session = session or self.create_db_session()
            registrations = session.query(ChatRegistration).\
                    filter(ChatRegistration.chat_id == chat_id).\
                    filter(ChatRegistration.chat_session_id == None).\
                    filter(ChatRegistration.checked_in == True).\
                    all()
            
            self.log.info("Found %d registrations for chat_id=%d" % (len(registrations), chat_id))
            
            #return coefficients for grouping n registrations
            #into groups with min / max sizes.
            #i.e. group(11, 2, 3) will return:
            #[1, 3], 1 group 2, and 3 groups of 3.
            grouping = group(len(registrations), MIN_GROUP_SIZE, MAX_GROUP_SIZE)
            if grouping is None:
                message = "Unable to determine groups for chat_id=%d" % chat_id
                self.log.error(message)
                raise RuntimeError(message)
            self.log.info("Determined grouping, %s, for chat_id=%d" % (grouping, chat_id))
            

            registration_offset = 0
            for group_index, group_size in enumerate(range(MIN_GROUP_SIZE, MAX_GROUP_SIZE+1)):
                num_groups = grouping[group_index]
                for i in range(0, num_groups):
                    tokbox_session = self._create_tokbox_session()
                    chat_session = ChatSession(
                            chat_id=chat_id,
                            token=tokbox_session.session_id,
                            participants=group_size)

                    session.add(chat_session)
                    
                    for registration_index, registration in \
                            enumerate(registrations[registration_offset:registration_offset+group_size]):
                        registration_offset += 1
                        registration.chat_session = chat_session 
                        chat_user = ChatUser(
                                chat_session=chat_session,
                                user_id=registration.user_id,
                                participant=registration_index+1)
                        session.add(chat_user)
            session.commit()
            self.log.info("Created chat sessions and users for chat_id=%d" % chat_id)
        except Exception:
            session.rollback()
            raise

class ChatScheduler(object):
    """Chat scheduler creates and delegates work items to the ChatSchedulerThreadPool.
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
        self.threadpool = ChatSchedulerThreadPool(num_threads, db_session_factory)

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
        """Start scheduler."""
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
                for chat in session.query(Chat).\
                        outerjoin(ChatScheduleJob).\
                        filter(Chat.checkin_end < func.current_timestamp()).\
                        filter(Chat.checkin_end + datetime.timedelta(hours=1) > func.current_timestamp()).\
                        filter(ChatScheduleJob.id == None): 
                    
                    #delegate chats to threadpool for processing
                    self.threadpool.put(chat.id)
                
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
        """Stop scheduler."""
        if self.running:
            self.running = False
            #acquire cv and wake up monitorThread run method.
            with self.exit:
                self.exit.notify_all()
            self.threadpool.stop()
    
    def join(self, timeout):
        """Join scheduler."""
        join([self.threadpool, self.monitorThread], timeout)
