from PyQt6 import QtCore
from PyQt6.QtCore import Qt, pyqtSlot, QThread, QTimer
from PyQt6.QtWidgets import QFrame, QTabWidget, QGridLayout, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, QListWidget, QStackedLayout, QDialog, QDialogButtonBox, QListWidgetItem
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.animation as animation

from client.zmqQtBridge import ZmqBridgeQt
from client.menus import DataSeriesTable, DataSeriesTableSettings, SettingsUI

from common.logger import getmylogger
from common.config import LinePlotCfg, ScatterPlotCfg, BarPlotCfg
from common.config import PlotCfg, PlotAppCfg, PlotTypeMap

from common.zmqutils import ZmqPub, ZmqSub, Endpoint, Transport

import numpy as np

from common.messages import TopicMap

from common.utils import check_darkmode

if(check_darkmode()):
    plt.style.use('dark_background')
else:
    plt.style.use('bmh')


""" ----------------- Plot App ----------------- """
class PlotApp(QFrame):
    def __init__(self, config: PlotAppCfg, topicMap):
        super().__init__()
        self.log = getmylogger(__name__)
        self.setWindowTitle("Plot App")
        self.topicMap = topicMap
        self.config = config
        self.plots = list()  # List of plot instances
        self.initUI()
        
        for plotCfg in self.config.plotConfigs:
            self.newPlot(plotCfg) 

    def closeEvent(self, event):
        for plot in self.plots:
            plot.close()
        self.log.info("Closing Plot App")
        event.accept()


    def initUI(self):
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_plt_handle)
        self.tabs.setTabPosition(QTabWidget.TabPosition.South)
        self.grid = QGridLayout()
        self.grid.addWidget(self.tabs, 1, 0, 4, 4)
        self.setLayout(self.grid)

    def newPlot(self, plotCfg: PlotCfg):
        if plotCfg.plotType == "LINE":
            plot = LinePlot(topicMap=self.topicMap, config=plotCfg,
                            transport=Transport.TCP, endpoint=Endpoint.BOT_MSG)
        else:
            raise NotImplementedError("Plot Type not implemented")

        self.plots.append(plot)      
        self.tabs.addTab(plot, plot.config.name)

    def close_plt_handle(self, index):
        pass  # Callback for closing a plot

class BasePlot(QFrame):
    """Base class for plotting."""
    def __init__(self, topicMap, transport: Transport, endpoint: Endpoint):
        super().__init__()
        self.config = PlotCfg()
        self.log = getmylogger(__name__)
        self.zmqBridge = ZmqBridgeQt(topicMap=topicMap, transport=transport, endpoint=endpoint)
        self.zmqBridge.msgSig.connect(self._updateData)

    @QtCore.pyqtSlot(tuple)
    def _updateData(self, msg: tuple[str, str]):
        raise NotImplementedError("Subclasses must implement updateData method")
    
    def close(self):
        self.log.debug(f"Closing Plot {self.config.name}")
        self.zmqBridge.workerIO._stop()  # Stop the device thread

class LinePlot(BasePlot):
    """Class for line plotting."""
    def __init__(self, topicMap, config: PlotCfg, transport: Transport, endpoint: Endpoint):
        super().__init__(topicMap=topicMap, transport=transport, endpoint=endpoint)
        if isinstance(config.typeCfg, LinePlotCfg):
            self.config = config

        self.dataSet = dict()
        self.lines = list()
        self.initUI()
        self.zmqBridge.registerSubscriptions(self.config.protocol)
        self.zmqBridge.workerIO._begin()
        self.anim = None
        self.setupPlot()

    def setupPlot(self):
        # Set initial x-data based on the configured sample buffer length
        self.xs = list(range(0, self.config.sampleBufferLen))
        if isinstance(self.config.typeCfg, LinePlotCfg):
            self.ax.set_ylim(self.config.typeCfg.yrange)

            # Enable minor ticks and set thinner grid lines
            self.ax.minorticks_on()
            self.ax.grid(which='major', linestyle='--', linewidth=0.5)
            self.ax.grid(which='minor', linestyle=':', linewidth=0.3)

            for label in self.config.protocol:
                if label not in self.dataSet:
                    # Start with an empty data list
                    self.dataSet[label] = []
                    line, = self.ax.plot([], [], label=label, linewidth=0.75)
                    self.lines.append(line)
            self.ax.legend(loc=1)
            self.ax.tick_params(axis="both", which="both")
            self.ax.set_xlabel("Sample")
            self.anim = self.animation = animation.FuncAnimation(
                self.fig, self.animate, fargs=(self.lines,),
                interval=200, blit=False, cache_frame_data=False
            )

    def initUI(self):
        """Initializes the plot UI."""
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(1, 1, 1)
        self.ax.grid(linestyle='dashed', linewidth=0.5)
        self.canvas = FigureCanvas(self.fig)
        layout = QGridLayout()
        layout.addWidget(self.canvas, 0, 0, 5, 5)
        self.setLayout(layout)
        self.setContentsMargins(0, 0, 0, 0)
      
    @QtCore.pyqtSlot(tuple)
    def _updateData(self, msg: tuple[tuple, str]):
        topic, data = msg
        try:
            # Append new data to the list for this topic
            self.dataSet[topic].append(float(data))
        except Exception as e:
            self.log.error(f"Exception in UpdateData: {e}")
       
    def animate(self, i, lines):
        # Update each line with new data while supporting variable-length arrays.
        for line, (key, value) in zip(lines, self.dataSet.items()):
            # If there are more points than the buffer, show only the last N points;
            # otherwise, display all points.
            display_data = value[-self.config.sampleBufferLen:] if len(value) > self.config.sampleBufferLen else value
            new_x = list(range(len(display_data)))
            line.set_data(new_x, display_data)
        self.ax.relim()
        self.ax.autoscale_view()
        return lines
    
    def drawLineOnPlot(self, label: str, data: np.ndarray):
        """Directly update the plot with a new complete dataset for the given label."""
        new_data = data.tolist() if isinstance(data, np.ndarray) else data
        new_x = list(range(len(new_data)))
        if label in self.dataSet and any(line.get_label() == label for line in self.lines):
            self.dataSet[label] = new_data
            for line in self.lines:
                if line.get_label() == label:
                    line.set_data(new_x, new_data)
                    break
        else:
            self.dataSet[label] = new_data
            line, = self.ax.plot(new_x, new_data, label=label)
            self.lines.append(line)
            
        self.ax.relim()
        self.ax.autoscale_view()
        self.ax.legend(loc=1)
        self.canvas.draw_idle() # Update the plot with the new data

    def clearData(self, label: str):
        """Clear the data for the specified label."""
        if label in self.dataSet:
            self.dataSet[label] = []
            for line in self.lines:
                if line.get_label() == label:
                    line.set_data([], [])
                    break
            self.canvas.draw_idle()
""" ----------------- Plot App Settings ----------------- """
class PlotAppSettings(SettingsUI):
    def __init__(self, config: PlotAppCfg, topicMap: TopicMap):
        super().__init__()
        self.setWindowTitle("Plot Settings")
        self.topicMap = topicMap
        self.config = config  # Populate UI with current config
        self.initUI()
        
    def initUI(self):
        self.dataSeriesConfig = DataSeriesTableSettings(self.topicMap)
        self.plotList = QListWidget()
        # Create a stack layout for the plot configurations
        self.plotConfigStack = QStackedLayout()   
        if isinstance(self.config, PlotAppCfg):   
            for idx in range(len(self.config.plotConfigs)):
                self.createPlotCfg(self.config.plotConfigs[idx]) 
            self.plotList.currentRowChanged.connect(self.plotConfigStack.setCurrentIndex)
            self.addPlot_PB = QPushButton("+")
            self.addPlot_PB.clicked.connect(lambda: self.addPlot_handle(PlotCfg()))
            self.removePlot_PB = QPushButton("-")
            self.removePlot_PB.clicked.connect(lambda: self.removePlot_handle(self.plotList.currentRow()))
        
            self.dataSeriesConfig.addSeriesBtn.clicked.connect(
                lambda:  self.plotConfigStack.currentWidget().table.addSeries(self.dataSeriesConfig.grabSeries()))
            self.dataSeriesConfig.removeSeriesBtn.clicked.connect(
                lambda:  self.plotConfigStack.currentWidget().table.removeSeries())
            grid = QGridLayout()
            grid.addWidget(self.addPlot_PB, 0, 0)
            grid.addWidget(self.removePlot_PB, 1, 0)
            grid.addWidget(self.plotList, 0, 1, 2, 2)

            hBox = QHBoxLayout()
            hBox.addWidget(self.dataSeriesConfig)
            hBox.addLayout(grid)

            vBox = QVBoxLayout()
            vBox.addLayout(hBox)
            vBox.addLayout(self.plotConfigStack)
            self.setLayout(vBox)

    def createPlotCfg(self, plotCfg: PlotCfg):
        new_plotSettings = PlotSettings(plotCfg)
        self.plotList.addItem(new_plotSettings.plotName.text())
        self.plotList.setCurrentRow(self.plotList.count()-1)
        listWidget = self.plotList.currentItem()
        if isinstance(listWidget, QListWidgetItem):
            new_plotSettings.plotName.textChanged.connect(
                lambda: listWidget.setText(new_plotSettings.plotName.text()))
            self.plotConfigStack.addWidget(new_plotSettings)
            self.plotConfigStack.setCurrentIndex(self.plotList.count()-1)

    def updateConfig(self):
        for i in range(self.plotList.count()):
            stackWidget = self.plotConfigStack.widget(i)
            if isinstance(stackWidget, PlotSettings):
                stackWidget.updateConfig()
                self.config.plotConfigs[i] = stackWidget.config

    def addPlot_handle(self, plotCfg: PlotCfg):
        self.config.plotConfigs.append(plotCfg)
        self.createPlotCfg(plotCfg)
        
    def removePlot_handle(self, index):
        self.plotConfigStack.removeWidget(self.plotConfigStack.widget(index))
        self.config.plotConfigs.pop(index)
        self.plotList.takeItem(index)

    def load_handle(self, fp):
        for idx in range(self.plotList.count()):
            self.removePlot_handle(idx)
        self.config.load(fp)
        for idx in range(len(self.config.plotConfigs)):
            self.addPlot_handle(self.config.plotConfigs[idx])

class PlotSettings(SettingsUI):
    def __init__(self, plotCfg: PlotCfg):
        super().__init__()
        self.log = getmylogger(__name__)
        self.config = plotCfg
        self.initUI()
    
    def initUI(self):
        self.plotName = QLineEdit(self.config.name)
        self.plotType = QComboBox()
        self.plotType.addItems(PlotTypeMap.keys())
        if self.config.plotType in PlotTypeMap.keys():
            self.plotType.setCurrentText(self.config.plotType)
        self.maxSeries = QLineEdit(str(self.config.maxPlotSeries))
        self.maxSeries.setMaximumWidth(50)
        self.sampleBuffer = QLineEdit(str(self.config.sampleBufferLen))
        self.sampleBuffer.setMaximumWidth(50)
        self.linePlotSettings = LinePlotSettings(LinePlotCfg())
        self.scatterPlotSettings = ScatterPlotSettings(ScatterPlotCfg())
        self.barPlotSettings = BarPlotSettings(BarPlotCfg())        
        self.plotCfgStack = QStackedLayout()
        self.plotCfgStack.addWidget(self.linePlotSettings)
        self.plotCfgStack.addWidget(self.scatterPlotSettings)
        self.plotCfgStack.addWidget(self.barPlotSettings)
        self.plotType.currentIndexChanged.connect(self.plotCfgStack.setCurrentIndex)
        self.table = DataSeriesTable()
        self.table.loadSubscriptions(self.config.protocol)
        grid = QGridLayout()
        grid.addWidget(QLabel("Plot Name"), 0, 0)
        grid.addWidget(self.plotName, 0, 1)
        grid.addWidget(QLabel("Plot Type"), 0, 2)
        grid.addWidget(self.plotType, 0, 3)
        grid.addWidget(QLabel("Max # Series"), 1, 0)
        grid.addWidget(self.maxSeries, 1, 1)
        grid.addWidget(QLabel("Sample Buffer"), 1, 2)
        grid.addWidget(self.sampleBuffer, 1, 3)
        grid.addLayout(self.plotCfgStack, 2, 0, 1, 4)

        hBox = QHBoxLayout()
        hBox.addWidget(self.table)
        hBox.addLayout(grid)
        self.setLayout(hBox)

    def updateConfig(self):
        self.config.name = self.plotName.text()
        self.config.plotType = self.plotType.currentText()
        self.config.maxPlotSeries = int(self.maxSeries.text())
        self.config.sampleBufferLen = int(self.sampleBuffer.text())
        self.config.protocol = self.table.grabSubscriptions()
        stackWidget = self.plotCfgStack.currentWidget()
        if isinstance(stackWidget, LinePlotSettings):
            stackWidget.updateConfig()
            self.config.typeCfg = stackWidget.config

class LinePlotSettings(SettingsUI):
    def __init__(self, config: LinePlotCfg):
        super().__init__()
        self.config = config
        self.initUI()
    def initUI(self):
        self.yMin = QLineEdit(str(self.config.yrange[0]))
        self.yMax = QLineEdit(str(self.config.yrange[1]))
        self.yMin.setMaximumWidth(50)
        self.yMax.setMaximumWidth(50)
        self.grid = QGridLayout()
        self.grid.addWidget(QLabel("Y Min"), 0, 0)
        self.grid.addWidget(self.yMin, 0, 1)
        self.grid.addWidget(QLabel("Y Max"), 0, 2)
        self.grid.addWidget(self.yMax, 0, 3)
        self.setLayout(self.grid)

    def updateConfig(self):
        self.config.yrange = (float(self.yMin.text()), float(self.yMax.text()))

class ScatterPlotSettings(SettingsUI):
    def __init__(self, config: ScatterPlotCfg):
        super().__init__()
        self.config = config
        self.initUI()
    def initUI(self):
        self.yMin = QLineEdit(str(self.config.yrange[0]))
        self.yMax = QLineEdit(str(self.config.yrange[1]))
        self.xMin = QLineEdit(str(self.config.xrange[0]))
        self.xMax = QLineEdit(str(self.config.xrange[1]))
        self.yMin.setMaximumWidth(50)
        self.yMax.setMaximumWidth(50)
        self.xMin.setMaximumWidth(50)
        self.xMax.setMaximumWidth(50)
        self.marker = QComboBox()
        self.marker.addItems(["o", "x", "s", "d"])
        self.grid = QGridLayout()
        self.grid.addWidget(QLabel("Y Min"), 0, 0)
        self.grid.addWidget(self.yMin, 0, 1)
        self.grid.addWidget(QLabel("Y Max"), 0, 2)
        self.grid.addWidget(self.yMax, 0, 3)
        self.grid.addWidget(QLabel("X Min"), 1, 0)
        self.grid.addWidget(self.xMin, 1, 1)
        self.grid.addWidget(QLabel("X Max"), 1, 2)
        self.grid.addWidget(self.xMax, 1, 3)
        self.grid.addWidget(QLabel("Marker"), 2, 0)
        self.grid.addWidget(self.marker, 2, 1)
        self.setLayout(self.grid)

    def updateConfig(self):
        self.config.yrange = (float(self.yMin.text()), float(self.yMax.text()))
        self.config.xrange = (float(self.xMin.text()), float(self.xMax.text()))
        self.config.marker = self.marker.currentText()

class BarPlotSettings(SettingsUI):
    def __init__(self, config: BarPlotCfg):
        super().__init__()
        self.config = config
        self.initUI()
    def initUI(self):
        self.ylim = QLineEdit(str(self.config.ylim))
        self.barWidth = QLineEdit(str(self.config.barWidth))
        self.ylim.setMaximumWidth(50)
        self.barWidth.setMaximumWidth(50)
        self.grid = QGridLayout()
        self.grid.addWidget(QLabel("Y Limit"), 0, 0)
        self.grid.addWidget(self.ylim, 0, 1)
        self.grid.addWidget(QLabel("Bar Width"), 0, 2)
        self.grid.addWidget(self.barWidth, 0, 3)
        self.setLayout(self.grid)

    def updateConfig(self):
        self.config.ylim = int(self.ylim.text())
        self.config.barWidth = float(self.barWidth.text())

class PlotAppSettingsDialog(QDialog):
    def __init__(self, config: PlotAppCfg, topicMap: TopicMap):
        super().__init__()
        self.setWindowTitle("Plot Settings")
        self.settingsUI = PlotAppSettings(config, topicMap)
        self.initUI()

    def initUI(self):
        QBtn = (QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.handleAccepted) 
        self.buttonBox.rejected.connect(self.reject)
        layout = QVBoxLayout()
        layout.addWidget(self.settingsUI)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)

    def handleAccepted(self):
        self.settingsUI.updateConfig()
        self.accept()
