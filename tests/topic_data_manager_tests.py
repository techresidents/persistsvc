
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../persistsvc"))
sys.path.insert(0, PROJECT_ROOT)

import unittest
import logging

from topic_data_manager import TopicDataManager, TopicDataCollection, TopicData
from topic_test_data import TopicTestDataSets, TopicTestData

class TopicDataCollectionTest(unittest.TestCase):
    """
        Test the Topic Data Collection class
    """

    @classmethod
    def setUpClass(cls):

        data = TopicTestDataSets()
        cls.test_topic_data = data.get_list()

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



if __name__ == '__main__':
    unittest.main()


