from PyQt6 import QtCore
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QTextCursor

from core.zmqutils import ZmqBridgeQt

from common.logger import getmylogger
from common.messages import TopicMap
from common.utils import TopicMenu


class Console(QWidget):
    """Widget representing a console for displaying messages."""

    def __init__(self, topics: tuple[str , ...], parent=None):
        """Constructor method for Console class.

        Args:
            topic (str): The topic of the console.
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super(Console, self).__init__(parent)

        self.log = getmylogger(__name__)

        self.setGeometry(100, 100, 300, 300)
        self.topics = topics
        self.setWindowTitle("console")
        self.initUI()
        self.log.debug(f"Opened Console {topics}")
        self.zmqBridge = ZmqBridgeQt() 
        
        self.zmqBridge.msgSig.connect(self._updateData)
        self.zmqBridge.workerIO._begin()
        print(topics)
        [self.zmqBridge.subscriber.addTopicSub(t) for t in topics]

    def closeEvent(self, event):
        """Event handler for closing the console.

        Args:
            event (QCloseEvent): The close event.
        """
        self.log.debug(f"Closing Console {self.topics}")
        self.zmqBridge.workerIO._stop()  # stop device thread
        event.accept()

    def initUI(self):
        """Initializes the user interface."""
        self.setMinimumWidth(300)
        # Create Layout
        self.vBox = QVBoxLayout()
        self.vBox.setContentsMargins(5, 5, 5, 5)
        self.setLayout(self.vBox)

        self.configBtn = QPushButton("Settings")
        self.configBtn.setMaximumWidth(300)

        self.consoleText = QTextEdit()
        self.consoleText.setReadOnly(True)
        self.consoleText.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.consoleText.setAcceptRichText(True)
        self.consoleText.setStyleSheet("background-color: black; color: green;")

        # Add Widgets to Layout
        self.vBox.addWidget(self.consoleText)
        self.vBox.addWidget(self.configBtn)

    def clearConsole(self):
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
            if self.consoleText.document().lineCount() > 200:
                self.consoleText.clear()

            self.consoleText.append(topic +"    "+data)  # add data to console


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


    def getValues(self) -> tuple[str, ...]:
        """Returns the value entered in the console topic field.

        Returns:
            str: The topic entered in the console topic field.
        """
        try:
            topic = self.consoleTopic.currentText()
            print(topic)
        except ValueError as e:
            self.log.error(f"Error in getValues {e}")

        return 
