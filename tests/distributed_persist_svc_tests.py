
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
from trsvcscore.db.models import Chat, ChatPersistJob, ChatSession, ChatMessage, ChatMinute, ChatSpeakingMarker, ChatTag, \
    Topic

from chat_test_data import ChatTestDataBuilder
from testbase import DistributedTestCase

import settings




#TODO This test class is not very robust. It relies
#upon a fixed Topic structure.  Additionally, at
#present no speaking markers are being tested.
#The chat minute models that are created for testing
#are also very simple. It will have to do for now.


class DistributedPersistServiceTest(DistributedTestCase):
    """
        Run multiple instances of the PersistService simultaneously
        and ensure operation is correct.
    """

    @classmethod
    def setUpClass(cls):
        DistributedTestCase.setUpClass()


        # Need to create the data objs that persist job requires
        #   1) Need to write ChatPersistJobs
        #   2) Need to write ChatMessages


        # Generate chat persist job data
        #
        # Match the topic structure of the test chat data
        # that was used above to generate chat messages.
        cls.root_topic = Topic(
            parent_id=None,
            rank=0,
            title="DistributedTestChat",
            description="Chat topic used to test the persist service",
            duration=30,
            public=True,
            user_id=1,
            type_id=1
        )
        cls.topic1 = Topic(
            rank=1,
            title="t1",
            description="t1 description",
            duration=10,
            public=True,
            user_id=1,
            type_id=1
        )
        cls.root_topic.children.append(cls.topic1)

        cls.chat = Chat(
            type_id=1,
            topic=cls.root_topic,
            start=tz.utcnow(),
            end=tz.utcnow()+datetime.timedelta(minutes=5))



        # Can have as many chat_sessions and jobs as needed
        # Just doing 1 session and 1 persist job for now.
        cls.chat_session_token = 'test1_dummy_token'


        cls.chat_session = ChatSession(
            chat=cls.chat,
            token=cls.chat_session_token,
            participants=1)

        cls.chat_persist_job = ChatPersistJob(
            chat_session=cls.chat_session,
            created=tz.utcnow()
        )

        try:
            # Write ChatPersistJob data to the db
            db_session = cls.service.handler.get_database_session()
            db_session.add(cls.chat_session)
            db_session.add(cls.chat)
            db_session.add(cls.root_topic)
            db_session.add(cls.chat_persist_job)
            db_session.commit()

            # Generate chat message data
            # Note the commit() above is required since we need
            # real IDs to build and persist ChatMessages.
            builder = ChatTestDataBuilder()
            cls.chat_data = builder.build(
                root_topic_id=cls.root_topic.id,
                topic1_id=cls.topic1.id,
                chat_session_id=cls.chat_session.id,
                chat_session_token=cls.chat_session_token,
                user_id=1
            )

            # Write ChatMessages to the db for consumption by the persist svc
            cls.chat_messages = cls.chat_data.serialized_message_list
            for chat_message in cls.chat_messages:
                db_session.add(chat_message)
            db_session.commit()

        except Exception as e:
            logging.exception(e)
        finally:
            db_session.close()




    @classmethod
    def tearDownClass(cls):
        DistributedTestCase.tearDownClass()

        try:
            # Remove chat data from db
            db_session = cls.service.handler.get_database_session()

            # Delete data generated by persist service
            chat_session = db_session.query(ChatSession).\
                filter_by(token=cls.chat_session_token).\
                one()
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


            # Delete data generated by Setup()
            db_session.delete(cls.chat_persist_job)
            db_session.delete(chat_session)
            db_session.delete(cls.chat)
            db_session.delete(cls.root_topic)
            db_session.delete(cls.topic1)
            for chat_message in cls.chat_messages:
                db_session.delete(chat_message)

            db_session.commit()

        except Exception as e:
            logging.exception(e)
        finally:
            db_session.close()



    def test_multipleServicesRunning(self):

        # Setup() will have started two instances of the persist service.
        # Services poll at 60 second intervals.
        # Sleep poll+30 secs to ensure that the unprocessed jobs written
        # during setup() will have been processed.
        time.sleep(settings.PERSISTER_POLL_SECONDS + 30)

        # Read and verify the data that the persist job
        # added to the db.
        chat_minutes = []
        chat_tags = []
        chat_speaking_markers = []

        try:
            # Retrieve all created ChatMinutes, ChatTags,
            # and ChatSpeakingMarkers
            db_session = self.service.handler.get_database_session()

            chat_session = db_session.query(ChatSession).\
                filter_by(token=self.chat_session_token).\
                one()

            minutes = db_session.query(ChatMinute).\
                filter_by(chat_session_id=chat_session.id).\
                order_by(ChatMinute.start).\
                all()
            chat_minutes.extend(minutes)

            for minute in chat_minutes:

                #TODO ordering tags this way is not robust and relies upon an implementation detail
                tags = db_session.query(ChatTag).\
                    filter_by(chat_minute_id=minute.id).\
                    order_by(ChatTag.id).\
                    all()
                chat_tags.extend(tags)

                markers = db_session.query(ChatSpeakingMarker).\
                    filter_by(chat_minute_id=minute.id).\
                    order_by(ChatSpeakingMarker.start).\
                    all()
                chat_speaking_markers.extend(markers)



            # Compare number of tags created to expected number
            expected_chat_tags = self.chat_data.expected_tag_models
            self.assertEqual(len(expected_chat_tags), len(chat_tags))

            # Compare output to expected values
            for index, actual_tag in enumerate(chat_tags):
                # index values start at 0
                self.assertEqual(expected_chat_tags[index].user_id, actual_tag.user_id)
                self.assertEqual(expected_chat_tags[index].tag_id, actual_tag.tag_id)
                self.assertEqual(expected_chat_tags[index].name, actual_tag.name)
                self.assertEqual(expected_chat_tags[index].deleted, actual_tag.deleted)
                self.assertEqual(expected_chat_tags[index].chat_minute.chat_session_id, actual_tag.chat_minute.chat_session_id)
                self.assertEqual(expected_chat_tags[index].chat_minute.topic_id, actual_tag.chat_minute.topic_id)
                self.assertEqual(expected_chat_tags[index].chat_minute.start, actual_tag.chat_minute.start)
                self.assertEqual(expected_chat_tags[index].chat_minute.end, actual_tag.chat_minute.end)



            # Compare number of minutes created to expected number
            expected_chat_minutes = self.chat_data.expected_minute_models
            self.assertEqual(len(expected_chat_minutes), len(chat_minutes))

            # Compare output to expected values
            for index, model in enumerate(chat_minutes):
                self.assertEqual(expected_chat_minutes[index].chat_session_id, model.chat_session_id)
                self.assertEqual(expected_chat_minutes[index].topic_id, model.topic_id)
                self.assertEqual(expected_chat_minutes[index].start, model.start)
                self.assertEqual(expected_chat_minutes[index].end, model.end)



            # Compare number of markers created to expected number
            expected_chat_markers = self.chat_data.expected_marker_models
            self.assertEqual(len(expected_chat_markers), len(chat_speaking_markers))

            # Compare output to expected values
            for index, model in enumerate(chat_speaking_markers):
                self.assertIsNotNone(model.start)
                self.assertIsNotNone(model.end)
                self.assertEqual(expected_chat_markers[index].user_id, model.user_id)
                self.assertEqual(expected_chat_markers[index].chat_minute.chat_session_id, model.chat_minute.chat_session_id)
                self.assertEqual(expected_chat_markers[index].chat_minute.topic_id, model.chat_minute.topic_id)
                self.assertEqual(expected_chat_markers[index].chat_minute.start, model.chat_minute.start)
                self.assertEqual(expected_chat_markers[index].chat_minute.end, model.chat_minute.end)



        except Exception as e:
            logging.exception(e)
        finally:
            db_session.close()







if __name__ == '__main__':
    unittest.main()



