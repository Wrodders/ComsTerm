import zmq
import argparse
import sys,os
from enum import Enum


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
from common.logger import getmylogger

class Transport(Enum):
    INPROC = "inproc"
    IPC = "ipc"
    TCP = "tcp"
    UDP = "udp"

class Endpoint(Enum):
    COMSTERM_MSG = "comsterm_msg"
    COMSTERM_CMD = "comsterm_cmd"
    PI_MSG = "raspberrypi.local:5555"
    PI_CMD = "raspberrypi.local:5556"
    PC_MSG = "Rodrigos-MacBook-Air.local:5555"
    PC_CMD = "Rodrigos-MacBook-Air.local:5556"
    DBOT_MSG = "dbot.local:5555"
    DBOT_CMD = "dbot.local:5556"
    LOCAL_MSG= "*:5555"
    LOCAL_CMD = "*:5556"

def buildAddress(transport: Transport, endpoint: Endpoint) -> str:
    if transport == Transport.TCP:
        return f"{transport.value}://{endpoint.value}"
    elif transport == Transport.IPC:
        return f"{transport.value}:///tmp/{endpoint.value}"
    elif transport == Transport.INPROC:
        return f"{transport.value}://{endpoint.value}"
    else:
        raise ValueError(f"Unsupported transport type: {transport.value}")

class ZmqPub:
    def __init__(self, transport: Transport, endpoint: Endpoint):
        self.log = getmylogger(__name__)
        self.socketEndpoint = buildAddress(transport, endpoint)
        self.context = zmq.Context.instance()
        self.socket = self.context.socket(zmq.PUB)
    
    def bind(self):
        self.socket.bind(self.socketEndpoint)
        self.log.debug(f"Binded ZMQ PUB socket to {self.socketEndpoint}")

    def send(self, topic: str, data: str):
        topic_b = topic.encode() if isinstance(topic, str) else topic
        data_b = data.encode() if isinstance(data, str) else data
        self.socket.send_multipart([topic_b, data_b])

    def close(self):
        if self.socket:
            self.socket.close()
            self.log.debug(f"Closed ZMQ PUB socket binded to: {self.socketEndpoint}")

class ZmqSub:
    def __init__(self, transport: Transport, endpoint: Endpoint):
        self.log = getmylogger(__name__)
        self.socketAddress = buildAddress(transport, endpoint)
        self.context = zmq.Context.instance()
        self.socket = self.context.socket(zmq.SUB)
        self.topicList = []

    def connect(self):
        self.socket.connect(self.socketAddress)
        self.log.debug(f"Connected ZMQ SUB socket to: {self.socketAddress}")

    def addTopicSub(self, topic: str):
        if topic not in self.topicList:
            self.socket.setsockopt(zmq.SUBSCRIBE, topic.encode())
            self.topicList.append(topic)
           
            self.log.debug(f"ZMQ SUB Subscribed to {topic}")

    def receive(self) -> tuple[str, str]:
        try:
            dataFrame = self.socket.recv_multipart()
            return (dataFrame[0].decode(), dataFrame[1].decode())
        except zmq.Again:
            return ("", "")
        except Exception as e:
            self.log.error(f"Exception in ZMQSUB Receive: {e}")
            return ("", "")

    def close(self):
        self.socket.close()
        self.log.debug(f"Closed ZMQ SUB socket connected to: {self.socketAddress}")

def main():
    parser = argparse.ArgumentParser(description="ZMQ Publisher/Subscriber")
    parser.add_argument("mode", choices=["pub", "sub"], help="Run as publisher or subscriber")
    parser.add_argument("transport", type=str, choices=[t.value for t in Transport],
                        help="Transport method: inproc, ipc, tcp, udp")
    parser.add_argument("endpoint", type=str, choices=[e.value for e in Endpoint],
                        help="Endpoint to bind/connect to")

    args = parser.parse_args()

    if args.mode == "pub":
        publisher = ZmqPub(Transport(args.transport), Endpoint(args.endpoint))
        publisher.bind()
        print("Publisher is running. Type messages to send (Ctrl+C to exit).")
        try:
            while True:
                publisher.socket.send_multipart([pckt.encode()+b'\n' for pckt in input("ENTER:").split('/')])
        except KeyboardInterrupt:
            pass
        finally:
            publisher.close()

    elif args.mode == "sub":
        subscriber = ZmqSub(Transport(args.transport), Endpoint(args.endpoint))
        subscriber.connect()
        subscriber.addTopicSub("")  # Subscribe to all messages
        print("Subscriber is running. Receiving messages (Ctrl+C to exit).")
        try:
            while True:
                topic, message = subscriber.receive()
                if topic and message:
                    print(f"{topic} {message}")
        except KeyboardInterrupt:
            pass
        finally:
            subscriber.close()

if __name__ == "__main__":
    main()
