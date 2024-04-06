
from dataclasses import dataclass, field
from typing import Dict, List, Tuple



''' 
MsgFrame: Represents the raw serialized msg from a device. 

|-------Packet---------|
|-----+----+- - - +----|
| SOF | ID | DATA | EOF|
| 1   | 1  | ...  | 1  |
|-----+----+- - - +----|
      |------Frame-----|

SOF  -- Start of Frame  == '<'
ID   --  Topic Identifier 
DATA -- LEN bytes of data
EOF  -- End of Frame == '\n'
    
'''
@dataclass
class MsgFrame():
    ID: str = ""
    data: str = ""

    @classmethod
    def extractMsg(cls, packet:str):
        ID = str(packet[1])
        data = packet[2:]
        return cls(ID=ID, data=data)

        

""" 
Topics: Devices Publish Data over topics. 
        Descriptive names are mapped to msg ids.
        Msgs validated Topics protocol
"""
@dataclass
class Topic:
    ID : str = "" # Topics ID
    name : str = "" # Topics Name
    args: List[str] = field(default_factory=list)
    delim : str = ":" # Data Argument Delimiter
    nArgs : int = 0 # Number of Arguments in Topics Data

class TopicMap:
    def __init__(self): 
        self.topics: Dict[str, Topic] = {}

    def getTopicNameFormat(self, name: str) -> tuple[str, list]:
        topic = self.topics.get(name)
        if isinstance(topic, Topic):
            return (topic.delim, topic.args)
        else:
            return (str(), list())

    def getTopicIDFormat(self, ID: str)-> tuple[str, list]:
        topic = self.topics.get(ID)
        if isinstance(topic, Topic):
            return (topic.delim, topic.args)
        else:
            return (str(), list())

    def getNameByID(self, ID: str) -> str:
        
        topic = self.topics.get(ID)
    
        return topic.name if topic else ""
    
    def getIDByName(self, name:str) -> str:
        topic = self.topics.get(name)
        return topic.ID if topic else ""

    def getTopicNames(self) -> List[str]:
        
        return list(set([topic.name for topic in self.topics.values()]))
    


    def registerTopic(self, topicID : str, topicName: str, topicArgs: List[str], delim: str):
        if delim != "":
            numArgs = len(topicArgs)
        else:
            numArgs = 0
        newTopic = Topic(ID=topicID, name=topicName, args=topicArgs, delim=delim, nArgs= numArgs)
        self.topics[newTopic.name] = newTopic
        self.topics[newTopic.ID] = newTopic
    
