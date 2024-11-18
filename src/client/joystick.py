from math import hypot

from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
import sys



from math import hypot

from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
import sys

class JoystickButton(QPushButton):
    sigStateChanged = pyqtSignal(float, float)  # x, y

    def __init__(self, parent=None):
        QPushButton.__init__(self, parent)
        self.radius = 75  # Set joystick radius
        self.setCheckable(True)
        self.change_counter = 0
        self.update_threshold = 10  # Emit state every 10th change
        self.state = None
        self.setState(0, 0)
        self.setFixedWidth(2 * self.radius)
        self.setFixedHeight(2 * self.radius)


        # Last position before updating
        self.last_position = QPoint(0, 0)

        # Counter to track number of state changes before emitting
      
     

        # Make the button circular by setting the mask
        self.setCircularMask()

    def setCircularMask(self):
        # Create a circular mask based on the button's size
        circle_region = QRegion(self.rect(), QRegion.RegionType.Ellipse)
        self.setMask(circle_region)

    def mousePressEvent(self, ev):
        self.setChecked(True)
        lpos = ev.position() if hasattr(ev, 'position') else ev.localPos()
        self.pressPos = lpos
        ev.accept()

    def mouseMoveEvent(self, ev):
        lpos = ev.position() if hasattr(ev, 'position') else ev.localPos()
        dif = lpos - self.pressPos
        self.setState(dif.x(), -dif.y())
           
    def mouseReleaseEvent(self, ev):
        self.setChecked(False)
        self.setState(0, 0)
        self.change_counter = 0  # Reset counter on release

    def wheelEvent(self, ev):
        ev.accept()

    def doubleClickEvent(self, ev):
        ev.accept()

    def getState(self):
        return self.state

    def setState(self, *xy):
        xy = list(xy)
        d = hypot(xy[0], xy[1])  # length
        nxy = [0, 0]
        for i in [0, 1]:
            if xy[i] == 0:
                nxy[i] = 0
            else:
                nxy[i] = xy[i] / d

        if d > self.radius:
            d = self.radius
        d = (d / self.radius) ** 2
        xy = [nxy[0] * d, nxy[1] * d]

        w2 = self.width() / 2
        h2 = self.height() / 2
        self.spotPos = QPoint(
            int(w2 * (1 + xy[0])),
            int(h2 * (1 - xy[1]))
        )
        self.update()

        if self.state == xy:
            return
        self.state = xy
        # Increment the counter for each change
        self.change_counter += 1

        # Emit state every 10th change
     
        if (self.change_counter >= self.update_threshold) or self.state == [0,0]:
            self.sigStateChanged.emit(self.state[0], self.state[1])
            self.change_counter = 0  # Reset the counter after emitting

    def paintEvent(self, ev):
        super().paintEvent(ev)
        p = QPainter(self)

        # Draw the background circle
        p.setBrush(QBrush(QColor(211, 211, 211)))  # Light gray
        p.setPen(Qt.PenStyle.SolidLine)  # No border
        center = QPoint(self.width() // 2, self.height() // 2)
        p.drawEllipse(center, self.radius, self.radius)

        # Draw the moving spot
        p.setBrush(QBrush(QColor(0, 0, 0)))  # Black
        p.drawEllipse(self.spotPos.x() - 10,
                      self.spotPos.y() - 10,
                      20,
                      20)

    def resizeEvent(self, ev):
        self.setState(*self.state)
        self.setCircularMask()  # Reapply circular mask on resize
        super().resizeEvent(ev)
