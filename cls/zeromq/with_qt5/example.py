#!/usr/bin/env python
# -*- coding: utf-8 -*-

import signal
import sys
import uuid

import zmq

from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtWidgets import QPlainTextEdit, QPushButton
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtCore import QSocketNotifier

#ENDPOINT = "ipc://routing.ipc"
port = "5560"
ENDPOINT = "tcp://localhost:%s" % port


class Client():
    def __init__(self):
        self.context = zmq.Context.instance()
        self.client = self.context.socket(zmq.DEALER)
        self.client.setsockopt(zmq.IDENTITY, b'QtClient')
        self.client.connect(ENDPOINT)

        self.socket = self.client

    def dispatch(self, msg):
        msg = bytes.encode(msg, 'utf-8')
        uid = uuid.uuid4().bytes
        self.socket.send_multipart([uid, msg])
        return uid

    def recv(self):
        return self.socket.recv_multipart()


class Example(QWidget):

    def __init__(self):
        super(Example, self).__init__()

        self.initUI()
        self._client = Client()
        self.socket = self._client.socket

        self._notifier = QSocketNotifier(self.socket.getsockopt(zmq.FD), QSocketNotifier.Read, self)
        self._notifier.activated.connect(self._socket_activity)
        self._counter = 0

    def initUI(self):
        self.qpteText = QPlainTextEdit(self)
        btn = QPushButton("Send something")
        btn.clicked.connect(self._send_data)

        layout = QGridLayout()
        layout.addWidget(self.qpteText, 1, 1)
        layout.addWidget(btn, 2, 1)
        self.setLayout(layout)

        self.setGeometry(200, 200, 480, 400)
        self.setWindowTitle('QT & ZMQ integration test')
        self.show()

        self._log('[UI] started')

    def _log(self, data):
        text = self.qpteText.toPlainText()
        self.qpteText.setPlainText(text + data + '\n')

    def _send_data(self):
        msg = "Test message #" + str(self._counter)
        self._client.dispatch(msg)
        #self._log("[UI] sent: " + msg)
        self._counter += 1

    def _socket_activity(self):
        self._notifier.setEnabled(False)

        flags = self._client.socket.getsockopt(zmq.EVENTS)
        self._log("[Socket] socket.getsockopt(zmq.EVENTS): " + repr(flags))

        if flags & zmq.POLLIN:
            received = self._client.recv()
            self._log("[Socket] zmq.POLLIN")
            self._log("[Socket] received: " + repr(received))
        elif flags & zmq.POLLOUT:
            self._log("[Socket] zmq.POLLOUT")
        elif flags & zmq.POLLERR:
            self._log("[Socket] zmq.POLLERR")
        else:
            self._log("[Socket] FAILURE")
        self._notifier.setEnabled(True)

        # I have no idea why I need this here, but it won't work more than once
        # if this is not used
        flags = self._client.socket.getsockopt(zmq.EVENTS)
        self._log("[Socket] socket.getsockopt(zmq.EVENTS): " + repr(flags))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Example()

    # Ensure that the application quits using CTRL-C
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    sys.exit(app.exec_())