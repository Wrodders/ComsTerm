from PyQt6 import QtCore
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *


import sys, random, threading, time, lorem, zmq
import serial,serial.tools.list_ports
from queue import Queue, Empty
from dataclasses import dataclass, astuple, asdict

from typing import Dict, Tuple, List


from logger import getmylogger


log = getmylogger(__name__)



@dataclass
class MsgFrame():
    ID: str = ""
    data: str = ""

    @classmethod
    def parse_packet(cls, packet):
        if packet[0] == '<':
            return cls(ID=packet[1], data=packet[2:])
        else:
            return cls()

@dataclass
class Cmd():
    ID : str = ""
    name : str = ""
    fmt : str = ""


class CmdMap:
    def __init__(self, cmds):
        self.cmds: Dict[str, Cmd] = {}
        if cmds:
            for cmd in cmds:
                self.addCmd(cmd)

    def getFormatByName(self, name: str) -> str:
        cmd = self.cmds.get(name)
        return cmd.fmt if cmd else ""

    def getFormatByID(self, ID: str) -> str:
        cmd = self.cmds.get(ID)
        return cmd.fmt if cmd else ""

    def getNameByID(self, ID: str) -> str:
        cmd = self.cmds.get(ID)
        return cmd.name if cmd else ""
    
    def getIDByName(self, name:str) -> str:
        cmd = self.cmds.get(name)
        return cmd.ID if cmd else ""

    def getAllCmds(self) -> List[Tuple[str, str]]:
        return [(cmd.name, cmd.fmt) for cmd in self.cmds.values()]

    def addCmd(self, cmd: Cmd):
        self.cmds[cmd.ID] = cmd
        self.cmds[cmd.name] = cmd


"""
@Brief: Base Class for an Interface

@Description: Child Classes Implement start() and _run() functions

Handles communications through Messages delimited by a Packet defined as:

|-------Packet---------|
|-----+----+- - - +----|
| SOF | ID | DATA | EOF|
| 1   | 1  | ...  | 1  |
|-----+----+- - - +----|
      |------Frame-----|

SOF  -- Start of Frame  == '<'
ID   --  Topic Identifier 
DATA -- LEN bytes of data
EOF  -- End of Frame == '\n'

"""
class BaseInterface(QObject):
    deviceDataSig = QtCore.pyqtSignal(tuple)

    def __init__(self):
        super().__init__()
        self._stopped = True
        self._mutex = QMutex()
        self.thread = threading.Thread(target=self._run)
        self.cmdQueue = Queue() 

        #create DeviceInterface Cmds 
        cmds = [
            Cmd(ID = '0', name = "ID", fmt=""),
            Cmd(ID = '1', name="RESET", fmt="d:d"),
        ]
        self.cmdMap = CmdMap(cmds)

    def parseCmd(self, text: str) -> str :
        cmdParts = text.split(" ") # cmdName arg1 arg2 argN
        cmdName = cmdParts[0] 
        if cmdName not in self.cmdMap.cmds:
            log.warning(f"Cmd Name; {cmdName} not found")
            return ''

        cmdArgs = " ".join(cmdParts[1:]).split(" ")
        fmt = str(self.cmdMap.getFormatByName(cmdName)) # e.g d:d:f 
        fmtArgs = self.cmdMap.getFormatByName(cmdName).split(":")
        if fmtArgs == ['']:
            # Cmd Takes no input 
            if cmdArgs != ['']:
                log.warning(f"Cmd syntax error, see {cmdName} {fmt}")
                return ''
        elif len(cmdArgs) != len(fmtArgs) or ''  in cmdArgs:
                log.warning(f"Cmd syntax error, see {cmdName} {fmt}")
                return ''
        
        data = ":".join(cmdParts[1:]) # exclude cmdName
        cmdID = self.cmdMap.getIDByName(cmdName)
        # compose packet 
        msgPacket = '<' + str(len(data)) + cmdID + data + '\n'
        
        return msgPacket
        
    def sendCmd(self, text:str):
        #Pushes cmd to IO Queue
        packet = self.parseCmd(text)
        if packet != '':
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
class SimulatedDevice(BaseInterface):
    def __init__(self, rate: float):
        super().__init__()
        self.thread = threading.Thread(target=self._run)
        

        #Simulated only parameters
        self.rate = rate # publish rate in seconds
        self.topicGenFuncMap = {
            'LINE' : self._generate_line_data,
            'TELEM' : self._generate_word_data,
            'ACCEL' : self._generate_accel_data,
            'GYRO' : self._generate_gyro_data
        }
    
    def start(self):
        self.thread.start()
    
    def _run(self):
        '''Execute Thread'''
        self._stopped = False
        log.info("Started SimulatedInterface ")
        for topic in self.topicGenFuncMap.keys():
            log.info(f"Publishing: {topic}")
        while not self._stopped:
            try: # grab data from device 
                topic, msg = self._generate_msg_for_topic()
                self.deviceDataSig.emit((topic, msg))
                time.sleep(self.rate)        
            except Exception as e:
                log.error(f"Exception in Simulated Data :{e}")
                break

            try:
                cmdPacket = self.cmdQueue.get_nowait()
                #print(cmdPacket)
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
class SerialDevice(BaseInterface):
    def __init__(self):
        super().__init__()
        self.thread = threading.Thread(target=self._run) # IO
        self.port = serial.Serial() # Data input

    def start(self):
        key = "usb"
        ports = self.scanUSB(key)
        if not ports :
            log.error(f"No ports found for key: {key}")
            log.warning(f"Serial I/O Thread not started")
            return
        elif self.connect(ports[0], 9600) == False:
            log.error(f"Failed to connect to{ports[0]}")
            log.warning(f"Serial I/O Thread not started")
            return

        self.thread.start()  
        
    # ********************** IO THREAD ************************* # 
    def _run(self):
        self._stopped = False
        log.info("Started Serial Interface I/O Thread")
        while (not self._stopped) and self.port.is_open:
            try: 
                # Read and parse a MsgFrame from serial port, emit to Qt Main loop                   
                msgPacket = self.port.readline()
                recvMsg = MsgFrame.parse_packet(msgPacket.decode())
                if recvMsg.ID:
                    self.deviceDataSig.emit((recvMsg.ID, recvMsg.data)) # output Data
                                               
            except Exception as e:
                log.error(f"Exception in Serial Read: {e}")
                pass

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
class ZmqDevice(BaseInterface):
    def __init__(self, transport : str, socketAddress : str ): 
        super().__init__()
        self.thread = threading.Thread(target=self._run)
        self.socketAddr = socketAddress
        self.transport  = transport
        
    def start(self):
        self.thread.start()

    def _run(self):
        '''Execute Thread'''
        self._stopped = False
        self.sub  = ZmqSub(transport=self.transport, address=self.socketAddr)
        self.sub.connect()
        self.sub.addTopicSub("") # recevies only data sent on the GUI topic
        log.info(f"Started ZMQ Interface")
        while not self._stopped:
            try:
                topic, msgPacket = self.sub.socket.recv_multipart()
                if msgPacket != "":
                    recvMsg = MsgFrame.parse_packet(msgPacket.decode())
                    if recvMsg.ID:
                        try:
                            topic=topic.decode() + '/' + recvMsg.ID
                            self.deviceDataSig.emit((topic, recvMsg.data))
                        except Exception as e:
                            log.warning(f"Exception in ZmqQTSignal:{e} ")
                            pass
            except Exception as e:
                log.error(f"Exception in ZmqQTSignal:{e}")
                pass
        
        self.sub.close() 
        log.info("exit Zmq Bridge QT I/O Thread")  
        return
    
