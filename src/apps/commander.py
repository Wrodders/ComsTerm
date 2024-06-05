from PyQt6 import QtCore
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen

from common.logger import getmylogger


class Commander(QWidget):
    """Widget for sending commands."""

    cmdSendSig = QtCore.pyqtSignal(str)

    def __init__(self):
        """Constructor method for Commander class."""
        super().__init__()

        self.log = getmylogger(__name__)
        self.initUI()
        
    def initUI(self):
        """Initializes the user interface."""
        self.setContentsMargins(0, 0, 0, 0)
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.console.setAcceptRichText(True)
        self.console.setStyleSheet("background-color: black; color: grey;")

        self.cmdEntry = QLineEdit()
        self.cmdEntry.setMinimumWidth(100)
        self.cmdEntry.setMinimumHeight(25)
        self.cmdEntry.textChanged.connect(self.enableSend)
        self.sendB = QPushButton("Send")
        self.sendB.setMaximumWidth(100)

        self.grid = QGridLayout()
        self.grid.addWidget(self.console, 0, 0, 2, 2)
        self.grid.addWidget(self.cmdEntry, 2, 0)
        self.grid.addWidget(self.sendB, 2, 1)
        self.setLayout(self.grid)

    @QtCore.pyqtSlot(str)
    def _updateData(self, msg: str):
        """Updates the console with new data.

        Args:
            msg (str): The message to be displayed in the console.
        """
        if msg == "":
            return
        if(isinstance(self.console.document, QTextEdit)):
            if self.console.document().lineCount() > 200:
                self.console.clear()

        self.console.append(msg)  # Add data to console 

    def enableSend(self):
        """Enables or disables the send button based on text entry."""
        if self.cmdEntry.text():
            self.sendB.setEnabled(True)
        else: 
            self.sendB.setEnabled(False)


class JoyPad(QWidget):
    """Widget representing a joystick pad."""

    def __init__(self):
        """Constructor method for JoyPad class."""
        super().__init__()

        self.outer_radius = 60
        self.inner_radius = 15
        self.center = QPoint(self.outer_radius, self.outer_radius)
        self.inner_position = QPoint(self.outer_radius, self.outer_radius)

        self.setFixedSize(self.outer_radius * 2, self.outer_radius * 2)

    def paintEvent(self, event):
        """Paint event handler."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw outer circle
        painter.setBrush(QBrush(Qt.GlobalColor.black))
        painter.drawEllipse(self.center, self.outer_radius, self.outer_radius)

        # Draw inner circle
        painter.setBrush(QBrush(Qt.GlobalColor.gray))
        painter.drawEllipse(self.inner_position, self.inner_radius, self.inner_radius)

    def mouseMoveEvent(self, event):
        """Mouse move event handler."""
        new_position = event.pos()

        # Calculate distance from new position to the center
        distance = QPoint(new_position - self.center).manhattanLength()

        # Ensure the new position is within the outer circle
        if distance <= self.outer_radius - self.inner_radius:
            self.inner_position = new_position
            self.update()

    def mouseReleaseEvent(self, event):
        """Mouse release event handler."""
        # Reset inner circle to the center when mouse is released
        self.inner_position = self.center
        self.update()

    def updatePos(self, newPos):
        """Update the position of the inner circle."""
        # Calculate distance from new position to the center
        distance = QPoint(newPos - self.center).manhattanLength()

        # Ensure the new position is within the outer circle
        if distance <= self.outer_radius - self.inner_radius:
            self.inner_position = newPos
            self.update()

    def getVal(self):
        """Get the current position."""
        return self.inner_position

    def keyPressEvent(self, event):
        """Key press event handler."""
        step = 5
        print("A")
        currentPos = self.getVal()
        if event.key() == Qt.Key.Key_W:
            newPos = currentPos + QPoint(0, -step)
            self.updatePos(newPos)
        elif event.key() == Qt.Key.Key_A:
            newPos = currentPos + QPoint(-step, 0)
            self.updatePos(newPos)
        elif event.key() == Qt.Key.Key_S:
            newPos = currentPos + QPoint(0, step)
            self.updatePos(newPos)
        elif event.key() == Qt.Key.Key_D:
            newPos = currentPos + QPoint(step, 0)
            self.updatePos(newPos)


class Speedometer(QWidget):
    """Widget representing a speedometer."""

    def __init__(self):
        """Constructor method for Speedometer class."""
        super().__init__()
        self.initUI()

    def initUI(self):
        """Initializes the user interface."""
        self.setContentsMargins(0, 0, 0, 0)

        self.speedLCD = QLCDNumber()
        self.speedLCD.setMaximumSize(100, 50)
        self.speedLCD.display(0)
        self.speedLabel = QLabel("Speed: m/s")

        self.vBox = QVBoxLayout()
        self.vBox.addWidget(self.speedLCD)
        self.vBox.addWidget(self.speedLabel)
        self.setLayout(self.vBox)

    def updateSpeed(self, val: float):
        """Update the speed value on the LCD display.

        Args:
            val (float): The speed value to be displayed.
        """
        self.speedLCD.display(val)


class Remote(QWidget):
    """Widget representing a remote control interface."""

    def __init__(self):
        """Constructor method for Remote class."""
        super().__init__()
        self.initUI()

    def initUI(self):
        """Initializes the user interface."""
        self.setContentsMargins(0, 0, 0, 0)

        self.joyPad = JoyPad()
        self.speedometer = Speedometer()
        
        self.grid = QGridLayout()
        self.grid.addWidget(self.joyPad, 0, 0, 2, 2)
        self.grid.addWidget(self.speedometer, 0, 2, 2, 1)
        self.setLayout(self.grid)


class ControlFrame(QWidget):
    """Widget representing the main control frame."""

    def __init__(self):
        """Constructor method for ControlFrame class."""
        super().__init__()
        self.initUI()

    def initUI(self):
        """Initializes the user interface."""
        self.setContentsMargins(0, 0, 0, 0)

        self.commander = Commander()
        self.remote = Remote()
        self.tabs = QTabWidget()
        self.tabs.addTab(self.commander, "Commander")
        self.tabs.addTab(self.remote, "Remote")

        self.vBox = QVBoxLayout()
        self.vBox.addWidget(self.tabs)
        self.setLayout(self.vBox)
