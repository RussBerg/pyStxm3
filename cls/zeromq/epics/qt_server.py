import zmq
from PyQt5 import QtCore, QtGui, QtWidgets

class QZmqSocketNotifier( QtCore.QSocketNotifier ):
    """ Provides Qt event notifier for ZMQ socket events """
    def __init__( self, zmq_sock, event_type, parent=None ):
        """
        Parameters:
        ----------
        zmq_sock : zmq.Socket
            The ZMQ socket to listen on. Must already be connected or bound to a socket address.
        event_type : QtSocketNotifier.Type
            Event type to listen for, as described in documentation for QtSocketNotifier.
        """
        super( QZmqSocketNotifier, self ).__init__( zmq_sock.getsockopt(zmq.FD), event_type, parent )

class Server(QtWidgets.QFrame):

    def __init__(self, topics=['ZoneplateX'], port='5556', parent=None):
        super(Server, self).__init__(parent)

        self._PORT = port

        # Create notifier to handle ZMQ socket events coming from client
        self._zmq_context = zmq.Context()
        self._zmq_sock = self._zmq_context.socket( zmq.SUB )
        self._zmq_sock.bind( "tcp://*:" + self._PORT )
        for topic in topics:
            self._zmq_sock.setsockopt( zmq.SUBSCRIBE, topic )
        self._zmq_notifier = QZmqSocketNotifier( self._zmq_sock, QtCore.QSocketNotifier.Read )

        # connect signals and slots
        self._zmq_notifier.activated.connect( self._onZmqMsgRecv )
        #mainwindow.quit.connect( self._onQuit )

    @QtCore.pyqtSlot()
    def _onZmqMsgRecv(self):
        #self._test_info_notifier.setEnabled(False)
        # Verify that there's data in the stream
        sock_status = self._zmq_sock.getsockopt( zmq.EVENTS )
        if sock_status == zmq.POLLIN:
            msg = self._zmq_sock.recv_multipart()
            print(msg)
            # topic = msg[0]
            # callback = self._topic_map[ topic ]
            # callback( msg )
        self._zmq_notifier.setEnabled(True)
        self._zmq_sock.getsockopt(zmq.EVENTS)

    def _onQuit(self):
        self._zmq_notifier.activated.disconnect( self._onZmqMsgRecv )
        self._zmq_notifier.setEnabled(False)
        del self._zmq_notifier
        self._zmq_context.destroy(0)


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)

    mw = Server()
    mw.show()

    sys.exit(app.exec_())