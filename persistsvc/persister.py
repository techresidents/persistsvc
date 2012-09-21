import datetime
import logging

from sqlalchemy.sql import func

from trchatsvc.gen.ttypes import Message
from trpycore.thrift.serialization import deserialize
from trpycore.timezone import tz
from trsvcscore.db.models import ChatPersistJob, ChatMessage, ChatMessageFormatType, ChatArchiveJob

from message_handler import ChatMessageHandler
from persistsvc_exceptions import DuplicatePersistJobException
from topic_data_manager import TopicDataManager



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
            chat message data.

            Only data we plan on consuming is currently
            being persisted.
        """
        try:
            self._start_chat_persist_job()
            self._persist_data()
            self._create_chat_archive_job()
            self._end_chat_persist_job()

        except DuplicatePersistJobException:
            self.log.warning("Chat persist job with job_id=%d already claimed. Stopping processing." % self.job_id)
            # This means that the PersistJob was claimed just before
            # this thread claimed it. Stop processing the job. There's
            # no need to abort the job since no processing of the job
            # has occurred.

        except Exception as e:
            self.log.exception(e)
            self._abort_chat_persist_job()


    def _start_chat_persist_job(self):
        """Start processing the chat persist job.

        Mark the ChatPersistJob record in the db as started by updating the 'start'
        field with the current timestamp.
        """
        self.log.info("Starting chat persist job with job_id=%d ..." % self.job_id)

        try:
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

            if not num_rows_updated:
                raise DuplicatePersistJobException()

            db_session.commit()

        except DuplicatePersistJobException as e:
            # No data was modified in the db so no need to rollback.
            raise e
        except Exception as e:
            self.log.exception(e)
            db_session.rollback()
            raise e
        finally:
            db_session.close()

    def _end_chat_persist_job(self):
        """End processing of the ChatPersistJob.

        Mark the ChatPersistJob record as finished by updating the 'end'
        field with the current time.
        """
        self.log.info("Ending chat persist job with job_id=%d ..." % self.job_id)

        try:
            db_session = self.create_db_session()
            job = db_session.query(ChatPersistJob).filter(ChatPersistJob.id==self.job_id).one()
            job.end = func.current_timestamp()
            job.successful = True
            db_session.commit()
        except Exception as e:
            self.log.exception(e)
            db_session.rollback()
            raise e
        finally:
            db_session.close()

    def _abort_chat_persist_job(self):
        """Abort the ChatPersistJob.

        Abort the current persist job. Reset the 'start' column and
        'owner' column to NULL.
        """

        self.log.error("Aborting chat persist job with job_id=%d ..." % self.job_id)

        try:
            db_session = self.create_db_session()
            job = db_session.query(ChatPersistJob).filter(ChatPersistJob.id==self.job_id).one()
            job.successful = False
            db_session.commit()
        except Exception as e:
            self.log.error(e)
            db_session.rollback()
        finally:
            db_session.close()

    def _persist_data(self):
        """Persist chat data to the db

        This method will create the necessary chat minutes, tags,
        and other entities for the chat based on the chat messages
        that were created by the chat service.
        """
        try:
            db_session = self.create_db_session()

            # Retrieve the chat session id
            job = db_session.query(ChatPersistJob).filter(ChatPersistJob.id==self.job_id).one()
            self.chat_session_id = job.chat_session.id

            # Specify the format of the msg data
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
                handler.process(message)

            # Persist the generated models
            models_to_persist = handler.finalize()
            for model in models_to_persist:
                db_session.add(model)

            # commit all db changes
            db_session.commit()

        except Exception as e:
            self.log.exception(e)
            db_session.rollback()
            raise e
        finally:
            db_session.close()
    
    def _create_chat_archive_job(self):
        try:
            db_session = self.create_db_session()

            #wait 5 minutes before we start the archive job
            #since it takes Tokbox time a few minutes.
            not_before = func.current_timestamp() \
                    + datetime.timedelta(minutes=5)
            job = ChatArchiveJob(
                    chat_session_id=self.chat_session_id,
                    created=func.current_timestamp(),
                    not_before=not_before,
                    retries_remaining=3)
            db_session.add(job)
            db_session.commit()
        except Exception as e:
            self.log.exception(e)
            db_session.rollback()
        finally:
            if db_session:
                db_session.close()
