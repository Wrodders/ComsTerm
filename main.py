# basic_window.py
# Import necessary modules
import sys
import pandas as pd
import random

from PyQt6.QtWidgets import (QApplication,QWidget, QLabel, 
                            QPushButton, QLineEdit, QHBoxLayout, QVBoxLayout,
                            QLineEdit, QTextEdit, QGridLayout, QComboBox,
                            QFrame,QSplitter,QMenuBar,QTabWidget,QDialog,QButtonGroup,
                            QMessageBox,QTableWidget,QTableWidgetItem,QCheckBox,QStackedWidget
                            )
from PyQt6.QtCore import Qt


        




class MainWindow(QWidget):
    def __init__(self):
        """ Constructor for Empty Window Class """
        super().__init__()
        self.initializeUI()
    def initializeUI(self):
        """Set up the application."""
        self.setGeometry(200, 100, 800, 800) # x, y, width, height
        self.setWindowTitle("ComsTerm")



        self.setUpUI()
        self.show() # Display the window on the screen
        login_dlg = Login()
        if (login_dlg.exec()):
           print("Login Successful")
        else:
           print("Login Failed")
           sys.exit()
    # line_edits.py
    def setUpUI(self):
        vbox = QVBoxLayout(self)
        topFrame = QFrame(self) # Create a frame for the top section

        #Set Up Bottom Tabs        
        bottomTab = QTabWidget(self) # Create a table widget for the bottom section
        bottomTab.addTab(consoleTab(), "Console")   # Add a tab to the tab widget
        bottomTab.addTab(sutTab(), "SUT") # Add a tab to the tab widget
        bottomTab.currentChanged.connect(self.handleTabChange)

        
        splitter = QSplitter(Qt.Orientation.Vertical) # Create a vertical splitter
        splitter.setChildrenCollapsible(False)
        
        splitter.addWidget(topFrame)
        splitter.addWidget(bottomTab)
        splitter.setStretchFactor(1, 2)
        vbox.addWidget(splitter)
        self.setLayout(vbox)

        self.setUpMenuBar(vbox)
        self.setUpTopFrame(topFrame)
        
    def setUpMenuBar(self,vbox):
        menubar = QMenuBar()
        vbox.addWidget(menubar)
        actionFile = menubar.addMenu("File")
        actionFile.addAction("Open")
        actionFile.addAction("Save")
        

        actionView = menubar.addMenu("View")
        actionView.addAction("Console")
        actionView.addAction("Device Settings")
        actionView.addAction("SUT")
        actionView.addAction("Logs")
        actionView.addSeparator()
        actionView.addAction("Augmented Reality")

    def setUpTopFrame(self, topFrame):
        # Set up Splitter for top frame
        tbox = QHBoxLayout(topFrame)
        tbox.setContentsMargins(0,0,0,0)
        
        # Create Left Frane
        lFrame = QFrame(self)
        #lFrame.setFrameShape(QFrame.Shape.StyledPanel)
       
        # Create MultiTabWindow for Right Section
        self.mainStack = QStackedWidget(self)

        splitter = QSplitter(Qt.Orientation.Horizontal) # Create a horizontal splitter
        splitter.setChildrenCollapsible(False)

        splitter.addWidget(lFrame) # Add the left frame to the splitter
        splitter.addWidget(self.mainStack) # Add the MultiTabWindow to the splitter
        splitter.setStretchFactor(2, 1)
        tbox.addWidget(splitter)       # Add the splitter with sub frames to the top frame

        # Left Frame Setup #####################################################
        ports_Entry = QLineEdit()
        ports_Entry.setPlaceholderText("Enter Port Path")
        
        scan_Button = QPushButton("Scan")
        scan_Button.setMaximumWidth(150)
        connect_Button = QPushButton("Connect")
        connect_Button.setMaximumWidth(150)

        self.conType_ComboBox = QComboBox(self)
        self.conType_ComboBox.addItems(["OTA Programer", "Ethernet", "USB"])
        self.conType_ComboBox.setMaximumWidth(250)
    
        scan_Button.clicked.connect(self.handleScan)
        connect_Button.clicked.connect(self.handleConnect)

        f = QFrame(lFrame)

        # add widgets to left frame
        lGrid = QGridLayout(lFrame) # Create a grid layout for the left frame
        lGrid.addWidget(ports_Entry, 0, 0,1,2)
        lGrid.addWidget(scan_Button, 1, 0)
        lGrid.addWidget(connect_Button, 1, 1 )
        lGrid.addWidget(self.conType_ComboBox, 0, 2)
        lGrid.addWidget(f, 2, 0)

        # Right Frame Setup ####################################################
        
        self.mainStack.addWidget(slavConn())
        self.mainStack.addWidget(sutImgLoader())





    def handleTabChange(self):
        self.mainStack.setCurrentIndex(self.sender().currentIndex())
        print(1)


    ##### Functions for handling signals #####

    def handleScan(self,):
        print("Scanning")
        print(self.conType_ComboBox.currentText())
        
    def handleConnect(self):
        print("Connecting")




## Sub Window Classes ##

class slavConn(QWidget):
    def __init__(self):
        super().__init__()
        self.initializeUI()
    def initializeUI(self):

        # create Widgets
        scanSlaves_Button = QPushButton("Scan Slaves")
        scanSlaves_Button.setMaximumWidth(150)
        connectSlaves_Button = QPushButton("Connect to Slaves")
        connectSlaves_Button.setMaximumWidth(150)

        table= QTableWidget()
        table.setColumnCount(2)
        table.setRowCount(4)
        table.setHorizontalHeaderLabels(["Slave ID", "Slave Name"])

        # add widgets to layout
        grid = QGridLayout(self)
        grid.addWidget(scanSlaves_Button, 0, 0)
        grid.addWidget(connectSlaves_Button, 0, 1)
        grid.addWidget(table, 1, 0,1,2)
        self.setLayout(grid)


class sutImgLoader(QWidget):
    def __init__(self):
        super().__init__()
        self.initializeUI()
    def initializeUI(self):
        # create Widgets
        imgPath_Entry = QLineEdit()
        imgPath_Entry.setPlaceholderText("Enter Image Path")
        dwldImg_Button = QPushButton("Download")
        dwldImg_Button.setMaximumWidth(150)
        upldImg_Button = QPushButton("Upload")
        upldImg_Button.setMaximumWidth(150)
        
        # add widgets to layout
        grid = QGridLayout(self)
        grid.addWidget(imgPath_Entry, 0, 0,1,2)
        grid.addWidget(dwldImg_Button, 1, 0)
        grid.addWidget(upldImg_Button, 1, 1)
        f = QFrame(self)
        grid.addWidget(f, 2, 0,1,2)




    
       

        



class Login(QDialog):
    def __init__(self):
        super().__init__()
        self.initializeUI()
    def initializeUI(self):
        self.setWindowTitle("Login")
    

        self.uName_Entry = QLineEdit()
        self.uName_Entry.setPlaceholderText("Enter Username")
        self.uName_Entry.setMaximumWidth(250)
        self.pWord_Entry = QLineEdit()
        self.pWord_Entry.setPlaceholderText("Enter Password")
        self.pWord_Entry.setMaximumWidth(250)

        self.login_Button = QPushButton("Login")
        self.login_Button.setMaximumWidth(150)
        self.login_Button.clicked.connect(self.handleLogin)

        #add widgets to layout
        vbox = QVBoxLayout()
        vbox.addWidget(self.uName_Entry)
        vbox.addWidget(self.pWord_Entry)
        vbox.addWidget(self.login_Button)
        self.setLayout(vbox)
        
    def handleLogin(self):
        print("Login")
        if(self.uName_Entry.text() == "admin" and self.pWord_Entry.text() == "admin"):
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Invalid Username or Password")
            self.uName_Entry.clear()
            self.pWord_Entry.clear()
            self.uName_Entry.setFocus()
        
class consoleTab(QWidget):
    def __init__(self):
        super().__init__()
        self.initializeUI()
    def initializeUI(self):
        grid = QGridLayout()
        grid.setContentsMargins(0,0,0,0)
        self.setLayout(grid)

        # create Widgets
        output_Text = QTextEdit()
        output_Text.setReadOnly(True)
        output_Text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)

        cmd_Entry = QLineEdit()
        cmd_Entry.setPlaceholderText("Enter Command")
        cmd_Entry.returnPressed.connect(self.handleSend)

        send_Button = QPushButton("Send")
        send_Button.setMaximumWidth(150)
        send_Button.clicked.connect(self.handleSend)

        # add widgets to grid
        grid.addWidget(output_Text, 0, 0, 1, 3)
        grid.addWidget(cmd_Entry, 1, 0, 1, 2)
        grid.addWidget(send_Button, 1, 2)

    def handleSend(self):
        print("Sending")

class sutTab(QWidget):
    def __init__(self):
        super().__init__()
        self.initializeUI()
    def initializeUI(self):
        vbox = QVBoxLayout()
        vbox.setContentsMargins(0,0,0,0)
        self.setLayout(vbox)
        

        



    

                

# Run the program
if __name__ == '__main__':
    app = QApplication(sys.argv) # manages the apps main event loop and starts the app
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
    