
import sys
import matplotlib
matplotlib.use('qt5agg')

from bluesky.plans import count, scan
from bluesky.plan_stubs import pause, open_run, close_run, sleep, mv
from bluesky.callbacks.zmq import Proxy

from ophyd.sim import det1, det2  # two simulated detectors
from ophyd.sim import motor1, motor2
from ophyd import EpicsMotor

from PyQt5 import QtWidgets, QtCore

from qt_run_engine import QRunEngine, EngineWidget


IDLE = 0
RUNNING = 1
PAUSED = 2

def local_plan():
    yield from open_run()
    yield from sleep(1)
    yield from pause()
    yield from close_run()

def motor_plan(mtr1, mtr2, scaler):
    #first move motors to first locations
    yield from mv(mtr1, scaler * 1234, mtr2, scaler * 5773)


def move_then_count(mtr1, mtr2, dets):
    "Move motor1 and motor2 into position; then count det."
    yield from mv(mtr1, 1456, mtr2, 5320)
    yield from count(dets)

def coarse_and_fine(detectors, motor, start, stop, steps):
    "Scan from 'start' to 'stop' in 10 steps and then again in 100 steps."
    yield from scan(detectors, motor, start, stop, steps)
    yield from scan(detectors, motor, start, stop, steps*4)


def start_proxy():
    print('starting Proxy')
    Proxy(5577, 5578).start()

class QRecorder(QtCore.QObject):
    """Helper object to record state change signals"""
    def __init__(self):
        super().__init__()
        self.state_changes = list()

    @QtCore.pyqtSlot('QString', 'QString')
    def on_state_change(self, new, old):
        """Record all state changes"""
        #print('QRecorder: on_state_change: old[%s] new[%s]' % (old, new))
        self.state_changes.append((new, old))

class EngineLabel(QtWidgets.QLabel):
    """
    QLabel to display the RunEngine Status
    Attributes
    ----------
    color_map : dict
        Mapping of Engine states to color displays
    """
    changed = QtCore.pyqtSignal(object)

    color_map = {'running': 'green',
                 'paused': 'yellow',
                 'idle': 'red'}

    @QtCore.pyqtSlot('QString', 'QString')
    def on_state_change(self, state, old_state):
        """Update the display Engine"""
        # Update the label
        self.setText(state.capitalize())
        # Update the background color
        color = self.color_map[state]
        self.setStyleSheet('QLabel {background-color: %s}' % color)
        self.changed.emit(state.capitalize())

    def connect(self, engine):
        """Connect an existing QRunEngine"""
        engine.state_changed.connect(self.on_state_change)
        self.on_state_change(engine.state, None)

# def on_engine_doc(name, docu):
#     print('on_engine_doc')


class Example(QtWidgets.QWidget):

    sig_start = QtCore.pyqtSignal(object)
    changed = QtCore.pyqtSignal(object)

    def __init__(self):
        global start_proxy, on_engine_doc
        super().__init__()

        self.ew = EngineWidget()
        #self.sub_id = self.ew.engine.subscribe(MyCollectThenCompute, name='event')
        self.sub_id = self.ew.engine.subscribe(self.on_engine_doc)

        #self.ew.engine._metadata_per_call = {'user': 'bergr', 'host': 'myNotebook'}
        self.ew.engine.md['user'] = 'bergr'
        self.ew.engine.md['host'] = 'myNotebook'

        self.do_coarse_fineBtn = QtWidgets.QPushButton('Do Coarse and Fine Scan')
        self.startBtn = QtWidgets.QPushButton('Start')
        self.pauseBtn = QtWidgets.QPushButton('Pause')
        self.resumeBtn = QtWidgets.QPushButton('Resume')
        self.abortBtn = QtWidgets.QPushButton('Abort')
        self.haltBtn = QtWidgets.QPushButton('Halt')
        self.lbl = QtWidgets.QLabel('here is the label')

        self.do_coarse_fineBtn.clicked.connect(self.do_coarse_and_fine)
        self.startBtn.clicked.connect(self.go)
        self.pauseBtn.clicked.connect(self.pause)
        self.resumeBtn.clicked.connect(self.resume)
        self.abortBtn.clicked.connect(self.abort)
        self.haltBtn.clicked.connect(self.halt)

        self.status_label = EngineLabel('Engine Status')
        self.status_label.connect(self.ew.engine)
        self.status_label.changed.connect(self.on_state_changed)

        self.changed.connect(self.on_new_msg)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.status_label)
        vbox.addWidget(self.do_coarse_fineBtn)
        vbox.addWidget(self.startBtn)
        vbox.addWidget(self.pauseBtn)
        vbox.addWidget(self.resumeBtn)
        vbox.addWidget(self.abortBtn)
        vbox.addWidget(self.haltBtn)
        vbox.addWidget(self.lbl)

        self.setLayout(vbox)
        self.scaler = 1

        self.cur_state = IDLE

    def on_engine_doc(self, name, doc):
        print('on_engine_doc: [%s]\n' % name)
        self.changed.emit(name)
        print(doc)


    def on_new_msg(self, msg):
        #print('on_new_msg')
        #print(msg)
        self.lbl.setText(msg)

    def on_state_changed(self, state_str):
        print('on_state_changed: [%s]' % state_str)
        if(state_str.find('Idle') > -1):
            self.cur_state = IDLE


    def go(self):
        if(self.cur_state is IDLE):

            # Create a plan
            # ew.engine.plan_creator = lambda: local_plan()
            print('go: top')
            self.cur_state = RUNNING

            #mtr1 = EpicsMotor('IOC:m912', name='mtr_x')
            #mtr2 = EpicsMotor('IOC:m913', name='mtr_y')
            dets = [det1, det2]

            if(self.scaler > 0):
                self.scaler = -1
            else:
                self.scaler = 1

            # ew.engine.plan_creator = lambda: scan(dets, mtr, -1000, 1000, 300)
            self.ew.engine.plan_creator = lambda: motor_plan(motor1, motor2, self.scaler)

            # assert ew.engine.state == 'idle'
            # Start the RunEngine, counter intuitive I know but emitting idle is connecterd to engine start
            self.ew.control.state_widgets['idle'].clicked.emit()

    def do_coarse_and_fine(self):
        if (self.cur_state is IDLE):

            # Create a plan
            # ew.engine.plan_creator = lambda: local_plan()
            print('go: top')
            self.cur_state = RUNNING
            #mtr1 = EpicsMotor('IOC:m912', name='mtr_x')
            #mtr2 = EpicsMotor('IOC:m913', name='mtr_y')

            dets = [det1, det2]

            if (self.scaler > 0):
                self.scaler = -1
            else:
                self.scaler = 1

            steps = 15
            self.ew.engine.plan_creator = lambda: coarse_and_fine(dets, motor1, self.scaler*500, self.scaler*500, steps)

            # assert ew.engine.state == 'idle'
            # Start the RunEngine, counter intuitive I know but emitting idle is connecterd to engine start
            self.ew.control.state_widgets['idle'].clicked.emit()

    def pause(self):
        if(self.cur_state is RUNNING):
            print('pause: top')
            self.cur_state = PAUSED
            #request a pause
            self.ew.control.state_widgets['running'].clicked.emit()

    def resume(self):
        if (self.cur_state is PAUSED):
            print('resume: top')
            self.cur_state = RUNNING
            #resume
            self.ew.control.state_widgets['paused'].clicked.emit()

    def abort(self):
        if (self.cur_state is PAUSED):
            print('abort: top')
            self.cur_state = RUNNING
            #abort
            self.ew.control.state_widgets['abort'].clicked.emit()

    def halt(self):
        if (self.cur_state is PAUSED):
            print('halt: top')
            self.cur_state = RUNNING
            #halt
            self.ew.control.state_widgets['halt'].clicked.emit()






if __name__ == '__main__':
    def mycallback(*args, **kwargs):
        global w
        #print('received this:')
        type = args[0]
        d = args[1]
        #dict_keys(['descriptor', 'time', 'data', 'timestamps', 'seq_num', 'uid', 'filled'])
        #print(d.keys())
        print (d['time'])
        #w.changed.emit(str(d['time']))
        # dct_print(args[0])
        print('\n\n')


    application = app = QtWidgets.QApplication(sys.argv)
    w = Example()
    w.show()
    sys.exit(app.exec_())
    sys.exit(app.exec_())