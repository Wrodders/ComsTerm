from PyQt6 import QtCore
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *

import sys, argparse

from device import BaseInterface, SerialDevice, SimulatedDevice
from plot import  CreatePlot, LinePlot
from console import CreateConsole, Console, CommandFrame
from logger import getmylogger

log = getmylogger(__name__)

class GUI(QWidget):
    
    def __init__(self, deviceInterface:BaseInterface):
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
        self.setGeometry(100,100, 600, 300)

        self.grid = QGridLayout()
        self.grid.setContentsMargins(0,0,0,0)
        self.setLayout(self.grid)

        #Create Widgets
        self.consoleFrame = TabFrame("Console", 4)
        self.controlFrame = CommandFrame()
        self.plotFrame = TabFrame("Plot", 4)

        #create Splitters
        vSplit = QSplitter(Qt.Orientation.Vertical)
        vSplit.setChildrenCollapsible(True)
        vSplit.addWidget(self.consoleFrame)
        vSplit.addWidget(self.controlFrame)

        hSplit = QSplitter(Qt.Orientation.Horizontal) # main splitter
        hSplit.setChildrenCollapsible(True)
        hSplit.addWidget(vSplit) # add splitter Frames to left
        hSplit.addWidget(self.plotFrame)

        # Add to Layout
        self.grid.addWidget(hSplit)
        
    def connectSignals(self):
        self.plotFrame.newTabB.clicked.connect(self.newPlotHandle)
        self.consoleFrame.newTabB.clicked.connect(self.newConsoleHandle)
        self.controlFrame.sendB.clicked.connect(self.sendCmdHandel)

    def newPlotHandle(self):
        if self.plotFrame.checkMaxTabs():
            log.error("Max Number of plots reached")
            return 
        diag = CreatePlot()
        if diag.exec() == True:
            topic, plotType, yRange, time_window, protocol = diag.getValues()
            if plotType == "Line Plot":
                plot = LinePlot(topic, yRange, time_window, protocol)
                self.plotFrame.newTab(plot, topic)
                self.device.deviceDataSig.connect(plot._updateData) # connect new plot to signal

    def newConsoleHandle(self):
        if self.consoleFrame.checkMaxTabs():
            log.error("Max Number of consoles reached")
            return 
        diag = CreateConsole()
        if diag.exec() == True:
            topic = diag.getValues()
            console = Console(topic=topic)
            self.consoleFrame.newTab(console, topic)
            self.device.deviceDataSig.connect(console._updateData)

    def sendCmdHandel(self):
        text = self.controlFrame.cmdEntry.text()
        self.device.sendCmd(text)




class TabFrame(QFrame):
    def __init__(self, frameType : str, maxTabs : int):
        super().__init__()
        self.numTabs = 0
        self.frameType = frameType
        self.maxTabs = maxTabs
        self.initUI()
        self.connectSignals()

    def initUI(self):
        self.grid = QGridLayout()
        self.setMinimumWidth = 400

        self.tabs = QTabWidget()
        self.initTabs()

        self.newTabB = QPushButton(f"New {self.frameType}")
        self.newTabB.setMaximumWidth(100)

        self.grid.addWidget(self.tabs, 0,0,4,4)
        self.grid.addWidget(self.newTabB, 4,0)

        self.setLayout(self.grid)

    def connectSignals(self):
        self.tabs.currentChanged.connect(self.tabChangedHandle)
    
    def initTabs(self):
        placeholder = QWidget()
        self.tabs.addTab(placeholder, self.frameType)
        self.numTabs = 0

    def tabChangedHandle(self):
        pass

    def checkMaxTabs(self) -> bool:
        return self.numTabs == self.maxTabs
    
    def newTab(self, tabWidget : QWidget, tabName : str):
        if self.numTabs == 0:
            self.tabs.removeTab(0)
        idx = self.tabs.addTab(tabWidget, tabName)
        self.numTabs +=1
        self.tabs.setCurrentIndex(idx)






'''
CLI Application
'''
def parse_command_line_args():
    parser = argparse.ArgumentParser(description="GUI application with different data receivers")
    parser.add_argument('--serial', action='store_true', help='Use serial interface')
    parser.add_argument('--simulated', action='store_true', help='Use simulated interface')
    #parser.add_argument('--zmq', action='store_true', help='Use zmq interface')
    return parser.parse_args()

def main():

    args = parse_command_line_args()

    if args.serial:
        dataInterface = SerialDevice()
    elif args.simulated:
        dataInterface = SimulatedDevice(0.01)
    else:
        print("Error: Please specify either --serial or --simulated")
        return
    
    app = QApplication(sys.argv)
    gui = GUI(dataInterface)
    gui.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
