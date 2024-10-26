
from dataclasses import dataclass, field
from typing import Dict, List
import csv

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

@dataclass
class TopicMap:
    topics: Dict[str, Topic] = field(default_factory=dict)
    namesToIds: Dict[str, str] = field(default_factory=dict)
    numTopics = int()

    def register(self, topicName: str, topicID:str, topicArgs: List[str], delim: str):
        """Register a new topic"""
        numArgs = len(topicArgs) if delim else 0
        topic = Topic(ID=topicID, name=topicName, args=topicArgs, delim=delim, nArgs=numArgs)
        self.numTopics += 1
        self.topics[topicID] = topic
        self.namesToIds[topicName] = topicID

    def loadTopicsFromCSV(self, filename: str):
        """Load topics from a CSV file"""
        with open(filename, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                topicName = row['PubName']
                topicID = chr((int(row['pubid']) + ord('a')))
                topicArgs = [arg  for arg in row['format'].split(':')]  # Split format string into list
                delim = row['delim']
                self.register(topicName,topicID, topicArgs, delim)

    def getTopicByID(self, topic_id: str) -> Topic | None:
        """Get topic by ID"""
        return self.topics.get(topic_id)
    
    def getTopicByName(self, name: str) -> Topic | None:
        """Get topic by name"""
        topicId = self.namesToIds.get(name)
        if topicId:
            return self.topics[topicId]
        return None

    def getTopicFormat(self, name: str) -> tuple[str, list]:
        topicId= self.namesToIds.get(name)
        if topicId:
            return (self.topics[topicId].delim, self.topics[topicId].args)
        else:
            return (str(), list())
        
    def getTopicNames(self) -> List[str]:
        return list(set([topic.name for topic in self.topics.values()]))
    

    def getTopics(self) -> List[Topic]:
        return list(self.topics.values())