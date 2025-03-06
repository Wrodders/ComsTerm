from PyQt6.QtWidgets import QFrame, QTabWidget, QVBoxLayout, QScrollArea, QWidget, QLabel, QPushButton, QStackedWidget, QLineEdit, QHBoxLayout
from PyQt6.QtCore import pyqtSignal


from functools import partial


from client.menus import ProgressBar
from common.logger import getmylogger
from core.commander import ZMQCommander

class ParamTableApp(QFrame):
    """
    Generic Parameter Table App - Implements GET SET on Parameters
    Each Nodes Parameters are displayed in a tab
    """
    def __init__(self, cmdr: ZMQCommander):
        super().__init__()
        self.log = getmylogger(__name__)
        self.cmdr = cmdr
        self.tabs = QTabWidget()  
        self.tabs.setTabsClosable(False)
        self.nodeTabs = []
       
        for node_name, node_params in cmdr.paramRegMap.getAllParameters().items():
           
            description = node_params.get('description', "")
            if not isinstance(description, str):
                description = str(description)
            paramTable = ParamTable(paramNames=list(node_params.keys()), description=description)
            self.tabs.addTab(paramTable, node_name)
            self.nodeTabs.append(paramTable)
            # Connect App Signals to Commander
            for paramUI in paramTable.paramTable:
                if isinstance(paramUI, ParamRegUI):
                    paramUI.get_btn.clicked.connect(
                        partial(self.cmdr.sendGetCmd, nodeID=node_name, paramName=paramUI.label.text()))
                    paramUI.set_btn.clicked.connect(
                        lambda checked, pui=paramUI: self.cmdr.sendSetCmd(
                            nodeID=self.tabs.tabText(self.tabs.currentIndex()),
                            paramName=pui.label.text(),
                            value=pui.value_entry.text()
                        )
                    )
        vbox = QVBoxLayout()
        vbox.addWidget(self.tabs)
        self.setLayout(vbox)
        
    def closeEvent(self, event):
        self.log.info("Closing ParamTable")
        event.accept() 

class ParamTable(QWidget):
    def __init__(self, paramNames: list[str], description: str = ""):
        super().__init__()
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True) 
        vBox = QVBoxLayout()
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.paramTable = []
       
        for paramName in paramNames:
            paramRegUI = ParamRegUI(paramName, description)
            self.paramTable.append(paramRegUI)
            self.scroll_layout.addWidget(paramRegUI)
        
        self.scroll_area.setWidget(self.scroll_content)
        vBox.addWidget(self.scroll_area) 
        self.setLayout(vBox)
        self.scroll_area.setWidget(self.scroll_content)
        vBox.addWidget(self.scroll_area) 
        # add a space at the bottom
        vBox.addStretch(1)
        self.setLayout(vBox)


class ParamRegUI(QWidget):
    valueUpdated = pyqtSignal(str)  # Signal to update the value entry

    def __init__(self, paramName: str, description: str = ""):
        super().__init__()
        self.descriptionText = description
        self.label = QLabel(paramName)
        self.label.setToolTip(description)

        self.get_btn = QPushButton("Get")
        self.get_btn.setMaximumWidth(50)
        self.set_btn = QPushButton("Set")
        self.set_btn.setMaximumWidth(50)

        self.stack = QStackedWidget()
        self.value_entry = QLineEdit()
        self.value_entry.setMaximumWidth(200)
        self.value_entry.setMaximumHeight(30)
        self.progress_bar = ProgressBar(timeout=500)

        self.stack.addWidget(self.value_entry)  # Index 0
        self.stack.addWidget(self.progress_bar)  # Index 1

        self.get_btn.clicked.connect(self.get_handle)
        self.progress_bar.timeoutSig.connect(self.restore_input)
        self.valueUpdated.connect(self.update_value)

        hbox = QHBoxLayout()
        hbox.addWidget(self.label)
        # add space between label and buttons
        hbox.addStretch(1)
        hbox.addWidget(self.stack)
        hbox.addWidget(self.get_btn)
        hbox.addWidget(self.set_btn)
        self.setLayout(hbox)

    def get_handle(self):
        """ Handles 'Get' button click: disables button, swaps to progress bar. """
        self.get_btn.setEnabled(False)
        self.stack.setCurrentIndex(1)  # Show progress bar
        self.progress_bar.timer.start(100)  # Start progress bar timer
    def restore_input(self):
        """ Restores the input field and re-enables the Get button after timeout. """
        self.stack.setCurrentIndex(0)  # Swap back to line edit
        self.get_btn.setEnabled(True)

    def update_value(self, value):
        """ Updates the input field with the new value and restores UI immediately. """
        self.value_entry.setText(value)
        self.restore_input()  # Swap back early if a value is received before timeout