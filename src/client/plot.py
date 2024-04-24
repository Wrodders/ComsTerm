from PyQt6 import QtCore
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QColor

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.animation as animation
plt.style.use('dark_background')

from common.zmqutils import ZmqBridgeQt
from common.logger import getmylogger
from common.utils import TopicMenu
from core.device import TopicMap

"""     
Plot:   Subscribes to topics publishing data over ZMQ. 
        Topic Data pushed to thread safe ring buffer to be polled by main GUI loop.
        Topic data treated as a data series for plotting and graphing.   
        Add and remove DataSeries dynamically. 
"""

class BasePlot(QFrame):
    """Base class for plotting."""
    def __init__(self):
        """Constructor method for BasePlot class."""
        super().__init__()
        self.log = getmylogger(__name__)
        self.zmqBridge = ZmqBridgeQt() 

        self.zmqBridge.msgSig.connect(self._updateData)
        self.zmqBridge.workerIO._begin()

    @QtCore.pyqtSlot(tuple)
    def _updateData(self, msg: tuple[str, str]):
        raise NotImplementedError("Subclasses must implement updateData method")


class LinePlot(BasePlot):
    """Class for line plotting."""
    def __init__(self, yrange: tuple[float, float], xrange: int, protocol: tuple[str, ...]):
        """Constructor method for LinePlot class."""
        super().__init__()  
        self.x_len = xrange
        self.y_range = yrange
        self.protocol = protocol
        self.dataSet = dict()
        self.lines = list()

        self.initUI()
        self.connectSignals()

    def closeEvent(self, event):
        """Event handler for closing the console.

        Args:
            event (QCloseEvent): The close event.
        """
        self.log.debug(f"Closing Plot {self.protocol}")
        self.zmqBridge.workerIO._stop()  # stop device thread
        event.accept()

    def initUI(self):
        """Initializes the user interface."""
            # Create a figure and axis for the plot
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(1,1,1)
        self.ax.grid(linestyle='dashed', linewidth=0.5)

        # Initialize the plot
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


        self.canvas = FigureCanvas(self.fig)
        self.settingsB = QPushButton("Plot Settings")
        self.cursorsB = QPushButton("Cursors")
        self.cursorsB.setCheckable(True)
        self.clearB = QPushButton("Clear")
        self.recordB = QPushButton("Start Record")
        self.recordB.setCheckable(True)
        self.filterB = QPushButton("Filters")

        layout = QGridLayout()
        layout.addWidget(self.settingsB, 0, 0)
        layout.addWidget(self.cursorsB, 0, 1)
        layout.addWidget(self.clearB, 0, 2)
        layout.addWidget(self.recordB, 0, 3)
        layout.addWidget(self.filterB, 0, 4)
        layout.addWidget(self.canvas, 1, 0, 5, 5)
        self.setLayout(layout)
        self.setContentsMargins(0, 0, 0, 0)
        self.setMinimumSize(300, 300)

    def connectSignals(self):
        """Connects signals to slots."""
        self.settingsB.clicked.connect(self.settingsHandle)


    def settingsHandle(self):
        """Handles opening settings."""
        pass

    def cursorsHandle(self):
        """Handles cursor actions."""
        pass

    def clearHandle(self):
        """Handles clearing the plot."""
        pass

    def recordHandle(self):
        """Handles recording."""
        pass

    def filterHandle(self):
        """Handles filtering."""
        pass


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
            
                

