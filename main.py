# ComsTerm V3 a simple Serial Terminal 

import queue as Queue
import sys
import time
from enum import Enum, auto
import serial.tools.list_ports
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QPainter, QColor, QFont,QPen
from serial import Serial
from serial.serialutil import SerialException



class App(QMainWindow):
    #Main Application Window############################################
    def __init__(self):
        super().__init__()
        self.initializeUI()


    def initializeUI(self):
        # Create Main Application User Interface
        self.setWindowTitle('ComsTerm V3')
        #self.setGeometry(100, 100, 800, 600)

        # Create Initial Dockable Widgets ######
        consoleDock = QDockWidget('Console', self)
        consoleDock.setWidget(consoleTab) # Set Console Tab as Dock Widget
        # set allowed areas
        consoleDock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        connectionsDock = QDockWidget("Connections", self)
        connectionsDock.setWidget(connectionsTab) # Set Connections Tab as Dock Widget
        # set allowed areas
        connectionsDock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)

        optDock = QDockWidget("Options", self)
        optDock.setWidget(optionTab) # Set OptionTab Instance as Dock Widget
        # set allowed areas
        optDock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)

        # Add Dockable Widgets to Main Window
        self.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, connectionsDock) # Add Connections Dock to Top
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, optDock)   # Add Option Dock to Right
        # Split Connections and Options Docks
        self.splitDockWidget(connectionsDock, optDock, Qt.Orientation.Horizontal)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, consoleDock) # Add Console Dock to Bottom
        

               
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


## TABS ##
class ConnectionsTab(QWidget):
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
        self.disconnectBtn.clicked.connect(self.handelDisconnect)
        self.preferencesBtn = QPushButton('Preferences')
        self.preferencesBtn.setMaximumWidth(150)
        self.preferencesBtn.clicked.connect(self.handelPreferences)

        # Add Widgets to Layout
        self.connectionlayout.addWidget(self.scanBtn, 0, 0,)
        self.connectionlayout.addWidget(self.portList, 0, 1, 1, 2)
        self.connectionlayout.addWidget(self.connectBtn, 1,0)
        self.connectionlayout.addWidget(self.disconnectBtn, 1,1)
        self.connectionlayout.addWidget(self.preferencesBtn, 1,2)


        # Set row stretch
        self.connectionlayout.setRowStretch(2, 1) 
       

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

class OptTab(QWidget):
    def __init__(self):
        super().__init__()
        self.UI()
    
    def UI(self):
        #Create Console Stack Widgets############################################
        scanBoardsButton = QPushButton("Scan Boards")
        connectBoardsButton = QPushButton("Connect to Boards")
        boardTable = QTableWidget()
        boardTable.setColumnCount(3)
        boardTable.setHorizontalHeaderLabels(["Board ID", "Board Name","Connect"])
        boardTable.setRowCount(4)
        boardTable.setMaximumHeight(5*boardTable.rowHeight(0))
        boardTable.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        #Add check boxes to connect column 
        for i in range(4):
            checkBox = QCheckBox()
            boardTable.setCellWidget(i,2,checkBox)
        #Create Console Stack Layout€############################################
        consoleStackLayout = QGridLayout()
        self.setLayout(consoleStackLayout)
        consoleStackLayout.addWidget(scanBoardsButton, 0,0)
        consoleStackLayout.addWidget(connectBoardsButton, 0,1)
        consoleStackLayout.addWidget(boardTable, 1,0,2,2)

        # Set row stretch
        consoleStackLayout.setRowStretch(3, 1)

class ConsoleTab(QWidget):
    cmdSend = pyqtSignal(str) # Signal for sending command to serial port

    def __init__(self):
        super().__init__()
        self.UI()

    def UI(self):
        #set size 
        self.setMinimumSize(800, 600)
        consoleTabLayout = QGridLayout()
        consoleTabLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(consoleTabLayout)
        # set minimum size of tab

        # Create Widgets
        self.inputEntry = QLineEdit()
        self.inputEntry.returnPressed.connect(self.handelSend)
        self.inputEntry.setPlaceholderText('Enter Command')

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
        if cmd == '':
            return
            # Disable Send Button to prevent multiple clicks
        self.cmdSend.emit(cmd) 
        self.inputEntry.clear()

    def holdSend(self):
        # Disables Send Command Button to prevent multiple clicks
        state = self.sendBtn.isEnabled()
        self.sendBtn.setEnabled(not state)
        self.inputEntry.setEnabled(not state)



    # CONSOLE FUNCTIONS
    def clearConsole(self):
        outputconsole.clear()
    def saveLog(self):
        #Open file dialogue to save log
        pass    

    def startMotionControl(self):
        # Creates Sub Window for Motion Control
        pass



# Console Text Area ##
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
    class SerialState(Enum):
        # Enum for Serial Device State
        CLOSED = auto() # Serial Port is Closed
        CONNECTED = auto() # Serial Port is Open AND Connected
        INITIALIZED = auto() # Serial Port is Open AND Initialized
  


    devData = pyqtSignal(str) # Signal for Device Data
    devSysLog = pyqtSignal(str) # Signal for Operational System Log Messages
    holdSignal = pyqtSignal() # Signal for Thread Work Finished
    dTimeout = 10 # Timeout for Device Response cna be set in preferences



    data  = [] # Data Buffer
    # Commands dictionary
    commands = {}
    
    def __init__(self,):
        super().__init__()
        self.__state = self.SerialState.CLOSED
        self.SessionSetup = {
            'port': "",
            'baudrate': 115200,
            'bytesize': 8,
            'parity': 'N',
            'timeout': 1,
        }
        self.threadManager = QThreadPool()
        self.setDfaultCommands()

    def setState(self, state):
        self.__state = state 
    def getState(self):
        return self.__state
    
    def setDfaultCommands(self):
        # Sets Default Commands
        self.commands = {
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

    def connect(self,port):
        self.SessionSetup['port'] = port
        #Check if port is already open
        if self.getState() != self.SerialState.CLOSED:
            try:
                self.serial.isOpen()
            except Exception as e:
                self.devSysLog.emit('Connection Error: ' + str(e))
                self.disconnect() # Close Port
                return None # Exit Function
            else:
                self.devSysLog.emit('Port Already Open')
                return None # Exit Function
        # Open Port
        try:
            self.serial = Serial(**self.SessionSetup)
        except SerialException as e:
            self.devSysLog.emit(str(e)) # Send Error Message
            self.disconnect() # Close Port
        except TypeError as e:
            self.devSysLog.emit(str(e))
            self.disconnect() # Close Port
        else:
            self.setState(self.SerialState.CONNECTED)
            self.devSysLog.emit('Connecting to ' + self.SessionSetup['port'])
            # Initialize Device 
            self.initialize()
    def disconnect(self):
        # Disconnects Serial Port
        self.setState(self.SerialState.CLOSED)
        try:
            self.serial.close()
        except Exception as e:
            self.devSysLog.emit('Error Closing Port: ' + str(e))
        finally:
            self.setDfaultCommands()
            self.devSysLog.emit('Disconnecting from ' + self.SessionSetup['port'])
        
    def initialize(self):
        # Initialize Device collect Device ID and other info
        # TODO Collect Device ID Separately 
        msg  = 'help'
        self.checkCmd(msg) # Send Command to get Device Function List
        
    def checkCmd(self, cmd):
        # Checks if command is valid
        # Check State
        if self.getState() == self.SerialState.CLOSED:
            self.devSysLog.emit('Port is Closed')
            return None # Exit Function if Port is Closed

        cmdName = cmd.split(',')[0] # Get Command Name
        if cmdName not in self.commands:
            self.devSysLog.emit('Invalid Command type help for list of commands')
            return None # Exit Function if Command is Invalid

        # Check if command has correct number of arguments
        cmdN = self.commands[cmdName].get('cmdNum') # Get Command Number
        cmdArgs = self.commands[cmdName].get('args') # Get Number of Arguments for Command
        # Check if correct number of arguments are provided
        if cmdArgs > 0:
            try:
                cmd = cmdN + ',' + cmd.split(',')[1] # Combine Command Number and Argument
            except IndexError:
                self.devSysLog.emit('Invalid Number of Arguments for command: ' + cmdName)
                return None # Exit Function if Command is Invalid
        else:
            cmd = cmdN #
        
        # Send Command
        self.write(cmd)
        
    def write(self,cmd):
        # TODO Add Encryption
        # create cmd serial packet
        cmd = ('<'+ cmd + '>').encode() # Add Start and End of Packet
        # Write Command to Serial Device
        try:
            self.serial.write(cmd) # encode command to bytes
        except SerialException as e:
            self.devSysLog.emit('Failed to Write to Device' + "\n"+ str(e))
            self.disconnect() # Close Port
        except AttributeError as e:
            self.devSysLog.emit('No Device Connected' + "\n"+ str(e))
            self.disconnect() # Close Port
        else:
            # Read Response from Device
            self.holdSignal.emit() # Hold Signal to prevent new commands from being sent until response is received
            self.callReadSafe()

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
                self.devSysLog.emit('Device Connection Timeout')
                self.disconnect() # Close Port
                break # Exit Loop
            try: #read line form serial and decode to string remove \r\n
                dataline = self.serial.readline().decode().rstrip()
            except SerialException as e:
                reading = False
                self.devSysLog.emit('Failed to Read from Device' + "\n"+ str(e))
                self.disconnect() # Close Port
            except AttributeError as e:
                reading = False
                self.devSysLog.emit('No Device Connected' + "\n"+ str(e))
                self.disconnect() # Close Port
            except UnicodeDecodeError as e:
                reading = False
                self.devSysLog.emit('Failed to Decode Data' + "\n"+ str(e))
                self.disconnect() # Close Port
            else:
                if dataline == '':
                    pass
                    
                elif dataline == "<D>":
                    if self.getState() == self.SerialState.CONNECTED:
                        self.setState(self.SerialState.INITIALIZED)
                        self.devSysLog.emit('Device Initialized')
                    reading = False # Stop Reading
                    break
                else:
                    dataline = [i for i in dataline if i != '<' and i != '>'] # remove < and > from data
                    dataline = ''.join(dataline) # convert list to string
                    self.data.append(dataline) # add data to buffer
                    # check if data is response to Initializer Command
                    if self.getState() == self.SerialState.INITIALIZED:
                        self.devData.emit(dataline) # emit data to main thread
                    else:
                        if dataline !="id" and dataline != "help": # Ignore Default Commands
                            self.commands[dataline] = {}
                            self.commands[dataline]['cmdNum'] = str(len(self.commands)-1)
                            self.commands[dataline]['args'] = 1 #TODO add ability to change number of arguments                   
            
        self.devSysLog.emit('Done') # Done Reading
        self.holdSignal.emit() # Send Hold Signal to allow new commands to be sent

# Run Main Program
if __name__ == '__main__':

    app = QApplication(sys.argv)

    connectionsTab = ConnectionsTab()
    outputconsole = consoleOutput()
    consoleTab = ConsoleTab()
    optionTab = OptTab()
    #Create Serial Device Object
    serialDevice = SerialDevice()
    #Create Main Application
    window = App()
    window.show()


    # Connect Signals and Slots
    serialDevice.devData.connect(outputconsole.createDataLog)
    serialDevice.devSysLog.connect(outputconsole.createSysLog)
    serialDevice.holdSignal.connect(consoleTab.holdSend)

    connectionsTab.connectSignal.connect(serialDevice.connect)
    connectionsTab.sysLog.connect(outputconsole.createSysLog)
    connectionsTab.disconnectSignal.connect(serialDevice.disconnect)
    
    consoleTab.cmdSend.connect(outputconsole.createULog)
    consoleTab.cmdSend.connect(serialDevice.checkCmd)
    
    # Start Application
    sys.exit(app.exec())

