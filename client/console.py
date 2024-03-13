from PyQt6 import QtCore
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *

from core.zmqutils import ZmqBridgeQt

from logger import getmylogger

log = getmylogger(__name__)


class Console(QWidget):    
    def __init__(self, topic : str, parent=None):
        super(Console, self).__init__(parent)
        self.setGeometry(100,100,300,300)
        self.topic = topic
        self.setWindowTitle(topic)
        self.initUI()  

        self.zmqBridge = ZmqBridgeQt()

    def initUI(self):
        self.setMinimumWidth(300)
        # Create  Layout
        self.vBox = QVBoxLayout()
        self.vBox.setContentsMargins(5, 5, 5, 5)
        self.setLayout(self.vBox)

        self.consoleText = QTextEdit()
        self.consoleText.setReadOnly(True)
        self.consoleText.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.consoleText.setAcceptRichText(True)
        self.consoleText.setStyleSheet("background-color: black; color: green;")

        # Add Widgets to Layout
        self.vBox.addWidget(self.consoleText)


    def clearConsole(self):
        '''Clear Console'''
        self.consoleText.clear()

    @QtCore.pyqtSlot(tuple) 
    def _updateData(self, msg : tuple[str, str]):
        '''Update Console with new data'''
        if(msg[0] != self.topic): # filter on topic
            return
        if self.consoleText.document().lineCount() > 200:
            self.consoleText.clear()

        self.consoleText.append(msg[1]) # add data to console 


class CreateConsole(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("New Console")

        topicLabel = QLabel("Topic")
        self.consoleTopic = QLineEdit()
        form = QFormLayout()
        form.addRow(topicLabel, self.consoleTopic)

        QBtn = QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.validateInput)
        self.buttonBox.rejected.connect(self.reject)
        vBox = QVBoxLayout()
        vBox.addLayout(form)
        vBox.addWidget(self.buttonBox)
        self.setLayout(vBox)


    def validateInput(self):
        if self.consoleTopic.text() == "":
            errMsg = QMessageBox.critical(self, "Error", "All Fields are Mandatory")
            return
        self.accept()

    def getValues(self) -> str:
        try:
            topic = self.consoleTopic.text()
        except ValueError as e:
            log.error(f"Error in getValues {e}")

        return str(topic)

