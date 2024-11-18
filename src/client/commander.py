from PyQt6 import QtCore
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen
import sys
from common.zmqutils import ZmqPub, Transport, Endpoint
from common.messages import Parameter, ParameterMap
from client.joystick import JoystickButton
from common.logger import getmylogger

class CommanderApp(QFrame):
    def __init__(self):
        super().__init__()
        self.log = getmylogger(__name__)
        self.cmdr = Commander()
        self.paramUI = ParamUI(paramMap=self.cmdr.paramRegMap)
        self.controller = Controller(paramMap=self.cmdr.paramRegMap)
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(False)
        self.tabs.addTab(self.paramUI, "Params")
        self.tabs.addTab(self.controller, "Controller")

        vbox = QVBoxLayout()
        vbox.addWidget(self.tabs)
        self.setLayout(vbox)

        self.controller.joystickDataChanged.connect(self.sendJoystickCmd)

        for param in self.paramUI.paramTable:
            if(isinstance(param, ParamReg)):
                param.get_btn.clicked.connect(lambda checked, p=param: self.cmdr.sendGetCmd(paramName=p.label.text()))
                param.set_btn.clicked.connect(lambda checked, p=param: self.cmdr.sendSetCmd(paramName=p.label.text(), value=p.value_entry.text()))

    def sendJoystickCmd(self, paramName, value):
        # Forward the data from joystick to Commander to send the command
        self.cmdr.sendSetCmd(paramName, str(value))


    def _stop(self):
        self.cmdr.publisher.close()



class ParamUI(QFrame):
    def __init__(self, paramMap: ParameterMap):
        super().__init__()
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True) 
    
        vBox = QVBoxLayout()
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        self.paramTable = []
        if(isinstance(paramMap,ParameterMap)):
            [self.paramTable.append(ParamReg(name)) for name in paramMap.getParameterNames()]
            [self.scroll_layout.addWidget(w) for w in self.paramTable]

        self.scroll_area.setWidget(self.scroll_content)
        vBox.addWidget(self.scroll_area) 
        self.setLayout(vBox)

        self.scroll_area.setWidget(self.scroll_content)
        vBox.addWidget(self.scroll_area) 
        self.setLayout(vBox)


class ParamReg(QFrame):
    def __init__(self, paramName: str):
        super().__init__()
        hbox = QHBoxLayout()
        self.setFrameShape(QFrame.Shape.StyledPanel)

        self.label = QLabel(paramName)
        self.value_entry = QLineEdit()
        self.value_entry.setMaximumWidth(75)
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
    

class Controller(QFrame):
    joystickDataChanged = QtCore.pyqtSignal(str, float)
    def __init__(self, paramMap: ParameterMap):
        super().__init__()
        grid = QGridLayout()
        self.setContentsMargins(0,0,0,0)
        self.joy = JoystickButton()

        self.xlable = QLabel("X Param:")
        self.xVal_lbl = QLabel("0")
        self.xPrmCombo = QComboBox()
        self.xPrmCombo.addItems([name for name in paramMap.getParameterNames()])
        self.ylable = QLabel("Y Param:")
        self.yVal_lbl = QLabel("0")
        self.yPrmCombo = QComboBox()
        self.yPrmCombo.addItems([name for name in paramMap.getParameterNames()])

        grid.addWidget(self.joy,0,1,1,3)
        grid.addWidget(self.xlable,1,0)
        grid.addWidget(self.xPrmCombo,1,1)
        grid.addWidget(self.xVal_lbl,2,1)
        grid.addWidget(self.ylable,1,2)
        grid.addWidget(self.yPrmCombo,1,3)
        grid.addWidget(self.yVal_lbl,2,3)
        spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Expanding)
        grid.addItem(spacer, 3, 0, 1, 4)
        self.setLayout(grid)
        self.joy.sigStateChanged.connect(self.handleJoy)

    @QtCore.pyqtSlot(float,float)
    def handleJoy(self,joyX,joyY):
        xVal = round(joyX/2,3)
        xName = self.xPrmCombo.currentText()
        yVal = round(joyY/2,3)
        yName = self.yPrmCombo.currentText()
        self.xVal_lbl.setText(str(xVal))
        self.yVal_lbl.setText(str(yVal))
        self.joystickDataChanged.emit(xName, xVal)
        self.joystickDataChanged.emit(yName, yVal)
      

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

            





