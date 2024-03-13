from queue import Queue
from enum import Enum

from common.worker import Worker
from core.messages import MsgFrame, TopicMap
from core.zmqutils import ZmqPub, ZmqSub, Transport, Endpoint

from logger import getmylogger


log = getmylogger(__name__)

class Devices(Enum):
    SERIAL = 0
    UDP = 1
    TCP = 2
    ZMQ = 3
    BLE = 4
    



"""
@Brief: Base Class for a Device. Handles communications between device and ComsTerm.
@Description:   Implements a set of CMDs and PUBs topics. Parses and Validates Commands against a devices protocols. 
                Controls the Child Devices _run() method to obtain data from I/O.
"""
class BaseDevice():
    def __init__(self):
        super().__init__()
        self.name = str()

        self.workerIO = Worker(self._run)
        self.cmdQueue = Queue() 
        self.publisher = ZmqPub(transport=Transport.IPC, endpoint=Endpoint.COMSTERM)

        # Create Base Topic Maps
        self.cmdMap = TopicMap()
        self.pubMap = TopicMap()

        self.cmdMap.registerTopic(topicID = 'a', topicName="ID", topicFmt="", delim="")
        self.cmdMap.registerTopic(topicID = 'b', topicName="RESET", topicFmt="d:d", delim=":")

        self.pubMap.registerTopic(topicID = 'a', topicName="CMD_RET", topicFmt="s", delim="")
        self.pubMap.registerTopic(topicID = 'b', topicName="ERR", topicFmt="s", delim="")
        self.pubMap.registerTopic(topicID = 'c', topicName="INFO", topicFmt="s", delim="")

        topics = self.pubMap.getAllTopics()
        print(topics)


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
        if numArgs != cmdTopic.nArgs:
            log.warning(f"Cmd syntax error: incorrect num args for {cmdName} {fmt}")
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
    
    def _start(self):
        raise NotImplementedError("Subclasses must implement start method")
    
    def _stop(self):
       self.workerIO._stop()