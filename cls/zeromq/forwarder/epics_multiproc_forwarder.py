

import sys
import zmq
import random
import time
from  multiprocessing import Process
from epics import caput, caget

from .device_map import motors

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


def fowarder_subscriber(port="5560", ext_name='zoneplateX'):
    # Socket to talk to server
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    print("Collecting updates from server on port=%s..." % port)
    print("fowarder_subscriber [topicfilter=%s]: tcp://localhost:%s" % (ext_name,port))
    socket.connect ("tcp://localhost:%s" % port)
    topicfilter = ext_name
    socket.setsockopt(zmq.SUBSCRIBE, topicfilter)
    for update_nbr in range(10):
        print('fowarder_subscriber: string = socket.recv()')
        string = socket.recv()
        topic, messagedata = string.split()
        print('fowarder_subscriber: RECV: ', (topic, messagedata))


def fowarder_subscriber(port="5560", ext_name='zoneplateX'):
    # Socket to talk to server
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    print("Collecting updates from server on port=%s..." % port)
    print("fowarder_subscriber [topicfilter=%s]: tcp://localhost:%s" % (ext_name,port))
    socket.connect ("tcp://localhost:%s" % port)
    topicfilter = ext_name
    socket.setsockopt(zmq.SUBSCRIBE, topicfilter)
    for update_nbr in range(10):
        print('fowarder_subscriber: string = socket.recv()')
        string = socket.recv()
        topic, messagedata = string.split()
        print('fowarder_subscriber: RECV: ', (topic, messagedata))

def fowarder_server(port="5559", ext_name='zoneplateX'):

    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.connect("tcp://localhost:%s" % port)
    print("fowarder_server: tcp://localhost:%s" % port)
    publisher_id = random.randrange(0, 9999)
    while True:
        topic = ext_name
        pvname = motors[ext_name]['RBV']
        val = caget(pvname)
        messagedata = "%s#val=%.3f" % (pvname, val)
        print("[%s] %s %s" % (port, topic, messagedata))
        socket.send("%s %s" % (topic, messagedata))
        time.sleep(0.025)


if __name__ == "__main__":
    from cls.zeromq.ports import front_port, back_port
    #start device
    Process(target=forwarder_device, args=(front_port,back_port)).start()

    for mtr_nm in motors:
        mtr = motors[mtr_nm]
        #server_port = (front_port, back_port)
        Process(target=fowarder_server, args=(front_port, mtr['EXT_NAME'],)).start()
    #Process(target=fowarder_server, args=("5559",)).start()

    time.sleep(1.0)
    # Now we can connect a client to all these servers
    motor = motors['zoneplateX']
    Process(target=fowarder_subscriber, args=(back_port, motor['EXT_NAME'], )).start()
