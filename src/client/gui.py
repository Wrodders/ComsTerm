from PyQt6.QtCore import *
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import *

import os

from client.menus import FileExplorer
from client.plot import PlotAppSettings
from client.console import ConsoleAppSettings
from client.controller import ControlsAppSettings

from common.logger import getmylogger
from common.config import SessionConfig, AppTypeMap, PlotAppCfg, ConsoleAppCfg, ControllerCfg, AppCfg, CfgBase



class AppSettings(QFrame):
    def __init__(self, config: SessionConfig):
        super().__init__()
        self.log = getmylogger(__name__)
        self.setWindowTitle("Settings")
        self.config = config

        self.plotSettings = PlotAppSettings(PlotAppCfg(), self.config.topicMap)
        self.consoleSettings = ConsoleAppSettings(ConsoleAppCfg(), self.config.topicMap)
        self.controlsSettings = ControlsAppSettings(ControllerCfg())
        self.initUI()

    def initUI(self):
        # List of Applications on Left
        # Stacked Layout on Right for each apps settings
        self.appList = QListWidget()
        self.appList.setMaximumWidth(100)
        self.appList.addItem("General")
        self.appList.addItems(AppTypeMap.keys())
        self.appList.setCurrentRow(0)
        self.sessionFile = FileExplorer("Session Config")
        self.stackedLayout = QStackedLayout()
        self.stackedLayout.addWidget(self.sessionFile)# General Settings Page
        self.stackedLayout.addWidget(self.plotSettings)
        self.stackedLayout.addWidget(self.consoleSettings)
        self.stackedLayout.addWidget(self.controlsSettings)
    
        # Connect the list widget to the stacked layout
        self.appList.currentRowChanged.connect(self.stackedLayout.setCurrentIndex)
        # Layout
        layout = QGridLayout()
        layout.addWidget(self.appList, 0, 0)
        layout.addLayout(self.stackedLayout, 0, 1, 2, 1)
        self.setLayout(layout)

    def updateConfig(self):
        self.plotSettings.updateConfig()
        self.consoleSettings.updateConfig()
        self.controlsSettings.updateConfig()

    def load_handle(self):
        print("Load Config")

    def save_handle(self):
        self.updateConfig()
        sessionFp = self.sessionFile.fileEntry.text()
        # dont save if no file provided, 
        # if file path exists prompt message box overwriting
        if(sessionFp != ""):
            if(os.path.exists(sessionFp)):
                reply = QMessageBox.question(self, "File Exists", "Overwrite Existing File?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if(reply == QMessageBox.StandardButton.No):
                    return
                self.config.save(sessionFp)
                self.log.info(f"Saved Session Config to: {sessionFp}")
        else:
            QMessageBox.information(self, "No File Provided", "No File Provided, Not Saving")
            self.appList.setCurrentRow(0)

class AppSettingsDialog(QDialog):
    def __init__(self, config: SessionConfig):
        super().__init__()
        self.setWindowTitle("ComsTerm Settings")
        # create settings UI with current config
        self.settingsUI = AppSettings(config) 
        self.initUI()
    
    def initUI(self):
        QBtn = (
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.handleAccepted)
        self.buttonBox.rejected.connect(self.reject)

        self.saveButton = QPushButton("Save")
        self.saveButton.clicked.connect(self.settingsUI.save_handle)

        layout = QGridLayout()
        layout.addWidget(self.settingsUI, 0, 0, 1, 2)
        layout.addWidget(self.saveButton, 1, 0)
        layout.addWidget(self.buttonBox, 1, 1)

        self.setLayout(layout)
    
    def handleAccepted(self):
        self.settingsUI.updateConfig()
        self.accept()