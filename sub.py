import zmq

# Set up ZeroMQ context and socket
context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect("tcp://piStream.local:5555")  # Replace with actual hostname or IP address

# Subscribe to all topics
socket.setsockopt_string(zmq.SUBSCRIBE, '')

# Main function for subscribing
def subscribe_data():
    while True:
        topic, data = socket.recv_multipart()
        if topic.decode() == 'stm':
            print(f"Received: {data}")

if __name__ == "__main__":
    subscribe_data()
