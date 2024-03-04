import sys
from PyQt6 import QtCore
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *

from dataclasses import dataclass

from device import Cmd, CmdMap

from collections import deque

class Slider(QWidget):
    def __init__(self, name, min_val=0, max_val=100, float_mode=False):
        super().__init__()
        self.name = name
        self.min_val = min_val
        self.max_val = max_val
        self.float_mode = float_mode
        self.onHold = False
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.label = QLabel(self.name + ': 0')
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        self.slider.setSingleStep(1)
        self.slider.valueChanged.connect(self.onValueChanged)

        self.input_entry = QLineEdit()
        self.input_entry.returnPressed.connect(self.onInputValueChanged)
        self.input_entry.setMaximumWidth(150)

        self.hold_button = QPushButton("Hold")
        self.hold_button.setCheckable(True)
        self.hold_button.setChecked(True)
        self.hold_button.clicked.connect(self.toggleHold)
        self.hold_button.setMaximumWidth(150)

        layout.addWidget(self.label)
        layout.addWidget(self.slider)
        layout.addWidget(self.input_entry)
        layout.addWidget(self.hold_button)

        self.setLayout(layout)

    def toggleHold(self):
        self.onHold = self.hold_button.isChecked()
        self.input_entry.setFocus()


    def onValueChanged(self):
        value = int(self.slider.value() * (self.max_val - self.min_val) / 100 + self.min_val)
        if self.float_mode:
            value *=0.01
            value = round(value, 2)

        self.label.setText(f'{self.name}: {value}')
        self.input_entry.setText(f'{value}')
        if(self.onHold):
            # Emit signal for value change
            self.valueChanged.emit(self.name, value)

    def onInputValueChanged(self):
        text = self.input_entry.text()
        try:
         
            value = float(text)

            value = max(self.min_val, min(self.max_val, value))
            print(value)
            scaled_value = int((value - self.min_val) / (self.max_val - self.min_val) * 100)
            self.slider.setValue(scaled_value)
            self.onValueChanged()
        except ValueError:
            pass

    # Define a signal for value change
    valueChanged = QtCore.pyqtSignal(str, float)



class ConfigDialog(QDialog):
    def __init__(self, sliders, parent=None):
        super().__init__(parent)
        self.sliders = sliders
    

        self.setWindowTitle('Configure Sliders')

        layout = QVBoxLayout()

        # Combo box for selecting sliders
        self.slider_combo = QComboBox()
        for slider in sliders:
            self.slider_combo.addItem(slider.name)

        # Combo box for selecting data mode
        name = self.slider_combo.currentData()


        self.data_mode_combo = QComboBox()
        self.data_mode_combo.addItems(['int', 'float'])
        self.data_mode_combo.currentIndexChanged.connect(self.updateFloatMode)
     

        # Form layout for min and max values
        self.form_layout = QFormLayout()

        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addWidget(self.slider_combo)
        layout.addWidget(self.data_mode_combo)
        layout.addLayout(self.form_layout)
        layout.addWidget(button_box)

        self.setLayout(layout)

        # Connect combo box change to update form layout
        self.slider_combo.currentIndexChanged.connect(self.updateFormLayout)

        # Initialize form layout
        self.updateFormLayout(0)

    def updateFloatMode(self, index):
        float_mode = (self.data_mode_combo.currentText() == 'float')
        for slider in self.sliders:
            slider.float_mode = float_mode

    def updateFormLayout(self, index):
        # Clear previous widgets from form layout
        for i in reversed(range(self.form_layout.count())):
            widget = self.form_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        # Get selected slider
        slider = self.sliders[index]

        # Add min and max value entries to form layout
        min_entry = QLineEdit(str(slider.min_val))
        max_entry = QLineEdit(str(slider.max_val))

        self.form_layout.addRow('Min Value:', min_entry)
        self.form_layout.addRow('Max Value:', max_entry)

        # Connect text changed signals to update slider's min and max values with validation
        min_entry.textChanged.connect(lambda text, entry=min_entry, slider=slider: self.updateSliderMin(entry, slider))
        max_entry.textChanged.connect(lambda text, entry=max_entry, slider=slider: self.updateSliderMax(entry, slider))

    def updateSliderMin(self, entry, slider):
        try:
            min_val = int(entry.text())
            if slider.float_mode :
                min_val *=100
            slider.slider.setMinimum(min_val)
            
            
        except ValueError:
            pass  # Ignore non-numeric input

    def updateSliderMax(self, entry, slider):
        try:
            max_val = int(entry.text())
            slider.slider.setSingleStep(1)
            if slider.float_mode :
                max_val *=100
                slider.slider.setSingleStep(0.01)
            slider.slider.setMaximum(max_val)
        except ValueError:
            pass  # Ignore non-numeric input


class ControlDash(QWidget):
    def __init__(self):
        super().__init__()

        cmds = [
            Cmd(ID='0', name="ID", fmt=""),
            Cmd(ID='1', name="RESET", fmt="d:d"),
            Cmd(ID='2', name="Alpha", fmt="f"),
            Cmd(ID='3', name="Kp", fmt="f"),
            Cmd(ID='4', name="Ki", fmt="f"),
            Cmd(ID='5', name="Trgt Vel", fmt="f")
        ]

        self.cmdMap = CmdMap(cmds)

        self.initUI()

    def initUI(self):
        self.setWindowTitle('Control Dashboard')

        layout = QVBoxLayout()
        self.alpha = Slider('Alpha')
        self.ki = Slider('Ki')
        self.kp = Slider('Kp')
        self.trgtVel = Slider('Target Velocity')

        # List of sliders
        self.sliders = [self.alpha, self.ki, self.kp, self.trgtVel]

        layout.addWidget(self.alpha)
        layout.addWidget(self.ki)
        layout.addWidget(self.kp)
        layout.addWidget(self.trgtVel)

        # Config button
        config_button = QPushButton("Configure Sliders")
        config_button.clicked.connect(self.openConfigDialog)
        layout.addWidget(config_button)

        self.setLayout(layout)

        # Connect slider signals to a method for processing changes
        self.alpha.valueChanged.connect(self.processChange)
        self.ki.valueChanged.connect(self.processChange)
        self.kp.valueChanged.connect(self.processChange)
        self.trgtVel.valueChanged.connect(self.processChange)

    def processChange(self, name, value):
        # Here, you can process the change as desired
        print(f"Received change: {name} -> {value}")

    def openConfigDialog(self):
        # Set all sliders on hold
        for slider in self.sliders:
            slider.toggleHold()

        dialog = ConfigDialog(self.sliders, parent=self)
        dialog.exec()



if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = ControlDash()
    widget.show()
    sys.exit(app.exec())
