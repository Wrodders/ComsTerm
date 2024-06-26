from PyQt6 import QtCore
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *

from common.messages import MsgFrame, TopicMap


class Controls(QWidget):
    """Widget representing control panel with sliders and dials."""
    
    def __init__(self):
        """Constructor method for Controls class."""
        super().__init__()

        self.initUI()

    def initUI(self):
        """Initializes the user interface."""
        self.setFixedSize(500, 300)

        # Splitter with Frames
        splitter = QSplitter()

        sliders_frame = SlidersFrame()
        dials_frame = DialsFrame()

        splitter.addWidget(sliders_frame)
        splitter.addWidget(dials_frame)

        # Set the sizes of the sections
        sizes = [3 * self.height() // 4, self.height() // 4]
        splitter.setSizes(sizes)

        self.configButton = QPushButton("Config")
        self.configButton.setMaximumWidth(150)
        self.configButton.clicked.connect(self.configure)

        layout = QVBoxLayout()
        layout.addWidget(splitter)
        layout.addWidget(self.configButton)
        self.setLayout(layout)


    def configure(self):
        """Opens configuration dialog."""
        pass



class CmdBtnFrame(QWidget):
    cmdBtnClick = pyqtSignal(str)  # Define custom signal to emit button text

    def __init__(self, cmdMap : TopicMap):
        super().__init__()
        self.setWindowTitle("Device Commands")
        self.setGeometry(100, 100, 200, 100)
        self.setMaximumWidth(200)
        self.vBox = QVBoxLayout()
        self.cmdButtons = [QPushButton(cmd.name) for cmd in cmdMap.getTopics()]

        for btn in self.cmdButtons:
            btn.setMaximumWidth(100)
            btn.clicked.connect(lambda checked, name=btn.text(): self.cmdBtnClick.emit(name))  # Connect button clicked signal to emit custom signal with button text

        [self.vBox.addWidget(btn) for btn in self.cmdButtons]
        self.setLayout(self.vBox)





class SlidersFrame(QFrame):
    """Widget representing frame with sliders."""
    
    def __init__(self):
        """Constructor method for SlidersFrame class."""
        super().__init__()
        self.initUI()

    def initUI(self):
        """Initializes the user interface."""
        layout = QVBoxLayout()

        # Sliders
        self.slider1 = QSlider(Qt.Orientation.Horizontal)
        self.slider2 = QSlider(Qt.Orientation.Horizontal)
        self.slider3 = QSlider(Qt.Orientation.Horizontal)

        self.slider1.setMinimum(0)
        self.slider1.setMaximum(100)
        self.slider2.setMinimum(0)
        self.slider2.setMaximum(100)
        self.slider3.setMinimum(0)
        self.slider3.setMaximum(100)

        self.label1 = QLabel("Slider 1: 0")
        self.label2 = QLabel("Slider 2: 0")
        self.label3 = QLabel("Slider 3: 0")

        layout.addWidget(self.label1)
        layout.addWidget(self.slider1)
        layout.addWidget(self.label2)
        layout.addWidget(self.slider2)
        layout.addWidget(self.label3)
        layout.addWidget(self.slider3)

        self.slider1.valueChanged.connect(lambda value: self.updateLabel(self.label1, value))
        self.slider2.valueChanged.connect(lambda value: self.updateLabel(self.label2, value))
        self.slider3.valueChanged.connect(lambda value: self.updateLabel(self.label3, value))

        self.setLayout(layout)

    def updateLabel(self, label, value):
        """Updates label text with slider value."""
        label.setText(f"{label.text().split(':')[0]}: {value}")

class DialsFrame(QFrame):
    """Widget representing frame with dials."""
    
    def __init__(self):
        """Constructor method for DialsFrame class."""
        super().__init__()
        self.initUI()

    def initUI(self):
        """Initializes the user interface."""
        layout = QVBoxLayout()

        # Dials
        self.dial1 = QDial()
        self.dial2 = QDial()

        self.dial1.setMinimum(0)
        self.dial1.setMaximum(100)
        self.dial2.setMinimum(0)
        self.dial2.setMaximum(100)

        self.label1 = QLabel("Dial 1: 0")
        self.label2 = QLabel("Dial 2: 0")

        layout.addWidget(self.label1)
        layout.addWidget(self.dial1)
        layout.addWidget(self.label2)
        layout.addWidget(self.dial2)

        self.dial1.valueChanged.connect(lambda value: self.updateLabel(self.label1, value))
        self.dial2.valueChanged.connect(lambda value: self.updateLabel(self.label2, value))

        self.setLayout(layout)

    def updateLabel(self, label, value):
        """Updates label text with dial value."""
        label.setText(f"{label.text().split(':')[0]}: {value}")


