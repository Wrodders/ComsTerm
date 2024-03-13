
from PyQt6 import QtCore
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *

class ConnectionsDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Connection Settings")
        self.setFixedSize(500, 300)  # Set dialog size to fixed size

        self.vBox = QVBoxLayout()

        # Table to display device connections
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Connection Method", "Device Path", "Status"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.vBox.addWidget(self.table)

        # Sub-widget for adding connections
        self.addConnectionWidget = QWidget()
        self.addConnectionLayout = QHBoxLayout()

        # Combo box for selecting connection method
        self.connectionMethodCombo = QComboBox()
        self.connectionMethodCombo.addItems(["Serial", "UDP", "ZMQ"])
        self.addConnectionLayout.addWidget(self.connectionMethodCombo)

        # Button to connect device
        self.connectButton = QPushButton("Connect")
        self.connectButton.clicked.connect(self.addConnection)
        self.addConnectionLayout.addWidget(self.connectButton)

        # Button to disconnect device
        self.disconnectButton = QPushButton("Disconnect")
        self.disconnectButton.clicked.connect(self.disconnectConnection)
        self.addConnectionLayout.addWidget(self.disconnectButton)

        self.addConnectionWidget.setLayout(self.addConnectionLayout)
        self.vBox.addWidget(self.addConnectionWidget)

        self.setLayout(self.vBox)

    def addConnection(self):
        method = self.connectionMethodCombo.currentText()
        devicePath = "/path/to/device"  # Replace with actual device path
        status = "Connected"  # Assume connected for simplicity
        rowPosition = self.table.rowCount()
        self.table.insertRow(rowPosition)
        self.table.setItem(rowPosition, 0, QTableWidgetItem(method))
        self.table.setItem(rowPosition, 1, QTableWidgetItem(devicePath))
        self.table.setItem(rowPosition, 2, QTableWidgetItem(status))


    def connectDevice(self):
        method = self.connectionMethodCombo.currentText()
        if method == "serial":
            serial_device = SerialDevice()
            try:
                devices = serial_device.scan()
                if len(devices) == 0:
                    QMessageBox.warning(self, "No Devices", "No devices found.")
                elif len(devices) == 1:
                    QMessageBox.information(self, "Device Found", f"Device found: {devices[0]}")
                else:
                    device, ok = QInputDialog.getItem(self, "Select Device", "Available Devices:", devices, 0, False)
                    if ok:
                        QMessageBox.information(self, "Device Selected", f"Device selected: {device}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error occurred while scanning devices: {str(e)}")
                del serial_device


    def disconnectConnection(self):
        selectedRow = self.table.currentRow()
        if selectedRow != -1:
            self.table.removeRow(selectedRow)
