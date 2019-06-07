#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random

import zmq

ENDPOINT = "tcp://*:5555"


def main():
    context = zmq.Context.instance()
    worker = context.socket(zmq.REP)
    worker.bind(ENDPOINT)

    while True:
        #request = worker.recv_multipart()
        msg = worker.recv()
        print(("[Worker] received request: ", msg))
        #client_id, msg_id, msg = request

        if random.choice([True, True, False]):  # should I respond?
            response = msg + b'(received)'
            #worker.send_multipart([client_id, msg_id, response])
            worker.send('earsBeard')
            print("[Worker] response sent: earsBeard")

        if msg == b"END":
            break


if __name__ == "__main__":
    main()