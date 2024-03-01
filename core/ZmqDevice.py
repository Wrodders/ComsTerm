
import zmq
from enum import Enum

from logger import getmylogger
from core.device import BaseDevice


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
    




"""
ZMQ SOCKET INTERFACE FUNCTIONS

"""    
class Transport(Enum):
    INPROC = "inproc"
    IPC = "ipc"
    TCP = "tcp"
    UDP = "udp"

def checkAddress(transport: Transport, endpoint: str) -> str:
    if transport == Transport.TCP:
        # Example: tcp://127.0.0.1:5555
        return f"{transport.value}://{endpoint}"
    elif transport == Transport.IPC:
        # Example: ipc:///tmp/zmq_socket
        return f"{transport.value}:///tmp/{endpoint}"
    elif transport == Transport.INPROC:
        # Example: inproc://example
        return f"{transport.value}://{endpoint}"
    else:
        raise ValueError(f"Unsupported transport type: {transport.value}")



"""
@Breif: ZMQ Publish socket with added functionality.
"""
class ZmqPub:
    def __init__(self,transport : Transport, endpoint : str):
        self.socketAddress = checkAddress(transport, endpoint)
        self.context = zmq.Context.instance()
        self.socket = self.context.socket(zmq.PUB)

    def bind(self):
        self.socket.bind(self.socketAddress)
        log.debug(f"Binded ZMQ PUB socket to {self.socketAddress}")

    def send(self, topic: str, data : str):
        self.socket.send_multipart([topic.encode(), data.encode()])
"""
@Brief: ZMQ Subscription socket with added functionality.
@Description: Creates a SUB Socket with add/remove topics, clean up and logging. 
"""
class ZmqSub:
    def __init__(self, transport : Transport, address : str):
        self.socketAddress = checkAddress(transport, address)
        self.context = zmq.Context.instance()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.setsockopt(zmq.LINGER, 0)
        
        self.topicList = []

    def connect(self):
        self.socket.connect(self.socketAddress)
        log.debug(f"Connected ZMQ SUB socket to: {self.socketAddress}")

    def addTopicSub(self, topic : str):
        if topic not in self.topicList:
            self.socket.setsockopt(zmq.SUBSCRIBE, topic.encode())
            self.topicList.append(topic)
            log.debug(f"ZMQ SUB Subscribed to {topic}")

    def removeTopic(self, topic : str):
        self.socket.setsockopt(zmq.UNSUBSCRIBE, topic)
        if topic in self.topicList:
            self.topicList.remove(topic)
            log.debug(f"Unsubscribed to {topic}")

    def getTopics(self): # returns list of topic names the socket is subscribed
        return self.topicList
    
    def receive(self) -> tuple[str, str]:
        dataFrame = self.socket.recv_multipart()
        return (dataFrame[0].decode(),dataFrame[1].decode())

    def close(self):
        self.socket.close()
        log.debug(f"Closed ZMQ SUB socket connected to: {self.socketAddress}" )
