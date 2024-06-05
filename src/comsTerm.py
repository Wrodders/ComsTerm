from PyQt6.QtCore import *
from PyQt6.QtWidgets import *

import sys

from common.logger import getmylogger

from core.device import BaseDevice 
from apps.deviceManager import DevManGui

import typer

app = typer.Typer()
@app.command()
def rundevicemanager(mode: str = typer.Option(..., "-m", help="Mode to run the application in, either 'gui' or 'cli'")):
    if mode == 'gui':
        app = QApplication(sys.argv)
        gui = DevManGui()
        gui.show()
        sys.exit(app.exec())
    elif mode == 'cli':
        print("Running Device Manager in CLI mode")
        # CLI logic for Device Manager here

    else:
        typer.echo("Invalid mode. Use 'gui' or 'cli'.", err=True)
@app.command()
def runPlot():
    pass
@app.command()
def runCommander():
    pass
@app.command()
def runControls():
    pass
@app.command()
def runConsole():
    pass

if __name__ == '__main__':
    app()
