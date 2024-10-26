from core.device import BaseDevice, DeviceInfo
from common.zmqutils import ZmqSub, ZmqPub, Transport, Endpoint
from common.worker import Worker
from common.messages import Topic


from dataclasses import dataclass
from common.logger import getmylogger


'''

|-------| PUB --> TCP MSG --> SUB |---------|  PUB --> INPROC --> SUB | Console |                   
| SerDev|                         | ZMQ Dev | 
|-------| SUB <--TCP CMD <--  PUB |---------|  SUB <-- INPROC <-- PUB | CONTROL | 


'''


@dataclass
class ZmqInfo(DeviceInfo):
    clientSub_transport : Transport = Transport.TCP
    clientSub_endpoint : Endpoint = Endpoint.PI_MSG
    clientCmd_transport : Transport = Transport.TCP
    clientCmd_endpoint : Endpoint = Endpoint.PI_CMD

class ZmqDevice(BaseDevice):
    def __init__(self, info: ZmqInfo ): 
        super().__init__(pubEndpoint=info.pubEndpoint, pubTransport=info.pubTransport, 
                        cmdEndpoint=info.cmdEndpoint, cmdTransport=info.cmdTransport)   
        self.log = getmylogger(__name__)
        self.info = info

        self.pubMap.loadTopicsFromCSV('devicePub.csv')
        self.clientSub  = ZmqSub(transport=self.info.clientSub_transport, endpoint=self.info.clientSub_endpoint) 
        self.clientPub  = ZmqPub(transport=self.info.clientCmd_transport, endpoint=self.info.clientCmd_endpoint) 
        
    def _start(self) -> bool:
        self.workerRead._begin()
        return True

    def _cleanup(self):
        self.clientSub.close()
        self.clientPub.close()
  

    def _readDevice(self):
        self.msgPublisher.bind()
        self.clientSub.connect()
        self.clientSub.addTopicSub("") # Allowing for Pb Sub Multiple Devices
        self.log.info(f"Started ZMQ Device")
        while (not self.workerRead.stopEvent.is_set()):
            try:
                topic, data = self.clientSub.receive()
                if(topic):
                    self.msgPublisher.send(topic=topic, data=data)
            except Exception as e:
                    self.log.warning(f"Exception in ZmqDeviceRun:{e} ")
                    pass
            
        self.log.info("Exit Zmq Device I/O Thread")  
        return
    
    def _writeDevice(self):
        self.log.debug("Started ZMQ Device Write Thread")
        self.clientPub.bind()
        self.cmdSubscriber.connect()
        self.cmdSubscriber.addTopicSub("") # Allowing for Pb Sub Multiple Devices
        self.log.info(f"Started ZMQ Device")
        while (not self.workerRead.stopEvent.is_set()):
            try:
                topic, data = self.cmdSubscriber.receive()
                self.clientPub.send(topic=topic, data=data)
            except Exception as e:
                    self.log.warning(f"Exception in ZmqDeviceRun:{e} ")
                    pass

        self.log.debug("Exit ZMQ Interface Write Thread")
    

    
