from queue import Queue
from enum import Enum

from common.worker import Worker
from common.messages import MsgFrame, TopicMap
from core.zmqutils import ZmqPub, ZmqSub, Transport, Endpoint
from dataclasses import dataclass
from typing import Dict, List, Tuple
from common.logger import getmylogger


class Devices(Enum):
    SERIAL = 0
    UDP = 1
    TCP = 2
    ZMQ = 3
    BLE = 4
    SIM = 5


@dataclass
class DeviceInfo():
    name : str = ""
    devType : Devices = Devices.SIM
    status : bool = False
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
        self.cmdQueue = Queue() 
        self.publisher = ZmqPub(transport=Transport.IPC, endpoint=Endpoint.COMSTERM)

        # Create Base Topic Maps
        self.cmdMap = TopicMap()
        self.pubMap = TopicMap()

        self.cmdMap.registerTopic(topicID = 'a', topicName="ID", topicArgs=[], delim="")
        self.cmdMap.registerTopic(topicID = 'b', topicName="RESET", topicArgs=[], delim="")

        self.pubMap.registerTopic(topicID = 'a', topicName="CMD_RET", topicArgs=["CMDID", "RETVAL"], delim=":")
        self.pubMap.registerTopic(topicID = 'b', topicName="ERROR", topicArgs=[], delim="")
        self.pubMap.registerTopic(topicID = 'c', topicName="INFO", topicArgs=[], delim="")
        self.pubMap.registerTopic(topicID = 'd', topicName="DEBUG", topicArgs=[], delim="")



    def parseCmd(self, text: str) -> str:
        cmdParts = text.split(" ", 1) # cmdName arguments
        cmdName = cmdParts[0] 
        cmdTopic = self.cmdMap.topics.get(cmdName)
        if cmdTopic == None: # exit early if cmd name wrong 
            self.log.warning(f"Cmd Name; {cmdName} not found")
            return ""

        fmt = cmdTopic.fmt # grab the topics protocol format string
        cmdArgs = cmdParts[1:] #extract arguments
        if cmdArgs == []:
            numArgs = 0
        else:
            numArgs = sum(1 for c in cmdArgs[0] if c == cmdTopic.delim) + 1 # num args = num delim + 1 
        if numArgs != cmdTopic.nArgs:
            self.log.warning(f"Cmd syntax error: incorrect num args for {cmdName} {fmt}")
            return ""

        data = cmdTopic.delim.join(cmdArgs)  # Join arguments using delimiter
        cmdID = cmdTopic.ID
        # assemble packet 
        msgPacket = f'<{len(data)}{cmdID}{data}\n'
    
        return msgPacket
        
    def sendCmd(self, text:str):
        """
        @Brief: Push Valid Cmds to Worker IO Queue
        """
        packet = self.parseCmd(text)
        if packet != "":
            self.cmdQueue.put(packet)

    
    def _run(self):
        raise NotImplementedError("Subclasses must implement _run method")
    
    def _start(self) -> bool:
        raise NotImplementedError("Subclasses must implement start method")
    
    def _stop(self):
       self.workerIO._stop()