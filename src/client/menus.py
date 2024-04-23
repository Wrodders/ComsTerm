from PyQt6 import QtCore
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *

from common.utils import scanUSB

from core.device import Devices, DeviceInfo
from core.SerialDevice import SerialInfo
from core.SimulatedDevice import SimInfo
from core.ZmqDevice import ZmqInfo
from common.zmqutils import Transport, Endpoint


class SettingsMenu(QFrame):

    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        pass

"""
New Device Config UI
"""

class DeviceConfig(QWidget):
    def __init__(self):
        super(DeviceConfig, self).__init__()
        self.grid = QGridLayout()
        self.setMinimumWidth(350)

        self.serialConfig = SerialConfig()
        self.simConfig = SimConfig()
        self.zmqConfig = ZMQConfig()
        self.tcpConfig = TCPConfig()
        self.udpConfig = UDPConfig()
        
        self.stackLayout = QStackedLayout()
        self.stackLayout.addWidget(self.serialConfig)
        self.stackLayout.addWidget(self.zmqConfig)
        self.stackLayout.addWidget(self.tcpConfig)
        self.stackLayout.addWidget(self.udpConfig)
        self.connectBtn = QPushButton("Connect")
        self.connectBtn.setMaximumWidth(350)
        self.disconnectBtn = QPushButton("Disconnect")
        self.disconnectBtn.setMaximumWidth(350)
        self.conDeviceCB = QComboBox()
        self.conDeviceCB.setMaximumWidth(350)
        self.conDeviceCB.currentIndexChanged.connect(self.updateDeviceStack)
        self.conDeviceCB.addItems(Devices._member_names_)

        self.grid.addWidget(self.conDeviceCB, 0,0, 1, 2)
        self.grid.addLayout(self.stackLayout, 1, 0 , 2, 2)
        self.grid.addWidget(self.connectBtn, 3, 0, 1,1)
        self.grid.addWidget(self.disconnectBtn, 3, 1, 1,1)
        self.setLayout(self.grid)

    def updateDeviceStack(self):
        index = self.conDeviceCB.currentIndex()
        self.stackLayout.setCurrentIndex(index)

    def getValues(self) -> DeviceInfo:

        if self.conDeviceCB.currentText() == Devices.SERIAL.name:
            port = self.serialConfig.portCB.currentText()
            baud = self.serialConfig.baudRate.currentText()
            devInfo = SerialInfo(name="1", port=port, baudRate=int(baud))

        elif self.conDeviceCB.currentText() == Devices.SIM.name:
            rate = self.simConfig.rateCB.currentText()
            devInfo = SimInfo(rate=int(rate))

        elif self.conDeviceCB.currentText() == Devices.ZMQ.name:
            tp = self.zmqConfig.transportCB.currentText()
            ep = self.zmqConfig.endpointCB.currentText()
           
            devInfo = ZmqInfo(transport=tp, endpoint=ep)

        return devInfo



class SerialConfig(QFrame):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setMaximumWidth(350)
        self.setFrameShape(self.Shape.StyledPanel)
        self.setFrameShadow(self.Shadow.Plain)
        layout = QGridLayout()
        
        layout.addWidget(QLabel("Serial Port:"), 0, 0)
        self.portCB = QComboBox()
        self.portCB.addItems(scanUSB("usb"))
        self.baudRate = QComboBox()
        self.baudRate.addItems(["9600", "115200"])
        self.dataBits = QComboBox()
        self.dataBits.addItems(["8", "7", "6", "5"])  
        self.stopBits = QComboBox()
        self.stopBits.addItems(["1", "1.5", "2"])  
        self.parity = QComboBox()
        self.parity.addItems(["None", "Even", "Odd", "Mark", "Space"])
        self.rts_cts = QCheckBox()
        self.dtr_dsr = QCheckBox()
        
        layout.addWidget(self.portCB, 0, 1)
        layout.addWidget(QLabel("Baud Rate:"), 1, 0)
        layout.addWidget(self.baudRate, 1, 1)
        layout.addWidget(QLabel("Data Bits:"), 2, 0)
        layout.addWidget(self.dataBits, 2, 1)
        layout.addWidget(QLabel("Stop Bits:"), 3, 0)
        layout.addWidget(self.stopBits, 3, 1)
        layout.addWidget(QLabel("Parity:"), 4, 0)
        layout.addWidget(self.parity, 4, 1)
        layout.addWidget(QLabel("RTS/CTS:"), 5, 0)
        layout.addWidget(self.rts_cts, 5, 1)
        layout.addWidget(QLabel("DTR/DSR:"), 6, 0)
        layout.addWidget(self.dtr_dsr, 6, 1)

        self.setLayout(layout)

    def getPort(self)-> str:
        return self.portCB.currentText()
    
    def getBaud(self)-> int:
        return int(self.baudRate.currentText())

class TCPConfig(QFrame):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setMaximumWidth(350)
        self.setFrameShape(self.Shape.StyledPanel)
        self.setFrameShadow(self.Shadow.Plain)
        layout = QGridLayout()
        layout.addWidget(QLabel("IP Address:"), 0, 0)
        layout.addWidget(QComboBox(), 0, 1)
        layout.addWidget(QLabel("Port:"), 1, 0)
        layout.addWidget(QComboBox(), 1, 1)

        self.setLayout(layout)

class UDPConfig(QFrame):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setMaximumWidth(350)
        self.setFrameShape(self.Shape.StyledPanel)
        self.setFrameShadow(self.Shadow.Plain)
        layout = QGridLayout()
        layout.addWidget(QLabel("I Address:"), 0, 0)
        layout.addWidget(QComboBox(), 0, 1)
        layout.addWidget(QLabel("Port:"), 1, 0)
        layout.addWidget(QComboBox(), 1, 1)

        self.setLayout(layout)

class ZMQConfig(QFrame):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setMaximumWidth(350)
        self.setFrameShape(self.Shape.StyledPanel)
        self.setFrameShadow(self.Shadow.Plain)
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Socket Endpoint:"))
        self.transportCB = QComboBox()
        self.transportCB.addItems(Transport._member_names_)
        self.endpointCB = QComboBox()
        self.endpointCB.addItems(Endpoint._member_names_)
        layout.addWidget(self.transportCB)
        layout.addWidget(self.endpointCB)
        self.setLayout(layout)


class SimConfig(QFrame):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setMaximumWidth(350)
        self.setFrameShape(self.Shape.StyledPanel)
        self.setFrameShadow(self.Shadow.Plain)
        self.rateCB = QComboBox()
        self.rateCB.addItems(["1", "10", "100"])
        layout = QGridLayout()
        layout.addWidget(QLabel("Rate:"), 0, 0)
        layout.addWidget(self.rateCB, 1, 1)

        self.setLayout(layout)