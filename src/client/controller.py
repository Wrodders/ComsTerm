from PyQt6 import QtCore
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen

from multiprocessing import Process, Pipe
import sys, os

from common.config import ControllerCfg
from common.zmqutils import ZmqPub, Transport, Endpoint
from common.messages import Parameter, ParameterMap
from common.logger import getmylogger

from client.console import Console
from client.joystick import JoystickButton

from core.commander import ZMQCommander
from core.ps4Joy import ps4_joystick_handler


""" ----------------- Controls App ----------------- """
class ControlsApp(QFrame):
    def __init__(self, config: ControllerCfg):
        super().__init__()
        self.log = getmylogger(__name__)
        self.config = config
        self.cmdr = ZMQCommander(config.paramRegMapFile)
        self.paramConfigApp = ParamConfigApp(paramMap=self.cmdr.paramRegMap)
        self.joystickApp = JoyController(paramMap=self.cmdr.paramRegMap)
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(False)
        self.tabs.addTab(self.paramConfigApp, "Params")
        self.tabs.addTab(self.joystickApp, "Controller")

        vbox = QVBoxLayout()
        vbox.addWidget(self.tabs)
        self.setLayout(vbox)
        # Connect App Signals to Commander 
        self.joystickApp.joystickDataChanged.connect(self.sendJoystickCmd)        
        for param in self.paramConfigApp.paramTable:
            if(isinstance(param, ParamReg)):
                param.get_btn.clicked.connect(lambda checked, p=param: self.cmdr.sendGetCmd(paramName=p.label.text()))
                param.set_btn.clicked.connect(lambda checked, p=param: self.cmdr.sendSetCmd(paramName=p.label.text(), value=p.value_entry.text()))

    def sendJoystickCmd(self, paramName, value):
        self.cmdr.sendSetCmd(paramName, str(value))

    def _stop(self):
        self.joystickApp.stopPs4Process()
        self.cmdr.publisher.close()

    def closeEvent(self, event):
        self._stop()
        event.accept()

class JoyController(QFrame):
    joystickDataChanged = QtCore.pyqtSignal(str, float)
    def __init__(self, paramMap: ParameterMap):
        super().__init__()
        grid = QGridLayout()
        self.setContentsMargins(0,0,0,0)
        self.joyBtn = JoystickButton()
        self.xlable = QLabel("X Param:")
        self.xVal_lbl = QLabel("0")
        self.xPrmCombo = QComboBox()
        self.xPrmCombo.addItems([name for name in paramMap.getParameterNames()])
        self.ylabel = QLabel("Y Param:")
        self.yVal_lbl = QLabel("0")
        self.yPrmCombo = QComboBox()
        self.yPrmCombo.addItems([name for name in paramMap.getParameterNames()])
        self.usePS4_ck = QCheckBox()
        self.usePS4_ck.clicked.connect(self.handlePs4)
        self.usePS4_lbl  = QLabel("Use PS4 Controller")

        grid.addWidget(self.joyBtn,0,1,1,3)
        grid.addWidget(self.xlable,1,0)
        grid.addWidget(self.xPrmCombo,1,1)
        grid.addWidget(self.xVal_lbl,2,1)
        grid.addWidget(self.ylabel,1,2)
        grid.addWidget(self.yPrmCombo,1,3)
        grid.addWidget(self.yVal_lbl,2,3)
        grid.addWidget(self.usePS4_lbl, 3,0)
        grid.addWidget(self.usePS4_ck, 3,1)
        spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Expanding)
        grid.addItem(spacer, 4, 0, 1, 4)
        self.setLayout(grid)
        self.joyBtn.sigStateChanged.connect(self.handleJoy)

        self.ps4_process = None
        self.ps4_pipe_parent = None
        self.ps4_timer = QTimer()
        self.ps4_timer.timeout.connect(self.readPs4Data)

    @QtCore.pyqtSlot(float,float)
    def handleJoy(self,joyX,joyY):
        if(not self.usePS4_ck.isChecked() ):
            xVal = round(joyX/2,3)
            xName = self.xPrmCombo.currentText()
            yVal = round(joyY/2,3)
            yName = self.yPrmCombo.currentText()
            self.xVal_lbl.setText(str(xVal))
            self.yVal_lbl.setText(str(yVal))
            self.joystickDataChanged.emit(xName, xVal)
            self.joystickDataChanged.emit(yName, yVal)

    def handlePs4(self):
        if self.usePS4_ck.isChecked():
            self.startPs4Process()
        else:
            self.stopPs4Process()

    def startPs4Process(self):
        """Start the PS4 joystick subprocess."""
        self.ps4_pipe_parent, ps4_pipe_child = Pipe()
        self.ps4_process = Process(target=ps4_joystick_handler, args=(ps4_pipe_child,))
        self.ps4_process.start()
        self.ps4_timer.start(50)  # Poll joystick data every 50ms

    def stopPs4Process(self):
        """Stop the PS4 joystick process."""
        if self.ps4_process and self.ps4_process.is_alive():
            self.ps4_pipe_parent.send("STOP")  
            self.ps4_process.join(timeout=1)  # Wait for graceful exit

        if self.ps4_process:
            if self.ps4_process.is_alive():  
                print("Forcing PS4 process termination...")
                self.ps4_process.terminate()  # Force terminate
                self.ps4_process.join()  # Ensure complete termination

        self.ps4_process = None
        self.ps4_pipe_parent = None

    def readPs4Data(self):
        """Read data from the PS4 joystick subprocess."""
        if self.ps4_pipe_parent and self.ps4_pipe_parent.poll():
            data = self.ps4_pipe_parent.recv()
            if "error" in data:
                print(f"Error: {data['error']}")
                self.usePS4_ck.setChecked(False)
                self.stopPs4Process()
            elif "status" in data:
                print(f"Joystick Status: {data['status']} - {data['name']}")
            else:
                rx = data.get("rx", 0)
                ry = data.get("ry", 0)
                xName = self.xPrmCombo.currentText()
                yName = self.yPrmCombo.currentText()
                self.xVal_lbl.setText(str(-rx))
                self.yVal_lbl.setText(str(ry))
                self.joystickDataChanged.emit(xName, -rx)
                self.joystickDataChanged.emit(yName, ry)

class ParamConfigApp(QFrame):
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

""" ----------------- Controls App Settings ----------------- """

class ControlsAppSettings(QFrame):
    def __init__(self, config: ControllerCfg):
        super().__init__()
        self.log = getmylogger(__name__)
        self.config = config
        self.initUI()

    def initUI(self):
        pass
 

