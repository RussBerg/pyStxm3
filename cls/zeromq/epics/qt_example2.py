import sys
import zmq

from PyQt5 import QtCore, QtGui, QtWidgets


class ZeroMQ_Listener(QtCore.QObject):
    message = QtCore.pyqtSignal(str)

    def __init__(self):
        QtCore.QObject.__init__(self)

        # ZeroMQ endpoint
        context = zmq.Context()
        self.socket = context.socket(zmq.PULL)
        self.socket.connect("tcp://localhost:5555")

        self.running = True

    def loop(self):
        while self.running:
            string = self.socket.recv()
            self.message.emit(string)

class ZeroMQ_Window(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)
        frame = QtWidgets.QFrame()
        label = QtWidgets.QLabel("listening")
        self.text_edit = QtWidgets.QTextEdit()
        layout = QtWidgets.QVBoxLayout(frame)
        layout.addWidget(label)
        layout.addWidget(self.text_edit)
        self.setCentralWidget(frame)

        # ZeroMQ hook up listener to Qt
        self.thread = QtCore.QThread()
        self.zeromq_listener = ZeroMQ_Listener()
        self.zeromq_listener.moveToThread(self.thread)
        self.thread.started.connect(self.zeromq_listener.loop)
        self.zeromq_listener.message.connect(self.signal_received)
        QtCore.QTimer.singleShot(0, self.thread.start)

    def signal_received(self, message):
        self.text_edit.append("%s\n" % message)

    def closeEvent(self, event):
        self.zeromq_listener.running = False
        self.thread.quit()
        self.thread.wait()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    mw = ZeroMQ_Window()
    mw.show()
    sys.exit(app.exec_())