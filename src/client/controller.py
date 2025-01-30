from PyQt6.QtWidgets import *


from common.config import ControllerCfg
from common.logger import getmylogger
from client.menus import FileExplorer, SettingsUI



""" ----------------- Controls App Settings ----------------- """
class ControlsAppSettings(SettingsUI):
    def __init__(self, config: ControllerCfg):
        super().__init__()
        self.log = getmylogger(__name__)
        self.config = config
        self.initUI()

    def initUI(self):
        self.paramMapEntry = FileExplorer("Parameter Map")
        self.paramMapEntry.fileEntry.setText(self.config.paramRegMapFile)
        layout = QVBoxLayout()
        layout.addWidget(self.paramMapEntry)
        self.setLayout(layout)

    def updateConfig(self):
        self.config.paramRegMapFile = self.paramMapEntry.fileEntry.text()
 

