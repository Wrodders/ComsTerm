from PyQt6 import QtCore
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *


import sys, random, threading, time, lorem, zmq
import serial,serial.tools.list_ports
from collections import namedtuple


from logger import getmylogger


log = getmylogger(__name__)

MsgFrame = namedtuple("MsgFrame", ['topic', 'msg'])

"""
@Brief: Generates Simulated data for testing.

@Description:   Simulates different datatypes under different topics,
                Sends MessageFrames To the Qt Event loop via pyqtSignal. 
"""
class SimulatedInterface(QObject):
    socketDataSig = QtCore.pyqtSignal(tuple)
    def __init__(self, rate: float):
        super().__init__()
        self._stopped = True
        self._mutex = QMutex()
        self.thread = threading.Thread(target=self._run)

        #Simulated only parameters
        self.rate = rate # publish rate in seconds
        self.topicGenFuncMap = {
            'IMU' : self._generate_imu_data,
            'TELEM' : self._generate_word_data,
            'ACCEL' : self._generate_accel_data,
            'GYRO' : self._generate_gyro_data
        }

    def stop(self):
        self._mutex.lock()
        self._stopped = True
        self._mutex.unlock()

    def start(self):
        self.thread.start()

    def _run(self):
        '''Execute Thread'''
        self._stopped = False
        log.info("Started SimulatedInterface ")
        while not self._stopped:
            try: # grab data from device 
                topic, msg = self._generate_msg_for_topic()
                self.socketDataSig.emit((topic, msg))
                time.sleep(self.rate)
                
            except Exception as e:
                log.error(f"Exception in SimulatedInterface :{e} ")
                break
        log.info("Exit Simulated Interface I/O Thread")
        return # exit thread
    
    # Private Functions
    def _generate_imu_data(self) -> str:
        return ':'.join(map(str, [random.uniform(0.0, 1.0) for _ in range(3)]))
    
    def _generate_accel_data(self) -> str:
        return ':'.join(map(str, [random.uniform(-1.0, 1.0) for _ in range(3)]))

    def _generate_gyro_data(self) -> str:
        return ':'.join(map(str, [random.uniform(-1.0, 1.0) for _ in range(3)]))

    def _generate_word_data(self) -> str:
        sentence = lorem.sentence()
        return sentence

    def _generate_msg_for_topic(self) -> tuple[str,str]:
        topics = list(self.topicGenFuncMap.keys())
        topic = random.choice(topics)
        msg = self.topicGenFuncMap[topic]() #execute function to generate data
        return (topic, msg)


'''
@Brief: Connects and Reads Data from Serial Port. 

@Description:   Scans for available ports by Key, (default 'usb'),
                opens thread and connects to port, reads lines terminating in '\n'
                sends data to Qt Event loop via pyqtSignal.
'''
class SerialInterface(QObject):
    socketDataSig = QtCore.pyqtSignal(tuple)
    def __init__(self):
        super().__init__()
        self._stopped = True
        self._mutex = QMutex()
        self.thread = threading.Thread(target=self._run)
        # Data input
        self.port = serial.Serial()

    def stop(self):

        self._mutex.lock()
        self._stopped = True
        self._mutex.unlock()

    def start(self):
        key = "usb"
        ports = self.scanUSB(key)
        if not ports :
            log.error(f"No ports found for key: {key}")
            log.warning(f"Serial I/O Thread not started")
            return
        elif self.connect(ports[0], 115200) == False:
            log.error(f"Failed to connect to{ports[0]}")
            log.warning(f"Serial I/O Thread not started")
            return

        self.thread.start()  

    # Internal Functions     
    def _run(self):
        # Read and parse msgFrame from Serial Port
        self._stopped = False
        log.info("Started Serial Interface I/O Thread")
        while (not self._stopped) and self.port.is_open:
            try:                    
                line = self.port.readline()
                topic, msg = self.grabMsg(line)
                if msg == None:
                    continue
                self.socketDataSig.emit((topic, msg)) # data output
            except Exception as e:
                log.error(f"Exception in Serial Interface: {e}")
                break 

        log.info('Exit Serial Interface I/O Thread')
        self.disconnect()
        return # exit thread
    

    def grabMsg(self, line: bytearray) -> tuple[str, str]:
        try: 
            msgFrame = line.decode('utf-8').strip[:-1]
        except Exception as e: 
            log.warning(f"{e}")
            msgFrame = None
            return msgFrame
        
        msgFrame = ''.join(char for char in msgFrame if char.isprintable()) # remove null chars
        msgFrame = msgFrame.split('/') # split on topic delimeter
        return (msgFrame[0], msgFrame[1]) # topic msg
    

    # Public Functions
    def scanUSB(self, key: str) -> list:
        ports = [p.device for p in serial.tools.list_ports.comports() if key.lower() in p.device]
        return ports
    
    def connect(self, portNum, baud) -> bool:
        '''Connect to serial device and start reading'''
        log.info(f"Connecting Device to: {portNum}, At Baud: {baud}")
        if self.port.is_open == True:
            log.error('Connect Error: Serial Port Already Open')
            return False
        
        self.port.port = portNum
        self.port.baudrate = baud
        self.port.timeout = 0.1
        self.port.xonxoff=1
        try:
            self.port.open()
        except serial.SerialException as e:
            log.error(f"Exception in Serial connect:{e} ")
        else:
            log.info(f'Connection to {portNum} Successful')
            return True
    
    def disconnect(self):
        '''Disconnect from serial device'''
        if self.port.is_open == False:
            log.warning("Disconnect Error: Serial Port Is Already Closed")
            return False
        try:
            self.port.close() # close serial port
        except Exception as e:
            log.error(f"Exception in Disconnect:{e}")
            return False
        else:
            log.info('Serial Port Closed')
            return True
        
    def getPortInfo(self) -> dict:
        info = {
            "DeviceId": self.id,
            "Port": self.port.port,
            "Baud": self.port.baudrate,
            "Publish": self.pubAddr,
            "Port Status": "open" if self.port.is_open else "closed"
        }
        return info
    

"""
@Breif: ZMQ Publish socket with added functionality.
"""
class ZmqPub:
    def __init__(self,transport : str, endpoint : str):
        self.socketAddress = checkAddress(transport, endpoint)
        self.context = zmq.Context.instance()
        self.socket = self.context.socket(zmq.PUB)

    def bind(self):
        self.socket.bind(self.socketAddress)
        log.debug(f"Binded ZMQ PUB socket to {self.socketAddress}")

    def send(self, topic: str, data : str):
        self.socket.send_multipart([topic.encode(), data.encode()])
"""
@Brief: ZMQ Subscription socket with added functionality.
@Description: Creates a SUB Socket with add/remove topics, clean up and logging. 
"""
class ZmqSub:
    def __init__(self, transport : str, address : str):
        self.socketAddress = checkAddress(transport, address)
        self.context = zmq.Context.instance()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.setsockopt(zmq.LINGER, 0)
        
        self.topicList = []

    def connect(self):
        self.socket.connect(self.socketAddress)
        log.debug(f"Connected ZMQ SUB socket to: {self.socketAddress}")

    def addTopicSub(self, topic : str):
        if topic not in self.topicList:
            self.socket.setsockopt(zmq.SUBSCRIBE, topic.encode())
            self.topicList.append(topic)
            log.debug(f"ZMQ SUB Subscribed to {topic}")

    def removeTopic(self, topic : str):
        self.socket.setsockopt(zmq.UNSUBSCRIBE, topic)
        if topic in self.topicList:
            self.topicList.remove(topic)
            log.debug(f"Unsubscribed to {topic}")

    def getTopics(self) -> [str]:
        return self.topicList
    
    def receive(self) -> tuple[str, str]:
        dataFrame = self.socket.recv_multipart()
        return (dataFrame[0].decode(),dataFrame[1].decode())

    def close(self):
        self.socket.close()
        log.debug(f"Closed ZMQ SUB socket connected to: {self.socketAddress}" )

"""
@Breif: WIP
"""
class ZmqInterface(QObject):

    socketDataSig = QtCore.pyqtSignal(tuple)

    def __init__(self, socketAddress : str ): 
        super().__init__()
        self._stopped = True
        self._mutex = QMutex()
        self.thread = threading.Thread(target=self._run)
        self.socketAddr = socketAddress

    def stop(self):
        print("Stop")
        self._mutex.lock()
        self._stopped = True
        self._mutex.unlock()
        
    def start(self):
        self.thread.start()

    def _run(self):
        '''Execute Thread'''
        self._stopped = False
        self.sub  = ZmqSub(transport="ipc", address=self.socketAddr)
        self.sub.connect()
        self.sub.addTopicSub("") # recevies only data sent on the GUI topic
        log.info(f"Started ZMQ Interface")
        while not self._stopped:
            try:
                msg = self.sub.socket.recv_multipart()
                #self.socketDataSig.emit((topic, msg))
            except Exception as e:
                log.error(f"Exception in ZmqQTSignal:{e} ")
                break
        
        self.sub.close() 
        log.info("exit Zmq Bridge QT I/O Thread")  
        return
    

TRANSPORT_TYPES = ["inproc", "ipc", "tcp", "udp"]

def checkAddress(transport : str, endpoint : str) -> str:
    if transport == 'tcp':
        # Example: tcp://127.0.0.1:5555
        return f"{transport}://{endpoint}"
    elif transport == 'ipc':
        # Example: ipc:///tmp/zmq_socket
        return f"{transport}:///tmp/{endpoint}"
    elif transport == 'inproc':
        # Example: inproc://example
        return f"{transport}://{endpoint}"
    else:
        raise ValueError(f"Unsupported transport type: {transport}")