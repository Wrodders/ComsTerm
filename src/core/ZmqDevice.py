from core.device import BaseDevice, DeviceInfo
from common.zmqutils import ZmqSub, ZmqPub, Transport, Endpoint
from common.worker import Worker
from common.messages import Topic


from dataclasses import dataclass
from common.logger import getmylogger


'''


Device1  | PUB | udp://DeviceIP:Port | Proxy SUB |  
Device2  | PUB | udp://DeviceIP:Port | Proxy SUB ||Proxy PUB | ipc://comsTerm_msg
            

Device1  | SUB |    udp://PCIp:port | Proxy PUB || Proxy SUB | icp://comsTerm_cmd
Device2  | SUB |    udp://PCIp:port | Proxy PUB |             


'''


@dataclass
class ZmqInfo(DeviceInfo):
    clientSub_transport : Transport = Transport.TCP
    clientSub_endpoint : Endpoint = Endpoint.PI_MSG
    clientCmd_transport : Transport = Transport.IPC
    clientCmd_endpoint : Endpoint = Endpoint.COMSTERM_CMD

class ZmqProxy(BaseDevice):
    def __init__(self, info: ZmqInfo ): 
        super().__init__(pubEndpoint=info.pubEndpoint, pubTransport=info.pubTransport, 
                        cmdEndpoint=info.cmdEndpoint, cmdTransport=info.cmdTransport)   
        self.log = getmylogger(__name__)
        self.info = info

        self.pubMap.loadTopicsFromCSV('devicePub.csv')

        self.proxySub = ZmqSub(info.clientSub_transport, info.clientSub_endpoint)
        self.proxyPub = ZmqPub(info.clientCmd_transport, info.clientCmd_endpoint)
        self.workerIO = Worker(self._run)

    def _start(self) -> bool:
        self.proxySub.connect()
        self.proxyPub.bind()
        self.workerIO._begin()
        return True

    def _stop(self):
        self.proxySub.close()
        self.proxyPub.close()

    def _run(self):
        self.log.info(f"Started ZmqProxy I/O Thread")
        while not self.workerIO.stopEvent.is_set():
            try:
                topic, msg = self.proxySub.receive()
                if((topic or msg) != ""):
                    self.pubCmdSckt.publish(topic, msg)
            except Exception as e:
                self.log.error(f"Exception in ZmqProxy {e}")
                break
        self.log.info("Exiting ZmqProxy I/O Thread")


    

    
  