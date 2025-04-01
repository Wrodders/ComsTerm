from PyQt6.QtWidgets import QFrame, QComboBox, QVBoxLayout, QFormLayout, QLineEdit, QLabel, QCheckBox, QStackedWidget, QPushButton, QGridLayout, QWidget, QMessageBox, QFileDialog
from PyQt6.QtCore import QThread, pyqtSignal
from functools import partial
from core.commander import ZMQCommander
from common.logger import getmylogger
from client.paramTable import ParamTable, ParamRegUI
from client.menus import ProgressBar
from client.plot import LinePlot, PlotCfg, LinePlotCfg
from common.sigGenCLI import *
from client.menus import SettingsUI
from client.controller import ControllerCfg
from common.messages import TopicMap, Topic
import time
import numpy as np
from dataclasses import dataclass

from common.zmqutils import ZmqPub, Transport, Endpoint

import queue
from PyQt6.QtGui import QDoubleValidator

class ParamComboConfig(QFrame):
    def __init__(self, cmdr: ZMQCommander, numParams: int):
        super().__init__()
        self.cmdr = cmdr
        # Node Id Config
        self.nodeIdCombo = QComboBox()  # Node Id available
        self.nodeIdCombo.addItems([nodeId for nodeId in self.cmdr.paramRegMap.nodes])
        self.nodeIdCombo.setMinimumWidth(120)
        self.nodeIdCombo.currentTextChanged.connect(self.updateParamCombo)

        self.vbox = QVBoxLayout()
       
        # Form Layout
        self.formLayout = QFormLayout()
        self.formLayout.addRow("Node Id", self.nodeIdCombo)
        self.vbox.addLayout(self.formLayout)

        self.paramComboList = []
        for i in range(numParams) if numParams <= 4 else range(4):
            self.paramCombo = QComboBox()
            self.paramCombo.addItems([name for name in self.cmdr.paramRegMap.getClientParameters(self.nodeIdCombo.currentText())])
            self.paramCombo.setMinimumWidth(120)
            self.paramComboList.append(self.paramCombo)
            self.formLayout.addRow(f"Param {i}", self.paramCombo)
        self.setLayout(self.vbox)

    def updateParamCombo(self, nodeId):
        for paramCombo in self.paramComboList:
            paramCombo.clear()
            paramCombo.addItems([name for name in self.cmdr.paramRegMap.getClientParameters(nodeId)])


class PubComboConfig(QFrame): 
    def __init__(self, topicMap: TopicMap):
        super().__init__()
        self.topicMap = topicMap
        self.vbox = QVBoxLayout()
        self.formLayout = QFormLayout()
        self.setLayout(self.vbox)
        self.topicCombo = QComboBox()
        self.topicCombo.addItems(self.topicMap.get_topic_names())
        self.topicCombo.setMinimumWidth(120)
        self.formLayout.addRow("Topic", self.topicCombo)
        self.vbox.addLayout(self.formLayout)

    def updateTopicCombo(self, topicMap: TopicMap):
        self.topicCombo.clear()
        self.topicCombo.addItems(topicMap.get_topic_names())
    
class PulseSigSettings(SettingsUI):
    def __init__(self, config: PulseSigParameters):
        super().__init__()
        self.config = config
        self.vbox = QVBoxLayout()
        self.setLayout(self.vbox)
        self.initialValue = QLineEdit(str(self.config.initial_value))
        self.onTime = QLineEdit(str(self.config.on_time))
        self.onValue = QLineEdit(str(self.config.on_value))
        self.offTime = QLineEdit(str(self.config.off_time))
        self.offValue = QLineEdit(str(self.config.off_value))
        self.formLayout = QFormLayout()
        self.formLayout.addRow("Initial Value", self.initialValue)
        self.formLayout.addRow("On Time", self.onTime)
        self.formLayout.addRow("On Value", self.onValue)
        self.formLayout.addRow("Off Time", self.offTime)
        self.formLayout.addRow("Off Value", self.offValue)
        self.vbox.addLayout(self.formLayout)

    def updateConfig(self):
        self.config.initial_value = float(self.initialValue.text())
        self.config.on_time = float(self.onTime.text())
        self.config.on_value = float(self.onValue.text())
        self.config.off_time = float(self.offTime.text())
        self.config.off_value = float(self.offValue.text())
        return self.config
    
class SineSigSettings(SettingsUI):
    def __init__(self, config: SineSigParameters):
        super().__init__()
        self.log = getmylogger(__name__)
        self.config = config
        self.vbox = QVBoxLayout()
        self.setLayout(self.vbox)
        self.frequency = QLineEdit(str(self.config.frequency))
        self.phase = QLineEdit(str(self.config.phase))
        self.amplitude = QLineEdit(str(self.config.amplitude))
        self.formLayout = QFormLayout()
        self.formLayout.addRow("Frequency", self.frequency)
        self.formLayout.addRow("Phase", self.phase)
        self.formLayout.addRow("Amplitude", self.amplitude)
        self.vbox.addLayout(self.formLayout)

    def updateConfig(self) -> SineSigParameters:
        try:
            self.config.frequency = float(self.frequency.text())
            self.config.phase = float(self.phase.text())
            self.config.amplitude = float(self.amplitude.text())
        except ValueError as e:
            self.log.error(f"Error in SineSigSettings {e}")
        return self.config
    
class ChirpSigSettings(SettingsUI):
    def __init__(self, config: ChirpSigParameters):
        super().__init__()
        self.log = getmylogger(__name__)
        self.config = config
        self.vbox = QVBoxLayout()
        self.setLayout(self.vbox)
        self.f0 = QLineEdit(str(self.config.f0))
        self.f1 = QLineEdit(str(self.config.f1))
        self.amplitude = QLineEdit(str(self.config.amplitude))
        self.formLayout = QFormLayout()
        self.formLayout.addRow("f0", self.f0)
        self.formLayout.addRow("f1", self.f1)
        self.formLayout.addRow("Amplitude", self.amplitude)
        self.vbox.addLayout(self.formLayout)

    def updateConfig(self) -> ChirpSigParameters:
        try:
            self.config.f0 = float(self.f0.text())
            self.config.f1 = float(self.f1.text())
            self.config.amplitude = float(self.amplitude.text())
        except ValueError as e:
            self.log.error(f"Error in ChirpSigSettings {e}")
        return self.config
    
class RampSigSettings(SettingsUI):
    def __init__(self, config: RampSigParameters):
        super().__init__()
        self.log = getmylogger(__name__)
        self.config = config
        self.vbox = QVBoxLayout()
        self.setLayout(self.vbox)
        self.slope = QLineEdit(str(self.config.slope))
        self.formLayout = QFormLayout()
        self.formLayout.addRow("Slope", self.slope)
        self.vbox.addLayout(self.formLayout)

    def updateConfig(self) -> RampSigParameters:
        try:
            self.config.slope = float(self.slope.text())
        except ValueError as e:
            self.log.error(f"Error in RampSigSettings {e}")
        return self.config

class SigGenPanel(QFrame):
    def __init__(self):
        super().__init__()
        self.log = getmylogger(__name__)
        self.vbox = QVBoxLayout()
        # Stack of signal type settings
        self.settingsStack = QStackedWidget()
        # Signal Settings
        self.sineSigSettings = SineSigSettings(SineSigParameters())
        self.pulseSigSettings = PulseSigSettings(PulseSigParameters())
        self.chirpSigSettings = ChirpSigSettings(ChirpSigParameters())
        self.rampSigSettings = RampSigSettings(RampSigParameters())
        # Add settings to stack
        self.settingsStack.addWidget(self.sineSigSettings)
        self.settingsStack.addWidget(self.pulseSigSettings)
        self.settingsStack.addWidget(self.chirpSigSettings)
        self.settingsStack.addWidget(self.rampSigSettings)

        # Signal Type Combo
        self.signalTypeCombo = QComboBox()
        self.signalTypeCombo.addItems(["Sine", "Ramp", "Chirp", "Step"])
        self.signalTypeCombo.currentTextChanged.connect(self.updateSettingsStack)

        self.durationEntry = QLineEdit()
        self.durationEntry.setText(str(1.0))
        self.durationEntry.setValidator(QDoubleValidator(0.0, 10.0, 5))
        self.durationEntry.textChanged.connect(self.updateBufSizeLabel)

        self.samplePeriodEntry = QLineEdit()
        self.samplePeriodEntry.setText(str(0.001))
        self.samplePeriodEntry.setValidator(QDoubleValidator(0.0, 1.0, 5))
        self.samplePeriodEntry.textChanged.connect(self.updateBufSizeLabel)

        self.buffsizelabel = QLabel("Buffer Size")
        
        self.loopCheckBox = QCheckBox("Loop Signal")
        self.loopCheckBox.setChecked(False)
        
        self.formLayout = QFormLayout()
        self.formLayout.addRow("Duration [s]", self.durationEntry)
        self.formLayout.addRow("Sample Period [s]", self.samplePeriodEntry)
        self.vbox.addWidget(self.signalTypeCombo)
        self.vbox.addWidget(self.settingsStack)
        self.vbox.addLayout(self.formLayout)
        self.vbox.addWidget(self.buffsizelabel)
        self.vbox.addWidget(self.loopCheckBox)
        self.setLayout(self.vbox)

    def updateSettingsStack(self, _):
        self.settingsStack.setCurrentIndex(self.signalTypeCombo.currentIndex())

    def updateBufSizeLabel(self):
        self.buffsizelabel.setText(f"Buffer Size: {self.calculateBufferLength()}")

    def calculateBufferLength(self) -> int:
        try:
            duration = float(self.durationEntry.text() if self.durationEntry.text() != "" else 0)
            samplePeriod = float(self.samplePeriodEntry.text() if self.samplePeriodEntry.text() != "" else 0)
            if samplePeriod == 0:
                return 0
            return int(duration / samplePeriod)
        except ValueError as e:
            self.log.error(f"Error in calculateBufferLength {e}")
            return 0        

# ============================
# Persistent Thread for Signal Streaming using a Queue
# ============================
class SignalStreamerThread(QThread):
    finishedStreaming = pyqtSignal()
    progress = pyqtSignal(int)  # emits progress percentage

    def __init__(self, cmdr: ZMQCommander, parent=None):
        super().__init__(parent)
        self.log = getmylogger(__name__)
        self.cmdr = cmdr
        self._stop_flag = False
        self.queue = queue.Queue()  # holds (signal_data, sample_period, nodeID, paramName)
        self.pub = ZmqPub(Transport.INPROC, Endpoint.SIG)
        self.pub.bind()

    def run(self):
        while not self._stop_flag:
            try:
                task = self.queue.get(block=True, timeout=0.1)
            except queue.Empty:
                continue
            if task is None:
                continue
            signal_data, sample_period, nodeID, paramName = task
            total_samples = len(signal_data)
            for i, sample in enumerate(signal_data):
                if self._stop_flag:
                    break
                try:
                    self.cmdr.sendSetCmd(nodeID, paramName, str(round(sample, 4)))
                    self.pub.sendTimestamped("sig/signal", str(round(sample, 4)), str(time.time()))
                except Exception as e:
                    self.log.error(f"Error sending signal: {e}")
                progress_val = int((i + 1) * 100 / total_samples)
                self.progress.emit(progress_val)
                time.sleep(sample_period)
            
            time.sleep(0.5)  # HACK
            self.finishedStreaming.emit()

            self.cmdr.sendSetCmd(nodeID, paramName, "0")
            self.pub.sendTimestamped("sig/signal", "0", str(time.time()))
        
        self.log.info("SignalStreamerThread stopped")

    def pushSignal(self, signal_data, sample_period, nodeID, paramName):
        self.queue.put((signal_data, sample_period, nodeID, paramName))

    def stop(self):
        self._stop_flag = True

# ============================
# Main Signal Generator Application
# ============================
class SigGenApp(QWidget):
    def __init__(self):
        super().__init__()
        self.log = getmylogger(__name__)
        self.cmdr = ZMQCommander("robotConfig.json")
        self.setWindowTitle("Signal Generator")

        # Set up the signal generator UI
        self.sigGenPanel = SigGenPanel()

        # Set up Signal Viewer UI (preview)
        self.plotConfig = PlotCfg()
        self.plotConfig.name = "SigGen Plot"
        self.plotConfig.protocol = ("sig/preview", "sig/signal")
        self.plotConfig.maxPlotSeries = 1
        # Use the calculated buffer length for streaming (if applicable)
        self.plotConfig.sampleBufferLen = self.sigGenPanel.calculateBufferLength()
        self.plotConfig.plotType = "LINE"
        self.plotConfig.typeCfg = LinePlotCfg()
        self.plotConfig.typeCfg.yrange = (-1, 1)
        
        topicMap = TopicMap()
        topicMap.register("sig/preview", "0", ["msg", "timestamp"], ":")
        topicMap.register("sig/signal", "1", ["msg", "timestamp"], ":")
        self.plot = LinePlot(topicMap=topicMap, config=self.plotConfig,
                             transport=Transport.INPROC, endpoint=Endpoint.SIG)
        
        #make the preview line dashed
        self.plot.ax.lines[0].set_linestyle("--")
        self.plot.ax.lines[1].set_linewidth(1)

        # Set up signal output stream UI
        self.paramConfig = ParamComboConfig(self.cmdr, 1)
        self.recordButton = QPushButton("Record Signal")
        self.recordButton.clicked.connect(self.saveSignal)
        self.playButton = QPushButton("Play Signal")
        self.playButton.clicked.connect(self.playSignal)
        self.progressBar = ProgressBar(timeout=1000)
        self.previewButton = QPushButton("Preview Signal")
        self.previewButton.clicked.connect(self.previewSignal)

        grid = QGridLayout()
        grid.addWidget(self.plot, 0, 0, 4, 4)
        grid.addWidget(self.progressBar, 4, 0, 2, 4)
        grid.addWidget(self.sigGenPanel, 0, 4, 2, 2)
        grid.addWidget(self.paramConfig, 2, 4, 2, 2)
        grid.addWidget(self.previewButton, 4, 4, 1, 1)
        grid.addWidget(self.recordButton, 4, 5, 1, 1)
        grid.addWidget(self.playButton, 5, 4, 1, 2)
        self.setLayout(grid)

        # Create and start the persistent signal streaming thread.
        self.signalStreamer = SignalStreamerThread(self.cmdr)
        self.signalStreamer.progress.connect(self.updateProgressBar)
        self.signalStreamer.finishedStreaming.connect(self.handleStreamEnd)
        self.signalStreamer.start()

    def updateProgressBar(self, value: int):
        self.progressBar.setValue(value)

    def handleStreamEnd(self):
        self.plot.clearData("sig/signal")
        self.progressBar.setValue(0)

    def previewSignal(self):
        """Generate and preview the complete signal without streaming it sample-by-sample."""
        config = self.grabSettings()
        if isinstance(config, BaseSigParameters):
            try:
                signal_series, _ = generate_signal(config)
            except Exception as e:
                QMessageBox.critical(self, "Signal Generation Error", f"Error generating signal: {e}")
                return
            self.plot.clearData("sig/preview")
            # Draw the full generated signal (variable length)
            self.plot.drawLineOnPlot("sig/preview", signal_series)

    def grabSettings(self) -> BaseSigParameters | None:
        currentStack = self.sigGenPanel.settingsStack.currentWidget()
        if isinstance(currentStack, SettingsUI):
            try:
                config = currentStack.updateConfig()
                # Update sample buffer length for streaming
                self.plotConfig.sampleBufferLen = self.sigGenPanel.calculateBufferLength()
                config.duration = float(self.sigGenPanel.durationEntry.text())
                config.sample_period = float(self.sigGenPanel.samplePeriodEntry.text())
            except ValueError as e:
                QMessageBox.critical(self, "Input Error", f"Invalid input: {e}")
                return None
            if self.plotConfig.sampleBufferLen > 1024*1024:
                QMessageBox.critical(self, "Buffer Size Error", "Buffer size too large (>)")
                return None
            return config
        return None

    def playSignal(self):
        """Generate the signal and push it to the persistent streaming thread."""
        config = self.grabSettings() 
        if isinstance(config, BaseSigParameters):
            try:
                signal_series, _ = generate_signal(config)
            except Exception as e:
                QMessageBox.critical(self, "Signal Generation Error", f"Error generating signal: {e}")
                return
            self.signalStreamer.pushSignal(signal_series, config.sample_period, 
                                           self.paramConfig.nodeIdCombo.currentText(), 
                                           self.paramConfig.paramComboList[0].currentText())
            self.log.debug("Pushed signal for streaming")

    def saveSignal(self):
        """Generate and save the complete signal to a CSV file."""
        currentStack = self.sigGenPanel.settingsStack.currentWidget()
        if isinstance(currentStack, SettingsUI):
            try:
                config = currentStack.updateConfig()
                self.plotConfig.sampleBufferLen = self.sigGenPanel.calculateBufferLength()
                config.duration = float(self.sigGenPanel.durationEntry.text())
                config.sample_period = float(self.sigGenPanel.samplePeriodEntry.text())
            except ValueError as e:
                QMessageBox.critical(self, "Input Error", f"Invalid input: {e}")
                return
            try:
                signal_series, time_series = generate_signal(config)
            except Exception as e:
                QMessageBox.critical(self, "Signal Generation Error", f"Error generating signal: {e}")
                return
            filename, _ = QFileDialog.getSaveFileName(
                self, "Save Signal Data", "", "CSV Files (*.csv);;All Files (*)"
            )
            if filename:
                try:
                    data = np.column_stack((time_series, signal_series))
                    np.savetxt(filename, data, delimiter=",", header="Time,Signal", comments="")
                    self.log.info(f"Signal recorded to {filename}")
                except Exception as e:
                    QMessageBox.critical(self, "File Save Error", f"Error saving file: {e}")

    def closeEvent(self, event):
        if self.signalStreamer is not None and self.signalStreamer.isRunning():
            self.signalStreamer.stop()
            self.signalStreamer.wait()

        self.log.info("Closing SigGenApp")
        event.accept()
