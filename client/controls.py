import sys
from PyQt6.QtWidgets import QApplication, QWidget, QDial, QSlider, QLabel, QGridLayout, QPushButton, QFrame, QVBoxLayout, QHBoxLayout, QSplitter
from PyQt6.QtCore import Qt

class Controls(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
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
        pass

class SlidersFrame(QFrame):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
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
        label.setText(f"{label.text().split(':')[0]}: {value}")

class DialsFrame(QFrame):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
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
        label.setText(f"{label.text().split(':')[0]}: {value}")


def main():
    app = QApplication(sys.argv)
    controls = Controls()
    controls.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
