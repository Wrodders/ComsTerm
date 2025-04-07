import os
import re
import csv
import sys
import signal
from functools import partial
from datetime import datetime
from typing import TextIO
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from core.commander import ZMQCommander
from common.logger import getmylogger
from client.paramTable import ParamTable, ParamRegUI
from client.menus import ProgressBar
from client.plot import LinePlot, PlotCfg, LinePlotCfg
from client.menus import SettingsUI
from client.controller import ControllerCfg
from common.messages import TopicMap, Topic
from common.zmqutils import ZmqPub, Transport, Endpoint, ZmqSub
from client.menus import DataSeriesTable, ProgressBar, SettingsUI, FileExplorer, DataSeriesTableSettings


class RecorderThread(QThread):
    progress = pyqtSignal(int)
    error = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, filename, subscriptions, topic_map, transport, endpoint):
        super().__init__()
        self.filename = filename
        self.subscriptions = subscriptions
        self.topic_map = topic_map
        self.transport = transport
        self.endpoint = endpoint
        self._stopped = False
        self.sub = None

    def run(self):
        try:
            self.sub = ZmqSub(transport=self.transport, endpoint=self.endpoint)
            for topicname in self.subscriptions:
                self.sub.addTopicSub(topicname)
                print(f"Subscribed to {topicname}")
            self.sub.connect()

            os.makedirs(os.path.dirname(self.filename), exist_ok=True)
            current_file = None
            writer = None


            while not self._stopped:
                if current_file is None or current_file.closed:
                    current_file, writer, headers = self.initialize_file()
                
                try:
                    topic_name, msg, timestamp = self.sub.receive()
                except TimeoutError:
                    continue

                topic = self.topic_map.get_topic_by_name(topic_name)
                if not isinstance(topic, Topic):
                    continue
                
                if(topic.nArgs > 2): # HACK makes data-points shallow vs deep
                        msgArgsVal = msg.split(topic.delim)
                        msgSubTopics  = [f"{topic}/{argname}" for argname in topic.args[:-1]]# HACK omit timestamp from arg names
                        if len(msgArgsVal) == len(msgSubTopics) :  # check all data is present
                            row = [timestamp] + msgArgsVal
                            if writer is not None:
                                writer.writerow(row)
                                self.progress.emit(1)
                else:
                    row = [timestamp] + [msg]
                    if writer is not None:
                        writer.writerow(row)
                    self.progress.emit(1)

                if current_file.tell() > 5 * 1024 * 1024:  # 5MB
                    current_file.close()
                    self.rotate_file()
                    current_file, writer, headers = self.initialize_file()

        except Exception as e:
            self.error.emit(f"Recording error: {str(e)}")
        finally:
            if current_file and not current_file.closed:
                current_file.close()
            self.finished.emit()

    def initialize_file(self):
        try:
            file = open(self.filename, 'w', newline='')
            writer = csv.writer(file)
            headers = ['timestamp'] 
            for topic_name in self.subscriptions:
                topic = self.topic_map.get_topic_by_name(topic_name)
                if not isinstance(topic, Topic):
                    continue
                for arg in topic.args[:-1]: # HACK omit timestamp from arg names
                    headers.append(f"{topic_name}/{arg}")
                    
            writer.writerow(headers)
            return file, writer, headers
        except IOError as e:
            self.error.emit(f"Failed to open file: {str(e)}")
            raise

    def rotate_file(self):
        try:
            base, ext = os.path.splitext(self.filename)
            dir_name = os.path.dirname(self.filename)
            max_index = 0
            pattern = re.compile(rf'^{re.escape(base)}_(\d+){re.escape(ext)}$')
            
            for filename in os.listdir(dir_name):
                match = pattern.match(filename)
                if match:
                    index = int(match.group(1))
                    max_index = max(max_index, index)
            
            new_filename = f"{base}_{max_index + 1}{ext}"
            os.rename(self.filename, new_filename)
        except Exception as e:
            self.error.emit(f"File rotation failed: {str(e)}")

    def stop(self):
        self._stopped = True


class RecorderApp(QWidget):
    def __init__(self, endpoint: Endpoint, transport: Transport):
        super().__init__()
        self.setWindowTitle("RecorderApp")
        self.log = getmylogger(__name__)
        self.topicMap = TopicMap()
        self.endpoint = endpoint
        self.transport = transport
        self.recording_thread = None
        self.topicMap.load_topics_from_json("robotConfig.json")          
        self.filename = "recordings/rec0.csv" 
        self.initUI()
        


    def initUI(self):
        self.vbox = QVBoxLayout()
        self.fileMenu = FileExplorer("Select File")

        
        self.dataSeriesTable = DataSeriesTable()
        self.dataSeriesTable.setMaximumSize(300, 100)
        self.topicCombo = QComboBox()
        self.topicCombo.addItems(self.topicMap.get_topic_names())
        self.add_PB = QPushButton("Add")
        self.add_PB.clicked.connect(self.add_series_handle)
        self.remove_PB = QPushButton("Remove")
        self.remove_PB.clicked.connect(self.remove_series_handle)
        hbox = QHBoxLayout()
        hbox.addWidget(self.add_PB)
        hbox.addWidget(self.remove_PB)

        self.fileLbl = QLabel(f"File: {self.filename}")
        self.file_PB = QPushButton("Select File")
        self.file_PB.clicked.connect(partial(self.fileMenu.browse))
        self.fileMenu.fileEntry.textChanged.connect(self.file_selected_handle)
        
        self.record_PB = QPushButton("Record")
        self.record_PB.clicked.connect(self.record_handle)
        self.stop_PB = QPushButton("Stop")
        self.stop_PB.clicked.connect(self.stop_handle)
        self.stop_PB.setEnabled(False)
        self.progressBar = ProgressBar()

        self.vbox.addWidget(self.topicCombo, alignment=Qt.AlignmentFlag.AlignTop)
        self.vbox.addWidget(self.dataSeriesTable, alignment=Qt.AlignmentFlag.AlignCenter)
        self.vbox.addLayout(hbox)

        self.vbox.addWidget(self.fileLbl, alignment=Qt.AlignmentFlag.AlignCenter)
        self.vbox.addWidget(self.file_PB)
        self.vbox.addWidget(self.record_PB)
        self.vbox.addWidget(self.progressBar)
        self.vbox.addWidget(self.stop_PB)
        self.setLayout(self.vbox)

    def file_selected_handle(self, file):
        self.fileLbl.setText(f"File: {file}")
        self.filename = file
        

    def add_series_handle(self):
        selected_topic = self.topicCombo.currentText()
        if selected_topic and selected_topic not in self.dataSeriesTable.grabSubscriptions():
            self.dataSeriesTable.addDataSeries((selected_topic.split('/')[0], selected_topic.split('/')[1]))

    def remove_series_handle(self):
        self.dataSeriesTable.removeDataSeries()

    def record_handle(self):
        if self.recording_thread and self.recording_thread.isRunning():
            self.log.warning("Recording already in progress")
            return

        if not self.dataSeriesTable.validate():
            self.log.error("No data series selected")
            return

        
        if not self.filename:
            self.log.error("No file selected")
            return

        subscriptions = self.dataSeriesTable.grabSubscriptions()
        self.recording_thread = RecorderThread(
            filename=self.filename,
            subscriptions=subscriptions,
            topic_map=self.topicMap,
            transport=self.transport,
            endpoint=self.endpoint
        )
        self.recording_thread.progress.connect(self.progressBar.update)
        self.recording_thread.error.connect(self.handle_error)
        self.recording_thread.finished.connect(self.on_recording_finished)
        self.recording_thread.start()

        self.record_PB.setEnabled(False)
        self.stop_PB.setEnabled(True)

    def stop_handle(self):
        if self.recording_thread:
            self.recording_thread.stop()
            self.recording_thread.quit()
            self.recording_thread.wait()
        self.record_PB.setEnabled(True)
        self.stop_PB.setEnabled(False)
        self.progressBar.reset()

    def handle_error(self, message):
        self.log.error(message)
        self.stop_handle()

    def on_recording_finished(self):
        self.record_PB.setEnabled(True)
        self.stop_PB.setEnabled(False)
        self.progressBar.reset()

    def closeEvent(self, event):
        self.stop_handle()
        event.accept()


def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(sys.argv)
    guiApp = RecorderApp(endpoint=Endpoint.BOT_MSG, transport=Transport.TCP)
    guiApp.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()