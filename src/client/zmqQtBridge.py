from PyQt6.QtCore import *
from PyQt6.QtWidgets import *



from common.logger import getmylogger
from common.worker import Worker
from common.zmqutils import ZmqPub, ZmqSub,Endpoint,Transport
from common.messages import ParameterMap, TopicMap, Topic

class ZmqBridgeQt(QObject):
    msgSig = pyqtSignal(tuple)
    def __init__(self, topicMap: TopicMap, transport: Transport, endpoint: Endpoint):
        super().__init__()
        self.log = getmylogger(__name__)
        self.topicMap = topicMap
        self.workerIO = Worker(self._run)
        self.subscriptions = None
        self.subscriber = ZmqSub(transport=transport, endpoint=endpoint)
      
    def _run(self):
       
        if(self.subscriptions == None):
            self.log.error("No subscriptions")
            self.log.info("Exiting ZmqBridge I/O Thread")
            return
        
        self.subscriber.connect()
        while not self.workerIO.stopEvent.is_set():
            try:
                topicname, msg, _ = self.subscriber.receive()
                topic = self.topicMap.get_topic_by_name(topicname)
                if(isinstance(topic, Topic)):
                    if(topic.nArgs > 2): # HACK makes data-points shallow vs deep
                        msgArgsVal = msg.split(topic.delim)
                        msgSubTopics  = [f"{topicname}/{argname}" for argname in topic.args[:-1]]# HACK ommit timestamp from arg names
                        if len(msgArgsVal) == len(msgSubTopics) :  # check all data is present
                            for i, topicstr in enumerate(msgSubTopics):
                                if(topicstr in self.subscriptions):
                                    self.msgSig.emit((topicstr, msgArgsVal[i]))                                
                    else:
                        self.msgSig.emit((topicname, msg)) 
            except Exception as e:
                self.log.error(f"Exception in ZmqBridgeQt {e}")
                break
        
        self.subscriber.close()
        self.log.info("Exiting ZmqBridge I/O Thread")

    def registerSubscriptions(self, subscriptions: tuple[str, ...]):
        # WTAH have i gotten myself into????? Theres no API I AM the API, no MORE JSON PLS PLS PLS 
        self.subscriptions = subscriptions
        for topicname in subscriptions:
            if("TELEM/TWSB" in topicname):  # HACK
                topicname = "TELEM/TWSB"
            
            topic = self.topicMap.get_topic_by_name(topicname)
            if(isinstance(topic, Topic)):  
                self.subscriber.addTopicSub(topicname)
            else:
                self.log.error(f"Unknown topic {topicname}")

