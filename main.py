# ComsTermV2 - A Console Terminal for with  MesoRobotics
# Split into 2 Sections Console and SystemUptadeTool

import sys
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ComsTermV2")
        self.setGeometry(100, 100, 800, 600)
        self.UI()

    def UI(self):
        # Create Main User Interface
        
        topFrame = QFrame(self) # Create a frame for the top section
        topFrame.setFrameShape(QFrame.Shape.StyledPanel)

        #Set Up Bottom Tabs        
        bottomTab = QTabWidget(self) # Create a table widget for the bottom section
        bottomTab.addTab(consoleTab(), "Console")   # Add a tab to the tab widget
        bottomTab.addTab(sutTab(), "SUT") # Add a tab to the tab widget
        #bottomTab.currentChanged.connect(self.handleTabChange)

        
        splitter = QSplitter(Qt.Orientation.Vertical) # Create a vertical splitter
        splitter.setChildrenCollapsible(False)
        
        vbox = QVBoxLayout(self)
        self.setLayout(vbox)
        vbox.addWidget(splitter)

        splitter.addWidget(topFrame)
        splitter.addWidget(bottomTab)
        splitter.setStretchFactor(1, 1)
    
    
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

        self.cmd_Entry = QLineEdit(self)
        self.cmd_Entry.setPlaceholderText("Enter Command")
        self.cmd_Entry.returnPressed.connect(lambda: self.handleSend())

        send_Button = QPushButton("Send")
        send_Button.setMaximumWidth(150)
        send_Button.clicked.connect(lambda: self.handleSend())

        # add widgets to grid
        grid.addWidget(output_Text, 0, 0, 1, 3)
        grid.addWidget(self.cmd_Entry, 1, 0, 1, 2)
        grid.addWidget(send_Button, 1, 2)

    def handleSend(self):
        print("Sending")
        readCmds(self.cmd_Entry.text())

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