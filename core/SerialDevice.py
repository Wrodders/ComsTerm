import serial, serial.tools.list_ports
from queue import Empty

from core.device import BaseDevice, MsgFrame
from logger import getmylogger


log = getmylogger(__name__)


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

    def _start(self):
        """
        @Brief: Connect to USB port being IO thread
        @Description: Scans for usb ports and connects to the first one
        """
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

        self.workerIO._begin()  
        

    def _run(self):
        """
        @Brief: Serial IO Thread
        """
        log.info("Started Serial Interface I/O Thread")
    
        while (not self.workerIO.stopEvent.is_set()) and self.port.is_open:
            try:
                self.readDevice()
                self.writeDevice()
            except Exception as e:
                log.error(f"Unexpected exception in thread loop: {e}")
                break

        log.info('Exit Serial Interface I/O Thread')
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
            #Decode Message
            recvMsg = MsgFrame.extractMsg(msg)        
            
            topic = self.pubMap.getNameByID(recvMsg.ID)
            if topic != "":  
                print(f"TP: {topic}", recvMsg.data)
                self.publisher.send(topic, recvMsg.data) # Output Message

        except UnicodeDecodeError as e:
            log.warning(f"{e}")
            return 
        except Exception as e:
            log.error(f"Exception in Serial Read: {e}")
            raise 

    def writeDevice(self):
        """
        @Brief: Writes cmds from the queue to the device.
        """
        #Service CmdMsg Queue And Transmit MsgFrame over Serial
        try:
            cmdPacket = self.cmdQueue.get_nowait()
            self.port.write(cmdPacket) # output Data
        except Empty:
            pass
        except Exception as e:
            log.error(f"Exception in Serial Write: {e}")
            raise

    """
    ************** PUBLIC FUNCTIONS *************************
    """
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
        try:
            self.port.open()
        except serial.SerialException as e:
            log.error(f"Exception in Serial connect:{e} ")
            return False
        else:
            log.info(f'Connection to {portNum} Successful')
            return True
    
    def disconnect(self) -> bool:
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
        