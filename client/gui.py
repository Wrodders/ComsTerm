"""
Main Process Interaction GUI Pr
Handles creation of new GUI submodules and IO Threads

Each Device has its own IO thread
GUI Communicated to device
"""

from PyQt6 import QtCore
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *

from core.device import BaseDevice

from client.plot import  CreatePlot, LinePlot
from client.console import CreateConsole, Console, ControlFrame, Commander
from logger import getmylogger

log = getmylogger(__name__)

class GUI(QWidget):
    
    def __init__(self, deviceInterface:BaseDevice):
        super().__init__()

        self.setWindowTitle("ComsTermV4")
        self.device = deviceInterface
        self.device.start() # Begin Device Server

        self.initUI()
        self.connectSignals()

    def closeEvent(self, event):
        log.info("Closing GUI")
        self.device.stop() # stop thread
        event.accept()
    def initUI(self): 
        self.setGeometry(100,100, 300, 300)

        self.grid = QGridLayout()
        self.grid.setContentsMargins(10,10,10,10)
        self.setLayout(self.grid)

        #Create Widgets

        self.settingsB = QPushButton("Settings")
        self.settingsB.setMaximumWidth(100)
        self.connectionB = QPushButton("Connections")
        self.connectionB.setMaximumWidth(100)
        self.newConsoleB = QPushButton("New Console")
        self.newConsoleB.setMaximumWidth(100)
        self.newPlotB = QPushButton("New Plot")
        self.newPlotB.setMaximumWidth(100)

        self.commander = Commander()
        # Add to Layout
        self.grid.addWidget(self.settingsB, 0,0)
        self.grid.addWidget(self.connectionB, 0,1)
        self.grid.addWidget(self.newPlotB, 0,2)
        self.grid.addWidget(self.newConsoleB, 0,3)
        self.grid.addWidget(self.commander, 1,0, 4, 4)
        
        
    def connectSignals(self):
        self.newPlotB.clicked.connect(self.newPlotHandle)
        self.newConsoleB.clicked.connect(self.newConsoleHandle)
        self.commander.sendB.clicked.connect(self.sendCmdHandel)
        self.settingsB.clicked.connect(self.settingsHandel)
        self.connectionB.clicked.connect(self.connectionHandel)
     
    def newPlotHandle(self):
        diag = CreatePlot()
        diag.exec()
       
    def newConsoleHandle(self):
        diag = CreateConsole()
        diag.exec()
    
    def sendCmdHandel(self):
        text = self.commander.cmdEntry.text()
        self.device.sendCmd(text)

    def settingsHandel(self):
        pass

    def connectionHandel(self):
        pass
