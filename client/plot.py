from PyQt6 import QtCore
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QColor
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.animation as animation


from core.device import TopicMap, Worker
from core.ZmqDevice import ZmqSub, Transport, Endpoint
from common.logger import getmylogger

from collections import deque , defaultdict

plt.style.use('dark_background')



"""     
Plot:   Subscribes to topics publishing data over ZMQ. 
        Topic Data pushed to thread safe ring buffer to be polled by main GUI loop.
        Topic data treated as a data series for plotting and graphing.   
        Add and remove DataSeries dynamically. 
"""

class BasePlot(QFrame):
    def __init__(self):
        super().__init__()
        self.log = getmylogger(__name__)
        self.workerIO = Worker(self._run)
        self.sub = ZmqSub(Transport.IPC, Endpoint.COMSTERM)
        self.dataSeries = defaultdict(deque)

    def _run(self):
        """
        Acquire data over zmq socket, push data to relevant ring buffers dQueue
        """
        while True:
            topic, data = self.sub.receive()  # Assuming `receive` method to receive topic and data from ZMQ
            if topic:
                self.dataSeries[topic].append(data)


class LinePlot(BasePlot):
    def __init__(self,yrange: tuple[float, float], xrange:int, protocol :str ):
        super().__init__()

        self.initUI()
        self.connectSignals()

        self.protocol = protocol
    
        # Create a figure and axis for the plot
        self.x_len = xrange
        self.y_range = yrange
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(1,1,1)
        self.lines = [] 

        self.dataSet = {}

       
        # Initialize the plot
        self.xs = list(range(0,self.x_len)) # time series (x-axis)
        self.ax.set_ylim(self.y_range) 

        for label in self.protocol:
            self.dataSet[label] = [0] * self.x_len  # zero out data values array
            line, = self.ax.plot(self.xs, self.dataSet[label], label=label )  # create a line on the plot
            self.lines.append(line)
        self.ax.legend(loc=1)
        # matplotlib timer animation
        self.animation =  animation.FuncAnimation(self.fig,self.animate,fargs=(self.lines,),interval=200,blit=False,cache_frame_data=False)


    def initUI(self):
        self.canvas = FigureCanvas(self.fig)
        self.settingsB = QPushButton("Plot Settings")
        self.cursorsB = QPushButton("Cursors")
        self.cursorsB.setCheckable(True)
        self.clearB  = QPushButton("Clear")
        self.recordB = QPushButton("Start Record")
        self.recordB.setCheckable(True)
        self.filterB = QPushButton("Filters")

        layout = QGridLayout()
        layout.addWidget(self.settingsB, 0,0)
        layout.addWidget(self.cursorsB, 0,1)
        layout.addWidget(self.clearB, 0,2)
        layout.addWidget(self.recordB, 0,3)
        layout.addWidget(self.filterB, 0,4)
        layout.addWidget(self.canvas, 1, 0, 5,5)
        self.setLayout(layout)
        self.setContentsMargins(0,0,0,0)
        self.setMinimumSize(300, 300)

    def connectSignals(self):
        self.settingsB.clicked.connect(self.settingsHandel)


    def settingsHandel(self):
        pass

    def cursorsHandel(self):
        pass

    def clearHandel(self):
        pass

    def recordHandel(self):
        pass

    def filterHandel(self):
        pass


    @QtCore.pyqtSlot(tuple)
    def _updateData(self, msg : tuple[str,str]):
       # Grabs msg data from the worker thread
        topic, data = msg

        try:
            for i, name in enumerate(self.protocol):
                if name != "":
                    argData = float(data.split(":")[i]) # extract data arguments from topic header
                    self.dataSet[name].append(argData)   
        except Exception as e:
           self.log.error(f"Exception in UpdateData:{e}")
           pass
       
    def animate(self, i, lines):
        # Update the plot with new data
        for line, (key, value) in zip(lines, self.dataSet.items()):
            line.set_ydata(value[-self.x_len:])        # Update lines with new Y values
        return lines




class CreatePlot(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()

        self.maxDataSeries = 8

    def initUI(self):
        self.log = getmylogger(__name__)
        self.setWindowTitle("New Plot")
        self.setMinimumSize(600,300)

        self.seriesInfo = defaultdict(dict) # holds the info about the requested topic data series to plot
        self.plotCombo = QComboBox()
        self.plotCombo.addItems(["Line Plot", "Bar Plot", "Scatter Plot"])
        self.newSeriesB = QPushButton("Add Data Series")
        self.newSeriesB.clicked.connect(self.newSeriesHandle)
        self.newSeriesB.setMaximumWidth(150)
        self.plotCombo.setMaximumWidth(200)

        self.saveConfigB = QPushButton("Save Plot Config")
        self.saveConfigB.setMaximumWidth(200)


        hBox = QHBoxLayout()
        hBox.addWidget(self.plotCombo)
        hBox.addWidget(self.newSeriesB)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Topic Path", "Series Name", "Data Type", "Color", ""])


        # Dialogue Accept
        QBtn = QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel 
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.validateInput)
        self.buttonBox.rejected.connect(self.reject)

        vBox = QVBoxLayout()
        vBox.addLayout(hBox)
        vBox.addWidget(self.table)
        vBox.addWidget(self.saveConfigB)
        vBox.addWidget(self.buttonBox)
        self.setLayout(vBox)


    def newSeriesHandle(self):
        rowCount = self.table.rowCount()
        if rowCount >= self.maxDataSeries:
            self.log.error(f"Max number of Data Series per plot is {self.maxDataSeries}")
            return
        
        self.table.insertRow(rowCount)
        colorCombo = QComboBox()
        colors = ["Black", "Blue", "Green", "Red", "Yellow", "Orange", "Pink", "Cyan", "Magenta"]
        colorCombo.addItems(colors)
        colorCombo.setCurrentIndex(rowCount)
        self.table.setCellWidget(rowCount, 3, colorCombo)

        removeB = QPushButton("Remove")
        removeB.clicked.connect(lambda _, row=rowCount: self.removeSeries(row))
        self.table.setCellWidget(rowCount, 4, removeB)

    def removeSeries(self, row):
        self.table.removeRow(row)


    def validateInput(self):
        pass