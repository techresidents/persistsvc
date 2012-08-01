import logging

from trpycore.thread.util import join
from trsvcscore.service.handler.service import ServiceHandler
from trpersistsvc.gen import TPersistService

import settings
from persister import ChatPersister

class PersistServiceHandler(TPersistService.Iface, ServiceHandler):
    def __init__(self, service):
        super(PersistServiceHandler, self).__init__(
		service,
                zookeeper_hosts=settings.ZOOKEEPER_HOSTS,
                database_connection=settings.DATABASE_CONNECTION)

        self.log = logging.getLogger("%s.%s" % (__name__, PersistServiceHandler.__name__))

        #create persister which does the real work
        self.chat_persister = ChatPersister(
                settings.PERSISTER_THREADS,
                self.get_database_session,
                settings.PERSISTER_POLL_SECONDS)
    
    def start(self):
        """Start handler."""
        super(PersistServiceHandler, self).start()
        self.chat_persister.start()

    
    def stop(self):
        """Stop handler."""
        self.chat_persister.stop()
        super(PersistServiceHandler, self).stop()

    def join(self, timeout=None):
        """Join handler."""
        join([self.chat_persister, super(PersistServiceHandler, self)], timeout)

    def reinitialize(self, requestContext):
        """Reinitialize - nothing to do."""
        #TODO - anything to do here?
        pass
