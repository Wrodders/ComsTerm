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
from core.SimulatedDevice import SimulatedDevice, SimInfo

from core.device import Devices

from core.comsTerm import ComsTerm

class GUI(QWidget):
    """
    Main Process Interaction GUI 
    Handles creation of new GUI submodules and IO Threads

    Each Window has its own IO thread
    GUI Communicated to device through ComsTerm 
    """
    
    def __init__(self):
        """Constructor method for GUI class."""
        super().__init__()
        self.log = getmylogger(__name__)

        self.setWindowTitle("ComsTermV5")

        self.comsTerm = ComsTerm()
        self.windows = list()
     

        self.initUI()
        self.connectSignals()

    def closeEvent(self, event):
        """Event handler for closing the GUI."""
        self.log.info("Closing GUI")
        [win.close() for win in self.windows]
        self.comsTerm.stopDevice()
        event.accept()

    def initUI(self): 
        """Initializes the user interface."""
        self.setGeometry(100, 100, 300, 300)

        self.grid = QGridLayout()
        self.grid.setContentsMargins(10, 10, 10, 10)
        self.setLayout(self.grid)
        # Create Widgets
        self.devLabel = QLabel("Device: ")
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
        self.grid.addWidget(self.devLabel, 0, 2)
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
        if isinstance(self.comsTerm.device, BaseDevice):
            diag = CreatePlot(self.comsTerm.device.pubMap)
            if diag.exec() == True:
                protocol = diag.topicMenu.saveProtocol()
                plot = LinePlot(protocol=protocol, yrange=(10,-10),xrange=100)
                self.windows.append(plot)
                plot.show()
                pass
        else:
            err = QMessageBox.critical(self, "Error", "No Device Connected")
                
       
    def newConsoleHandle(self):
        """Handles creation of a new console."""
        if(isinstance(self.comsTerm.device, BaseDevice)):
            diag = ConfigConsole(self.comsTerm.device.pubMap)
            if diag.exec() == True:
                protocol = diag.topicMenu.saveProtocol()
                console = Console(topics=protocol)
                self.windows.append(console)
                console.show()
        else:
            err = QMessageBox.critical(self, "Error", "No Device Connected")
            
    
    def sendCmdHandle(self):
        """Handles sending a command."""
        text = self.commander.cmdEntry.text()
        if(isinstance(self.comsTerm.device, BaseDevice)):
            if text == "help":
                devCmds = self.comsTerm.device.cmdMap.getTopicNames()
            
                for cmdName in devCmds:

                    delim ,cmdArgs = self.comsTerm.device.cmdMap.getTopicFormat(cmdName)
                    self.commander._updateData(f"{cmdName} {delim.join(cmdArgs)}") 
            else:
                self.comsTerm.device.sendCmd(text)
        else:
            err = QMessageBox.critical(self, "Error", "No Device Connected")



    def handleConnect(self):
        if isinstance(self.comsTerm.device, BaseDevice):
            err = QMessageBox.information(self, "Info", f"Already Connected")
        else:
            self.comsTerm.newDevice(self.deviceCon.getValues())
            self.devLabel.setText(f"Device : Connected")        
               
 
    def handelDisconnect(self):
        if isinstance(self.comsTerm.device, BaseDevice) == False:
            err = QMessageBox.information(self, "Info", "No Connections")
        else:
            self.comsTerm.stopDevice()
            self.devLabel.setText("Device :")
            self.deviceCon.connectBtn.setDisabled(False)

        


