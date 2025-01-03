from PyQt6.QtCore import *
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QAction

import sys

from common.logger import getmylogger
from common.messages import TopicMap

from core.device import BaseDevice 
from core.comsTerm import ComsTerm

from client.plot import  LinePlot, PlotApp
from client.console import ConfigConsole, Console, ConsoleApp
from client.controller import ControlsApp


from client.plot import PlotAppCfg
from dataclasses import dataclass , field, asdict


@dataclass
class AppConfig():
    plotCfg: PlotAppCfg = field(default_factory=PlotAppCfg)
   
    
class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.log = getmylogger(__name__)
        self.setWindowTitle("ComsTermV6")
        self.config = AppConfig()
        self.initMenu()
        # Set the central widget as GUI
        self.gui = GUI()
        self.launchPlot()
        self.setCentralWidget(self.gui)

    def initMenu(self):
        # Menu Bar setup
        self.menu_bar = QMenuBar()
        self.fileMenu = self.menu_bar.addMenu("File")
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.settings)
        self.fileMenu.addAction(settings_action)
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        self.fileMenu.addAction(exit_action)

        self.appMenu = self.menu_bar.addMenu("Apps")
        self.plotMenu = self.appMenu.addMenu("Plot")
        new_plot_action = QAction("New", self)
        new_plot_action.triggered.connect(self.newPlot)
        self.plotMenu.addAction(new_plot_action)


        self.consoleMenu = self.appMenu.addMenu("Console")
        new_console_action = QAction("New", self)
        new_console_action.triggered.connect(self.newConsole)
        clear_all_action = QAction("Clear All", self)
        clear_all_action.triggered.connect(self.clearAll)
        self.consoleMenu.addAction(clear_all_action)
        self.consoleMenu.addAction(new_console_action)

        self.setMenuBar(self.menu_bar)


    def settings(self):
        self.log.debug("Opening Settings")

    def newPlot(self):
        self.log.debug("Opening New Plot")

    def launchPlot(self):
        self.log.debug("Launching PlotApp")
        self.gui.plotApp.beginApp()

    def newConsole(self):
        self.log.debug("Opening New Console")

    def clearAll(self):
        self.log.debug("Clearing All Consoles")
        self.gui.consoleApp.clearAll()

    def closeEvent(self, event):
        self.log.info("Closing App")
        event.accept()

class GUI(QWidget):
    def __init__(self):
        super().__init__()
        self.log = getmylogger(__name__)
        self.setWindowTitle("ComsTermV5")
        self.windows = list()
        # Create applications
        self.controlsApp = ControlsApp()
        self.plotApp = PlotApp("config/cfg_plotCfg.json")
        self.consoleApp = ConsoleApp()
        
        self.initUI()
    def initUI(self):
        # Vertical Splitter: Controls and Console apps
        vSplit = QSplitter(Qt.Orientation.Vertical)
        vSplit.addWidget(self.controlsApp)
        vSplit.addWidget(self.consoleApp)
        vSplit.setSizes([300, 100])

        # Horizontal Splitter: Plot and (Controls + Console)
        hSplit = QSplitter(Qt.Orientation.Horizontal)
        hSplit.addWidget(self.plotApp)
        hSplit.addWidget(vSplit)
        hSplit.setSizes([300, 100])

        hBox = QHBoxLayout()
        hBox.addWidget(hSplit)
        self.setLayout(hBox)


def main():
    app = QApplication(sys.argv)
    guiApp = App()
    guiApp.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()