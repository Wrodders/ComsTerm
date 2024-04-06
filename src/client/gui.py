from PyQt6 import QtCore
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *

from core.device import BaseDevice

from client.plot import CreatePlot, LinePlot
from client.console import ConfigConsole, Console
from client.commander import Commander
from client.menues import DeviceConfig, SettingsMenu
from common.logger import getmylogger
from typing import Dict, List, Tuple


from core.SerialDevice import SerialDevice
from core.ZmqDevice import ZmqDevice
from core.SimulatedDevice import SimulatedDevice

from core.device import Devices

class GUI(QWidget):
    """
    Main Process Interaction GUI Pr
    Handles creation of new GUI submodules and IO Threads

    Each Device has its own IO thread
    GUI Communicated to device
    """
    
    def __init__(self):
        """Constructor method for GUI class."""
        super().__init__()
        self.log = getmylogger(__name__)

        self.setWindowTitle("ComsTermV5")

        self.device = None
        self.windows = list()
     

        self.initUI()
        self.connectSignals()

    def closeEvent(self, event):
        """Event handler for closing the GUI."""
        self.log.info("Closing GUI")
        [win.close() for win in self.windows]
        if isinstance(self.device, BaseDevice):
            self.device._stop()
        event.accept()

    def initUI(self): 
        """Initializes the user interface."""
        self.setGeometry(100, 100, 300, 300)

        self.grid = QGridLayout()
        self.grid.setContentsMargins(10, 10, 10, 10)
        self.setLayout(self.grid)
        # Create Widgets
        self.commander = Commander()
        self.settings = SettingsMenu()
        self.deviceCon = DeviceConfig()



        self.tabs = QTabWidget()
        self.tabs.addTab(self.commander, "Commander")
        self.tabs.addTab(self.settings, "Settings")
        self.tabs.addTab(self.deviceCon, "Device")

        self.newConsoleB = QPushButton("New Console")
        self.newConsoleB.setMaximumWidth(100)
        self.newPlotB = QPushButton("New Plot")
        self.newPlotB.setMaximumWidth(100)

        # Add to Layout
        self.grid.addWidget(self.newPlotB, 0, 0)
        self.grid.addWidget(self.newConsoleB, 0, 1)
        self.grid.addWidget(self.tabs, 1, 0, 4, 4)
        
    def connectSignals(self):
        """Connects signals to slots."""
        # Connect GUI Buttons
        self.newPlotB.clicked.connect(self.newPlotHandle)
        self.newConsoleB.clicked.connect(self.newConsoleHandle)
        self.commander.sendB.clicked.connect(self.sendCmdHandle)
        self.deviceCon.connectBtn.clicked.connect(self.handleConnect)
        self.deviceCon.disconnectBtn.clicked.connect(self.handelDisconnect)


    def newPlotHandle(self):
        """Handles creation of a new plot."""
        diag = CreatePlot()
        diag.exec()
       
    def newConsoleHandle(self):
        """Handles creation of a new console."""
        if(self.device == None):
            err = QMessageBox.critical(self, "Error", "No Device Connected")
            return
        
        diag = ConfigConsole(self.device.pubMap)
        if diag.exec() == True:
            console = Console(topic=diag.getValues())
            self.windows.append(console)
            console.show()
    
    def sendCmdHandle(self):
        """Handles sending a command."""
        text = self.commander.cmdEntry.text()
        self.device[0].sendCmd(text)


    def handleConnect(self):

        if self.device != None:
            err = QMessageBox.information(self, "Info", "Already Connected")
        else:
            if self.deviceCon.conDeviceCB.currentText() == Devices.SERIAL.name:
                self.device = SerialDevice()
                portPath = self.deviceCon.serialConfig.getPort()
                if portPath == "":
                    err = QMessageBox.critical(self, "Error", "No Ports Found")
                    return
                baud = self.deviceCon.serialConfig.getBaud()
                if self.device.connect(portPath, baud ):
                    self.device._start()
            elif self.deviceCon.conDeviceCB.currentText() ==Devices.SIM.name:
                pass
            elif self.deviceCon.conDeviceCB.currentText() == Devices.BLE.name:
                raise NotImplementedError("BLE")
            elif self.deviceCon.conDeviceCB.currentText() == Devices.TCP.name:
                raise NotImplementedError("TCP")
            elif self.deviceCon.conDeviceCB.currentText() == Devices.UDP.name:
                raise NotImplementedError("UDP")
            elif self.deviceCon.conDeviceCB.currentText() == Devices.ZMQ.name:
                raise NotImplementedError("ZMQ")


    def handelDisconnect(self):

        if self.device == None:
            err = QMessageBox.information(self, "Info", "No Connections")
        else:
            self.device._stop()
            del(self.device)
            self.device = None
        


