import datetime
import logging

class ChatMessageCache(object):
    """
        Cache to temporarily store chat messages for fast access.

        The SQLAlchemy sessions hit the db when querying data, even
        if the data is accessible within the session.  Consequently,
        chat message data will be cached using this class to prevent
        having to frequently reach out to the db.
    """
    def __init__(self,
                 marker_type_id,
                 minute_type_id,
                 tag_type_id):
        self.log = logging.getLogger(__name__)

        self.chat_marker_type_id = marker_type_id
        self.chat_minute_type_id = minute_type_id
        self.chat_tag_type_id = tag_type_id

        self.chat_markers = ChatMarkerCache()
        self.chat_minutes = ChatMinuteCache()
        self.chat_tags = ChatTagCache()

    def add(self, message):
        """
            Add message to the cache
        """
        if (message_type.id == self.chat_marker_type_id):
            self.chat_markers.add(message)
        elif (message_type.id == self.chat_minute_type_id):
            self.chat_minutes.add(message)
        elif (message_type.id == self.chat_tag_type_id):
            self.chat_tags.add(message)


    def get_chat_minute(self, timestamp):
        print 'need to return the active chat minute message'

    def get_chat_minutes(self):
        return self.chat_minutes.get_filtered_messages()

    def get_chat_markers(self):
        return self.chat_markers.get_filtered_messages()

    def get_chat_tags(self):
        return self.chat_tags.get_filtered_messages()

#TODO create abstract base for these caches below?

class ChatMarkerCache(object):
    """
        Cache to house Chat Marker messages

        This class is responsible for temporarily housing
        chat marker messages while the persist svc is
        working.  This class is also responsible for
        defining and applying the business rules to handle
        duplicate messages and filtering any unwanted messages.
        """

    def __init__(self):
        self.log = logging.getLogger(__name__)
        self.raw_messages = []
        self.filtered_messages = []

    def get_raw_messages(self):
        """
            Return all chat marker messages.
        """
        return self.raw_messages

    def get_filtered_messages(self):
        """
            Return chat marker messages that pass the biz rules filter.
        """
        return self.filtered_messages

    def add(self, message):
        """
            Add message to the cache
        """
        self.raw_messages.append(message)
        self._filter_message(message)

    def _filter_message(self, message):
        """
            Given a collection of chat messages associated with a chat, this method will
            filter the messages down to only those we want to persist.
        """
        # Apply Biz Rules here

        # Messages are guaranteed to be unique due to the message_id attribute that each
        # message possesses.  This means we can avoid a duplicate message check here.

        self.filtered_messages.append(message)

class ChatMinuteCache(object):
    """
        Cache to house Chat Minute messages

        This class is responsible for temporarily housing
        chat minute messages while the persist svc is
        working.  This class is also responsible for
        defining and applying the business rules to handle
        duplicate messages and filtering any unwanted messages.
    """
    def __init__(self):
        self.log = logging.getLogger(__name__)
        self.raw_messages = []
        self.filtered_messages = []

    def get_raw_messages(self):
        """
            Return all chat minute messages.
        """
        return self.raw_messages

    def get_filtered_messages(self):
        """
            Return chat minute messages that pass the biz rules filter.
        """
        return self.filtered_messages

    def add(self, message):
        """
            Add message to the cache
        """
        self.raw_messages.append(message)
        self._filter_message(message)

    def _filter_message(self, message):
        """
            Given a collection of chat messages associated with a chat, this method will
            filter the messages down to only those we want to persist.
        """

        # Apply Biz Rules here

        # Messages are guaranteed to be unique due to the message_id attribute that each
        # message possesses.  This means we can avoid a duplicate message check here.

        self.filtered_messages.append(message)

class ChatTagCache(object):
    """
        Cache to house Chat Tag messages

        This class is responsible for temporarily housing
        chat tag messages while the persist svc is
        working.  This class is also responsible for
        defining and applying the business rules to handle
        duplicate messages and filtering any unwanted messages.
    """
    def __init__(self):
        self.log = logging.getLogger(__name__)
        self.raw_messages = []
        self.filtered_messages = []

    def get_raw_messages(self):
        """
            Return all chat tag messages.
        """
        return self.raw_messages

    def get_filtered_messages(self):
        """
            Return chat tag messages that pass the biz rules filter.
        """
        return self.filtered_messages

    def add(self, message):
        """
            Add message to the cache
        """
        self.raw_messages.append(message)
        self._filter_message(message)

    def _filter_message(self, message):
        """
            Given a collection of chat messages associated with a chat, this method will
            filter the messages down to only those we want to persist.

            Removes duplicate tags that occur within the same chat minute.
            Removes tags that were added and then deleted within the same chat minute.
        """

        # Messages are guaranteed to be unique due to the message_id attribute that each
        # message possesses.  This means we can avoid a duplicate message check here.

        self.filtered_messages.append(message)