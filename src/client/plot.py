from PyQt6 import QtCore
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QColor

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.animation as animation
plt.style.use('dark_background')

from client.zmqQtBridge import ZmqBridgeQt
from common.logger import getmylogger
from client.menus import TopicMenu
from core.device import TopicMap

"""     
Plot:   Subscribes to topics publishing data over ZMQ. 
        Topic Data pushed to thread safe ring buffer to be polled by main GUI loop.
        Topic data treated as a data series for plotting and graphing.   
        Add and remove DataSeries dynamically. 
"""
class PlotApp(QFrame):
    def __init__(self):
        super().__init__()
        self.log = getmylogger(__name__)
        self.maxPlots = 4
        self.topicMap = None
        self.plots = list()
        self.initUI()

    def initUI(self):
        self.grid = QGridLayout()
        self.setLayout(self.grid)

        self.newPlot_PB = QPushButton("New Plot")
        self.newPlot_PB.clicked.connect(self.new_handle)
        self.plotSettings_PB = QPushButton("Settings")
        self.plotSettings_PB.clicked.connect(self.settings_handle)
        self.record_PB = QPushButton("Record")
        self.record_PB.clicked.connect(self.record_handle)
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_plt_handle)
        self.tabs.setTabPosition(QTabWidget.TabPosition.South)

        self.grid.addWidget(self.tabs, 1, 0, 4, 4)
        self.grid.addWidget(self.newPlot_PB, 0, 0)
        self.grid.addWidget(self.plotSettings_PB, 0, 1)
        self.grid.addWidget(self.record_PB, 0,2)

    def close(self):
        for plot in self.plots:
            plot.close()

    def new_handle(self):
        if(self.tabs.count() <= self.maxPlots):
            if(isinstance(self.topicMap, TopicMap)):
                diag = CreatePlot(self.topicMap)
                if diag.exec() == True:
                    protocol = diag.topicMenu.saveProtocol()
                    yRange = (float(diag.topicMenu.yMin.text()) , float(diag.topicMenu.yMax.text()))
                    plot = LinePlot()
                    plot.config(protocol=protocol, yrange=yRange,xrange=100)
                    self.plots.append(plot)
                    self.tabs.addTab(plot, plot.name)
            else:
                self.log.error("No Valid TopicMap")

    def close_plt_handle(self, index):
        active_plot = self.tabs.widget(index)
        if(isinstance(active_plot, BasePlot)):
            active_plot.close()
            self.tabs.removeTab(index)


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
        self.setMinimumSize(600,300)
      

    @QtCore.pyqtSlot(tuple)
    def _updateData(self, msg: tuple[tuple, str]):
       # Grabs msg data from the worker thread
       
        topic, data = msg
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


class CreatePlot(QDialog):
    """Dialog for creating a new plot."""

    def __init__(self, topicMap: TopicMap):
        """Constructor method for CreatePlot class."""
        super().__init__()
        self.pubMap = topicMap
        self.initUI()
        self.maxDataSeries = 8
    def initUI(self):
        """Initializes the user interface."""
        self.setWindowTitle("New Plot")
        self.setMinimumSize(600, 300)

        self.grid = QGridLayout()

        self.topicMenu = TopicMenu(self.pubMap)

        QBtn = (
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.verify)
        self.buttonBox.rejected.connect(self.reject)

        self.grid.addWidget(self.topicMenu, 0, 0, 4, 2)
        self.grid.addWidget(self.buttonBox, 4, 0, 1, 2)
        self.setLayout(self.grid)

    def verify(self):
        try:
            float(self.topicMenu.yMin.text())
            float(self.topicMenu.yMax.text())
            self.accept()
        except ValueError:
            err = QMessageBox.critical(self, "Error", "NaN Entry")
            
                

