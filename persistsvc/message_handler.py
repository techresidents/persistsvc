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


    def process(self, message):
        """
            Converts input chat message to a model instance based upon the
            chat message's type and persists the created model instance to the db.

            This method is the orchestrator of persisting all the chat entities
            that need to be stored.  It's assumed that messages that are input
            are in chronological order. This is to satisfy any ordering dependencies
            that may exist between the chat messages.
        """
        ret = None

        if (message.type_id == self.MINUTE_CREATE_TYPE):
            ret = self.chat_minute_handler.create_model(message)
            if (ret is not None):
                self.db_session.add(ret)
                self.db_session.flush() # force a flush so that the chat minute object gets an ID
                self.chat_minute_handler.set_active_minute(ret)

        elif (message.type_id == self.MINUTE_UPDATE_TYPE):
            ret = self.chat_minute_handler.update_model(message)
            if (ret is not None):
                self.db_session.add(ret)

        elif (message_type.id == self.MARKER_CREATE_TYPE):
            ret = self.chat_marker_handler.create_model(
                message,
                self.chat_minute_handler.get_active_minute())
            if (ret is not None):
                db_session.add(ret)

        elif (message_type.id == self.TAG_CREATE_TYPE):
            ret = self.chat_tag_handler.create_model(
                message,
                self.chat_minute_handler.get_active_minute())
            if (ret is not None):
                db_session.add(ret)

        elif (message_type.id == self.TAG_DELETE_TYPE):
            ret = self.chat_tag_handler.update_model(message)
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

        This class also maintains the active chat minute.
        """

    def __init__(self):
        self.log = logging.getLogger(__name__)
        self.active_minute = None
        self.all_minutes = {}

    def set_active_minute(self, chat_minute):
        self.active_minute = chat_minute
        self.log.debug('The new active chat minute id=%s' % self.active_minute.id)

    def get_active_minute(self):
        return self.active_minute

    def _decode_message_data(self, message):
        # read message format type
        # parse message data and fill in data structure
        return None

    def create_model(self, message):
        """
            Create model instance

            Returns None if creation failed.
            Creation can fail if the input message fails to pass biz rules filter.
        """
        ret = None

        # Decode chat message data blob
        message_data = _decode_message_data(message)

        # Create model from message
        if (self._is_valid_create_message(message, message_data)):
            minute_start = datetime.datetime.now() # from data blob
            minute_end = message.time # from data blob
            ret = ChatMinute(
                chat_session_id=message.chat_session_id,
                start=minute_start,
                end=minute_end)
            self.active_minute = ret

        # Store message and its data for easy reference,
        # (specifically for minuteID look-ups on minute-update messages)
        minute_data = JobData(message_data.minuteId, message, message_data, ret)
        self.all_minutes[minute_data.id] = minute_data

        return ret

    def update_model(self, message):
        """
            Update model instance

            Handles marking the end time of a chat minute model.
            Returns the updated model instance.
            Returns None if message is invalid.
        """
        ret = None

        # Decode chat message data blob
        message_data = _decode_message_data(message)

        if (self._is_valid_update_message(message, message_data)):
            minute_data = self.all_minutes[message_data.minuteId]
            minute_model = minute_data.get_model()
            minute.model.end = message_data.endTimestamp
            ret = minute_model
            # The active minute is being set to None to ensure that we catch any messages
            # that might occur between the end of one chat minute and the start of the
            # next chat minute.
            self.active_minute = None

        # Overwrite existing chat minute data with the newly updated data
        minute_data = JobData(message_data.minuteId, message, message_data, ret)
        self.all_minutes[minute_data.id] = minute_data

        return ret

    def _is_valid_create_message(self, message, message_data):
        """
            Returns True if message should be persisted, returns False otherwise.
        """
        ret = False

        # Chat messages are guaranteed to be unique due to the message_id attribute that each
        # message possesses.  This means we can avoid a duplicate message ID check here.

        # TODO add timestamp check to ensure it doesn't precede the previous minute?
        ret = True
        return ret

    def _is_valid_update_message(self, message, message_data):
        """
            Returns True if message should be persisted, returns False otherwise.
        """
        ret = False

        if (message_data.minuteId in self.all_minutes):
            minute_data = self.all_minutes[message_data.minuteId]
            minute_model = minute_data.get_model()
            # if minuteID has an associated model, then we tried to persist the message
            if (minute_model is not None):
                # Since we process messages chronologically, ensure that the referenced minuteID
                # is also the active chat minute
                if(minute_model == self.active_minute):
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

    # We will only store speaking markers if the user
    # was speaking for longer than this threshold value.
    SPEAKING_DURATION_THRESHOLD = 30000 # 30 secs in millis

    def __init__(self):
        self.log = logging.getLogger(__name__)
        self.all_markers = {}
        self.speaking_state = {}

    def _decode_message_data(self, message):
        # read message format type
        # parse message data and fill in data structure
        return None

    def create_model(self, message, chat_minute_id):
        """
            Create model instance

            Returns None if creation failed.
            Creation can fail if the input message fails to pass biz rules filter.
        """
        ret = None

        # Decode chat message data blob
        message_data = _decode_message_data(message)

        if (self._is_valid_message(message, message_data)):

            # Only expecting & handling speaking markers for now

            # Read userId and get associated speaking state
            user_id = message_data.userId
            user_speaking_data = None
            if (user_id not in self.speaking_state):
                user_speaking_data = SpeakingData(user_id)
            else:
                user_speaking_data = self.speaking_state[user_id]

            # Determine if the speaking minute has ended and we need to persist the marker
            if (message_data.isSpeaking):
                # msg indicates user started speaking
                if (not user_speaking_data.is_speaking()):
                    # If user wasn't already speaking, process msg.
                    # Ignore duplicate speaking_start markers.
                    user_speaking_data.set_start_timestamp(message.timestamp)
                    user_speaking_data.set_speaking(True)
            else:
                # msg indicates user stopped speaking
                if (user_speaking_data.is_speaking()):
                    # If user was already speaking, process msg.
                    # Ignore duplicate speaking_end markers.
                    user_speaking_data.set_end_timestamp(message.timestamp)
                    duration = user_speaking_data.calculate_speaking_duration()
                    if (duration > SPEAKING_DURATION_THRESHOLD):
                        # Only persist speaking markers with significant duration
                        ret = ChatSpeakingMarker(
                            user_id=user_id,
                            chat_minute_id=chat_minute_id,
                            start=user_speaking_data.get_start_timestamp(),
                            end=user_speaking_data.get_end_timestamp())
                    # Reset user's speaking state
                    user_speaking_data.set_start_timestamp(None)
                    user_speaking_data.set_end_timestamp(None)
                    user_speaking_data.set_speaking(False)

            # Update state
            self.speaking_state[user_id] = user_speaking_data
            persist_marker = False

        # Store message and its data for easy reference
        marker_data = JobData(message_data.markerId, message, message_data, ret)
        self.all_markers[marker_data.id] = marker_data

        return ret

    def _is_valid_message(self, message, message_data):
        """
            Returns True if message should be persisted, returns False otherwise.

            Only passes speaking markers.
        """
        ret = False

        # Chat messages are guaranteed to be unique due to the message_id attribute that each
        # message possesses.  This means we can avoid a duplicate message ID check here.

        #TODO only pass chat speaking markers
        # if message_data.marker.type == chat_speaking
        #   ret = True

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
        self.all_tags = {}

    def _decode_message_data(self, message):
        # read message format type
        # parse message data and fill in data structure
        return None

    def create_model(self, message, chat_minute_id):
        """
            Create model instance

            Returns None if creation failed.
            Creation can fail if the input message fails to pass biz rules filter.
        """
        ret = None

        # Decode chat message data blob
        message_data = _decode_message_data(message)

        # Create the model from the message
        if (self._is_valid_create_tag_message(message, message_data)):
            user = 'userID' # from data blob
            name = 'name' # from data blob
            tag_ref_id = '1' # from data blob
            ret = ChatTag(
                user_id=user,
                chat_minute_id=chat_minute_id,
                tag=tag_ref_id,
                name=name)

        # Store message and its data for easy reference,
        # (specifically for tagID look-ups on tag delete messages)
        tag_data = JobData(message_data.tagId, message, message_data, ret)
        self.all_tags[tag_data.tag_id] = tag_data

        return ret

    def update_model(self, message):
        """
            Update model instance.

            Handles marking a chat tag model for delete.
            Returns the updated model instance.
            Returns None if message is invalid.
        """
        ret = None

        # Decode chat message data blob
        message_data = _decode_message_data(message)

        # Update model
        if (self._is_valid_delete_tag_message(message, message_data)):
            tag_data = self.all_tags[message_data.tagId]
            tag_model = tag_data.get_tag_model()
            if (tag_model is not None):
                # implies the tag-create msg was valid and persisted
                tag_model.deleted = True
            ret = tag_model

        # Update state
        # This will overwrite the message data associated with the tag create message
        tag_data = JobData(message_data.tagId, message, message_data, ret)
        self.all_tags[message_data.tagId] = tag_data

        return ret

    def _is_valid_create_tag_message(self, message, message_data):
        """
            Returns True if message should be persisted, returns False otherwise.
        """
        ret = False

        # Chat messages are guaranteed to be unique due to the message_id attribute that each
        # chat message possesses.  This means we can avoid a duplicate messageID check here.

        # Check for duplicate tagID to prevent overwriting existing tag data
        if (message_data.tagId in self.all_tags):
            self.log.warning('Chat message to create tag with duplicate tagID=%s' % message_data.tagId)
            return ret

        # Prevent adding the same tag within the same chat minute


        ret = True
        return ret

    def _is_valid_delete_tag_message(self, message, message_data):
        """
            Returns True if message should be persisted, returns False otherwise.
        """
        ret = False

        if (message_data.tagId in self.all_tags):
            tag_data = self.all_tags[message_data.tagId]
            tag_model = tag_data.get_model()
            # if tagID has an associated model, then we tried to persist the message
            if (tag_model is not None):
                # Ensure that the model hasn't already been marked for delete
                if (tag_model.deleted == False):
                    ret = True

        return ret



class JobData(object):
    """
        Data structure to maintain references to a chat message's
        associated message, decoded message data, and model.

        The id parameter represents a tagId, minuteId, or markerId.
        This data is included in the chat message data blob.
    """
    def __init__(self, id, message, message_data, model=None):
        self.id = id
        self.message = message
        self.message_data = message_data
        self.model = model

    def set_message(self, message):
        self.message = message

    def get_message(self):
        return self.message

    def set_message_data(self, message_data):
        self.message_data = message_data

    def get_message_data(self):
        return self.message_data

    def set_model(self, tag_model):
        self.model = tag_model

    def get_model(self):
        return self.model


class SpeakingData(object):
    """
        Data structure to store chat speaking state.
    """
    def __init__(self, user_id, is_speaking=False, start_timestamp=None, end_timestamp=None):
        self.user_id = user_id
        self.is_speaking=is_speaking
        self.start = start_timestamp
        self.end = end_timestamp

    def set_speaking(self, is_speaking):
        self.is_speaking = is_speaking

    def is_speaking(self):
        return self.is_speaking

    def set_start_timestamp(self, start):
        self.start = start

    def get_start_timestamp(self):
        return self.start

    def set_end_timestamp(self, end):
        self.end = end

    def get_end_timestamp(self):
        return self.end

    def calculate_speaking_duration(self):
        ret = 0
        if (self.start is not None and
            self.end is not None):
            ret = end-start
        return ret