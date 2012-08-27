
import os
import sys
import unittest

from trchatsvc.gen.ttypes import Message, MessageHeader, MessageRoute,\
    Marker, MarkerCreateMessage, JoinedMarker, ConnectedMarker,\
    WhiteboardCreateMessage,\
    MinuteCreateMessage, MinuteUpdateMessage, \
    TagCreateMessage, TagDeleteMessage,\
    StartedMarker, EndedMarker
from trpycore.timezone import tz
from trsvcscore.db.models import ChatMinute, ChatSpeakingMarker, ChatTag

SERVICE_NAME = "persistsvc"

#Add SERVICE_ROOT to python path, for imports.
SERVICE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../", SERVICE_NAME))
sys.path.insert(0, SERVICE_ROOT)

from chat_test_data import ChatTestDataSets
from message_handler import ChatMessageHandler, ChatTagHandler
from persistsvc_exceptions import DuplicateTagIdException, NoActiveChatMinuteException, \
    TagIdDoesNotExistException
from testbase import IntegrationTestCase
from topic_test_data import TopicTestDataSets

class ChatTagHandlerTest(IntegrationTestCase):
    """
        Test the ChatTagHandler class
    """

    @classmethod
    def setUpClass(cls):

        #IntegrationTestCase.setUpClass()
        #cls.db_session = cls.service.handler.get_database_session()

        # Get chat data
        chat_data = ChatTestDataSets()
        cls.test_chat_datasets = chat_data.get_list()

        # Dummy Chat Minute
        cls.dummy_chat_minute = ChatMinute(
            chat_session_id='dummy_session_id',
            topic_id=777, # Random ID
            start=tz.timestamp_to_utc(1345643963),
            end = tz.timestamp_to_utc(1345643999))


    @classmethod
    def tearDownClass(cls):
        #IntegrationTestCase.tearDownClass()
        pass


    def test_chatMessageHandler(self):

        # Get chat data
        chat_data = self.test_chat_datasets[1]

        # Create ChatTagHandler
        message_handler = ChatMessageHandler(chat_data.chat_session_id, chat_data.topic_collection)

        # Process messages
        for deserialized_msg in chat_data.message_list:
            message_handler.process(deserialized_msg)

        # Retrieve all chat tag models
        tag_models = message_handler.chat_tag_handler.finalize()

        # Compare output to expected values
        expected_tag_models = chat_data.expected_tag_models
        for (index, actual_tag) in enumerate(tag_models):
            # index values start at 0
            self.assertEqual(expected_tag_models[index].user_id, actual_tag.user_id)
            self.assertEqual(expected_tag_models[index].tag_id, actual_tag.tag_id)
            self.assertEqual(expected_tag_models[index].name, actual_tag.name)
            self.assertEqual(expected_tag_models[index].deleted, actual_tag.deleted)
            self.assertEqual(expected_tag_models[index].chat_minute.chat_session_id, actual_tag.chat_minute.chat_session_id)
            self.assertEqual(expected_tag_models[index].chat_minute.topic_id, actual_tag.chat_minute.topic_id)
            self.assertEqual(expected_tag_models[index].chat_minute.start, actual_tag.chat_minute.start)
            self.assertEqual(expected_tag_models[index].chat_minute.end, actual_tag.chat_minute.end)

    def test_createModels_singleTag(self):

        # Get chat data
        chat_data = self.test_chat_datasets[1]
        chat_minute = chat_data.expected_minute_models[1]

        # Create ChatTagHandler
        message_handler = ChatMessageHandler(chat_data.chat_session_id, chat_data.topic_collection)
        message_handler.chat_minute_handler._set_active_minute(chat_minute)
        tag_handler = message_handler.chat_tag_handler

        # Expected ChatTag
        message = chat_data.message_list[6]
        expected_tag = ChatTag(
            user_id=message.header.userId,
            chat_minute=chat_minute,
            tag_id=message.tagCreateMessage.tagReferenceId,
            name=message.tagCreateMessage.name,
            deleted=False)

        # Create the real ChatTag
        tag_handler.create_models(message)
        created_tags = tag_handler.finalize()
        self.assertEqual(1, len(created_tags))
        actual_tag = created_tags[0]

        # Compare output to expected values
        self.assertEqual(expected_tag.user_id, actual_tag.user_id)
        self.assertEqual(expected_tag.chat_minute, actual_tag.chat_minute)
        self.assertEqual(expected_tag.tag_id, actual_tag.tag_id)
        self.assertEqual(expected_tag.name, actual_tag.name)
        self.assertEqual(expected_tag.deleted, actual_tag.deleted)

    def test_createModels_duplicateTags(self):

        # Get chat data
        chat_data = self.test_chat_datasets[1]
        chat_minute = chat_data.expected_minute_models[1]

        # Create ChatTagHandler
        message_handler = ChatMessageHandler(chat_data.chat_session_id, chat_data.topic_collection)
        message_handler.chat_minute_handler._set_active_minute(chat_minute)
        tag_handler = message_handler.chat_tag_handler

        # Expected ChatTag
        message = chat_data.message_list[6]
        expected_tag = ChatTag(
            user_id=message.header.userId,
            chat_minute=chat_minute,
            tag_id=message.tagCreateMessage.tagReferenceId,
            name=message.tagCreateMessage.name,
            deleted=False)

        # Create the real ChatTag
        tag_handler.create_models(message)

        # Create a duplicate ChatTag - same user, chat_minute, and tag name
        with self.assertRaises(DuplicateTagIdException):
            tag_handler.create_models(message)

        # Get created tags
        created_tags = tag_handler.finalize()
        self.assertEqual(1, len(created_tags))
        actual_tag = created_tags[0]

        # Compare output to expected values
        self.assertEqual(expected_tag.user_id, actual_tag.user_id)
        self.assertEqual(expected_tag.chat_minute, actual_tag.chat_minute)
        self.assertEqual(expected_tag.tag_id, actual_tag.tag_id)
        self.assertEqual(expected_tag.name, actual_tag.name)
        self.assertEqual(expected_tag.deleted, actual_tag.deleted)

    def test_createModels_noActiveChatMinute(self):

        # Get chat data
        chat_data = self.test_chat_datasets[1]
        chat_minute = None

        # Create ChatTagHandler
        message_handler = ChatMessageHandler(chat_data.chat_session_id, chat_data.topic_collection)
        message_handler.chat_minute_handler._set_active_minute(chat_minute)
        tag_handler = message_handler.chat_tag_handler

        # Test create_models
        message = chat_data.message_list[6]
        with self.assertRaises(NoActiveChatMinuteException):
            tag_handler.create_models(message)

        # Test delete_models
        message = chat_data.message_list[8]
        with self.assertRaises(NoActiveChatMinuteException):
            tag_handler.delete_models(message)

    def test_createModels_sameUserSameTagNameDifferentMinute(self):

        # Get chat data
        chat_data = self.test_chat_datasets[1]
        chat_minute = chat_data.expected_minute_models[1]

        # Create ChatTagHandler
        message_handler = ChatMessageHandler(chat_data.chat_session_id, chat_data.topic_collection)
        tag_handler = message_handler.chat_tag_handler

        # Expected ChatTag
        message = chat_data.message_list[9]
        expected_tag1 = ChatTag(
            user_id=message.header.userId,
            chat_minute=chat_minute,
            tag_id=message.tagCreateMessage.tagReferenceId,
            name=message.tagCreateMessage.name,
            deleted=False)

        # Create the real ChatTag
        message_handler.chat_minute_handler._set_active_minute(chat_minute)
        tag_handler.create_models(message)

        # Expected ChatTag
        message = chat_data.message_list[10]
        expected_tag2 = ChatTag(
            user_id=message.header.userId,
            chat_minute=self.dummy_chat_minute,  #Different ChatMinute than 1st Tag
            tag_id=message.tagCreateMessage.tagReferenceId,
            name=message.tagCreateMessage.name,
            deleted=False)

        # Create the real ChatTag
        message_handler.chat_minute_handler._set_active_minute(self.dummy_chat_minute)
        tag_handler.create_models(message)

        # Retrieve created models
        created_tags = tag_handler.finalize()
        self.assertEqual(2, len(created_tags))
        self.assertIsNotNone(created_tags[0])
        self.assertIsNotNone(created_tags[1])

        actual_tag1 = created_tags[0]
        actual_tag2 = created_tags[1]

        # Compare output to expected values
        self.assertEqual(expected_tag1.user_id, actual_tag1.user_id)
        self.assertEqual(expected_tag1.chat_minute, actual_tag1.chat_minute)
        self.assertEqual(expected_tag1.tag_id, actual_tag1.tag_id)
        self.assertEqual(expected_tag1.name, actual_tag1.name)
        self.assertEqual(expected_tag1.deleted, actual_tag1.deleted)

        # Compare output to expected values
        self.assertEqual(expected_tag2.user_id, actual_tag2.user_id)
        self.assertEqual(expected_tag2.chat_minute, actual_tag2.chat_minute)
        self.assertEqual(expected_tag2.tag_id, actual_tag2.tag_id)
        self.assertEqual(expected_tag2.name, actual_tag2.name)
        self.assertEqual(expected_tag2.deleted, actual_tag2.deleted)

    def test_createModels_sameUserDifferentTagNameSameMinute(self):

        # Get chat data
        chat_data = self.test_chat_datasets[1]
        chat_minute = chat_data.expected_minute_models[1]

        # Create ChatTagHandler
        message_handler = ChatMessageHandler(chat_data.chat_session_id, chat_data.topic_collection)
        message_handler.chat_minute_handler._set_active_minute(chat_minute)
        tag_handler = message_handler.chat_tag_handler

        # Expected ChatTag
        message = chat_data.message_list[6]
        expected_tag1 = ChatTag(
            user_id=message.header.userId,
            chat_minute=chat_minute,
            tag_id=message.tagCreateMessage.tagReferenceId,
            name=message.tagCreateMessage.name,
            deleted=False)

        # Create the real ChatTag
        tag_handler.create_models(message)

        # Expected ChatTag
        message = chat_data.message_list[7]
        expected_tag2 = ChatTag(
            user_id=message.header.userId,
            chat_minute=chat_minute,
            tag_id=message.tagCreateMessage.tagReferenceId,
            name=message.tagCreateMessage.name,
            deleted=False)

        # Create the real ChatTag
        tag_handler.create_models(message)

        # Retrieve created models
        created_tags = tag_handler.finalize()
        self.assertEqual(2, len(created_tags))
        self.assertIsNotNone(created_tags[0])
        self.assertIsNotNone(created_tags[1])

        actual_tag1 = created_tags[0]
        actual_tag2 = created_tags[1]

        # Compare output to expected values
        self.assertEqual(expected_tag1.user_id, actual_tag1.user_id)
        self.assertEqual(expected_tag1.chat_minute, actual_tag1.chat_minute)
        self.assertEqual(expected_tag1.tag_id, actual_tag1.tag_id)
        self.assertEqual(expected_tag1.name, actual_tag1.name)
        self.assertEqual(expected_tag1.deleted, actual_tag1.deleted)

        # Compare output to expected values
        self.assertEqual(expected_tag2.user_id, actual_tag2.user_id)
        self.assertEqual(expected_tag2.chat_minute, actual_tag2.chat_minute)
        self.assertEqual(expected_tag2.tag_id, actual_tag2.tag_id)
        self.assertEqual(expected_tag2.name, actual_tag2.name)
        self.assertEqual(expected_tag2.deleted, actual_tag2.deleted)

    def test_createModels_differentUserSameTagNameSameMinute(self):

        # Get chat data
        chat_data = self.test_chat_datasets[1]
        chat_minute = chat_data.expected_minute_models[1]

        # Create ChatTagHandler
        message_handler = ChatMessageHandler(chat_data.chat_session_id, chat_data.topic_collection)
        message_handler.chat_minute_handler._set_active_minute(chat_minute)
        tag_handler = message_handler.chat_tag_handler

        # Expected ChatTag
        message = chat_data.message_list[6]
        expected_tag1 = ChatTag(
            user_id=message.header.userId,
            chat_minute=chat_minute,
            tag_id=message.tagCreateMessage.tagReferenceId,
            name=message.tagCreateMessage.name,
            deleted=False)

        # Create the real ChatTag
        tag_handler.create_models(message)

        # Expected ChatTag
        # Message is a copy of m7, with changes to tagId, userId
        message = Message(tagCreateMessage=TagCreateMessage(tagId='4141decbb6f44471939149d6bc801777', name='Tag', tagReferenceId=None, minuteId='6350813013bd4472b9ef5366fca0b434'), minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-V2VkIEF1ZyAyMiAwNjo1ODoyNSBQRFQgMjAxMn4wLjg5Mjc3OTJ-', timestamp=1345643936.348819, route=MessageRoute(type=1, recipients=[]), userId=14, type=100, id='7f577979990945efa0b41ab887155a1d'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=None, whiteboardCreatePathMessage=None)
        expected_tag2 = ChatTag(
            user_id=message.header.userId,
            chat_minute=chat_minute,
            tag_id=message.tagCreateMessage.tagReferenceId,
            name=message.tagCreateMessage.name,
            deleted=False)

        # Create the real ChatTag
        tag_handler.create_models(message)

        # Retrieve created models
        created_tags = tag_handler.finalize()
        self.assertEqual(2, len(created_tags))
        self.assertIsNotNone(created_tags[0])
        self.assertIsNotNone(created_tags[1])

        actual_tag1 = created_tags[0]
        actual_tag2 = created_tags[1]

        # Compare output to expected values
        self.assertEqual(expected_tag1.user_id, actual_tag1.user_id)
        self.assertEqual(expected_tag1.chat_minute, actual_tag1.chat_minute)
        self.assertEqual(expected_tag1.tag_id, actual_tag1.tag_id)
        self.assertEqual(expected_tag1.name, actual_tag1.name)
        self.assertEqual(expected_tag1.deleted, actual_tag1.deleted)

        # Compare output to expected values
        self.assertEqual(expected_tag2.user_id, actual_tag2.user_id)
        self.assertEqual(expected_tag2.chat_minute, actual_tag2.chat_minute)
        self.assertEqual(expected_tag2.tag_id, actual_tag2.tag_id)
        self.assertEqual(expected_tag2.name, actual_tag2.name)
        self.assertEqual(expected_tag2.deleted, actual_tag2.deleted)

    def test_updateModels(self):

        # Get chat data
        chat_data = self.test_chat_datasets[1]

        # Create ChatTagHandler
        message_handler = ChatMessageHandler(chat_data.chat_session_id, chat_data.topic_collection)
        tag_handler = message_handler.chat_tag_handler

        message = chat_data.message_list[6]
        with self.assertRaises(NotImplementedError):
            tag_handler.update_models(message)

    def test_deleteModels(self):

        # Get chat data
        chat_data = self.test_chat_datasets[1]
        chat_minute = chat_data.expected_minute_models[1]

        # Create ChatTagHandler
        message_handler = ChatMessageHandler(chat_data.chat_session_id, chat_data.topic_collection)
        message_handler.chat_minute_handler._set_active_minute(chat_minute)
        tag_handler = message_handler.chat_tag_handler

        # Create the real ChatTag
        tag_create_message = chat_data.message_list[7]
        tag_handler.create_models(tag_create_message)

        # Delete the ChatTag
        tag_delete_message = chat_data.message_list[8]
        tag_handler.delete_models(tag_delete_message)

        created_tags = tag_handler.finalize()
        self.assertEqual(0, len(created_tags))

    def test_deleteModels_invalidTagID(self):

        # Get chat data
        chat_data = self.test_chat_datasets[1]
        chat_minute = chat_data.expected_minute_models[1]

        # Create ChatTagHandler
        message_handler = ChatMessageHandler(chat_data.chat_session_id, chat_data.topic_collection)
        message_handler.chat_minute_handler._set_active_minute(chat_minute)
        tag_handler = message_handler.chat_tag_handler

        message = chat_data.message_list[8]
        with self.assertRaises(TagIdDoesNotExistException):
            tag_handler.delete_models(message)

    def test_deleteModels_doubleDelete(self):

        # Get chat data
        chat_data = self.test_chat_datasets[1]
        chat_minute = chat_data.expected_minute_models[1]

        # Create ChatTagHandler
        message_handler = ChatMessageHandler(chat_data.chat_session_id, chat_data.topic_collection)
        message_handler.chat_minute_handler._set_active_minute(chat_minute)
        tag_handler = message_handler.chat_tag_handler

        # Create the real ChatTag
        tag_create_message = chat_data.message_list[7]
        tag_handler.create_models(tag_create_message)

        # Delete the ChatTag
        tag_delete_message = chat_data.message_list[8]
        tag_handler.delete_models(tag_delete_message)

        # Delete the tag again
        # Should silently fail
        tag_handler.delete_models(tag_delete_message)

        created_tags = tag_handler.finalize()
        self.assertEqual(0, len(created_tags))


if __name__ == '__main__':
    unittest.main()
