
from trsvcscore.db.managers.tree import TreeManager
from trsvcscore.db.models import Topic, Chat, ChatSession

class TopicDataManager(object):
    """
        The TopicDataManager class is responsible for making
        it easy to access topic data.  The class is used
        to return a TopicDataCollection object using the
        root topic ID as input.
    """

    def __init__(self):
        self.manager = TreeManager(Topic)

    def get_root_topic_id(self, db_session, chat_session_id):
        """
            Return a chat topic's root topic ID.

            Args:
                db_session: a SQL Alchemy db session
                chat_session_id: a ChatSession ID
        """

        chat_id = db_session.query(ChatSession).\
            filter(ChatSession.id == chat_session_id).\
            one().\
            chat_id
        topic_id = db_session.query(Chat).\
            filter(Chat.id == chat_id).\
            one().\
            topic_id
        return topic_id

    def _get_list_by_rank(self, db_session, root_topic_id):
        """
            Internal method used to return a list of TopicData
            objects ordered by their topic rank.

            Args:
                db_session: a SQL Alchemy db session
                root_topic_id: the chat's root topic ID
        """
        topic_list = []
        for sqlalchemy_topic, level in self.manager.tree_by_rank(db_session, root_topic_id):
            #print "%s (%s)" % (sqlalchemy_topic.title, level) TODO log
            topic = TopicData(
                sqlalchemy_topic.id,
                sqlalchemy_topic.parent_id,
                sqlalchemy_topic.rank,
                level,
                sqlalchemy_topic.title,
                sqlalchemy_topic.description
            )
            topic_list.append(topic)
        return topic_list

    def get_collection(self, db_session, root_topic_id):
        """
            Returns a TopicDataCollection object

            Args:
                db_session: a SQL Alchemy db session
                root_topic_id: the chat's root topic ID
        """
        return TopicDataCollection(self._get_list_by_rank(db_session, root_topic_id))



class TopicDataCollection(object):
    """
        Data structure to maintain references to a chat's topic data.
        The purpose of this class is to encapsulate all the functionality
        that is required to work with chat topic data.

    """

    def __init__(self, topic_list_by_rank):
        """
            Initialize the TopicDataCollection.

            Args:
                A list of TopicData objects ordered
                by rank. The TopicDataManager class has
                a method to generate this list.
        """
        self.topic_list_by_rank = topic_list_by_rank
        self.topic_dict = {}
        self.leaf_topic_list_by_rank = []
        self.parent_topic_ids = []

        for topic in topic_list_by_rank:
            # Create dict of topics
            self.topic_dict[topic.id] = topic
            # Create list of parents
            if topic.parent_id is not None:
                self.parent_topic_ids.append(topic.parent_id)

        for topic in topic_list_by_rank:
            if topic.id not in self.parent_topic_ids:
                self.leaf_topic_list_by_rank.append(topic)


    def as_list_by_rank(self):
        """
            Return a list of TopicData objects
            ordered by their rank.
        """
        return self.topic_list_by_rank

    def as_dict(self):
        """
            Return the topic data as a
            dictionary.
            { topic_id : TopicData }
        """
        return self.topic_dict

    def get_leaf_list_by_rank(self):
        """
            Return all leaf topics as a
            list of TopicData objects ordered
            by rank.
        """
        return self.leaf_topic_list_by_rank

    def is_leaf_topic(self, topic):
        """
            Determine if input topic is a leaf.

            Args:
                topic: TopicData object in the TopicDataCollection

            Returns:
                True if topic is a leaf topic; False otherwise.
        """
        return topic in self.leaf_topic_list_by_rank

    def is_leaf_topic_by_id(self, topic_id):
        """
            Determine if input topic is a leaf.

            Args:
                topic_id: The ID of the TopicData object in the TopicDataCollection

            Returns:
                True if topic is a leaf topic; False otherwise.
        """
        ret = False
        topic = self.topic_dict.get(topic_id)
        if topic is not None:
            ret = self.is_leaf_topic(topic)
        return ret

    def get_next_topic_by_id(self, topic_id):
        """
            Get the next topic in the collection.

            Args:
                topic_id: The ID of the TopicData object in the TopicDataCollection

            Returns:
                The topic with a rank value one higher than the input topic.
                Returns None if the input topic is not in the topic collection, or
                if there is no next topic (it was the last topic).
        """
        ret = None
        topic = self.topic_dict.get(topic_id)
        if topic is not None:
            ret = self.get_next_topic(topic)
        return ret

    def get_next_topic(self, topic):
        """
            Get the next topic in the collection.

            Args:
                topic: TopicData object in the TopicDataCollection

            Returns:
                The topic with a rank value one higher than the input topic.
                Returns None if the input topic is not in the topic collection, or
                if there is no next topic (it was the last topic).
        """
        return self._get_next_item(self.topic_list_by_rank, topic)

    def get_next_leaf_by_id(self, leaf_topic_id):
        """
            Get the next leaf topic in the collection.

            Args:
                topic_id: The ID of a leaf TopicData object in the TopicDataCollection

            Returns:
                Returns the next leaf topic in the collection
                using topic rank (next topics have a higher rank).
                Returns None if the input topic is not a leaf in the topic collection, or
                if there is no next leaf topic (it was the last leaf topic).
        """
        ret = None
        topic = self.topic_dict.get(leaf_topic_id)
        if topic is not None:
            ret = self.get_next_leaf(topic)

    def get_next_leaf(self, leaf_topic):
        """
            Get the next leaf topic in the collection.

            Args:
                topic: A leaf TopicData object in the TopicDataCollection

            Returns:
                Returns the next leaf topic in the collection
                using topic rank (next topics have a higher rank).
                Returns None if the input topic is not a leaf in the topic collection, or
                if there is no next leaf topic (it was the last leaf topic).
        """
        return self._get_next_item(self.leaf_topic_list_by_rank, leaf_topic)

    def _get_next_item(self, list, item):
        """
            Get the next item the list.

            Args:
                list: List of TopicData objects
                item: The topic in the list to reference as
                      the starting point.

            Returns:
                Returns the next topic in the list
                using topic rank (next topics have a higher rank).
                Returns None if the input topic is in the topic collection, or
                if there is no next topic (it was the last topic).
        """
        ret = None
        if item in list:
            index = list.index(item)
            next_index = index+1
            # The last item in the list will have an index of len-1
            if next_index < len(list):
                ret = list[next_index]
        return ret

    def get_previous_topic_by_id(self, topic_id):
        """
            Get the previous topic in the collection.

            Args:
                topic_id: The ID of the TopicData object in the TopicDataCollection

            Returns:
                The topic with a rank value one lower than the input topic.
                Returns None if the input topic is not in the topic collection, or
                if there is no previous topic (it was the first topic).
        """
        ret = None
        topic = self.topic_dict.get(topic_id)
        if topic is not None:
            ret = self.get_previous_topic(topic)
        return ret

    def get_previous_topic(self, topic):
        """
            Get the previous topic in the collection.

            Args:
                topic: TopicData object in the TopicDataCollection

            Returns:
                The topic with a rank value one lower than the input topic.
                Returns None if the input topic is not in the topic collection, or
                if there is no previous topic (it was the first topic).
        """
        return self._get_previous_item(self.topic_list_by_rank, topic)

    def get_previous_leaf_by_id(self, leaf_topic_id):
        """
            Get the previous leaf topic in the collection.

            Args:
                topic_id: The ID of a leaf TopicData object in the TopicDataCollection

            Returns:
                Returns the previous leaf topic in the collection
                using topic rank (previous topics have a lower rank).
                Returns None if the input topic is not a leaf in the topic collection, or
                if there is no previous leaf topic (it was the first leaf topic).
        """
        ret = None
        topic = self.topic_dict.get(leaf_topic_id)
        if topic is not None:
            ret = self.get_previous_leaf(topic)
        return ret

    def get_previous_leaf(self, leaf_topic):
        """
            Get the previous leaf topic in the collection.

            Args:
                topic: A leaf TopicData object in the TopicDataCollection

            Returns:
                Returns the previous leaf topic in the collection
                using topic rank (previous topics have a lower rank).
                Returns None if the input topic is not a leaf in the topic collection, or
                if there is no previous leaf topic (it was the first leaf topic).
        """
        return self._get_previous_item(self.leaf_topic_list_by_rank, leaf_topic)

    def _get_previous_item(self, list, item):
        """
            Get the previous item the list.

            Args:
                list: List of TopicData objects
                item: The topic in the list to reference as
                      the starting point.

            Returns:
                Returns the previous topic in the list
                using topic rank (previous topics have a lower rank).
                Returns None if the input topic is in the topic collection, or
                if there is no previous topic (it was the first topic).
        """
        ret = None
        if item in list:
            index = list.index(item)
            prev_index = index-1
            # The first item in the list will have an index of 0
            if prev_index >= 0:
                ret = list[prev_index]
        return ret


class TopicData(object):
    """
        Data structure to keep chat Topic data.
    """

    def __init__(self, topic_id, parent_id, rank, level, title, description):
        self.id = topic_id
        self.parent_id = parent_id
        self.rank = rank
        self.level = level
        self.title = title
        self.description = description