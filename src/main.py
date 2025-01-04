from PyQt6.QtCore import *
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QAction

import sys, os
from dataclasses import dataclass , field, asdict
import json

from common.logger import getmylogger
from common.messages import TopicMap, ParameterMap
from common.config import SessionConfig, PlotAppCfg, PlotCfg, AppTypeMap, ConsoleAppCfg, ControllerCfg

from core.device import BaseDevice 
from core.comsTerm import ComsTerm

from client.menus import FileExplorer
from client.plot import  LinePlot, PlotApp
from client.console import ConsoleAppSettings, Console, ConsoleApp
from client.controller import ControlsApp
from client.gui import AppSettingsDialog, SessionConfig, AppSettings
from client.plot import PlotAppCfg, PlotAppSettings, PlotApp, PlotCfg


class App(QMainWindow):
    def __init__(self, cfgFile: str):
        super().__init__()
        self.log = getmylogger(__name__)
        self.setWindowTitle("ComsTermV6")
        self.config = SessionConfig() # Default Config
        self.appWindows = list()
        # Load Config File if provided
        if(cfgFile != None):
            self.log.info(f"Loading Config File: {cfgFile}")
            self.config.load(cfgFile)
        else:
            self.log.info("No Config File Provided, Opening Settings")
         
            diag = AppSettingsDialog(self.config) # Settings Menu with default config
            if(diag.exec() == True):
                self.config = diag.settingsUI.config # Update Config with new settings

        self.launchSession()

    def launchSession(self):
        self.log.info("Launching Session")
        self.initMenu()
        self.initUI()
    def initUI(self):
       # Lauch Apps
        for cfg in self.config.appCfgs:
            if(isinstance(cfg.typeCfg, PlotAppCfg)):
                self.appWindows.append(PlotApp(cfg.typeCfg, self.config.topicMap))
            elif(isinstance(cfg.typeCfg, ConsoleAppCfg)):
                self.appWindows.append(ConsoleApp(cfg.typeCfg, self.config.topicMap))
            elif(isinstance(cfg.typeCfg, ControllerCfg)):
                self.appWindows.append(ControlsApp(cfg.typeCfg))
            else:
                self.log.error("Unknown App Type")

        
       

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

    def newConsole(self):
        self.log.debug("Opening New Console")

    def clearAll(self):
        self.log.debug("Clearing All Consoles")

    def closeEvent(self, event):
        self.log.info("Closing App")
        event.accept()



def main():
    app = QApplication(sys.argv)
    guiApp = App(None)
    guiApp.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()