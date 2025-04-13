import sys
import numpy as np
from collections import deque
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from PyQt6.QtCore import QTimer, pyqtSlot
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.animation import FuncAnimation
import matplotlib.pyplot as plt
from scipy.interpolate import CubicSpline

from common.logger import getmylogger
from client.zmqQtBridge import ZmqBridgeQt
from common.zmqutils import Endpoint, Transport
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

        self.predicted_trajectory.clear()
        dt = 0.5
        pred_x = self.x_g
        pred_y = self.y_g
        pred_phi = self.phi_g
        for i in range(1, self.horizon + 1):
            pred_phi += omega_g * dt
            pred_x += vel_g * np.cos(pred_phi) * dt
            pred_y += vel_g * np.sin(pred_phi) * dt
            self.predicted_trajectory.append((pred_x, pred_y))

from collections import deque, defaultdict

class MapPlot(FigureCanvas):
    def __init__(self):
        fig, self.ax = plt.subplots(figsize=(5, 5))
        super().__init__(fig)
        self.log = getmylogger(__name__)

        self.required_topics = [
            "TELEM/TWSB/XG",
            "TELEM/TWSB/YG",
            "TELEM/TWSB/PSIG",
            "TELEM/TWSB/LINEAR_VEL",
            "TELEM/TWSB/ANGULAR_VEL",
        ]

        self.topic_to_key = {
            "TELEM/TWSB/XG": "x",
            "TELEM/TWSB/YG": "y",
            "TELEM/TWSB/PSIG": "phi",
            "TELEM/TWSB/LINEAR_VEL": "vel",
            "TELEM/TWSB/ANGULAR_VEL": "omega",
        }

        # Store data per topic
        self.dataset = {topic: deque(maxlen=2028) for topic in self.required_topics}

        # Latest message tracker
        self.frame_cache = {}

        # Used to collect sequential frames
        self.current_frame = {}

        topic_map = TopicMap()
        topic_map.load_topics_from_json("robotConfig.json")

        self.zmqBridge = ZmqBridgeQt(
            topicMap=topic_map,
            transport=Transport.TCP,
            endpoint=Endpoint.BOT_MSG
        )
        self.zmqBridge.subscriptions = tuple(self.required_topics)
        self.zmqBridge.subscriber.addTopicSub("TELEM/TWSB")
        self.zmqBridge.msgSig.connect(self._updateData)
        self.zmqBridge.workerIO._begin()

        self.robot = MobileRobot("bot1")

        self.ax.set_xlim(-2, 2)
        self.ax.set_ylim(-2, 2)
        self.ax.set_xlabel("X Position (cm)")
        self.ax.set_ylabel("Y Position (cm)")
        self.ax.legend(["Robot", "History", "Predicted"], loc="upper right")
        self.ax.grid()

        self.robot_dot, = self.ax.plot([], [], 'bo', markersize=8)
        self.history_line, = self.ax.plot([], [], 'g-', linewidth=1)
        self.predicted_line, = self.ax.plot([], [], 'r--')

        self.ani = FuncAnimation(self.figure, self.animate, interval=100)

    @pyqtSlot(tuple)
    def _updateData(self, msg: tuple[tuple, str]):
        topic, data = msg
        try:
            value = float(data)
            self.dataset[topic].append(value)

            key = self.topic_to_key.get(topic)
            if key:
                self.current_frame[key] = value


            # Only proceed if we have all values
            if all(k in self.current_frame for k in ["x", "y", "phi", "vel", "omega"]):
                self.update_plot(
                    self.current_frame["x"],
                    self.current_frame["y"],
                    self.current_frame["phi"],
                    self.current_frame["vel"],
                    self.current_frame["omega"]
                )
        except Exception as e:
            self.log.error(f"Error in _updateData: {e}")

    def update_plot(self, x, y, phi, v, omega):
        self.robot.update(x, y, phi, v, omega)



    def animate(self, i):
        self.robot_dot.set_data([self.robot.x_g], [self.robot.y_g])
        if len(self.robot.prev_trajectory) > 1:
            x_hist, y_hist = zip(*self.robot.prev_trajectory)
            self.history_line.set_data(x_hist, y_hist)

        if len(self.robot.predicted_trajectory) > 1:
            x_pred, y_pred = zip(*self.robot.predicted_trajectory)
            t = np.arange(len(x_pred))
            cs_x = CubicSpline(t, x_pred)
            cs_y = CubicSpline(t, y_pred)
            t_fine = np.linspace(0, len(x_pred) - 1, 50)
            self.predicted_line.set_data(cs_x(t_fine), cs_y(t_fine))

        return self.robot_dot, self.history_line, self.predicted_line


class MapApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Map App")
        self.setGeometry(100, 100, 800, 600)
        self.initUI()

    def initUI(self):
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        layout = QVBoxLayout(self.central_widget)
        self.map_plot = MapPlot()
        self.saveBtn = QPushButton("Save", self)
        self.saveBtn.clicked.connect(self.handle_save)

        layout.addWidget(self.map_plot)
        layout.addWidget(self.saveBtn)

    def handle_save(self):
        self.map_plot.figure.savefig("robot_map.png")
        print("Map saved as 'robot_map.png'")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MapApp()
    window.show()
    sys.exit(app.exec())
