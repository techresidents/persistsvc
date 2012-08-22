
import os
import sys
import unittest

from trchatsvc.gen.ttypes import Message, MessageHeader, MessageRoute,\
    Marker, MarkerCreateMessage, JoinedMarker, ConnectedMarker,\
    WhiteboardCreateMessage,\
    MinuteCreateMessage, MinuteUpdateMessage, \
    TagCreateMessage, TagDeleteMessage,\
    StartedMarker, EndedMarker
from trsvcscore.db.models import ChatMinute, ChatSpeakingMarker, ChatTag

SERVICE_NAME = "persistsvc"

#Add SERVICE_ROOT to python path, for imports.
SERVICE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../", SERVICE_NAME))
sys.path.insert(0, SERVICE_ROOT)

from message_handler import ChatMessageHandler, ChatTagHandler
from testbase import IntegrationTestCase


class ChatTagHandlerTest(IntegrationTestCase):
    """
        Test the ChatTagHandler class
    """

    @classmethod
    def setUpClass(cls):

        IntegrationTestCase.setUpClass()

        chat_session_id = 29
        db_session = cls.service.handler.get_database_session()
        message_handler = ChatMessageHandler(db_session, chat_session_id)
        cls.tag_handler = message_handler.chat_tag_handler

        # Chat #1
        Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-V2VkIEF1ZyAyMiAwNjo1ODoyNSBQRFQgMjAxMn4wLjg5Mjc3OTJ-', timestamp=1345643917.544588, route=MessageRoute(type=0, recipients=[]), userId=13, type=400, id='b64efda139224cdc9e8b2248fdf49117'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=None, connectedMarker=None, endedMarker=None, joinedMarker=JoinedMarker(userId=13, name='brian'), startedMarker=None, type=0), markerId='68819105102c4fdd8dffcce983d34f76'), whiteboardCreatePathMessage=None)
        Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-V2VkIEF1ZyAyMiAwNjo1ODoyNSBQRFQgMjAxMn4wLjg5Mjc3OTJ-', timestamp=1345643917.847823, route=MessageRoute(type=1, recipients=[]), userId=13, type=200, id='096a9f1f54984e079ef45c3f07f21ed3'), tagDeleteMessage=None, whiteboardCreateMessage=WhiteboardCreateMessage(name='Default Whiteboard', whiteboardId='d74b1bd64a4a48909e3c727299b7ab8c'), whiteboardDeleteMessage=None, markerCreateMessage=None, whiteboardCreatePathMessage=None)
        Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-V2VkIEF1ZyAyMiAwNjo1ODoyNSBQRFQgMjAxMn4wLjg5Mjc3OTJ-', timestamp=1345643921.425069, route=MessageRoute(type=0, recipients=[]), userId=13, type=400, id='6a683f85bcf54ce0a1fad423317a030b'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=None, connectedMarker=ConnectedMarker(userId=13, isConnected=True), endedMarker=None, joinedMarker=None, startedMarker=None, type=1), markerId='9acbd831c59e4461b58d6218d68443ef'), whiteboardCreatePathMessage=None)
        Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=MinuteCreateMessage(topicId=1, startTimestamp=1345643927, endTimestamp=None, minuteId='6a0a875dcdce49b9a86e757376d34615'), header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-V2VkIEF1ZyAyMiAwNjo1ODoyNSBQRFQgMjAxMn4wLjg5Mjc3OTJ-', timestamp=1345643927.795392, route=MessageRoute(type=1, recipients=[]), userId=13, type=300, id='e6dd1585f3524ed7b4910cee4abc808a'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=None, whiteboardCreatePathMessage=None)
        Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=MinuteCreateMessage(topicId=2, startTimestamp=1345643927, endTimestamp=None, minuteId='6350813013bd4472b9ef5366fca0b434'), header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-V2VkIEF1ZyAyMiAwNjo1ODoyNSBQRFQgMjAxMn4wLjg5Mjc3OTJ-', timestamp=1345643927.803031, route=MessageRoute(type=1, recipients=[]), userId=13, type=300, id='b8fd5a57657e4ae5bb77ed8f691193ea'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=None, whiteboardCreatePathMessage=None)
        Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-V2VkIEF1ZyAyMiAwNjo1ODoyNSBQRFQgMjAxMn4wLjg5Mjc3OTJ-', timestamp=1345643927.934734, route=MessageRoute(type=0, recipients=[]), userId=13, type=400, id='2d344bec420c4b11a4f7bdb2d63de2a4'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=None, connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=StartedMarker(userId=13), type=4), markerId='652270426d064f4da8069d7f5f39846e'), whiteboardCreatePathMessage=None)
        Message(tagCreateMessage=TagCreateMessage(tagId='4141decbb6f44471939149d6bc801700', name='Tag', tagReferenceId=None, minuteId='6350813013bd4472b9ef5366fca0b434'), minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-V2VkIEF1ZyAyMiAwNjo1ODoyNSBQRFQgMjAxMn4wLjg5Mjc3OTJ-', timestamp=1345643936.348819, route=MessageRoute(type=1, recipients=[]), userId=13, type=100, id='7f577979990945efa0b41ab887155a1d'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=None, whiteboardCreatePathMessage=None)
        Message(tagCreateMessage=TagCreateMessage(tagId='80821d7947a545aa86b3ef4400a4749c', name='deletedTag', tagReferenceId=None, minuteId='6350813013bd4472b9ef5366fca0b434'), minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-V2VkIEF1ZyAyMiAwNjo1ODoyNSBQRFQgMjAxMn4wLjg5Mjc3OTJ-', timestamp=1345643943.648114, route=MessageRoute(type=1, recipients=[]), userId=13, type=100, id='13a5a7d1eaad469a8bb8603ee580b3e1'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=None, whiteboardCreatePathMessage=None)
        Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-V2VkIEF1ZyAyMiAwNjo1ODoyNSBQRFQgMjAxMn4wLjg5Mjc3OTJ-', timestamp=1345643948.168495, route=MessageRoute(type=1, recipients=[]), userId=13, type=101, id='79e315e656fd4d56b348ea7472412ab5'), tagDeleteMessage=TagDeleteMessage(tagId='80821d7947a545aa86b3ef4400a4749c'), whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=None, whiteboardCreatePathMessage=None)
        Message(tagCreateMessage=TagCreateMessage(tagId='b5e8a3b469e04fd883a2c9ee9f527e1b', name='duplicate tag', tagReferenceId=None, minuteId='6350813013bd4472b9ef5366fca0b434'), minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-V2VkIEF1ZyAyMiAwNjo1ODoyNSBQRFQgMjAxMn4wLjg5Mjc3OTJ-', timestamp=1345643953.358221, route=MessageRoute(type=1, recipients=[]), userId=13, type=100, id='667e7f48a9f74058a26445e283c3482c'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=None, whiteboardCreatePathMessage=None)
        Message(tagCreateMessage=TagCreateMessage(tagId='35ffbbc263fe41879b83df27a328f3c2', name='duplicate tag', tagReferenceId=None, minuteId='6350813013bd4472b9ef5366fca0b434'), minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-V2VkIEF1ZyAyMiAwNjo1ODoyNSBQRFQgMjAxMn4wLjg5Mjc3OTJ-', timestamp=1345643957.397479, route=MessageRoute(type=1, recipients=[]), userId=13, type=100, id='b24bbcc26432461bb72b70823dcbf67e'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=None, whiteboardCreatePathMessage=None)
        Message(tagCreateMessage=None, minuteUpdateMessage=MinuteUpdateMessage(topicId=2, startTimestamp=1345643927, endTimestamp=1345643963, minuteId='6350813013bd4472b9ef5366fca0b434'), whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-V2VkIEF1ZyAyMiAwNjo1ODoyNSBQRFQgMjAxMn4wLjg5Mjc3OTJ-', timestamp=1345643963.615939, route=MessageRoute(type=1, recipients=[]), userId=13, type=301, id='719ced197ae94e75b1cbde6881fa79de'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=None, whiteboardCreatePathMessage=None)
        Message(tagCreateMessage=None, minuteUpdateMessage=MinuteUpdateMessage(topicId=1, startTimestamp=1345643927, endTimestamp=1345643963, minuteId='6a0a875dcdce49b9a86e757376d34615'), whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-V2VkIEF1ZyAyMiAwNjo1ODoyNSBQRFQgMjAxMn4wLjg5Mjc3OTJ-', timestamp=1345643963.650789, route=MessageRoute(type=1, recipients=[]), userId=13, type=301, id='6a0cbc29819547a895c53e2d7e0f61be'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=None, whiteboardCreatePathMessage=None)
        Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-V2VkIEF1ZyAyMiAwNjo1ODoyNSBQRFQgMjAxMn4wLjg5Mjc3OTJ-', timestamp=1345643964.04311, route=MessageRoute(type=0, recipients=[]), userId=13, type=400, id='c375ef54d7774768bb1c888478b4b906'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=None, connectedMarker=None, endedMarker=EndedMarker(userId=13), joinedMarker=None, startedMarker=None, type=5), markerId='4c862ffda41c4925be232a6fcb6fda26'), whiteboardCreatePathMessage=None)

    @classmethod
    def tearDownClass(cls):
        IntegrationTestCase.tearDownClass()

    def test_createModels(self):
        pass

    def test_updateModels(self):
        pass

    def test_deleteModels(self):
        pass

    def test_isDuplicateTag(self):
        pass


if __name__ == '__main__':
    unittest.main()
