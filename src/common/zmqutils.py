from PyQt6.QtCore import *
from PyQt6.QtWidgets import *

import zmq, platform
from enum import Enum

from common.logger import getmylogger
from common.worker import Worker


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
    PISERVER = "raspberrypi.local:5555"
    DBOT = "dbot.local:5555"
    LOOPBACK = "127.0.0.1:5555"

def buildAddress(transport: Transport, endpoint: Endpoint) -> str:
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
@Brief: ZMQ Publish socket with added functionality.
"""
class ZmqPub:
    def __init__(self,transport : Transport, endpoint : Endpoint):
        self.log = getmylogger(__name__)
        self.socketEndpoint = buildAddress(transport, endpoint)
        self.context = zmq.Context.instance()
        self.socket = self.context.socket(zmq.PUB)
    def bind(self):
        self.socket.bind(self.socketEndpoint)
        self.log.debug(f"Binded ZMQ PUB socket to {self.socketEndpoint}")

    def send(self, topic: str, data : str):
        if(isinstance(topic, str)):
            topic_b = topic.encode()
        else: 
            topic_b = topic
        if(isinstance(data, str)):
            data_b = data.encode()
        else: 
            data_b = data
        self.socket.send_multipart([topic_b, data_b])

    def close(self):
        self.socket.close()
        self.log.debug(f"Closed ZMQ PUB socket binded to: {self.socketEndpoint}" )

"""
@Brief: ZMQ Subscription socket with added functionality.
@Description: Creates a SUB Socket with add/remove topics, clean up and logging. 
"""
class ZmqSub:
    def __init__(self, transport : Transport, endpoint : Endpoint):
        self.log = getmylogger(__name__)
        self.socketAddress = buildAddress(transport, endpoint)
        self.context = zmq.Context.instance()
        self.socket = self.context.socket(zmq.SUB)
        self.topicList = []

    def connect(self):
        self.socket.connect(self.socketAddress)
        self.log.debug(f"Connected ZMQ SUB socket to: {self.socketAddress}")

    def addTopicSub(self, topic : str):
        if topic not in self.topicList:
            self.socket.setsockopt(zmq.SUBSCRIBE, topic.encode())
            self.topicList.append(topic)
            if(topic==""):
                topic = "*"
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
            self.log.error(f"Exception in ZMQSUB Receive: {e}")
            return ("","")

    def close(self):
        self.socket.close()
        self.log.debug(f"Closed ZMQ SUB socket connected to: {self.socketAddress}" )


"""
@Brief: ZMQ Subscription End Point for Qt Components

"""
class ZmqServer():
    def __init__(self):
        super().__init__()
        self.log = getmylogger(__name__)
        self.context = zmq.Context.instance()
        self.dealer = self.context.socket(zmq.DEALER)
     

        


class ZmqBridgeQt(QObject):
    msgSig = pyqtSignal(tuple)
    def __init__(self):
        super().__init__()
        self.log = getmylogger(__name__)
        self.subscriber = ZmqSub(Transport.INPROC, Endpoint.COMSTERM)
        self.workerIO = Worker(self._run)
        
       
    def _run(self):
        self.log.info(f"Started ZmqBridge I/O Thread")
       
        self.subscriber.connect()
        
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
                
        