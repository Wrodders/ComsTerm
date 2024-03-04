from PyQt6 import QtCore
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen

from logger import getmylogger

log = getmylogger(__name__)


class Console(QWidget):    
    def __init__(self, topic : str):
        super().__init__()
        self.topic = topic
        self.initUI()   

    def initUI(self):
        self.setMinimumWidth(300)
        # Create  Layout
        self.vBox = QVBoxLayout()
        self.vBox.setContentsMargins(5, 5, 5, 5)
        self.setLayout(self.vBox)

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.console.setAcceptRichText(True)
        self.console.setStyleSheet("background-color: black; color: green;")

        # Add Widgets to Layout
        self.vBox.addWidget(self.console)

    def clearConsole(self):
        '''Clear Console'''
        self.console.clear()

    @QtCore.pyqtSlot(tuple) 
    def _updateData(self, msg : tuple[str, str]):
        '''Update Console with new data'''
        if(msg[0] != self.topic): # filter on topic
            return
        if self.console.document().lineCount() > 200:
            self.console.clear()

        self.console.append(msg[1]) # add data to console 



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
        if isinstance(self.consoleTopic, QLineEdit):
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


class CommandFrame(QFrame):
    cmdSendSig = QtCore.pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.setContentsMargins(0,0,0,0)
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.console.setAcceptRichText(True)
        self.console.setStyleSheet("background-color: black; color: grey;")

        self.cmdEntry = QLineEdit()
        self.cmdEntry.setMinimumWidth(100)
        self.cmdEntry.textChanged.connect(self.enableSend)
        self.sendB = QPushButton("Send")
        self.sendB.setMaximumWidth(100)

        self.grid = QGridLayout()
        self.grid.addWidget(self.console, 0, 0, 2, 2)
        self.grid.addWidget(self.cmdEntry,2,0 )
        self.grid.addWidget(self.sendB, 2,1)
        self.setLayout(self.grid)

    @QtCore.pyqtSlot(str)
    def _updateData(self, msg : str):
        '''Update Console with new data'''
        if msg == "":
            return
        if self.console.document().lineCount() > 200:
            self.console.clear()

        self.console.append(msg) # add data to console 

    def enableSend(self):
        '''Stops Spamming Send'''
        if self.cmdEntry.text():
            self.sendB.setEnabled(True)
        else: 
            self.sendB.setEnabled(False)


           