from PyQt6.QtCore import QTimer, QThread, pyqtSignal, pyqtSlot, QEventLoop
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QMainWindow, QMenuBar, QMenu
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QAction

import sys, os
from dataclasses import dataclass , field, asdict
import json

from common.logger import getmylogger
from common.messages import TopicMap, ParameterMap
from common.config import SessionConfig, PlotAppCfg, PlotCfg, AppTypeMap, ConsoleAppCfg, ControllerCfg
from common.zmqutils import Transport, Endpoint

from core.commander import ZMQCommander

from client.menus import FileExplorer
from client.plot import  LinePlot, PlotApp
from client.console import ConsoleAppSettings, Console, ConsoleApp
from client.gui import AppSettingsDialog, SessionConfig, AppSettings
from client.plot import PlotAppCfg, PlotAppSettings, PlotApp, PlotCfg
from client.joystick import JoystickApp
from client.paramTable import ParamTableApp
from client.sigGen import SigGenApp
from recorder import RecorderApp




class App(QMainWindow):
    def __init__(self, cfgFile: str):
        super().__init__()
        self.log = getmylogger(__name__)
        self.setWindowTitle("ComsTermV6")
        self.config = SessionConfig() # Default Config
        self.appWindows = list()
        # Load Config File if provided
        if(cfgFile != None):
            self.log.info(f"Loading App Config File: {cfgFile}")
            self.config.load(cfgFile)
        else:
            self.log.info("No App Config File Provided, Opening Settings")
         
            diag = AppSettingsDialog(self.config) # Settings Menu with default config
            if(diag.exec() == True):
                self.config = diag.settingsUI.config # Update Config with new settings

        self.zmqCommander = ZMQCommander(self.config.controllerAppCfg.paramRegMapFile)
        self.launchSession()

    def launchSession(self):
        self.log.info("Launching Session")
        self.initMenu()
        # load App Windows
        self.plotApp = PlotApp(self.config.plotAppCfg, self.config.topicMap)
        self.appWindows.append(self.plotApp)
        self.plotApp.show()
        self.consoleApp = ConsoleApp(self.config.consoleAppCfg, self.config.topicMap)
        self.appWindows.append(self.consoleApp)
        self.consoleApp.show()
        self.joystickApp = JoystickApp(self.zmqCommander)
        self.appWindows.append(self.joystickApp)
        self.joystickApp.show()
        self.paramTableApp = ParamTableApp(self.zmqCommander)
        self.appWindows.append(self.paramTableApp)
        self.paramTableApp.show()
        self.sigGenApp = SigGenApp()
        self.appWindows.append(self.sigGenApp)
        self.sigGenApp.show()
        self.recorderApp = RecorderApp(transport=Transport.TCP, endpoint=Endpoint.BOT_MSG)
        self.appWindows.append(self.recorderApp)
        self.recorderApp.show()

        self.setCentralWidget(self.paramTableApp)

    def initMenu(self):
        # Menu Bar setup
        self.menu_bar = QMenuBar()
        self.fileMenu = self.menu_bar.addMenu("File")
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.settings)
        if(isinstance(self.fileMenu, QMenu)):
            self.fileMenu.addAction(settings_action)
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        if(isinstance(self.fileMenu, QMenu)):
            self.fileMenu.addAction(exit_action)

        self.appMenu = self.menu_bar.addMenu("Apps")
        if(isinstance(self.appMenu, QMenu)):
            self.plotMenu = self.appMenu.addMenu("Plot")
        new_plot_action = QAction("New", self)
        new_plot_action.triggered.connect(self.newPlot)
        if(isinstance(self.plotMenu, QMenu)):
            self.plotMenu.addAction(new_plot_action)

        if(isinstance(self.appMenu, QMenu)):
            self.consoleMenu = self.appMenu.addMenu("Console")
        new_console_action = QAction("New", self)
        new_console_action.triggered.connect(self.newConsole)
        clear_all_action = QAction("Clear All", self)
        clear_all_action.triggered.connect(self.clearAll)
        if(isinstance(self.consoleMenu, QMenu)):
            self.consoleMenu.addAction(clear_all_action)
            self.consoleMenu.addAction(new_console_action)

        self.setMenuBar(self.menu_bar)

    def settings(self):
        self.log.debug("Opening Settings")

    def newPlot(self):
        self.log.debug("Opening New Plot")

    def newConsole(self):
        self.log.debug("Opening New Console")

    def clearAll(self):
        self.log.debug("Clearing All Consoles")

    def closeEvent(self, event):
        event.accept()



def main():
    app = QApplication(sys.argv)
    guiApp = App("config/test.json")
    guiApp.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()