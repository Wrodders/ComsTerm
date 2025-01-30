from PyQt6 import QtCore
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *

from common.utils import scanUSB

from core.device import Devices, DeviceInfo
from core.SerialDevice import SerialInfo
from core.SimulatedDevice import SimInfo
from core.ZmqDevice import ZmqInfo
from common.zmqutils import Transport, Endpoint
from common.messages import TopicMap, ParameterMap

from PyQt6.QtWidgets import QProgressBar
from PyQt6.QtCore import QTimer, pyqtSignal

class ProgressBar(QProgressBar):
    """ Custom progress bar with a configurable timeout. """
    timeoutSig = pyqtSignal()  

    def __init__(self, timeout: int = 500):  
        """
        :param timeout: Total duration in milliseconds for the progress bar to complete.
        """
        super().__init__()

        self.timeout = timeout  # Total time in ms
        self.update_interval = 100  # Update every 10ms
        self.increment = max(1, int(100 / (self.timeout / self.update_interval)))  

        self.timer = QTimer()
        self.timer.timeout.connect(self.updateBar)

        self.setValue(0)
        self.setMaximum(100)

    def start(self):
        """ Starts the progress bar animation and timeout. """
        self.setValue(0)
        self.timer.start(self.update_interval)

    def updateBar(self):
        """ Updates the progress bar value. """
        if self.value() < 100:
            self.setValue(self.value() + self.increment)
        else:
            self.timer.stop()
            self.timeoutSig.emit()  # Emit signal when done
            self.setValue(0)  # Reset for future use


    


class SettingsUI(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
    def updateConfig(self):
        raise NotImplementedError
    
class FileExplorer(QWidget):
    def __init__(self, name: str):
        super().__init__()
        self.nameLabel = QLabel(name)  
        self.fileEntry = QLineEdit()
        self.browserButton = QPushButton("Browse")
        self.browserButton.clicked.connect(self.browse)

        layout = QGridLayout()  
        layout.addWidget(self.nameLabel, 0, 0, 1,2)
        layout.addWidget(self.fileEntry, 1, 1)
        layout.addWidget(self.browserButton, 1, 2)
        self.setLayout(layout)

    def browse(self):
        fileDialog = QFileDialog()
        fileDialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        fileDialog.setNameFilter("Config Files (*.json)")
        if fileDialog.exec():
            fileNames = fileDialog.selectedFiles()
            self.fileEntry.setText(fileNames[0])

class DataSeriesTableSettings(QFrame):
    def __init__(self, pubMap : TopicMap):
        super().__init__()
        self.pubMap = pubMap
        self.grid = QGridLayout()
        self.topicCB = QComboBox()
        self.topicCB.addItems(self.pubMap.getTopicNames())
        self.topicCB.currentIndexChanged.connect(self.updateArgComboBox)
        self.addSeriesBtn = QPushButton("Add Series")
        self.removeSeriesBtn = QPushButton("Remove Series")
        self.argCb = QComboBox()
        self.updateArgComboBox() 
        #Layout
        self.grid.addWidget(QLabel("Topic Name:"), 0, 0)
        self.grid.addWidget(self.topicCB, 1, 0)
        self.grid.addWidget(QLabel("Argument:"), 0, 1)
        self.grid.addWidget(self.argCb, 1, 1)
        self.grid.addWidget(self.addSeriesBtn, 2, 0)
        self.grid.addWidget(self.removeSeriesBtn, 2,1)
        self.setLayout(self.grid)

    def updateArgComboBox(self):
        """Update argument combo box based on the selected topic."""
        topicName = self.topicCB.currentText()
        _, topicArgs = self.pubMap.getTopicFormat(topicName)
        self.argCb.clear()
        self.argCb.addItems(topicArgs)

    def grabSeries(self) -> tuple[str, str]:
        return (self.topicCB.currentText(), self.argCb.currentText())

class DataSeriesTable(QFrame):
    def __init__(self, protocol: tuple[str, ...]):
        super().__init__()
        self.initUI()
        self.loadProtocol(protocol) # Load protocol into the table

    def initUI(self):
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Topic Name", "Arg"])
        layout = QVBoxLayout()
        layout.addWidget(self.table)
        self.setLayout(layout)

    def grabProtocol(self) -> tuple[str, ...]:
        # Grab protocol from Table, return as a tuple of rows
        # separate collums with a "/"
        protocol = tuple()
        for row in range(self.table.rowCount()):
            topic = self.table.item(row, 0).text()
            arg = self.table.item(row, 1).text()
            protocol += (topic + "/" + arg,)  
        return protocol
    
    def loadProtocol(self, protocol: tuple[str, ...]):
        # Load protocol into the table
        for row, series in enumerate(protocol):
            topic, arg = series.split("/")
            self.table.setItem(row, 0, QTableWidgetItem(topic))
            self.table.setItem(row, 1, QTableWidgetItem(arg))
    
    def addSeries(self, series: tuple[str, str]):
        # Add selected data series to the table
        topicName, argName = series
        rowPosition = self.table.rowCount()
        self.table.insertRow(rowPosition)
        self.table.setItem(rowPosition, 0, QTableWidgetItem(topicName))
        self.table.setItem(rowPosition, 1, QTableWidgetItem(argName))

    def removeSeries(self):
        row = self.table.currentRow()
        self.table.removeRow(row)


