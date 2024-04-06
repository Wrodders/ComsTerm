import sys, argparse

from PyQt6 import QtCore
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *

from core.device import BaseDevice

from client.plot import CreatePlot, LinePlot
from client.console import ConfigConsole, Console
from client.commander import Commander
from client.menues import DeviceConfig, SettingsMenu
from common.logger import getmylogger
from typing import Dict, List, Tuple


from core.SerialDevice import SerialDevice, SerialInfo
from core.ZmqDevice import ZmqDevice, ZmqInfo
from core.SimulatedDevice import SimulatedDevice, SimInfo

from core.device import Devices, DeviceInfo


from common.logger import getmylogger



class ComsTerm():
    """ Back End handler """
    def __init__(self):
        self.log = getmylogger(__name__)
        self.device = None

    def newDevice(self, deivceInfo: DeviceInfo):
        if isinstance(deivceInfo, SerialInfo):
            self.device = SerialDevice(deivceInfo)
        elif isinstance(deivceInfo, SimInfo):
            self.device = SimulatedDevice(deivceInfo)
            
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


              
