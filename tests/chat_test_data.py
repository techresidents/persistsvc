import os
import sys
import uuid

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../persistsvc"))
sys.path.insert(0, PROJECT_ROOT)


from trchatsvc.gen.ttypes import Message, MessageHeader, MessageRoute,\
    Marker, MarkerCreateMessage, \
    JoinedMarker, ConnectedMarker,\
    SpeakingMarker,PublishingMarker,\
    StartedMarker, EndedMarker,\
    WhiteboardCreateMessage,\
    MinuteCreateMessage, MinuteUpdateMessage,\
    TagCreateMessage, TagDeleteMessage
from trpycore.thrift.serialization import serialize
from trpycore.timezone import tz
from trsvcscore.db.models import ChatMessage, ChatMinute, ChatSpeakingMarker, ChatTag

from topic_data_manager import TopicDataCollection, TopicData
from topic_test_data import TopicTestDataSets




class ChatTestDataBuilder(object):
    """
        Class to generate chat data for testing.
        All generated data has the following chat topic hierarchy:
            - Root
            --- Topic1
        All generated data assumes one user in the chat.

        This class was created to facilitate tests that require
        writing ChatMessages and ChatPersistJobs to the database.
        The data in the ChatTestDataSets class has hard coded
        database IDs for things like Topics, Users, and ChatSessions
        which means it couldn't be used to actually write the data
        to the database. These values are parameterized in this class.
    """

    def __init__(self):

        # Get the topic collection that matches a topic hierarchy of
        # Root
        #    Topic1
        #
        topic_data = TopicTestDataSets().get_list()
        self.topic_collection = topic_data[4].topic_collection


    def build(self, root_topic_id, topic1_id, chat_session_id, chat_session_token, user_id):
        """
            Generate chat data

            Args:
                root_topic_id: The root topic's database ID
                topic1_id: Topic1's database ID
                chat_session_id: The database ID of the ChatSession the generated chat should use
                chat_session_token: The chat session token the generated chat should use
                user_id: The user ID the generated chat should use

            Returns:
                Returns a ChatTestData object
        """

        deserialized_message_list = self.get_deserialized_messages(root_topic_id, topic1_id, chat_session_token, user_id)
        serialized_message_list = self.get_serialized_messages(deserialized_message_list, chat_session_id)
        expected_minute_models = self.get_expected_minute_models(root_topic_id, topic1_id, chat_session_id)
        expected_marker_models = self.get_expected_marker_models(user_id, expected_minute_models)
        expected_tag_models = self.get_expected_tag_models(deserialized_message_list, expected_minute_models)

        return ChatTestData(
            chat_session_id,
            chat_session_token,
            deserialized_message_list,
            serialized_message_list,
            self.topic_collection,
            expected_minute_models,
            expected_marker_models,
            expected_tag_models
        )

    def get_deserialized_messages(self, root_topic_id, topic1_id, chat_session_token, user_id):
        """
            Args:
                root_topic_id: The root topic's database ID
                topic1_id: Topic1's database ID
                chat_session_token: The chat session token the generated messages should use
                user_id: The user ID the generated chat should use

            Returns:
                Return list of deserialized Thrift Messages
        """

        m0 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken=chat_session_token, timestamp=1345643917.544588, route=MessageRoute(type=0, recipients=[]), userId=user_id, type=400, id='b64efda139224cdc9e8b2248fdf49117'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=None, connectedMarker=None, endedMarker=None, joinedMarker=JoinedMarker(userId=user_id, name='brian'), startedMarker=None, type=0), markerId='68819105102c4fdd8dffcce983d34f76'), whiteboardCreatePathMessage=None)
        m1 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken=chat_session_token, timestamp=1345643917.847823, route=MessageRoute(type=1, recipients=[]), userId=user_id, type=200, id='096a9f1f54984e079ef45c3f07f21ed3'), tagDeleteMessage=None, whiteboardCreateMessage=WhiteboardCreateMessage(name='Default Whiteboard', whiteboardId='d74b1bd64a4a48909e3c727299b7ab8c'), whiteboardDeleteMessage=None, markerCreateMessage=None, whiteboardCreatePathMessage=None)
        m2 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken=chat_session_token, timestamp=1345643921.425069, route=MessageRoute(type=0, recipients=[]), userId=user_id, type=400, id='6a683f85bcf54ce0a1fad423317a030b'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=None, connectedMarker=ConnectedMarker(userId=user_id, isConnected=True), endedMarker=None, joinedMarker=None, startedMarker=None, type=1), markerId='9acbd831c59e4461b58d6218d68443ef'), whiteboardCreatePathMessage=None)
        m3 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=MinuteCreateMessage(topicId=root_topic_id, startTimestamp=1345643927, endTimestamp=None, minuteId='6a0a875dcdce49b9a86e757376d34615'), header=MessageHeader(chatSessionToken=chat_session_token, timestamp=1345643927.795392, route=MessageRoute(type=1, recipients=[]), userId=user_id, type=300, id='e6dd1585f3524ed7b4910cee4abc808a'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=None, whiteboardCreatePathMessage=None)
        m4 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=MinuteCreateMessage(topicId=topic1_id, startTimestamp=1345643927, endTimestamp=None, minuteId='6350813013bd4472b9ef5366fca0b434'), header=MessageHeader(chatSessionToken=chat_session_token, timestamp=1345643927.803031, route=MessageRoute(type=1, recipients=[]), userId=user_id, type=300, id='b8fd5a57657e4ae5bb77ed8f691193ea'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=None, whiteboardCreatePathMessage=None)
        m5 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken=chat_session_token, timestamp=1345643927.934734, route=MessageRoute(type=0, recipients=[]), userId=user_id, type=400, id='2d344bec420c4b11a4f7bdb2d63de2a4'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=None, connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=StartedMarker(userId=user_id), type=4), markerId='652270426d064f4da8069d7f5f39846e'), whiteboardCreatePathMessage=None)

        # Tag related messages
        m6 = Message(tagCreateMessage=TagCreateMessage(tagId='4141decbb6f44471939149d6bc801700', name='Tag', tagReferenceId=None, minuteId='6350813013bd4472b9ef5366fca0b434'), minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken=chat_session_token, timestamp=1345643936.348819, route=MessageRoute(type=1, recipients=[]), userId=user_id, type=100, id='7f577979990945efa0b41ab887155a1d'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=None, whiteboardCreatePathMessage=None)
        m7 = Message(tagCreateMessage=TagCreateMessage(tagId='80821d7947a545aa86b3ef4400a4749c', name='deletedTag', tagReferenceId=None, minuteId='6350813013bd4472b9ef5366fca0b434'), minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken=chat_session_token, timestamp=1345643943.648114, route=MessageRoute(type=1, recipients=[]), userId=user_id, type=100, id='13a5a7d1eaad469a8bb8603ee580b3e1'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=None, whiteboardCreatePathMessage=None)
        m8 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken=chat_session_token, timestamp=1345643948.168495, route=MessageRoute(type=1, recipients=[]), userId=user_id, type=101, id='79e315e656fd4d56b348ea7472412ab5'), tagDeleteMessage=TagDeleteMessage(tagId='80821d7947a545aa86b3ef4400a4749c'), whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=None, whiteboardCreatePathMessage=None)
        m9 = Message(tagCreateMessage=TagCreateMessage(tagId='b5e8a3b469e04fd883a2c9ee9f527e1b', name='duplicate tag', tagReferenceId=None, minuteId='6350813013bd4472b9ef5366fca0b434'), minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken=chat_session_token, timestamp=1345643953.358221, route=MessageRoute(type=1, recipients=[]), userId=user_id, type=100, id='667e7f48a9f74058a26445e283c3482c'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=None, whiteboardCreatePathMessage=None)
        m10 = Message(tagCreateMessage=TagCreateMessage(tagId='35ffbbc263fe41879b83df27a328f3c2', name='duplicate tag', tagReferenceId=None, minuteId='6350813013bd4472b9ef5366fca0b434'), minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken=chat_session_token, timestamp=1345643957.397479, route=MessageRoute(type=1, recipients=[]), userId=user_id, type=100, id='b24bbcc26432461bb72b70823dcbf67e'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=None, whiteboardCreatePathMessage=None)

        m11 = Message(tagCreateMessage=None, minuteUpdateMessage=MinuteUpdateMessage(topicId=topic1_id, startTimestamp=1345643927, endTimestamp=1345643963, minuteId='6350813013bd4472b9ef5366fca0b434'), whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken=chat_session_token, timestamp=1345643963.615939, route=MessageRoute(type=1, recipients=[]), userId=user_id, type=301, id='719ced197ae94e75b1cbde6881fa79de'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=None, whiteboardCreatePathMessage=None)
        m12 = Message(tagCreateMessage=None, minuteUpdateMessage=MinuteUpdateMessage(topicId=root_topic_id, startTimestamp=1345643927, endTimestamp=1345643963, minuteId='6a0a875dcdce49b9a86e757376d34615'), whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken=chat_session_token, timestamp=1345643963.650789, route=MessageRoute(type=1, recipients=[]), userId=user_id, type=301, id='6a0cbc29819547a895c53e2d7e0f61be'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=None, whiteboardCreatePathMessage=None)
        m13 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken=chat_session_token, timestamp=1345643964.04311, route=MessageRoute(type=0, recipients=[]), userId=user_id, type=400, id='c375ef54d7774768bb1c888478b4b906'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=None, connectedMarker=None, endedMarker=EndedMarker(userId=user_id), joinedMarker=None, startedMarker=None, type=5), markerId='4c862ffda41c4925be232a6fcb6fda26'), whiteboardCreatePathMessage=None)
        chat = [m0, m1, m2, m3, m4, m5, m6, m7, m8, m9, m10, m11, m12, m13]

        return chat

    def get_serialized_messages(self, deserialized_msg_list, chat_session_id):
        """
            Args:
                deserialized_msg_list: list of deserialized Thrift Message objects
                chat_session_id: The database ID of the ChatSession the generated chat should use

            Returns:
                Return a list of ChatMessages
        """
        serialized_messages = []

        for deserialized_msg in deserialized_msg_list:
            data = serialize(deserialized_msg)
            message_type_id = self.getMessageTypeID(deserialized_msg)
            format_type_id = 2 # the db ID which represents message data formatted using THRIFT which is base-64 encoded
            chat_msg = ChatMessage(
                message_id=uuid.uuid4().hex, # Mimic the chat svc, assign randomID
                chat_session_id=chat_session_id,
                type_id=message_type_id,
                format_type_id=format_type_id,
                timestamp=tz.timestamp(),
                time=tz.utcnow(),
                data=data
            )
            serialized_messages.append(chat_msg)

        return serialized_messages

    def get_expected_minute_models(self, root_topic_id, topic1_id, chat_session_id):
        """
            Args:
                root_topic_id: The root topic's database ID
                topic1_id: Topic1's database ID
                chat_session_id: The database ID of the ChatSession the generated chat should use

            Returns:
                Returns list of ChatMinute models the PersistService should create
        """

        # Chat1 parent topic minute
        parent_chat_minute = ChatMinute(
            chat_session_id=chat_session_id,
            topic_id=root_topic_id,
            start=tz.timestamp_to_utc(1345643927),
            end = tz.timestamp_to_utc(1345643963))


        # Chat1 leaf topic minute
        leaf_chat_minute = ChatMinute(
            chat_session_id=chat_session_id,
            topic_id=topic1_id,
            start=tz.timestamp_to_utc(1345643927),
            end = tz.timestamp_to_utc(1345643963))

        # Return chat minute models ordered by topic rank
        return [parent_chat_minute, leaf_chat_minute]

    def get_expected_marker_models(self, user_id, expected_chat_minute_list):
        """
            Args:
                user_id: The user ID the generated chat used
                expected_chat_minute_list: The list of expected ChatMinute models

            Returns:
                Returns list of ChatSpeakingMarker models the PersistService should create
        """
        # No Chat Speaking Marker Models in this chat
        return []

    def get_expected_tag_models(self, deserialized_message_list, expected_chat_minute_list):
        """
            Args:
                deserialized_msg_list: The list of deserialized Thrift Messages the generated chat used
                expected_chat_minute_list: The list of expected ChatMinute models

            Returns:
                Returns list of ChatTag models the PersistService should create
        """

        expected_tag_models = []

        persisted_tag_messages = [deserialized_message_list[6], deserialized_message_list[9]]
        for message in persisted_tag_messages:
            expected_tag = ChatTag(
                user_id=message.header.userId,
                chat_minute=expected_chat_minute_list[1],
                tag_id=message.tagCreateMessage.tagReferenceId,
                name=message.tagCreateMessage.name,
                deleted=False)
            expected_tag_models.append(expected_tag)
        return expected_tag_models

    def getMessageTypeID(self, message):
        """
            Convenience function to determine a message's type.
            Args:
                message: deserialized Thrift Message
            Returns:
                The message type's db ID
        """
        # Map of message types to IDs in the db
        message_type_dict = {
            'MARKER_CREATE': 1,
            'MINUTE_CREATE': 2,
            'MINUTE_UPDATE': 3,
            'TAG_CREATE': 4,
            'TAG_DELETE': 5,
            'WHITEBOARD_CREATE': 6,
            'WHITEBOARD_DELETE': 7,
            'WHITEBOARD_CREATE_PATH': 8,
            'WHITEBOARD_DELETE_PATH': 9
        }
        ret = None
        if message.markerCreateMessage is not None:
            ret = message_type_dict['MARKER_CREATE']
        elif message.minuteCreateMessage is not None:
            ret = message_type_dict['MINUTE_CREATE']
        elif message.minuteUpdateMessage is not None:
            ret = message_type_dict['MINUTE_UPDATE']
        elif message.tagCreateMessage is not None:
            ret = message_type_dict['TAG_CREATE']
        elif message.tagDeleteMessage is not None:
            ret = message_type_dict['TAG_DELETE']
        elif message.whiteboardCreateMessage is not None:
            ret = message_type_dict['WHITEBOARD_CREATE']
        elif message.whiteboardDeleteMessage is not None:
            ret = message_type_dict['WHITEBOARD_DELETE']
        elif message.whiteboardCreatePathMessage is not None:
            ret = message_type_dict['WHITEBOARD_CREATE_PATH']
        elif message.whiteboardDeletePathMessage is not None:
            ret = message_type_dict['WHITEBOARD_DELETE_PATH']
        else:
            raise Exception("Can't retrieve message type ID for unknown message type")

        return ret





class ChatTestDataSets(object):
    """
        Convenience class to keep all created
        chat data in one place.

        This test data is meant to be used for
        in-memory tests.  It contains hard coded
        topic IDs and user IDs which will cause
        problems if written to the db.
    """

    def __init__(self):

        # Get Topic Data
        topic_data = TopicTestDataSets()
        test_topic_datasets = topic_data.get_list()

        #
        # Dataset #1
        # Topic Structure
        # Root
        #   Topic1
        #
        # No tag messages. Lots of speaking messages.
        #
        chat_session_id = 3200 # Random ID
        message_list = self.get_chat1_msgs()
        chat_session_token = message_list[0].header.chatSessionToken
        topic_collection = test_topic_datasets[4].topic_collection  # Get the topic collection that matches the captured chat messages
        expected_minute_models = self.get_chat1_expected_minute_models(chat_session_id)
        expected_marker_models = self.get_chat1_expected_marker_models(expected_minute_models)
        expected_tag_models = self.get_chat1_expected_tag_models(message_list, expected_minute_models)

        dataset1 = ChatTestData(
            chat_session_id,
            chat_session_token,
            message_list,
            None, # TODO Don't need a serialized msg list right now
            topic_collection,
            expected_minute_models,
            expected_marker_models,
            expected_tag_models
        )


        #
        # Dataset #2
        # Topic structure
        # Root
        #   Topic1
        #
        # No speaking messages. Lots of tag messages.
        #
        chat_session_id = 243 # Random ID
        message_list = self.get_chat2_msgs()
        chat_session_token = message_list[0].header.chatSessionToken
        topic_collection = test_topic_datasets[4].topic_collection  # Get the topic collection that matches the captured chat messages
        expected_minute_models = self.get_chat2_expected_minute_models(chat_session_id)
        expected_marker_models = self.get_chat2_expected_marker_models(expected_minute_models)
        expected_tag_models = self.get_chat2_expected_tag_models(message_list, expected_minute_models)

        dataset2 = ChatTestData(
            chat_session_id,
            chat_session_token,
            message_list,
            None, # TODO Don't need a serialized msg list right now
            topic_collection,
            expected_minute_models,
            expected_marker_models,
            expected_tag_models
        )

        self.test_chat_data_sets = [dataset1, dataset2]



    def get_list(self):
        return self.test_chat_data_sets

    def get_chat1_msgs(self):
        # Deserialized Chat Messages from real Chat
        # Root
        #   T1
        m0 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345997955.351787, route=MessageRoute(type=0, recipients=[]), userId=3, type=400, id='0e3f0d301aa9408e9c6622f54ed850e3'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=None, connectedMarker=None, endedMarker=None, joinedMarker=JoinedMarker(userId=3, name='brian'), startedMarker=None, type=0), markerId='581099e86b604dd4a14a07ee361e7c8b'), whiteboardCreatePathMessage=None)
        m1 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345997955.546505, route=MessageRoute(type=1, recipients=[]), userId=3, type=200, id='775a98d5be984f26bc4625f1d1c8881f'), tagDeleteMessage=None, whiteboardCreateMessage=WhiteboardCreateMessage(name='Default Whiteboard', whiteboardId='48c0b851412848c89589162bd9633081'), whiteboardDeleteMessage=None, markerCreateMessage=None, whiteboardCreatePathMessage=None)
        m2 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345997958.252566, route=MessageRoute(type=0, recipients=[]), userId=3, type=400, id='f70da9bcb28b465a866ce0380dd323d9'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=None, connectedMarker=ConnectedMarker(userId=3, isConnected=True), endedMarker=None, joinedMarker=None, startedMarker=None, type=1), markerId='63e5ee7e22164504a36c22a2eb0f6f5d'), whiteboardCreatePathMessage=None)
        m3 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345997985.703346, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='2f60b1e5d6b04cb6837518ee1a69721d'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=None, connectedMarker=None, endedMarker=None, joinedMarker=JoinedMarker(userId=4, name='jeff'), startedMarker=None, type=0), markerId='6e05fbea729e46fd8c6092303c4ab598'), whiteboardCreatePathMessage=None)
        m4 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345997985.760209, route=MessageRoute(type=1, recipients=[]), userId=4, type=200, id='f5abec0c2b2b406c8ad1c8409cb207ce'), tagDeleteMessage=None, whiteboardCreateMessage=WhiteboardCreateMessage(name='Default Whiteboard', whiteboardId='1b383024a3bc43ca901b695141bd97b4'), whiteboardDeleteMessage=None, markerCreateMessage=None, whiteboardCreatePathMessage=None)
        m5 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345997988.770594, route=MessageRoute(type=0, recipients=[]), userId=3, type=400, id='04ec21f6ed944d91a32654b7fe94a036'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=None, connectedMarker=ConnectedMarker(userId=4, isConnected=True), endedMarker=None, joinedMarker=None, startedMarker=None, type=1), markerId='070c6a92b8dc46fcad322ff757c4768a'), whiteboardCreatePathMessage=None)
        m6 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345997988.80604, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='ac9a8208bfcd41aa92fd8ab767a47166'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=None, connectedMarker=ConnectedMarker(userId=4, isConnected=True), endedMarker=None, joinedMarker=None, startedMarker=None, type=1), markerId='e7796136457e49dcb947d764e5b0990f'), whiteboardCreatePathMessage=None)
        m7 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345997988.81679, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='62b28383483246a2a66ad06a1e49ac81'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=None, connectedMarker=ConnectedMarker(userId=3, isConnected=True), endedMarker=None, joinedMarker=None, startedMarker=None, type=1), markerId='d30d61de64324f30a8589ed3789035fd'), whiteboardCreatePathMessage=None)
        m8 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998006.70588, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='b3186261a6b045fbb9bd69bc26fc7a78'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=PublishingMarker(isPublishing=True, userId=4), speakingMarker=None, connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=2), markerId='2932dcb4f92a4e27865d7dea3f178892'), whiteboardCreatePathMessage=None)
        m9 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998006.805657, route=MessageRoute(type=0, recipients=[]), userId=3, type=400, id='76ce735ce6394037b0935e4e2e5f4e4b'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=PublishingMarker(isPublishing=True, userId=4), speakingMarker=None, connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=2), markerId='0457b7d8e9d348219d89510366d312d5'), whiteboardCreatePathMessage=None)
        m10 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998020.692639, route=MessageRoute(type=0, recipients=[]), userId=3, type=400, id='eeaecc0ce345442fbfe9a7dd49e9c02a'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=PublishingMarker(isPublishing=True, userId=3), speakingMarker=None, connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=2), markerId='aa18907bfe0e4e0f95152f69d130a287'), whiteboardCreatePathMessage=None)
        m11 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998020.843055, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='cef9a114a77f4fdf8989f2de52417ad7'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=PublishingMarker(isPublishing=True, userId=3), speakingMarker=None, connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=2), markerId='02837bebb309448eaeaa95129154ee13'), whiteboardCreatePathMessage=None)
        m12 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998027.46263, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='d89648bce53d4327a4c74723d468960b'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=SpeakingMarker(isSpeaking=True, userId=3), connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=3), markerId='94a1f00c6b394425b434d6ecee35de49'), whiteboardCreatePathMessage=None)
        m13 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998032.394882, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='61380937af0b483a9b9db4564de3c054'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=SpeakingMarker(isSpeaking=False, userId=3), connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=3), markerId='73c0adbcf5f449f8921cdfa5de442231'), whiteboardCreatePathMessage=None)
        m14 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998034.250782, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='cdf827801017434db79c88646f43659a'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=SpeakingMarker(isSpeaking=True, userId=3), connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=3), markerId='0ad5c6f0023148fc9f0ef50ad865929a'), whiteboardCreatePathMessage=None)
        m15 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998040.303078, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='4cfc1a09ada24b908d81b49b051c8ef4'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=SpeakingMarker(isSpeaking=False, userId=3), connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=3), markerId='296e84ec7bf64e74bf47785b127b3899'), whiteboardCreatePathMessage=None)
        m16 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998041.176721, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='4fd2cdac60054cdd9e73ddcf16b8fdca'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=SpeakingMarker(isSpeaking=True, userId=3), connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=3), markerId='4ab9a904b10e44daaa33364031288a11'), whiteboardCreatePathMessage=None)
        m17 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998043.108687, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='fc3c807d472e4372bd2497478d02dab0'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=SpeakingMarker(isSpeaking=False, userId=3), connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=3), markerId='e00090b13780433ab398792f0a7b8932'), whiteboardCreatePathMessage=None)
        m18 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998044.692994, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='c40eb8cd08cd4b4e8af2f1f5d34d103c'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=SpeakingMarker(isSpeaking=True, userId=3), connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=3), markerId='f04bf449707f4a2da0c1f5c3ab5d492b'), whiteboardCreatePathMessage=None)
        m19 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998048.866415, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='8e835002bb10452bb03719913b3a97e4'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=SpeakingMarker(isSpeaking=False, userId=3), connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=3), markerId='494c1630ca4d4d458c11218c94d22a35'), whiteboardCreatePathMessage=None)
        m20 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998052.199869, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='12a9b10f4cd34a8da890a9346e5f0e29'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=SpeakingMarker(isSpeaking=True, userId=3), connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=3), markerId='d2fac2f99be249a688a73ca37dc50fb7'), whiteboardCreatePathMessage=None)
        m21 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998062.415358, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='db146f60e73d48048b19641773f4bfe3'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=SpeakingMarker(isSpeaking=False, userId=3), connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=3), markerId='6da1f0a66d774f43af6e72fe2e5cd43d'), whiteboardCreatePathMessage=None)
        m22 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998063.310327, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='711876b9200a4313882a409041b89c5f'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=SpeakingMarker(isSpeaking=True, userId=3), connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=3), markerId='9945576fd49742f186cff25b283c459f'), whiteboardCreatePathMessage=None)
        m23 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998064.946696, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='9a4c6789f2014840bb14b55ef1b784f3'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=SpeakingMarker(isSpeaking=False, userId=3), connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=3), markerId='6dbb3aed0c1c4be5bb82b6b96edcbc9a'), whiteboardCreatePathMessage=None)
        m24 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998065.801316, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='7e5f8d98248a4189aeee868a5ce0be1b'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=SpeakingMarker(isSpeaking=True, userId=3), connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=3), markerId='5eb73f19861540f4888048026a6417bb'), whiteboardCreatePathMessage=None)
        m25 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998067.492652, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='0e975c85f816416e9eab92e7b5879390'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=SpeakingMarker(isSpeaking=False, userId=3), connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=3), markerId='204625d3d8be475f942e6581838a451d'), whiteboardCreatePathMessage=None)
        m26 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=MinuteCreateMessage(topicId=1, startTimestamp=1345998072, endTimestamp=None, minuteId='d9ef2b24908c4eec98c215997537a607'), header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998072.612342, route=MessageRoute(type=1, recipients=[]), userId=4, type=300, id='ab189beac2464f928b6c0e139e1a9e87'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=None, whiteboardCreatePathMessage=None)
        m27 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=MinuteCreateMessage(topicId=2, startTimestamp=1345998072, endTimestamp=None, minuteId='b91b4423b4864dc7875b052f6cbedb37'), header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998072.628422, route=MessageRoute(type=1, recipients=[]), userId=4, type=300, id='30bc88d82fb14145b6589cc7f65228da'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=None, whiteboardCreatePathMessage=None)
        m28 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998072.707757, route=MessageRoute(type=0, recipients=[]), userId=3, type=400, id='8e72de15244046499836ba53d3f461a8'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=None, connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=StartedMarker(userId=3), type=4), markerId='cf79037172764204b70bdeedf16d2a7a'), whiteboardCreatePathMessage=None)
        m29 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998072.919589, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='f00e201bc0aa4d0ba9157fff5bce5b57'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=None, connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=StartedMarker(userId=4), type=4), markerId='412ae01793b34fad95b2ce7e0d0e193e'), whiteboardCreatePathMessage=None)
        m30 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998075.464798, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='2eb067a966e74c18a8f57d12d4993e3f'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=SpeakingMarker(isSpeaking=True, userId=3), connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=3), markerId='ce790b88e40147678e6f3e61a9cfe327'), whiteboardCreatePathMessage=None)
        m31 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998092.304439, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='64e98c678f754e2f88f3d14ffc65b82b'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=SpeakingMarker(isSpeaking=False, userId=3), connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=3), markerId='31c0f965c011462080a1aa13327e965c'), whiteboardCreatePathMessage=None)
        m32 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998095.26175, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='5451530a7f0c428e9b897969e7beddfd'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=SpeakingMarker(isSpeaking=True, userId=3), connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=3), markerId='b6346e77a3564516a1a1c0ccba751dfe'), whiteboardCreatePathMessage=None)
        m33 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998102.073912, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='66d0741b235943a286a49e1706d689b1'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=SpeakingMarker(isSpeaking=False, userId=3), connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=3), markerId='e4de4810cc324c08b641ab0d0055485a'), whiteboardCreatePathMessage=None)
        m34 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998112.604138, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='82ba750beafa480ea01f71ba9702c5d6'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=SpeakingMarker(isSpeaking=True, userId=3), connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=3), markerId='042d3c1b78394f34b143007b19b39d05'), whiteboardCreatePathMessage=None)
        m35 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998137.60935, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='92317469f99c45d290150dde8174dbc1'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=SpeakingMarker(isSpeaking=False, userId=3), connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=3), markerId='465ff8a080424e4a9d3e4b89a9d1823e'), whiteboardCreatePathMessage=None)
        m36 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998140.745692, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='bc2a35d38b69435795ddd7a4985811bf'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=SpeakingMarker(isSpeaking=True, userId=3), connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=3), markerId='6c1b038d20db499ab77ade1a5ad54bc2'), whiteboardCreatePathMessage=None)
        m37 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998144.714979, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='22ba661127ab438691b520824b6fa9bb'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=SpeakingMarker(isSpeaking=False, userId=3), connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=3), markerId='0ccda16d57ea41f0ad2b9eaf40c3434c'), whiteboardCreatePathMessage=None)
        m38 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998148.138694, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='bfd85596594c418a8a49767ba360bfe0'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=SpeakingMarker(isSpeaking=True, userId=3), connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=3), markerId='bce5b57ce871442184fe9bb0341997ff'), whiteboardCreatePathMessage=None)
        m39 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998153.787653, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='0dbbfe3073c84350b57ccfa9fa6cfb92'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=SpeakingMarker(isSpeaking=False, userId=3), connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=3), markerId='1b8a81228e224d2ea0c77270008e62cf'), whiteboardCreatePathMessage=None)
        m40 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998156.118762, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='8e3aa7f9514a461aa216011e615a3ab9'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=SpeakingMarker(isSpeaking=True, userId=3), connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=3), markerId='821b8af027f148e1990b83bc0cf70162'), whiteboardCreatePathMessage=None)
        m41 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998160.142176, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='6025f62900054f69b70beba9ccd16e5b'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=SpeakingMarker(isSpeaking=False, userId=3), connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=3), markerId='169ff012a433431ea0ecf386b0091637'), whiteboardCreatePathMessage=None)
        m42 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998162.400711, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='4a486b41737e44c2a0d84d322a3f5614'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=SpeakingMarker(isSpeaking=True, userId=3), connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=3), markerId='309b8ae664b94b1aaf1f3cbc0fdee3c2'), whiteboardCreatePathMessage=None)
        m43 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998164.822266, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='dd8616e8cc0a4c19856bcf97ace0dbcc'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=SpeakingMarker(isSpeaking=False, userId=3), connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=3), markerId='90b6cd40301c4174ab329552e01832a4'), whiteboardCreatePathMessage=None)
        m44 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998165.459133, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='29524c294f11453e816336fe9247bbd4'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=SpeakingMarker(isSpeaking=True, userId=3), connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=3), markerId='d505b2e30b9e4f7cb753d90288071819'), whiteboardCreatePathMessage=None)
        m45 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998166.837886, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='2a687fc862c346c2b7d9caadb5a59034'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=SpeakingMarker(isSpeaking=False, userId=3), connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=3), markerId='5f131326c27a41ba992e9a4ef9c53168'), whiteboardCreatePathMessage=None)
        m46 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998167.788183, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='7d31456e16e24910a34f962029461f58'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=SpeakingMarker(isSpeaking=True, userId=3), connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=3), markerId='99922ad82e0840bd97a0e06f00086cf4'), whiteboardCreatePathMessage=None)
        m47 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998168.468729, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='ccd1f109e4bf4b64891a9f5da2171bc3'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=SpeakingMarker(isSpeaking=False, userId=3), connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=3), markerId='2e3ea22d7249437ebfb772017a12197e'), whiteboardCreatePathMessage=None)
        m48 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998171.075732, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='227f133858ab425aab293e522039e4ba'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=SpeakingMarker(isSpeaking=True, userId=3), connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=3), markerId='bb4d3a98fb5349649c9b39c13487b171'), whiteboardCreatePathMessage=None)
        m49 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998171.57157, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='a72ec3672c4d4114a221edb13a7bb728'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=SpeakingMarker(isSpeaking=False, userId=3), connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=3), markerId='bb75214a4ebe4cdfbd732e2d73c50ecc'), whiteboardCreatePathMessage=None)
        m50 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998171.79755, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='eca15fffa5db451685998a22257d6834'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=SpeakingMarker(isSpeaking=True, userId=3), connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=3), markerId='eeea4f7a2c1b4e5da1b3122d7f4967cb'), whiteboardCreatePathMessage=None)
        m51 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998175.888601, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='51d2270a8ff64ac18195fff04ef2a856'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=SpeakingMarker(isSpeaking=False, userId=3), connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=3), markerId='10f5acd6a9554550a3cb8789107105a2'), whiteboardCreatePathMessage=None)
        m52 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998178.047888, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='d9486794aec3402188e1513bc24df9cd'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=SpeakingMarker(isSpeaking=True, userId=3), connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=3), markerId='ac41c281fc9d4d92a005a1bf08915772'), whiteboardCreatePathMessage=None)
        m53 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998179.424917, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='7f28757e092e424a99f3ce6ddd84c35c'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=SpeakingMarker(isSpeaking=False, userId=3), connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=3), markerId='f06a53668cdb4a2485bda47364f90481'), whiteboardCreatePathMessage=None)
        m54 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998182.292958, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='8558cfeeb801455ebf9ec2c434f762bc'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=SpeakingMarker(isSpeaking=True, userId=3), connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=3), markerId='cecb98998b694ebbb74a68a0bda416be'), whiteboardCreatePathMessage=None)
        m55 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998192.618924, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='188f97f2d8fc4e0fa57c690538bae24b'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=SpeakingMarker(isSpeaking=False, userId=3), connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=3), markerId='75cacfd3244447a29e6132eb093931e5'), whiteboardCreatePathMessage=None)
        m56 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998198.943102, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='4a52fa0c45c24a2581d416b974d08630'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=SpeakingMarker(isSpeaking=True, userId=3), connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=3), markerId='e9a9daa9b2ab49458fd4ad7687d71f6d'), whiteboardCreatePathMessage=None)
        m57 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998199.345952, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='a295e3c9fede4a5ebab88cc80811e2a7'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=SpeakingMarker(isSpeaking=False, userId=3), connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=3), markerId='c441f0bac8264fe89107fbfc2f5ce484'), whiteboardCreatePathMessage=None)
        m58 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998199.676182, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='4cb53d73c7f145ab9e1ae0e6f248249a'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=SpeakingMarker(isSpeaking=True, userId=3), connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=3), markerId='26a17cbce4dd49449c3a07a2ae71f309'), whiteboardCreatePathMessage=None)
        m59 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998199.920061, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='2206123ccf1e47e187c61f321a4bca57'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=SpeakingMarker(isSpeaking=False, userId=3), connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=3), markerId='d0f66be00c4f4fceae5ab854c47e76c5'), whiteboardCreatePathMessage=None)
        m60 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998200.768258, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='d908648e610a44ea9ff5091841408565'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=SpeakingMarker(isSpeaking=True, userId=3), connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=3), markerId='849fe8ff11be446183a30033c072a5d5'), whiteboardCreatePathMessage=None)
        m61 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998203.384303, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='3ddcac2b99534692b0099f5963a41ab2'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=SpeakingMarker(isSpeaking=False, userId=3), connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=3), markerId='fb5e3e293ffd40d792ea7f5491b9834d'), whiteboardCreatePathMessage=None)
        m62 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998206.104575, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='5247f3b97810468788c8488be1d3d349'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=SpeakingMarker(isSpeaking=True, userId=3), connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=3), markerId='943a96f3bccf4981af6dee3e3198bc13'), whiteboardCreatePathMessage=None)
        m63 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998206.770535, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='1f7d7b7fe3484cf7a141912b4fd68daf'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=SpeakingMarker(isSpeaking=False, userId=3), connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=None, type=3), markerId='48c173348afd4ecfa0450a167fee21a7'), whiteboardCreatePathMessage=None)
        m64 = Message(tagCreateMessage=None, minuteUpdateMessage=MinuteUpdateMessage(topicId=2, startTimestamp=1345998072, endTimestamp=1345998211, minuteId='b91b4423b4864dc7875b052f6cbedb37'), whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998211.847257, route=MessageRoute(type=1, recipients=[]), userId=4, type=301, id='badb4f94801d4aa1aa3e11b422760726'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=None, whiteboardCreatePathMessage=None)
        m65 = Message(tagCreateMessage=None, minuteUpdateMessage=MinuteUpdateMessage(topicId=1, startTimestamp=1345998072, endTimestamp=1345998211, minuteId='d9ef2b24908c4eec98c215997537a607'), whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998211.856598, route=MessageRoute(type=1, recipients=[]), userId=4, type=301, id='2fd9e45ee45c4e16abb565f2d702fb07'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=None, whiteboardCreatePathMessage=None)
        m66 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998212.502966, route=MessageRoute(type=0, recipients=[]), userId=3, type=400, id='842a623c53304209a52525810542a3a5'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=None, connectedMarker=None, endedMarker=EndedMarker(userId=3), joinedMarker=None, startedMarker=None, type=5), markerId='55181f3d4c784c81832ce4b3c0b1d43a'), whiteboardCreatePathMessage=None)
        m67 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-U3VuIEF1ZyAyNiAwOToxOTowMiBQRFQgMjAxMn4wLjQzMDM2NzUzfg', timestamp=1345998212.626946, route=MessageRoute(type=0, recipients=[]), userId=4, type=400, id='7a5baa6edba648ed99d1d81d08d0d4c7'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=None, connectedMarker=None, endedMarker=EndedMarker(userId=4), joinedMarker=None, startedMarker=None, type=5), markerId='9555c34facc345868432b370df64a1a6'), whiteboardCreatePathMessage=None)
        chat1 = [m0, m1, m2, m3, m4, m5, m6, m7, m8, m9, m10,
                 m11, m12, m13, m14, m15, m16, m17, m18, m19, m20,
                 m21, m22, m23, m24, m25, m26, m27, m28, m29, m30,
                 m31, m32, m33, m34, m35, m36, m37, m38, m39, m40,
                 m41, m42, m43, m44, m45, m46, m47, m48, m49, m50,
                 m51, m52, m53, m54, m55, m56, m57, m58, m59, m60,
                 m61, m62, m63, m64, m65, m66, m67]
        return chat1

    def get_chat1_expected_minute_models(self, chat_session_id):

        # Chat1 parent topic minute
        parent_chat_minute = ChatMinute(
            chat_session_id=chat_session_id,
            topic_id=1,
            start=tz.timestamp_to_utc(1345998072),
            end = tz.timestamp_to_utc(1345998211))

        # Chat1 leaf topic minute
        leaf_chat_minute = ChatMinute(
            chat_session_id=chat_session_id,
            topic_id=2,
            start=tz.timestamp_to_utc(1345998072),
            end = tz.timestamp_to_utc(1345998211))

        # Return chat minute models ordered by topic rank
        return [parent_chat_minute, leaf_chat_minute]

    def get_chat1_expected_marker_models(self, expected_chat_minute_list):
        m = ChatSpeakingMarker(
            user_id=3,
            chat_minute=expected_chat_minute_list[1],
            start=None, # Punted on verifying start times of these models
            end=None) # Punted on verifying end time of these models

        # Create 17 speaking markers. In this case, they will all
        # have the same user_id and chat_minute.
        list = [m, m, m, m, m,
                m, m, m, m, m,
                m, m, m, m, m,
                m, m]
        return list

    def get_chat1_expected_tag_models(self, message_list, expected_chat_minute_list):
        # No Chat Tag Models in this chat
        return []



    def get_chat2_msgs(self):

        # Deserialized Chat Messages from real Chat
        # Root
        #   T1
        m0 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-V2VkIEF1ZyAyMiAwNjo1ODoyNSBQRFQgMjAxMn4wLjg5Mjc3OTJ-', timestamp=1345643917.544588, route=MessageRoute(type=0, recipients=[]), userId=3, type=400, id='b64efda139224cdc9e8b2248fdf49117'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=None, connectedMarker=None, endedMarker=None, joinedMarker=JoinedMarker(userId=3, name='brian'), startedMarker=None, type=0), markerId='68819105102c4fdd8dffcce983d34f76'), whiteboardCreatePathMessage=None)
        m1 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-V2VkIEF1ZyAyMiAwNjo1ODoyNSBQRFQgMjAxMn4wLjg5Mjc3OTJ-', timestamp=1345643917.847823, route=MessageRoute(type=1, recipients=[]), userId=3, type=200, id='096a9f1f54984e079ef45c3f07f21ed3'), tagDeleteMessage=None, whiteboardCreateMessage=WhiteboardCreateMessage(name='Default Whiteboard', whiteboardId='d74b1bd64a4a48909e3c727299b7ab8c'), whiteboardDeleteMessage=None, markerCreateMessage=None, whiteboardCreatePathMessage=None)
        m2 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-V2VkIEF1ZyAyMiAwNjo1ODoyNSBQRFQgMjAxMn4wLjg5Mjc3OTJ-', timestamp=1345643921.425069, route=MessageRoute(type=0, recipients=[]), userId=3, type=400, id='6a683f85bcf54ce0a1fad423317a030b'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=None, connectedMarker=ConnectedMarker(userId=3, isConnected=True), endedMarker=None, joinedMarker=None, startedMarker=None, type=1), markerId='9acbd831c59e4461b58d6218d68443ef'), whiteboardCreatePathMessage=None)
        m3 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=MinuteCreateMessage(topicId=1, startTimestamp=1345643927, endTimestamp=None, minuteId='6a0a875dcdce49b9a86e757376d34615'), header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-V2VkIEF1ZyAyMiAwNjo1ODoyNSBQRFQgMjAxMn4wLjg5Mjc3OTJ-', timestamp=1345643927.795392, route=MessageRoute(type=1, recipients=[]), userId=3, type=300, id='e6dd1585f3524ed7b4910cee4abc808a'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=None, whiteboardCreatePathMessage=None)
        m4 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=MinuteCreateMessage(topicId=2, startTimestamp=1345643927, endTimestamp=None, minuteId='6350813013bd4472b9ef5366fca0b434'), header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-V2VkIEF1ZyAyMiAwNjo1ODoyNSBQRFQgMjAxMn4wLjg5Mjc3OTJ-', timestamp=1345643927.803031, route=MessageRoute(type=1, recipients=[]), userId=3, type=300, id='b8fd5a57657e4ae5bb77ed8f691193ea'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=None, whiteboardCreatePathMessage=None)
        m5 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-V2VkIEF1ZyAyMiAwNjo1ODoyNSBQRFQgMjAxMn4wLjg5Mjc3OTJ-', timestamp=1345643927.934734, route=MessageRoute(type=0, recipients=[]), userId=3, type=400, id='2d344bec420c4b11a4f7bdb2d63de2a4'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=None, connectedMarker=None, endedMarker=None, joinedMarker=None, startedMarker=StartedMarker(userId=3), type=4), markerId='652270426d064f4da8069d7f5f39846e'), whiteboardCreatePathMessage=None)

        # Tag related messages
        m6 = Message(tagCreateMessage=TagCreateMessage(tagId='4141decbb6f44471939149d6bc801700', name='Tag', tagReferenceId=None, minuteId='6350813013bd4472b9ef5366fca0b434'), minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-V2VkIEF1ZyAyMiAwNjo1ODoyNSBQRFQgMjAxMn4wLjg5Mjc3OTJ-', timestamp=1345643936.348819, route=MessageRoute(type=1, recipients=[]), userId=3, type=100, id='7f577979990945efa0b41ab887155a1d'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=None, whiteboardCreatePathMessage=None)
        m7 = Message(tagCreateMessage=TagCreateMessage(tagId='80821d7947a545aa86b3ef4400a4749c', name='deletedTag', tagReferenceId=None, minuteId='6350813013bd4472b9ef5366fca0b434'), minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-V2VkIEF1ZyAyMiAwNjo1ODoyNSBQRFQgMjAxMn4wLjg5Mjc3OTJ-', timestamp=1345643943.648114, route=MessageRoute(type=1, recipients=[]), userId=3, type=100, id='13a5a7d1eaad469a8bb8603ee580b3e1'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=None, whiteboardCreatePathMessage=None)
        m8 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-V2VkIEF1ZyAyMiAwNjo1ODoyNSBQRFQgMjAxMn4wLjg5Mjc3OTJ-', timestamp=1345643948.168495, route=MessageRoute(type=1, recipients=[]), userId=3, type=101, id='79e315e656fd4d56b348ea7472412ab5'), tagDeleteMessage=TagDeleteMessage(tagId='80821d7947a545aa86b3ef4400a4749c'), whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=None, whiteboardCreatePathMessage=None)
        m9 = Message(tagCreateMessage=TagCreateMessage(tagId='b5e8a3b469e04fd883a2c9ee9f527e1b', name='duplicate tag', tagReferenceId=None, minuteId='6350813013bd4472b9ef5366fca0b434'), minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-V2VkIEF1ZyAyMiAwNjo1ODoyNSBQRFQgMjAxMn4wLjg5Mjc3OTJ-', timestamp=1345643953.358221, route=MessageRoute(type=1, recipients=[]), userId=3, type=100, id='667e7f48a9f74058a26445e283c3482c'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=None, whiteboardCreatePathMessage=None)
        m10 = Message(tagCreateMessage=TagCreateMessage(tagId='35ffbbc263fe41879b83df27a328f3c2', name='duplicate tag', tagReferenceId=None, minuteId='6350813013bd4472b9ef5366fca0b434'), minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-V2VkIEF1ZyAyMiAwNjo1ODoyNSBQRFQgMjAxMn4wLjg5Mjc3OTJ-', timestamp=1345643957.397479, route=MessageRoute(type=1, recipients=[]), userId=3, type=100, id='b24bbcc26432461bb72b70823dcbf67e'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=None, whiteboardCreatePathMessage=None)

        m11 = Message(tagCreateMessage=None, minuteUpdateMessage=MinuteUpdateMessage(topicId=2, startTimestamp=1345643927, endTimestamp=1345643963, minuteId='6350813013bd4472b9ef5366fca0b434'), whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-V2VkIEF1ZyAyMiAwNjo1ODoyNSBQRFQgMjAxMn4wLjg5Mjc3OTJ-', timestamp=1345643963.615939, route=MessageRoute(type=1, recipients=[]), userId=3, type=301, id='719ced197ae94e75b1cbde6881fa79de'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=None, whiteboardCreatePathMessage=None)
        m12 = Message(tagCreateMessage=None, minuteUpdateMessage=MinuteUpdateMessage(topicId=1, startTimestamp=1345643927, endTimestamp=1345643963, minuteId='6a0a875dcdce49b9a86e757376d34615'), whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-V2VkIEF1ZyAyMiAwNjo1ODoyNSBQRFQgMjAxMn4wLjg5Mjc3OTJ-', timestamp=1345643963.650789, route=MessageRoute(type=1, recipients=[]), userId=3, type=301, id='6a0cbc29819547a895c53e2d7e0f61be'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=None, whiteboardCreatePathMessage=None)
        m13 = Message(tagCreateMessage=None, minuteUpdateMessage=None, whiteboardDeletePathMessage=None, minuteCreateMessage=None, header=MessageHeader(chatSessionToken='1_MX4xNTg4OTk5MX4xMjcuMC4wLjF-V2VkIEF1ZyAyMiAwNjo1ODoyNSBQRFQgMjAxMn4wLjg5Mjc3OTJ-', timestamp=1345643964.04311, route=MessageRoute(type=0, recipients=[]), userId=3, type=400, id='c375ef54d7774768bb1c888478b4b906'), tagDeleteMessage=None, whiteboardCreateMessage=None, whiteboardDeleteMessage=None, markerCreateMessage=MarkerCreateMessage(marker=Marker(publishingMarker=None, speakingMarker=None, connectedMarker=None, endedMarker=EndedMarker(userId=3), joinedMarker=None, startedMarker=None, type=5), markerId='4c862ffda41c4925be232a6fcb6fda26'), whiteboardCreatePathMessage=None)
        chat2 = [m0, m1, m2, m3, m4, m5, m6, m7, m8, m9, m10, m11, m12, m13]

        return chat2

    def get_chat2_expected_minute_models(self, chat_session_id):

        # Chat2 parent topic minute
        parent_chat_minute = ChatMinute(
            chat_session_id=chat_session_id,
            topic_id=1,
            start=tz.timestamp_to_utc(1345643927),
            end = tz.timestamp_to_utc(1345643963))

        # Chat2 leaf topic minute
        leaf_chat_minute = ChatMinute(
            chat_session_id=chat_session_id,
            topic_id=2,
            start=tz.timestamp_to_utc(1345643927),
            end = tz.timestamp_to_utc(1345643963))

        # Return chat minute models ordered by topic rank
        return [parent_chat_minute, leaf_chat_minute]

    def get_chat2_expected_marker_models(self, expected_chat_minute_list):
        # No Chat Speaking Marker Models in this chat
        return []

    def get_chat2_expected_tag_models(self, message_list, expected_chat_minute_list):

        expected_tag_models = []

        persisted_tag_messages = [message_list[6], message_list[9]]
        for message in persisted_tag_messages:
            expected_tag = ChatTag(
                user_id=message.header.userId,
                chat_minute=expected_chat_minute_list[1],
                tag_id=message.tagCreateMessage.tagReferenceId,
                name=message.tagCreateMessage.name,
                deleted=False)
            expected_tag_models.append(expected_tag)
        return expected_tag_models



class ChatTestData(object):
    """
        Data structure to house chat data.
    """

    def __init__(self,
                 chat_session_id,
                 chat_session_token,
                 deserialized_message_list,
                 serialized_message_list,
                 topic_collection,
                 expected_minute_models,
                 expected_marker_models,
                 expected_tag_models
    ):
        self.chat_session_id = chat_session_id
        self.chat_session_token = chat_session_token
        self.message_list = deserialized_message_list # msgs in chronological order
        self.serialized_message_list = serialized_message_list # msgs in chronological order
        self.topic_collection = topic_collection
        self.expected_minute_models = expected_minute_models
        self.expected_marker_models = expected_marker_models
        self.expected_tag_models = expected_tag_models

