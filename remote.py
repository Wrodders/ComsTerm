
from PyQt6 import QtCore
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QKeyEvent

import sys, math
import numpy as np
from typing import Dict, Tuple, List
from collections import deque

from logger import getmylogger



log = getmylogger(__name__)

class Remote(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        #self.setContentsMargins(0,0,0,0)

        self.joyPad = JoyPad()
        self.speedometer = Speedometer()
        
        self.grid = QGridLayout()
        self.grid.addWidget(self.joyPad, 0,0, 2,2)
        self.grid.addWidget(self.speedometer, 0,2, 2,1)
        self.setLayout(self.grid)

        # Create a QTimer instance
        self.timer = QTimer(self)
        # Connect the timeout signal of the timer to a slot (printVelocities)
        self.timer.timeout.connect(self.printVelocities)
        # Set the interval (milliseconds) for the timer
        self.timer.start(250)  # Print velocities every second

    def printVelocities(self):
        # Retrieve velocities from JoyPad and print them
        lV, wV = self.joyPad.getVel()
        print(f"{lV} {wV}")





class JoyPad(QWidget):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle('Joystick')
        self.workspaceRadius = 80
        self.setFixedSize(self.workspaceRadius * 3, self.workspaceRadius * 3)
        self.center = QPoint(self.workspaceRadius, self.workspaceRadius)
        self.joyRadius = 20
        self.joyPos = self.center
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateVelocities)
        self.timer.start(50)  # Update velocities every 50ms
        self.linVel = 0
        self.angVel = 0


    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setBrush(QBrush(Qt.GlobalColor.black))
        painter.drawEllipse(self.center, self.workspaceRadius, self.workspaceRadius)

        painter.setBrush(QBrush(Qt.GlobalColor.gray))
        painter.drawEllipse(self.joyPos, self.joyRadius, self.joyRadius)

    def mouseMoveEvent(self, event):
        newPos = event.pos()
        distance = QPoint(newPos - self.center).manhattanLength()
        
        # Limit the movement of the joystick within the workspace radius
        if distance <= self.workspaceRadius - self.joyRadius:
            self.joyPos = newPos
        else:
            # Calculate the direction vector towards newPos from the center
            direction = newPos - self.center
            # Calculate the length of the direction vector
            length = distance
            # Normalize the direction vector
            direction.setX(int(direction.x() / length))
            direction.setY(int(direction.y() / length))
            # Scale the direction vector to the workspace radius
            self.joyPos = self.joyPos
        
        self.update()

    def mouseReleaseEvent(self, event):
        self.joyPos = self.center
        self.linVel = 0
        self.angVel = 0
        self.update()

    def updateVelocities(self):

        newPos = self.joyPos
        newX = newPos.x()
        newY = newPos.y()
        # Ensure the joystick position does not exceed the workspace radius

       

        # center coordanates to 0,0
        newX = newX - self.workspaceRadius
        newY = -newY + self.workspaceRadius

        # Normalize joystick's x and y coordinates to the unit circle
        normX = newX / (self.workspaceRadius )
        normY = newY / (self.workspaceRadius )

        # Calculate linear and angular velocities
        linearVelocity = normY
        angularVelocity = normX

        # Apply a scaling factor to the velocities
        linearScale = 0.5  # Example scale value for linear velocity
        angularScale = 0.2  # Example scale value for angular velocity
        linearVelocity *= linearScale
        angularVelocity *= angularScale

        # Apply a low-pass filter to the velocities
        alpha = 0.4
        self.linVel = alpha * linearVelocity + (1 - alpha) * self.linVel
        self.angVel = alpha * angularVelocity + (1 - alpha) * self.angVel

        # Round the filtered velocities to 3 decimal places
        self.linVel = round(self.linVel, 3)
        self.angVel = round(self.angVel, 3)

        # Update the joystick position within the workspace
            

            
        


    def getVel(self):
        return self.linVel, self.angVel
    


class Speedometer(QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setContentsMargins(0,0,0,0)

        self.speedLCD = QLCDNumber()
        self.speedLCD.setMaximumSize(100, 50)
        self.speedLCD.display(0)
        self.speedLabel = QLabel("Speed: m/s")

        self.vBox = QVBoxLayout()
   
        self.vBox.addWidget(self.speedLCD)
        self.vBox.addWidget(self.speedLabel)
        self.setLayout(self.vBox)
    
    def updateSpeed(self, val : float):
        self.speedLCD.display(val)






'''
CLI Application
'''
def parse_command_line_args():
    parser = argparse.ArgumentParser(description="GUI application with different data receivers")
    parser.add_argument('--serial', action='store_true', help='Use serial interface')
    parser.add_argument('--simulated', action='store_true', help='Use simulated interface')
    #parser.add_argument('--zmq', action='store_true', help='Use zmq interface')
    return parser.parse_args()

def main():
    
    app = QApplication(sys.argv)
    gui = Remote()
    gui.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
