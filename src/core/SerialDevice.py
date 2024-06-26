import serial, serial.tools.list_ports, os
from queue import Empty
from dataclasses import dataclass

from common.logger import getmylogger
from common.utils import scanUSB
from common.messages import Topic, MsgFrame

from core.device import BaseDevice, DeviceInfo, Devices

@dataclass
class SerialInfo(DeviceInfo):
    devType : Devices = Devices.SERIAL
    port : str = ""
    baudRate : int = 115200


'''
@Brief: Connects and Reads Data from Serial Port. 

@Description:   Scans for available ports by Key, (default 'usb'),
                opens thread and connects to port, reads lines terminating in '\n'
                sends data to Qt Event loop via pyqtSignal.
'''
class SerialDevice(BaseDevice):
    def __init__(self, info: SerialInfo):
        super().__init__()
        self.log = getmylogger(__name__)
        self.info = info

        self.cmdMap.register(topicName="STOP", topicArgs=[], delim="")
        self.cmdMap.register(topicName="START", topicArgs=[], delim="")
        self.cmdMap.register(topicName="LINE", topicArgs=[], delim="")
        self.cmdMap.register(topicName="TURN", topicArgs=[], delim="")

        self.pubMap.register(topicName="MOTOR", topicArgs=["L", "R", "TL","TR","OL", "OR"], delim=":")
        self.pubMap.register(topicName="LINE", topicArgs=["L", "C", "R" ], delim=":")

        self.port = serial.Serial() # Data input
        self.connect()

    def _start(self) -> bool:
        """
        @Brief: Starts Worker IO Thread to read and write from serial port
        @Description: Scans for usb ports and connects to the first one
        """        
        if self.port.is_open == False:
            self.log.error(f"Port {self.port.name} not open")
            self.log.debug(f"Serial I/O Thread not started")
            return False
        
        self.info.status = True
        self.workerIO._begin()  
        return True
        

    def _run(self):
        """
        @Brief: Serial IO Thread
        """
        self.log.debug("Started Serial Interface I/O Thread")
        self.publisher.bind()
        while (not self.workerIO.stopEvent.is_set()) and self.port.is_open:
            try:
                self.readDevice()
                self.writeDevice()
            except Exception as e:
                self.log.error(f"Unexpected exception in thread loop: {e}")
                break

        self.log.debug('Exit Serial Interface I/O Thread')
        self.disconnect()
    
    def readDevice(self):
        """
        @Brief: Reads a message from a device, parses and publishes over its topic.
        """
        try: 
            # Read ASCII Message
            msgPacket = self.port.readline()
            msg = msgPacket.decode('utf-8').rstrip("\n")
            msg = msg.replace('\x00','')
            if len(msg) <= 0:
                return
        except UnicodeDecodeError as e:
                self.log.warning(f"{e} {msgPacket}")
                return
        except Exception as e :
            self.log.error(f"Exception in Serial Read: {e}")
            raise 

        try:
            #Decode Message
            recvMsg = MsgFrame.extractMsg(msg)        
            topic = self.pubMap.getTopicByID(recvMsg.ID)
            if isinstance(topic, Topic):
                if topic.name != "": 
                    delim , args = self.pubMap.getTopicFormat( topic.name)
                    msgArgs = recvMsg.data.split(delim)
                    msgSubTopics = [( topic.name + "/" + arg) for arg in args]
                    [self.publisher.send(msgSubTopics[i], msgArgs[i]) for i, _ in enumerate(msgArgs)]
        except UnicodeDecodeError as e:
            self.log.warning(f"{e} {msgPacket}")
            return 
        except Exception as e:
            self.log.error(f"Exception in Serial Decode: {e}")
            raise 

    def writeDevice(self):
        """
        @Brief: Writes cmds from the queue to the device.
        """
        #Service CmdMsg Queue And Transmit MsgFrame over Serial
        try:
            cmdPacket = self.cmdQueue.get_nowait()
            self.port.write(cmdPacket.encode()) # output Data
        except Empty:
            pass
        except Exception as e:
            self.log.error(f"Exception in Serial Write: {e}")
            raise

    """
    ************** PUBLIC FUNCTIONS *************************
    """    
    def connect(self) -> bool:
        '''Connect to serial device and start reading'''
        self.log.info(f"Connecting Device to: {self.info.port}, At Baud: {self.info.baudRate}")
        if self.port.is_open == True:
            self.log.error('Connect Error: Serial Port Already Open')
            return False
        
        self.port.port = self.info.port
        self.port.baudrate = self.info.baudRate
        self.port.timeout = 0.1
        try:
            self.port.open()
        except serial.SerialException as e:
            self.log.error(f"Exception in Serial connect:{e} ")
            return False
        else:
            self.log.info(f'Connection to {self.info.port} Successful')
            return True
    
    def disconnect(self) -> bool:
        '''Disconnect from serial device'''
        if self.port.is_open == False:
            self.log.warning("Disconnect Error: Serial Port Is Already Closed")
            return False
        try:
            self.port.close() # close serial port
        except Exception as e:
            self.log.error(f"Exception in Disconnect:{e}")
            return False
        else:
            self.log.info('Serial Port Closed')
            return True
        