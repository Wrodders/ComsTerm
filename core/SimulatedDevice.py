import random,time, lorem
from queue import Queue, Empty


from logger import getmylogger
from core.device import BaseDevice

log = getmylogger(__name__)


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
        self.workerIO._begin()
    
    def _run(self):
        '''Execute Thread'''
        self.workerIO._stopped = False
        log.info("Started SimulatedInterface ")
        while not self.workerIO.isStopped():
            try: # grab data from device 
                topic, msg = self._generate_msg_for_topic()
                self.deviceDataSig.emit((topic, msg))      
            except Exception as e:
                log.error(f"Exception in Simulated Data :{e}")
                break

            try: # Send Cmd MsgPacket to Device
                cmdPacket = self.cmdQueue.get_nowait()
                print(cmdPacket) # test commander validation & packetazation 
            except Empty:
                pass
            except Exception as e:
                log.error(f"Exception in Simulated Cmd :{e}")
                break

            time.sleep(self.rate)  

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