import os
import sys
import unittest

SERVICE_NAME = "persistsvc"

#Add SERVICE_ROOT to python path, for imports.
SERVICE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../", SERVICE_NAME))
sys.path.insert(0, SERVICE_ROOT)

from trpycore.timezone import tz

from chat_test_data import ChatTestDataSets
from message_handler import ChatMessageHandler, ChatTagHandler
from persistsvc_exceptions import DuplicateTagIdException, NoActiveChatMinuteException,\
    TagIdDoesNotExistException
from testbase import IntegrationTestCase


class ChatMarkerHandlerTest(IntegrationTestCase):
    """
        Test the ChatMarkerHandler class
    """

    @classmethod
    def setUpClass(cls):

        # Get chat data
        chat_data = ChatTestDataSets()
        cls.test_chat_datasets = chat_data.get_list()

    @classmethod
    def tearDownClass(cls):
        pass

    def test_createModels(self):

        # Get chat data
        chat_data = self.test_chat_datasets[0]

        # Create ChatMarkerHandler
        message_handler = ChatMessageHandler(chat_data.chat_session_id, chat_data.topic_collection)
        marker_handler = message_handler.chat_marker_handler

        # Process messages
        for deserialized_msg in chat_data.message_list:
            message_handler.process(deserialized_msg)

        # Retrieve all speaking marker models
        speaking_models = marker_handler.finalize()

        # Ensure number of created models
        self.assertEqual(len(chat_data.expected_marker_models), len(speaking_models))

        # Ensure models are returned in chronological order
        prev_model_start = 0
        for model in speaking_models:
            model_start = tz.utc_to_timestamp(model.start)
            self.assertGreater(model_start, prev_model_start)
            prev_model_start = model_start

        # Check model data
        expected_models = chat_data.expected_marker_models
        for index, model in enumerate(speaking_models):
            self.assertIsNotNone(model.start)
            self.assertIsNotNone(model.end)
            self.assertEqual(expected_models[index].user_id, model.user_id)
            self.assertEqual(expected_models[index].chat_minute.chat_session_id, model.chat_minute.chat_session_id)
            self.assertEqual(expected_models[index].chat_minute.topic_id, model.chat_minute.topic_id)
            self.assertEqual(expected_models[index].chat_minute.start, model.chat_minute.start)
            self.assertEqual(expected_models[index].chat_minute.end, model.chat_minute.end)

    def test_createModels_noActiveChatMinute(self):

        # Get chat data
        chat_data = self.test_chat_datasets[0]

        # Create ChatMarkerHandler
        message_handler = ChatMessageHandler(chat_data.chat_session_id, chat_data.topic_collection)
        message_handler.chat_minute_handler._set_active_minute(None)
        marker_handler = message_handler.chat_marker_handler

        # Process chat-started message to indicate that the active minute
        # should now never be None
        self.assertEqual(False, marker_handler.is_chat_started)
        message = chat_data.message_list[28]
        marker_handler.create_models(message)
        self.assertEqual(True, marker_handler.is_chat_started)

        # Test create_models
        message = chat_data.message_list[31] # Get a speaking marker message
        with self.assertRaises(NoActiveChatMinuteException):
            marker_handler.create_models(message)

    def test_updateModels(self):

        # Get chat data
        chat_data = self.test_chat_datasets[0]

        # Create ChatTagHandler
        message_handler = ChatMessageHandler(chat_data.chat_session_id, chat_data.topic_collection)
        marker_handler = message_handler.chat_marker_handler

        with self.assertRaises(NotImplementedError):
            marker_handler.update_models(None)

    def test_deleteModels(self):

        # Get chat data
        chat_data = self.test_chat_datasets[0]

        # Create ChatTagHandler
        message_handler = ChatMessageHandler(chat_data.chat_session_id, chat_data.topic_collection)
        marker_handler = message_handler.chat_marker_handler

        with self.assertRaises(NotImplementedError):
            marker_handler.delete_models(None)



if __name__ == '__main__':
    unittest.main()
