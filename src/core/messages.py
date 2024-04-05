
from dataclasses import dataclass
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

    def getAllTopics(self) -> List[Tuple[str, str,  str, int]]:
        return [(topic.name, topic.ID, topic.fmt, topic.nArgs) for topic in self.topics.values()]

    def registerTopic(self, topicID : str, topicName: str, topicFmt: str, delim: str):
        if delim != "":
            numArgs = len(topicFmt.split(delim))
        else:
            numArgs = 0
        newTopic = Topic(ID=topicID, name=topicName, fmt=topicFmt, delim=delim, nArgs= numArgs)
        self.topics[newTopic.name] = newTopic
        self.topics[newTopic.ID] = newTopic
    
