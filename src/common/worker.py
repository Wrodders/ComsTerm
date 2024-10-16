import threading
from common.logger import getmylogger

log = getmylogger(__name__)

"""
@Brief: Worker IO Thread for Devices
"""
class Worker():
    def __init__(self, runFunc) -> None:
        self.log = getmylogger(__name__)
        self.stopEvent = threading.Event()
        self.wThread = threading.Thread(target=runFunc) # worker IO thread
        self.wThread.daemon = True
        
    def _begin(self):
        self.wThread.start()
        log.debug(f"START:{self.wThread.ident}")

    def _stop(self):
        log.debug(f"STOP:{self.wThread.ident}")
        self.stopEvent.set()