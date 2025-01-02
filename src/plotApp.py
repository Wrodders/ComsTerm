# This file contains the main application class for the plotter application

import sys
from PyQt6.QtWidgets import QApplication
from client.plot import PlotApp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = PlotApp(".config/cfg_plotApps.json")
    ex.show()
    sys.exit(app.exec())