# ComsTerm V3 a simple Serial Terminal 

import queue as Queue
from serial import Serial
import serial.tools.list_ports, sys, time
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *




class App(QWidget):
    cmdSend = pyqtSignal(str) # Signal for send button click with command
    connectSignal = pyqtSignal(str)
    sysLog = pyqtSignal(str) # Signal for Operational System Log Messages

    def __init__(self):
        super().__init__()
        self.setWindowTitle('ComsTerm V3')
        self.setGeometry(100, 100, 800, 600)
        self.UI()


    def UI(self):
        # Create Main Application User Interface
        # Create Layout
        consoleTabLayout = QGridLayout()
        consoleTabLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(consoleTabLayout)

        # Create Widgets for Console Tab
        self.scanBtn = QPushButton('Scan')
        self.scanBtn.clicked.connect(self.handelScan)
        self.portList = QComboBox()
        self.disconnectBtn = QPushButton('Disconnect')
        self.disconnectBtn.clicked.connect(self.handelDisconnect)   
        self.connectBtn = QPushButton('Connect')
        self.connectBtn.clicked.connect(self.handelConnect)
        self.preferencesBtn = QPushButton('Preferences')
        self.preferencesBtn.clicked.connect(self.handelPreferences)


        self.inputEntry = QLineEdit()
        self.inputEntry.setPlaceholderText('Enter Command')
        self.inputEntry.returnPressed.connect(self.handelSend)
        self.sendBtn = QPushButton('Send')
        self.sendBtn.clicked.connect(self.handelSend)
        self.sendBtn.setMaximumWidth(300)
        # Add Widgets to Layout
        consoleTabLayout.addWidget(self.scanBtn, 0, 0)
        consoleTabLayout.addWidget(self.portList, 0, 1, 1, 2)
        consoleTabLayout.addWidget(self.disconnectBtn, 1, 0)
        consoleTabLayout.addWidget(self.connectBtn, 1, 1)
        consoleTabLayout.addWidget(self.preferencesBtn, 1, 2)
        consoleTabLayout.addWidget(outputconsole, 2, 0,1,3)
        consoleTabLayout.addWidget(self.inputEntry, 3, 0,1,2)
        consoleTabLayout.addWidget(self.sendBtn, 3, 2)

    def closeEvent(self,*event):
        # Close Event
        try:
            self.serial.close()
        except:
            pass

    def handelScan(self):
        # Scan Button Clicked
        self.portList.clear()
        ports = list(serial.tools.list_ports.comports()) # gets list of serial ports on system
        ports = [p.device for p in ports if "USB" in p.description] # gets port path of USB Ports
        if len(ports) == 0:
            self.sysLog.emit('No USB Ports Found')
            
        self.portList.addItems(ports)

    def handelDisconnect(self):
        pass

    def handelConnect(self):
        # Check is valid port path is selected
        #if self.portList.currentText() == '':
         #   self.sysLog.emit('No Port Selected')
          #  return
        # Check if port is already open
        #TODO
        # Open Port
        self.connectSignal.emit(self.portList.currentText())

  

    def handelPreferences(self):
        pass

    def handelSend(self):
        # Send Button Clicked
        cmd = self.inputEntry.text()
        if cmd != '':
            # Disable Send Button to prevent multiple clicks
            self.holdSend()
            self.cmdSend.emit(cmd)
            self.inputEntry.clear()
        
    def holdSend(self):
        # Disable Send Button to prevent multiple clicks
        state = self.sendBtn.isEnabled()
        self.sendBtn.setEnabled(not state)
        self.inputEntry.setEnabled(not state)

class SerialDevice(QObject):
    devData = pyqtSignal(str) # Signal for Device Data
    finished = pyqtSignal(str) # Signal for Thread Finished
    dTimeout = 10 # Timeout for Device Response cna be set in preferences
    def __init__(self,):
        super().__init__()
        self.SessionSetup = {
            'port': "",
            'baudrate': 9600,
            'bytesize': 8,
            'parity': 'N',
            'timeout': 1,
        }
        self.threadManager = QThreadPool()

    def connect(self,port):
        self.SessionSetup['port'] = port
    
        # Conneyt to Serial Device
        try:
            self.serial = Serial(**self.SessionSetup)
            print('Connected')
        except:
            print('Error Connecting to Serial Device')
            return False

    def write(self,cmd):
        # Write Command to Serial Device
        try:
            self.serial.write(cmd.encode()) # encode command to bytes
        except:
            print('Error Writing to Serial Device')
        
        self.callReadSafe() # call read in thread

    def callReadSafe(self):
        # Call Read in Thread
        self.threadManager.start(self.read)
    def read(self):
        # Read Response from Serial Device
        reading = True
        # time out after 10 seconds
        start = time.time()
        #TODO add possibility to change timeout based on function type
    
        while reading:
            if start + self.dTimeout < time.time():
                reading = False
                self.finished.emit('Timeout')
                break
            try: #read line form serial and decode to string remove \r\n
                dataline = self.serial.readline().decode().rstrip()
                if dataline == '':
                    pass
                elif dataline == "<D>":
                        reading = False
                        break
                else:
                    self.devData.emit(dataline) # emit data to main thread
            except:
                reading = False
                print('Error Reading from Serial Device')      
        self.finished.emit("Done >>") # emit finished to main thread
        


        
            

        

            

    



class consoleOutput(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.setAcceptRichText(False)
        self.setUndoRedoEnabled(False)
        self.setAcceptDrops(False)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.setStyleSheet('background-color: black; color: green;')
    def createULog(self, msg):
        # Used to create a message of the users input 
        msg =  ">> " + msg
        self.write(msg)

    def createDataLog(self, msg):
        # Used to create a message on Device Data
        msg = "<< " + msg 
        self.write(msg)
    def createSysLog(self, msg):
        # Used to create a message on Operational Logs
        msg = "<<!!" + msg +"!!>>"
        self.write(msg)
    def write(self, msg):
        self.append(msg)



  
     
if __name__ == '__main__':
    app = QApplication(sys.argv)
    outputconsole = consoleOutput()
    serialDevice = SerialDevice()
    window = App()
    app.aboutToQuit.connect(window.closeEvent)
    window.show()

    window.cmdSend.connect(outputconsole.createULog)
    window.cmdSend.connect(serialDevice.write)
    window.sysLog.connect(outputconsole.createSysLog)
    window.connectSignal.connect(serialDevice.connect)

    serialDevice.devData.connect(outputconsole.createDataLog)
    serialDevice.finished.connect(outputconsole.createDataLog)
    serialDevice.finished.connect(window.holdSend)


    
    
    sys.exit(app.exec())

