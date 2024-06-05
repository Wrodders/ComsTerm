from PyQt6.QtCore import *
from PyQt6.QtWidgets import *

from common.logger import getmylogger

from core.device import BaseDevice, Devices, DeviceInfo
from core.SerialDevice import SerialDevice, SerialInfo
from core.ZmqDevice import ZmqDevice, ZmqInfo
from core.SimulatedDevice import SimulatedDevice, SimInfo
from apps.menus import DeviceConfig

import sys


class DevManGui(QWidget):

    def __init__(self):
        super().__init__()
        self.deviceManager = DeviceManager()
        self.setWindowTitle("Device Manager")
        # Layouts
        mainLayout = QHBoxLayout()
        # Table
        self.table = QTableWidget()
        self.table.setRowCount(0)  # Start with no rows
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Id", "Type", "Address", "Status"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # Make the table non-editable
        
        # Configs
        self.deviceCon = DeviceConfig()
    
        mainLayout.addWidget(self.table)
        mainLayout.addWidget(self.deviceCon)

        self.setLayout(mainLayout)
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
    
    
    def disconnectDevice(self):
        selectedRow = self.table.currentRow()
        if selectedRow >= 0:
            confirm = QMessageBox.question(self, 'Confirm Disconnect', 'Are you sure you want to disconnect the selected device?',
                                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            if confirm == QMessageBox.StandardButton.Yes:
                self.table.removeRow(selectedRow)
        else:
            QMessageBox.warning(self, 'No Selection', 'No Device Selected', QMessageBox.StandardButton.Ok)



class DeviceManager():
    """ System I/O Server 
    
    Reads and parses Data 
    
    """
    def __init__(self):
        self.log = getmylogger(__name__)
        self.device = None

    def newDevice(self, deviceInfo: DeviceInfo) -> bool:
        if isinstance(deviceInfo, SerialInfo):
            self.device = SerialDevice(deviceInfo)
        elif isinstance(deviceInfo, SimInfo):
            self.device = SimulatedDevice(deviceInfo)
        else :
            self.log.debug(f"Device {deviceInfo.name} not implemented")
            raise NotImplemented
        """ Start New Device IO"""
        return self.device._start()
            
    def stopDevice(self):
        if(isinstance(self.device, BaseDevice)):
              self.device._stop()
              del(self.device)
              self.device = None
    

