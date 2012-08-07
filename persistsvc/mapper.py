import datetime
import logging

from trsvcscore.models import ChatMinute, ChatSpeakingMarker, \
    ChatTag

class ChatMessageMapper(object):
    """
        Class to convert ChatMessages to their db model representation.

        This class converts ChatMessages to their db model representation
        based upon the type of the ChatMessage.
    """

    @staticmethod
    def chatMessage_to_ChatMinute(message):

        # deserialize data blob of message
        minute_start = datetime.datetime.now() # from data blob
        minute_end = datetime.datetime.now() # from data blob

        chat_minute = ChatMinute(
            chat_session_id=message.chat_session_id,
            start=minute_start,
            end=minute_end)

        return chat_minute


    @staticmethod
    def chatMessage_to_ChatSpeakingMarker(message, chat_minute_messages):

        # deserialize data blob of message

        # Pull out needed chat message data from data blob
        user = 'userID' # from data blob
        speaking_start = datetime.datetime.now() # from data blob
        speaking_end = datetime.datetime.now() # from data blob

        # Determine which chat minute the marker message occurred within
        # TODO need to use cache to lookup needed chat minute
        # How will the cache have the id I need?
        chat_minute = db_session.query(ChatMinute).\
            filter(ChatMinute.chat_session==chat_session_id).\
            filter(ChatMinute.start<= speaking_start).\
            filter(ChatMinute.end>=speaking_end).\
            one()

        # Create ChatSpeakingMarker object and add to db
        chat_speaking_marker = ChatSpeakingMarker(
            user_id=user,
            chat_minute_id=chat_minute.id,
            start=speaking_start,
            end=speaking_end)

        return chat_speaking_marker


    @staticmethod
    def chatMessage_to_ChatTag(message):

        # Pull out needed chat message data from data blob
        user = 'userID' # from data blob
        name = 'name' # from data blob
        timestamp = 'time of message' # from data blob

        # Determine if this tag exists in our inventory of tags
        tag = db_session.query(ChatTag).\
            filter(ChatTag.name== name)
        tag_id = (tag.id if tag else None)

        # Determine which chat minute the marker message occurred within
        chat_minute = db_session.query(ChatMinute).\
            filter(ChatMinute.start<= timestamp).\
            filter(ChatMinute.end>=timestamp).\
            one()

        # Create ChatSpeakingMarker object and add to db
        chat_tag = ChatTag(
            user_id=user,
            chat_minute_id=chat_minute.id,
            tag=tag_id,
            name=name)

        return chat_tag