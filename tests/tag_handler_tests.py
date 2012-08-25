
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

        IntegrationTestCase.setUpClass()

        # Data required to construct a ChatMessageHandler
        topic_data = TopicTestDataSets()
        test_topic_datasets = topic_data.get_list()
        cls.topic_collection = test_topic_datasets[0].topic_collection
        cls.chat_session_id = 27 # Random ID
        cls.db_session = cls.service.handler.get_database_session()

        # Deserialized Chat Messages from real Chat
        # Root
        #   T1
        m1 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-V2VkIEF1ZyAyMiAwNjo1ODoyNSBQRFQgMjAxMn4wLjg5Mjc3OTJ-', timestamp=1345643917.544588, route=MessageRoute(type=0, recipients=[]), userId=13, type=400, id='b64efda139224cdc9e8b2248fdf49117'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=None, connectedMarker=None, endedMarker=None, joinedMarker=JoinedMarker(userId=13, name='brian'), startedMarker=None, type=0), markerId='68819105102c4fdd8dffcce983d34f76'), whiteboardCreatePathMessage=None)
        m2 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-V2VkIEF1ZyAyMiAwNjo1ODoyNSBQRFQgMjAxMn4wLjg5Mjc3OTJ-', timestamp=1345643917.847823, route=MessageRoute(type=1, recipients=[]), userId=13, type=200, id='096a9f1f54984e079ef45c3f07f21ed3'), tagDeleteMessage=None, whiteboardCreateMessage=WhiteboardCreateMessage(name='Default Whiteboard', whiteboardId='d74b1bd64a4a48909e3c727299b7ab8c'), whiteboardDeleteMessage=None, markerCreateMessage=None, whiteboardCreatePathMessage=None)
        m3 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-V2VkIEF1ZyAyMiAwNjo1ODoyNSBQRFQgMjAxMn4wLjg5Mjc3OTJ-', timestamp=1345643921.425069, route=MessageRoute(type=0, recipients=[]), userId=13, type=400, id='6a683f85bcf54ce0a1fad423317a030b'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=None, connectedMarker=ConnectedMarker(userId=13, isConnected=True), endedMarker=None, joinedMarker=None, startedMarker=None, type=1), markerId='9acbd831c59e4461b58d6218d68443ef'), whiteboardCreatePathMessage=None)
        m4 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=MinuteCreateMessage(topicId=1, startTimestamp=1345643927, endTimestamp=None, minuteId='6a0a875dcdce49b9a86e757376d34615'), header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-V2VkIEF1ZyAyMiAwNjo1ODoyNSBQRFQgMjAxMn4wLjg5Mjc3OTJ-', timestamp=1345643927.795392, route=MessageRoute(type=1, recipients=[]), userId=13, type=300, id='e6dd1585f3524ed7b4910cee4abc808a'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=None, whiteboardCreatePathMessage=None)
        m5 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=MinuteCreateMessage(topicId=2, startTimestamp=1345643927, endTimestamp=None, minuteId='6350813013bd4472b9ef5366fca0b434'), header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-V2VkIEF1ZyAyMiAwNjo1ODoyNSBQRFQgMjAxMn4wLjg5Mjc3OTJ-', timestamp=1345643927.803031, route=MessageRoute(type=1, recipients=[]), userId=13, type=300, id='b8fd5a57657e4ae5bb77ed8f691193ea'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=None, whiteboardCreatePathMessage=None)
        m6 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-V2VkIEF1ZyAyMiAwNjo1ODoyNSBQRFQgMjAxMn4wLjg5Mjc3OTJ-', timestamp=1345643927.934734, route=MessageRoute(type=0, recipients=[]), userId=13, type=400, id='2d344bec420c4b11a4f7bdb2d63de2a4'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=None, connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=StartedMarker(userId=13), type=4), markerId='652270426d064f4da8069d7f5f39846e'), whiteboardCreatePathMessage=None)
        cls.m7 = Message(tagCreateMessage=TagCreateMessage(tagId='4141decbb6f44471939149d6bc801700', name='Tag', tagReferenceId=None, minuteId='6350813013bd4472b9ef5366fca0b434'), minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-V2VkIEF1ZyAyMiAwNjo1ODoyNSBQRFQgMjAxMn4wLjg5Mjc3OTJ-', timestamp=1345643936.348819, route=MessageRoute(type=1, recipients=[]), userId=13, type=100, id='7f577979990945efa0b41ab887155a1d'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=None, whiteboardCreatePathMessage=None)
        cls.m8 = Message(tagCreateMessage=TagCreateMessage(tagId='80821d7947a545aa86b3ef4400a4749c', name='deletedTag', tagReferenceId=None, minuteId='6350813013bd4472b9ef5366fca0b434'), minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-V2VkIEF1ZyAyMiAwNjo1ODoyNSBQRFQgMjAxMn4wLjg5Mjc3OTJ-', timestamp=1345643943.648114, route=MessageRoute(type=1, recipients=[]), userId=13, type=100, id='13a5a7d1eaad469a8bb8603ee580b3e1'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=None, whiteboardCreatePathMessage=None)
        cls.m9 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-V2VkIEF1ZyAyMiAwNjo1ODoyNSBQRFQgMjAxMn4wLjg5Mjc3OTJ-', timestamp=1345643948.168495, route=MessageRoute(type=1, recipients=[]), userId=13, type=101, id='79e315e656fd4d56b348ea7472412ab5'), tagDeleteMessage=TagDeleteMessage(tagId='80821d7947a545aa86b3ef4400a4749c'), whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=None, whiteboardCreatePathMessage=None)
        cls.m10 = Message(tagCreateMessage=TagCreateMessage(tagId='b5e8a3b469e04fd883a2c9ee9f527e1b', name='duplicate tag', tagReferenceId=None, minuteId='6350813013bd4472b9ef5366fca0b434'), minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-V2VkIEF1ZyAyMiAwNjo1ODoyNSBQRFQgMjAxMn4wLjg5Mjc3OTJ-', timestamp=1345643953.358221, route=MessageRoute(type=1, recipients=[]), userId=13, type=100, id='667e7f48a9f74058a26445e283c3482c'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=None, whiteboardCreatePathMessage=None)
        cls.m11 = Message(tagCreateMessage=TagCreateMessage(tagId='35ffbbc263fe41879b83df27a328f3c2', name='duplicate tag', tagReferenceId=None, minuteId='6350813013bd4472b9ef5366fca0b434'), minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-V2VkIEF1ZyAyMiAwNjo1ODoyNSBQRFQgMjAxMn4wLjg5Mjc3OTJ-', timestamp=1345643957.397479, route=MessageRoute(type=1, recipients=[]), userId=13, type=100, id='b24bbcc26432461bb72b70823dcbf67e'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=None, whiteboardCreatePathMessage=None)
        m12 = Message(tagCreateMessage=None, minuteUpdateMessage=MinuteUpdateMessage(topicId=2, startTimestamp=1345643927, endTimestamp=1345643963, minuteId='6350813013bd4472b9ef5366fca0b434'), whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-V2VkIEF1ZyAyMiAwNjo1ODoyNSBQRFQgMjAxMn4wLjg5Mjc3OTJ-', timestamp=1345643963.615939, route=MessageRoute(type=1, recipients=[]), userId=13, type=301, id='719ced197ae94e75b1cbde6881fa79de'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=None, whiteboardCreatePathMessage=None)
        m13 = Message(tagCreateMessage=None, minuteUpdateMessage=MinuteUpdateMessage(topicId=1, startTimestamp=1345643927, endTimestamp=1345643963, minuteId='6a0a875dcdce49b9a86e757376d34615'), whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-V2VkIEF1ZyAyMiAwNjo1ODoyNSBQRFQgMjAxMn4wLjg5Mjc3OTJ-', timestamp=1345643963.650789, route=MessageRoute(type=1, recipients=[]), userId=13, type=301, id='6a0cbc29819547a895c53e2d7e0f61be'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=None, whiteboardCreatePathMessage=None)
        m14 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-V2VkIEF1ZyAyMiAwNjo1ODoyNSBQRFQgMjAxMn4wLjg5Mjc3OTJ-', timestamp=1345643964.04311, route=MessageRoute(type=0, recipients=[]), userId=13, type=400, id='c375ef54d7774768bb1c888478b4b906'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=None, connectedMarker=None, endedMarker=EndedMarker(userId=13), joinedMarker=None, startedMarker=None, type=5), markerId='4c862ffda41c4925be232a6fcb6fda26'), whiteboardCreatePathMessage=None)
        cls.chat1 = [m1, m2, m3, m4, m5, m6, cls.m7, cls.m8, cls.m9, cls.m10, cls.m11, m12, m13, m14]


        # Chat1 parent topic minute
        cls.parent_chat_minute = ChatMinute(
            chat_session_id=cls.chat_session_id,
            topic_id=1,
            start=tz.timestamp_to_utc(1345643927),
            end = tz.timestamp_to_utc(1345643963))

        # Chat1 leaf topic minute
        cls.chat_minute = ChatMinute(
            chat_session_id=cls.chat_session_id,
            topic_id=2,
            start=tz.timestamp_to_utc(1345643927),
            end = tz.timestamp_to_utc(1345643963))

        # Dummy Chat Minute
        cls.dummy_chat_minute = ChatMinute(
            chat_session_id=cls.chat_session_id,
            topic_id=777777,
            start=tz.timestamp_to_utc(1345643963),
            end = tz.timestamp_to_utc(1345643999))


    @classmethod
    def tearDownClass(cls):
        IntegrationTestCase.tearDownClass()


    def test_chatMessageHandler(self):

        # Create ChatTagHandler
        message_handler = ChatMessageHandler(self.chat_session_id, self.topic_collection)

        # Specify the tags expected to be persisted
        persisted_tag_messages = [self.m7, self.m10]
        expected_tag_models = []
        for message in persisted_tag_messages:
            expected_tag = ChatTag(
                user_id=message.header.userId,
                chat_minute=self.chat_minute, #placeholder chat minute
                tag_id=message.tagCreateMessage.tagReferenceId,
                name=message.tagCreateMessage.name,
                deleted=False)
            expected_tag_models.append(expected_tag)

        # Process messages
        for deserialized_msg in self.chat1:
            message_handler.process(deserialized_msg)

        # Retrieve all chat tag models
        tag_models = message_handler.chat_tag_handler.finalize()

        # Compare output to expected values
        for (counter, actual_tag) in enumerate(tag_models):
            # counter values start at 0
            fail_msg = 'Failed with loop counter=%d' % counter
            self.assertEqual(expected_tag_models[counter].user_id, actual_tag.user_id, fail_msg)
            #self.assertEqual(expected_tag_models[counter].chat_minute, actual_tag.chat_minute, fail_msg) TODO
            self.assertEqual(expected_tag_models[counter].tag_id, actual_tag.tag_id, fail_msg)
            self.assertEqual(expected_tag_models[counter].name, actual_tag.name, fail_msg)
            self.assertEqual(expected_tag_models[counter].deleted, actual_tag.deleted, fail_msg)

    def test_createModels_singleTag(self):

        # Create ChatTagHandler
        message_handler = ChatMessageHandler(self.chat_session_id, self.topic_collection)
        message_handler.chat_minute_handler._set_active_minute(self.chat_minute)
        tag_handler = message_handler.chat_tag_handler

        # Expected ChatTag
        message = self.m7
        expected_tag = ChatTag(
            user_id=message.header.userId,
            chat_minute=self.chat_minute,
            tag_id=message.tagCreateMessage.tagReferenceId,
            name=message.tagCreateMessage.name,
            deleted=False)

        # Create the real ChatTag
        tag_handler.create_models(message)
        created_tags = tag_handler.finalize()
        self.assertEqual(1, len(created_tags))
        actual_tag = created_tags[0]

        # Compare output to expected values
        #self.assertEqual(expected_tag, actual_tag) # TODO why fails?
        self.assertEqual(expected_tag.user_id, actual_tag.user_id)
        self.assertEqual(expected_tag.chat_minute, actual_tag.chat_minute)
        self.assertEqual(expected_tag.tag_id, actual_tag.tag_id)
        self.assertEqual(expected_tag.name, actual_tag.name)
        self.assertEqual(expected_tag.deleted, actual_tag.deleted)

    def test_createModels_duplicateTags(self):

        # Create ChatTagHandler
        message_handler = ChatMessageHandler(self.chat_session_id, self.topic_collection)
        message_handler.chat_minute_handler._set_active_minute(self.chat_minute)
        tag_handler = message_handler.chat_tag_handler

        # Expected ChatTag
        message = self.m7
        expected_tag = ChatTag(
            user_id=message.header.userId,
            chat_minute=self.chat_minute,
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
        print created_tags
        self.assertEqual(1, len(created_tags))
        actual_tag = created_tags[0]

        # Compare output to expected values
        self.assertEqual(expected_tag.user_id, actual_tag.user_id)
        self.assertEqual(expected_tag.chat_minute, actual_tag.chat_minute)
        self.assertEqual(expected_tag.tag_id, actual_tag.tag_id)
        self.assertEqual(expected_tag.name, actual_tag.name)
        self.assertEqual(expected_tag.deleted, actual_tag.deleted)

    def test_createModels_noActiveChatMinute(self):

        # Create ChatTagHandler
        message_handler = ChatMessageHandler(self.chat_session_id, self.topic_collection)
        message_handler.chat_minute_handler._set_active_minute(None)
        tag_handler = message_handler.chat_tag_handler

        # Test create_models
        message = self.m7
        with self.assertRaises(NoActiveChatMinuteException):
            tag_handler.create_models(message)

        # Test delete_models
        message = self.m9
        with self.assertRaises(NoActiveChatMinuteException):
            tag_handler.delete_models(message)

    def test_createModels_sameUserSameTagNameDifferentMinute(self):

        # Create ChatTagHandler
        message_handler = ChatMessageHandler(self.chat_session_id, self.topic_collection)
        tag_handler = message_handler.chat_tag_handler

        # Expected ChatTag
        message = self.m10
        expected_tag1 = ChatTag(
            user_id=message.header.userId,
            chat_minute=self.chat_minute,
            tag_id=message.tagCreateMessage.tagReferenceId,
            name=message.tagCreateMessage.name,
            deleted=False)

        # Create the real ChatTag
        message_handler.chat_minute_handler._set_active_minute(self.chat_minute)
        tag_handler.create_models(message)

        # Expected ChatTag
        message = self.m11
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

        # Create ChatTagHandler
        message_handler = ChatMessageHandler(self.chat_session_id, self.topic_collection)
        tag_handler = message_handler.chat_tag_handler

        # Expected ChatTag
        message = self.m7
        expected_tag1 = ChatTag(
            user_id=message.header.userId,
            chat_minute=self.chat_minute,
            tag_id=message.tagCreateMessage.tagReferenceId,
            name=message.tagCreateMessage.name,
            deleted=False)

        # Create the real ChatTag
        message_handler.chat_minute_handler._set_active_minute(self.chat_minute)
        tag_handler.create_models(message)

        # Expected ChatTag
        message = self.m8
        expected_tag2 = ChatTag(
            user_id=message.header.userId,
            chat_minute=self.chat_minute,
            tag_id=message.tagCreateMessage.tagReferenceId,
            name=message.tagCreateMessage.name,
            deleted=False)

        # Create the real ChatTag
        message_handler.chat_minute_handler._set_active_minute(self.chat_minute)
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

        # Create ChatTagHandler
        message_handler = ChatMessageHandler(self.chat_session_id, self.topic_collection)
        tag_handler = message_handler.chat_tag_handler

        # Expected ChatTag
        message = self.m7
        expected_tag1 = ChatTag(
            user_id=message.header.userId,
            chat_minute=self.chat_minute,
            tag_id=message.tagCreateMessage.tagReferenceId,
            name=message.tagCreateMessage.name,
            deleted=False)

        # Create the real ChatTag
        message_handler.chat_minute_handler._set_active_minute(self.chat_minute)
        tag_handler.create_models(message)

        # Expected ChatTag
        # Copy m7, change tagId, userId
        message = Message(tagCreateMessage=TagCreateMessage(tagId='4141decbb6f44471939149d6bc801777', name='Tag', tagReferenceId=None, minuteId='6350813013bd4472b9ef5366fca0b434'), minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-V2VkIEF1ZyAyMiAwNjo1ODoyNSBQRFQgMjAxMn4wLjg5Mjc3OTJ-', timestamp=1345643936.348819, route=MessageRoute(type=1, recipients=[]), userId=14, type=100, id='7f577979990945efa0b41ab887155a1d'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=None, whiteboardCreatePathMessage=None)
        expected_tag2 = ChatTag(
            user_id=message.header.userId,
            chat_minute=self.chat_minute,
            tag_id=message.tagCreateMessage.tagReferenceId,
            name=message.tagCreateMessage.name,
            deleted=False)

        # Create the real ChatTag
        message_handler.chat_minute_handler._set_active_minute(self.chat_minute)
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

        # Create ChatTagHandler
        message_handler = ChatMessageHandler(self.chat_session_id, self.topic_collection)
        tag_handler = message_handler.chat_tag_handler

        message = self.m7
        with self.assertRaises(NotImplementedError):
            tag_handler.update_models(message)

    def test_deleteModels(self):

        # Create ChatTagHandler
        message_handler = ChatMessageHandler(self.chat_session_id, self.topic_collection)
        message_handler.chat_minute_handler._set_active_minute(self.chat_minute)
        tag_handler = message_handler.chat_tag_handler

        # Create the real ChatTag
        tag_create_message = self.m8
        tag_handler.create_models(tag_create_message)

        # Delete the ChatTag
        tag_delete_message = self.m9
        tag_handler.delete_models(tag_delete_message)

        created_tags = tag_handler.finalize()
        self.assertEqual(0, len(created_tags))

    def test_deleteModels_invalidTagID(self):

        # Create ChatTagHandler
        message_handler = ChatMessageHandler(self.chat_session_id, self.topic_collection)
        message_handler.chat_minute_handler._set_active_minute(self.chat_minute)
        tag_handler = message_handler.chat_tag_handler

        message = self.m9
        with self.assertRaises(TagIdDoesNotExistException):
            tag_handler.delete_models(message)

    def test_deleteModels_doubleDelete(self):

        # Create ChatTagHandler
        message_handler = ChatMessageHandler(self.chat_session_id, self.topic_collection)
        message_handler.chat_minute_handler._set_active_minute(self.chat_minute)
        tag_handler = message_handler.chat_tag_handler

        # Create the real ChatTag
        tag_create_message = self.m8
        tag_handler.create_models(tag_create_message)

        # Delete the ChatTag
        tag_delete_message = self.m9
        tag_handler.delete_models(tag_delete_message)

        # Delete the tag again
        # Should silently fail
        tag_handler.delete_models(tag_delete_message)

        created_tags = tag_handler.finalize()
        self.assertEqual(0, len(created_tags))


if __name__ == '__main__':
    unittest.main()
