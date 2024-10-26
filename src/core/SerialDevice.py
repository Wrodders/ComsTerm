import serial, serial.tools.list_ports
from dataclasses import dataclass

import sys,os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
from common.logger import getmylogger
from common.utils import scanUSB
from common.messages import Topic, MsgFrame
from common.zmqutils import Transport, Endpoint

from core.device import BaseDevice, DeviceInfo, Devices
import argparse


'''
|-------| TX --> UART --> RX |---------| PUB  --> INPROC --> SUB | Console | 
|  MCU  |                    | SER Dev | 
|-------| RX <-- UART <-- TX |---------| SUB <--  INPROC <-- PUB | Control |                     

'''



@dataclass
class SerialInfo(DeviceInfo):
    devType : Devices = Devices.SERIAL
    port : str = ""
    baudRate : int = 115200

class SerialDevice(BaseDevice):
    def __init__(self, info: SerialInfo):
        super().__init__(pubEndpoint=info.pubEndpoint, pubTransport=info.pubTransport, 
                        cmdEndpoint=info.cmdEndpoint, cmdTransport=info.cmdTransport)
        self.log = getmylogger(__name__)
        self.info = info
        self.pubMap.loadTopicsFromCSV('devicePub.csv')
        self.port = serial.Serial() # Data input
        self.connect()

    def _start(self) -> bool:   
        if self.port.is_open == False:
            self.log.error(f"Port {self.port.name} not open")
            self.log.debug(f"Serial I/O Threads not started")
            return False
        self.workerRead._begin() 
        self.workerWrite._begin() 
        return True
    
    def _stop(self):
        self.msgPublisher.close()   

        
    def _readDevice(self):
        self.log.debug("Started Serial Interface I/O Thread")
        self.msgPublisher.bind()
        
        self.log.debug(f"Publishing: {[t.name for t in self.pubMap.getTopics()]}")
        while (not self.workerRead.stopEvent.is_set()):
            try: # Read Message Packets Over UART (Blocking)
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
                return 
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
                return 

        self.log.debug(f'Exit {self.info.devType.name} Read Thread')
        self.msgPublisher.close()   
        

    def _writeDevice(self):        
        self.log.debug("Started Serial Interface Write Thread")
        self.cmdSubscriber.addTopicSub(f"{self.info.name}")
        self.cmdSubscriber.connect()
        while (not self.workerWrite.stopEvent.is_set()):
            try: # Grab Message from Subsriction Socket
                if(self.port.writable):
                    topic, message = self.cmdSubscriber.receive();
                    if(message):
                        self.port.write(message.encode())
            except Exception as e:
                self.log.error("Exception in Serial Write") 
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
        


if __name__ == "__main__":
   

    parser = argparse.ArgumentParser(description="Configure and run the serial device.")
  
    # SerialInfo parameters
    parser.add_argument("--port", type=str, required=True, help="The serial port to connect to (e.g., COM3, /dev/ttyUSB0).")
    parser.add_argument("--baudrate", type=int, default=115200, help="Baud rate for the serial connection.")
    parser.add_argument("--pubEndpoint", type=str, choices=[e.value for e in Endpoint], default=Endpoint.COMSTERM_MSG.value, help="Publishing endpoint.")
    parser.add_argument("--pubTransport", type=str, choices=[e.value for e in Transport], default=Transport.INPROC.value, help="Publishing transport method.")
    parser.add_argument("--cmdEndpoint", type=str, choices=[e.value for e in Endpoint], default=Endpoint.COMSTERM_CMD.value, help="Command endpoint.")
    parser.add_argument("--cmdTransport", type=str, choices=[e.value for e in Transport], default=Transport.INPROC.value, help="Command transport method.")

    args = parser.parse_args()
    
    # Create SerialInfo instance using parsed arguments
    serial_info = SerialInfo(
        name=Devices.SERIAL.name,
        devType=Devices.SERIAL,
        port=args.port,
        baudRate=args.baudrate,
        pubEndpoint=Endpoint[args.pubEndpoint.upper()],
        pubTransport=Transport[args.pubTransport.upper()],
        cmdEndpoint=Endpoint[args.cmdEndpoint.upper()],
        cmdTransport=Transport[args.cmdTransport.upper()]
    )
    
    # Instantiate and start the SerialDevice
    device = SerialDevice(info=serial_info)

    try:
        device._start()
    except Exception as e:
        device.log.error(f"Failed to start device: {e}")
        device._stop()