import unittest
import logging
import time

from trpycore.zookeeper.client import ZookeeperClient
from trsvcscore.proxy.zoo import ZookeeperServiceProxy
from tridlcore.gen.ttypes import RequestContext
from trpersistsvc.gen import TPersistService

class MessageHandlerTest(unittest.TestCase):
    """
        Test the persist service's chat message handler.
    """

    @classmethod
    def setUpClass(cls):
        cls.service_name = "persistsvc"
        cls.service_class = TPersistService

        cls.zookeeper_client = ZookeeperClient(["localdev:2181"])
        cls.zookeeper_client.start()
        time.sleep(1)

        cls.service = ZookeeperServiceProxy(cls.zookeeper_client, cls.service_name, cls.service_class, keepalive=True)
        cls.request_context = RequestContext(userId=0, impersonatingUserId=0, sessionId="dummy_session_id", context="")

        logging.basicConfig(level=logging.DEBUG)

        # Instantiate MessageHandler
        # dbSession =
        # msg_handler = MessageHandler(dbSession)

    @classmethod
    def tearDownClass(cls):
        cls.zookeeper_client.stop()
        cls.zookeeper_client.join()


    def test_minuteCreateMessage(self):
        # Create ChatMessage using SQLAlchemy
        # Pass in to process
        # Verify type of object returned
        # Verify data
        # Verify biz rules depending upon input data
        # Will probably need a ChatMessage builder class to encode
        pass

    def test_activeMinute(self):
        pass

    def test_persistChat(self):
        # test end to end
        pass



if __name__ == '__main__':
    unittest.main()

