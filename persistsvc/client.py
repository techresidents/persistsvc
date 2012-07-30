import sys
import time

from trpycore.zookeeper.client import ZookeeperClient
from trsvcscore.proxy.zookeeper import ZookeeperServiceProxy
from tridlcore.gen.ttypes import RequestContext
from trschedulesvc.gen import TScheduleService

def main(argv):
    try:
        zookeeper_client = ZookeeperClient(["localdev:2181"])
        zookeeper_client.start()
        time.sleep(1)
        schedulesvc = ZookeeperServiceProxy(zookeeper_client, "schedulesvc", TScheduleService, keepalive=True)

        context = RequestContext(userId=0, impersonatingUserId=0, sessionId="sessionid", context="")
        while True:
            print schedulesvc.getVersion(context)
            time.sleep(1)
    
    except Exception as error:
        print str(error)
    finally:
        zookeeper_client.stop()            
        zookeeper_client.join()
     
if __name__ == '__main__':
    sys.exit(main(sys.argv))
