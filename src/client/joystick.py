from math import hypot
from PyQt6 import QtCore 
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

from multiprocessing import Process, Pipe
from common.messages import ParameterMap 
from core.commander import ZMQCommander
from core.ps4Joy import ps4_joystick_handler

class JoystickApp(QFrame):
    joystickDataChanged = QtCore.pyqtSignal(str, str, float)  # nodeName, paramName, value
    def __init__(self, cmdr: ZMQCommander):
        super().__init__()
        self.cmdr = cmdr

        self.initUI()
        self.ps4_process = None
        self.ps4_pipe_parent = None
        self.ps4_timer = QTimer()
        self.ps4_timer.timeout.connect(self.readPs4Data) # Read PS4 data every 50ms
        # Connect App Signals to Commander
        self.joystickDataChanged.connect(self.sendJoystickCmd)

    def sendJoystickCmd(self, nodeName: str , paramName: str, value : float):
        self.cmdr.sendSetCmd(nodeName, paramName, str(value))

    def initUI(self):
        print("Init Joystick App")
        grid = QGridLayout()
        self.setContentsMargins(0,0,0,0)
        self.joyBtn = JoystickButton()
        self.usePS4_ck = QPushButton("Use PS4 Controller")
        self.usePS4_ck.setCheckable(True)
        self.usePS4_ck.clicked.connect(self.handlePs4)
        # Node Id Config
        self.nodeIdCombo = QComboBox() # Node Id available
        self.nodeIdCombo.addItems([nodeId for nodeId in self.cmdr.paramRegMap.nodes])
        self.nodeIdCombo.setMinimumWidth(120)
        # X Param Config
        self.xMult = QLineEdit("1.0")
        self.xMult.setMaximumWidth(50)
        self.xPrmCombo = QComboBox()
        self.xPrmCombo.addItems([name for name in self.cmdr.paramRegMap.getClientParameters(self.nodeIdCombo.currentText())])
        self.xVal_lbl = QLabel("0")
        self.xLayout = QHBoxLayout()
        self.xLayout.addWidget(QLabel("X Param:"))
        self.xLayout.addWidget(self.xMult)
        self.xLayout.addWidget(self.xPrmCombo)
        self.xLayout.addStretch(1)
        self.xLayout.addWidget(self.xVal_lbl)
        # Y Param Config
        self.yMult = QLineEdit("1.0")
        self.yMult.setMaximumWidth(50)
        self.yPrmCombo = QComboBox()
        self.yPrmCombo.addItems([name for name in self.cmdr.paramRegMap.getClientParameters(self.nodeIdCombo.currentText())])
        self.yVal_lbl = QLabel("0")
        self.yLayout = QHBoxLayout()
        self.yLayout.addWidget(QLabel("Y Param:"))
        self.yLayout.addWidget(self.yMult)
        self.yLayout.addWidget(self.yPrmCombo)
        self.yLayout.addStretch(1)
        self.yLayout.addWidget(self.yVal_lbl)

        configLabelLayout = QHBoxLayout()
        configLabelLayout.addWidget(QLabel("Axis"))
        configLabelLayout.addWidget(QLabel("Multiplier"))
        configLabelLayout.addWidget(QLabel("Parameter"))
        configLabelLayout.addWidget(QLabel("Value"))


        grid.addWidget(self.joyBtn,0,1,1,5)
        grid.addWidget(self.usePS4_ck,1,1,1,3)
        grid.addWidget(QLabel("Node Id:"),2,1,1,1)
        grid.addWidget(self.nodeIdCombo,2,2,1,1)
        grid.addLayout(configLabelLayout,3,0,1,4)
        grid.addLayout(self.xLayout,4,0, 1,4)
        grid.addLayout(self.yLayout,5,0,1,4 )

        self.setLayout(grid)
       
        # Connect Signals
        self.joyBtn.sigStateChanged.connect(self.handleJoy)
        # connect node id change to refresh param combo
        self.nodeIdCombo.currentTextChanged.connect(self.updateParamCombo)


    def closeEvent(self, event):
        self.stopPs4Process()
        event.accept()

    def updateParamCombo(self, nodeId):
        self.xPrmCombo.clear()
        self.yPrmCombo.clear()
        self.xPrmCombo.addItems([name for name in self.cmdr.paramRegMap.getClientParameters(nodeId)])
        self.yPrmCombo.addItems([name for name in self.cmdr.paramRegMap.getClientParameters(nodeId)])

    @QtCore.pyqtSlot(float,float)
    def handleJoy(self,joyX,joyY):
        # Update the parameter values based on the joystick position
        if(not self.usePS4_ck.isChecked() ):
            nodeName = self.nodeIdCombo.currentText()
            xVal = round(joyX/2,3)
            xName = self.xPrmCombo.currentText()
            yVal = round(joyY/2,3)
            yName = self.yPrmCombo.currentText()
            self.xVal_lbl.setText(str(xVal))
            self.yVal_lbl.setText(str(yVal))
            self.joystickDataChanged.emit(nodeName, xName, xVal) 
            self.joystickDataChanged.emit(nodeName, yName, yVal)

    def handlePs4(self):
        # Start or stop the PS4 joystick process
        if self.usePS4_ck.isChecked():
            self.startPs4Process()
        else:
            self.stopPs4Process()

    def startPs4Process(self):
        """Start the PS4 joystick subprocess."""
        self.ps4_pipe_parent, ps4_pipe_child = Pipe()
        self.ps4_process = Process(target=ps4_joystick_handler, args=(ps4_pipe_child,))
        self.ps4_process.start()
        self.ps4_timer.start(50)  # Poll joystick data every 50ms

    def stopPs4Process(self):
        """Stop the PS4 joystick process."""
        if self.ps4_process and self.ps4_process.is_alive():
            self.ps4_pipe_parent.send("STOP")   # Send stop signal
            self.ps4_process.join(timeout=1)  # Wait for graceful exit

        if self.ps4_process:
            if self.ps4_process.is_alive():  
                print("Forcing PS4 process termination...")
                self.ps4_process.terminate()  # Force terminate
                self.ps4_process.join()  # Ensure complete termination

        self.ps4_process = None
        self.ps4_pipe_parent = None

    def readPs4Data(self):
        """Read data from the PS4 joystick subprocess."""
        if self.ps4_pipe_parent and self.ps4_pipe_parent.poll():
            data = self.ps4_pipe_parent.recv()
            if "error" in data:
                print(f"Error: {data['error']}")
                self.usePS4_ck.setChecked(False)
                self.stopPs4Process()
            elif "status" in data:
                print(f"Joystick Status: {data['status']} - {data['name']}")
            else:
                rx = data.get("rx", 0)
                ry = data.get("ry", 0)
                xName = self.xPrmCombo.currentText()
                yName = self.yPrmCombo.currentText()
                self.xVal_lbl.setText(str(rx))
                self.yVal_lbl.setText(str(ry))
                self.joystickDataChanged.emit(xName, rx) # Emit the joystick data
                self.joystickDataChanged.emit(yName, ry)

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
