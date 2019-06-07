

import sys
import zmq
import random
import time
from  multiprocessing import Process

def forwarder_device(front_port="5559",back_port="5560"):
    try:
        context = zmq.Context(1)
        # Socket facing clients
        frontend = context.socket(zmq.SUB)
        frontend.bind("tcp://*:%s" % front_port)

        frontend.setsockopt(zmq.SUBSCRIBE, "")

        # Socket facing services
        backend = context.socket(zmq.PUB)
        backend.bind("tcp://*:%s" % back_port)

        print('starting forwarder_device on [front=%s, back=%s]' % (front_port, back_port))
        zmq.device(zmq.FORWARDER, frontend, backend)
    except Exception as e:
        print(e)
        print("bringing down zmq device")
    finally:
        pass
        frontend.close()
        backend.close()
        context.term()


def fowarder_subscriber(port="5560"):
    # Socket to talk to server
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    print("Collecting updates from server on port=%s..." % port)
    print("fowarder_subscriber: tcp://localhost:%s" % port)
    socket.connect ("tcp://localhost:%s" % port)
    topicfilter = "9"
    socket.setsockopt(zmq.SUBSCRIBE, topicfilter)
    for update_nbr in range(10):
        print('fowarder_subscriber: string = socket.recv()')
        string = socket.recv()
        topic, messagedata = string.split()
        print('fowarder_subscriber: RECV: ', (topic, messagedata))


def fowarder_server(port="5559"):


    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.connect("tcp://localhost:%s" % port)
    print("fowarder_server: tcp://localhost:%s" % port)
    publisher_id = random.randrange(0, 9999)
    while True:
        topic = random.randrange(1, 10)
        messagedata = "server#pub_id=%d" % publisher_id
        print("[%s] %s %s" % (port, topic, messagedata))
        socket.send("%d %s" % (topic, messagedata))
        time.sleep(1)

if __name__ == "__main__":

    #start device
    front_port = "5559"
    back_port = "5560"
    Process(target=forwarder_device, args=(front_port,back_port)).start()

    time.sleep(1.0)
    # Now we can run a few servers
    server_ports = list(range(5555, 5561, 1))
    for front_port in server_ports:
        #server_port = (front_port, back_port)
        Process(target=fowarder_server, args=(front_port,)).start()
    #Process(target=fowarder_server, args=("5559",)).start()

    time.sleep(1.0)
    # Now we can connect a client to all these servers
    Process(target=fowarder_subscriber, args=(back_port,)).start()
