from PyQt6 import QtCore
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen
import sys


class Commander(QWidget):
    def __init__(self):
        super().__init__()
        vBox = QVBoxLayout()
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True) 

        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        self.params = []
        paramList = ["WP", "WI", "BP", "BI", "BD", "VP", "VI", "STATE"]
        [self.params.append(ParamReg(name)) for name in paramList]

        [self.scroll_layout.addWidget(w) for w in self.params]

        self.scroll_area.setWidget(self.scroll_content)

        vBox.addWidget(self.scroll_area) 
        self.setLayout(vBox)


class ParamReg(QFrame):
    def __init__(self, paramName: str):
        super().__init__()
        hbox = QHBoxLayout()
        self.setFrameShape(QFrame.Shape.StyledPanel)

        self.label = QLabel(paramName)
        self.value_entry = QLineEdit()
        self.value_entry.setMaximumWidth(250)
        self.get_btn = QPushButton("Get")
        self.get_btn.setMaximumWidth(50)
        self.get_btn.clicked.connect(self.get_handle)
        self.set_btn = QPushButton("Set")
        self.set_btn.setMaximumWidth(50)
        self.set_btn.clicked.connect(self.set_handle)

        self.setLayout(hbox)
        hbox.addWidget(self.label)
        hbox.addWidget(self.value_entry)
        hbox.addWidget(self.get_btn)
        hbox.addWidget(self.set_btn)

    def set_handle(self):
        pass

    def get_handle(self):
        pass


