# ComsTerm V3 a simple Serial Terminal 

import queue as Queue
import sys
import time

import serial.tools.list_ports
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from serial import Serial
from serial.serialutil import SerialException


class App(QWidget):
    #Main Application Window############################################
    def __init__(self):
        super().__init__()
        self.initializeUI()


    def initializeUI(self):
        # Create Main Application User Interface
        self.setWindowTitle('ComsTerm V3')
        self.setGeometry(100, 100, 800, 600)

        # Create Main Layout
        self.mainLayout = QVBoxLayout() # Main Layout
        self.setLayout(self.mainLayout)

        #Main Layout is formed of 3 Sections Top Left Top Right and Bottom

        #Split Main Layout into 2 Sections################################
        mainSplitter = QSplitter(Qt.Orientation.Vertical)
        mainSplitter.setChildrenCollapsible(False)
        self.mainLayout.addWidget(mainSplitter) # Add Splitter to Main Layout
        top_panel = QFrame()
        top_panel.setFrameShape(QFrame.Shape.StyledPanel)

        mainSplitter.addWidget(top_panel)
        mainSplitter.addWidget(consoleTab) # Add Console Tab Object Main Splitter
        mainSplitter.setSizes([100, 600]) # Set Initial Size of Top and Bottom Panel

        #Create Top Panel #################################################
        topLayout = QHBoxLayout()
        top_panel.setLayout(topLayout)
        #Split Top Panel into 2 Sections###################################
        topSplitter = QSplitter(Qt.Orientation.Horizontal)
        topSplitter.setChildrenCollapsible(False)
        topLayout.addWidget(topSplitter) 

        right_panel = QFrame() #TODO change to QStackedWidget
        right_panel.setFrameShape(QFrame.Shape.StyledPanel)
        right_panel.setContentsMargins(2, 0, 0, 0)
        topSplitter.addWidget(connections)
        topSplitter.addWidget(right_panel)
        
    ## Event Handlers ##    
    def closeEvent(self,event):
            # Close all open ports
        try :
            serialDevice.serial.close() # Close Serial Port
            QThreadPool.globalInstance().waitForDone() #Kill Thread Pool
        except SerialException as e:
            print(e)
        except AttributeError as e:
            print(e)
        except Exception as e:
            print(e)
        finally:
            event.accept()
            sys.exit()
    


#####Sub Classes########

class ConnectionsPannel(QWidget):
    connectSignal = pyqtSignal(str) # Signal for connect button click with port path
    disconnectSignal = pyqtSignal(str) # Signal for disconnect button click
    sysLog = pyqtSignal(str) # Signal for Operational System Log Messages

    def __init__(self):
        super().__init__()
        self.UI()
    def UI(self):

        # Create Layout
        self.connectionlayout = QGridLayout()
        self.setLayout(self.connectionlayout)

        # Create Widgets
        self.portList = QComboBox()
        self.portList.setPlaceholderText('Select Port')
        self.scanBtn = QPushButton('Scan')
        self.scanBtn.setMaximumWidth(150)
        self.scanBtn.clicked.connect(self.handelScan)

        self.connectBtn = QPushButton('Connect')
        self.connectBtn.setMaximumWidth(150)
        self.connectBtn.clicked.connect(self.handelConnect)
        self.disconnectBtn = QPushButton('Disconnect')
        self.disconnectBtn.setMaximumWidth(150)
        self.preferencesBtn = QPushButton('Preferences')
        self.preferencesBtn.setMaximumWidth(150)
        self.preferencesBtn.clicked.connect(self.handelPreferences)

        # Add Widgets to Layout
        self.connectionlayout.addWidget(self.scanBtn, 0, 0,)
        self.connectionlayout.addWidget(self.portList, 0, 1, 1, 2)
        self.connectionlayout.addWidget(self.connectBtn, 1,0)
        self.connectionlayout.addWidget(self.disconnectBtn, 1,1)
        self.connectionlayout.addWidget(self.preferencesBtn, 1,2)


    # Event Handlers
   
    def handelScan(self):
        # Scan Button Clicked
        self.portList.clear()
        ports = list(serial.tools.list_ports.comports()) # gets list of serial ports on system
        ports = [p.device for p in ports if "USB" in p.description] # gets port path of USB Ports
        if len(ports) == 0:
            self.sysLog.emit('No USB Ports Found')
            
        self.portList.addItems(ports)
        self.portList.setCurrentIndex(0)

    def handelDisconnect(self):
        self.disconnectSignal.emit(self.portList.currentText())# Send Disconnect Signal

    def handelConnect(self):
        # Check is valid port path is selected
        if self.portList.currentText() == '':
            self.sysLog.emit('No Port Selected')
            return
        # Open Port
        self.connectSignal.emit(self.portList.currentText())
    

    def handelPreferences(self):
        pass

class ConsoleTab(QWidget):
    cmdSend = pyqtSignal(str) # Signal for sending command to serial port

    def __init__(self):
        super().__init__()
        self.UI()
    def UI(self):
        consoleTabLayout = QGridLayout()
        consoleTabLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(consoleTabLayout)
        # Create Widgets
        self.inputEntry = QLineEdit()
        self.inputEntry.setPlaceholderText('Enter Command')
        self.inputEntry.returnPressed.connect(self.handelSend)
        self.sendBtn = QPushButton('Send')
        self.sendBtn.clicked.connect(self.handelSend)
        self.sendBtn.setMaximumWidth(300)

        #Add Widgets to Layout
        consoleTabLayout.addWidget(outputconsole, 2, 0,1,3)
        consoleTabLayout.addWidget(self.inputEntry, 3, 0,1,2)
        consoleTabLayout.addWidget(self.sendBtn, 3, 2)


    # Event Handlers
    def handelSend(self):
        cmd = self.inputEntry.text()

        if cmd != '':
            # Disable Send Button to prevent multiple clicks
            self.holdSend() # Anti Spam
            self.cmdSend.emit(cmd) 
            self.inputEntry.clear()

    def holdSend(self):
        # Disables Send Comand Button to prevent multiple clicks
        state = self.sendBtn.isEnabled()
        self.sendBtn.setEnabled(not state)
        self.inputEntry.setEnabled(not state)

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
        msg =  "->> " + msg +':'
        self.write(msg)
    def createDataLog(self, msg):
        # Used to create a message on Device Data
        msg = "<<- " + msg 
        self.write(msg)
    def createSysLog(self, msg):
        # Used to create a message on Operational Logs
        msg = "<<!! " + msg +" !!>>"
        self.write(msg)
    def write(self, msg):
        self.append(msg)


##### Serial Objects #####

class SerialDevice(QObject):
    devData = pyqtSignal(str) # Signal for Device Data
    devSysLog = pyqtSignal(str) # Signal for Operational System Log Messages
    finished = pyqtSignal() # Signal for Thread Finished
    dTimeout = 10 # Timeout for Device Response cna be set in preferences


    initalized = False # Flag for if device is initalized
    data  = [] # Data Buffer
    # Commands dictionary
    commands = {
        'id': {
            'cmdNum': '0',
            'desc': 'Get Device ID',
            'args': 0,

        },
        'help': {
            "cmdNum": '1',
            "desc": 'List Commands',
            "args": 0,
        }
    }
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
            self.devSysLog.emit('Connected to ' + port)
            # Get Devcice Function List
            self.getDevFuncs()
        except SerialException as e:
            self.devSysLog.emit('Failed to Connect to Device')
            self.initalized = False
            self.finished.emit() # Send Finished Signal
            return None
   
    def getDevFuncs(self):
        msg  = str(list(self.commands).index('help'))
        self.write(msg) # Send Command to get Device Function List
        
    def checkCmd(self, cmd):
        # Checks if command is valid
       
       
        cmdName = cmd.split(',')[0]
        if cmdName in self.commands:
            pass
        else:
            self.devSysLog.emit('Invalid Command type help for list of commands')
            self.finished.emit() # Send Finished Signal
            return False
        # Map Command to Command Number
        cmdN = self.commands[cmdName].get('cmdNum') 
        cmdArgs = self.commands[cmdName].get('args') # Get Number of Arguments for Command
        # Check if correct number of arguments are provided
        if cmdArgs > 0:
            try:
                cmd = cmdN + ',' + cmd.split(',')[1] # Combine Command Number and Argument
            except IndexError:
                self.devSysLog.emit('Invalid Number of Arguments for command: ' + cmdName)
                self.finished.emit()
                return False    
        else:
            cmd = cmdN 
            
        self.write(cmd)
        

    
    def write(self,cmd):
    
        # check if device is connected 
        
        # create cmd serial packet
        cmd  = ('<' + cmd + '>').encode()
        # Write Command to Serial Device
        try:
            self.serial.write(cmd) # encode command to bytes
            self.callReadSafe() # call read in thread
        except SerialException as e:
            self.finished.emit()
            self.devSysLog.emit('Failed to Write to Device' + "\n"+ str(e))
            self.initalized = False
            return None
        except AttributeError as e:
            self.finished.emit() # emit thread finished signal
            self.devSysLog.emit('No Device Connected' + "\n"+ str(e))
            self.initalized = False
            return None
        

        

    def callReadSafe(self):
        # Call Read in Thread
        self.threadManager.tryStart(self.read)
    def read(self):
        # Read Response from Serial Device
        # Clear Data Buffer
        self.data = []
        dataline = '' # Data Line Buffer
        reading = True
        # time out after 10 seconds
        start = time.time()
        #TODO add possibility to change timeout based on function type
        while reading:
            if start + self.dTimeout < time.time():
                reading = False
                self.devSysLog.emit('Device Connection Timeout')
                self.initalized = False
                reading = False
                self.finished.emit()
                return None
            try: #read line form serial and decode to string remove \r\n
                dataline = self.serial.readline().decode().rstrip()
                
            except SerialException as e:
                self.devSysLog.emit('Failed to Read from Device' + "\n"+ str(e))
                self.initalized = False
                reading = False
                self.finished.emit()
            except AttributeError as e:
                self.devSysLog.emit('No Device Connected' + "\n"+ str(e))
                self.initalized = False
                reading = False
                self.finished.emit()
            except UnicodeDecodeError as e:
                self.devSysLog.emit('Failed to Decode Data' + "\n"+ str(e))
                self.initalized = False
                reading = False
                self.finished.emit()
        
            if dataline == '':
                pass
            elif dataline == "<D>":
                reading = False
                break
            else:
                dataline = [i for i in dataline if i != '<' and i != '>'] # remove < and > from data
                dataline = ''.join(dataline) # convert list to string
                self.data.append(dataline) # add data to buffer
                # check if data is response to Initializer Command
                if self.initalized != False:
                    self.devData.emit(dataline) # emit data to main thread
                else:
                    if dataline !="id" and dataline != "help":
                        self.commands[dataline] = {}
                        self.commands[dataline]['cmdNum'] = str(len(self.commands)-1)
                        self.commands[dataline]['args'] = 1 #TODO add ability to change number of arguments
        reading = False  
        self.initalized = True
        self.devSysLog.emit('Done')     
        self.finished.emit() # emit finished to main thread
            


  
     
if __name__ == '__main__':
    app = QApplication(sys.argv)
    connections = ConnectionsPannel()
    outputconsole = consoleOutput()
    consoleTab = ConsoleTab()
    serialDevice = SerialDevice()
    window = App()
    
    window.show()

    

    serialDevice.devData.connect(outputconsole.createDataLog)
    serialDevice.devSysLog.connect(outputconsole.createSysLog)
    serialDevice.finished.connect(consoleTab.holdSend)

    connections.connectSignal.connect(serialDevice.connect)
    connections.connectSignal.connect(consoleTab.holdSend)
    connections.sysLog.connect(outputconsole.createSysLog)
    connections.disconnectSignal.connect(serialDevice.disconnect)
    
    consoleTab.cmdSend.connect(outputconsole.createULog)
    consoleTab.cmdSend.connect(serialDevice.checkCmd)
    

    
    sys.exit(app.exec())

