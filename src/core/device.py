from enum import Enum
from dataclasses import dataclass

from common.logger import getmylogger

from common.worker import Worker
from common.messages import TopicMap, Topic, MsgFrame, Parameter, ParameterMap
from common.zmqutils import ZmqPub, Transport, Endpoint, ZmqSub



class Devices(Enum):
    SERIAL = 0
    SIMULATED = 1
    ZMQ=2

@dataclass
class DeviceInfo():
    name : str = ""
    devType : Devices = Devices.SIMULATED
    pubEndpoint : Endpoint = Endpoint.COMSTERM_MSG
    pubTransport : Transport =Transport.INPROC
    cmdEndpoint : Endpoint = Endpoint.COMSTERM_CMD
    cmdTransport : Transport =Transport.INPROC
    

    
"""
@Brief: Base Class for a Device. Handles communications between device and ComsTerm.
@Description:   Implements a set of CMDs and PUBs topics. Parses and Validates Commands against a devices protocols. 
                Controls the Child Devices _run() method to obtain data from I/O.
"""
class BaseDevice():
    def __init__(self, pubEndpoint: Endpoint, pubTransport:Transport, cmdEndpoint: Endpoint, cmdTransport:Transport):
        super().__init__()
        self.log = getmylogger(__name__)

        self.info = DeviceInfo()

        self.workerRead = Worker(self._readDevice)
        self.workerWrite = Worker(self._writeDevice) 
        self.msgPublisher = ZmqPub(pubTransport, pubEndpoint)
        self.cmdSubscriber = ZmqSub(cmdTransport, cmdEndpoint)
        # Create Base Topic Maps
        self.pubMap = TopicMap()


        
    def _start(self) -> bool:
        raise NotImplementedError("Subclasses must implement start method")
    
    def _stop(self):    
        raise NotImplementedError("Subclasses Must Implemetn _stop")
  
       
    def _readDevice(self):
        raise NotImplementedError("Subclass must implement _readDevice method")
    
    def _writeDevice(self):
        raise NotImplementedError("Subclass must implement _writeDevice method")
    

    def pubMsgSubTopics(self, topic: Topic, data:str):
        if topic != None: 
            if(topic.nArgs > 0):
                msgArgs = data.split(topic.delim)
                msgSubTopics = [( topic.name +"/" +arg) for arg in topic.args]
                [self.msgPublisher.send(topic=msgSubTopics[i], data=msgArgs[i]) for i, _ in enumerate(msgArgs)]
            else:
                self.msgPublisher.send(topic=(topic.name +"/"), data=data)
