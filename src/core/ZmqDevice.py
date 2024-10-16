from core.device import BaseDevice, DeviceInfo
from common.zmqutils import ZmqSub, ZmqPub, Transport, Endpoint
from common.worker import Worker


from dataclasses import dataclass
from common.logger import getmylogger

@dataclass
class ZmqInfo(DeviceInfo):
    clientSide_transport : Transport = Transport.TCP
    clientSide_endpoint : Endpoint = Endpoint.PISERVER


class ZmqDevice(BaseDevice):
    def __init__(self, info: ZmqInfo ): 
        super().__init__()        
        self.log = getmylogger(__name__)
        self.info = info

        self.cmdMap.register(topicName="STOP", topicArgs=[], delim="")
        self.cmdMap.register(topicName="START", topicArgs=[], delim="")
        self.cmdMap.register(topicName="LINE", topicArgs=[], delim="")
        self.cmdMap.register(topicName="TURN", topicArgs=[], delim="")
        
        self.pubMap.register(topicName="CMD_RET", topicArgs=[], delim=":")
        self.pubMap.register(topicName="ERROR", topicArgs=[], delim=":")
        self.pubMap.register(topicName="INFO", topicArgs=[], delim=":")
        self.pubMap.register(topicName="DEBUG", topicArgs=[], delim=":")
        self.pubMap.register(topicName="IMU", topicArgs=["RP", "CR", "KP","RR","CP", "KR"], delim=":")
     

        self.sub  = ZmqSub(transport=self.info.clientSide_transport, endpoint=self.info.clientSide_endpoint)
        
    def _start(self) -> bool:
        self.workerIO._begin()
        return True

    def _stop(self):
        self.publisher.close()
        self.sub.close()
        self.workerIO._stop()

    def _run(self):
        '''Execute Thread'''
        self.publisher.bind()
        self.sub.connect()
        self.sub.addTopicSub("") # Allowing for Pb Sub Multiple Devices
        self.log.info(f"Started ZMQ Device")
        while (not self.workerIO.stopEvent.is_set()):
            try:
                topic, data = self.sub.socket.recv_multipart()
                topic = self.pubMap.getTopicByName(topic.decode())
                self.pubMsgSubTopics(topic=topic, data=data.decode())
            except Exception as e:
                    self.log.warning(f"Exception in ZmqDeviceRun:{e} ")
                    pass
            
        self.log.info("Exit Zmq Device I/O Thread")  
        return
    
