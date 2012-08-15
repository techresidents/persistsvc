import datetime
import logging

from trchatsvc.gen.ttypes import Message, MessageType

from trpycore.timezone import tz

from trsvcscore.models import ChatMinute, ChatSpeakingMarker,\
    ChatTag, ChatMessageType

class ChatMessageHandler(object):
    """
        Handler to process a chat message by creating the associated
        entity (Tag, Minute, Marker, etc) and storing it in the db.

        This handler is responsible for:
            1) Filtering out messages that don't need to be persisted
            2) Creating model instances from chat messages
            3) Persisting model instances
    """
    def __init__(self, db_session, chat_session_id):
        self.log = logging.getLogger(__name__)
        self.db_session = db_session
        self.chat_session_id = chat_session_id

        # Retrieve chat message type IDs
        self.MARKER_CREATE_TYPE = db_session.query(ChatMessageType).filter(ChatMessageType.name=='MARKER_CREATE').one().id

        # Create handlers for each type of message we need to persist
        self.chat_marker_handler = ChatMarkerHandler()
        self.chat_minute_handler = ChatMinuteHandler(self.chat_session_id)
        self.chat_tag_handler = ChatTagHandler(self.chat_session_id)


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

        if message.header.type == MessageType.MINUTE_CREATE:
            print 'handling minute create message id=%s' % message.minuteCreateMessage.minuteId
            ret = self.chat_minute_handler.create_model(message)
            if ret is not None:
                self.db_session.add(ret)
                self.db_session.flush() # force a flush so that the chat minute object gets an ID
                self.chat_minute_handler.set_active_minute(ret)

        elif message.header.type == MessageType.MINUTE_UPDATE:
            print 'handling minute update message id=%s' % message.minuteUpdateMessage.minuteId
            ret = self.chat_minute_handler.update_model(message)
            if ret is not None:
                self.db_session.add(ret)

#        elif message_type.id == self.MARKER_CREATE_TYPE:
#            ret = self.chat_marker_handler.create_model(
#                message,
#                self.chat_minute_handler.get_active_minute().id)
#            if (ret is not None):
#                db_session.add(ret)
#
        elif message.header.type == MessageType.TAG_CREATE:
            print 'handling tag create message id=%s' % message.tagCreateMessage.tagId
            ret = self.chat_tag_handler.create_model(
                message,
                self.chat_minute_handler.get_active_minute().id)
            if ret is not None:
                self.db_session.add(ret)

        elif message.header.type == MessageType.TAG_DELETE:
            print 'handling tag delete message id=%s' % message.tagDeleteMessage.tagId
            ret = self.chat_tag_handler.delete_model(message)
            if ret is not None:
                self.db_session.add(ret)

        return ret


class ChatMinuteHandler(object):
    """
        Handler for Chat Minute messages.

        This class creates model instances
        from chat minute messages and persists
        them to the db.

        This class is also responsible for
        defining and applying the business rules to handle
        duplicate messages and filtering any unwanted messages.

        This class also maintains the active chat minute.
        """

    def __init__(self, chat_session_id):
        self.log = logging.getLogger(__name__)
        self.chat_session_id = chat_session_id
        self.active_minute_stack = [] # stores chat_minute models
        self.all_minutes = {} # includes invalid chat messages that were not persisted, if any

    def set_active_minute(self, chat_minute):
        # We set the active minute via this method so that we can
        # set the active after the db_session has been flushed.
        self.active_minute_stack.append(chat_minute)
        self.log.debug('The new active chat minute id=%s' % chat_minute.id)

    def get_active_minute(self):
        # The active minute is the last minute added to the stack
        return self.active_minute_stack[-1]

    def create_model(self, message):
        """
            Create model instance from Thrift Message

            Returns None if creation failed.
            Creation can fail if the input message fails to pass biz rules filter.
        """
        ret = None

        # Create model from message
        if (self._is_valid_create_message(message)):
            start_time = tz.timestamp_to_utc(message.minuteCreateMessage.startTimestamp)
            ret = ChatMinute(
                chat_session_id=self.chat_session_id,
                start=start_time,
                end=None)

        # Store message and its associated model for easy reference,
        # (specifically for minuteID look-ups on minute-update messages)
        minute_data = JobData(message.minuteCreateMessage.minuteId, message, None, ret)
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
        minute_id = message.minuteUpdateMessage.minuteId

        if (self._is_valid_update_message(message)):
            # Update the minute model with the end timestamp
            minute_data = self.all_minutes[minute_id]
            minute_model = minute_data.get_model()
            end_time = tz.timestamp_to_utc(message.minuteUpdateMessage.endTimestamp)
            minute_model.end = end_time
            ret = minute_model
            # Pop the active minute off the stack
            self.active_minute_stack.pop()

        # Overwrite existing chat minute data with the newly updated data
        # TODO is this the best way?
        minute_data = JobData(minute_id, message, None, ret)
        self.all_minutes[minute_id] = minute_data

#        # Update state
#        if ret is not None:
#            # Overwrite the model data associated
#            # with the minute create message
#            # to reflect its new updated state.
#            minute_data = self.all_minutes[minute_id]
#            minute_data.set_model(ret)
#            self.all_minutes[minute_id] = minute_data

        return ret

    def _is_valid_create_message(self, message):
        """
            Returns True if message should be persisted, returns False otherwise.
        """
        ret = False

        # Chat messages are guaranteed to be unique due to the message_id attribute that each
        # message possesses.  This means we can avoid a duplicate message ID check here.

        # TODO add timestamp check to ensure it doesn't precede the previous minute?

        ret = True
        return ret

    def _is_valid_update_message(self, message):
        """
            Returns True if message should be persisted, returns False otherwise.
        """
        ret = False
        minute_id = message.minuteUpdateMessage.minuteId
        if (minute_id in self.all_minutes):
            minute_data = self.all_minutes[minute_id]
            minute_model = minute_data.get_model()
            # if minuteID has an associated model, then we tried to persist the message
            if (minute_model is not None):
                # Since we process messages chronologically, ensure that the referenced minuteID
                # is also the active chat minute. This will also prevent us from processing
                # duplicate update minute messages, if any.
                if(minute_model is self.active_minute_stack[-1]):
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
    #TODO Jeff wanted to detect if the current speaking marker was too large

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

    def __init__(self, chat_session_id):
        self.chat_session_id = chat_session_id
        self.log = logging.getLogger(__name__)
        self.all_tags = {}

    def create_model(self, message, chat_minute_id):
        """
            Create model instance

            Returns None if creation failed.
            Creation can fail if the input message fails to pass biz rules filter.
        """
        ret = None

        # Create the model from the message
        if self._is_valid_create_tag_message(message):
            ret = ChatTag(
                user_id=message.header.userId,
                chat_minute_id=chat_minute_id,
                tag_id=message.tagCreateMessage.tagReferenceId,
                name=message.tagCreateMessage.name)

        # Store message and its data for easy reference,
        # (specifically for tagID look-ups on tag delete messages)
        tag_data = JobData(message.tagCreateMessage.tagId, message, None, ret)
        self.all_tags[tag_data.id] = tag_data

        return ret

    def delete_model(self, message):
        """
            Delete model instance.

            Handles marking a chat tag model for delete.
            Returns the updated model instance.
            Returns None if message is invalid.
        """
        ret = None

        # Update model
        tag_id = message.tagDeleteMessage.tagId
        if self._is_valid_delete_tag_message(message):
            tag_data = self.all_tags[tag_id]
            tag_model = tag_data.get_model()
            tag_model.deleted = True
            ret = tag_model

        # Update state
        if ret is not None:
            # Overwrite the model data associated
            # with the tag create message
            # to reflect its new deleted state.
            tag_data = self.all_tags[tag_id]
            tag_data.set_model(ret)
            self.all_tags[tag_id] = tag_data

        return ret

    def _is_valid_create_tag_message(self, message):
        """
            Returns True if message should be persisted, returns False otherwise.
        """
        ret = False

        # Chat messages are guaranteed to be unique due to the message_id attribute that each
        # chat message possesses.  This means we can avoid a duplicate messageID check here.

        # Check for duplicate tagID to prevent overwriting existing tag data
        tag_id = message.tagCreateMessage.tagId
        if tag_id in self.all_tags:
            self.log.warning('Attempted to create tag with duplicate tagID=%s' % tag_id)
            return ret

        # TODO Prevent adding the same tag within the same chat minute
        ret = True
        return ret

    def _is_valid_delete_tag_message(self, message):
        """
            Returns True if message should be persisted, returns False otherwise.
        """
        ret = False
        tag_id = message.tagDeleteMessage.tagId
        if tag_id in self.all_tags:
            tag_data = self.all_tags[tag_id]
            tag_model = tag_data.get_model()
            # if tagID has an associated model, then we tried to persist the message
            if tag_model is not None:
                # Ensure that the model hasn't already been marked for delete
                if not tag_model.deleted:
                    ret = True

        return ret



class JobData(object):
    """
        Data structure to maintain references to a chat message's
        associated message, decoded message data, and model.

        The id parameter represents a tagId, minuteId, or markerId.
        This data is included in the chat message data blob.
    """
    def __init__(self, id, message, message_data=None, model=None):
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