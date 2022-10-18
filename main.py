# ComsTermV2 - A Console Terminal for with  MesoRobotics
# Split into 2 Sections Console and SystemUptadeTool

import os
from platform import release
from select import select
import sys
from turtle import home
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *


#Global Variables
releaseImgs = [""] #list of imgs file names to selected for update
releaseImgsPaths = [""] #list of imgs paths to selected for update


    

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ComsTermV2")
        self.setGeometry(100, 100, 800, 800)
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
        connectButton = QPushButton("Connect")
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

    def handleTabChange(self):
        # Connects tab change to Top Right Stack Widget
        self.mainStack.setCurrentIndex(self.mainTabs.currentIndex())
   



#Subclass Windows 
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
    testsignal = pyqtSignal()
    def __init__(self):
        super().__init__()
        self.UI()
    def UI(self):
        #Create System Update Tool Stack############################################

        #Create Widgets###########################################################
        releaseLabel = QLabel("Major System Release: ")
        releaseLabel.setAlignment(Qt.AlignmentFlag.AlignLeft)
        latestButton = QPushButton("Get Latest")
        latestButton.clicked.connect(lambda: self.browseReleases("1"))
        browseButton = QPushButton("Browse Releases")
        browseButton.clicked.connect(lambda: self.browseReleases("2"))
        scanButton = QPushButton("Scan Boards")
        connectButton = QPushButton("Connect to Boards")
        downloadButton = QPushButton("Download Images") # Placeholder for Cloud Integration 
        upgradeButton = QPushButton("Upgrade Boards")
    
        #Add Widgets to Layout####################################################
        sutStackLayout = QGridLayout()
        self.setLayout(sutStackLayout)
        sutStackLayout.addWidget(releaseLabel, 0,0)
        sutStackLayout.addWidget(latestButton, 0,1)
        sutStackLayout.addWidget(browseButton, 0,2)
        sutStackLayout.addWidget(scanButton, 1,0)
        sutStackLayout.addWidget(connectButton, 2,0)
        sutStackLayout.addWidget(downloadButton, 1,1,1,2)
        sutStackLayout.addWidget(upgradeButton, 2,1,1,2)

    #Signals and Slots#######################################################

    def browseReleases(self, *version):
        # Open Brouse Dialoge to select release
        path = '/Users/rodrigoscott/Dev/SoftwareDistribution/'
        self.type = version[0]
        global releaseImgs
        global releaseImgsPaths
        
        if self.type == "1":
            #get latest version set 
            releasesFolder = [f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]
            releasesFolder.sort(reverse=True) # Sorts list in place
            latestPath = path + releasesFolder[0]
            #get latest imgs set
            releaseImgs = [f for f in os.listdir(latestPath) if os.path.isfile(os.path.join(latestPath, f)) and f.endswith(".txt")]
            #update releasImgsPaths list
            releaseImgsPaths = [latestPath + i for i in releaseImgs]
        elif self.type == "2":
            #browse for release
            releaseFolder =QFileDialog.getExistingDirectory(self, 'Select Folder',path)
            #get release imgs set
            if releaseFolder:
                releaseImgs = [f for f in os.listdir(releaseFolder) if os.path.isfile(os.path.join(releaseFolder, f))and f.endswith(".txt")]
                #update releasImgsPaths list
                releaseImgsPaths = [releaseFolder + i for i in releaseImgs]
        #update table in SUT Tab with release imgs
                
        

        # Send signal to table to update with release imgs
        self.testsignal.emit()
        
  

class sutTab(QWidget):

    def __init__(self):
        super().__init__()
        self.UI()

    def UI(self):
         # Place holder for Boards Table
        boardsInfo  = {
            "Board ID": ["0x01", "0x02", "0x03","0x4"], # I2C Address of Boards scanned
            "Board Name": ["Interface Controller", "Kinematics Controller", "Joint Controller (JC1)","Vision Controller"], # Name of Board    
            "Firmware Version": ["0.0.1", "0.0.0", "0.0.0", "0.0.0"], # Current Firmware Version of Board
            "UDID": ["0x00000001", "0x00000002", "0x00000003", "0x00000004"], # Unique Device ID of Board
        }
        self.numBoards = len(boardsInfo["Board ID"])
        for i in range(self.numBoards):
            releaseImgs.append("")
        #Place holder for Release Number Table
        #Create SUT Tab #######################################################
        #Create Widgets
        self.updateTable = QTableWidget()
        self.updateTable.setColumnCount(6)
        self.updateTable.setHorizontalHeaderLabels(["Board Name", "Current Version","Upgrade Version","Custom Version", "Progress","Select"])
        self.updateTable.setRowCount(self.numBoards)
        self.updateTable.setVerticalHeaderLabels(boardsInfo["Board ID"])
        self.updateTable.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.updateTable.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.updateTable.horizontalHeader().sectionClicked.connect(self.selectAll) # Select All Check Boxes Signal
        consoleLabel = QLabel("Consol Log Output")
        consoleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outputConsole = QTextEdit()
        outputConsole.setReadOnly(True)
        #Create Table Widgets Objects 
        
        brouseBtns = []
        progressBars = []
        self.selectCheckBoxes = []
        #Add Objects to Table
        for i in range(self.numBoards):
            progressBars.append(progressBar()) # Create a list of Progress Bar Objects
            self.selectCheckBoxes.append(QCheckBox()) # Create a list of Check Box Objects
            brouseBtns.append(browsBtn()) # Create a list of Browse Button Objects
            brouseBtns[i].clicked.connect(lambda: self.browseReleases(brouseBtns.index(self.sender()))) # Browse Button Signal
            self.updateTable.setItem(i,0,QTableWidgetItem(boardsInfo["Board Name"][i]))
            self.updateTable.setItem(i,1,QTableWidgetItem(boardsInfo["Firmware Version"][i]))
            self.updateTable.setCellWidget(i,3,brouseBtns[i])
            self.updateTable.setCellWidget(i,4,progressBars[i])
            self.updateTable.setCellWidget(i,5,self.selectCheckBoxes[i])
        #expand columns to fill
        for i in range(6):
            self.updateTable.resizeColumnToContents(i)
            self.updateTable.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
        #add widgets to layout##################################################
        sutTabLayout = QVBoxLayout()
        sutTabLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(sutTabLayout)
        sutTabLayout.addWidget(self.updateTable)
        sutTabLayout.addWidget(consoleLabel)
        sutTabLayout.addWidget(outputConsole)
    #Signals and Slots#######################################################
    def updateVersion(self):
        #Update Version of Selected Boards
    
        try :
            for i in range(self.numBoards):
                self.updateTable.setItem(i,2,QTableWidgetItem(releaseImgs[i]))
        except:
            pass      

    def browseReleases(self,index):
         # Open Brouse Dialoge to select release file
        releaseFile =QFileDialog.getOpenFileName(self) # gets file path
        #update releaseImgs List
        if releaseFile[0]:
            try:
                releaseImgs[index] = releaseFile[0]
            except:
                releaseImgs.append(releaseFile[0])
            versionNumber = releaseFile[0].split("/")[-1].split('.txt')[0] # gets version number from file name
            self.updateTable.setItem(index,2,QTableWidgetItem(versionNumber)) # sets version number in table
        # TODO check if imgs are valid and compleat for the Scan Chain
        # add version number to tablle
    def selectAll(self, logicalIndex):
        # Toggles all check boxes in table
        if logicalIndex == 5:
            for checkBox in self.selectCheckBoxes:
                checkBox.toggle()
    

        



class consoleTab(QWidget):
    def __init__(self):
        super().__init__()
        self.UI()
    def UI(self):
        #Create Console Tab Widgets############################################
        consoleTabLayout = QGridLayout()
        consoleTabLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(consoleTabLayout)
        outputText = QTextEdit()
        outputText.setReadOnly(True)
        inputEntry = QLineEdit()
        sendButton = QPushButton("Send")
        sendButton.setMaximumWidth(300)
        inputEntry.setPlaceholderText("Enter Command")
        #Add Widgets to Layout####################################################
        consoleTabLayout.addWidget(outputText, 0,0,1,3)
        consoleTabLayout.addWidget(inputEntry, 1,0,1,2)
        consoleTabLayout.addWidget(sendButton, 1,2)

    #Signals and Slots#######################################################


    

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
    
class browsBtn(QPushButton):
    def __init__(self):
        super().__init__()
        self.UI()
    def UI(self):
        self.setText("Browse")
        self.setMaximumWidth(100)


    
        

# Run the program ############################################################
if __name__ == '__main__':
    app = QApplication(sys.argv) # manages the apps main event loop and starts the app
    # create class instances
    
    suttab = sutTab()
    sutstack = sutStack()
    consolestack = consoleStack()
    consoletab= consoleTab()
    sutstack.testsignal.connect(suttab.updateVersion)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
    sutstack.testsignal.connect(suttab.updateVersion)