from core.device import BaseDevice
from core.zmqutils import ZmqPub, ZmqSub, Transport, Endpoint

from common.logger import getmylogger


"""
@Brief: ZMQ Network Device Endpoint
@Description: Publishes Messages From Cmd Queue to Device
                Receives Messages from Proxy
"""
class ZmqDevice(BaseDevice):
    def __init__(self, socketAddress : str ): 
        super().__init__()
        self.log = getmylogger(__name__)
        self.socketAddr = socketAddress
        
    def _start(self):
        self.workerIO._begin()

    def _run(self):
        '''Execute Thread'''
        #self.pub  = ZmqPub(transport=Transport.TCP, endpoint=Endpoint.COMSTERM)
        self.sub  = ZmqSub(transport=Transport.IPC, endpoint=Endpoint.COMSTERM)
        self.sub.connect()
        self.sub.addTopicSub("")
        self.log.info(f"Started ZMQ Interface")
        while (not self.workerIO.stopEvent.is_set()):
            try:
                topic, msg = self.sub.socket.recv_multipart()


            except Exception as e:
                self.log.error(f"Exception in ZmqQTSignal:{e} ")
                break
        
        self.sub.close() 
        self.log.info("exit Zmq Bridge QT I/O Thread")  
        return