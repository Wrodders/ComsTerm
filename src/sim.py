import sys
import numpy as np
import cv2
from scipy.interpolate import splprep, splev
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QHBoxLayout, QGraphicsView, QGraphicsScene
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

def ensure_minimum_curve_radius(points, min_angle_deg=45):
    """Adjusts control points to ensure no angle between segments is sharper than min_angle_deg."""
    min_angle_rad = np.deg2rad(min_angle_deg)
    adjusted_points = [points[0]]  # Start with the first point
    
    for i in range(1, len(points) - 1):
        prev_point = adjusted_points[-1]
        current_point = points[i]
        next_point = points[(i + 1) % len(points)]
        
        # Vectors for the segments
        vec1 = prev_point - current_point
        vec2 = next_point - current_point
        
        # Calculate the angle between vec1 and vec2
        angle = np.arccos(
            np.clip(
                np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)), 
                -1.0, 
                1.0
            )
        )
        
        if angle < min_angle_rad:
            # Adjust the current point to smooth the curve
            mid_point = (prev_point + next_point) / 2
            adjusted_points.append(mid_point)
        else:
            adjusted_points.append(current_point)
    
    # Close the loop
    adjusted_points.append(adjusted_points[0])
    return np.array(adjusted_points)

def generate_smooth_random_track(canvas_size=512, num_points=20, track_width=15, margin=50, randomness=30, min_curve_angle=45):
    # Generate rough spiral control points
    angles = np.linspace(0, 2 * np.pi, num_points, endpoint=False)
    radius = np.linspace(margin, canvas_size // 2 - margin, num_points)
    
    # Add small random perturbations
    random_offsets = np.random.uniform(-randomness, randomness, size=(num_points, 2))
    control_points = np.array([
        canvas_size // 2 + radius * np.cos(angles),
        canvas_size // 2 + radius * np.sin(angles)
    ]).T + random_offsets
    
    # Adjust control points to enforce minimum curve radius
    control_points = ensure_minimum_curve_radius(control_points, min_angle_deg=min_curve_angle)
    
    # Smooth and close the loop using spline interpolation
    tck, u = splprep([control_points[:, 0], control_points[:, 1]], s=0, per=True)
    u_fine = np.linspace(0, 1, 1000)
    x_fine, y_fine = splev(u_fine, tck)
    
    return x_fine, y_fine

def transform_to_robot_view(x_fine, y_fine, robot_x, robot_y, robot_heading, fov_range=100, view_angle=np.pi/2):
    """Transform track points into the robot's point of view (top-down perspective)."""
    
    # Compute the relative position of each track point to the robot's position
    relative_x = x_fine - robot_x
    relative_y = y_fine - robot_y
    
    # Rotate the points based on the robot's heading (counter-clockwise rotation)
    rotation_matrix = np.array([[np.cos(robot_heading), -np.sin(robot_heading)], 
                                [np.sin(robot_heading), np.cos(robot_heading)]])
    rotated_points = np.dot(np.vstack([relative_x, relative_y]).T, rotation_matrix.T)
    
    # Only keep points within the robot's field of view
    view_mask = np.abs(rotated_points[:, 1]) < fov_range
    return rotated_points[view_mask]

class Robot:
    def __init__(self, x, y, heading):
        self.x = x
        self.y = y
        self.heading = heading  # Angle in radians
    
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
        
        # Create a layout and add widgets
        layout = QVBoxLayout()
        
        self.track_label = QLabel(self)
        layout.addWidget(self.track_label)
        
        self.generate_button = QPushButton('Generate', self)
        self.generate_button.clicked.connect(self.generate_new_track)
        layout.addWidget(self.generate_button)
        
        # Button to start the simulation
        self.start_simulation_button = QPushButton('Start Simulation', self)
        self.start_simulation_button.clicked.connect(self.start_simulation)
        layout.addWidget(self.start_simulation_button)
        
        # Matplotlib plot setup for track visualization
        self.figure, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=(12, 6))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        self.robot = None
        self.track_x = None
        self.track_y = None
        
        self.setLayout(layout)
        
        self.generate_new_track()

    def generate_new_track(self):
        # Generate a new track
        track_x, track_y = generate_smooth_random_track(canvas_size=512, num_points=15, track_width=20, randomness=40, min_curve_angle=45)
        
        # Set the initial robot position (lowest y-coordinate of the track)
        min_y_index = np.argmin(track_y)
        initial_x = track_x[min_y_index]
        initial_y = track_y[min_y_index]
        
        # Robot heading is left (pointing along negative x-axis)
        initial_heading = np.pi
        
        self.robot = Robot(initial_x, initial_y, initial_heading)
        
        # Update the track and robot's position on the plot
        self.track_x = track_x
        self.track_y = track_y
        
        # Plot the track and robot on the first axis (track visualization)
        self.ax1.clear()
        self.ax1.plot(self.track_x, self.track_y, label="Track", color="black", linewidth=2)
        self.ax1.scatter(self.robot.x, self.robot.y, color="blue", s=100, label="Robot")
        self.ax1.quiver(self.robot.x, self.robot.y, np.cos(self.robot.heading), np.sin(self.robot.heading), angles='xy', scale_units='xy', scale=1, color='blue', width=0.01)
        
        self.ax1.set_xlim([min(self.track_x) - 50, max(self.track_x) + 50])
        self.ax1.set_ylim([min(self.track_y) - 50, max(self.track_y) + 50])
        self.ax1.set_aspect('equal', 'box')
        self.ax1.set_title("Track with Robot")
        self.ax1.legend(loc="upper left")
        
        # Transform track for robot's point of view and plot on the second axis
        transformed_track = transform_to_robot_view(self.track_x, self.track_y, self.robot.x, self.robot.y, self.robot.heading)
        self.ax2.clear()
        self.ax2.plot(transformed_track[:, 0], transformed_track[:, 1], label="Track", color="black", linewidth=2)
        self.ax2.scatter(0, 0, color="blue", s=100, label="Robot")
        self.ax2.set_xlim([-100, 100])
        self.ax2.set_ylim([-100, 100])
        self.ax2.set_aspect('equal', 'box')
        self.ax2.set_title("Robot's View")
        self.ax2.legend(loc="upper left")
        
        self.canvas.draw()

    def start_simulation(self):
        # Set up the animation to animate the robot
        self.animation = FuncAnimation(self.figure, self.update_robot_position, frames=np.linspace(0, len(self.track_x) - 1, len(self.track_x)), interval=50, repeat=False)
    
    def update_robot_position(self, frame):
        # Get the current position on the track
        x = self.track_x[int(frame)]
        y = self.track_y[int(frame)]
        
        # Update robot's position and heading (for simplicity, assuming the robot follows the track smoothly)
        self.robot.update_position(x, y, self.robot.heading)
        
        # Update the first plot (track plot)
        self.ax1.clear()
        self.ax1.plot(self.track_x, self.track_y, label="Track", color="black", linewidth=2)
        self.ax1.scatter(self.robot.x, self.robot.y, color="blue", s=100, label="Robot")
        self.ax1.quiver(self.robot.x, self.robot.y, np.cos(self.robot.heading), np.sin(self.robot.heading), angles='xy', scale_units='xy', scale=1, color='blue', width=0.01)
        
        self.ax1.set_xlim([min(self.track_x) - 50, max(self.track_x) + 50])
        self.ax1.set_ylim([min(self.track_y) - 50, max(self.track_y) + 50])
        self.ax1.set_aspect('equal', 'box')
        self.ax1.set_title("Track with Robot")
        self.ax1.legend(loc="upper left")
        
        # Transform the track for robot's view and update the second plot
        transformed_track = transform_to_robot_view(self.track_x, self.track_y, self.robot.x, self.robot.y, self.robot.heading)
        self.ax2.clear()
        self.ax2.plot(transformed_track[:, 0], transformed_track[:, 1], label="Track", color="black", linewidth=2)
        self.ax2.scatter(0, 0, color="blue", s=100, label="Robot")
        self.ax2.set_xlim([-100, 100])
        self.ax2.set_ylim([-100, 100])
        self.ax2.set_aspect('equal', 'box')
        self.ax2.set_title("Robot's View")
        self.ax2.legend(loc="upper left")
        
        self.canvas.draw()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TrackGeneratorApp()
    window.show()
    sys.exit(app.exec())
