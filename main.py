# ComsTermV2 - A Console Terminal for with  MesoRobotics
# Split into 2 Sections Console and SystemUpdateTool

from datetime import datetime
import os
import sys
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
import serial
from serial import Serial
import serial.tools.list_ports
import csv

#Global Variables
releaseImgs = [""] #list of imgs file names to selected for update
releaseImgsPaths = [""] #list of imgs paths to selected for update
path = '/Users/rodrigoscott/Dev/SoftwareDistribution/' #path to the folder with the imgs

#Holds info collected from the system and the user
systemInfo = {
    "boardsInfo": {
            "Board ID": ["0x01", "0x02", "0x03","0x4"], # I2C Address of Boards scanned
            "Board Name": ["Interface Controller", "Kinematics Controller", "Joint Controller (JC1)","Vision Controller"], # Name of Board    
            "Firmware Version": ["0.0.1", "0.0.0", "0.0.0", "0.0.0"], # Current Firmware Version of Board
            "UDID": ["0x00000001", "0x00000002", "0x00000003", "0x00000004"], # Unique Device ID of Board
            }
}

    
# Main Application GUI Class ###############################################
class MainWindow(QWidget):
    scanPortsSignal = pyqtSignal()
    connectPortSignal = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ComsTermV2")
        self.setGeometry(100, 100, 800, 600)
        self.UI()

    def UI(self):
        # Create Main User Interface

        self.mainLayout = QVBoxLayout() # Main Layout
        self.setLayout(self.mainLayout)

        #Split Main Layout into 2 Sections###################################
        mainSplitter = QSplitter(Qt.Orientation.Vertical)
        mainSplitter.setChildrenCollapsible(False)
        self.mainLayout.addWidget(mainSplitter) # Add Splitter to Main Layout
        top_panel = QFrame() # Top Panel 
        top_panel.setFrameShape(QFrame.Shape.StyledPanel)
        bottom_panel = QFrame() # Bottom Panel
        mainSplitter.addWidget(top_panel)
        mainSplitter.addWidget(bottom_panel)
        mainSplitter.setSizes([200, 600]) # Set Initial Size of Top and Bottom Panel

        #Create Top Panel #####################################################
        topLayout = QHBoxLayout()
        top_panel.setLayout(topLayout)
        #Split Top Panel into 2 Sections#######################################
        topSplitter = QSplitter(Qt.Orientation.Horizontal)
        topSplitter.setChildrenCollapsible(False)
        topLayout.addWidget(topSplitter) # Add Splitter to Top Layout

        left_panel = QFrame() # Left Panel
        left_panel.setFrameShape(QFrame.Shape.StyledPanel)
        left_panel.setContentsMargins(0, 0, 2, 0)
        right_panel = QFrame() # Right Panel
        right_panel.setFrameShape(QFrame.Shape.StyledPanel)
        right_panel.setContentsMargins(2, 0, 0, 0)
        topSplitter.addWidget(left_panel)
        topSplitter.addWidget(right_panel)

        #Create Left Panel ####################################################
        leftLayout = QGridLayout()
        left_panel.setLayout(leftLayout)
        self.portPath = QLineEdit()
        self.portPath.setPlaceholderText("Enter Port Path")
        scanButton = QPushButton("Scan")
        scanButton.clicked.connect(lambda: self.scanPortsSignal.emit()) # Connect Scan Button to Scan Ports Function
        connectButton = QPushButton("Connect")
        connectButton.clicked.connect(lambda: self.connectPortSignal.emit(self.portPath.text())) # Connect Connect Button to Connect Port Function
        lspacer = QFrame()
        lspacer.setFrameShape(QFrame.Shape.NoFrame)
        
        leftLayout.addWidget(self.portPath, 0, 0,1,2)
        leftLayout.addWidget(scanButton, 1,0)
        leftLayout.addWidget(connectButton, 1,1)
        leftLayout.addWidget(lspacer, 2,0,1,2)
        #Create Right Panel Stack ###################################################
        rightLayout = QGridLayout()
        rightLayout.setContentsMargins(0, 0, 0, 0)
        right_panel.setLayout(rightLayout)
        self.mainStack = QStackedWidget()
        self.mainStack.addWidget(consolestack) # Add Console Stack to Main Stack
        self.mainStack.addWidget(sutstack) # Add System Update Tool Stack to Main Stack
        rightLayout.addWidget(self.mainStack, 0, 0, 1, 2)
        
        #Create Bottom Panel ####################################################
        #Create Bottom Panel Tab Widget #########################################
        bottomLayout = QVBoxLayout()
        bottomLayout.setContentsMargins(0, 0, 0, 0)
        bottom_panel.setLayout(bottomLayout)
        self.mainTabs = QTabWidget()
        self.mainTabs.setTabPosition(QTabWidget.TabPosition.North)
        self.mainTabs.setTabShape(QTabWidget.TabShape.Rounded)
        self.mainTabs.addTab(consoletab, "Console")
        self.mainTabs.addTab(suttab, "SUT")
        self.mainTabs.currentChanged.connect(self.handleTabChange)
        bottomLayout.addWidget(self.mainTabs)

    #Signals and Slots#######################################################   
    def updatePortPath(self, portPath):
        # Update Port Path
        self.portPath.setText(portPath)
    def handleTabChange(self):
        # Connects tab change to Top Right Stack Widget
        self.mainStack.setCurrentIndex(self.mainTabs.currentIndex())


#Subclass Windows ##########################################################
class consoleStack(QWidget):
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
        consoleStackLayout.addWidget(boardTable, 1,0,1,2)

class  sutStack(QWidget):
    imgsSelectedSignal = pyqtSignal()
    uploadStartSignal = pyqtSignal()
    syslogsSignal = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.UI()
    def UI(self):
        #Create System Update Tool Stack############################################

        #Create Widgets###########################################################
        self.releaseLabel = QLabel("Major System Release: ")
        self.releaseLabel.setAlignment(Qt.AlignmentFlag.AlignLeft)
        latestButton = QPushButton("Get Latest")
        browseButton = QPushButton("Browse Releases")
        scanButton = QPushButton("Scan Boards")
        connectButton = QPushButton("Connect to Boards")
        downloadButton = QPushButton("Download Images") # Placeholder for Cloud Integration 
        upgradeButton = QPushButton("Upgrade Boards")
    
        #Add Widgets to Layout####################################################
        sutStackLayout = QGridLayout()
        self.setLayout(sutStackLayout)
        sutStackLayout.addWidget(self.releaseLabel, 0,0)
        sutStackLayout.addWidget(latestButton, 0,1)
        sutStackLayout.addWidget(browseButton, 0,2)
        sutStackLayout.addWidget(scanButton, 1,0)
        sutStackLayout.addWidget(connectButton, 2,0)
        sutStackLayout.addWidget(downloadButton, 1,1,1,2)
        sutStackLayout.addWidget(upgradeButton, 2,1,1,2)

        #Signals and Slots#######################################################
        #These Signals call functions on the Serial Device Class
        upgradeButton.clicked.connect(lambda: self.uploadStartSignal.emit())
        upgradeButton.clicked.connect(lambda: self.syslogsSignal.emit("Upgrade Board")) # Placeholder for Serial Device Upgrade Function
        scanButton.clicked.connect(lambda: self.syslogsSignal.emit("Scan Boards")) # Placeholder for Serial Device Scan Function

        #These Signals call functions on the Cloud Class
        browseButton.clicked.connect(lambda: self.browseReleases("2"))
        latestButton.clicked.connect(lambda: self.browseReleases("1"))
    #Class Functions###########################################################
    def browseReleases(self, *version):
        # Open Brouse Dialoge to select release
        
        self.type = version[0]
        global releaseImgs
        global releaseImgsPaths
        global path
        if self.type == "1":
            #get latest version set 
            releasesFolder = [f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]
            releasesFolder.sort(reverse=True) # Sorts list in place
            latestPath = path + releasesFolder[0]
            #get latest imgs set
            releaseImgs = [f for f in os.listdir(latestPath) if os.path.isfile(os.path.join(latestPath, f)) and f.endswith(".txt")]
            #update releasImgsPaths list
            releaseImgsPaths = [latestPath + i for i in releaseImgs]
            self.releaseLabel.setText("Major System Release: " + releasesFolder[0])   
            
        elif self.type == "2":
            #browse for release
            releasesFolder =QFileDialog.getExistingDirectory(self, 'Select Folder',path)
            #get release imgs set
            if releasesFolder:
                releaseImgs = [f for f in os.listdir(releasesFolder) if os.path.isfile(os.path.join(releasesFolder, f))and f.endswith(".txt")]
                #update releasImgsPaths list
                releaseImgsPaths = [releasesFolder + i for i in releaseImgs]
                self.releaseLabel.setText("Major System Release: " + releasesFolder.split("/")[-1])   
        #update table in SUT Tab with release imgs
        # Send signal to table to update ui with release imgs
        self.imgsSelectedSignal.emit()
        
class sutTab(QWidget):

    def __init__(self):
        super().__init__()
        self.UI()

    def UI(self):
         # Place holder for Boards Table
         # this data should come from the command send by Scan Boards button
        boardsInfo  = systemInfo["boardsInfo"]
          
        self.numBoards = len(boardsInfo["Board ID"])
        for i in range(self.numBoards):
            releaseImgs.append("") # Add empty string to releaseImgs list for each board in scaChain
        #Create SUT Tab #######################################################
        #Create Widgets
        #Create Table
        self.updateTable = QTableWidget()
        self.updateTable.setColumnCount(6)
        self.updateTable.setHorizontalHeaderLabels(["Board Name", "Current Version","Upgrade Version","Custom Version", "Progress","Select"])
        self.updateTable.setRowCount(self.numBoards)
        self.updateTable.setVerticalHeaderLabels(boardsInfo["Board ID"])
        self.updateTable.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.updateTable.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.updateTable.horizontalHeader().sectionClicked.connect(self.selectAll) # Select All Check Boxes Signal
        #Create Table Widgets Objects 
        brouseBtns = [] # List of Browse Buttons objects
        self.progressBars = [] # List of Progress Bars objects
        self.selectCheckBoxes = [] # List of Select Check Boxes objects 
        #Add Objects to Table
        for i in range(self.numBoards):
            self.progressBars.append(progressBar()) # Create a list of Progress Bar Objects
            self.selectCheckBoxes.append(QCheckBox()) # Create a list of Check Box Objects
            brouseBtns.append(browsBtn()) # Create a list of Browse Button Objects
            brouseBtns[i].clicked.connect(lambda: self.browseReleases(brouseBtns.index(self.sender()))) # Browse Button Signal
            self.updateTable.setItem(i,0,QTableWidgetItem(boardsInfo["Board Name"][i]))
            self.updateTable.setItem(i,1,QTableWidgetItem(boardsInfo["Firmware Version"][i]))
            self.updateTable.setCellWidget(i,3,brouseBtns[i])
            self.updateTable.setCellWidget(i,4,self.progressBars[i])
            self.updateTable.setCellWidget(i,5,self.selectCheckBoxes[i])
        #expand columns to fill
        for i in range(6):
            self.updateTable.resizeColumnToContents(i)
            self.updateTable.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
        #add widgets to layout##################################################
        sutTabLayout = QVBoxLayout()
        sutTabLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(sutTabLayout)
        #create splitter pannels
        self.splitter = QSplitter(Qt.Orientation.Vertical)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(self.updateTable)
        self.splitter.addWidget(syslogsconsole)
        sutTabLayout.addWidget(self.splitter)

    
    #Signals and Slots#######################################################
    def updateVersion(self):
        #Update imgs Version of Selected Board
        # Called by SUT Stack Class when a new System release is selected
        try :
            for i in range(self.numBoards):
                self.updateTable.setItem(i,2,QTableWidgetItem(releaseImgs[i]))
        except:
            pass      

    def updateProgress(self):
        #place holder for update simulation
        # updates progess bar based on progress of write img to board
        #called by the Serail Device Class
        for i in range(self.numBoards):
            for j in range(101):
                self.progressBars[i].uploadProgress(j)

    #Class Functions###########################################################
    def browseReleases(self,index):
        # Selects a custom img for a board in the SUT Table
         # Open Brouse Dialoge to select release file
        releaseFile =QFileDialog.getOpenFileName(self,"Select Img File", path ) # gets file path
        #update releaseImgs List
        if releaseFile[0]:
            try:
                releaseImgs[index] = releaseFile[0]
            except:
                releaseImgs.append(releaseFile[0])
            versionNumber = releaseFile[0].split("/")[-1].split('.txt')[0] # gets version number from file name
            self.updateTable.setItem(index,2,QTableWidgetItem(versionNumber)) # sets version number in table
            sutstack.releaseLabel.setText("Major System Release: " + "Custom") # sets release number in SUT Tab
    
    def selectAll(self, logicalIndex):
        # Toggles all check boxes in table
        if logicalIndex == 5:
            for checkBox in self.selectCheckBoxes:
                checkBox.toggle()
    
class consoleTab(QWidget):
    sendSignal = pyqtSignal(str)
    def __init__(self):
        super().__init__()

        self.UI()

    def UI(self):
        #Create Console Tab Widgets############################################
        consoleTabLayout = QGridLayout()
        consoleTabLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(consoleTabLayout)
    
        inputEntry = QLineEdit()
        inputEntry.returnPressed.connect(lambda: self.sendSignal.emit(inputEntry.text()))
        sendButton = QPushButton("Send")
        sendButton.clicked.connect(lambda: self.sendSignal.emit(inputEntry.text()))
        sendButton.setMaximumWidth(300)
        inputEntry.setPlaceholderText("Enter Command")
        #Add Widgets to Layout####################################################
        consoleTabLayout.addWidget(devicelogsconsole, 0,0,1,3)
        consoleTabLayout.addWidget(inputEntry, 1,0,1,2)
        consoleTabLayout.addWidget(sendButton, 1,2)



class progressBar(QProgressBar):
    def __init__(self):
        super().__init__()
        self.UI()
    def UI(self):
        self.setRange(0,100)
        self.setValue(0)
        self.setTextVisible(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFormat("%p%")

    def uploadProgress(self, value):
        self.setValue(value)
    
class browsBtn(QPushButton):
    def __init__(self):
        super().__init__()
        self.UI()
    def UI(self):
        self.setText("Browse")
        self.setMaximumWidth(150)
        self.setMinimumWidth(100)

class logsConsole(QTextEdit):
    # Class for System Logs Console
    #Other classes send signals to this class to update the console Log with system logs

    logsTable = {
        #ComsTerm Function Logs
        "Scan" : "*--Scanning for Serial Devices--*", # 
        "Connect" : "*--Connecting to Serial Device--*",
        "Disconnect" : "*--Disconnecting from Serial Device--*",
        "sendCMD" : ">>",
        "recvData" : "<<",
        "Help": "--Help--",
        "Done": "*--Done--*"
    }
    def __init__(self):
        super().__init__()
        self.UI()
    def UI(self):
        self.setReadOnly(True)

    def createLog(self, msg):
        #create syslogs message
        #syslog messages provide info on the status of the current operation
        #syslog messages can have errors if the operation fails or is not completed
        #map message to logsTable
        if msg[0] in self.logsTable:
            #checks if message is not an Error Message
            if len(msg)>1:
                #checks if message contains Arguments
                
                log = self.logsTable[msg[0]] + msg[1]
            else:
                log = self.logsTable[msg[0]] #gets log message from logsTable
            self.append(log) #add log to console
        else:
            self.errorLog(msg) #if message is not in logsTable send to errorLog
        
    def errorLog(self,errmsg):
        #create error message
        #error messages provide info on the type of User error that occurred that prevented the operation from starting
        #add message to console
        errmsg = " ".join(errmsg)
        self.append(">>!!"+ errmsg + "!!<<")

        
class serialDevice(QWidget):
    # Class for Serial device
    # Handles all serial connection and communication with boards
    deviceLogsSignal = pyqtSignal(list) #signal for device logs in form of [Log Text,*Data]
    scanPathSignal = pyqtSignal(str) #signal for port scan results

    deviceSession = {
        "connected" : False,
        "port" : [],
        "baudrate" : 115200,
        "timeout" : 0.1,
        "Commands" : {},
    }


    def __init__(self):
        super().__init__()

    def scanPorts(self):
        #Scans avaialble serial ports to find Device and Updates the deviceSession Dictionary


        #Check if a Device is connected to the serial port
        if self.deviceSession["connected"]:
            #create pop up window to notify user that device is already connected to a port
            dlg = QMessageBox()
            dlg.setText("Device is already connected on port: "+ self.deviceSession["port"][0])
            dlg.setInformativeText("Click OK to disconnect from current port and scan for device")
            dlg.setWindowTitle("Device Already Connected")
            dlg.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
            rtnVal = dlg.exec() # returns value of button clicked
            if rtnVal == QMessageBox.StandardButton.Ok:
                self.disconnectDevice() #disconnects device from current port
                self.scanPorts() #rescans ports after disconnecting
                return
            elif rtnVal == QMessageBox.StandardButton.Cancel:
                return #cancels scan function if user clicks cancel

        #Begin Scanning Ports
        self.deviceLogsSignal.emit(["Scan"]) #send scan ports message to console
        #scan for serial ports
        ports = list(serial.tools.list_ports.comports()) # gets list of serial ports on system
        self.deviceSession["port"] = [p.device for p in ports if "USB" in p.description] # gets port path of USB Ports
        if self.deviceSession["port"]:  # Checks if a Valid port was found
            self.deviceLogsSignal.emit(["recvData", "Device Found on port: "+ self.deviceSession["port"][0]]) #send device found and port address message to console
            self.scanPathSignal.emit(self.deviceSession["port"][0]) # send port address to main window to update port label
            self.deviceLogsSignal.emit(["Done"]) # Port Scan Is Done
            return
        else:
            self.deviceLogsSignal.emit(["Device Not Found"]) #send device not found Error message to console
            self.scanPathSignal.emit("") # Update main windows port label with empty port path
            return False

    def connectPort(self,portPath):
        #Connects to Device on portPath
        # Check if a Device is connected to the serial port
        if self.deviceSession["connected"]:
            #create pop up window to notify user that device is already connected to a port
            dlg = QMessageBox()
            dlg.setText("Device is already connected on port: "+ self.deviceSession["port"][0])
            dlg.setInformativeText("Click OK to disconnect from current port")
            dlg.setWindowTitle("Device Already Connected")
            dlg.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
            rtnVal = dlg.exec()
            if rtnVal == QMessageBox.StandardButton.Ok:
                self.disconnectDevice()
                return
            elif rtnVal == QMessageBox.StandardButton.Cancel:
                return #cancels new connect function if user clicks cancel
        #Check if User entered custom port path
        if portPath:
            self.deviceSession["port"] = [portPath] #sets port path to user entered path, Duplicated if user entered path is already in deviceSession["port"]
        else:
            self.deviceLogsSignal.emit(["No Port Selected"]) #send no port selected Error message to console
            self.deviceSession["port"] = [] #clears port path if user PortPath is empty
            return False #returns False if no port path is selected
        
        #Connect to Device on portPath ############################################
        try:
            self.device = serial.Serial(self.deviceSession["port"][0], self.deviceSession["baudrate"], timeout=self.deviceSession["timeout"]) #connects to device on portPath
            self.deviceLogsSignal.emit(["Connect", self.deviceSession["port"][0]]) #send connect device message to console
            self.deviceSession["connected"] = True #sets connected status to True
            self.deviceLogsSignal.emit(["Done"]) #send done message to console
            self.deviceLogsSignal.emit(["**----NEW SESSION----**"]) #send new session message to console
            # Send Command to read Valid Commands from Device
            self.sendCommand("help") #sends help command to device to get list of valid commands
            # Send command to device to get device info
            self.sendCommand("id") #sends id command to device to get device info
            
            return True
        except serial.SerialException:
            self.deviceSession["connected"] = False
            self.deviceLogsSignal.emit(["Unable to Connect to Device on port: "+ self.deviceSession["port"][0]]) #send connect device Error message to console
            return False

    def disconnectDevice(self):
        #disconnects device from current port 
        self.deviceLogsSignal.emit(["Disconnect",self.deviceSession["port"][0]])
        #self.ser.close() # closes serial port
        self.deviceSession["connected"] = False # sets device session to disconnected
        self.deviceSession["port"] = [] # clears port path
        self.scanPathSignal.emit("") # Clears main windows port label with empty port path
        self.deviceLogsSignal.emit(["Done"])
        self.deviceLogsSignal.emit(["**---SESSION TERMINATED---**"]) #send done message to console
        
        return

    #ComsTerminal Functions###################################################
    def sendCommand(self, cmd):
        #check if device is connected
        #if not self.deviceSession["connected"]:
        #    self.deviceLogsSignal.emit(["Device Not Connected"]) #send device not connected Error message to console
        #    return False
        #Check if command is valid
        if cmd == "":
            self.deviceLogsSignal.emit(["No Command Entered"])
            return False
        if cmd == "help":
            self.deviceLogsSignal.emit(["Help"]) #send help message to console
            #PLACEHLDER FOR HELP COMMAND
            if not self.deviceSession["Commands"]:
                with open('Commands.csv', 'r') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        self.deviceSession["Commands"].update({row[0]:[row[1],row[2],row[3]]})# reads row into dictionary
                    self.deviceSession["Commands"].pop("cmdName") #removes headernames from dictionary
                self.deviceLogsSignal.emit(["Done"]) #send done message to console
            else: # if commands have already been read from device
               # display commands key and value in console
                for key, value in self.deviceSession["Commands"].items():
                    self.deviceLogsSignal.emit(["recvData", key + " : " + "-".join(value)])
                self.deviceLogsSignal.emit(["Done"]) #send done message to console
            return True
        # Check if command is valid
        if cmd not in self.deviceSession["Commands"]:
            self.deviceLogsSignal.emit(["Invalid Command"])


       
  

   

        

# Run the program ############################################################
if __name__ == '__main__':
    app = QApplication(sys.argv) # manages the apps main event loop and starts the app
   
    # create class instances###############################################
    syslogsconsole= logsConsole() # Creates System Logs Console for SUT TAB
    devicelogsconsole = logsConsole() # Creates Device Logs Console for Connections TAB

    suttab = sutTab()
    sutstack = sutStack()
    consolestack = consoleStack()
    consoletab= consoleTab()
    #Connect Signals and Slots################################################
    sutstack.imgsSelectedSignal.connect(suttab.updateVersion) # Updates SUT TAB with selected image Release Version form SUT STACK
    sutstack.uploadStartSignal.connect(suttab.updateProgress) # PLACEHOLDER Updates SUT TAB with progress of upload
    sutstack.syslogsSignal.connect(syslogsconsole.createLog) # Creates System Logs in SUT TAB syslogsconsole 


    serialdevice = serialDevice() # creates instance of serialDevice 
    serialdevice.deviceLogsSignal.connect(devicelogsconsole.createLog) # Creates Device Logs in Connections TAB devicelogsconsole
    consoletab.sendSignal.connect(serialdevice.sendCommand) # Sends command from Connections TAB to serialDevice
    
    
     # create main window###################################################
    window = MainWindow()# create main window GUI Application
    
    window.scanPortsSignal.connect(serialdevice.scanPorts) # Connects Scan Ports Button to serialDevice scanPorts function
    window.connectPortSignal.connect(serialdevice.connectPort) # Connects Connect to Port Button to serialDevice connectPort function
    serialdevice.scanPathSignal.connect(window.updatePortPath) # Connects results of serialDevice scanPorts to updatePortPath function in main window
    
    window.show()

    sys.exit(app.exec()) # exit the app when the main event loop ends