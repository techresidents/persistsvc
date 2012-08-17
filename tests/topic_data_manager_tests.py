
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../persistsvc"))
sys.path.insert(0, PROJECT_ROOT)

import unittest
import logging

from topic_data_manager import TopicDataManager, TopicDataCollection, TopicData

class TopicDataManagerTest(unittest.TestCase):
    """
        Test the Topic Data Manager class
    """

    @classmethod
    def setUpClass(cls):

        #
        # Dataset #1
        #
        # Root
        #   T1
        #   T2
        #   T3
        #   T4
        #
        root = TopicData(topic_id=1, parent_id=None, rank=0, level=1, title='Root', description='')
        t1   = TopicData(topic_id=2, parent_id=1,    rank=1, level=2, title='t1',   description='')
        t2   = TopicData(topic_id=3, parent_id=1,    rank=2, level=2, title='t2',   description='')
        t3   = TopicData(topic_id=4, parent_id=1,    rank=3, level=2, title='t3',   description='')
        topic_list_by_rank = [root, t1, t2, t3]
        leaf_list_by_rank = [t1, t2, t3]
        topic_dict = {
            root.id : root,
            t1.id : t1,
            t2.id : t2,
            t3.id : t3
        }
        dataset1 = TopicTestData(
            topic_list_by_rank,
            leaf_list_by_rank,
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
        root = TopicData(topic_id=1, parent_id=None, rank=0, level=1, title='Root', description='')
        t1   = TopicData(topic_id=2, parent_id=1,    rank=1, level=2, title='t1',   description='')
        t2   = TopicData(topic_id=3, parent_id=1,    rank=2, level=2, title='t2',   description='')
        t3   = TopicData(topic_id=4, parent_id=3,    rank=3, level=3, title='t3',   description='')
        t4   = TopicData(topic_id=5, parent_id=4,    rank=4, level=4, title='t4',   description='')
        t5   = TopicData(topic_id=6, parent_id=3,    rank=5, level=3, title='t5',   description='')
        t6   = TopicData(topic_id=7, parent_id=1,    rank=6, level=2, title='t6',   description='')
        topic_list_by_rank = [root, t1, t2, t3, t4, t5, t6]
        leaf_list_by_rank = [t1, t4, t5, t6]
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
            topic_dict,
            TopicDataCollection(topic_list_by_rank)
        )


        cls.test_topic_data = [dataset1, dataset2, dataset3]

    @classmethod
    def tearDownClass(cls):
        pass

    def test_topicCollectionListByRank(self):
        for dataset in self.test_topic_data:

            # Verify topics
            self.assertEqual(
                dataset.expected_topic_list_by_rank,
                dataset.topic_collection.as_list_by_rank()
            )

            # Verify rank of items in list
            expected_rank = 0
            for topic in dataset.topic_collection.as_list_by_rank():
                self.assertEqual(expected_rank, topic.rank)
                expected_rank+=1

            # Verify parent_id of first topic is None
            root_topic = dataset.topic_collection.as_list_by_rank()[0]
            self.assertIsNone(root_topic.parent_id)


    def test_topicCollectionLeafListByRank(self):
        for dataset in self.test_topic_data:

            # Verify leaf topics
            self.assertEqual(
                dataset.expected_leaf_list_by_rank,
                dataset.topic_collection.get_leaf_list_by_rank()
            )

            # Verify rank of items in list
            prev_topic_rank = 0
            for topic in dataset.topic_collection.get_leaf_list_by_rank():
                self.assertGreater(topic.rank, prev_topic_rank)
                prev_topic_rank = topic.rank


    def test_topicDict(self):
        for dataset in self.test_topic_data:

            # Verify topics
            self.assertEqual(
                dataset.expected_topic_dict,
                dataset.topic_collection.as_dict()
            )


    def test_getNextTopic(self):
        for dataset in self.test_topic_data:

            # Verify topics - sanity check
            self.assertEqual(
                dataset.expected_topic_list_by_rank,
                dataset.topic_collection.as_list_by_rank()
            )

            topic_list = dataset.topic_collection.as_list_by_rank()

            for topic in topic_list:
                index = topic_list.index(topic)
                next_index = index+1
                if next_index < len(topic_list):
                    expected_next_topic = topic_list[next_index]
                else:
                    expected_next_topic = None
                next_topic = dataset.topic_collection.get_next_topic(topic)
                self.assertEqual(expected_next_topic, next_topic)


    def test_getPreviousTopic(self):
        for dataset in self.test_topic_data:

            # Verify topics - sanity check
            self.assertEqual(
                dataset.expected_topic_list_by_rank,
                dataset.topic_collection.as_list_by_rank()
            )

            topic_list = dataset.topic_collection.as_list_by_rank()

            for topic in topic_list:
                index = topic_list.index(topic)
                prev_index = index-1
                if prev_index >= 0:
                    expected_prev_topic = topic_list[prev_index]
                else:
                    expected_prev_topic = None
                prev_topic = dataset.topic_collection.get_previous_topic(topic)
                self.assertEqual(expected_prev_topic, prev_topic)


    def test_getNextLeaf(self):
        for dataset in self.test_topic_data:

            # Verify topics - sanity check
            self.assertEqual(
                dataset.expected_leaf_list_by_rank,
                dataset.topic_collection.get_leaf_list_by_rank()
            )

            topic_list = dataset.topic_collection.get_leaf_list_by_rank()

            for topic in topic_list:
                index = topic_list.index(topic)
                next_index = index+1
                if next_index < len(topic_list):
                    expected_next_topic = topic_list[next_index]
                else:
                    expected_next_topic = None
                next_topic = dataset.topic_collection.get_next_leaf(topic)
                self.assertEqual(expected_next_topic, next_topic)


    def test_getPreviousLeaf(self):
        for dataset in self.test_topic_data:

            # Verify topics - sanity check
            self.assertEqual(
                dataset.expected_leaf_list_by_rank,
                dataset.topic_collection.get_leaf_list_by_rank()
            )

            topic_list = dataset.topic_collection.get_leaf_list_by_rank()

            for topic in topic_list:
                index = topic_list.index(topic)
                prev_index = index-1
                if prev_index >= 0:
                    expected_prev_topic = topic_list[prev_index]
                else:
                    expected_prev_topic = None
                prev_topic = dataset.topic_collection.get_previous_leaf(topic)
                self.assertEqual(expected_prev_topic, prev_topic)




class TopicTestData(object):

    def __init__(self, topic_list, leaf_list, topic_dict, topic_collection):
        self.expected_topic_list_by_rank = topic_list
        self.expected_leaf_list_by_rank = leaf_list
        self.expected_topic_dict = topic_dict
        self.topic_collection = topic_collection




if __name__ == '__main__':
    unittest.main()


