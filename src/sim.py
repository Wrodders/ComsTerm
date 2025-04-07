#-----------------------------------------------------------
# @file    : sim.py
# @brief   : Simulate Path Follower on a a generated closed Random Track  
# @description : Visualizes GLobal and Robot Frames of Reference

import sys
import numpy as np
from scipy.interpolate import splprep, splev
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QLineEdit
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.patches import Polygon
from matplotlib.path import Path

def ensure_minimum_curve_radius(points, min_angle_deg=10):
    min_angle_rad = np.deg2rad(min_angle_deg)
    adjusted_points = [points[0]]
    for i in range(1, len(points) - 1):
        prev_point = adjusted_points[-1]
        current_point = points[i]
        next_point = points[(i + 1) % len(points)]
        vec1 = prev_point - current_point
        vec2 = next_point - current_point
        angle = np.arccos(
            np.clip(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)), -1.0, 1.0)
        )
        if angle < min_angle_rad:
            mid_point = (prev_point + next_point) / 2
            adjusted_points.append(mid_point)
        else:
            adjusted_points.append(current_point)
    adjusted_points.append(adjusted_points[0])
    return np.array(adjusted_points)

def generate_smooth_random_track(canvas_size=512, num_points=20, track_width=15, margin=50, randomness=30, min_curve_angle=10):
    angles = np.linspace(0, 2 * np.pi, num_points, endpoint=False)
    radius = np.linspace(margin, canvas_size // 2 - margin, num_points)
    random_offsets = np.random.uniform(-randomness, randomness, size=(num_points, 2))
    control_points = np.array([
        canvas_size // 2 + radius * np.cos(angles),
        canvas_size // 2 + radius * np.sin(angles)
    ]).T + random_offsets
    control_points = ensure_minimum_curve_radius(control_points, min_angle_deg=min_curve_angle)
    tck, u = splprep([control_points[:, 0], control_points[:, 1]], s=0, per=True)
    u_fine = np.linspace(0, 1, 1000)
    x_fine, y_fine = splev(u_fine, tck)
    return x_fine, y_fine

def transform_to_robot_view(x_fine, y_fine, robot_x, robot_y, robot_heading, fov_range=100):
    # Translate points to robot-centric coordinates
    relative_x = x_fine - robot_x
    relative_y = y_fine - robot_y
    
    # Create rotation matrix to align robot's heading
    total_rotation = -robot_heading + np.pi/2
    rotation_matrix = np.array([
        [np.cos(total_rotation), -np.sin(total_rotation)],
        [np.sin(total_rotation), np.cos(total_rotation)]
    ])
    
    # Apply rotation
    rotated_points = np.dot(np.vstack([relative_x, relative_y]).T, rotation_matrix.T)
    
    # Filter points that are in front of the robot (positive y) and within range
    view_mask = (rotated_points[:, 1] > 0) & (rotated_points[:, 1] < fov_range)
    return rotated_points[view_mask]

def compute_heading(x1, y1, x2, y2):
    return np.arctan2(y2 - y1, x2 - x1)

def get_fov_trapezoid(x, y, heading, near_width=60, far_width=80, length=60):
    direction = np.array([np.cos(heading), np.sin(heading)])
    right = np.array([-direction[1], direction[0]])

    near_center = np.array([x, y]) + direction * 10
    far_center = np.array([x, y]) + direction * length

    p1 = near_center - right * (near_width / 2)
    p2 = near_center + right * (near_width / 2)
    p3 = far_center + right * (far_width / 2)
    p4 = far_center - right * (far_width / 2)

    return np.array([p1, p2, p3, p4])

class Robot:
    def __init__(self, x, y, heading):
        self.x = x
        self.y = y
        self.heading = heading

    def update_position(self, x, y, heading):
        self.x = x
        self.y = y
        self.heading = heading

    def get_position(self):
        return self.x, self.y

    def get_heading(self):
        return self.heading

class TrackGeneratorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Track Generator with Robot')
        self.setGeometry(100, 100, 800, 600)
        layout = QVBoxLayout()

        self.track_label = QLabel(self)
        layout.addWidget(self.track_label)

        self.generate_button = QPushButton('Generate', self)
        self.generate_button.clicked.connect(self.generate_new_track)
        layout.addWidget(self.generate_button)

        self.simulation_button = QPushButton('Start Simulation', self)
        self.simulation_button.setCheckable(True)  # Make the button checkable
        self.simulation_button.clicked.connect(self.toggle_simulation)
        layout.addWidget(self.simulation_button)

        self.simRateLabel = QLabel("Simulation Rate (Hz):", self)
        self.simRate = QLineEdit("1.0")
        layout.addWidget(self.simRateLabel)
        layout.addWidget(self.simRate)

        self.figure, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=(12, 6))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        self.robot = None
        self.track_x = None
        self.track_y = None

        self.track_line1 = None
        self.robot_dot1 = None
        self.robot_heading_quiver = None
        self.fov_patch_global = None

        self.track_line2 = None
        self.robot_dot2 = None
        self.fov_patch_local = None

        self.setLayout(layout)
        self.generate_new_track()
        self.current_index = 0
        self.animation = None

    def generate_new_track(self):
        # Generate new track and initialize robot
        self.track_x, self.track_y = generate_smooth_random_track(canvas_size=512, num_points=15, track_width=20, randomness=40, min_curve_angle=120)
        self.initial_x = self.track_x[0]
        self.initial_y = self.track_y[0]
        self.initial_heading = compute_heading(self.track_x[0], self.track_y[0], self.track_x[1], self.track_y[1])
        self.robot = Robot(self.initial_x, self.initial_y, self.initial_heading)

        self.ax1.clear()
        self.ax2.clear()

        # Setup both views
        self.setup_global_view(self.initial_x, self.initial_y, self.initial_heading)
        self.setup_robot_view()

        self.canvas.draw()

    def setup_global_view(self, x, y, heading):
        # Global view setup
        self.track_line1, = self.ax1.plot(self.track_x, self.track_y, color="black", linewidth=2)
        self.robot_dot1 = self.ax1.scatter(x, y, color="blue", s=100)
        self.robot_heading_quiver = self.ax1.quiver(x, y, np.cos(heading), np.sin(heading), color='red', scale=10)

        # Global FOV patch
        fov_coords = get_fov_trapezoid(x, y, heading)
        self.fov_patch_global = Polygon(fov_coords, closed=True, color='orange', alpha=0.3)
        self.ax1.add_patch(self.fov_patch_global)

        self.ax1.set_xlim([min(self.track_x) - 50, max(self.track_x) + 50])
        self.ax1.set_ylim([min(self.track_y) - 50, max(self.track_y) + 50])
        self.ax1.set_aspect('equal', 'box')
        self.ax1.set_title("Global Track View")
        self.ax1.grid(True)

    def setup_robot_view(self):
        # Robot-centered view setup
        transformed = transform_to_robot_view(self.track_x, self.track_y, self.robot.x, self.robot.y, self.robot.heading)
        self.track_line2, = self.ax2.plot(transformed[:, 0], transformed[:, 1], color="red", linewidth=2)
        self.robot_dot2 = self.ax2.scatter(0, 0, color="blue", s=100)

        # Robot-centered FOV patch (always facing upwards in this view)
        self.fov_coords_local = get_fov_trapezoid(0, 0, np.pi / 2, near_width=60, far_width=100, length=60)  # 0° = straight up in this view
        self.fov_patch_local = Polygon(self.fov_coords_local, closed=True, color='orange', alpha=0.3)
        self.ax2.add_patch(self.fov_patch_local)

        # Set up robot-centered view
        self.ax2.set_xlim([-100, 100])
        self.ax2.set_ylim([0, 100])  # Only show what's in front of the robot
        self.ax2.set_aspect('equal', 'box')
        self.ax2.set_title("Robot-Centered View")
        self.ax2.grid(True)
        self.ax2.axhline(0, color='gray', linestyle='--')  # Robot position line
        self.ax2.axvline(0, color='gray', linestyle='--')  # Center line

    def toggle_simulation(self):
        # Toggle simulation state
        if self.simulation_button.isChecked():
            self.simulation_button.setText("Stop Simulation")
            self.start_simulation()
        else:
            self.simulation_button.setText("Start Simulation")
            self.stop_simulation()

    def start_simulation(self):
        self.update_robot_position(0)  # Initialize the robot position
        self.animation = FuncAnimation(
            self.figure, self.update_robot_position,
            frames=np.arange(0, len(self.track_x), 1),
            interval=50
        )

    def stop_simulation(self):
        if self.animation:
            self.animation.event_source.stop()
        self.reset_simulation_state()

    def update_robot_position(self, frame):
        try:
            sim_rate = float(self.simRate.text())
        except ValueError:
            sim_rate = 1.0
        step_size = int(sim_rate) if sim_rate > 0 else 1

        self.current_index += step_size
        if self.current_index >= len(self.track_x):
            self.current_index = 0  # Reset to the start

        x1 = self.track_x[self.current_index - step_size]
        y1 = self.track_y[self.current_index - step_size]
        x2 = self.track_x[self.current_index]
        y2 = self.track_y[self.current_index]

        heading = compute_heading(x1, y1, x2, y2)
        self.robot.update_position(x2, y2, heading)

        # Update global view
        self.robot_dot1.set_offsets([[x2, y2]])
        self.robot_heading_quiver.set_offsets([x2, y2])
        self.robot_heading_quiver.set_UVC(np.cos(heading), np.sin(heading))

        fov_coords = get_fov_trapezoid(x2, y2, heading)
        self.fov_patch_global.set_xy(fov_coords)

        transformed = transform_to_robot_view(self.track_x, self.track_y, x2, y2, heading)
        fov_path = Path(self.fov_patch_local.get_xy())
        valid_transformed = []

        for point in transformed:
            if fov_path.contains_point(point) and 0 < point[1] < 100:
                valid_transformed.append(point)
            else:
                valid_transformed.append([np.nan, np.nan])

        valid_transformed = np.array(valid_transformed)
        if(valid_transformed.size == 0):
            print("Track View Lost")
        self.track_line2.set_data(valid_transformed[:, 0], valid_transformed[:, 1])
        self.canvas.draw_idle()

    def reset_simulation_state(self):
        self.current_index = 0
        self.update_robot_position(0)
        self.ax1.clear()
        self.ax2.clear()
        self.setup_global_view(self.initial_x, self.initial_y, self.initial_heading)
        self.setup_robot_view()
        self.canvas.draw()
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TrackGeneratorApp()
    window.show()
    sys.exit(app.exec())
