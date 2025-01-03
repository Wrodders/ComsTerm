from common.messages import ParameterMap
from common.zmqutils import ZmqPub, Endpoint, Transport


class ZMQCommander():
    def __init__(self):
        self.paramRegMap = ParameterMap()
        self.paramRegMap.loadParametersFromCSV('paramRegMap.csv')
        self.publisher = ZmqPub(endpoint=Endpoint.COMSTERM_CMD, transport=Transport.IPC)
        self.publisher.bind()
        
    def sendGetCmd(self, paramName :str):
        paramId = self.paramRegMap.getParameterByRegister(paramName)
        if(paramId):
            paramId = paramId.address
            # SOF | TYPE | ID | DATA(0)| EOF
            packet = ("<" + "a" + paramId).encode() + b'\n'
            self.publisher.socket.send_multipart([b"SERIAL", packet])

    def sendSetCmd(self, paramName:str, value:str):
                    # SOF | TYPE | ID | DATA(0)| EOF
        paramId = self.paramRegMap.getParameterByRegister(paramName)
        
        if(paramId):
            paramId = paramId.address
            # SOF | ID | TYPE | DATA(0)| EOF
            packet = ("<" + "b" + paramId + str(value)).encode() + b'\n'
            self.publisher.socket.send_multipart([b"SERIAL", packet])