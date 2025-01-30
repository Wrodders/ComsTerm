import sys
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import CubicSpline
from PyQt6.QtCore import QObject, pyqtSignal, QThread
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.animation import FuncAnimation
from common.logger import getmylogger
from common.worker import Worker
from common.zmqutils import ZmqSub, Endpoint, Transport

from client.zmqQtBridge import ZmqBridgeQt

class PlotCanvas(FigureCanvas):
    def __init__(self, parent=None):
        fig, self.ax = plt.subplots(figsize=(5, 5))
        super().__init__(fig)
        self.setParent(parent)

        self.ax.set_xlim(-500, 500)
        self.ax.set_ylim(-500, 500)
        self.ax.set_xlabel("X Position (cm)")
        self.ax.set_ylabel("Y Position (cm)")

        # Initialize position values and buffer
        self.xpos = 0.0
        self.ypos = 0.0
        self.buffer_size = 5000
        self.buffer = {'x': [], 'y': []}
        self.scatter_plot = self.ax.scatter([], [], color='blue')  # Initialize an empty scatter plot
        self.spline_line, = self.ax.plot([], [], color='red', label='Trajectory Spline')  # For spline plot
        self.ax.legend(loc='upper left')
        # add grid
        self.ax.grid(True)

        # Set up the animation
        self.animation = FuncAnimation(
            fig, self.animate, fargs=(self.scatter_plot,), interval=200, blit=True, cache_frame_data=False
        )

    def update_plot(self, xpos, ypos):
        """Update the latest point on the plot and store it in the buffer."""
        self.xpos = xpos
        self.ypos = ypos

        # Maintain a circular buffer of the last 100 points
        if len(self.buffer['x']) >= self.buffer_size:
            self.buffer['x'].pop(0)
            self.buffer['y'].pop(0)
        
        self.buffer['x'].append(self.xpos)
        self.buffer['y'].append(self.ypos)

    def animate(self, i, scatter_plot):
        """Animation function to update the plot with the latest position and plot the spline."""
        # Update the scatter plot with the latest point
        scatter_plot.set_offsets([[self.xpos, self.ypos]])

        # Compute the spline from the circular buffer
        if len(self.buffer['x']) > 2:  # Ensure there are enough points to compute a spline
            # Create a cubic spline of the past trajectory
            cs_x = CubicSpline(range(len(self.buffer['x'])), self.buffer['x'])
            cs_y = CubicSpline(range(len(self.buffer['y'])), self.buffer['y'])

            # Generate fine-grained points for smooth curve
            fine_x = np.linspace(0, len(self.buffer['x'])-1, 100)
            fine_y = cs_y(fine_x)
            fine_x_vals = cs_x(fine_x)

            # Update the spline line
            self.spline_line.set_data(fine_x_vals, fine_y)

        return [scatter_plot, self.spline_line]


class MatplotlibWidget(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Robot Position Plot")
        self.setGeometry(100, 100, 800, 600)

        # Initialize xpos and ypos
        self.xpos = 0.0
        self.ypos = 0.0

        self.canvas = PlotCanvas(self)  # Ensure parent-child relationship
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.canvas)

        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

        self.zmqBridge = ZmqBridgeQt()
        self.zmqBridge.msgSig.connect(self.update_robot_state_from_zmq)  # Connect to the update function
        self.zmqBridge.subscriber.addTopicSub("STATE/XPOS")
        self.zmqBridge.subscriber.addTopicSub("STATE/YPOS")

        self.zmqBridge.workerIO._begin()

    def update_robot_state_from_zmq(self, data):
        topic, msg = data
        # Process the data and update the plot
        try:
            coordinate = float(msg)  # Assuming msg is a float as string
            if topic == "STATE/XPOS":
                self.xpos = coordinate
            elif topic == "STATE/YPOS":
                self.ypos = coordinate
            # Update the plot with the latest position
            self.canvas.update_plot(self.xpos, self.ypos)
        except ValueError:
            self.zmqBridge.log.error(f"Invalid coordinate received: {msg}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MatplotlibWidget()
    window.show()
    sys.exit(app.exec())
