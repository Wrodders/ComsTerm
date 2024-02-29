import serial, serial.tools.list_ports
from queue import Queue, Empty

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
                # HOT FIX BELOW
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
        