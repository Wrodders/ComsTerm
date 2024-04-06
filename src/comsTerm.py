import sys, argparse

from PyQt6 import QtCore
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *



from client.gui import GUI
from common.logger import getmylogger

log = getmylogger(__name__)

'''
CLI Application
'''
def parse_command_line_args():
    parser = argparse.ArgumentParser(description="GUI application with different data receivers")
    return parser.parse_args()

def main():


    
    app = QApplication(sys.argv)
    gui = GUI()
    gui.show()
   

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
