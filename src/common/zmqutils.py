import zmq
import argparse
import sys, os
from enum import Enum

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
from common.logger import getmylogger

class Transport(Enum):
    TCP = "tcp://"
    UDP = "udp://"
    INPROC = "inproc://"
    IPC = "ipc:///tmp/"

class Endpoint(Enum):
    COMSTERM_MSG = "comsterm_msg"
    COMSTERM_CMD = "comsterm_cmd"
    BOT_MSG = "bot.local:5555"
    BOT_CMD = "bot.local:5556"
    PC_MSG = "Rodrigos-MacBook-Air.local:5555"
    PC_CMD = "Rodrigos-MacBook-Air.local:5556"
    BB_MSG = "buildbox.local:5555"
    BB_CMD = "buildbox.local:5556"
    DBOT_MSG = "dbot.local:5555"
    DBOT_CMD = "dbot.local:5556"
    LOCAL_MSG = "localhost:5555"
    LOCAL_CMD = "localhost:5556"
    SIG = "siggen"

def buildAddress(transport: Transport, endpoint: Endpoint) -> str:
    return f"{transport.value}{endpoint.value}"

class ZmqPub():
    def __init__(self, transport: Transport, endpoint: Endpoint):
        self.log = getmylogger(__name__)
        self.socketAddress = buildAddress(transport, endpoint)
        self.context = zmq.Context.instance()
        self.socket = self.context.socket(zmq.PUB)

    def bind(self):
        self.socket.bind(self.socketAddress)

    def connect(self):
        self.socket.connect(self.socketAddress)

    def send(self, topic: str, data: str):
        self.socket.send_multipart([topic.encode(), data.encode()])

    def sendTimestamped(self, topic: str, data: str, timestamp: str):
        self.socket.send_multipart([topic.encode(), data.encode(), timestamp.encode()])

    def close(self):
        self.socket.close()

class ZmqSub():
    def __init__(self, transport: Transport, endpoint: Endpoint):
        self.log = getmylogger(__name__)
        self.socketAddress = buildAddress(transport, endpoint)
        self.context = zmq.Context.instance()
        self.socket = self.context.socket(zmq.SUB)

    def connect(self):
        self.socket.connect(self.socketAddress)

    def addTopicSub(self, topic: str):
        self.socket.setsockopt(zmq.SUBSCRIBE, topic.encode())

    def receive(self) -> tuple[str, str, str]:
        try:
            topic, message, timestamp = self.socket.recv_multipart()
            return topic.decode(), message.decode(), timestamp.decode()
        except zmq.Again:
            return "", "", ""
        except Exception as e:
            self.log.error(f"Error receiving message: {e}")
            return "", "", ""

    def close(self):
        self.socket.close()

def main():
    parser = argparse.ArgumentParser(description="ZMQ Publisher/Subscriber CLI")
    parser.add_argument("mode", choices=["pub", "sub"], help="Mode: 'pub' to publish, 'sub' to subscribe")
    parser.add_argument("transport", type=str, choices=[t.name for t in Transport],
                        help="Transport method: TCP, UDP, INPROC, IPC")
    parser.add_argument("endpoint", type=str, choices=[e.name for e in Endpoint],
                        help="Endpoint to bind/connect to (choose from predefined endpoint names)")

    parser.add_argument("--topic", default="", help="Topic to subscribe to (default: all)")

    args = parser.parse_args()

    transport = Transport[args.transport]  # Map string to the corresponding Transport Enum
    endpoint = Endpoint[args.endpoint]  # Map string to the corresponding Endpoint Enum

    if args.mode == "pub":
        publisher = ZmqPub(transport, endpoint)
        publisher.bind()
        print("Publisher is running. Type messages to send (Ctrl+C to exit).")
        try:
            while True:
                topic = input("Enter topic: ").strip()
                message = input("Enter message: ").strip()
                publisher.send(topic, message)
        except KeyboardInterrupt:
            pass
        finally:
            publisher.close()

    elif args.mode == "sub":
        subscriber = ZmqSub(transport, endpoint)
        subscriber.connect()
        subscriber.addTopicSub(args.topic)
        print("Subscriber is running. Receiving messages (Ctrl+C to exit).")
        try:
            while True:
                topic, message,_ = subscriber.receive()
                if topic and message:
                    print(f"{topic}: {message}")
        except KeyboardInterrupt:
            pass
        finally:
            subscriber.close()

if __name__ == "__main__":
    main()
