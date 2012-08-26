import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../persistsvc"))
sys.path.insert(0, PROJECT_ROOT)

from topic_data_manager import TopicDataCollection, TopicData


class TopicTestDataSets(object):

    def __init__(self):

        #
        # Dataset #1
        #
        # Root
        #   T1
        #   T2
        #   T3
        #
        root = TopicData(topic_id=0, parent_id=None, rank=0, level=1, title='Root', description='')
        t1   = TopicData(topic_id=1, parent_id=0,    rank=1, level=2, title='t1',   description='')
        t2   = TopicData(topic_id=2, parent_id=0,    rank=2, level=2, title='t2',   description='')
        t3   = TopicData(topic_id=3, parent_id=0,    rank=3, level=2, title='t3',   description='')
        topic_list_by_rank = [root, t1, t2, t3]
        leaf_list_by_rank = [t1, t2, t3]
        highest_leaf_list_by_rank = [t3]
        chat_minute_end_topic_chain = {
            t3.id : [root]
        }
        topic_dict = {
            root.id : root,
            t1.id : t1,
            t2.id : t2,
            t3.id : t3
        }
        dataset1 = TopicTestData(
            topic_list_by_rank,
            leaf_list_by_rank,
            highest_leaf_list_by_rank,
            chat_minute_end_topic_chain,
            topic_dict,
            TopicDataCollection(topic_list_by_rank)
        )


        #
        # Dataset #2
        #
        # Root
        #   T1
        #   T2
        #     T3
        #       T4
        #     T5
        #   T6
        #
        root = TopicData(topic_id=0, parent_id=None, rank=0, level=1, title='Root', description='')
        t1   = TopicData(topic_id=1, parent_id=0,    rank=1, level=2, title='t1',   description='')
        t2   = TopicData(topic_id=2, parent_id=0,    rank=2, level=2, title='t2',   description='')
        t3   = TopicData(topic_id=3, parent_id=2,    rank=3, level=3, title='t3',   description='')
        t4   = TopicData(topic_id=4, parent_id=3,    rank=4, level=4, title='t4',   description='')
        t5   = TopicData(topic_id=5, parent_id=2,    rank=5, level=3, title='t5',   description='')
        t6   = TopicData(topic_id=6, parent_id=0,    rank=6, level=2, title='t6',   description='')
        topic_list_by_rank = [root, t1, t2, t3, t4, t5, t6]
        leaf_list_by_rank = [t1, t4, t5, t6]
        highest_leaf_list_by_rank = [t4, t5, t6]
        chat_minute_end_topic_chain = {
            t4.id : [t3],
            t5.id : [t2],
            t6.id : [root]
        }
        topic_dict = {
            root.id : root,
            t1.id : t1,
            t2.id : t2,
            t3.id : t3,
            t4.id : t4,
            t5.id : t5,
            t6.id : t6
        }
        dataset2 = TopicTestData(
            topic_list_by_rank,
            leaf_list_by_rank,
            highest_leaf_list_by_rank,
            chat_minute_end_topic_chain,
            topic_dict,
            TopicDataCollection(topic_list_by_rank)
        )



        #
        # Dataset #3
        #
        # Root
        #   T1
        #   T2
        #     T3
        #       T4
        #     T5
        #     T6
        #       T7
        #         T8
        #   T9
        #     T10
        #
        root = TopicData(topic_id=0, parent_id=None, rank=0, level=1, title='Root', description='')
        t1   = TopicData(topic_id=1, parent_id=0,    rank=1, level=2, title='t1',   description='')
        t2   = TopicData(topic_id=2, parent_id=0,    rank=2, level=2, title='t2',   description='')
        t3   = TopicData(topic_id=3, parent_id=2,    rank=3, level=3, title='t3',   description='')
        t4   = TopicData(topic_id=4, parent_id=3,    rank=4, level=4, title='t4',   description='')
        t5   = TopicData(topic_id=5, parent_id=3,    rank=5, level=3, title='t5',   description='')
        t6   = TopicData(topic_id=6, parent_id=2,    rank=6, level=3, title='t6',   description='')
        t7   = TopicData(topic_id=7, parent_id=6,    rank=7, level=4, title='t7',   description='')
        t8   = TopicData(topic_id=8, parent_id=7,    rank=8, level=5, title='t8',   description='')
        t9   = TopicData(topic_id=9, parent_id=0,    rank=9, level=2, title='t9',   description='')
        t10  = TopicData(topic_id=10, parent_id=9,  rank=10, level=3, title='t10',  description='')
        topic_list_by_rank = [root, t1, t2, t3, t4, t5, t6, t7, t8, t9, t10]
        leaf_list_by_rank = [t1, t4, t5, t8, t10]
        highest_leaf_list_by_rank = [t4, t8, t10]
        chat_minute_end_topic_chain = {
            t4.id : [t3],
            t8.id : [t7, t6, t2],
            t10.id : [t9, root]
        }
        topic_dict = {
            root.id : root,
            t1.id : t1,
            t2.id : t2,
            t3.id : t3,
            t4.id : t4,
            t5.id : t5,
            t6.id : t6,
            t7.id : t7,
            t8.id : t8,
            t9.id : t9,
            t10.id: t10
        }
        dataset3 = TopicTestData(
            topic_list_by_rank,
            leaf_list_by_rank,
            highest_leaf_list_by_rank,
            chat_minute_end_topic_chain,
            topic_dict,
            TopicDataCollection(topic_list_by_rank)
        )


        #
        # Dataset #4
        #
        # Root
        #   T1
        #     T2
        #   T3
        #     T4
        #     T5
        #       T6
        #     T7
        #   T8
        #   T9
        #     T10
        #
        root = TopicData(topic_id=0, parent_id=None, rank=0, level=1, title='Root', description='')
        t1   = TopicData(topic_id=1, parent_id=0,    rank=1, level=2, title='t1',   description='')
        t2   = TopicData(topic_id=2, parent_id=1,    rank=2, level=3, title='t2',   description='')
        t3   = TopicData(topic_id=3, parent_id=0,    rank=3, level=2, title='t3',   description='')
        t4   = TopicData(topic_id=4, parent_id=3,    rank=4, level=3, title='t4',   description='')
        t5   = TopicData(topic_id=5, parent_id=3,    rank=5, level=3, title='t5',   description='')
        t6   = TopicData(topic_id=6, parent_id=5,    rank=6, level=4, title='t6',   description='')
        t7   = TopicData(topic_id=7, parent_id=3,    rank=7, level=3, title='t7',   description='')
        t8   = TopicData(topic_id=8, parent_id=0,    rank=8, level=2, title='t8',   description='')
        t9   = TopicData(topic_id=9, parent_id=0,    rank=9, level=2, title='t9',   description='')
        t10  = TopicData(topic_id=10, parent_id=9,  rank=10, level=3, title='t10',  description='')
        topic_list_by_rank = [root, t1, t2, t3, t4, t5, t6, t7, t8, t9, t10]
        leaf_list_by_rank = [t2, t4, t6, t7, t8, t10]
        highest_leaf_list_by_rank = [t2, t6, t7, t10]
        chat_minute_end_topic_chain = {
            t2.id : [t1],
            t6.id : [t5],
            t7.id : [t3],
            t10.id : [t9, root]
        }
        topic_dict = {
            root.id : root,
            t1.id : t1,
            t2.id : t2,
            t3.id : t3,
            t4.id : t4,
            t5.id : t5,
            t6.id : t6,
            t7.id : t7,
            t8.id : t8,
            t9.id : t9,
            t10.id: t10
        }
        dataset4 = TopicTestData(
            topic_list_by_rank,
            leaf_list_by_rank,
            highest_leaf_list_by_rank,
            chat_minute_end_topic_chain,
            topic_dict,
            TopicDataCollection(topic_list_by_rank)
        )

        #
        # Dataset #5
        #
        # Root
        #   T1
        #
        root = TopicData(topic_id=1, parent_id=None, rank=0, level=1, title='Root', description='')
        t1   = TopicData(topic_id=2, parent_id=1,    rank=1, level=2, title='t1',   description='')
        topic_list_by_rank = [root, t1]
        leaf_list_by_rank = [t1]
        highest_leaf_list_by_rank = [t1]
        chat_minute_end_topic_chain = {
            t1.id : [root]
        }
        topic_dict = {
            root.id : root,
            t1.id : t1
        }
        dataset5 = TopicTestData(
            topic_list_by_rank,
            leaf_list_by_rank,
            highest_leaf_list_by_rank,
            chat_minute_end_topic_chain,
            topic_dict,
            TopicDataCollection(topic_list_by_rank)
        )

        self.test_topic_data_sets = [dataset1, dataset2, dataset3, dataset4, dataset5]

    def get_list(self):
        return self.test_topic_data_sets



class TopicTestData(object):

    def __init__(self, topic_list, leaf_list, highest_leaf_list, chat_minute_end_topic_chain, topic_dict, topic_collection):
        self.expected_topic_list_by_rank = topic_list
        self.expected_leaf_list_by_rank = leaf_list
        self.expected_topic_dict = topic_dict
        self.topic_collection = topic_collection
        # The following attributes are only needed by the Chat Minute Handler
        self.expected_highest_leaf_list_by_rank = highest_leaf_list
        self.expected_chat_minute_end_topic_chain = chat_minute_end_topic_chain