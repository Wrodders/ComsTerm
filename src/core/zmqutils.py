from PyQt6 import QtCore
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *

import zmq, time
from enum import Enum

from common.worker import Worker


from common.logger import getmylogger



"""
ZMQ SOCKET INTERFACE FUNCTIONS

"""    
class Transport(Enum):
    INPROC = "inproc"
    IPC = "ipc"
    TCP = "tcp"
    UDP = "udp"


class Endpoint(Enum):
    COMSTERM = "comsterm"
    PISTREAM = "piStream.local"

def checkAddress(transport: Transport, endpoint: Endpoint) -> str:
    if transport == Transport.TCP:
        # Example: tcp://127.0.0.1:5555
        return f"{transport.value}://{endpoint.value}"
    elif transport == Transport.IPC:
        # Example: ipc:///tmp/zmq_socket
        return f"{transport.value}:///tmp/{endpoint.value}"
    elif transport == Transport.INPROC:
        # Example: inproc://example
        return f"{transport.value}://{endpoint.value}"
    else:
        raise ValueError(f"Unsupported transport type: {transport.value}")



"""
@Breif: ZMQ Publish socket with added functionality.
"""
class ZmqPub:
    def __init__(self,transport : Transport, endpoint : Endpoint):
        self.log = getmylogger(__name__)
        self.socketAddress = checkAddress(transport, endpoint)
        self.context = zmq.Context.instance()
        self.socket = self.context.socket(zmq.PUB)

    def bind(self):
        self.socket.bind(self.socketAddress)
        self.log.debug(f"Binded ZMQ PUB socket to {self.socketAddress}")

    def send(self, topic: str, data : str):
        self.socket.send_multipart([topic.encode(), data.encode()])
"""
@Brief: ZMQ Subscription socket with added functionality.
@Description: Creates a SUB Socket with add/remove topics, clean up and logging. 
"""
class ZmqSub:
    def __init__(self, transport : Transport, endpoint : Endpoint):
        self.log = getmylogger(__name__)
        self.socketEndpoint = checkAddress(transport, endpoint)
        self.context = zmq.Context.instance()
        self.socket = self.context.socket(zmq.SUB)
        self.topicList = []

    def connect(self):
        self.socket.connect(self.socketEndpoint)
        self.log.debug(f"Connected ZMQ SUB socket to: {self.socketEndpoint}")

    def addTopicSub(self, topic : str):
        if topic not in self.topicList:
            self.socket.setsockopt(zmq.SUBSCRIBE, topic.encode())
            self.topicList.append(topic)
            self.log.debug(f"ZMQ SUB Subscribed to {topic}")

    def removeTopic(self, topic : str):
        self.socket.setsockopt(zmq.UNSUBSCRIBE, topic)
        if topic in self.topicList:
            self.topicList.remove(topic)
            self.log.debug(f"Unsubscribed to {topic}")

    def getTopics(self): # returns list of topic names the socket is subscribed
        return self.topicList
    
    def receive(self) -> tuple[str, str]:
        try:
            dataFrame = self.socket.recv_multipart(flags=zmq.NOBLOCK)
            return (dataFrame[0].decode(),dataFrame[1].decode())
        except zmq.Again:
            # No message received, continue loop
            return ("","")
        except Exception as e:
            self.log.error(f"Excpetion in ZMQSUB Receive: {e}")
            return ("","")

    def close(self):
        self.socket.close()
        self.log.debug(f"Closed ZMQ SUB socket connected to: {self.socketEndpoint}" )


"""
@Brief: ZMQ Subscription End Point for Qt Components

"""
class ZmqBridgeQt(QObject):
    msgSig = pyqtSignal(tuple)
    def __init__(self):
        super().__init__()
        self.log = getmylogger(__name__)
        
        self.workerIO = Worker(self._run)
        
       
    def _run(self):
        self.log.info(f"Started ZmqBridge I/O Thread")
        self.subscriber = ZmqSub(Transport.IPC, Endpoint.COMSTERM)
        self.subscriber.addTopicSub("")
        
        self.subscriber.connect()
        
        while not self.workerIO.stopEvent.is_set():
            try:
                topic, msg = self.subscriber.receive()
                self.msgSig.emit((topic,msg))
                
            except Exception as e:
                self.log.error(f"Exception in ZmqBridgeQt {e}")
                break
        
        self.subscriber.close()
        self.log.info("Exiting ZmqBridge I/O Thread")
                
        