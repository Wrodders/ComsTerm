from PyQt6 import QtCore
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.animation as animation

from logger import getmylogger


log = getmylogger(__name__)

plt.style.use('dark_background')

class LinePlot(QWidget):
    def __init__(self, title: str, yrange: tuple[float, float], xrange:int, protocol :str):
        super().__init__()
        self.topic = title
        self.protocol = protocol.split(":") # msgData format

        # Create a figure and axis for the plot
        self.x_len = xrange
        self.y_range = yrange
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(1,1,1)
        self.lines = [] 
        self.dataSeries = {}

        self.canvas = FigureCanvas(self.fig)
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        self.setContentsMargins(0,0,0,0)
        self.setMinimumSize(300, 300)

        # Initialize the plot
        self.xs = list(range(0,self.x_len)) # time series (x-axis)
        self.ax.set_ylim(self.y_range) 

        for label in self.protocol:
            self.dataSeries[label] = [0] * self.x_len  # zero out data values array
            line, = self.ax.plot(self.xs, self.dataSeries[label], label=label )  # create a line on the plot
            self.lines.append(line)
        self.ax.legend(loc=1)
        self.animation =  animation.FuncAnimation(self.fig,self.animate,fargs=(self.lines,),interval=200,blit=False,cache_frame_data=False)


    @QtCore.pyqtSlot(tuple)
    def _updateData(self, msg : tuple[str,str]):
       # Grabs msg data from the worker thread
        topic, data = msg
    
        if(topic != self.topic): # filter on topic
            return
        try:
            for i, name in enumerate(self.protocol):
                argData = float(data.split(":")[i]) #get data for each argument in protocol
                self.dataSeries[name].append(argData)   
        except Exception as e:
           log.error(f"Exception in UpdateData:{e}")
           pass
       
    def animate(self, i, lines):
        # Update the plot with new data
        for line, (key, value) in zip(lines, self.dataSeries.items()):
            line.set_ydata(value[-self.x_len:])        # Update lines with new Y values
        return lines

class CreatePlot(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("New Plot")
        self.setFixedSize(300,250)

        self.inputEntries = []
        
        
        topicLabel = QLabel("Topic")
        yAxisLabel = QLabel("Y-Axis")
        minLabel = QLabel("Min:")
        maxLabel = QLabel("Max:")
        timeWindowLabel =QLabel("Time Window")
        protocolLabel = QLabel("Protocol")
        typeLabel = QLabel("Plot Type")
        
        self.pltTopic = QLineEdit()
        self.pltTopic.setMinimumWidth(170)
        self.pltYMin = QLineEdit()
        self.pltYMax = QLineEdit()
        self.pltxWindow = QLineEdit()
        self.pltxWindow.setMaximumWidth(80)
        self.pltProtocol = QLineEdit()
        self.pltProtocol.setMinimumWidth(170)
        self.pltType = QComboBox()
        self.pltType.setMinimumWidth(180)
        self.pltType.addItem("Line Plot")# add more as implemented
        #self.pltType.addItem("Bar Char") 

        self.inputEntries.append(self.pltTopic)
        self.inputEntries.append(self.pltYMin)
        self.inputEntries.append(self.pltYMax)
        self.inputEntries.append(self.pltxWindow)
        self.inputEntries.append(self.pltProtocol)

        self.form = QFormLayout()
        self.form.addRow(topicLabel, self.pltTopic)
        hBox = QHBoxLayout()
        hBox.addWidget(minLabel)
        hBox.addWidget(self.pltYMin)
        hBox.addWidget(maxLabel)
        hBox.addWidget(self.pltYMax)

        self.form.addRow(yAxisLabel, hBox)
        self.form.addRow(timeWindowLabel, self.pltxWindow)
        self.form.addRow(protocolLabel, self.pltProtocol)
        self.form.addRow(typeLabel, self.pltType)

        QBtn = QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.validateInput)
        self.buttonBox.rejected.connect(self.reject)

        vBox = QVBoxLayout()
        vBox.addLayout(self.form)
        vBox.addWidget(self.buttonBox)
        self.setLayout(vBox)
        

    def validateInput(self):
        for entry in self.inputEntries:
            if isinstance(entry, QLineEdit):
                if entry.text() == "":
                    errMsg = QMessageBox.critical(self, "Error", "All Fields are Mandatory")
                    return
        self.accept()
        
    def getValues(self) -> tuple:
        # Retrieve values from the input fields and return them
        try:
            topic = self.pltTopic.text()
            plotType = self.pltType.currentText()
            yRange = [float(self.pltYMin.text()), float(self.pltYMax.text())]
            timeWindow = int(self.pltxWindow.text())
            protocol = self.pltProtocol.text()
        except ValueError as e:
            log.error(f"Error in Get_Values {e}")
        

        return (topic, plotType, yRange, timeWindow, protocol)