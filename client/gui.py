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
from client.console import CreateConsole, Console
from client.commander import Commander
from client.menues import ConnectionsDialog
from common.logger import getmylogger



class GUI(QWidget):
    
    def __init__(self, deviceInterface:BaseDevice):
        super().__init__()
        self.log = getmylogger(__name__)

        self.setWindowTitle("ComsTermV5")
        self.device = deviceInterface
        self.device._start() # Begin Device Server

        self.windows = list()
        self.devices = list()

        self.initUI()
        self.connectSignals()

    def closeEvent(self, event):
        self.log.info("Closing GUI")
        [win.close() for win in self.windows]
        self.device._stop() # stop device thread
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
        # Connect GUI Buttons
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
        if diag.exec() == True:
            console = Console(topic=diag.getValues())
            self.windows.append(console)
            console.show()
    
    def sendCmdHandel(self):
        text = self.commander.cmdEntry.text()
        self.device.sendCmd(text)

    def settingsHandel(self):
        pass

    def connectionHandel(self):
        diag = ConnectionsDialog()
        if diag.exec() == True:
            pass



