#!/usr/bin/env python

import logging
import logging.config
import signal
import sys

import settings

from trpycore.process.pid import pidfile, PidFileException
from trsvcscore.service.base import Service
from trpersistsvc.gen import TPersistService

from handler import PersistServiceHandler

class PersistService(Service):
    def __init__(self):

        handler = PersistServiceHandler()

        super(PersistService, self).__init__(
                name=settings.SERVICE,
                interface=settings.SERVER_INTERFACE,
                port=settings.SERVER_PORT,
                handler=handler,
                processor=TPersistService.Processor(handler),
                threads=1)
 
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
                if not service.is_alive():
                    break
    
    except PidFileException as error:
        logging.error("Service is already running: %s" % str(error))

    except KeyboardInterrupt:
        service.stop()
        service.join()

if __name__ == '__main__':
    sys.exit(main(sys.argv))
