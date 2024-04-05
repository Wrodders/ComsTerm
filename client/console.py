from PyQt6 import QtCore
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *

from core.zmqutils import ZmqBridgeQt

from common.logger import getmylogger


class Console(QWidget):    
    def __init__(self, topic : str, parent=None):
        super(Console, self).__init__(parent)

        self.log = getmylogger(__name__)

        self.setGeometry(100,100,300,300)
        self.topic = topic
        self.setWindowTitle(topic)
        self.initUI()  
        self.log.debug(f"Opened Console {self.topic}")
        self.zmqBridge = ZmqBridgeQt()
        #self.zmqBridge.subscriber.addTopicSub(topic)
        self.zmqBridge.msgSig.connect(self._updateData)
        self.zmqBridge.workerIO._begin()
    
    def closeEvent(self, event):
        self.log.debug(f"Closing Console {self.topic}")
        self.zmqBridge.workerIO._stop() # stop device thread
        event.accept()
        

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
        topic, data = msg
        if(topic != self.topic): # filter on topic
            return
        if self.consoleText.document().lineCount() > 200:
            self.consoleText.clear()

        self.consoleText.append(data) # add data to console 


class CreateConsole(QDialog):
    def __init__(self):
        super().__init__()

        self.log = getmylogger(__name__)

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
            self.log.error(f"Error in getValues {e}")

        return str(topic)

