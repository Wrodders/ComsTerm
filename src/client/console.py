from PyQt6 import QtCore
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *

from client.zmqQtBridge import ZmqBridgeQt
from client.menus import DataSeriesTableSettings, DataSeriesTable, SettingsUI

from common.logger import getmylogger
from common.messages import TopicMap
from common.config import ConsoleAppCfg, ConsoleCfg

""" ----------------- Console App ----------------- """
class ConsoleApp(QFrame):
    def __init__(self, config: ConsoleAppCfg, topicMap: TopicMap):
        super().__init__()
        self.log = getmylogger(__name__)
        self.config = config
        self.topicMap = topicMap
        self.consoles = list()
        self.initUI()
        for consoleCfg in self.config.consoleCfgs:
            self.newConsole(consoleCfg)

    def closeEvent(self, event):
        for console in self.consoles:
            console.close()
        event.accept()

    def initUI(self):
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab_handle)
        self.clear_PB = QPushButton("Clear")
        self.clear_PB.clicked.connect(self.clear_handle)

        grid = QGridLayout()
        self.setLayout(grid)
        grid.addWidget(self.tabs, 0,0, 2, 4)
        grid.addWidget(self.clear_PB, 2, 0, 1, 1)

    def newConsole(self, consoleCfg: ConsoleCfg):
        console = Console(topicMap=self.topicMap, subscritions=consoleCfg.protocol, name=consoleCfg.name)
        self.consoles.append(console)
        self.tabs.addTab(console, console.name)

    def close_tab_handle(self, index):
        active_console = self.tabs.widget(index)
        if(isinstance(active_console, Console)):
            active_console.close()
            self.tabs.removeTab(index)

    def clear_handle(self):
        active_console = self.tabs.currentWidget()
        if(isinstance(active_console, Console)):
            active_console.clear()
    
    def settings_handle(self):
        active_console = self.tabs.currentWidget()
        if(isinstance(active_console, Console)):
            print("Settings")

class Console(QWidget):
    def __init__(self, topicMap: TopicMap,  subscritions: tuple[str, ...], name: str = "Console"):
        super().__init__()
        self.log = getmylogger(__name__)
        self.name = name
        self.topicMap = topicMap
        self.topics = subscritions

        self.initUI()
        self.zmqBridge = ZmqBridgeQt(topicMap=self.topicMap)
        self.zmqBridge.registerSubscriptions(self.topics)
        self.zmqBridge.msgSig.connect(self._updateData)
        self.zmqBridge.workerIO._begin()
               
    def closeEvent(self, event):
        self.log.debug(f"Closing Console {self.name}")
        self.zmqBridge.workerIO._stop()  # stop device thread
        event.accept()

    def initUI(self):
        """Initializes the user interface."""
        self.consoleText = QTextEdit()
        self.consoleText.setReadOnly(True)
        self.consoleText.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.consoleText.setAcceptRichText(True)
        self.consoleText.setStyleSheet("background-color: black; color: green;")
        
        self.vBox = QVBoxLayout()
        self.vBox.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.vBox)
        self.vBox.addWidget(self.consoleText)

    def clear(self):
        self.consoleText.clear()

    @QtCore.pyqtSlot(tuple)
    def _updateData(self, msg: tuple[str, str]):
        topic, data = msg
        if(isinstance(self.consoleText.document, QTextEdit)):
            if self.consoleText.document().lineCount() > 200:
                self.consoleText.clear()

        self.consoleText.append(topic +"    "+data)  # add data to console tab spaced

""" ----------------- Console App Settings ----------------- """

class ConsoleAppSettings(SettingsUI):
    def __init__(self,  config: ConsoleAppCfg, topicMap: TopicMap ):
        super().__init__()
        self.setWindowTitle("Console Settings")
        self.log = getmylogger(__name__)
        self.config = config
        self.topicMap = topicMap
        self.initUI()

    def initUI(self):
        self.dataSeriesConfig = DataSeriesTableSettings(self.topicMap)
        self.consoleList = QListWidget()
        self.consoleConfigStack = QStackedLayout()
        if(isinstance(self.config, ConsoleAppCfg)):
            for idx in range(len(self.config.consoleCfgs)):
                self.createConsoleCfg(self.config.consoleCfgs[idx])
            # Auto switch
            self.consoleList.currentRowChanged.connect(self.consoleConfigStack.setCurrentIndex)
            self.addConsole_PB = QPushButton("+")
            self.addConsole_PB.clicked.connect(lambda: self.addConsole_handle(ConsoleCfg()))
            self.removeConsole_PB = QPushButton("-")
            self.removeConsole_PB.clicked.connect(self.removeConsole_handle)     
            self.dataSeriesConfig.addSeriesBtn.clicked.connect(
                lambda: self.consoleConfigStack.currentWidget().table.addSeries(self.dataSeriesConfig.grabSeries()))
            self.dataSeriesConfig.removeSeriesBtn.clicked.connect(
                lambda: self.consoleConfigStack.currentWidget().table.removeSeries())
            grid = QGridLayout()
            grid.addWidget(self.consoleList, 0, 0, 1, 2)
            grid.addWidget(self.addConsole_PB, 1, 0)
            grid.addWidget(self.removeConsole_PB, 1, 1)
            hbox = QHBoxLayout()
            hbox.addLayout(grid)
            hbox.addWidget(self.dataSeriesConfig)
            hbox.addLayout(self.consoleConfigStack)
            self.setLayout(hbox)


    def createConsoleCfg(self, consoleCfg: ConsoleCfg):
        new_consoleSettings = ConsoleSettings(consoleCfg)
        self.consoleList.addItem(consoleCfg.name)
        self.consoleList.setCurrentRow(self.consoleList.count()-1)
        listWidget = self.consoleList.currentItem()
        if(isinstance(listWidget, QListWidgetItem)):
            new_consoleSettings.consoleName.textChanged.connect(
                lambda: listWidget.setText(new_consoleSettings.consoleName.text()))
            self.consoleConfigStack.addWidget(new_consoleSettings)
            self.consoleConfigStack.setCurrentIndex(self.consoleConfigStack.count()-1)

    def updateConfig(self):
        for i in range(self.consoleList.count()):
            stackWidget = self.consoleConfigStack.widget(i)
            if(isinstance(stackWidget, ConsoleSettings)):
                stackWidget.updateConfig() # Update Config for each console
                self.config.consoleCfgs[i] = stackWidget.config # Apply to app config 

    def addConsole_handle(self, consoleCfg: ConsoleCfg):
        self.config.consoleCfgs.append(consoleCfg)
        self.createConsoleCfg(consoleCfg)

    def removeConsole_handle(self, index):
        self.consoleConfigStack.removeWidget(self.consoleConfigStack.currentWidget())
        self.config.consoleCfgs.pop(index)
        self.consoleList.takeItem(self.consoleList.currentRow())
      
    def load_handle(self, fp):
        for idx in range(self.consoleList.count()):
            self.consoleList.setCurrentRow(idx)
            self.removeConsole_handle(idx)
        self.config.load(fp)
        for consoleCfg in self.config.consoleCfgs:
            self.addConsole_handle(consoleCfg)

  
class ConsoleSettings(SettingsUI):
    def __init__(self, config: ConsoleCfg):
        super().__init__()
        self.log = getmylogger(__name__)
        self.config = config
        self.initUI()
    
    def initUI(self):
        self.consoleName = QLineEdit(self.config.name)
        self.sampleBuffer = QLineEdit(str(self.config.sampleBufferLen))
        self.table = DataSeriesTable(self.config.protocol)

        grid = QGridLayout()
        grid.addWidget(QLabel("Console Name:"), 0, 0)
        grid.addWidget(self.consoleName, 0, 1)
        grid.addWidget(QLabel("Sample Buffer:"), 1, 0)
        grid.addWidget(self.sampleBuffer, 1, 1)
        grid.addWidget(self.table, 2, 0, 1, 2)
        self.setLayout(grid)


    def updateConfig(self):
        self.config.name = self.consoleName.text()
        self.config.sampleBufferLen = int(self.sampleBuffer.text())
        self.config.protocol = self.table.grabProtocol()

        



     
    
  