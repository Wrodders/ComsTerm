import platform
from queue import Queue
from enum import Enum
from dataclasses import dataclass

from common.logger import getmylogger

from common.worker import Worker
from common.messages import TopicMap, Topic, MsgFrame
from common.zmqutils import ZmqPub,Transport, Endpoint



class Devices(Enum):
    SERIAL = 0
    SIMULATED = 1
    ZMQ=2

@dataclass
class DeviceInfo():
    name : str = ""
    devType : Devices = Devices.SIMULATED
    threadId : str = ""
    
"""
@Brief: Base Class for a Device. Handles communications between device and ComsTerm.
@Description:   Implements a set of CMDs and PUBs topics. Parses and Validates Commands against a devices protocols. 
                Controls the Child Devices _run() method to obtain data from I/O.
"""
class BaseDevice():
    def __init__(self):
        super().__init__()
        self.log = getmylogger(__name__)

        self.info = DeviceInfo()
        self.workerIO = Worker(self._run)
        self.info.threadId = self.workerIO.wThread.name
        self.cmdQueue = Queue()
        osName = platform.system()
        if(osName == "Windows"):
            self.publisher = ZmqPub(Transport.TCP, Endpoint.LOOPBACK)
        elif(osName== "Darwin"  or osName =="Linux"): # mac os
            self.publisher = ZmqPub(Transport.INPROC, Endpoint.COMSTERM)
        # Create Base Topic Maps
        self.cmdMap = TopicMap()
        self.pubMap = TopicMap()

    def _run(self):
        raise NotImplementedError("Subclasses must implement _run method")
    
    def _start(self) -> bool:
        raise NotImplementedError("Subclasses must implement start method")
    
    def _stop(self):
        raise NotADirectoryError("Subclass must implement _stop method")

    def pubMsgSubTopics(self, topic: Topic, data:str):
        if topic != None: 
            if(topic.nArgs > 0):
                msgArgs = data.split(topic.delim)
                msgSubTopics = [( topic.name + "/" + arg) for arg in topic.args]
                [self.publisher.send(topic=msgSubTopics[i], data=msgArgs[i]) for i, _ in enumerate(msgArgs)]
            else:
                self.publisher.send(topic=(topic.name + "/"), data=data)

    def parseCmd(self, text: str) -> str:
        cmdParts = text.split(" ", 1) # cmdName arguments
        cmdName = cmdParts[0] 
        cmdTopic = self.cmdMap.getTopicByName(cmdName)
        if cmdTopic == None: # exit early if cmd name wrong 
            self.log.warning(f"Cmd Name; {cmdName} not found")
            return ""

        args = cmdTopic.args # grab the topics protocol format string
        cmdArgs = cmdParts[1:] #extract arguments
        if cmdArgs == []:
            numArgs = 0
        else:
            numArgs = sum(1 for c in cmdArgs[0] if c == cmdTopic.delim) + 1 # num args = num delim + 1 
        if numArgs != cmdTopic.nArgs:
            self.log.warning(f"Cmd syntax error: incorrect num args for {cmdName} {args}")
            return ""

        data = cmdTopic.delim.join(cmdArgs)  # Join arguments using delimiter
        cmdID = cmdTopic.ID
        # assemble packet 
        msgPacket = f"{cmdID}"
        return msgPacket
        
    def sendCmd(self, text:str):
        """
        @Brief: Push Valid Cmds to Worker IO Queue
        """
        packet = self.parseCmd(text)
        if packet != "":
            self.cmdQueue.put(packet)