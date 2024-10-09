from PyQt6.QtCore import *
from PyQt6.QtWidgets import *

from common.logger import getmylogger

from core.device import BaseDevice, Devices, DeviceInfo
from core.SerialDevice import SerialDevice, SerialInfo
from core.ZmqDevice import ZmqDevice, ZmqInfo
from core.SimulatedDevice import SimulatedDevice, SimInfo


class ComsTerm():
    """ Back End handler """
    def __init__(self):
        self.log = getmylogger(__name__)
        self.device = BaseDevice()

    def newDevice(self, deviceInfo: DeviceInfo):
        if isinstance(deviceInfo, SerialInfo):
            self.device = SerialDevice(deviceInfo)
        elif isinstance(deviceInfo, SimInfo):
            self.device = SimulatedDevice(deviceInfo)
            
        if(isinstance(self.device, BaseDevice)):
            if self.device._start() == False:
                del(self.device)
                self.device = None
                return False
            else:
                return True
            
    def stopDevice(self):
        if(isinstance(self.device, BaseDevice)):
              self.device._stop()
              del(self.device)
              self.device = None