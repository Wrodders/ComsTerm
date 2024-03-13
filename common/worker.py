import threading
from logger import getmylogger


log = getmylogger(__name__)

"""
@Brief: Worker IO Thread for Devices
"""
class Worker():
    def __init__(self, runFunc) -> None:
        self.stopEvent = threading.Event()
        self.wThread = threading.Thread(target=runFunc) # worker IO thread
        
    def _begin(self):
        self.wThread.start()

    def _stop(self):
        self.stopEvent.set()