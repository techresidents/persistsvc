
import logging
import threading
import time

from trpycore.thread.util import join
from trpycore.thread.threadpool import ThreadPool
from trsvcscore.db.models import ChatPersistJob

from persister import ChatPersister



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

                # Look for ChatPersistJobs with no owner and no start time.
                # This indicates a job which needs to be processed.
                for job in session.query(ChatPersistJob).\
                    filter(ChatPersistJob.owner == None).\
                    filter(ChatPersistJob.start == None):

                    # delegate jobs to threadpool for processing
                    self.threadpool.put(job.id)

                # commit is required so changes to db will be
                # reflected (MVCC).
                session.commit()

            except Exception as error:
                session.rollback()
                self.log.exception(error)

            finally:
                session.close()

            # Acquire exit conditional variable
            # and call wait on this to sleep the
            # necessary time between db checks.
            # Waiting on a conditional variable,
            # allows the wait to be interrupted
            # when stop() is called.
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
            #acquire conditional variable and wake up monitorThread run method.
            with self.exit:
                self.exit.notify_all()
            self.threadpool.stop()

    def join(self, timeout):
        """Join persister."""
        join([self.threadpool, self.monitorThread], timeout)

