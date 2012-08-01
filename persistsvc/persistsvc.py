#!/usr/bin/env python

import logging
import logging.config
import os
import signal
import socket
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
sys.path.insert(0, PROJECT_ROOT)

import settings
import version

from tridlcore.gen.ttypes import Status
from trpycore.process.pid import pidfile, PidFileException
from trsvcscore.service.default import DefaultService
from trsvcscore.service.server.default import ThriftServer
from trpersistsvc.gen import TPersistService


from handler import PersistServiceHandler

class PersistService(DefaultService):
    def __init__(self):

        handler = PersistServiceHandler(self)

        server = ThriftServer(
            name="%s-thrift" % settings.SERVICE,
            interface=settings.THRIFT_SERVER_INTERFACE,
            port=settings.THRIFT_SERVER_PORT,
            handler=handler,
            processor=TPersistService.Processor(handler),
            threads=1)

        super(PersistService, self).__init__(
            name=settings.SERVICE,
            version=version.VERSION,
            build=version.BUILD,
            servers=[server],
            hostname=socket.gethostname(),
            fqdn=socket.getfqdn())
 
def main(argv):
    try:
        #Configure logger
        logging.config.dictConfig(settings.LOGGING)

        with pidfile(settings.SERVICE_PID_FILE, create_directory=True):

            
            #Create service
            service = PersistService()
            
            #Register signal handlers
            def sigterm_handler(signum, stack_frame):
                service.stop()

            signal.signal(signal.SIGTERM, sigterm_handler);
            
            #Start service
            service.start()
            
            #Join service
            while True:
                #join needs to be invoked with a timeout
                #otherwise we will not receive SIGTERM
                #interrupt or the KeyboardInterrupt.
                service.join(settings.SERVICE_JOIN_TIMEOUT)
                status = service.status()
                if status == Status.STOPPED or \
                   status == Status.DEAD:
                    break
    
    except PidFileException as error:
        logging.error("Service is already running: %s" % str(error))

    except KeyboardInterrupt:
        service.stop()
        service.join()

if __name__ == '__main__':
    sys.exit(main(sys.argv))
