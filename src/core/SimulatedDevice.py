import random, time, lorem
from queue import Empty
from dataclasses import dataclass

from common.logger import getmylogger
from core.device import BaseDevice, DeviceInfo

@dataclass
class SimInfo(DeviceInfo):
    rate : float = 0.1
    
"""
@Brief: Generates Simulated data for testing.

@Description:   Simulates different datatypes under different topics,
                Sends MessageFrames To the Qt Event loop via pyqtSignal. 
"""
class SimulatedDevice(BaseDevice):
    def __init__(self, deviceInfo: SimInfo):
        super().__init__()        
        self.log = getmylogger(__name__)
        # Register Device Topics
        self.pubMap.register(topicName="LINE", topicArgs=["L", "C","R" ], delim=":")
        self.pubMap.register(topicName="LINE", topicArgs=["X", "Y","Z" ], delim=":")
        #Simulated only parameters
        self.info = deviceInfo
        self.topicGenFuncMap = {
            'LINE' : self._generate_line_data,
            'INFO' : self._generate_word_data,
            'ACCEL' : self._generate_accel_data,
        }
    
    def _start(self) -> bool:
        self.workerIO._begin()
        return True
    
    def _run(self):
        '''Execute Thread'''
        self.log.info("Started Simulated Device ")
        self.publisher.bind()
        self.log.info(f"Publishing: {[t for t in self.topicGenFuncMap.keys()]}")
        while not self.workerIO.stopEvent.is_set():
            try: # grab data from device 
                topic, msg = self._generate_msg_for_topic()
                self.publisher.send(topic, msg)      
            except Exception as e:
                self.log.error(f"Exception in Simulated Data :{e}")
                break

            try: # Send Cmd MsgPacket to Device
                cmdPacket = self.cmdQueue.get_nowait()
                print(cmdPacket) # test commander validation & packetazation 
            except Empty:
                pass
            except Exception as e:
                self.log.error(f"Exception in Simulated Cmd :{e}")
                break

            time.sleep(self.info.rate)  

        self.log.info("Exit Simulated Interface I/O Thread")
        return # exit thread
    
    # Private Functions
    def _generate_line_data(self) -> str:
        return ':'.join(map(str, [round(random.uniform(0.0, 1.0), 3) for _ in range(3)]))
    
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