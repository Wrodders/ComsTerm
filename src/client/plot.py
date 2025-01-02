from PyQt6 import QtCore
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QColor

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.animation as animation
plt.style.use('dark_background')
from collections import deque

from client.zmqQtBridge import ZmqBridgeQt
from common.logger import getmylogger
from client.menus import DataSeriesTable
from core.device import TopicMap
import sys
from dataclasses import dataclass , field, asdict
from typing import List, Tuple, Union
from enum import Enum
import os, json

"""     
Plot:   Subscribes to topics publishing data over ZMQ. 
        Topic Data pushed to thread safe ring buffer to be polled by main GUI loop.
        Topic data treated as a data series for plotting and graphing.   
        Add and remove DataSeries dynamically. 
        Settings -> UI Elements for configuring plot settings
        Config -> Values for plot settings
"""

@dataclass
class LinePlotCfg():
    yrange: tuple[float, float] = (-100, 100)

@dataclass
class ScatterPlotCfg():
    yrange: tuple[float, float] = (-100, 100)
    xrange: tuple[float, float] = (-100, 100)
    marker: str = "o"

@dataclass
class BarPlotCfg():
    ylim: int = 100
    barWidth: float = 0.35

PlotTypeMap = {
            "LINE": LinePlotCfg,
            "SCATTER": ScatterPlotCfg,
            "BAR": BarPlotCfg
        }

@dataclass
class PlotCfg():
    protocol: tuple[str, ...] = field(default_factory=tuple)
    plotType: str = "LINE"
    plotName: str = "Plot 0"
    typeCfg: Union[LinePlotCfg, ScatterPlotCfg, BarPlotCfg] = field(default_factory=LinePlotCfg)
    maxPlotSeries: int = 8
    sampleBufferLen: int = 100


@dataclass
class PlotAppCfg():
    #  list of plot configurations default to a single plot
    plotConfigs : List[PlotCfg] = field(default_factory=list)
    cfgFilePath: str = "config/cfg_plotApps.json"

    def save(self):
        def serialize(obj):
            if isinstance(obj, Enum):
                return obj.value
            return obj
        with open(self.cfgFilePath, "w") as file:
            json.dump(asdict(self), file, default=serialize, indent=4)
    def load(self):
        # Load the configuration from the JSON file
        with open(self.cfgFilePath, "r") as file:
            data = json.load(file)  # Parse the JSON into a Python dictionary
        
        plot_configs = []
        for config in data.get("plotConfigs", []):
            plot_type = config["plotType"]
            plotCfgClass = PlotTypeMap[plot_type]  # Get the appropriate class based on plotType
            plotCfgInstance = plotCfgClass(**config["typeCfg"])  # Create an instance of the class with the config data
            
            pltCfg = PlotCfg(
                protocol=config["protocol"],
                plotType=plot_type,
                plotName=config["plotName"],
                maxPlotSeries=config["maxPlotSeries"],
                sampleBufferLen=config["sampleBufferLen"],
                typeCfg=plotCfgInstance
            )
            
            plot_configs.append(pltCfg)  # Append to plot_configs

        # Return the fully populated PlotAppCfg
        return PlotAppCfg(
            plotConfigs=plot_configs,
            cfgFilePath=data.get("cfgFilePath", self.cfgFilePath)  # Default to the current path if not provided
        )

# Main Application Class
class PlotApp(QFrame):
    def __init__(self, configFilePath: str):
        super().__init__()
        self.log = getmylogger(__name__)
        self.maxPlots = 4
        self.topicMap = TopicMap()
        self.topicMap.loadTopicsFromCSV('devicePub.csv')
        self.plots = list()
        configDiag = PlotAppSettingsDialog(self.topicMap)
        if(configDiag.exec() == True):
            self.config = configDiag.config
    def initUI(self):
        self.grid = QGridLayout()
        self.setLayout(self.grid)



    def close(self):
        for plot in self.plots:
            plot.close()

    def new_plot_hdl(self):
        pass


    def close_plt_handle(self, index):
        pass

    def settings_handle(self):
        print("Settings")

    def record_handle(self):
        print("record")

class BasePlot(QFrame):
    """Base class for plotting."""
    def __init__(self):
        """Constructor method for BasePlot class."""
        super().__init__()
        self.name = ""
        self.log = getmylogger(__name__)
        self.zmqBridge = ZmqBridgeQt() 
        self.zmqBridge.msgSig.connect(self._updateData)
        self.zmqBridge.workerIO._begin()

    @QtCore.pyqtSlot(tuple)
    def _updateData(self, msg: tuple[str, str]):
        raise NotImplementedError("Subclasses must implement updateData method")
    
    def close(self):
        self.log.debug(f"Closing Plot {self.name}")
        self.zmqBridge.workerIO._stop()  # stop device thread

class LinePlot(BasePlot):
    """Class for line plotting."""
    def __init__(self):
        """Constructor method for LinePlot class."""
        super().__init__()  
        self.name = "Line Plot"
        self.x_len = int()
        self.y_range = tuple()
        self.protocol = tuple()
        self.dataSet = dict()
        self.lines = list()
        self.initUI()

    def config(self, yrange: tuple[float, float], xrange: int, protocol: tuple[str, ...]):
        self.x_len = xrange
        self.y_range = yrange
        self.protocol = protocol

        self.xs = list(range(0, self.x_len)) # time series (x-axis)
        self.ax.set_ylim(self.y_range) 

        for label in self.protocol:
            self.zmqBridge.subscriber.addTopicSub(label)
            self.dataSet[label] = [0] * self.x_len  # zero out data values array
            line, = self.ax.plot(self.xs, self.dataSet[label], label=label )  # create a line on the plot
            self.lines.append(line)
        self.ax.legend(loc=1)
         # matplotlib timer animation
        self.animation =  animation.FuncAnimation(self.fig, self.animate, fargs=(self.lines,), 
                                                  interval=200, blit=False, cache_frame_data=False)

    def initUI(self):
        """Initializes the user interface."""
        # Create a figure and axis for the plot
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(1,1,1)
        self.ax.grid(linestyle='dashed', linewidth=0.5)
        # Widgets
        self.canvas = FigureCanvas(self.fig)
        layout = QGridLayout()
        layout.addWidget(self.canvas, 0, 0, 5, 5)
        self.setLayout(layout)
        self.setContentsMargins(0, 0, 0, 0)
      
    @QtCore.pyqtSlot(tuple)
    def _updateData(self, msg: tuple[tuple, str]):
       # Grabs msg data from the worker thread
        topic, data = msg
        print(topic,data)
        try:
            self.dataSet[topic].append(float(data))   
        except Exception as e:
           self.log.error(f"Exception in UpdateData:{e}")
           pass
       
    def animate(self, i, lines):
        # Update the plot with new data
        for line, (key, value) in zip(lines, self.dataSet.items()):
            line.set_ydata(value[-self.x_len:])        # Update lines with new Y values
        return lines
  


# Settings Menus
class PlotAppSettingsDialog(QDialog):
    def __init__(self, topicMap: TopicMap):
        super().__init__()
        self.setWindowTitle("Plot Settings")
        self.topicMap = topicMap
        # if the config file exists load the settings from the file 
        if os.path.exists("config/cfg_plotApps.json"):
            config = PlotAppCfg()
            self.config = config.load()
        else:
            self.config = PlotAppCfg() # otherwise, use default settings
            self.config.plotConfigs.append(PlotCfg())
        self.initUI()
        
    def initUI(self):
        self.cfgFile = QLineEdit(self.config.cfgFilePath)
        self.load_PB = QPushButton("Load Config")
        self.load_PB.clicked.connect(self.load_handle)
        self.save_PB = QPushButton("Save Config")
        self.save_PB.clicked.connect(self.save_handle)
        self.plotList = QListWidget()
        # Create a stack layout for the plot configurations
        self.plotConfigStack = QStackedLayout()
                    
        for idx in range(len(self.config.plotConfigs)):
            self.createPlotCfg(self.config.plotConfigs[idx]) 
            

        # Auto switch plot config based on currently selected plot
        self.plotList.currentRowChanged.connect(self.plotConfigStack.setCurrentIndex)
        self.addPlot_PB = QPushButton("+")
        self.addPlot_PB.clicked.connect(lambda: self.addPlot_handle(PlotCfg()))
        self.removePlot_PB = QPushButton("-")
        self.removePlot_PB.clicked.connect(lambda: self.removePlot_handle(self.plotList.currentRow()))
        # Dialog buttons
        QBtn = (
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.dataSeriesConfig = DataSeriesTableSettings(self.topicMap)
        # connect the button to the method of the current plot configuration
        self.dataSeriesConfig.addSeriesBtn.clicked.connect(
            lambda: self.plotConfigStack.currentWidget().addSeries(self.dataSeriesConfig.grabSeries()))
        
        self.dataSeriesConfig.removeSeriesBtn.clicked.connect(
            lambda: self.plotConfigStack.currentWidget().removeSeries()
        )

        # Layout
        grid = QGridLayout()
        grid.addWidget(self.cfgFile, 0, 0, 1, 2)
        grid.addWidget(self.load_PB, 1, 0)
        grid.addWidget(self.save_PB, 1, 1)
        grid.addWidget(self.addPlot_PB, 2, 0)
        grid.addWidget(self.plotList, 2, 1, 2,1)
        grid.addWidget(self.removePlot_PB, 3, 0)

        hBox = QHBoxLayout()
        hBox.addWidget(self.dataSeriesConfig)
        hBox.addLayout(grid)

        vBox = QVBoxLayout()
        vBox.addLayout(hBox)
        vBox.addLayout(self.plotConfigStack)
        vBox.addWidget(self.buttonBox)
        self.setLayout(vBox)

    def addPlot_handle(self, plotCfg: PlotCfg):
       # Add a new plot confirufration to the stacked layout
        self.config.plotConfigs.append(plotCfg)
        self.createPlotCfg(plotCfg)
        

    def createPlotCfg(self, plotCfg: PlotCfg):
        new_plotSettings = PlotSettings(plotCfg)
        self.plotList.addItem(new_plotSettings.plotName.text())
        self.plotList.setCurrentRow(self.plotList.count()-1)
        
        new_plotSettings.plotName.textChanged.connect(lambda: self.plotList.currentItem().setText(new_plotSettings.plotName.text()))
        self.plotConfigStack.addWidget(new_plotSettings)
        self.plotConfigStack.setCurrentIndex(self.plotList.count()-1) # Auto switch to new plot config


    def removePlot_handle(self, index):
        # Remove the selected plot configuration from the stacked layout
        self.plotConfigStack.removeWidget(self.plotConfigStack.widget(index))
        self.config.plotConfigs.pop(index)
        self.plotList.takeItem(index)

    def load_handle(self):
        # load config from file 
        fileDialog = QFileDialog()
        fileDialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        fileDialog.setNameFilter("JSON Files (*.json)")
        if fileDialog.exec():
            self.config.cfgFilePath = fileDialog.selectedFiles()[0] # get the file path into config
            self.cfgFile.setText(self.config.cfgFilePath) # update the text box with the file path
    
            for idx in range(self.plotList.count()):
                self.removePlot_handle(idx)
            
            self.config = self.config.load()
           
            for idx in range(len(self.config.plotConfigs)):
                self.createPlotCfg(self.config.plotConfigs[idx])


    def save_handle(self):
        self.updateConfig()
        self.config.save()

    def updateConfig(self):
        # update settings with current plot configurations
        self.config.cfgFilePath = self.cfgFile.text()
        for i in range(self.plotList.count()):
            self.plotConfigStack.widget(i).updateConfig()
            self.config.plotConfigs[i] = self.plotConfigStack.widget(i).config
        

class DataSeriesTableSettings(QFrame):
    def __init__(self, pubMap):
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

class PlotSettings(QFrame):
    def __init__(self, plotCfg: PlotCfg):
        super().__init__()
        self.log = getmylogger(__name__)
        self.config = plotCfg
        self.initUI()
    def initUI(self):
        self.plotName = QLineEdit(self.config.plotName)
        self.plotType = QComboBox()
        self.plotType.addItems(PlotTypeMap.keys())
        if(self.config.plotType in PlotTypeMap.keys()):
            self.plotType.setCurrentText(self.config.plotType)
        self.maxSeries = QLineEdit(str(self.config.maxPlotSeries))
        self.maxSeries.setMaximumWidth(50)
        self.sampleBuffer = QLineEdit(str(self.config.sampleBufferLen))
        self.sampleBuffer.setMaximumWidth(50)

        # Config depending on plot type with default values
        self.linePlotSettings = LinePlotSettings(LinePlotCfg())
        self.scatterPlotSettings = ScatterPlotSettings(ScatterPlotCfg())
        self.barPlotSettings = BarPlotSettings(BarPlotCfg())        
        self.plotCfgStack = QStackedLayout()
        self.plotCfgStack.addWidget(self.linePlotSettings)
        self.plotCfgStack.addWidget(self.scatterPlotSettings)
        self.plotCfgStack.addWidget(self.barPlotSettings)
        self.plotCfgStack.setCurrentIndex(self.plotType.currentIndex())
        # Auto switch plot config based on currently selected plot type
        self.plotType.currentIndexChanged.connect(self.plotCfgStack.setCurrentIndex)
        # Data Series Table
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Topic Name", "Arg"])
        self.table.setRowCount(len(self.config.protocol))
        self.loadProtocol(self.config.protocol) # Load protocol into the table
        
        # Layout
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

    def saveProtocol(self) -> tuple[str, ...]:
        # Save current argument names of the table to a tuple protocol
        protocol = tuple(
            [
                (self.table.item(row, 0).text() + "/" + self.table.item(row, 1).text())
                for row in range(self.table.rowCount())
            ]
        )
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
        if self.table.rowCount() >= int(self.maxSeries.text()):
            self.log.error("Max number of series reached.")
        else:
            rowPosition = self.table.rowCount()
            self.table.insertRow(rowPosition)
            self.table.setItem(rowPosition, 0, QTableWidgetItem(topicName))
            self.table.setItem(rowPosition, 1, QTableWidgetItem(argName))

    def removeSeries(self):
        row = self.table.currentRow()
        self.table.removeRow(row)
        
    def updateConfig(self):
        self.config.plotName = self.plotName.text()
        self.config.plotType = self.plotType.currentText()
        self.config.maxPlotSeries = int(self.maxSeries.text())
        self.config.sampleBufferLen = int(self.sampleBuffer.text())
        self.config.protocol = self.saveProtocol()
        # Kinda Hacky; inheritance -> unnecessary complexity
        self.plotCfgStack.currentWidget().updateConfig() 
        self.config.typeCfg = self.plotCfgStack.currentWidget().config

class LinePlotSettings(QFrame):
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

class ScatterPlotSettings(QFrame):
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

class BarPlotSettings(QFrame):
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
