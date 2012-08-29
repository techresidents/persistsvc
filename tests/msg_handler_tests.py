
import logging
import os
import sys
import unittest


SERVICE_NAME = "persistsvc"
#Add SERVICE_ROOT to python path, for imports.
SERVICE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../", SERVICE_NAME))
sys.path.insert(0, SERVICE_ROOT)


from chat_test_data import ChatTestDataSets
from message_handler import ChatMessageHandler
from testbase import IntegrationTestCase
from topic_test_data import TopicTestDataSets





class ChatMessageHandlerTest(unittest.TestCase):
    """
        Test the persist service's chat message handler.
    """

    @classmethod
    def setUpClass(cls):
        #IntegrationTestCase.setUpClass()
        #cls.db_session = cls.service.handler.get_database_session()

        # Get topic data
        topic_data = TopicTestDataSets()
        cls.test_topic_datasets = topic_data.get_list()

        # Get chat data
        chat_data = ChatTestDataSets()
        cls.test_chat_datasets = chat_data.get_list()


    @classmethod
    def tearDownClass(cls):
        #IntegrationTestCase.setUpClass()
        pass



    def test_ChatMessageHandlerInit(self):

        # Specify a chat
        chat_data = self.test_chat_datasets[0]

        # Instantiate MessageHandler
        handler = ChatMessageHandler(chat_data.chat_session_id, chat_data.topic_collection)
        self.assertIsNotNone(handler.chat_marker_handler)
        self.assertIsNotNone(handler.chat_minute_handler)
        self.assertIsNotNone(handler.chat_tag_handler)





if __name__ == '__main__':
    unittest.main()

