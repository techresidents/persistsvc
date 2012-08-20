
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../persistsvc"))
sys.path.insert(0, PROJECT_ROOT)

import unittest
import logging

from message_handler import ChatMinuteHandler
from topic_data_manager import TopicDataManager, TopicDataCollection, TopicData
from topic_test_data import TopicTestDataSets, TopicTestData


class ChatMinuteHandlerTest(unittest.TestCase):
    """
        Test the Chat Minute Handler class
    """

    @classmethod
    def setUpClass(cls):

        data = TopicTestDataSets()
        cls.test_topic_datasets = data.get_list()
        cls.test_session_id = 'dummy_session_id'

    @classmethod
    def tearDownClass(cls):
        pass

    def test_getHighestLeafs(self):

        for dataset in self.test_topic_datasets:

            handler = ChatMinuteHandler(self.test_session_id, dataset.topic_collection)
            highest_leafs = handler._get_highest_ranked_leafs(dataset.topic_collection)
            expected_highest_leafs = dataset.expected_highest_leaf_list_by_rank

            # Verify topics
            self.assertEqual(
                expected_highest_leafs,
                highest_leafs
            )

    def test_getChatMinuteEndTopicChain(self):

        dataset_count = 0
        for dataset in self.test_topic_datasets:
            dataset_count += 1
            print 'Processing dataset# %s' % dataset_count
            handler = ChatMinuteHandler(self.test_session_id, dataset.topic_collection)
            chat_minute_end_topic_chain = handler._get_chat_minute_end_topic_chain(dataset.topic_collection)
            expected_topic_chain = dataset.expected_chat_minute_end_topic_chain

            print 'Topic Chain Output:'
            for key, value in chat_minute_end_topic_chain.items():
                for topic in value:
                    print 'key %s: %s' % (key, topic.id)

            # Verify topics
            self.assertEqual(
                expected_topic_chain,
                chat_minute_end_topic_chain
            )


if __name__ == '__main__':
    unittest.main()