import serial, serial.tools.list_ports

from core.device import TopicMap
from PyQt6 import QtCore
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QColor


def scanUSB( key: str) -> list:
    ports = [p.device for p in serial.tools.list_ports.comports() if key.lower() in p.device]
    return ports


class TopicMenu(QFrame):
    def __init__(self, pubMap : TopicMap):
        super().__init__()

        self.maxDataSeries = 8
        self.pubMap =  pubMap
        self.grid = QGridLayout()

        self.addSeriesBtn = QPushButton("Add Series")
        self.addSeriesBtn.clicked.connect(self.addSeries)
        self.yMin = QLineEdit("Min")
        self.yMin.setMaximumWidth(50)
        self.yMax = QLineEdit("Max")
        self.yMax.setMaximumWidth(50)

        self.removeSeriesBtn = QPushButton("Remove Series")

        self.topicCB = QComboBox()
        self.topicCB.addItems(self.pubMap.getTopicNames())
        self.topicCB.currentIndexChanged.connect(self.updateArgComboBox)

        self.argCb = QComboBox()
        self.updateArgComboBox()

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Topic Name", "Arg"])
        self.grid.addWidget(self.topicCB, 0 , 0, 1,1)                
        self.grid.addWidget(self.argCb, 0 , 1, 1,1)
        self.grid.addWidget(self.addSeriesBtn, 0 , 2, 1,1)
        self.grid.addWidget(self.yMin, 0, 3,  1, 1)
        self.grid.addWidget(self.yMax, 0 , 4, 1,1 )
        self.grid.addWidget(self.table, 1, 0, 3,5 )
        self.setLayout(self.grid)


    def updateArgComboBox(self):
        """Update argument combo box based on the selected topic."""
        topicName = self.topicCB.currentText()
        _, topicArgs = self.pubMap.getTopicFormat(topicName)
        self.argCb.clear()
        self.argCb.addItems(topicArgs)

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
                (self.table.item(row, 0).text()+"/"+self.table.item(row, 1).text())
                for row in range(self.table.rowCount())
            ]
        )
        return protocol