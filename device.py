from PyQt6 import QtCore
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *


import sys, random, threading, time, lorem, zmq, re
import serial,serial.tools.list_ports
from queue import Queue, Empty
from dataclasses import dataclass, astuple, asdict, field
from typing import Dict, List, Tuple

from typing import Dict, Tuple, List


from logger import getmylogger


log = getmylogger(__name__)


''' 
MsgFrame: Represents the raw serialized msg from a device. 

|-------------Packet---------|
|-----+-----+----+- - - +----|
| SOF | LEN | ID | DATA | EOF|
| 1   | 1   | 1  | ...  | 1  |
|-----+-----+----+- - - +----|
      |-------Frame-----|

SOF  -- Start of Frame  == '<'
LEN  -- Size of Data (bytes)
ID   --  Topic Identifier 
DATA -- LEN bytes of data
EOF  -- End of Frame == '\n'
    
'''
@dataclass
class MsgFrame():
    size: int =  0
    ID: str = ""
    data: str = ""

    @classmethod
    def extractMsg(cls, msgPacket: bytes):
        try:
            msg = msgPacket.decode('utf-8')
        except UnicodeDecodeError as e:
            log.warning(f"{e}")
            return None
        
        # Extract SIZE ID DATA
        print(msg)
        match = re.match(r'<(.)(.):([^\x00]+)\x00\n', msg) # this doesnt work
        if match:
            size = int(match.group(1))
            ID = match.group(2)
            data = match.group(3)
            if len(data) == size:
                return cls(size, ID, data)
        else:
            return None
        

""" 
Topics: Devices Publish Data over topics. 
        Descriptive names are mapped to msg ids.
        Msgs validated Topics protocol
"""

@dataclass
class Topic:
    ID : str = "" # Topics ID
    name : str = "" # Topics Name
    fmt : str = "" # Topics Data Format 
    delim : str = "," # Data Argument Delimiter
    nArgs : int = 0 # Number of Arguments in Topics Data

class TopicMap:
    def __init__(self): 
        self.topics: Dict[str, Topic] = {}

    def getFormatByName(self, name: str) -> str:
        topic = self.topics.get(name)
        return topic.fmt if topic else ""

    def getFormatByID(self, ID: str) -> str:
        topic = self.topics.get(ID)
        return topic.fmt if topic else ""

    def getNameByID(self, ID: str) -> str:
        topic = self.topics.get(ID)
        return topic.name if topic else ""
    
    def getIDByName(self, name:str) -> str:
        topic = self.topics.get(name)
        return topic.ID if topic else ""

    def getAllTopics(self) -> List[Tuple[str, str, int]]:
        return [(topic.name, topic.fmt, topic.nArgs) for topic in self.topics.values()]

    def registerTopic(self, topicID : str, topicName: str, topicFmt: str, delim: str):
        if delim != "":
            numArgs = len(topicFmt.split(delim))
        else:
            numArgs = 0
        newTopic = Topic(ID=topicID, name=topicName, fmt=topicFmt, delim=delim, nArgs= numArgs)
        self.topics[newTopic.name] = newTopic


       

"""
@Brief: Base Class for a Device. Handles communications between device and ComsTerm.
@Description:   Implements a set of CMDs and PUBs topics. Parses and Validates Commands against a devices protocols. 
                Controls the Child Devices _run() method to obtain data from I/O.
"""
class BaseDevice(QObject):
    deviceDataSig = QtCore.pyqtSignal(tuple)

    def __init__(self):
        super().__init__()
        self._stopped = True
        self._mutex = QMutex()
        self.wThread = threading.Thread(target=self._run)
        self.cmdQueue = Queue() 

        # Create Base Topic Maps
        self.cmdMap = TopicMap()
        self.pubMap = TopicMap()

        self.cmdMap.registerTopic(topicID = '0', topicName="ID", topicFmt="", delim="")
        self.cmdMap.registerTopic(topicID = '1', topicName="RESET", topicFmt="d:d", delim=":")

        self.pubMap.registerTopic(topicID = '0', topicName="CMD_RET", topicFmt="s", delim="")
        self.pubMap.registerTopic(topicID = '1', topicName="ERR", topicFmt="s", delim="")
        self.pubMap.registerTopic(topicID = '2', topicName="INFO", topicFmt="s", delim="")


    def parseCmd(self, text: str) -> str:
        cmdParts = text.split(" ", 1) # cmdName arguments
        cmdName = cmdParts[0] 
        cmdTopic = self.cmdMap.topics.get(cmdName)
        if cmdTopic == None: # exit early if cmd name wrong 
            log.warning(f"Cmd Name; {cmdName} not found")
            return ""

        fmt = cmdTopic.fmt # grab the topics protocol format string
        cmdArgs = cmdParts[1:] #extract arguments
        if cmdArgs == []:
            numArgs = 0
        else:
            numArgs = sum(1 for c in cmdArgs[0] if c == cmdTopic.delim) + 1 # num args = num delim + 1 
        print(cmdArgs, numArgs, cmdTopic.nArgs)
        if numArgs != cmdTopic.nArgs
            log.warning(f"Cmd syntax error: incorrect num args for {cmdName} {fmt}")
            return ""

        data = cmdTopic.delim.join(cmdArgs)  # Join arguments using delimiter
        cmdID = cmdTopic.ID
        # assemble packet 
        msgPacket = f'<{len(data)}{cmdID}{data}\n'
    
        return msgPacket
        
    def sendCmd(self, text:str):
        #Pushes cmd to IO Queue
        packet = self.parseCmd(text)
        if packet != "":
            self.cmdQueue.put(packet)
    
    def _run(self):
        raise NotImplementedError("Subclasses must implement _run method")
    
    def start(self):
        raise NotImplementedError("Subclasses must implement start method")
    
    def stop(self):
        self._mutex.lock()
        self._stopped = True
        self._mutex.unlock()

"""
@Brief: Generates Simulated data for testing.

@Description:   Simulates different datatypes under different topics,
                Sends MessageFrames To the Qt Event loop via pyqtSignal. 
"""
class SimulatedDevice(BaseDevice):
    def __init__(self, rate: float):
        super().__init__()        
        # Register Device Topics
        self.pubMap.registerTopic(topicID='3', topicName="LINE", topicFmt="f:f:f:f", delim=":")

        print(f"PUB: {self.pubMap.getAllTopics()}")

        #Simulated only parameters
        self.rate = rate # publish rate in seconds
        self.topicGenFuncMap = {
            'LINE' : self._generate_line_data,
            'INFO' : self._generate_word_data,
            'ACCEL' : self._generate_accel_data,
        }
    
    def start(self):
        self.wThread.start()
    
    def _run(self):
        '''Execute Thread'''
        self._stopped = False
        log.info("Started SimulatedInterface ")
        while not self._stopped:
            try: # grab data from device 
                topic, msg = self._generate_msg_for_topic()
                self.deviceDataSig.emit((topic, msg))
                time.sleep(self.rate)        
            except Exception as e:
                log.error(f"Exception in Simulated Data :{e}")
                break

            try: # Send Cmd MsgPacket to Device
                cmdPacket = self.cmdQueue.get_nowait()
                print(cmdPacket)
            except Empty:
                pass
            except Exception as e:
                log.error(f"Exception in Simulated Cmd :{e}")
                break

        log.info("Exit Simulated Interface I/O Thread")
        return # exit thread
    
    # Private Functions
    def _generate_line_data(self) -> str:
        return ':'.join(map(str, [round(random.uniform(0.0, 1.0), 3) for _ in range(5)]))
    
    def _generate_accel_data(self) -> str:
        return ':'.join(map(str, [round(random.uniform(-1.0, 1.0),3) for _ in range(3)]))

    def _generate_gyro_data(self) -> str:
        return ':'.join(map(str, [round(random.uniform(-1.0, 1.0),3) for _ in range(3)]))

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
class SerialDevice(BaseDevice):
    def __init__(self):
        super().__init__()
        self.port = serial.Serial() # Data input

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

        self.wThread.start()  
        
    # ********************** IO THREAD ************************* # 
    def _run(self):
        self._stopped = False
        log.info("Started Serial Interface I/O Thread")
        recvMsg =  MsgFrame()
        while (not self._stopped) and self.port.is_open:
            try: 
                # Read and parse a MsgFrame from serial port, emit to Qt Main loop                   
                msgPacket = self.port.readline()
              
                #recvMsg = MsgFrame.extractMsg(msgPacket)

                try:
                    msg = msgPacket.decode('utf-8').rstrip("\n")
                    msg = msg.replace('\x00','')
                except UnicodeDecodeError as e:
                    log.warning(f"{e}")
                    continue
                                
                if msg != '':
                    self.deviceDataSig.emit(("ODOM", msg)) # output Data

            except Exception as e:
                log.error(f"Exception in Serial Read: {e}")
                break 

             #Service CmdMsg Queue And Transmit MsgFrame over Serial
            try:
                cmdPacket = self.cmdQueue.get_nowait()
                self.port.write(cmdPacket) # output Data
            except Empty:
                pass
            except Exception as e:
                log.error(f"Exception in Serial Write: {e}")
                break

        log.info('Exit Serial Interface I/O Thread')
        self.disconnect()
        return # exit thread
    

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
        self.port.xonxoff = 1
        try:
            self.port.open()
        except serial.SerialException as e:
            log.error(f"Exception in Serial connect:{e} ")
            return False
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
        
    
class BLEDevice(BaseDevice):
    def __init__(self, dev_pts):
        super().__init__()
        self.dev_pts = dev_pts
        self.file_handle = None
    
    def _run(self):
        # Open the file representing the virtual COM port
        self.file_handle = open(self.dev_pts, 'r+')
        
        # Start reading data from the file
        while not self._stopped:
            try: 
                # Read and parse a MsgFrame from serial port, emit to Qt Main loop                   
                msgPacket = self.port.readline()
                if msgPacket[0] == '<':  # SOF Received
                    recvMsg = MsgFrame.extractMsg(msgPacket)
                    if recvMsg:
                        self.deviceDataSig.emit((recvMsg.ID, recvMsg.data)) # output Data
 
            except Exception as e:
                log.error(f"Exception in Serial Read: {e}")
                break 

            if not self.cmdQueue.empty():
                cmd_packet = self.cmdQueue.get()
                self.file_handle.write(cmd_packet)  # Send command packet to the device
                self.file_handle.flush()  # Flush the buffer to ensure data is sent immediately
                # Implement code to handle responses from the device if needed
            time.sleep(0.1)  # Adjust sleep time as needed
    
    def start(self):
        self._mutex.lock()
        self._stopped = False
        self._mutex.unlock()
        self.wThread.start()  # Start the thread for running the BLEDevice
    
    def stop(self):
        super().stop()  # Call the stop method of the base class
        if self.file_handle:
            self.file_handle.close()  # Close the file handle when stopping



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
class ZmqDevice(BaseDevice):
    def __init__(self, socketAddress : str ): 
        super().__init__()
        self.socketAddr = socketAddress
        
    def start(self):
        self.wThread.start()

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