##########################################################################
##                                                                          ##
##  adapted from http://zguide.zeromq.org/py:wuserver                       ##
##                                                                          ##
##############################################################################


import sys
import zmq

from PyQt5 import QtCore, QtGui, QtWidgets


class ZeroMQ_Listener(QtCore.QObject):
    message = QtCore.pyqtSignal(str)

    def __init__(self):
        QtCore.QObject.__init__(self)

        # Socket to talk to server
        context = zmq.Context()
        #self.socket = context.socket(zmq.REP)

        print("Listening on 5555")
        #self.socket.connect("tcp://*:5555")
        self.socket = context.socket(zmq.REP)
        self.socket.bind("tcp://*:5555")

        # Subscribe to zipcode, default is NYC, 10001
        #filter = str(app.arguments()[1]) if len(app.arguments()) > 1 else "10001"
        #self.socket.setsockopt(zmq.SUBSCRIBE, filter)

        self.running = True

    def loop(self):
        print('started listening')
        while self.running:
            _str = self.socket.recv()

            if(_str is not None):
                print('thread: rcvd [%s]' % _str)
                self.message.emit(_str)
            else:
                print('socket.recv() timedout')
        print('leaving listener thread')


class ZeroMQ_Window(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)

        frame = QtWidgets.QFrame()
        label = QtWidgets.QLabel("listening")
        self.text_edit = QtWidgets.QTextEdit()
        self.abortBtn = QtWidgets.QPushButton('Abort')
        self.abortBtn.clicked.connect(self.on_abort)

        layout = QtWidgets.QVBoxLayout(frame)
        layout.addWidget(label)
        layout.addWidget(self.abortBtn)
        layout.addWidget(self.text_edit)

        self.setCentralWidget(frame)

        self.thread = QtCore.QThread()
        self.zeromq_listener = ZeroMQ_Listener()
        self.zeromq_listener.moveToThread(self.thread)

        self.thread.started.connect(self.zeromq_listener.loop)
        self.zeromq_listener.message.connect(self.signal_received)

        QtCore.QTimer.singleShot(0, self.thread.start)

    def on_abort(self):
        self.zeromq_listener.running = False

    def signal_received(self, message):
        self.text_edit.append("rcvd: %s\n" % message)

    def closeEvent(self, event):
        self.zeromq_listener.running = False
        self.thread.quit()
        self.thread.wait()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    mw = ZeroMQ_Window()
    mw.show()

    sys.exit(app.exec_())