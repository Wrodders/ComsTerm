from PyQt6 import QtCore
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *

from common.utils import scanUSB

from core.device import Devices, DeviceInfo
from core.SerialDevice import SerialInfo
from core.SimulatedDevice import SimInfo
from core.ZmqDevice import ZmqInfo
from common.zmqutils import Transport, Endpoint


class TopicSeriesMenue(QFrame):
    def __init__(self, pubMap):
        super().__init__()
        self.maxDataSeries = 8
        self.pubMap = pubMap
        self.grid = QGridLayout()

        self.addSeriesBtn = QPushButton("Add Series")
        self.addSeriesBtn.clicked.connect(self.addSeries)
        self.removeSeriesBtn = QPushButton("Remove Series")

        self.topicCB = QComboBox()
        self.topicCB.addItems(self.pubMap.getTopicNames())
        self.topicCB.currentIndexChanged.connect(self.updateArgComboBox)

        self.argCb = QComboBox()
        self.updateArgComboBox()

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Topic Name", "Arg"])

        self.grid.addWidget(QLabel("Topic Name:"), 0, 0)
        self.grid.addWidget(self.topicCB, 0, 1)
        self.grid.addWidget(QLabel("Argument:"), 1, 0)
        self.grid.addWidget(self.argCb, 1, 1)
        self.grid.addWidget(self.addSeriesBtn, 2, 0, 1, 2)
        self.grid.addWidget(self.table, 3, 0, 1, 2)
        self.setLayout(self.grid)


    def updateArgComboBox(self):
        """Update argument combo box based on the selected topic."""
        topicName = self.topicCB.currentText()
        _, topicArgs = self.pubMap.getTopicFormat(topicName)
        self.argCb.clear()
        self.argCb.addItems(topicArgs)

    def loadProtocol(self, protocol: tuple[str, ...]):
        """Load protocol data into the table."""
        self.table.setRowCount(0) # Clear the table
        for row, series in enumerate(protocol):
            topicName, argName = series.split("/")
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(topicName))
            self.table.setItem(row, 1, QTableWidgetItem(argName))

    def addSeries(self):
        """Add selected data series to the table."""
        topicName = self.topicCB.currentText()
        argName = self.argCb.currentText()
        if self.table.rowCount() < self.maxDataSeries:
            rowPosition = self.table.rowCount()
            self.table.insertRow(rowPosition)
            self.table.setItem(rowPosition, 0, QTableWidgetItem(topicName))
            self.table.setItem(rowPosition, 1, QTableWidgetItem(argName))

    def saveProtocol(self) -> tuple[str, ...]:
        """Save current argument names of the table to a tuple called protocol."""
        protocol = tuple(
            [
                (self.table.item(row, 0).text() + "/" + self.table.item(row, 1).text())
                for row in range(self.table.rowCount())
            ]
        )
        return protocol



