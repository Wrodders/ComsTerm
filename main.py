# ComsTermV2 - A Console Terminal for with  MesoRobotics
# Split into 2 Sections Console and SystemUptadeTool

from curses.panel import top_panel
import sys
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt

boards = {
    'id': '1',
    'name': 'Kinematics Controller',
    'Firmware': '1.0.0',
    'UDID': '1234567890',
}




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
        leftLayout.addWidget(self.portPath, 0, 0,1,2)
        leftLayout.addWidget(scanButton, 1,0)
        leftLayout.addWidget(connectButton, 1,1)
        #Create Right Panel Stack ###################################################
        rightLayout = QVBoxLayout()
        rightLayout.setContentsMargins(0, 0, 0, 0)
        right_panel.setLayout(rightLayout)
        self.mainStack = QStackedWidget()
        self.mainStack.addWidget(consoleStack()) # Add Console Stack to Main Stack
        self.mainStack.addWidget(sutStack()) # Add System Update Tool Stack to Main Stack
        rightLayout.addWidget(self.mainStack)
        
        #Create Bottom Panel ####################################################
        #Create Bottom Panel Tab Widget #########################################
        bottomLayout = QVBoxLayout()
        bottomLayout.setContentsMargins(0, 0, 0, 0)
        bottom_panel.setLayout(bottomLayout)
        self.mainTabs = QTabWidget()
        self.mainTabs.setTabPosition(QTabWidget.TabPosition.North)
        self.mainTabs.setTabShape(QTabWidget.TabShape.Rounded)
        self.mainTabs.addTab(consoleTab(), "Console")
        self.mainTabs.addTab(sutTab(), "SUT")
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
        #Create Console Stack
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

        #Create Console Stack Layout
        consoleStackLayout = QGridLayout()
        self.setLayout(consoleStackLayout)
        consoleStackLayout.addWidget(scanBoardsButton, 0,0)
        consoleStackLayout.addWidget(connectBoardsButton, 0,1)
        consoleStackLayout.addWidget(boardTable, 1,0,1,2)
        


class   sutStack(QWidget):
    def __init__(self):
        super().__init__()
        self.UI()
    def UI(self):
        pass



class consoleTab(QWidget):
    def __init__(self):
        super().__init__()
        self.UI()
    def UI(self):
        #Create Console Tab
        consoleTabLayout = QGridLayout()
        consoleTabLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(consoleTabLayout)
        outputText = QTextEdit()
        outputText.setReadOnly(True)
        inputEntry = QLineEdit()
        sendButton = QPushButton("Send")
        sendButton.setMaximumWidth(300)
        inputEntry.setPlaceholderText("Enter Command")
        consoleTabLayout.addWidget(outputText, 0,0,1,3)
        consoleTabLayout.addWidget(inputEntry, 1,0,1,2)
        consoleTabLayout.addWidget(sendButton, 1,2)

class sutTab(QWidget):
    def __init__(self):
        super().__init__()
        self.UI()
    def UI(self):
        #Create SUT Tab
        sutTabLayout = QGridLayout()
        sutTabLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(sutTabLayout)
        

        

# Run the program
if __name__ == '__main__':
    app = QApplication(sys.argv) # manages the apps main event loop and starts the app
    window = MainWindow()
    window.show()
    sys.exit(app.exec())