import logging
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
sys.path.insert(0, PROJECT_ROOT)

from trpycore.thread.util import join
from trsvcscore.service.handler import ServiceHandler
from trpersistsvc.gen import TPersistService

import version
import settings
from persister import ChatPersister

class PersistServiceHandler(TPersistService.Iface, ServiceHandler):
    def __init__(self):
        super(PersistServiceHandler, self).__init__(
                name=settings.SERVICE,
                interface=settings.SERVER_INTERFACE,
                port=settings.SERVER_PORT,
                version=version.VERSION,
                build=version.BUILD,
                zookeeper_hosts=settings.ZOOKEEPER_HOSTS,
                database_connection=settings.DATABASE_CONNECTION)

        self.log = logging.getLogger("%s.%s" % (__name__, PersistServiceHandler.__name__))

        #create persister which does the real work
        self.persister = ChatPersister(
                settings.PERSISTER_THREADS,
                self.get_database_session,
                settings.PERSISTER_POLL_SECONDS)
    
    def start(self):
        """Start handler."""
        super(PersistServiceHandler, self).start()
        self.persister.start()

    
    def stop(self):
        """Stop handler."""
        self.persister.stop()
        super(PersistServiceHandler, self).stop()

    def join(self, timeout=None):
        """Join handler."""
        join([self.persister, super(PersistServiceHandler, self)], timeout)

    def reinitialize(self, requestContext):
        """Reinitialize - nothing to do."""
        #TODO - anything to do here?
        pass
