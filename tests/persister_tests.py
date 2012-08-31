
import unittest
import time

from testbase import DistributedTestCase, IntegrationTestCase


# TODO Add tests


class ChatPersisterTest(IntegrationTestCase):
    """
        Test the persist service's ChatPersister object which responsible for
        starting, processing, and ending a persist job.
    """

    @classmethod
    def setUpClass(cls):
        IntegrationTestCase.setUpClass()

        # Need to instantiate ChatPersister
        #persister = ChatPersister(self.db_session_factory, job_id)

    @classmethod
    def tearDownClass(cls):
        IntegrationTestCase.tearDownClass()



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


