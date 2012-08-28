import abc
import logging

from persistsvc_exceptions import \
    DuplicateTagIdException, \
    InvalidChatMinuteException,\
    NoActiveChatMinuteException, \
    TagIdDoesNotExistException, \
    TopicIdDoesNotExistException
from trchatsvc.gen.ttypes import Message, MessageType, MarkerType
from trsvcscore.db.models import ChatMinute, ChatSpeakingMarker,\
    ChatTag
from trpycore.timezone import tz


class MessageHandler(object):
    """MessageHandler abstract base class.

    Base class for concrete chat message handler implementations.
    The concrete ChatMessageHandler class processes all ChatMessages
    and delegates to specific handlers that implement this
    interface.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(
            self,
            chat_message_handler):
        """MessageHandler constructor.

        Args:
            chat_message_handler: ChatMessageHandler object
        """
        self.chat_message_handler = chat_message_handler
        self.chat_session_id = self.chat_message_handler.chat_session_id

    @abc.abstractmethod
    def initialize(self):
        """Hook to allow any initialization to be completed
        before processing chat messages.

        """
        return

    @abc.abstractmethod
    def finalize(self):
        """Hook to allow any operations to be completed
        after all chat messages have been consumed.

        This method is also responsible for returning
        all models to persist. It should be called
        after processing all messages in a chat.

        Returns:
            List of models to persist.

        """
        return

    @abc.abstractmethod
    def create_models(self, message):
        """Create model instance(s) from Thrift Message

        Args:
            message: Deserialized Thrift Message

        Returns:
            List of models to persist.
            None if creation failed.
            Creation can fail if the input chat message fails to pass biz rules filter.
        """
        return

    @abc.abstractmethod
    def update_models(self, message):
        """Update model instance(s) from Thrift Message

        Args:
            message: Deserialized Thrift Message

        Returns:
            List of models to persist.
            None if update(s) failed.
            Updates can fail if the input chat message fails to pass biz rules filter.
        """
        return

    @abc.abstractmethod
    def delete_models(self, message):
        """Delete model instance(s) from Thrift Message

        Args:
            message: Deserialized Thrift Message

        Returns:
            List of models to persist.
            None if deletion(s) failed.
            Deletions can fail if the input chat message fails to pass biz rules filter.
        """
        return

class ChatMessageHandler(object):
    """
        Handler to process a chat message by creating the associated
        entity (Tag, Minute, Marker, etc) and storing it in the db.

        This handler is responsible for:
            1) Filtering out messages that don't need to be persisted
            2) Creating model instances from chat messages
    """
    def __init__(self, chat_session_id, topics_collection):
        self.log = logging.getLogger(__name__)
        self.chat_session_id = chat_session_id
        self.topics_collection = topics_collection

        # Create handlers for each type of message we need to persist
        self.chat_marker_handler = ChatMarkerHandler(self)
        self.chat_minute_handler = ChatMinuteHandler(self)
        self.chat_tag_handler = ChatTagHandler(self)

        # Initialize handlers
        self.chat_marker_handler.initialize()
        self.chat_minute_handler.initialize()
        self.chat_tag_handler.initialize()


    def finalize(self):
        """
            Invoke to indicate that all chat messages have been consumed.

            Returns:
                List of models to persist.
        """
        ret = []
        ret.extend(self.chat_minute_handler.finalize())
        ret.extend(self.chat_marker_handler.finalize())
        ret.extend(self.chat_tag_handler.finalize())
        return ret

    def process(self, message):
        """
            Converts input deserialized Thrift Message to a model instance based upon the
            chat message's type.

            This method is the orchestrator of persisting all the chat entities
            that need to be stored.  Some handlers input one message and
            return multiple models to be persisted.
        """
        try:
            if message.header.type == MessageType.MINUTE_CREATE:
                self.log.debug('handling minute create message id=%s' % message.minuteCreateMessage.minuteId)
                self.chat_minute_handler.create_models(message)

            elif message.header.type == MessageType.MINUTE_UPDATE:
                self.log.debug('handling minute update message id=%s' % message.minuteUpdateMessage.minuteId)
                self.chat_minute_handler.update_models(message)

            elif message.header.type == MessageType.MARKER_CREATE:
                self.log.debug('handling marker create message id=%s' % message.markerCreateMessage.markerId)
                self.chat_marker_handler.create_models(message)

            elif message.header.type == MessageType.TAG_CREATE:
                self.log.debug('handling tag create message id=%s' % message.tagCreateMessage.tagId)
                self.chat_tag_handler.create_models(message)

            elif message.header.type == MessageType.TAG_DELETE:
                self.log.debug('handling tag delete message id=%s' % message.tagDeleteMessage.tagId)
                self.chat_tag_handler.delete_models(message)

        except TagIdDoesNotExistException as e:
            self.log.warning('Attempted to access tag with tagID=%s', e.id)
        except DuplicateTagIdException as e:
            self.log.warning('Attempted to create tag with duplicate tagID=%s' % e.id)
        except NoActiveChatMinuteException as e:
            # TODO We probably want to handle this differently depending on which handler it came from.
            self.log.warning('Attempted to process chat message with no active chat minute')


class ChatMinuteHandler(MessageHandler):
    """
        Handler for Chat Minute messages.

        This class creates/updates/deletes ChatMinute model instances.
        Each instance of this class should be used to process
        all messages from a chat.  Call finalize() after processing
        all messages to return all models to persist.

        This class is responsible for
        defining and applying the business rules to handle
        duplicate messages and filtering any unwanted messages.

        This class also maintains the active chat minute state.
        """
    DEFAULT_MINUTE_START_TIME = 0

    def __init__(self, chat_message_handler):
        super(ChatMinuteHandler, self).__init__(chat_message_handler)
        self.log = logging.getLogger(__name__)
        self.topics_collection = chat_message_handler.topics_collection

        # Maintain the active chat minute
        # Chat messages are expected to be consumed in chronological order.
        self.active_minute = None

        # Maintain a map of topics to chat minute models
        self.topic_minute_map = {}   # {topic_id : chatMinute model}

        # Maintain a dict which indicates which describes
        # which parent topics each leaf topic is responsible
        # for closing (setting the chat-minute's end time).
        # { leaf_topic_id : [parent1_topic_id, parent2_topic_id, ...] }
        self.minute_end_topic_chain = self._get_chat_minute_end_topic_chain(self.topics_collection)


    def _get_highest_ranked_leafs(self, topics_collection):
        """
            Method to retrieve the leaf topics which have the
            highest relative rank amongst their siblings.

            The leafs returned from this method will be responsible
            for closing their parent's chat minutes.

            As a simple example, consider the following topic hierarchy:

                Root
                    Topic1
                    Topic2
                        Topic3
                    Topic4

                The highest ranked leafs here are:
                [Topic3, Topic4]

            Args:
                topics_collection: the chat's associated TopicCollection
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
            which parent topics each leaf topic is responsible for 'closing'
            (setting the chat-minute-end time).

            As a simple example, consider the following topic hierarchy:

                Root
                    Topic1
                    Topic2
                        Topic3
                    Topic4

                The output dictionary would be:
                { Topic3.id : [Topic2],
                  Topic4.id : [Root]}

            Args:
                topics_collection: the chat's associated TopicCollection
        """
        minute_end_topic_chain = {}
        leaf_list = topics_collection.get_leaf_list_by_rank()
        highest_leafs = self._get_highest_ranked_leafs(topics_collection)
        for topic in highest_leafs:

            # We need to match the closing level of each leaf's next-topic.
            next_topic = topics_collection.get_next_topic(topic)

            # Close up to root level for the last leaf topic in topic hierarchy
            root_topic_level = 1
            level_to_close = next_topic.level if next_topic is not None else root_topic_level

            topic_parents_to_end_list = []
            # All leafs guaranteed to have at least one previous topic
            current_topic = topics_collection.get_previous_topic(topic)
            current_closing_level = topic.level
            while current_topic.level >= level_to_close:
                if current_topic not in leaf_list:
                    # We only want parents. No children allowed.
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

    def _set_active_minute(self, chat_minute):
        """
            The Chat Minute Handler class is responsible for
            setting the active minute using this method.
        """
        self.active_minute = chat_minute

    def get_active_minute(self):
        """
            Returns the active chat minute.
        """
        return self.active_minute

    def _start_parent_topic_minutes(self, topic_id, start_time):
        """
            Method responsible for setting the start time on
            parent topic chat minutes.

            This method will traverse backward through the
            topic list ordered by increasing rank.
            It will begin at the topic passed in and
            start any parent topics that have not yet been started.

            Args:
                topic_id: the topic ID of the newly started topic
                start_time: the start time to apply
        """
        topics = self.topics_collection.as_dict()
        topic = topics[topic_id]

        previous_topic = self.topics_collection.get_previous_topic(topic)
        while previous_topic is not None:
            minute = self.topic_minute_map[previous_topic.id]
            if minute.start == self.DEFAULT_MINUTE_START_TIME:
                # This topic hasn't been started yet, so start it
                minute.start = start_time
            else:
                # All prior topics have now been started, so we can stop
                break
            previous_topic = self.topics_collection.get_previous_topic(previous_topic)

        return

    def _end_previous_topic_minutes(self, topic_id, end_time):
        """
            Method responsible for setting the end time on
            chat minutes. This method will find the topics that need
            to be 'closed' by keying off of the input leaf topic.

            This method is expected to be called when each next leaf
            topic is started. It is not expected to be called for
            the very last leaf topic since there will be no next
            topic started.

            Args:
                topic_id: the topic ID of newly started topic
                end_time: the end time to apply
        """

        # We start at the previous leaf topic because only leaf topics
        # are actually discussed during a chat.
        previous_leaf = self.topics_collection.get_previous_leaf_by_id(topic_id)
        if previous_leaf is not None:

            # Update this leaf's end time
            minute = self.topic_minute_map[previous_leaf.id]
            minute.end = end_time

            # Update parent's end times, if needed
            parent_topics_to_end = self.minute_end_topic_chain.get(previous_leaf.id)
            if parent_topics_to_end is not None:
                for topic in parent_topics_to_end:
                    minute = self.topic_minute_map[topic.id]
                    minute.end = end_time

    def initialize(self):
        """
            Hook to allow any initialization to be completed
            before processing chat messages.
        """

        # Create a ChatMinute object for each topic that exists.
        # As the chat messages are processed each chat minute's
        # start and end time will be modified.
        for topic in self.topics_collection.as_list_by_rank():
            minute = ChatMinute(
                chat_session_id=self.chat_session_id,
                topic_id=topic.id,
                start=self.DEFAULT_MINUTE_START_TIME,
                end=None)
            self.topic_minute_map[topic.id] = minute
        return

    def finalize(self):
        """
            Hook to allow any operations to be completed
            after all chat messages have been consumed.

            This method is also responsible for returning
            all models to persist. It should be called
            after processing all messages in a chat.

            Throws:
                Raises a InvalidChatMinuteException if any of the
                ChatMinute models are invalid (e.g. No start time
                or no end time specified).

            Returns:
                List of models to persist ordered by topic rank
        """
        models_to_persist = []

        for topic in self.topics_collection.as_list_by_rank():
            model = self.topic_minute_map[topic.id]
            if model.start == self.DEFAULT_MINUTE_START_TIME or\
               model.end is None:
                raise InvalidChatMinuteException()
            models_to_persist.append(model)

        return models_to_persist

    def create_models(self, message):
        """
            Create model instance(s) from input message.
            Need to call finalize() after processing
            all the message in a chat to get the created
            instances.

            Args:
                message: Deserialized Thrift Message

            Throws:
                TopicIdDoesNotExistException
        """
        # Create models from message
        if self._is_valid_create_message(message):

            topic_id = message.minuteCreateMessage.topicId
            start_time = tz.timestamp_to_utc(message.minuteCreateMessage.startTimestamp)

            # Update this topic's start time
            minute = self.topic_minute_map[topic_id]
            minute.start = start_time
            self._set_active_minute(minute)

            # Update parent topic's start time
            self._start_parent_topic_minutes(topic_id, start_time)

            # Update previous topic's end-times
            self._end_previous_topic_minutes(topic_id, start_time)

    def update_models(self, message):
        """
            Update model instance(s) from Thrift Message

            This method is responsible for listening for a
            MinuteUpdateMessage on the last topic in a chat.
            Once received, this method will generate
            end-timestamps for the ChatMinute's that require it
            (the root topic and any parents of the final leaf topic).

            Note that for all other topics, the end-timestamps
            are written when a new minuteCreateMessage comes in
            via create_models().The reason that messages are processed this
            way is that the message order of minuteStart and minuteEnd
            messages was not guaranteed to be in chronological order
            since the time between these successive messages
            was so close (any network latency in one message
            but not the other was enough to change the order).

            Args:
                message: Deserialized Thrift Message

            Throws:
                TopicIdDoesNotExistException

        """
        if self._is_valid_update_message(message):

            topic_id = message.minuteUpdateMessage.topicId
            end_time = tz.timestamp_to_utc(message.minuteUpdateMessage.endTimestamp)

            # Update this final leaf's end time
            minute = self.topic_minute_map[topic_id]
            minute.end = end_time

            # Update parent's end times
            # Expecting at least the root topic to be updated here
            parent_topics_to_end = self.minute_end_topic_chain[topic_id]
            for topic in parent_topics_to_end:
                minute = self.topic_minute_map[topic.id]
                minute.end = end_time

    def delete_models(self, message):
        raise NotImplementedError

    def _is_valid_create_message(self, message):
        """
            Args:
                message: deserialized Thrift Message

            Returns:
                True if message should be persisted, False otherwise.

            Throws:
                TopicIdDoesNotExistException
        """
        ret = False

        # Chat messages are guaranteed to be unique due to the message_id attribute that each
        # message possesses.  This means we can avoid a duplicate message ID check here.

        topic_id = message.minuteCreateMessage.topicId

        # Topic ID must be present in the topic collection
        if topic_id not in self.topics_collection.as_dict():
            raise TopicIdDoesNotExistException()

        # We will only accept minute-create-messages when they pertain to leaf-topics.
        # This is done because we couldn't rely upon the ordering of messages (e.g.
        # the parent minute-create-msg arriving before the child's minute-create-msg).
        # By only allowing minute-create-msgs from leaf topics we can manually create
        # parent chat minutes.
        if self.topics_collection.is_leaf_topic_by_id(topic_id):
            ret = True

        return ret

    def _is_valid_update_message(self, message):
        """
            The only update message we are looking for is the one that ends the
            last topic in the chat.

            Args:
                message: deserialized Thrift Message

            Returns:
                True if message should be persisted, False otherwise.

            Throws:
                TopicIdDoesNotExistException
        """
        ret = False
        topic_id = message.minuteUpdateMessage.topicId

        # Topic ID must be present in the topic collection
        if topic_id not in self.topics_collection.as_dict():
            raise TopicIdDoesNotExistException()

        # Only update chat minutes when on leaf topics
        topic = self.topics_collection.as_dict().get(topic_id)
        if self.topics_collection.is_leaf_topic(topic):
            # Only listening for the last chat minute msg in the chat
            if self.topics_collection.get_next_topic(topic) is None:
                ret = True

        return ret

class ChatMarkerHandler(MessageHandler):
    """
        Handler for Chat Marker messages

        This class creates/updates/deletes ChatSpeakingMarker model instances.
        Each instance of this class should be used to process
        all messages from a chat.  Call finalize() after processing
        all messages to return all models to persist.

        This class is also responsible for
        defining and applying the business rules to handle
        duplicate messages and filtering unwanted messages.
        """

    SPEAKING_DURATION_THRESHOLD = 0 # Persist all speaking markers
    #TODO Detect if the current speaking marker gets too large


    def __init__(self, chat_message_handler):
        super(ChatMarkerHandler, self).__init__(chat_message_handler)
        self.log = logging.getLogger(__name__)
        self.all_markers = {}   # {markerID : MessageModelData}
        self.speaking_state = {}

    def initialize(self):
        """
            Hook to allow any initialization to be completed
            before processing chat messages.
        """
        # Nothing to do.
        return

    def finalize(self):
        """
            Hook to allow any operations to be completed
            after all chat messages have been consumed.

            This method is also responsible for returning
            all models to persist. It should be called
            after processing all messages in a chat.

            Returns:
                List of models to persist.
        """
        models_to_persist = []
        for message_model_data_obj in self.all_markers.values():
            model = message_model_data_obj.get_model()
            if model is not None:
                models_to_persist.append(model)

        # Sort list by timestamp and return
        models_to_persist.sort(key=lambda model: tz.utc_to_timestamp(model.start))

        return models_to_persist

    def create_models(self, message):
        """
            Create model instance(s) from input message.
            Need to call finalize() after processing
            all the message in a chat to get the created
            instances.

            Args:
                message: Deserialized Thrift Message

            Throws:
                NoActiveChatMinuteException
        """
        created_model = None

        if self._is_valid_message(message):

            # Only expecting & handling speaking markers

            # The general approach for handling speaking markers is to
            # listen for a speaking-start marker and then wait for
            # the corresponding speaking-end.  All other duplicate speaking-start
            # markers for the specified user will be ignored until the
            # corresponding speaking-end message is received.  The reason
            # this is done because in a chat with 3 users, the two users
            # who are not speaking will generate duplicate speaking marker messages.
            # Models are created when the end-speaking marker is received.

            # Get user's speaking state
            user_id = message.markerCreateMessage.marker.speakingMarker.userId
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
                    # Ignore duplicate speaking_start markers. Once the first speaking start
                    # message is processed, we will ignore the rest until we receive a speaking
                    # end message.
                    user_speaking_data.set_start_timestamp(message.header.timestamp)
                    user_speaking_data.set_speaking(True)
            else:
                # msg indicates user stopped speaking
                if user_speaking_data.is_speaking():
                    # If user was already speaking, process msg.
                    # Ignore duplicate speaking_end markers. Once the first speaking end
                    # message is processed, we will ignore the rest until we receive a speaking
                    # start message.
                    user_speaking_data.set_end_timestamp(message.header.timestamp)

                    duration = user_speaking_data.calculate_speaking_duration()
                    if duration > self.SPEAKING_DURATION_THRESHOLD:
                        chat_minute = self.chat_message_handler.chat_minute_handler.get_active_minute()
                        start_time = tz.timestamp_to_utc(user_speaking_data.get_start_timestamp())
                        end_time = tz.timestamp_to_utc(user_speaking_data.get_end_timestamp())
                        created_model = ChatSpeakingMarker(
                            user_id=user_id,
                            chat_minute=chat_minute,
                            start=start_time,
                            end=end_time)

                    # Reset user's speaking state
                    user_speaking_data.set_start_timestamp(None)
                    user_speaking_data.set_end_timestamp(None)
                    user_speaking_data.set_speaking(False)

            # Update state
            self.speaking_state[user_id] = user_speaking_data

        # Store message and its associated model
        marker_data = MessageModelData(message.markerCreateMessage.markerId, message, created_model)
        self.all_markers[marker_data.id] = marker_data

    def update_models(self, message):
        raise NotImplementedError

    def delete_models(self, message):
        raise NotImplementedError

    def _is_valid_message(self, message):
        """
         Only passes speaking markers.

            Args:
                message: deserialized Thrift Message

            Returns:
             True if message should be persisted, False otherwise.

            Throws:
                NoActiveChatMinuteException
        """
        ret = False

        # Chat messages are guaranteed to be unique due to the message_id attribute that each
        # message possesses.  This means we can avoid a duplicate message ID check here.

        # If there is no active ChatMinute then reject this message
        chat_minute = self.chat_message_handler.chat_minute_handler.get_active_minute()
        if chat_minute is None:
            raise NoActiveChatMinuteException()

        if message.markerCreateMessage.marker.type == MarkerType.SPEAKING_MARKER:
            ret = True

        return ret

class ChatTagHandler(MessageHandler):
    """
        Handler for Chat Tag messages

        This class creates/updates/deletes ChatTag model instances.
        Each instance should be used to process messages from
        a chat.  Call finalize() after processing all messages
        to return all created tag models.

        This class is responsible for
        defining and applying the business rules to handle
        duplicate messages and filtering any unwanted messages.
        """

    def __init__(self, chat_message_handler):
        super(ChatTagHandler, self).__init__(chat_message_handler)
        self.log = logging.getLogger(__name__)
        self.all_tags = {}   # {tag_id : MessageModelData}

        # Create nested dict to ensure only unique tags are persisted.
        # Tags are considered unique across (user, minute, tag-name)
        # The tagID is needed here to perform lookups when tags are deleted.
        # {chat_minute : { tagId : userID+tagName
        #                  tagId: userID+tagName}
        self.tags_to_persist = {}

    def _update_tags_to_persist(self, chat_minute, message, deleted=False):
        """
            Store a tag's associated user, minute, and name to ensure uniqueness.
            We will only store a tag if it is unique when considering these
            three values together.
        """
        if not deleted:
            # Storing the tag as the concatenation of userID and tag name.
            tag_value = str(message.header.userId)+message.tagCreateMessage.name
            if chat_minute not in self.tags_to_persist:
                self.tags_to_persist[chat_minute] = {}
            self.tags_to_persist[chat_minute][message.tagCreateMessage.tagId] = tag_value
        else:
            # Delete the tag
            if chat_minute in self.tags_to_persist:
                if message.tagDeleteMessage.tagId in self.tags_to_persist[chat_minute]:
                    del self.tags_to_persist[chat_minute][message.tagDeleteMessage.tagId]

    def _is_duplicate_tag(self, chat_minute, message):
        """
            Check for duplicate tag by looking at the userID, minute, and tag name
            together.
        """
        ret = False
        if chat_minute not in self.tags_to_persist:
            # Need to create new dict if this is the 1st tag in the chat minute
            self.tags_to_persist[chat_minute] = {}
        else:
            tag_value = str(message.header.userId) + message.tagCreateMessage.name
            if tag_value in self.tags_to_persist[chat_minute].values():
                ret = True
        return ret

    def initialize(self):
        """
            Hook to allow any initialization to be completed
            before processing chat messages.
        """
        # Nothing to do.
        return

    def finalize(self):
        """
            Hook to allow any operations to be completed
            after all chat messages have been consumed.

            This method is also responsible for returning
            all models to persist. It should be called
            after processing all messages in a chat.

            Returns:
                List of models to persist.
        """
        data_to_persist = []
        for minute in self.tags_to_persist:
            for tag_id in self.tags_to_persist[minute].keys():
                data_to_persist.append(self.all_tags[tag_id])

        # Sort list by timestamp and extract the models to persist
        models_to_persist = []
        data_to_persist.sort(key=lambda d: d.get_message().header.timestamp)
        for message_model_data_obj in data_to_persist:
            models_to_persist.append(message_model_data_obj.get_model())

        return models_to_persist

    def create_models(self, message):
        """
            Create model instance(s) from input message.
            Need to call finalize() after processing
            all the message in a chat to get the created
            instances.

            Args:
                message: Deserialized Thrift Message

            Throws:
                DuplicateTagIdException
                NoActiveChatMinuteException
        """
        created_model = None

        if self._is_valid_create_tag_message(message):
            chat_minute = self.chat_message_handler.chat_minute_handler.get_active_minute()
            created_model = ChatTag(
                user_id=message.header.userId,
                chat_minute=chat_minute,
                tag_id=message.tagCreateMessage.tagReferenceId,
                name=message.tagCreateMessage.name,
                deleted=False)
            self._update_tags_to_persist(chat_minute, message)

        # Store message and its associated model for tagID look-ups on tag delete messages.
        tag_data = MessageModelData(message.tagCreateMessage.tagId, message, created_model)
        self.all_tags[tag_data.id] = tag_data

    def update_models(self, message):
        raise NotImplementedError

    def delete_models(self, message):
        """
            Delete model instance(s) based upon input message.

            Args:
                message: Deserialized Thrift Message

            Throws:
                NoActiveChatMinuteException
        """
        deleted_model = None

        # Mark the referenced ChatTag model as deleted
        tag_id = message.tagDeleteMessage.tagId
        if self._is_valid_delete_tag_message(message):
            tag_model = self.all_tags[tag_id].get_model()
            tag_model.deleted = True
            deleted_model = tag_model
            self._update_tags_to_persist(
                self.chat_message_handler.chat_minute_handler.get_active_minute(),
                message,
                deleted=True
            )

        # Update state
        if deleted_model is not None:
            # Overwrite the model data associated
            # with the tag create message
            # to reflect its new deleted state.
            tag_data = self.all_tags[tag_id]
            tag_data.set_model(deleted_model)
            self.all_tags[tag_id] = tag_data

    def _is_valid_create_tag_message(self, message):
        """
            Args:
                message: deserialized Thrift Message

            Returns:
             True if message should be persisted, False otherwise.

            Throws:
                DuplicateTagIdException
                NoActiveChatMinuteException
        """
        ret = True

        # Chat messages are guaranteed to be unique due to the message_id attribute that each
        # chat message possesses.  This means we can avoid a duplicate messageID check here.

        # Check for duplicate tagID to prevent overwriting existing tag data
        tag_id = message.tagCreateMessage.tagId
        if tag_id in self.all_tags:
            raise DuplicateTagIdException(tag_id)

        # Ensure there's an active chat minute
        chat_minute = self.chat_message_handler.chat_minute_handler.get_active_minute()
        if chat_minute is None:
            raise NoActiveChatMinuteException()

        # Check if tag violates the unique-together constraint (user, minute, name)
        # The db will throw an exception if a tag violates this constraint. The reason
        # we don't simply catch the db exception is because the db throws an 'IntegrityError'
        # when commit() is invoked on the sql alchemy session, which occurs outside of this class.
        if self._is_duplicate_tag(chat_minute, message):
            ret = False

        return ret

    def _is_valid_delete_tag_message(self, message):
        """
            Args:
                message: deserialized Thrift Message

            Returns:
             True if message should be persisted, False otherwise.

            Throws:
                NoActiveChatMinuteException
                TagIdDoesNotExistException
        """
        ret = False

        # Ensure there is an active chat minute
        chat_minute = self.chat_message_handler.chat_minute_handler.get_active_minute()
        if chat_minute is None:
            raise NoActiveChatMinuteException()

        # Check that we have a reference to the tagId marked to be deleted
        tag_id = message.tagDeleteMessage.tagId
        if tag_id not in self.all_tags:
            raise TagIdDoesNotExistException(tag_id)

        # Check that this tag was marked to be persisted
        is_tag_persisted = False
        for minute, tags in self.tags_to_persist.iteritems():
            if tag_id in tags.keys():
                is_tag_persisted = True
                break
        if is_tag_persisted:
            tag_model = self.all_tags[tag_id].get_model()
            # Ensure that the model hasn't already been marked for delete
            if not tag_model.deleted:
                ret = True

        return ret


class MessageModelData(object):
    """
        Data structure to maintain references to a chat message's
        associated model.
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

        Each participant in a chat will have an associated
        instance of this class.
    """
    def __init__(self, user_id, is_speaking=False, start_timestamp=None, end_timestamp=None):
        self.user_id = user_id
        self.is_actively_speaking=is_speaking
        self.start = start_timestamp
        self.end = end_timestamp

    def set_speaking(self, is_speaking):
        self.is_actively_speaking = is_speaking

    def is_speaking(self):
        return self.is_actively_speaking

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
            ret = self.end - self.start
        return ret