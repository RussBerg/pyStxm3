import _thread
import time
import zmq
#from zmq.socket import Socket

# global zmg context
context = zmq.Context()
endpoint = "tcp://*:8888"

# the subscriber thread function
def subscriber(name, address, cnt, subscriptions):
    print(("\nstarting worker thread %s subscribing to %s for %s"%(name,address,subscriptions)))
    sub = context.socket(zmq.SUB)
    sub.connect(address)
    for subscription in subscriptions:
        sub.setsockopt(zmq.SUBSCRIBE, subscription)
    for x in range(0, cnt):
        print(("%s received %s" % (name, sub.recv())))
    print(("%s closing socket after %d messages" % (name, cnt)))
    sub.close()

def main():
    publisher = context.socket(zmq.XPUB)
    publisher.bind(endpoint)

    address = "tcp://localhost:8888"
    _thread.start_new(subscriber, ("subscriber1", address, 10, ["a", "b"]))
    _thread.start_new(subscriber, ("subscriber2", address, 20, ["b", "c"]))

    subscriptions = []
    r = 0
    while True:
        # handle subscription flow first to decide what messages need to be produced
        while True:
            try:
                rc = publisher.recv(zmq.NOBLOCK)
                subscription = rc[1:]
                status = rc[0]== "\x01"
                method = subscriptions.append if status else subscriptions.remove
                method(subscription)
            except zmq.ZMQError:
                break

        # produce a value for each existing subscription
        for subscription in subscriptions:
            print("publisher: sending " + subscription)
            publisher.send("%s %d" % (subscription, r))
        time.sleep(0.5)
        r += 1

if __name__ == "__main__":
    main()