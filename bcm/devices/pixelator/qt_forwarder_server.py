

from PyQt5 import QtWidgets, QtCore
import sys
import zmq
import random
import time
from  multiprocessing import Process
from epics import caput, caget

from .device_map import motors

class qt_forwarder_device(QtCore.QObject):

    def __init__(self, front_port="5560", back_port="5560"):
        super(qt_forwarder_device, self).__init__()

    def run(self):
        try:
            self.context = zmq.Context(1)
            # Socket facing clients
            self.frontend = self.context.socket(zmq.SUB)
            self.frontend.bind("tcp://*:%s" % front_port)

            self.frontend.setsockopt(zmq.SUBSCRIBE, "")

            # Socket facing services
            self.backend = self.context.socket(zmq.PUB)
            self.backend.bind("tcp://*:%s" % back_port)

            print('starting forwarder_device on [front=%s, back=%s]' % (front_port, back_port))
            zmq.device(zmq.FORWARDER, self.frontend, self.backend)
        except Exception as e:
            print(e)
            print("bringing down zmq device")
        finally:
            pass
            self.frontend.close()
            self.backend.close()
            self.context.term()

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


class sig_changed(QtCore.QObject):
    changed = QtCore.pyqtSignal(object, object)
    def __init__(self):
        super(sig_changed, self).__init__()
        self.sharedMemory = QtCore.QSharedMemory('Pixelator_sharedMem')
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.do_update)
        self.timer.start(500)

    def do_update(self):
        print('sig_changed: do_update called')
        if not self.sharedMemory.attach():
            print("Unable to attach to shared memory segment")
            return

        buf = QtCore.QBuffer()
        ins = QtCore.QDataStream(buf)

        self.sharedMemory.lock()
        buf.setData(self.sharedMemory.constData())
        buf.open(QtCore.QBuffer.ReadOnly)
        #ins >> image
        print(ins)
        self.sharedMemory.unlock()
        self.sharedMemory.detach()


class qt_forwarder_subscriber(QtWidgets.QWidget):
    #changed = QtCore.pyqtSignal(object, object)

    def __init__(self, port="5560", ext_name='ZoneplateX'):
        super(qt_forwarder_subscriber, self).__init__()
        self.sharedMemory = QtCore.QSharedMemory('Pixelator_sharedMem')
        # Socket to talk to server
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        print("Collecting updates from server on port=%s..." % port)
        print("qt_forwarder_subscriber [topic=topicfilter=%s]: tcp://localhost:%s" % (ext_name,port))
        self.socket.connect ("tcp://localhost:%s" % port)
        self.topicfilter = ext_name
        self.socket.setsockopt(zmq.SUBSCRIBE, self.topicfilter)
        self._zmq_notifier = QZmqSocketNotifier( self.socket, QtCore.QSocketNotifier.Read )

        # connect signals and slots
        self._zmq_notifier.activated.connect( self._onZmqMsgRecv )

        self.running = True
        print('qt_forwarder_subscriber: done init')

    @QtCore.pyqtSlot()
    def _onZmqMsgRecv(self):
        print('_onZmqMsgRecv')
        # self._test_info_notifier.setEnabled(False)
        # Verify that there's data in the stream
        sock_status = self.socket.getsockopt(zmq.EVENTS)
        if sock_status == zmq.POLLIN:
            msg = self.socket.recv_multipart()
            print(msg)
            topic, s = msg[0].split()
            # topic = msg[0]
            # callback = self._topic_map[ topic ]
            # callback( msg )
            #self.changed.emit(topic, s)
            self.do_update(topic, s)
        self._zmq_notifier.setEnabled(True)
        self.socket.getsockopt(zmq.EVENTS)
        

    def do_update(self, name, val):
        print('qt_forwarder_subscriber: do_update called')
        if self.sharedMemory.isAttached():
            self.detach()

        # Load into shared memory.
        buf = QtCore.QBuffer()
        buf.open(QtCore.QBuffer.ReadWrite)
        out = QtCore.QDataStream(buf)
        out << QtCore.QByteArray('%s=%s' % (name, val))
        size = buf.size()

        if not self.sharedMemory.create(size):
            self.ui.label.setText("Unable to create shared memory segment.")
            return

        size = min(self.sharedMemory.size(), size)
        try:
            self.sharedMemory.lock()

            # Copy image data from buf into shared memory area.
            self.sharedMemory.data()[:size] = buf.data().data()[:size]
            self.sharedMemory.unlock()
        except Exception as e:
            print('qt_forwarder_subscriber: do_update: Exception:' ,e)
            self.sharedMemory.unlock()

    def _onQuit(self):
        self._zmq_notifier.activated.disconnect(self._onZmqMsgRecv)
        self._zmq_notifier.setEnabled(False)
        del self._zmq_notifier
        self._zmq_context.destroy(0)

    # def run(self):
    #     try:
    #         print 'started listening'
    #         while self.running:
    #             _str = self.socket.recv()
    #             topic, messagedata = _str.split()
    #             if (topic is not None):
    #                 print 'thread: rcvd [%s, %s]' % (topic, messagedata)
    #                 self.changed.emit(topic, messagedata)
    #             else:
    #                 print 'socket.recv() timedout'
    #         print 'leaving listener thread'
    #     except Exception, e:
    #         print e
    #         print "qt_forwarder_subscriber: calved"

#def fowarder_server(port="5559", ext_name='ZoneplateX'):
class qt_forwarder_server(QtCore.QObject):
    def __init__(self, port="5559", ext_name='ZoneplateX'):
        super(qt_forwarder_server, self).__init__()
        self.ext_name = ext_name
        self.port = port

    def run(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.connect("tcp://localhost:%s" % self.port)
        print("fowarder_server: tcp://localhost:%s" % self.port)
        publisher_id = random.randrange(0, 9999)
        while True:
            topic = self.ext_name
            pvname = motors[self.ext_name]['RBV']
            val = caget(pvname)
            messagedata = "%s#val=%.3f" % (pvname, val)
            print("[%s] %s %s" % (self.port, topic, messagedata))
            self.socket.send("%s %s" % (topic, messagedata))
            time.sleep(0.025)


if __name__ == "__main__":
    from cls.zeromq.ports import front_port, back_port

    def on_changed(topic, msg):
        print('on_changed: [%s, %s]' % topic, msg)


    app = QtWidgets.QApplication([])

    #start device
    #Process(target=qt_forwarder_device, args=(front_port,back_port)).start()
    qfd = qt_forwarder_device(front_port, back_port)
    qfd_thread = QtCore.QThread()
    qfd.moveToThread(qfd_thread)
    qfd_thread.started.connect(qfd.run)
    qfd_thread.start()

    # for mtr_nm in motors:
    #     mtr = motors[mtr_nm]
    #     #server_port = (front_port, back_port)
    #     Process(target=fowarder_server, args=(front_port, mtr['EXT_NAME'],)).start()
    # #Process(target=fowarder_server, args=("5559",)).start()
    #Process(target=qt_forwarder_server, args=(front_port, 'ZoneplateX',)).start()
    qfs = qt_forwarder_server(front_port, 'ZoneplateX')
    qfs_thread = QtCore.QThread()
    qfs.moveToThread(qfs_thread)
    qfs_thread.started.connect(qfs.run)
    qfs_thread.start()

    time.sleep(1.0)
    # Now we can connect a client to all these servers
    motor = motors['ZoneplateX']
    #qfs = qt_forwarder_subscriber(back_port, motor['EXT_NAME'])
    #
    #Process(target=qt_forwarder_subscriber, args=(back_port, motor['EXT_NAME'], )).start()
    qfsub = qt_forwarder_subscriber(back_port, motor['EXT_NAME'])

    thread = QtCore.QThread()
    qfsub.moveToThread(thread)
    #qfsub.changed.connect(on_changed)
    #thread.started.connect(qfsub.run)
    #QtCore.QTimer.singleShot(0, thread.start)
    thread.start()

    sc = sig_changed()
    sc.changed.connect(on_changed)


    #Process(target=fowarder_subscriber, args=(back_port, motor['EXT_NAME'],)).start()
    #Process(target=qfs).start()
    sys.exit(app.exec_())