"""
Main Process Interaction GUI Pr
Handles creation of new GUI submodules and IO Threads

Each Device has its own IO thread
GUI Communicated to device
"""


from PyQt6 import QtCore
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *

import sys, argparse

from device import BaseDevice, SerialDevice, SimulatedDevice, BLEDevice
from plot import  CreatePlot, LinePlot
from console import CreateConsole, Console, ControlFrame, Commander
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




'''
CLI Application
'''
def parse_command_line_args():
    parser = argparse.ArgumentParser(description="GUI application with different data receivers")
    parser.add_argument('--serial', action='store_true', help='Use serial interface')
    parser.add_argument('--simulated', action='store_true', help='Use simulated interface')
    parser.add_argument('--ble', action='store_true', help='Use ble interface')
    #parser.add_argument('--zmq', action='store_true', help='Use zmq interface')
    return parser.parse_args()

def main():

    args = parse_command_line_args()

    if args.serial:
        dataInterface = SerialDevice()
    elif args.simulated:
        dataInterface = SimulatedDevice(0.01)
    elif args.ble:
        dataInterface = BLEDevice("18:62:E4:3C:85:E5")
    else:
        print("Error: Please specify either --serial or --simulated")
        return
    
    app = QApplication(sys.argv)
    gui = GUI(dataInterface)
    gui.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
