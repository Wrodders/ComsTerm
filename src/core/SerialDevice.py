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

class SerialDevice(BaseDevice):
    def __init__(self, info: SerialInfo):
        super().__init__()
        self.log = getmylogger(__name__)
        self.info = info

        self.cmdMap.register(topicName="STOP", topicArgs=[], delim="")
        self.cmdMap.register(topicName="START", topicArgs=[], delim="")
        self.cmdMap.register(topicName="LINE", topicArgs=[], delim="")
        self.cmdMap.register(topicName="TURN", topicArgs=[], delim="")
        
        self.pubMap.register(topicName="CMD_RET", topicArgs=[], delim=":")
        self.pubMap.register(topicName="ERROR", topicArgs=[], delim=":")
        self.pubMap.register(topicName="INFO", topicArgs=[], delim=":")
        self.pubMap.register(topicName="DEBUG", topicArgs=[], delim=":")
        self.pubMap.register(topicName="IMU", topicArgs=["RP", "CR", "KP","RR","CP", "KR"], delim=":")
     
        self.port = serial.Serial() # Data input
        self.connect()

    def _start(self) -> bool:   
        if self.port.is_open == False:
            self.log.error(f"Port {self.port.name} not open")
            self.log.debug(f"Serial I/O Thread not started")
            return False
        self.workerIO._begin()  
        return True
        
    def _stop(self):
        self.workerIO._stop()
        self.publisher.close()

    def _run(self):
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
        try: 
            msgPacket = self.port.read_until(b'\n')
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
        try: #Decode Message Publish Data under Arg SubTopic
            recvMsg = MsgFrame.extractMsg(msg)    
            topic = self.pubMap.getTopicByID(recvMsg.ID)
            if isinstance(topic, Topic):
                self.pubMsgSubTopics(topic=topic, data=recvMsg.data)
        except UnicodeDecodeError as e:
            self.log.warning(f"{e} {msgPacket}")
            return 
        except Exception as e:
            self.log.error(f"Exception in Serial Decode: {e}")
            raise 

    def writeDevice(self):
        try: #Service CmdMsg Queue And Transmit MsgFrame over Serial
            cmdPacket = self.cmdQueue.get_nowait()
            self.port.write(cmdPacket.encode()) # output Data
        except Empty:
            pass
        except Exception as e:
            self.log.error(f"Exception in Serial Write: {e}")
            raise
  
    def connect(self) -> bool:
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
        