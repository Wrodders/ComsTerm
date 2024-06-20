from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *

from core.logger import getmylogger
from core.device import BaseDevice, DeviceType, DeviceInfo
from core.zmqutils import Transport, Endpoint
from core.utils import scanUSB

from components.SerialDevice import SerialDevice, SerialInfo
from components.SimulatedDevice import SimulatedDevice, SimInfo
from components.ZmqDevice import ZmqDevice, ZmqInfo

import sys
from typing import Type


class DevManGui(QWidget):
    def __init__(self):
        super().__init__()
        self.log = getmylogger(__name__)
        self.deviceManager = DeviceManager()
        self.deviceCon = DeviceConfig()
        self.initUI()
        self.connectSignals()
 
    def initUI(self):
        self.setWindowTitle("Device Manager")
        hBox = QHBoxLayout()
        # Connection Table
        self.table = QTableWidget()
        self.table.setRowCount(0)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Id", "Type", "Address", "Status"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        # Layout
        hBox.addWidget(self.table)
        hBox.addWidget(self.deviceCon)
        self.setLayout(hBox)

    def closeEvent(self, event):
        self.log.debug(f"Closing DeviceManager")
        if(self.deviceManager.device):
            self.deviceManager.stopDevice()

        event.accept()

    def connectSignals(self):
        """Connects signals to slots."""
        self.deviceCon.connectBtn.clicked.connect(self.connectHandle)
        self.deviceCon.disconnectBtn.clicked.connect(self.disconnectHandle)

    def connectHandle(self):
        ret = self.deviceManager.newDevice(self.deviceCon.getValues())
        self.deviceCon.connectBtn.setDisabled(True)
        if(ret == False):
            del(self.deviceManager.device)
            self.deviceManager.device=None
            self.deviceCon.connectBtn.setDisabled(False)

    def disconnectHandle(self):
        if isinstance(self.deviceManager.device, BaseDevice) == False:
            err = QMessageBox.information(self, "Info", "No Connections")
        else:
            self.deviceManager.stopDevice()
            self.deviceCon.connectBtn.setDisabled(False)

    def scanHandle(self):
        match self.deviceCon.conDeviceCB.currentText():
            case DeviceType.SERIAL.name:
                pass
            case DeviceType.SIMULATED.name:
                pass
            case _:
                self.log.error(f"Case {self.deviceCon.conDeviceCB.currentText()} not supported")
                raise NotImplementedError

    def disconnectDevice(self):
        selectedRow = self.table.currentRow()
        if selectedRow >= 0:
            confirm = QMessageBox.question(self, 'Confirm Disconnect', 
                                           'Are you sure you want to disconnect the selected device?',
                                           QMessageBox.StandardButton.Yes | 
                                           QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            
            if confirm == QMessageBox.StandardButton.Yes:
                self.table.removeRow(selectedRow)
        else:
            QMessageBox.warning(self, 'No Selection', 'No Device Selected', QMessageBox.StandardButton.Ok)

class DeviceManager():
    """ System I/O Server 
    Maintains and monitors connections to peripheral Devices. 
    """
    def __init__(self):
        self.log = getmylogger(__name__)
        self.device = None

    def newDevice(self, deviceInfo: DeviceInfo) -> bool:
        """
        @Brief: Creates new Device I/O Loop
        @Return: False if unsuccessful 
        """
        if(isinstance(deviceInfo, SerialInfo)):
            self.device = SerialDevice(deviceInfo)
        elif(isinstance(deviceInfo, SimInfo)):
            self.device = SimulatedDevice(deviceInfo)
        else:
            self.log.debug(f"Device {deviceInfo.devType.name} not implemented")
            raise NotImplemented
                
        # Start Device I/O
        return self.device._start()
            
    def stopDevice(self):
        if(isinstance(self.device, BaseDevice)):
            self.device._stop()
            del(self.device)
            self.device = None

class DeviceConfig(QWidget):

    def __init__(self):
        super(DeviceConfig, self).__init__()
        self.log  = getmylogger(__name__)
        self.serialConfig = SerialConfig()
        self.simConfig = SimConfig()
        self.initUI()
        self.connectSignals()

    def initUI(self):
        self.grid = QGridLayout()
        self.setMinimumWidth(200)
        # Device Type Config Stack
        self.stackLayout = QStackedLayout()
        self.stackLayout.addWidget(self.serialConfig)
        self.stackLayout.addWidget(self.simConfig)
        self.connectBtn = QPushButton("Connect")
        self.connectBtn.setMaximumWidth(350)
        self.disconnectBtn = QPushButton("Disconnect")
        self.disconnectBtn.setMaximumWidth(350)
        self.scanBtn = QPushButton("Scan")
        self.scanBtn.setMaximumWidth(350)
        self.conDeviceCB = QComboBox()
        self.conDeviceCB.setMaximumWidth(350)
        self.conDeviceCB.addItems(DeviceType._member_names_)
        # Layout
        self.grid.addWidget(self.conDeviceCB, 0,0, 1, 3)
        self.grid.addLayout(self.stackLayout, 1, 0 , 2, 3)
        self.grid.addWidget(self.disconnectBtn, 3, 0, 1,1)
        self.grid.addWidget(self.connectBtn, 3, 1, 1,1)
        self.grid.addWidget(self.scanBtn, 3, 2, 1,1)
        self.setLayout(self.grid)

    def connectSignals(self):
        self.conDeviceCB.currentIndexChanged.connect(self.updateDeviceStack)

    def updateDeviceStack(self):
        index = self.conDeviceCB.currentIndex()
        self.stackLayout.setCurrentIndex(index)

    def getValues(self) -> DeviceInfo:
        """
        @Brief: Gets User Input Device Config Values
        """
        match self.conDeviceCB.currentText():
            case DeviceType.SERIAL.name:
                port = self.serialConfig.portCB.currentText()
                baud = self.serialConfig.baudRate.currentText()
                devInfo = SerialInfo(port=port, baudRate=int(baud))
            case DeviceType.SIMULATED.name:
                rate = self.simConfig.rateCB.currentText()
                devInfo = SimInfo(dt=1/float(rate))
            case _:
                self.log.debug(f"Device {self.conDeviceCB.currentText()} not implemented")
                raise NotImplementedError
        return devInfo

class SerialConfig(QFrame):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setFrameShape(self.Shape.StyledPanel)
        self.setFrameShadow(self.Shadow.Plain)
        layout = QGridLayout()
        
        layout.addWidget(QLabel("Serial Port:"), 0, 0)
        self.portCB = QComboBox()
        self.portCB.addItems(scanUSB())
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
        self.setFrameShape(self.Shape.StyledPanel)
        self.setFrameShadow(self.Shadow.Plain)
        self.rateCB = QComboBox()
        self.rateCB.addItems(["1", "10", "100"])
        layout = QGridLayout()
        layout.addWidget(QLabel("Rate:"), 0, 0, 1, 2)
        layout.addWidget(self.rateCB, 0, 1, 1, 1)
        layout.addWidget(QLabel("[per s]"), 0, 2, 1,1)
        self.setLayout(layout)
