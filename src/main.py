from PyQt6.QtCore import *
from PyQt6.QtWidgets import *

import sys

from common.logger import getmylogger

from core.device import BaseDevice 
from core.comsTerm import ComsTerm

from client.plot import CreatePlot, LinePlot, PlotApp
from client.console import ConfigConsole, Console, ConsoleApp
from client.commander import Commander
from client.controls import CmdBtnFrame
from client.menus import DeviceConfig

class GUI(QWidget):
    def __init__(self):
        super().__init__()
        self.log = getmylogger(__name__)
        self.setWindowTitle("ComsTermV5")
        self.windows = list()
        # Applications
        self.comsTerm = ComsTerm()
        self.plotApp = PlotApp(topicMap=self.comsTerm.device.pubMap)
        self.consoleApp = ConsoleApp(topicMap=self.comsTerm.device.pubMap)
        self.initUI()
    def closeEvent(self, event):
        self.plotApp.close()
        self.consoleApp.close()
        self.comsTerm.stopDevice()
        self.log.info("Closing GUI")
        event.accept()
    
    def initUI(self):
        self.hBox  = QHBoxLayout()
        self.setLayout(self.hBox)
        
        self.connections_PB = QPushButton("Device Connection")
        self.connections_PB.clicked.connect(self.con_handle)
        self.dev_lbl = QLabel("Device : None")

        conFrame = QFrame()
        conLayout = QHBoxLayout()
        conFrame.setLayout(conLayout)
        conLayout.addWidget(self.dev_lbl)
        conLayout.addWidget(self.connections_PB)

        self.splitV = QSplitter(Qt.Orientation.Vertical)
        self.splitV.setChildrenCollapsible(False)

        self.splitV.addWidget(conFrame)
        self.splitV.addWidget(QFrame())
        self.splitV.addWidget(self.consoleApp)

        self.splitH = QSplitter(Qt.Orientation.Horizontal)
        self.splitH.setChildrenCollapsible(False)
        self.splitH.addWidget(self.plotApp)
        self.splitH.addWidget(self.splitV)
        
        self.hBox.addWidget(self.splitH)

    def con_handle(self):
        diag = DeviceConfig()
        if(diag.exec() == True):
            if(("None" not in self.dev_lbl.text())):
                err = QMessageBox.information(self, "Info", f"A Device is Already Connected")
            else:
                self.comsTerm.newDevice(diag.getValues())
                self.dev_lbl.setText(f"Device : {self.comsTerm.device.info.devType.value}: Connected")
                self.plotApp.topicMap = self.comsTerm.device.pubMap
                self.consoleApp.topicMap = self.comsTerm.device.pubMap
        else: 
            self.comsTerm.stopDevice()
            self.dev_lbl.setText("Device : None")


def main():
    app = QApplication(sys.argv)
    gui = GUI()
    gui.show()
   
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
