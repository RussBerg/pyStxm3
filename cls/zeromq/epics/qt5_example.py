#!/usr/bin/env python
# -*- coding: utf-8 -*-

import signal
import sys
import uuid

import zmq
import traceback
import io
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtWidgets import QPlainTextEdit, QPushButton
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtCore import QSocketNotifier, QTimer

ENDPOINT = "tcp://localhost:5555"

def excepthook(excType, excValue, tracebackobj):
    """
    Global function to catch unhandled exceptions.

    @param excType exception type
    @param excValue exception value
    @param tracebackobj traceback object
    """
    separator = '-' * 80
    logFile = "simple.log"
    notice = \
        """An unhandled exception occurred. Please report the problem\n""" \
        """using the error reporting dialog or via email to <%s>.\n""" \
        """A log has been written to "%s".\n\nError information:\n""" % \
        ("russ.berg@lightsource.ca", "")
    versionInfo = "0.0.1"
    timeString = time.strftime("%Y-%m-%d, %H:%M:%S")

    tbinfofile = io.StringIO()
    traceback.print_tb(tracebackobj, None, tbinfofile)
    tbinfofile.seek(0)
    tbinfo = tbinfofile.read()
    errmsg = '%s: \n%s' % (str(excType), str(excValue))
    sections = [separator, timeString, separator, errmsg, separator, tbinfo]
    msg = '\n'.join(sections)
    try:
        f = open(logFile, "w")
        f.write(msg)
        f.write(versionInfo)
        f.close()
    except IOError:
        pass
    errorbox = QtWidgets.QMessageBox()
    errorbox.setText(str(notice) + str(msg) + str(versionInfo))
    errorbox.exec_()


class Client():
    def __init__(self):
        #context = zmq.Context.instance()
        #client = context.socket(zmq.REP)
        #client.setsockopt(zmq.IDENTITY, b'QtClient')
        #client.connect(ENDPOINT)

        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect(ENDPOINT)



    def dispatch(self, msg):
        print('dispatch going to try and send this [%s]' % msg)
        #msg = bytes(msg, 'utf-8')
        #uid = uuid.uuid4().bytes
        self.socket.send(msg)
        self.recv()
        #return msg

    def recv(self):
        message =  self.socket.recv()
        print(("Received request: %s" % message))
        return(message)


class Example(QWidget):

    def __init__(self):
        super(Example, self).__init__()

        self.initUI()
        self._client = Client()
        socket = self._client.socket

        self._notifier = QSocketNotifier(socket.getsockopt(zmq.FD), QSocketNotifier.Read, self)
        self._notifier.activated.connect(self._socket_activity)
        self._counter = 0

        self.testTimer = QTimer()
        self.testTimer.timeout.connect(self._send_data)
        self.testTimer.start(250)


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
        self._log("[UI] sent: " + msg)
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
            #self._log("[Socket] zmq.POLLOUT")
            pass
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
    sys.excepthook = excepthook
    w = Example()

    # Ensure that the application quits using CTRL-C
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    sys.exit(app.exec_())