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
    ChatMinute

import settings

class DuplicatePersistJobException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.__class__.__name__ + ": " + self.message

class ChatPersisterThreadPool(ThreadPool):
    """Persist chat sessions.

    Given a work item (job_id), this class will process the
    job and persist the associated chat data to the db.
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
        except DuplicatePersistJobException as warning:
            self.log.warning(warning)
            # This means that the PersistJob was claimed just before
            # this thread claimed it. Stop processing the job. There's
            # no need to abort the job since no processing of the job
            # has occurred.
        except Exception as error:
            self.log.exception(error)
            self._abort_chat_persist_job(job_id)


    def _start_chat_persist_job(self, job_id, session=None):
        """Start ChatPersistJob.

        Mark the current job record as started, by updating the start
        field with the current timestamp.
        """

        self.log.info("Starting chat persist job with job_id=%d ..." % job_id)

        session = session or self.create_db_session()
        # This query.update generates the following sql:
        # UPDATE chat_persist_job SET owner='persistsvc' WHERE
        # chat_persist_job.id = 1 AND chat_persist_job.owner IS NULL
        num_rows_updated = session.query(ChatPersistJob).\
            filter(ChatPersistJob.id==job_id).\
            filter(ChatPersistJob.owner==None).\
            update({
                ChatPersistJob.owner: 'persistsvc',
                ChatPersistJob.start: tz.utcnow()
            })

        if (not num_rows_updated):
            raise DuplicatePersistJobException(message="Chat persist job with job_id=%d already claimed. Stopping processing." % job_id)

        session.commit()

    def _end_chat_persist_job(self, job_id, session=None):
        """End ChatPersistJob.
        
        Mark the current job as finished by updating the end
        field with the current time.
        """
        self.log.info("Ending chat persist job with job_id=%d ..." % job_id)
        session = session or self.create_db_session()
        job = session.query(ChatPersistJob).filter(ChatPersistJob.id==job_id).one()
        job.end = func.current_timestamp()
        session.commit()

    def _abort_chat_persist_job(self, job_id, session=None):
        """Abort ChatPersitJob.

        Abort the current persist job. Reset the start column and
        owner columns to NULL.
        """
        self.log.error("Aborting chat persist job with job_id=%d ..." % job_id)
        session = session or self.create_db_session()
        job = session.query(ChatPersistJob).filter(ChatPersistJob.id==job_id).one()
        job.start = None
        job.owner = None
        session.commit()

    def _create_chat_entities(self, job_id, session=None):
        """Create chat tags and chat minutes.

        Given a work item (job_id), this method will create the necessary
        chat tags and minutes for the chat based on the existing chat messages
        that were created by the chat service.
        """
        try:
            self.log.info("Starting processing of persist job with job_id=%d" % job_id)

            db_session = session or self.create_db_session()

            # Retrieve the chat session id
            job = db_session.query(ChatPersistJob).filter(ChatPersistJob.id==job_id).one()
            chat_session_id = job.chat_session.id

            # Find all chat minute messages and store them in the db
            self._persist_chat_minutes(db_session, chat_session_id)

            # Find all speaking marker messages and store them in the db
            self._persist_chat_speaking_markers(db_session, chat_session_id)

            # Find all tag messages and store them in the db
            # self._persist_chat_tags(db_session, chat_session_id)

            # commit all db changes
            db_session.commit()

        except Exception:
            db_session.rollback()
            raise

    def _persist_chat_minutes(self, db_session, chat_session_id):
        """ Read all chat messages, pull out the chat minute messages,
            and store them in the db.
        """

        # Retrieve all Minute messages
        message_type = db_session.query(ChatMessageType).filter(ChatMessageType.name=='MINUTE_UPDATE').one()
        chat_minute_messages = db_session.query(ChatMessage).\
            filter(ChatMessage.chat_session_id == chat_session_id).\
            filter(ChatMessage.type_id == message_type.id).\
            order_by(ChatMessage.timestamp).\
            all()

        self.log.info("Found %d messages of type 'Minute' for chat_session_id=%d" % (len(chat_minute_messages), chat_session_id))

        # Messages are guaranteed to be unique due to the message_id attribute that each
        # message possesses.  This means we can avoid a duplicate message check here.

        # Create chat minute objects from chat messages
        for message in chat_minute_messages:
            # deserialize data blob of message
            minute_start = datetime.datetime.now() # from data blob
            minute_end = datetime.datetime.now() # from data blob
            chat_minute = ChatMinute(
                chat_session_id=chat_session_id,
                start=minute_start,
                end=minute_end)
            db_session.add(chat_minute)

    def _persist_chat_speaking_markers(self, db_session, chat_session_id):
        """ Read all chat messages, find the speaking marker messages,
            and store them in the db.
        """

        # Retrieve all speaking marker messages
        message_type = db_session.query(ChatMessageType).\
            filter(ChatMessageType.name=='MARKER_CREATE').\
            one()
        chat_marker_messages = db_session.query(ChatMessage).\
            filter(ChatMessage.chat_session_id == chat_session_id).\
            filter(ChatMessage.type_id == message_type.id).\
            order_by(ChatMessage.timestamp).\
            all()

        self.log.info("Found %d message of type 'Marker' for chat_session_id=%d" % (len(chat_marker_messages), chat_session_id))

        # Create chat marker objects from chat messages
        for message in chat_marker_messages:
            # deserialize data blob of message
            # whittle down markers to only chat_speaking markers
            # Apply biz rules / validation to remove any unneeded markers

            # Pull out needed chat message data from data blob
            user = 'userID' # from data blob
            speaking_start = datetime.datetime.now() # from data blob
            speaking_end = datetime.datetime.now() # from data blob

            # Determine which chat minute the marker message occurred within
            # TODO need to understand semantics of db_session as to how this query will work
            chat_minute = db_session.query(ChatMinute).\
                filter(ChatMinute.start<= speaking_start).\
                filter(ChatMinute.end>=speaking_end).\
                one()

            # Create ChatSpeakingMarker object and add to db
            chat_speaking_marker = ChatSpeaking(
                user_id=user,
                chat_minute_id=chat_minute.id,
                start=speaking_start,
                end=speaking_end)
            db_session.add(chat_speaking_marker)

    def _persist_chat_tags(self, db_session, chat_session_id):
        """ Read all chat messages, find tag messages,
            and store them in the db.
        """
        # Retrieve all chat tag messages
        message_type = db_session.query(ChatMessageType).filter(ChatMessageType.name=='TAG_CREATE').one()
        chat_tag_messages = db_session.query(ChatMessage).\
            filter(ChatMessage.chat_session == chat_session_id).\
            filter(ChatMessage.type == message_type.id).\
            order_by(ChatMessage.timestamp).\
            all()

        self.log.info("Found %d messages of type 'Tag' for chat_session_id=%d" % (len(chat_tag_messages), chat_session_id))

        # Iterate through messages, filtering using biz rules
        filtered_chat_tag_messages = self._filter_chat_tags(chat_tag_messages, chat_minute_messages)

        # Create chatTags entries in db
        for message in filtered_chat_tag_messages:
            self.log.info("Persisting tag messages")

            # Pull out needed chat message data from data blob
            user = 'userID' # from data blob
            name = 'name' # from data blob
            timestamp = 'time of message' # from data blob

            # Determine if this tag exists in our inventory of tags
            tag_ref = db_session.query(ChatTag).\
                filter(ChatTag.name== name)

            # Determine which chat minute the marker message occurred within
            # TODO need to understand semantics of db_session as to how this query will work
            chat_minute = db_session.query(ChatMinute).\
                filter(ChatMinute.start<= timestamp).\
                filter(ChatMinute.end>=timestamp).\
                one()

            # Create ChatSpeakingMarker object and add to db
            chat_tag = ChatTag(
                user_id=user,
                chat_minute_id=chat_minute.id,
                tag=tag_ref.id,
                name=name)
            db_session.add(chat_tag)



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
                self.log.info("ChatPersister is checking for new jobs to process...")

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
