#-----------------------------------------------------------
# @file: deadReckonTrack.py
# @brief: Real-time Map plotting robots position from telemetry data
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import CubicSpline
from PyQt6.QtCore import QObject, pyqtSignal, QThread, QTimer 
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QLineEdit, QComboBox, QCheckBox , QTableWidget, QTableWidgetItem
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.animation import FuncAnimation
from common.logger import getmylogger
from common.worker import Worker
from common.zmqutils import ZmqSub, Endpoint, Transport
import sys
from PyQt6 import QtCore
from client.zmqQtBridge import ZmqBridgeQt
from collections import deque
from dataclasses import dataclass
from typing import List, Tuple
from common.messages import TopicMap

class MobileRobot:
    def __init__(self, name: str):
        self.name = name
        self.x_g = 0.0
        self.y_g = 0.0
        self.phi_g = 0.0
        self.horizon = 10
        self.prev_trajectory = deque(maxlen=2048)
        self.predicted_trajectory = deque(maxlen=512)
        self.prev_trajectory.append((self.x_g, self.y_g))

    def update(self, x_g: float, y_g: float, phi_g: float, vel_g: float, omega_g: float):    
        self.prev_trajectory.append((self.x_g, self.y_g))
        self.x_g = x_g
        self.y_g = y_g
        self.phi_g = phi_g

        # Recalculate prediction using a dynamic integration over a small time step
        self.predicted_trajectory.clear()
        dt = 0.5  # Prediction time step in seconds (you can adjust as needed)
        pred_x = self.x_g
        pred_y = self.y_g
        pred_phi = self.phi_g
        for i in range(1, self.horizon + 1):
            pred_phi += omega_g * dt  # update the heading
            pred_x += vel_g * np.cos(pred_phi) * dt
            pred_y += vel_g * np.sin(pred_phi) * dt
            self.predicted_trajectory.append((pred_x, pred_y))


class MapPlot(FigureCanvas):
    def __init__(self):
        fig, self.ax = plt.subplots(figsize=(5, 5))
        super().__init__(fig)
        self.dataset = {
            "TWSB/XG": deque(maxlen=100),
            "TWSB/YG": deque(maxlen=100),
            "TWSB/PHIG": deque(maxlen=100)
        }
        topicMap = TopicMap()
        topicMap.register("TWSB/XG", "0", ["msg", "timestamp"], ":")
        topicMap.register("TWSB/YG", "1", ["msg", "timestamp"], ":")
        topicMap.register("TWSB/PHIG", "2", ["msg", "timestamp"], ":")

        self.zmqBridge = ZmqBridgeQt(topicMap=topicMap, transport=Transport.TCP, endpoint=Endpoint.BOT_MSG)
        self.zmqBridge.msgSig.connect(self._updateData)
        for topic in self.dataset.keys():
            self.zmqBridge.subscriber.addTopicSub(topic)
        self.zmqBridge.workerIO._begin()

        self.robot = MobileRobot("bot1")

        self.ax.set_xlim(-500, 500)
        self.ax.set_ylim(-500, 500)
        self.ax.set_xlabel("X Position (cm)")
        self.ax.set_ylabel("Y Position (cm)")
        self.ax.grid()

        # Initialize artists
        self.robot_dot, = self.ax.plot([], [], 'bo', markersize=8)
        self.history_line, = self.ax.plot([], [], 'g-', linewidth=1)
        self.predicted_line, = self.ax.plot([], [], 'r--')

        # Start animation
        self.ani = FuncAnimation(self.figure, self.animate, interval=100)


    @QtCore.pyqtSlot(tuple)
    def _updateData(self, msg: tuple[tuple, str]):
        topic, data = msg
        try:
            # Append new data to the list for this topic
            self.dataSet[topic].append(float(data))
        except Exception as e:
            self.log.error(f"Exception in UpdateData: {e}")

    def update_plot(self, x, y, phi, v, omega):
        """Call this function from external trigger to update robot state."""
        self.robot.update(x, y, phi, v, omega)

    def animate(self, i):
        # Current position
        self.robot_dot.set_data([self.robot.x_g], [self.robot.y_g])

        # History
        if len(self.robot.prev_trajectory) > 1:
            x_hist, y_hist = zip(*self.robot.prev_trajectory)
            self.history_line.set_data(x_hist, y_hist)

        # Prediction
        if len(self.robot.predicted_trajectory) > 1:
            x_pred, y_pred = zip(*self.robot.predicted_trajectory)
            # Fit spline for smooth path
            t = np.arange(len(x_pred))
            cs_x = CubicSpline(t, x_pred)
            cs_y = CubicSpline(t, y_pred)
            t_fine = np.linspace(0, len(x_pred) - 1, 50)
            self.predicted_line.set_data(cs_x(t_fine), cs_y(t_fine))

        return self.robot_dot, self.history_line, self.predicted_line


class MapApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.log = getmylogger(__name__)
        self.setWindowTitle("Map App")
        self.setGeometry(100, 100, 800, 600)
        self.initUI()

    def initUI(self):
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        vbox = QVBoxLayout(self.central_widget)
        self.map_plot = MapPlot()
        self.saveBtn = QPushButton("Save", self)
        self.saveBtn.clicked.connect(self.handle_save)

        vbox.addWidget(self.map_plot)
        vbox.addWidget(self.saveBtn)

    def handle_save(self):
        self.map_plot.figure.savefig("robot_map.png")
        print("Map saved as 'robot_map.png'")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MapApp()
    window.show()
    debug = False

    if(debug):
        start_time = QtCore.QTime.currentTime()
        def debug_simData():
            t_now = QtCore.QTime.currentTime()
            elapsed_ms = start_time.msecsTo(t_now)
            t = elapsed_ms / 1000.0  # time in seconds

            # Robot starts at (0, 0), angle 0
            if len(window.map_plot.robot.prev_trajectory) == 1:
                window.map_plot.robot.x_g = 0.0
                window.map_plot.robot.y_g = 0.0
                window.map_plot.robot.phi_g = 0.0

            # Velocity model: Figure-8 using sinusoidal angular velocity
            v = 20  # constant linear speed (cm/s)
            omega = 1.5 * np.sin(0.5 * t)  # figure-8 pattern

            # Dead reckoning update
            dt = 0.5  # time step (seconds)
            robot = window.map_plot.robot
            new_phi = robot.phi_g + omega * dt
            new_x = robot.x_g + v * np.cos(robot.phi_g) * dt
            new_y = robot.y_g + v * np.sin(robot.phi_g) * dt

            window.map_plot.update_plot(new_x, new_y, new_phi, v, omega)
        timer = QTimer()
        timer.timeout.connect(debug_simData)
        timer.start(100)  # Update every 100 ms


    sys.exit(app.exec())
#-----------------------------------------------------------