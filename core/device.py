from PyQt6 import QtCore
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *

import sys, random, threading, time, lorem, zmq, re
import serial,serial.tools.list_ports
from queue import Queue, Empty
from dataclasses import dataclass, astuple, asdict, field
from typing import Dict, List, Tuple

from typing import Dict, Tuple, List


from logger import getmylogger


log = getmylogger(__name__)


"""
@Brief: Base Class for a Device. Handles communications between device and ComsTerm.
@Description:   Implements a set of CMDs and PUBs topics. Parses and Validates Commands against a devices protocols. 
                Controls the Child Devices _run() method to obtain data from I/O.
"""
class BaseDevice(QObject):
    deviceDataSig = QtCore.pyqtSignal(tuple)

    def __init__(self):
        super().__init__()
        self._stopped = True
        self._mutex = QMutex()
        self.wThread = threading.Thread(target=self._run) # worker IO thread
        self.cmdQueue = Queue() 

        # Create Base Topic Maps
        self.cmdMap = TopicMap()
        self.pubMap = TopicMap()

        self.cmdMap.registerTopic(topicID = '0', topicName="ID", topicFmt="", delim="")
        self.cmdMap.registerTopic(topicID = '1', topicName="RESET", topicFmt="d:d", delim=":")

        self.pubMap.registerTopic(topicID = '0', topicName="CMD_RET", topicFmt="s", delim="")
        self.pubMap.registerTopic(topicID = '1', topicName="ERR", topicFmt="s", delim="")
        self.pubMap.registerTopic(topicID = '2', topicName="INFO", topicFmt="s", delim="")

    def parseCmd(self, text: str) -> str:
        cmdParts = text.split(" ", 1) # cmdName arguments
        cmdName = cmdParts[0] 
        cmdTopic = self.cmdMap.topics.get(cmdName)
        if cmdTopic == None: # exit early if cmd name wrong 
            log.warning(f"Cmd Name; {cmdName} not found")
            return ""

        fmt = cmdTopic.fmt # grab the topics protocol format string
        cmdArgs = cmdParts[1:] #extract arguments
        if cmdArgs == []:
            numArgs = 0
        else:
            numArgs = sum(1 for c in cmdArgs[0] if c == cmdTopic.delim) + 1 # num args = num delim + 1 
        print(cmdArgs, numArgs, cmdTopic.nArgs)
        if numArgs != cmdTopic.nArgs:
            log.warning(f"Cmd syntax error: incorrect num args for {cmdName} {fmt}")
            return ""

        data = cmdTopic.delim.join(cmdArgs)  # Join arguments using delimiter
        cmdID = cmdTopic.ID
        # assemble packet 
        msgPacket = f'<{len(data)}{cmdID}{data}\n'
    
        return msgPacket
        
    def sendCmd(self, text:str):
        #Pushes cmd to IO Queue
        packet = self.parseCmd(text)
        if packet != "":
            self.cmdQueue.put(packet)
    
    def _run(self):
        raise NotImplementedError("Subclasses must implement _run method")
    
    def start(self):
        raise NotImplementedError("Subclasses must implement start method")
    
    def stop(self):
        self._mutex.lock()
        self._stopped = True
        self._mutex.unlock()




"""
ZMQ SOCKET INTERFACE FUNCTIONS

"""    

TRANSPORT_TYPES = ["inproc", "ipc", "tcp", "udp"]

def checkAddress(transport : str, endpoint : str) -> str:
    if transport == 'tcp':
        # Example: tcp://127.0.0.1:5555
        return f"{transport}://{endpoint}"
    elif transport == 'ipc':
        # Example: ipc:///tmp/zmq_socket
        return f"{transport}:///tmp/{endpoint}"
    elif transport == 'inproc':
        # Example: inproc://example
        return f"{transport}://{endpoint}"
    else:
        raise ValueError(f"Unsupported transport type: {transport}")   


"""
@Breif: ZMQ Publish socket with added functionality.
"""
class ZmqPub:
    def __init__(self,transport : str, endpoint : str):
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
    def __init__(self, transport : str, address : str):
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



''' 
MsgFrame: Represents the raw serialized msg from a device. 

|-------------Packet---------|
|-----+-----+----+- - - +----|
| SOF | LEN | ID | DATA | EOF|
| 1   | 1   | 1  | ...  | 1  |
|-----+-----+----+- - - +----|
      |-------Frame-----|

SOF  -- Start of Frame  == '<'
LEN  -- Size of Data (bytes)
ID   --  Topic Identifier 
DATA -- LEN bytes of data
EOF  -- End of Frame == '\n'
    
'''
@dataclass
class MsgFrame():
    size: int =  0
    ID: str = ""
    data: str = ""

    @classmethod
    def extractMsg(cls, msgPacket: str):
        # Extract SIZE ID DATA
        print(msgPacket)
        match = re.match(r'<(.)(.):([^\x00]+)\x00\n', msgPacket) # this doesnt work
        if match:
            size = int(match.group(1))
            ID = match.group(2)
            data = match.group(3)
            if len(data) == size:
                return cls(size, ID, data)
        else:
            return None
        

""" 
Topics: Devices Publish Data over topics. 
        Descriptive names are mapped to msg ids.
        Msgs validated Topics protocol
"""
@dataclass
class Topic:
    ID : str = "" # Topics ID
    name : str = "" # Topics Name
    fmt : str = "" # Topics Data Format 
    delim : str = "," # Data Argument Delimiter
    nArgs : int = 0 # Number of Arguments in Topics Data

class TopicMap:
    def __init__(self): 
        self.topics: Dict[str, Topic] = {}

    def getFormatByName(self, name: str) -> str:
        topic = self.topics.get(name)
        return topic.fmt if topic else ""

    def getFormatByID(self, ID: str) -> str:
        topic = self.topics.get(ID)
        return topic.fmt if topic else ""

    def getNameByID(self, ID: str) -> str:
        topic = self.topics.get(ID)
        return topic.name if topic else ""
    
    def getIDByName(self, name:str) -> str:
        topic = self.topics.get(name)
        return topic.ID if topic else ""

    def getAllTopics(self) -> List[Tuple[str, str, int]]:
        return [(topic.name, topic.fmt, topic.nArgs) for topic in self.topics.values()]

    def registerTopic(self, topicID : str, topicName: str, topicFmt: str, delim: str):
        if delim != "":
            numArgs = len(topicFmt.split(delim))
        else:
            numArgs = 0
        newTopic = Topic(ID=topicID, name=topicName, fmt=topicFmt, delim=delim, nArgs= numArgs)
        self.topics[newTopic.name] = newTopic
