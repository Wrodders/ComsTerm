from common.messages import ParameterMap, Parameter
from common.zmqutils import ZmqPub, Endpoint, Transport
from common.worker import Worker
from common.logger import getmylogger

class ZMQCommander():
    def __init__(self, paramRegMapFile:str):
        self.paramRegMap = ParameterMap()
        self.paramRegMap.loadParametersFromJSON(paramRegMapFile)
        self.publisher = ZmqPub(endpoint=Endpoint.COMSTERM_CMD, transport=Transport.IPC)
        self.publisher.bind() # Bind Command Publisher
        self.log = getmylogger(__name__)

    def sendGetCmd(self,nodeID:str,  paramName :str) -> bool:
        param = self.paramRegMap.getParameterByName(nodeID,paramName)
        if(isinstance(param, Parameter)):
            paramId = chr(param.address + ord('a')) # encode as ascii
            # SOF | TYPE | ID | DATA(0)| EOF
            packet = ("<" + "a" + paramId).encode() + b'\n' 
            self.publisher.socket.send_multipart([nodeID.encode(), packet])
            self.log.debug(f"Sent {packet} to {nodeID}")
            return True
        else:
            return False
    def sendSetCmd(self, nodeID:str, paramName:str, value:str) -> bool:
                    # SOF | TYPE | ID | DATA(0)| EOF
        param = self.paramRegMap.getParameterByName(nodeID,paramName)
        if(isinstance(param, Parameter)):      
            paramId = chr(param.address + ord('a')) # encode as ascii
            # SOF | ID | TYPE | DATA(0)| EOF
            packet = ("<" + "b" + str(paramId) + str(value)).encode() + b'\n'
            self.publisher.socket.send_multipart([nodeID.encode(), packet])
            self.log.debug(f"Sent {packet} to {nodeID}")
            return True
        else:
            return False

    def sendRunCmd(self, nodeID:str, cmd:str):
        raise NotImplementedError("Not Implemented Yet")
    