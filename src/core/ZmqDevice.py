from core.device import BaseDevice, DeviceInfo
from common.zmqutils import ZmqSub, Transport, Endpoint


from dataclasses import dataclass
from common.logger import getmylogger

@dataclass
class ZmqInfo(DeviceInfo):
    transport : Transport  = Transport.IPC
    endpoint : Endpoint = Endpoint.COMSTERM


class ZmqDevice(BaseDevice):
    def __init__(self, transport : Transport, endpoint : Endpoint ): 
        super().__init__()
        self.log = getmylogger(__name__)
        self.endpoint = endpoint
        self.transport  = transport
        
    def _start(self) -> bool:
        self.workerIO._begin()
        return True

    def _run(self):
        '''Execute Thread'''
        self.sub  = ZmqSub(transport=self.transport, endpoint=self.endpoint)
        self.sub.connect()
        self.sub.addTopicSub("") # Allowing for Pb Sub Multiple Devices
        self.log.info(f"Started ZMQ Device")
        while (not self.workerIO.stopEvent.is_set()):
            try:
                topic, data = self.sub.socket.recv_multipart()
                if data != "":
                    self.publisher.send(f"zmq/{topic}", data)
            except Exception as e:
                    self.log.warning(f"Exception in ZmqDeviceRun:{e} ")
                    pass
        
        self.sub.close() 
        self.log.info("Exit Zmq Device")  
        return
    
