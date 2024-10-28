from PyQt6 import QtCore
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen
import sys
from common.zmqutils import ZmqPub, Transport, Endpoint
from common.messages import Parameter, ParameterMap

class CommanderApp(QWidget):
    def __init__(self):
        super().__init__()
        self.cmdr = Commander()
        self.setMinimumHeight(200)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True) 

        vBox = QVBoxLayout()
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        self.paramsUI = []
        if(isinstance(self.cmdr.paramRegMap,ParameterMap)):
            [self.paramsUI.append(ParamReg(name)) for name in self.cmdr.paramRegMap.getParameterNames()]
            [self.scroll_layout.addWidget(w) for w in self.paramsUI]

        self.scroll_area.setWidget(self.scroll_content)
        vBox.addWidget(self.scroll_area) 
        self.setLayout(vBox)

        for param in self.paramsUI:
            if(isinstance(param, ParamReg)):
                param.get_btn.clicked.connect(lambda checked, p=param: self.cmdr.sendGetCmd(paramName=p.label.text()))
                param.set_btn.clicked.connect(lambda checked, p=param: self.cmdr.sendSetCmd(paramName=p.label.text(), value=p.value_entry.text()))

    def _stop(self):
        self.cmdr.publisher.close()
                

class Commander():
    def __init__(self):
        self.paramRegMap = ParameterMap()
        self.paramRegMap.loadParametersFromCSV('paramRegMap.csv')
        self.publisher = ZmqPub(endpoint=Endpoint.COMSTERM_CMD, transport=Transport.INPROC)
        self.publisher.bind()
        
    def sendGetCmd(self, paramName :str):
        paramId = self.paramRegMap.getParameterByRegister(paramName)
        
        if(paramId):
            paramId = paramId.address
            # SOF | ID | TYPE | DATA(0)| EOF
            packet = ("<" + paramId +"a").encode() + b'\n'
            self.publisher.socket.send_multipart([b"SERIAL", packet])


    def sendSetCmd(self, paramName:str, value:str):
                    # SOF | ID | TYPE | DATA(0)| EOF
        paramId = self.paramRegMap.getParameterByRegister(paramName)
        
        if(paramId):
            paramId = paramId.address
            # SOF | ID | TYPE | DATA(0)| EOF
            packet = ("<" + paramId + "b" + str(value)).encode() + b'\n'
            self.publisher.socket.send_multipart([b"SERIAL", packet])

            


class ParamReg(QFrame):
    def __init__(self, paramName: str):
        super().__init__()
        hbox = QHBoxLayout()
        self.setFrameShape(QFrame.Shape.StyledPanel)

        self.label = QLabel(paramName)
        self.value_entry = QLineEdit()
        self.value_entry.setMaximumWidth(250)
        self.get_btn = QPushButton("Get")
        self.get_btn.setMaximumWidth(50)
        self.get_btn.clicked.connect(self.get_handle)
        self.set_btn = QPushButton("Set")
        self.set_btn.setMaximumWidth(50)
        self.set_btn.clicked.connect(self.set_handle)

        self.setLayout(hbox)
        hbox.addWidget(self.label)
        hbox.addWidget(self.value_entry)
        hbox.addWidget(self.get_btn)
        hbox.addWidget(self.set_btn)

    def set_handle(self):
        pass

    def get_handle(self):
        pass


