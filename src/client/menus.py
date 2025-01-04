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
        # Save current argument names of the table to a tuple protocol
        protocol = tuple()
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if(isinstance(item, QTableWidgetItem)):
                protocol += (item.text() + "/" + item.text(),)
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


