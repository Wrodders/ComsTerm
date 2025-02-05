from PyQt6.QtCore import *
from PyQt6.QtWidgets import *



from common.logger import getmylogger
from common.worker import Worker
from common.zmqutils import ZmqPub, ZmqSub,Endpoint,Transport
from common.messages import ParameterMap

class ZmqBridgeQt(QObject):
    msgSig = pyqtSignal(tuple)
    def __init__(self):
        super().__init__()
        self.log = getmylogger(__name__)
        self.subscriber = ZmqSub(Transport.TCP, Endpoint.BOT_MSG)
        self.workerIO = Worker(self._run)
        self.subscriber.connect()
    def _run(self):
        self.log.info(f"Started ZmqBridge I/O Thread")
        
        while not self.workerIO.stopEvent.is_set():
            try:
                topic, msg = self.subscriber.receive()
                if((topic or msg) != ""):
                    self.msgSig.emit((topic,msg))
                
            except Exception as e:
                self.log.error(f"Exception in ZmqBridgeQt {e}")
                break
        
        self.subscriber.close()
        self.log.info("Exiting ZmqBridge I/O Thread")

