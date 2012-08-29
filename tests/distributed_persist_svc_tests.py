
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
from trsvcscore.db.models import Chat, ChatPersistJob, ChatSession, ChatMinute, ChatSpeakingMarker, ChatTag, \
    Topic

from chat_test_data import ChatTestDataSets
from testbase import DistributedTestCase
from topic_test_data import TopicTestDataSets



class DistributedPersistServiceTest(DistributedTestCase):
    """
        Run multiple instances of the PersistService simultaneously
        and ensure operation is correct.
    """

    @classmethod
    def setUpClass(cls):
        DistributedTestCase.setUpClass()

        # Get chat data
        chat_data = ChatTestDataSets()
        cls.test_chat_datasets = chat_data.get_list()


        # Need to create the data objs that persist job requires
        # Need to write ChatPersistJobs

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

        cls.chat_session = ChatSession(
            chat=cls.chat,
            token='dummy_test_token1',
            participants=1)

        cls.chat_persist_job = ChatPersistJob(
            chat_session=cls.chat_session,
            created=tz.utcnow()
        )

        try:
            # Write data to the db
            db_session = cls.service.handler.get_database_session()
            db_session.add(cls.chat_session)
            db_session.add(cls.chat)
            db_session.add(cls.root_topic)
            db_session.add(cls.chat_persist_job)
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
            db_session.delete(cls.chat_persist_job)
            db_session.delete(cls.chat_session)
            db_session.delete(cls.chat)
            db_session.delete(cls.root_topic)
            db_session.delete(cls.topic1)
            db_session.commit()

        except Exception as e:
            logging.exception(e)
        finally:
            db_session.close()




    def test_multipleServicesRunning(self):

        # Setup() will have started two instances of the persist service.
        # Services poll at 60 second intervals.
        # Sleep 90 secs to ensure that the unprocessed jobs written
        # during setup() will have been processed.
        time.sleep(70)

        # Read back data written to db.
        pass




if __name__ == '__main__':
    unittest.main()



