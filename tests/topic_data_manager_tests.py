
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
        dataset1 = TopicTestData(
            topic_list_by_rank,
            leaf_list_by_rank,
            TopicDataCollection(topic_list_by_rank)
            )




        cls.test_topic_data = [dataset1]

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

    def __init__(self, topic_list, leaf_list, topic_collection):
        self.expected_topic_list_by_rank = topic_list
        self.expected_leaf_list_by_rank = leaf_list
        self.topic_collection = topic_collection




if __name__ == '__main__':
    unittest.main()


