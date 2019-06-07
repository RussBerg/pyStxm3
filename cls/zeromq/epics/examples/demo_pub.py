import time
import zmq
context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind('tcp://127.0.0.1:5555')

# Allow clients to connect before sending data
time.sleep(10)
socket.send_pyobj({1:[1,2,3]})
