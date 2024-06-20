from PyQt6 import QtCore
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.animation as animation
plt.style.use('dark_background')

from core.zmqutils import ZmqBridgeQt
from core.logger import getmylogger
from core.device import DeviceType, TopicMap
from core.utils import Trie, scanTopics

from dataclasses import dataclass, field
from enum import Enum
import sys
from typing import Type, List, Dict

class PlotType(Enum):
    LINE = 0

@dataclass
class LinePlotInfo():
    plotType : PlotType = PlotType.LINE
    dataSeries : dict = field(default_factory=dict)
    xLen : int = 50 # Data Buffer Size 
    xSeries : list = field(default_factory=list)
    yRange : tuple[float, float] = (0, 1)
    lines : list =  field(default_factory=list)


class LinePlotUI(QWidget):
    """"""
    def __init__(self, plotInfo: LinePlotInfo):
        """Constructor method for LinePlotUI class."""
        super().__init__()  

        self.log = getmylogger(__name__)
    
        self.info = LinePlotInfo()
        self.zmqBridge = ZmqBridgeQt() 
        self.zmqBridge.msgSig.connect(self._updateData)
        self.zmqBridge.workerIO._begin()

        self.initUI()
        self.updatePlotInfo(plotInfo)
  
        self.connectSignals()

    def initUI(self):
        """Initializes Line Plot Graph"""


        self.settingsB = QPushButton("Plot Settings")
        self.cursorsB = QPushButton("Cursors")
        self.cursorsB.setCheckable(True)
        self.clearB = QPushButton("Clear")
        self.recordB = QPushButton("Start Record")
        self.recordB.setCheckable(True)
        self.filterB = QPushButton("Filters")


        self.setContentsMargins(0, 0, 0, 0)
        self.setMinimumSize(300, 300)

        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(1,1,1)
        self.ax.grid(linestyle='dashed', linewidth=0.5)
        
        self.canvas = FigureCanvas(self.fig)
    

        self.grid = QGridLayout()
        self.grid.addWidget(self.settingsB, 0, 0)
        self.grid.addWidget(self.cursorsB, 0, 1)
        self.grid.addWidget(self.clearB, 0, 2)
        self.grid.addWidget(self.recordB, 0, 3)
        self.grid.addWidget(self.filterB, 0, 4)
        self.grid.addWidget(self.canvas, 1, 0, 5, 5)
        self.setLayout(self.grid)


    def connectSignals(self):
        """Connects signals to slots."""
        pass

    def updatePlotInfo(self, plotInfo: LinePlotInfo):
        """Resets and Updates plot configuration"""
        self.info = plotInfo
        self.info.lines = []
        for (name, data) in self.info.dataSeries.items():
            line, = self.ax.plot(self.info.xSeries, data, label= name )  # create a line on the plot
            self.info.lines.append(line)

        self.ax.set_ylim(self.info.yRange)
        # matplotlib timer animation
        self.animation = animation.FuncAnimation(self.fig, self.animate, fargs=(self.info.lines,), 
                                                interval=200, blit=False, cache_frame_data=False)
        
        self.ax.legend(loc=1)

        [self.zmqBridge.subscriber.addTopicSub(t) for t in self.info.dataSeries.keys()]
       
    def animate(self, i, lines):
        # Update the plot with new data
        for line, (key, value) in zip(lines, (self.info.dataSeries.items())):
            line.set_ydata(value[-self.info.xLen:])                    # Update lines with new Y values
        return lines
    

    @QtCore.pyqtSlot(tuple)
    def _updateData(self, msg: tuple[str, str]):
       # Grabs msg data from the worker thread
        topic, data = msg
        try:
            self.info.dataSeries[topic].append(float(data))   
        except Exception as e:
           self.log.error(f"Exception in UpdateData:{e}")
           pass

    def closeEvent(self, event):
        self.log.debug(f"Closing Line Plot")
        self.zmqBridge.workerIO._stop()  # stop thread
        event.accept()
  
class PlotConfigMenu(QDialog):

    def __init__(self, ):
        super().__init__()
        self.maxDataSeries = 8
        self.pubMap = scanTopics()
        self.plotInfo = LinePlotInfo()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Plot Configuration")
        self.grid = QGridLayout()

        plotTypeLabel = QLabel("Plot Type:")
        self.plotTypeCB = QComboBox()
        self.plotTypeCB.addItems(PlotType._member_names_)


        self.topicCB = QComboBox()
        self.topicCB.addItems(self.pubMap.getTopicNames())
        self.topicCB.currentIndexChanged.connect(self.updateArgComboBox)
        self.argCb = QComboBox()
        self.argCb.addItem("*")
        self.updateArgComboBox()

        self.addSeriesBtn = QPushButton("Add Data Series")
        self.addSeriesBtn.clicked.connect(self.addDataSeries)
        self.yMin = QLineEdit("Min")
        self.yMin.setMaximumWidth(100)
        self.yMax = QLineEdit("Max")
        self.yMax.setMaximumWidth(100)

        self.table = QTableWidget()
        self.table.setColumnCount(1)
        self.table.setHorizontalHeaderLabels(["Data Series Path"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        self.scanTopicsBtn = QPushButton("Scan")
        self.scanTopicsBtn.setMaximumWidth(100)
        self.scanTopicsBtn.clicked.connect(self.handelScan)
        # Dialog 
        QBtn = (  QDialogButtonBox.StandardButton.Ok
                | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.verifyEntry)
        self.buttonBox.rejected.connect(self.reject)
        
        self.grid.addWidget(plotTypeLabel, 0, 0, 1, 1)
        self.grid.addWidget(self.plotTypeCB, 0, 1, 1, 2)

        self.grid.addWidget(self.topicCB, 1, 0, 1, 1)
        self.grid.addWidget(self.argCb, 1, 1, 1, 1)
        self.grid.addWidget(self.addSeriesBtn, 1, 2, 1, 1)

        self.grid.addWidget(self.table, 2, 0, 4, 3)

        self.grid.addWidget(self.yMin, 6, 0, 1, 1)
        self.grid.addWidget(self.yMax, 6, 2, 1, 1)

        self.grid.addWidget(self.scanTopicsBtn, 7, 0, 1, 1)
        self.grid.addWidget(self.buttonBox, 7, 1, 1, 2)

        self.setLayout(self.grid)

    def verifyEntry(self):
        try:
            float(self.yMin.text())
            float(self.yMax.text())
            self.accept()
        except ValueError:
            err = QMessageBox.critical(self, "Error", "NaN Entry")


    def updateArgComboBox(self):
        """Update argument combo box based on the selected topic."""
        topicName = self.topicCB.currentText()
        _, topicArgs = self.pubMap.getTopicFormat(topicName)
        self.argCb.clear()
        self.argCb.addItems(topicArgs)
        

    def addDataSeries(self):
        """Add selected data series to the table."""
        topicName = self.topicCB.currentText()
        dataArgName = self.argCb.currentText()
        seriesPath = f"{topicName}/{dataArgName}"

        if(seriesPath not in self.plotInfo.dataSeries.keys()): 
            if self.table.rowCount() < self.maxDataSeries:
                self.plotInfo.dataSeries[seriesPath] = [0] * self.plotInfo.xLen
                rowPosition = self.table.rowCount()
                self.table.insertRow(rowPosition)
                self.table.setItem(rowPosition, 0, QTableWidgetItem(seriesPath))

    def handelScan(self):
        pass
          

    def grabTopicNames(self) -> List[str]:
        topicNames = [f"{self.table.item(row, 0).text()}"for row in range(self.table.rowCount())]
        return topicNames
    

    def getConfigValues(self) -> LinePlotInfo:
        match self.plotTypeCB.currentText():
            case PlotType.LINE.name:
                info = LinePlotInfo()
                info.plotType = PlotType.LINE
                info.yRange = (float(self.yMin.text()), 
                               float(self.yMax.text()))
                info.xLen = 100
                info.xSeries = list(range(0, info.xLen)) # time series (x-axis)
                for topic in self.grabTopicNames():
                    info.dataSeries[topic] = [0]*info.xLen
                return info
            case _:
                raise NotImplementedError()
            
class PlotterGUI(QMainWindow):
    """UI"""
    def __init__(self):
        super().__init__()
        self.log = getmylogger(__name__)
        self.windows = list()
        self.initUI()
        self.newPlotAsWindow() 

    def initUI(self):
        menubar = self.menuBar()
        if(isinstance(menubar, QMenuBar)):
            toolsMenu = menubar.addMenu('Tools')
            viewMenu = menubar.addMenu('View')

        newTabPlotAction = QAction('New Tab Plot', self)
        newWindowPlotAction = QAction('New Window Plot', self)

        newWindowPlotAction.triggered.connect(self.newPlotAsWindow)
        newTabPlotAction.triggered.connect(self.newPlotAsTab)
        if(isinstance(toolsMenu, QMenuBar)):
            toolsMenu.addAction(newTabPlotAction)
            toolsMenu.addAction(newWindowPlotAction)

        self.tabWidget = QTabWidget()
        self.setCentralWidget(self.tabWidget)
        self.tabWidget.setTabsClosable(True)
        self.tabWidget.tabCloseRequested.connect(self.removeTab)

        self.setWindowTitle('Plotter GUI')
        self.show()

    def newPlotAsTab(self):
        diag = PlotConfigMenu()
        if diag.exec() == True:
            info = diag.getConfigValues()
            plot = self.newPlot(info)
            self.tabWidget.addTab(plot, info.plotType.name)

    def newPlotAsWindow(self):
        dialog = PlotConfigMenu()
        if dialog.exec() == True:
            info = dialog.getConfigValues()
            plot = self.newPlot(info)
            self.windows.append(plot)
            if(len(self.windows) == 1):
                self.setCentralWidget(plot)
            else:
                plot.show()
            
    def newPlot(self, info: LinePlotInfo) -> LinePlotUI:
        if(isinstance(info, LinePlotInfo)):
                plot = LinePlotUI(info)
        return plot
            
    def removeTab(self, index):
        widget = self.tabWidget.widget(index)
        self.tabWidget.removeTab(index)
        if(isinstance(widget, QWidget)):
            widget.deleteLater()


    def closeEvent(self, event):
        self.log.debug(f"Closing Plot GUI")
        for window in self.windows:
            window.close()
