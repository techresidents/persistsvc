import datetime
import logging
import os
import sys
import time
import unittest

SERVICE_NAME = "persistsvc"
#Add SERVICE_ROOT to python path, for imports.
SERVICE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../", SERVICE_NAME))
sys.path.insert(0, SERVICE_ROOT)

from trpycore.timezone import tz
from trsvcscore.db.models import Chat, ChatPersistJob, ChatSession, \
    ChatArchiveJob, ChatMessage, ChatMinute, ChatSpeakingMarker, \
    ChatTag, ChatHighlightSession, ChatUser, User, Topic

from chat_test_data import ChatTestDataBuilder
from testbase import IntegrationTestCase

import settings



class ChatPersisterTest(IntegrationTestCase):
    """
        Test the persist service's ChatPersister object which is responsible for
        starting, processing, and ending a persist job.

        Since this object does not take any input params or output any data,
        we must prime the db so that a test job is processed. All data that
        is written to the db for this test is cleaned up in tearDown().
    """

    @classmethod
    def setUpClass(cls):
        print '################################################'
        print 'Invoking setUpClass'
        print '################################################'
        IntegrationTestCase.setUpClass()

    @classmethod
    def tearDownClass(cls):
        print '################################################'
        print 'Invoking tearDownClass'
        print '################################################'
        IntegrationTestCase.tearDownClass()

    def setUp(self):
        print '################################################'
        print 'Invoking setUp'
        print '################################################'

        # Need to create the data objs that persist job requires
        #   1) Need to write ChatPersistJobs
        #   2) Need to write ChatMessages


        # Generate chat persist job data
        self.test_user_id = 1

        # We need to match the topic structure of the test chat data
        # that will be generated:
        #   Root Topic
        #       --- Subtopic1
        self.root_topic = Topic(
            parent_id=None,
            rank=0,
            title="PersisterTestChat",
            description="Chat topic used to test the persist service",
            duration=60, # secs
            public=True,
            active=True,
            recommended_participants=1,
            user_id=self.test_user_id,
            type_id=1
        )
        self.topic1 = Topic(
            rank=1,
            title="subtopic1",
            description="subtopic1 description",
            duration=60, #secs
            public=True,
            active=True,
            recommended_participants=1,
            user_id=self.test_user_id,
            type_id=1
        )
        self.root_topic.children.append(self.topic1)

        self.chat = Chat(
            type_id=1,
            topic=self.root_topic,
            start=tz.utcnow(),
            end=tz.utcnow()+datetime.timedelta(minutes=5))

        # We can have as many chat_sessions and jobs as needed
        # For now, doing 1 chat session and 1 persist job.
        self.chat_session_token = 'persister_test_dummy_token'

        self.chat_session = ChatSession(
            chat=self.chat,
            token=self.chat_session_token,
            participants=1,
        )

        self.chat_user = ChatUser(
            chat_session=self.chat_session,
            user_id=self.test_user_id,
            participant=1
        )

        self.chat_persist_job = ChatPersistJob(
            chat_session=self.chat_session,
            created=tz.utcnow()
        )

        try:
            # Write data to db so we can test the persist svc

            # Write ChatPersistJob data to the db
            db_session = self.service.handler.get_database_session()
            db_session.add(self.chat_user)

            # Before writing chat session to db, we need
            # to add a reference to the test user. This field
            # is required for the svc to create ChatHighlightSessions.
            user = db_session.query(User).\
                filter_by(id=self.test_user_id).\
                one()
            self.chat_session.users.append(user)

            db_session.add(self.chat_session)
            db_session.add(self.chat)
            db_session.add(self.root_topic)
            db_session.add(self.chat_persist_job)
            db_session.commit()

            # Generate chat message data
            # Note the commit() above is required since we need
            # real IDs to build and persist ChatMessages.
            builder = ChatTestDataBuilder()
            chat_data = builder.build(
                root_topic_id=self.root_topic.id,
                topic1_id=self.topic1.id,
                chat_session_id=self.chat_session.id,
                chat_session_token=self.chat_session_token,
                user_id=self.test_user_id
            )

            # Write ChatMessages to the db for consumption by the persist svc
            self.chat_messages = chat_data.serialized_message_list
            for chat_message in self.chat_messages:
                db_session.add(chat_message)
            db_session.commit()

        except Exception as e:
            logging.exception(e)
            if db_session:
                db_session.rollback()
        finally:
            if db_session:
                db_session.close()

    def tearDown(self):
        print '################################################'
        print 'Invoking tearDown'
        print '################################################'
        try:
            # Remove chat data from db
            db_session = self.service.handler.get_database_session()

            # Delete all data generated and inserted into the db
            # by the persist service
            chat_session = db_session.query(ChatSession).\
                filter_by(token=self.chat_session_token).\
                one()

            # 1) Archive Job
            chat_archive_job = db_session.query(ChatArchiveJob).\
                filter_by(chat_session_id=chat_session.id).\
                all()
                # We call .all() here to support negative test cases where
                # this data is not inserted into the db
            for job in chat_archive_job:
                db_session.delete(job)

            # 2) Highlight Chat
            chat_highlight = db_session.query(ChatHighlightSession).\
                filter_by(chat_session_id=chat_session.id).\
                all()
            for highlight in chat_highlight:
                db_session.delete(highlight)

            # 3) Data generated from ChatMessages
            chat_minutes = db_session.query(ChatMinute).\
                filter_by(chat_session_id=chat_session.id).\
                all()
            for minute in chat_minutes:
                # Delete Tags
                tags = db_session.query(ChatTag).\
                    filter_by(chat_minute_id=minute.id).\
                    all()
                for tag in tags:
                    db_session.delete(tag)
                # Delete Markers
                markers = db_session.query(ChatSpeakingMarker).\
                    filter_by(chat_minute_id=minute.id).\
                    all()
                for marker in markers:
                    db_session.delete(marker)
                # Delete the Minute after all refs to it are deleted
                db_session.delete(minute)

            # Delete data created by setUp()
            db_session.delete(self.chat_persist_job)
            db_session.delete(chat_session)
            db_session.delete(self.chat_user)
            db_session.delete(self.chat)
            db_session.delete(self.root_topic)
            db_session.delete(self.topic1)
            for chat_message in self.chat_messages:
                db_session.delete(chat_message)

            db_session.commit()

        except Exception as e:
            logging.exception(e)
        finally:
            if db_session:
                db_session.close()


    def test_successful_job(self):

        print '################################################'
        print 'test_successful_job'
        print '################################################'

        # Service polls at 60 second intervals.
        # Sleep poll+30 secs to ensure that the unprocessed jobs written
        # during setup() will have been processed.
        time.sleep(settings.PERSISTER_POLL_SECONDS + 30)

        # Verify chat_persist_job fields updated properly
        db_session = self.service.handler.get_database_session()
        chat_session = db_session.query(ChatSession).\
            filter_by(token=self.chat_session_token).\
            one()
        chat_persist_job = db_session.query(ChatPersistJob).\
            filter_by(chat_session_id=chat_session.id).\
            one()

        # Verify job start
        self.assertIsNotNone(chat_persist_job.start)
        self.assertEqual('persistsvc', chat_persist_job.owner)

        # Verify job end
        self.assertIsNotNone(chat_persist_job.end)
        self.assertTrue(chat_persist_job.successful)

        # Verify ChatArchiveJob data
        chat_archive_job = db_session.query(ChatArchiveJob).\
            filter_by(chat_session_id=chat_session.id).\
            one()
        self.assertEqual(chat_session.id, chat_archive_job.chat_session_id)
        self.assertIsNotNone(chat_archive_job.created)
        self.assertIsNotNone(chat_archive_job.not_before)
        self.assertEqual(3, chat_archive_job.retries_remaining)

        # Verify ChatHighlightSessions created (only 1 in this case)
        chat_highlight = db_session.query(ChatHighlightSession).\
            filter_by(chat_session_id=chat_session.id).\
            filter_by(user_id=self.test_user_id).\
            one()
        self.assertEqual(chat_session.id, chat_highlight.chat_session_id)
        self.assertEqual(self.test_user_id, chat_highlight.user_id)
        self.assertIsNotNone(chat_highlight.rank)

        # TODO Verify ChatMessage data
        # The chat message db entities are already tested in the
        # distributed persist service test. I thought it useless
        # to copy and paste the code into this block.


    def test_chat_highlight_already_exists(self):
        # Verify job is successful if user has already added the chat
        # to their highlight reel before the persistsvc has run.

        print '################################################'
        print 'test_chat_highlight_already_exists'
        print '################################################'

        try:
            db_session = self.service.handler.get_database_session()
            chat_session = db_session.query(ChatSession).\
                filter_by(token=self.chat_session_token).\
                one()

            # Create ChatHighlightSession before the persist svc
            # Rank is 0-based, so counting the number of existing
            # chat highlights will enable us to insert this highlight
            # last.
            chat_highlight_count = db_session.query(ChatHighlightSession).\
                filter_by(user_id=self.test_user_id).\
                count()
            chat_highlight = ChatHighlightSession(
                chat_session_id=chat_session.id,
                user_id=self.test_user_id,
                rank=chat_highlight_count
            )
            db_session.add(chat_highlight)
            db_session.commit()
            print 'ChatHighlightSession manually created'

            # Sleep poll+30 secs to ensure that the unprocessed jobs written
            # during setup() will have been processed.
            time.sleep(settings.PERSISTER_POLL_SECONDS + 30)

            # For now, just ensure that this doesn't cause an
            # an exception to be thrown. The persist svc should
            # see the existing ChatHighlightSession and forego
            # creating another one.
            pass

        except Exception as e:
            logging.exception(e)
            if db_session:
                db_session.rollback()
        finally:
            if db_session:
                db_session.close()


#    def test_abort_job(self):
#        # TODO Verify all data is unwound if job is aborted
#        pass
#
#
#    def test_duplicate_job(self):
#        # TODO Verify job is aborted if already claimed by another thread
#        pass
#
#    def test_tutorial_chat(self):
#        # TODO Verify no chat highlight is created for this job
#        pass




if __name__ == '__main__':
    unittest.main()


