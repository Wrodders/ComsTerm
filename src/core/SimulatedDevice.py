import random, time, lorem
from queue import Empty
from dataclasses import dataclass

from common.logger import getmylogger
from core.device import BaseDevice, DeviceInfo

@dataclass
class SimInfo(DeviceInfo):
    dt : float = 0.1
    
"""
@Brief: Generates Simulated data for testing.

@Description:   Simulates different datatypes under different topics,
                Sends MessageFrames To the Qt Event loop via pyqtSignal. 
                What started as an overly convoluted way to parse data is now a feature
                in that it adequately simulates communications delay and patterns. 
"""
class SimulatedDevice(BaseDevice):
    def __init__(self, deviceInfo: SimInfo):
        super().__init__(pubEndpoint=deviceInfo.pubEndpoint, pubTransport=deviceInfo.pubTransport, 
                        cmdEndpoint=deviceInfo.cmdEndpoint, cmdTransport=deviceInfo.cmdTransport)   
        self.log = getmylogger(__name__)
        # Register Device Topics
        self.pubMap.register(topicName="LINE", topicID='0',topicArgs=["L", "C","R" ], delim=":")
        self.pubMap.register(topicName="ACCEL",topicID='1', topicArgs=["X", "Y","Z" ], delim=":")
        #Simulated only parameters
        self.info = deviceInfo
        self.lastTime = time.time()
        self.topicGenFuncMap = {
            'LINE' : self._generate_line_data,
            'ACCEL' : self._generate_accel_data,
        }
    
    def _start(self) -> bool:
        self.workerRead._begin()
        self.workerWrite._begin()
        return True
    
    def _cleanup(self):
        pass
    
    def _readDevice(self):
        self.log.debug("Started Simulated Device Read Thread")
        self.msgPublisher.bind()
        self.log.info(f"Publishing: {[t.name for t in self.pubMap.getTopics()]}")
        while (not self.workerRead.stopEvent.is_set()):
            try: # Send Cmd MsgPacket to Device    
                elapsedTime= time.time() - self.lastTime; 
               
                if(elapsedTime >= self.info.dt):
                    topic, msg = self._generate_msg_for_topic()
                    delim , args = self.pubMap.getTopicFormat(topic)
                    msgArgs = msg.split(delim)
                    msgSubTopics = [( topic + "/" + arg) for arg in args]
                    [self.msgPublisher.send(msgSubTopics[i], msgArgs[i]) for i, _ in enumerate(msgArgs)]
                    self.lastTime=time.time()
                    
            except Exception as e:
                self.log.error(f"Exception in Simulated Read :{e}")
                break
        self.log.debug("Exit Simulated Interface Read Thread")
        

    def _writeDevice(self):
        self.log.debug("Started Simulated Device Write Thread")
        self.log.debug("Exit Simulated Interface Write Thread")
    
    # Private Functions
    def _generate_line_data(self) -> str:
        return ':'.join(map(str, [round(random.uniform(0.0, 1.0), 3) for _ in range(3)]))
    
    def _generate_accel_data(self) -> str:
        return ':'.join(map(str, [round(random.uniform(-1.0, 1.0),3) for _ in range(3)]))

    def _generate_gyro_data(self) -> str:
        return ':'.join(map(str, [round(random.uniform(-1.0, 1.0),3) for _ in range(3)]))

    def _generate_msg_for_topic(self) -> tuple[str,str]:
        topics = list(self.topicGenFuncMap.keys())
        topic = random.choice(topics)
        msg = self.topicGenFuncMap[topic]() #execute function to generate data
        return (topic, msg)