import datetime
import logging

from trsvcscore.models import ChatMinute, ChatSpeakingMarker,\
    ChatTag, ChatMessageType


class ChatMessageHandler(object):
    """
        Handler to process chat messages and persist the associated
        message data.

        This handler is responsible for:
            1) Filtering out messages that don't need to be persisted
            2) Creating model instances from chat messages
            3) Persisting model instances
    """
    def __init__(self, db_session):
        self.log = logging.getLogger(__name__)
        self.db_session = db_session

        # Retrieve chat message type IDs
        self.MARKER_CREATE_TYPE = db_session.query(ChatMessageType).filter(ChatMessageType.name=='MARKER_CREATE').one().id
        self.MINUTE_CREATE_TYPE = db_session.query(ChatMessageType).filter(ChatMessageType.name=='MINUTE_CREATE').one().id
        self.MINUTE_UPDATE_TYPE = db_session.query(ChatMessageType).filter(ChatMessageType.name=='MINUTE_UPDATE').one().id
        self.TAG_CREATE_TYPE = db_session.query(ChatMessageType).filter(ChatMessageType.name=='TAG_CREATE').one().id
        self.TAG_DELETE_TYPE = db_session.query(ChatMessageType).filter(ChatMessageType.name=='TAG_DELETE').one().id

        # Create handlers for each type of message we need to persist
        self.chat_marker_handler = ChatMarkerHandler()
        self.chat_minute_handler = ChatMinuteHandler()
        self.chat_tag_handler = ChatTagHandler()

        # Initialize vars that maintain chat state
        self.active_chat_minute = None

    def process(self, message):
        """
            Converts input chat message to a model instance based upon the
            chat message's type and persists the instance to the db.

            This method is the orchestrator of persisting all the chat entities
            that need to be stored.
        """
        ret = None

        if (message.type_id == self.MINUTE_CREATE_TYPE):
            ret = self.chat_minute_handler.process(message)
            if (ret is not None):
                self.db_session.add(ret)
                self.db_session.flush()
                self.active_chat_minute = ret
                print 'active chat minute id is %s' % self.active_chat_minute.id

        elif (message.type_id == self.MINUTE_UPDATE_TYPE):
            ret = self.chat_minute_handler.process(message)
            if (ret is not None):
                self.active_chat_minute.end = ret.end
                self.db_session.add(self.active_chat_minute)
                self.active_chat_minute = None
                # The active minute is being set to None to ensure that we catch any messages
                # that might occur between the end of one chat minute and the start of the
                # next chat minute.

        elif (message_type.id == self.MARKER_CREATE_TYPE):
            ret = self.chat_marker_handler.process(message, self.active_chat_minute.id)
            if (ret is not None):
                db_session.add(ret)

        elif (message_type.id == self.TAG_CREATE_TYPE):
            ret = self.chat_marker_handler.process(message, self.active_chat_minute.id)
            if (ret is not None):
                db_session.add(ret)

        return ret


class ChatMinuteHandler(object):
    """
        Handler for Chat Minute messages

        This class creates model instances
        from chat minute messages and persists
        them to the db.

        This class is also responsible for
        defining and applying the business rules to handle
        duplicate messages and filtering any unwanted messages.
        """

    def __init__(self):
        self.log = logging.getLogger(__name__)
        self.all_messages = []
        self.persisted_messages = []

    def get_all_messages(self):
        """
            Return all chat marker messages.
        """
        return self.all_messages

    def get_persisted_messages(self):
        """
            Return chat marker messages that passed the biz rules filter
            and were persisted to the db
        """
        return self.persisted_messages

    def process(self, message):
        """
            Create model instance

            Returns None if creation failed.
            Creation can fail if the input message fails to pass biz rules filter.
        """
        ret = None
        self.all_messages.append(message)
        if (self._is_valid_message(message)):
            self.persisted_messages.append(message)
            ret = self._create_model(message)

        return ret

    def _create_model(self, message):
        # TODO deserialize data blob of message
        minute_start = datetime.datetime.now() # from data blob
        minute_end = message.time # from data blob

        chat_minute = ChatMinute(
            chat_session_id=message.chat_session_id,
            start=minute_start,
            end=minute_end)

        return chat_minute

    def _is_valid_message(self, message):
        """
            Returns True if message should be persisted, returns False otherwise.
        """
        ret = False
        # Apply Biz Rules here
        # Messages are guaranteed to be unique due to the message_id attribute that each
        # message possesses.  This means we can avoid a duplicate message check here.
        ret = True
        return ret

class ChatMarkerHandler(object):
    """
        Handler for Chat Marker messages

        This class creates model instances
        from chat marker messages and persists
        them to the db.

        This class is also responsible for
        defining and applying the business rules to handle
        duplicate messages and filtering unwanted messages.
        """

    def __init__(self):
        self.log = logging.getLogger(__name__)
        self.all_messages = []
        self.persisted_messages = []

    def get_all_messages(self):
        """
            Return all chat marker messages.
        """
        return self.all_messages

    def get_persisted_messages(self):
        """
            Return chat marker messages that passed the biz rules filter
            and were persisted to the db.
        """
        return self.persisted_messages

    def process(self, message, chat_minute_id):
        """
            Create model instance

            Returns None if creation failed.
            Creation can fail if the input message fails to pass biz rules filter.
        """
        ret = None
        self.all_messages.append(message)
        if (self._is_valid_message(message)):
            self.persisted_messages.append(message)
            ret = self._create_model(message, chat_minute_id)

        return ret

    def _create_model(self, message, chat_minute_id):
        # TODO deserialize data blob of message

        # Pull out needed chat message data from data blob
        user = 'userID' # from data blob
        speaking_start = datetime.datetime.now() # from data blob
        speaking_end = datetime.datetime.now() # from data blob

        # Create ChatSpeakingMarker object and add to db
        chat_speaking_marker = ChatSpeakingMarker(
            user_id=user,
            chat_minute_id=chat_minute_id,
            start=speaking_start,
            end=speaking_end)

        return chat_speaking_marker

    def _is_valid_message(self, message):
        """
            Returns True if message should be persisted, returns False otherwise.
        """
        ret = False
        # Apply Biz Rules here
        # Messages are guaranteed to be unique due to the message_id attribute that each
        # message possesses.  This means we can avoid a duplicate message check here.
        ret = True
        return ret

class ChatTagHandler(object):
    """
        Handler for Chat Tag messages

        This class creates model instances
        from chat minute messages and persists
        them to the db.

        This class is also responsible for
        defining and applying the business rules to handle
        duplicate messages and filtering any unwanted messages.
        """

    def __init__(self):
        self.log = logging.getLogger(__name__)
        self.all_messages = []
        self.persisted_messages = []

    def get_all_messages(self):
        """
            Return all chat marker messages.
        """
        return self.all_messages

    def get_persisted_messages(self):
        """
            Return chat marker messages that passed the biz rules filter
            and were persisted to the db.
        """
        return self.persisted_messages

    def process(self, message, chat_minute_id):
        """
            Create model instance

            Returns None if creation failed.
            Creation can fail if the input message fails to pass biz rules filter.
        """
        ret = None
        self.all_messages.append(message)
        if (self._is_valid_message(message)):
            self.persisted_messages.append(message)
            ret = self._create_model(message, chat_minute_id)

        return ret

    def _create_model(self, message, chat_minute_id):

        # Pull out needed chat message data from data blob
        user = 'userID' # from data blob
        name = 'name' # from data blob
        timestamp = 'time of message' # from data blob

        # Determine if this tag exists in our inventory of tags
        tag = db_session.query(ChatTag).\
            filter(ChatTag.name==name)
        tag_id = (tag.id if tag else None)

        # Create ChatSpeakingMarker object and add to db
        chat_tag = ChatTag(
            user_id=user,
            chat_minute_id=chat_minute.id,
            tag=tag_id,
            name=name)

        return chat_tag

    def _is_valid_message(self, message):
        """
            Returns True if message should be persisted, returns False otherwise.
        """
        ret = False
        # Apply Biz Rules here
        # Messages are guaranteed to be unique due to the message_id attribute that each
        # message possesses.  This means we can avoid a duplicate message check here.
        ret = True
        return ret