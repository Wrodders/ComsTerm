import sys, argparse

from PyQt6 import QtCore
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *

from core.SerialDevice import SerialDevice
from core.ZmqDevice import ZmqDevice
from core.SimulatedDevice import SimulatedDevice

from client.gui import GUI
from logger import getmylogger

log = getmylogger(__name__)

'''
CLI Application
'''
def parse_command_line_args():
    parser = argparse.ArgumentParser(description="GUI application with different data receivers")
    parser.add_argument('--serial', action='store_true', help='Use serial interface')
    parser.add_argument('--simulated', action='store_true', help='Use simulated interface')
    #parser.add_argument('--ble', action='store_true', help='Use ble interface')
    #parser.add_argument('--zmq', action='store_true', help='Use zmq interface')
    return parser.parse_args()

def main():

    args = parse_command_line_args()

    if args.serial:
        dataInterface = SerialDevice()
    elif args.simulated:
        dataInterface = SimulatedDevice(0.1)
    else:
        print("Error: Please specify either --serial or --simulated")
        return
    
    app = QApplication(sys.argv)
    gui = GUI(dataInterface)
   

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
