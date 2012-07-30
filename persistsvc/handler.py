import logging
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
sys.path.insert(0, PROJECT_ROOT)

from trpycore.thread.util import join
from trsvcscore.service.handler import ServiceHandler
from trschedulesvc.gen import TScheduleService

import version
import settings
from scheduler import ChatScheduler

class ScheduleServiceHandler(TScheduleService.Iface, ServiceHandler):
    def __init__(self):
        super(ScheduleServiceHandler, self).__init__(
                name=settings.SERVICE,
                interface=settings.SERVER_INTERFACE,
                port=settings.SERVER_PORT,
                version=version.VERSION,
                build=version.BUILD,
                zookeeper_hosts=settings.ZOOKEEPER_HOSTS,
                database_connection=settings.DATABASE_CONNECTION)

        self.log = logging.getLogger("%s.%s" % (__name__, ScheduleServiceHandler.__name__))

        #create scheduler which does the real work
        self.scheduler = ChatScheduler(
                settings.SCHEDULER_THREADS,
                self.get_database_session,
                settings.SCHEDULER_POLL_SECONDS)
    
    def start(self):
        """Start handler."""
        super(ScheduleServiceHandler, self).start()
        self.scheduler.start()

    
    def stop(self):
        """Stop handler."""
        self.scheduler.stop()
        super(ScheduleServiceHandler, self).stop()

    def join(self, timeout=None):
        """Join handler."""
        join([self.scheduler, super(ScheduleServiceHandler, self)], timeout)

    def reinitialize(self, requestContext):
        """Reinitialize - nothing to do."""
        pass
