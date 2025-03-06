
from dataclasses import dataclass, field
from typing import Dict, List
import csv, json
from typing import Optional, Tuple

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
@dataclass
class Parameter:
    name: str = ""          
    address: int = 0        # We'll map the JSON "id" field here
    access: str = ""        
    format: str = ""        
    description: str = ""   

@dataclass
class ParameterMap:
    nodes: Dict[str, Dict[str, Parameter]] = field(default_factory=dict)
    parameter_id_map: Dict[str, Dict[int, Parameter]] = field(default_factory=dict)
    
    def loadParametersFromJSON(self, filename: str):
        """Load parameters from a JSON file."""
        with open(filename, mode='r') as file:
            data = json.load(file)
            for node_name, node_data in data.items():
                # Ensure the dictionaries for this node exist.
                if node_name not in self.nodes:
                    self.nodes[node_name] = {}
                if node_name not in self.parameter_id_map: # note this overwrites duplicates
                    self.parameter_id_map[node_name] = {}
                    
                for parameter in node_data.get('parameters', []):
                    # Map the "id" from JSON to "address" in our Parameter instance.
                    p = Parameter(
                        name=parameter.get('name', ''),
                        address=parameter.get('id', 0),
                        access=parameter.get('access', ''),
                        format=parameter.get('format', ''),
                        description=parameter.get('description', '')
                    )
                    # Store by name
                    self.nodes[node_name][parameter['name']] = p
                    # Store by address (using the JSON "id")
                    self.parameter_id_map[node_name][parameter['id']] = p

    def getParameterByAddress(self, client_name: str, address: int) -> Parameter | None:
        """Get parameter by client and address."""
        return self.parameter_id_map.get(client_name, {}).get(address)

    def getParameterByName(self, client_name: str, reg_name: str) -> Parameter | None:
        """Get parameter by client and register name."""
        return self.nodes.get(client_name, {}).get(reg_name)

    def getClientParameters(self, client_name: str) -> Dict[str, Parameter]:
        """Get all parameters for a specific client."""
        return self.nodes.get(client_name, {})

    def getAllParameters(self) -> Dict[str, Dict[str, Parameter]]:
        """Get a list of all parameters across all clients."""
        return self.nodes

    def getNodesNames(self) -> List[str]:
        """Get all client (node) names."""
        return list(self.nodes.keys())
        
""" 
Topics: Devices Publish Data over topics. 
        Descriptive names are mapped to msg ids.
        Msgs validated Topics protocol
"""
@dataclass
class Topic:
    ID: str = ""  # Topic ID
    name: str = ""  # Topic Name
    args: List[str] = field(default_factory=list)  # Argument list
    delim: str = ":"  # Delimiter
    format: str = ""  # Data format
    nArgs: int = 0  # Number of arguments

@dataclass
class TopicMap:
    topics: Dict[str, Topic] = field(default_factory=dict)
    names_to_ids: Dict[str, str] = field(default_factory=dict)

    def register(self, topic_name: str, topic_id: str, topic_args: List[str], delim: str):
        """Register a new topic."""
        topic = Topic(ID=topic_id, name=topic_name, args=topic_args, delim=delim, nArgs=len(topic_args) if delim else 0)
        self.topics[topic_id] = topic
        self.names_to_ids[topic_name] = topic_id

    def load_topics_from_json(self, filename: str):
        """Load topics from a JSON file."""
        with open(filename, 'r') as file:
            data = json.load(file)
            for node_name, node_data in data.items():
                for publisher in node_data.get('publishers', []):
                    args = publisher.get('args', [])
                    
                    # Ensure args is a list
                    if isinstance(args, str):
                        args = args.split(", ")

                    topic = Topic(
                        ID=str(publisher.get('id', "")),
                        name=f"{publisher.get('name', '')}/{node_name}",
                        args=args,
                        delim=":",  # Default delimiter
                        format=publisher.get('format', ''),
                        nArgs=len(args)
                    )

                    self.topics[topic.ID] = topic
                    self.names_to_ids[topic.name] = topic.ID

    def get_topic_by_name(self, name: str) -> Optional[Topic]:
        """Get topic by name."""
        topic_id = self.names_to_ids.get(name)
        return self.topics.get(topic_id) if topic_id else None

    def get_topic_format(self, name: str) -> Tuple[Optional[str], Optional[List[str]]]:
        """Get the format of a topic."""
        topic = self.get_topic_by_name(name)
        return (topic.delim, topic.args) if topic else (None, None)

    def get_topic_names(self) -> List[str]:
        """Get all topic names."""
        return list(self.names_to_ids.keys())

    def print_topics(self):
        """Print all registered topics."""
        for topic in self.topics.values():
            print(f"Topic: {topic.name} | ID: {topic.ID} | Args: {topic.args} | Format: {topic.format} | nArgs: {topic.nArgs}")
