import unittest
import logging
import time

from trpycore.zookeeper.client import ZookeeperClient
from trsvcscore.proxy.zoo import ZookeeperServiceProxy
from tridlcore.gen.ttypes import RequestContext
from trpersistsvc.gen import TPersistService

class PersisterTest(unittest.TestCase):
    """
        Test the persist service's Persister object which responsible for
        starting, processing, and ending a persist job.
    """

    @classmethod
    def setUpClass(cls):
        cls.service_name = "persistsvc"
        cls.service_class = TPersistService

        cls.zookeeper_client = ZookeeperClient(["localdev:2181"])
        cls.zookeeper_client.start()
        time.sleep(1)

        cls.service = ZookeeperServiceProxy(cls.zookeeper_client, cls.service_name, cls.service_class, keepalive=True)
        cls.request_context = RequestContext(userId=0, impersonatingUserId=0, sessionId="dummy_session_id", context="")

        logging.basicConfig(level=logging.DEBUG)

        # Need to instantiate ChatPersister
        persister = ChatPersister(self.db_session_factory, job_id)

    @classmethod
    def tearDownClass(cls):
        cls.zookeeper_client.stop()
        cls.zookeeper_client.join()

    def test_startJob(self):
        # Verify the correct job fields have been updated to claim ownership of this job
        # Create new ChatPersistJob obj, read it, write it, check values
        pass

    def test_endJob(self):
        # Verify the correct job fields have been updated to indicate this job is complete
        pass

    def test_abortJob(self):
        # Verify all data is unwound if job is aborted
        pass

if __name__ == '__main__':
    unittest.main()


