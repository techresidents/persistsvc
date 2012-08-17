from trsvcscore.db.managers.tree import TreeManager
from trsvcscore.db.models import Topic, Chat, ChatSession

class TopicDataManager(object):
    """
        Data structure to maintain references to a chat's topic data.
    """
    def __init__(self):
        self.manager = TreeManager(Topic)

    def get_root_topic_id(self, db_session, chat_session_id):
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
        print 'Output from tree manager:'
        topic_list = []
        for sqlalchemy_topic, level in self.manager.tree_by_rank(db_session, root_topic_id):
            print "%s (%s)" % (sqlalchemy_topic.title, level)
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
        return TopicDataCollection(self._get_list_by_rank(db_session, root_topic_id))



class TopicDataCollection(object):

    def __init__(self, topic_list_by_rank):
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
        return self.topic_list_by_rank

    def as_dict(self):
        return self.topic_dict

    def get_leaf_list_by_rank(self):
        return self.leaf_topic_list_by_rank

    def is_leaf_topic(self, topic):
        return topic in self.leaf_topic_list_by_rank

    def get_next_topic(self, topic):
        return self._get_next_item(self.topic_list_by_rank, topic)

    def get_next_leaf(self, leaf_topic):
        return self._get_next_item(self.leaf_topic_list_by_rank, leaf_topic)

    def _get_next_item(self, list, item):
        ret = None
        if item in list:
            index = list.index(item)
            next_index = index+1
            # The last item in the list will have an index of len-1
            if next_index < len(list):
                ret = list[next_index]
        return ret

    def get_previous_topic(self, topic):
        return self._get_previous_item(self.topic_list_by_rank, topic)

    def get_previous_leaf(self, leaf_topic):
        return self._get_previous_item(self.leaf_topic_list_by_rank, leaf_topic)

    def _get_previous_item(self, list, item):
        ret = None
        if item in list:
            index = list.index(item)
            prev_index = index-1
            # The first item in the list will have an index of 0
            if prev_index >= 0:
                ret = list[prev_index]
        return ret


class TopicData(object):

    def __init__(self, topic_id, parent_id, rank, level, title, description):
        self.id = topic_id
        self.parent_id = parent_id
        self.rank = rank
        self.level = level
        self.title = title
        self.description = description