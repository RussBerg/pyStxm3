from PyQt5 import QtGui, QtCore, QtWidgets
import sys
import zmq

ctx = zmq.Context()

s1 = ctx.socket(zmq.REP)
s1.connect('tcp://localhost:5555')
#s1.setsockopt(zmq.SUBSCRIBE, '')

poller = zmq.Poller()
poller.register(s1, zmq.POLLIN)

def zmq_handler():
    socks = dict(poller.poll(100))
    if (s1 in socks):
        msg = s1.recv()
        print(msg)

app = QtWidgets.QApplication(sys.argv)
#win = MainWindow()
#win.show()

app.lastWindowClosed.connect(app.quit)

timer = QtCore.QTimer(app)
timer.timeout.connect(zmq_handler)
timer.start(0)

app.exec_()