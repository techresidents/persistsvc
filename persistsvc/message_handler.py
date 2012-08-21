import datetime
import logging

from trchatsvc.gen.ttypes import Message, MessageType, MarkerType
from trsvcscore.db.models import ChatMinute, ChatSpeakingMarker,\
    ChatTag
from trpycore.timezone import tz

from topic_data_manager import TopicDataManager, TopicData


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

        # Generate list of topics
        topics_manager = TopicDataManager()
        topic_id = topics_manager.get_root_topic_id(self.db_session, self.chat_session_id)
        self.topics = topics_manager.get_collection(self.db_session, topic_id)

        # Create handlers for each type of message we need to persist
        self.chat_marker_handler = ChatMarkerHandler()
        self.chat_minute_handler = ChatMinuteHandler(self.chat_session_id, self.topics)
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
            #print 'handling minute create message id=%s' % message.minuteCreateMessage.minuteId
            ret = self.chat_minute_handler.create_models(message)
            if ret is not None:
                for model in ret:
                    self.db_session.add(model)
                self.db_session.flush() # force a flush so that the chat minute object gets an ID
                self.chat_minute_handler.set_active_minute(ret[0]) #TODO clean up, make more robust

        elif message.header.type == MessageType.MINUTE_UPDATE:
            #print 'handling minute update message id=%s' % message.minuteUpdateMessage.minuteId
            ret = self.chat_minute_handler.update_models(message)
            if ret is not None:
                for model in ret:
                    self.db_session.add(model)

#        elif message.header.type == MessageType.MARKER_CREATE:
#            print 'handling marker create message id=%s' % message.markerCreateMessage.markerId
#            ret = self.chat_marker_handler.create_model(
#                message,
#                165) # TODO was testing just speaking markers
#            # TODO need to handle if there's no active chat minute yet
#            if ret is not None:
#                db_session.add(ret)

#        elif message.header.type == MessageType.TAG_CREATE:
#            #print 'handling tag create message id=%s' % message.tagCreateMessage.tagId
#            ret = self.chat_tag_handler.create_model(
#                message,
#                self.chat_minute_handler.get_active_minute().id)
#            if ret is not None:
#                self.db_session.add(ret)
#
#        elif message.header.type == MessageType.TAG_DELETE:
#            #print 'handling tag delete message id=%s' % message.tagDeleteMessage.tagId
#            ret = self.chat_tag_handler.delete_model(message)
#            if ret is not None:
#                self.db_session.add(ret)

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
    DEFAULT_MINUTE_START_TIME = 0

    def __init__(self, chat_session_id, topics_collection):
        self.chat_session_id = chat_session_id
        self.topics_collection = topics_collection
        self.log = logging.getLogger(__name__)
        self.active_minute = None
        self.minute_end_topic_chain = self._get_chat_minute_end_topic_chain(topics_collection)

        self.topic_minute_map = {}
        for topic in self.topics_collection.as_list_by_rank():
            minute = ChatMinute(
                chat_session_id=self.chat_session_id,
                topic_id=topic.id,
                start=self.DEFAULT_MINUTE_START_TIME,
                end=None)
            self.topic_minute_map[topic.id] = minute


    def _get_highest_ranked_leafs(self, topics_collection):
        """
            Method to retrieve the leaf topics which have the
            highest relative rank amongst their siblings.

            The leafs returned from this method will be responsible
            for potentially closing their parent's chat minutes.
        """
        ret = []
        leaf_list = topics_collection.get_leaf_list_by_rank()
        for leaf_topic in leaf_list:
            next_topic = self.topics_collection.get_next_topic(leaf_topic)
            if next_topic is None or \
               next_topic.level < leaf_topic.level:
                ret.append(leaf_topic)
        return ret

    def _get_chat_minute_end_topic_chain(self, topics_collection):
        """
            Method to create a topic chain dictionary which describes
            which parent topics each leaf topic is responsible for closing
            (setting the chat-minute-end time).
        """
        minute_end_topic_chain = {}
        leaf_list = topics_collection.get_leaf_list_by_rank()
        highest_leafs = self._get_highest_ranked_leafs(topics_collection)
        for topic in highest_leafs:

            # We need to match the closing level of each leaf's next-topic.
            next_topic = topics_collection.get_next_topic(topic)
            # Close up to root level for last leaf topic in topic hierarchy
            root_topic_level = 1
            level_to_close = next_topic.level if next_topic is not None else root_topic_level

            topic_parents_to_end_list = []
            # All leafs guaranteed to have at least one previous topic
            current_topic = topics_collection.get_previous_topic(topic)
            current_closing_level = topic.level
            while current_topic.level >= level_to_close:
                if current_topic not in leaf_list:
                    # We only want parents. No children allowed
                    if current_topic.level < current_closing_level:
                        # There will only ever be one topic per level that we need to close.
                        # Thus, every time we add a parent, decrement the current level.
                        topic_parents_to_end_list.append(current_topic)
                        current_closing_level -= 1
                current_topic = topics_collection.get_previous_topic(current_topic)
                if current_topic is None:
                    break


            minute_end_topic_chain[topic.id] = topic_parents_to_end_list

        return minute_end_topic_chain

    def set_active_minute(self, chat_minute):
        # We set the active minute via this method so that we can
        # set the active after the db_session has been flushed.
        self.active_minute = chat_minute
        self.log.debug('The new active chat minute id=%s' % chat_minute.id)

    def get_active_minute(self):
        # The active minute is the last minute added to the stack
        return self.active_minute

    def _start_parent_topic_minutes(self, topic_id, start_time):
        """
            Method responsible for starting any parent topics
            that have not yet been started.
        """
        ret = []
        topics = self.topics_collection.as_dict()
        topic = topics[topic_id]

        previous_topic = self.topics_collection.get_previous_topic(topic)
        while previous_topic is not None:
            minute = self.topic_minute_map[previous_topic.id]
            if minute.start == self.DEFAULT_MINUTE_START_TIME:
                # This topic hasn't been started yet, so start it
                minute.start = start_time
                ret.append(minute)
            else:
                # All prior topics have now been started, so we can stop
                break
            previous_topic = self.topics_collection.get_previous_topic(previous_topic)

        return ret

    def _end_previous_topic_minutes(self, topic_id, end_time):
        """
            Method responsible for ending the previous topic(s).
        """
        ret = []

        # We start at the previous leaf topic because only leaf topics
        # are actually discussed during a chat.
        previous_leaf = self.topics_collection.get_previous_leaf_by_id(topic_id)
        if previous_leaf is not None:

            # Update this leaf's end time
            minute = self.topic_minute_map[previous_leaf.id]
            minute.end = end_time
            ret.append(minute)

            # Update parent's end times, if needed
            parent_topics_to_end = self.minute_end_topic_chain.get(previous_leaf.id)
            if parent_topics_to_end is not None:
                for topic in parent_topics_to_end:
                    minute = self.topic_minute_map[topic.id]
                    minute.end = end_time
                    ret.append(minute)

        return ret

    def create_models(self, message):
        """
            Create model instance from Thrift Message

            Returns None if creation failed.
            Creation can fail if the input message fails to pass biz rules filter.
        """
        ret = None

        # Create models from message
        if self._is_valid_create_message(message):

            ret = []
            topic_id = message.minuteCreateMessage.topicId
            start_time = tz.timestamp_to_utc(message.minuteCreateMessage.startTimestamp)

            # Update this topic's start time
            minute = self.topic_minute_map[topic_id]
            minute.start = start_time
            ret.append(minute)

            # Update parent topic's start time
            models = self._start_parent_topic_minutes(topic_id, start_time)
            ret.extend(models)

            # Update previous topic's end-times
            models = self._end_previous_topic_minutes(topic_id, start_time)
            ret.extend(models)

        return ret

    def update_models(self, message):

        ret = None

        if self._is_valid_update_message(message):

            ret = []
            topic_id = message.minuteUpdateMessage.topicId
            end_time = tz.timestamp_to_utc(message.minuteUpdateMessage.endTimestamp)

            # Update this final leaf's end time
            minute = self.topic_minute_map[topic_id]
            minute.end = end_time
            ret.append(minute)

            # Update parent's end times
            # Expecting at least the root topic to be updated here
            parent_topics_to_end = self.minute_end_topic_chain[topic_id]
            for topic in parent_topics_to_end:
                minute = self.topic_minute_map[topic.id]
                minute.end = end_time
                ret.append(minute)

        return ret

    def _is_valid_create_message(self, message):
        """
            Returns True if message should be persisted, returns False otherwise.
        """
        ret = False

        # Chat messages are guaranteed to be unique due to the message_id attribute that each
        # message possesses.  This means we can avoid a duplicate message ID check here.

        # TODO add timestamp check to ensure it doesn't precede the previous minute?

        # Topic ID must be present in the topic collection
        topic_id = message.minuteCreateMessage.topicId
        if topic_id in self.topics_collection.as_dict():

            # We will only accept minute-create-messages when they pertain to leaf-topics.
            # This is done because we couldn't rely upon the ordering of messages (e.g.
            # the parent minute-create-msg arriving before the child's minute-create-msg).
            # By only allowing minute-create-msgs from leaf topics we can manually create
            # parent chat minutes.
            if self.topics_collection.is_leaf_topic_by_id(topic_id):
                print 'Valid message %s with topic id %s' % (message.minuteCreateMessage.minuteId, topic_id)
                ret = True

        return ret

    def _is_valid_update_message(self, message):
        """
            Returns True if message should be persisted, returns False otherwise.

            The only update message we are looking for is the one that ends the
            last topic in the chat.
        """
        ret = False
        topic_id = message.minuteUpdateMessage.topicId

        # Topic ID must be present in the topic collection
        topic = self.topics_collection.as_dict().get(topic_id)
        if topic is not None:
            if self.topics_collection.is_leaf_topic(topic):
                if self.topics_collection.get_next_topic(topic) is None:
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
    SPEAKING_DURATION_THRESHOLD = 0 # 30 secs in millis
    #TODO Jeff wanted to detect if the current speaking marker was too large

    def __init__(self):
        self.log = logging.getLogger(__name__)
        self.all_markers = {}
        self.speaking_state = {}

    def create_model(self, message, chat_minute_id):
        """
            Create model instance

            Returns None if creation failed.
            Creation can fail if the input message fails to pass biz rules filter.
        """
        ret = None

        if self._is_valid_message(message):

            # Only expecting & handling speaking markers for now

            # Get user's speaking state
            user_id = message.header.userId
            user_speaking_data = None
            if user_id not in self.speaking_state:
                user_speaking_data = SpeakingData(user_id)
            else:
                user_speaking_data = self.speaking_state[user_id]

            # Determine if the speaking minute has ended and we need to persist the marker
            if message.markerCreateMessage.marker.speakingMarker.isSpeaking:
                # msg indicates user started speaking
                if not user_speaking_data.is_speaking():
                    # If user wasn't already speaking, process msg.
                    # Ignore duplicate speaking_start markers.
                    user_speaking_data.set_start_timestamp(message.header.timestamp)
                    user_speaking_data.set_speaking(True)
            else:
                # msg indicates user stopped speaking
                if user_speaking_data.is_speaking():
                    # If user was already speaking, process msg.
                    # Ignore duplicate speaking_end markers.
                    user_speaking_data.set_end_timestamp(message.header.timestamp)
                    duration = user_speaking_data.calculate_speaking_duration()
                    if duration > SPEAKING_DURATION_THRESHOLD:
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
        marker_data = MessageData(message.markerCreateMessage.markerId, message, ret)
        self.all_markers[marker_data.id] = marker_data

        return ret

    def _is_valid_message(self, message):
        """
            Returns True if message should be persisted, returns False otherwise.

            Only passes speaking markers.
        """
        ret = False

        # Chat messages are guaranteed to be unique due to the message_id attribute that each
        # message possesses.  This means we can avoid a duplicate message ID check here.

        print 'marker type is: %s' % message.markerCreateMessage.marker.type
        if message.markerCreateMessage.marker.type == MarkerType.SPEAKING_MARKER:
            print 'valid speaking marker'
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
                name=message.tagCreateMessage.name,
                deleted=False)

        # Store message and its data for easy reference,
        # (specifically for tagID look-ups on tag delete messages)
        tag_data = MessageData(message.tagCreateMessage.tagId, message, ret)
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

        # TODO handle exception if tag violates unique together constraint (user, minute, name)
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



class MessageData(object):
    """
        Data structure to maintain references to a chat message's
        associated message and model.
    """
    def __init__(self, id, message, model=None):
        self.id = id
        self.message = message
        self.model = model

    def set_message(self, message):
        self.message = message

    def get_message(self):
        return self.message

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