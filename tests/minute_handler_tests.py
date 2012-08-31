
import os
import sys
import unittest

SERVICE_NAME = "persistsvc"
#Add SERVICE_ROOT to python path, for imports.
SERVICE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../", SERVICE_NAME))
sys.path.insert(0, SERVICE_ROOT)

from trpycore.timezone import tz
from trsvcscore.db.models import ChatMinute

from chat_test_data import ChatTestDataSets
from message_handler import ChatMessageHandler, ChatMinuteHandler
from persistsvc_exceptions import InvalidChatMinuteException
from topic_data_manager import TopicDataManager, TopicDataCollection, TopicData
from topic_test_data import TopicTestDataSets


class ChatMinuteHandlerTest(unittest.TestCase):
    """
        Test the Chat Minute Handler class
    """

    @classmethod
    def setUpClass(cls):

        cls.chat_session_id = 'dummy_session_id'

        # Get topic data
        topic_data = TopicTestDataSets()
        cls.test_topic_datasets = topic_data.get_list()

        # Get chat data
        chat_data = ChatTestDataSets()
        cls.test_chat_datasets = chat_data.get_list()

    @classmethod
    def tearDownClass(cls):
        pass

    def test_getHighestLeafs(self):

        for dataset in self.test_topic_datasets:

            message_handler = ChatMessageHandler(self.chat_session_id, dataset.topic_collection)
            handler = message_handler.chat_minute_handler
            highest_leafs = handler._get_highest_ranked_leafs(dataset.topic_collection)
            expected_highest_leafs = dataset.expected_highest_leaf_list_by_rank

            # Verify topics
            self.assertEqual(
                expected_highest_leafs,
                highest_leafs
            )

    def test_getChatMinuteEndTopicChain(self):

        for dataset in self.test_topic_datasets:

            message_handler = ChatMessageHandler(self.chat_session_id, dataset.topic_collection)
            handler = message_handler.chat_minute_handler
            chat_minute_end_topic_chain = handler._get_chat_minute_end_topic_chain(dataset.topic_collection)
            expected_topic_chain = dataset.expected_chat_minute_end_topic_chain

            for key, value in chat_minute_end_topic_chain.items():
                for topic in value:
                    #print 'key %s: %s' % (key, topic.id)
                    pass

            # Verify topics
            self.assertEqual(
                expected_topic_chain,
                chat_minute_end_topic_chain
            )

    def test_chatMinuteHandler(self):
        """ Sends input deserialized Thrift messages into
        the ChatMessageHandler and verifies the output
        ChatMinute objects.
        """

        # Get chat data
        chat_data = self.test_chat_datasets[0]

        # Create ChatMinuteHandler
        message_handler = ChatMessageHandler(chat_data.chat_session_id, chat_data.topic_collection)
        minute_handler = message_handler.chat_minute_handler

        # Process messages
        for deserialized_msg in chat_data.message_list:
            message_handler.process(deserialized_msg)

        # Retrieve all chat minute models ordered by topic rank
        minute_models = minute_handler.finalize()

        # Ensure number of created models
        self.assertEqual(len(chat_data.expected_minute_models), len(minute_models))

        # Ensure models are returned in chronological order
        prev_model_start = 0
        for model in minute_models:
            model_start = tz.utc_to_timestamp(model.start)
            self.assertGreaterEqual(model_start, prev_model_start)
            prev_model_start = model_start

        # Check model data
        expected_models = chat_data.expected_minute_models
        for index, model in enumerate(minute_models):
            self.assertEqual(expected_models[index].chat_session_id, model.chat_session_id)
            self.assertEqual(expected_models[index].topic_id, model.topic_id)
            self.assertEqual(expected_models[index].start, model.start)
            self.assertEqual(expected_models[index].end, model.end)

    def test_createModels_invalidMinute(self):

        # Get chat data
        chat_data = self.test_chat_datasets[0]

        # Create ChatMinuteHandler
        message_handler = ChatMessageHandler(chat_data.chat_session_id, chat_data.topic_collection)
        minute_handler = message_handler.chat_minute_handler

        # Create the real ChatTag
        message = chat_data.message_list[27]
        minute_handler.create_models(message)
        with self.assertRaises(InvalidChatMinuteException):
            minute_handler.finalize()

    def test_updateModels(self):

        # Get chat data
        chat_data = self.test_chat_datasets[0]

        # Create ChatMinuteHandler
        message_handler = ChatMessageHandler(chat_data.chat_session_id, chat_data.topic_collection)
        minute_handler = message_handler.chat_minute_handler

        # Set the start time on the chat minutes (Root, Topic1)
        message = chat_data.message_list[27]
        message_handler.process(message)

        # Since the end-time's have not been written, an exception should be raised
        with self.assertRaises(InvalidChatMinuteException):
            minute_handler.finalize()

        # Set the end time on the chat minutes (Root, Topic1)
        message = chat_data.message_list[64]
        message_handler.process(message)
        minute_models = minute_handler.finalize()

        # Ensure number of created models
        self.assertEqual(len(chat_data.expected_minute_models), len(minute_models))

        # Ensure models are returned in chronological order
        prev_model_start = 0
        for model in minute_models:
            model_start = tz.utc_to_timestamp(model.start)
            self.assertGreaterEqual(model_start, prev_model_start)
            prev_model_start = model_start

        # Check model data
        expected_models = chat_data.expected_minute_models
        for index, model in enumerate(minute_models):
            self.assertEqual(expected_models[index].chat_session_id, model.chat_session_id)
            self.assertEqual(expected_models[index].topic_id, model.topic_id)
            self.assertEqual(expected_models[index].start, model.start)
            self.assertEqual(expected_models[index].end, model.end)

    def test_deleteModels(self):

        # Get chat data
        chat_data = self.test_chat_datasets[0]

        # Create ChatTagHandler
        message_handler = ChatMessageHandler(chat_data.chat_session_id, chat_data.topic_collection)
        minute_handler = message_handler.chat_minute_handler

        with self.assertRaises(NotImplementedError):
            minute_handler.delete_models(None)



if __name__ == '__main__':
    unittest.main()