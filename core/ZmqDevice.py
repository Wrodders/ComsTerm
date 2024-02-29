
import zmq

from logger import getmylogger
from core.device import BaseDevice, ZmqPub, ZmqSub


log = getmylogger(__name__)

"""
@Breif: WIP
"""
class ZmqDevice(BaseDevice):
    def __init__(self, socketAddress : str ): 
        super().__init__()
        self.socketAddr = socketAddress
        
    def start(self):
        self.wThread.start()

    def _run(self):
        '''Execute Thread'''
        self._stopped = False
        self.sub  = ZmqSub(transport="ipc", address=self.socketAddr)
        self.sub.connect()
        self.sub.addTopicSub("") # recevies only data sent on the GUI topic
        log.info(f"Started ZMQ Interface")
        while not self._stopped:
            try:
                msg = self.sub.socket.recv_multipart()
                #self.socketDataSig.emit((topic, msg))
            except Exception as e:
                log.error(f"Exception in ZmqQTSignal:{e} ")
                break
        
        self.sub.close() 
        log.info("exit Zmq Bridge QT I/O Thread")  
        return
    



