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
from core.SimulatedDevice import SimulatedDevice

from core.device import Devices, DeviceInfo


from client.gui import GUI
from common.logger import getmylogger

log = getmylogger(__name__)

def main():
    app = QApplication(sys.argv)
    gui = GUI()
    gui.show()
   
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
