from PyQt6 import QtCore
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *

from client.zmqQtBridge import ZmqBridgeQt
from common.logger import getmylogger
from common.messages import TopicMap
from client.menus import TopicMenu

class ConsoleApp(QFrame):
    def __init__(self):
        super().__init__()
        self.log = getmylogger(__name__)
        self.maxConsoles = 4
        self.topicMap = None
        self.consoles = list()
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab_handle)

        self.clear_PB = QPushButton("Clear")
        self.clear_PB.clicked.connect(self.clear_handle)
        self.settings_PB = QPushButton("Console Settings")
        self.settings_PB.clicked.connect(self.settings_handle)
        self.new_console_PB = QPushButton("New Console")
        self.new_console_PB.clicked.connect(self.new_console_handle)

        grid = QGridLayout()
        self.setLayout(grid)
        grid.addWidget(self.tabs, 0,0, 2, 4)
        grid.addWidget(self.settings_PB, 4, 0, 1,1)
        grid.addWidget(self.clear_PB, 4,1, 1,1)
        grid.addWidget(self.new_console_PB, 4,2,1,1)

    def close(self):
        for console in self.consoles:
            console.close()
    
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

    def new_console_handle(self):
         if(self.tabs.count() <= self.maxConsoles):
            if(isinstance(self.topicMap, TopicMap)):
                diag = ConfigConsole(self.topicMap)
                if diag.exec() == True:
                    protocol = diag.topicMenu.saveProtocol()
                    console = Console()
                    console.config(topics=protocol, name="Console")
                    self.consoles.append(console)
                    self.tabs.addTab(console, console.name)
            else:
                self.log.error("No Valid TopicMap")

class Console(QWidget):
    """Widget representing a console for displaying messages."""

    def __init__(self):
        super().__init__()
        self.log = getmylogger(__name__)
        self.name = "Console"
        self.topics = tuple()
        self.initUI()
        self.zmqBridge = ZmqBridgeQt() 
        self.zmqBridge.msgSig.connect(self._updateData)
        self.zmqBridge.workerIO._begin()

    def close(self):
        self.log.debug(f"Closing Console {self.name}")
        self.zmqBridge.workerIO._stop()  # stop device thread

    def config(self, topics: tuple[str , ...], name : str):
        self.name = name
        self.topics = topics
        [self.zmqBridge.subscriber.addTopicSub(t) for t in self.topics]

    def initUI(self):
        """Initializes the user interface."""
        self.setMinimumWidth(300)
        # Create Layout
        self.vBox = QVBoxLayout()
        self.vBox.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.vBox)

        self.consoleText = QTextEdit()
        self.consoleText.setReadOnly(True)
        self.consoleText.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.consoleText.setAcceptRichText(True)
        self.consoleText.setStyleSheet("background-color: black; color: green;")
        self.vBox.addWidget(self.consoleText)

    def clear(self):
        """Clears the console."""
        self.consoleText.clear()

    @QtCore.pyqtSlot(tuple)
    def _updateData(self, msg: tuple[str, str]):
        """Updates the console with new data.
        Args:
            msg (tuple[str, str]): The message tuple containing topic and data.
        """
        topic, data = msg
        if(topic in self.topics):
            if(isinstance(self.consoleText.document, QTextEdit)):
                if self.consoleText.document().lineCount() > 200:
                    self.consoleText.clear()

            self.consoleText.append(topic +"    "+data)  # add data to console tab spaced


class ConfigConsole(QDialog):
    """Dialog for creating a new console."""

    def __init__(self,  topicMap: TopicMap ):
        """Constructor method for CreateConsole class."""
        super().__init__()

        self.log = getmylogger(__name__)

        self.setWindowTitle("New Console")

        self.topicMenu= TopicMenu(topicMap)
    
        QBtn = (
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        vBox = QVBoxLayout()
    
        vBox.addWidget(self.topicMenu)
        vBox.addWidget(self.buttonBox)
        self.setLayout(vBox)
