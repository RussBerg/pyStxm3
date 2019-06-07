############
# Standard #
############
import time
import sys

############
# External #
############
import pytest
from bluesky.plan_stubs import pause, open_run, close_run, sleep, mv
from bluesky.utils import RunEngineInterrupted
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject
from PyQt5 import QtWidgets

from functools import wraps
###########
# Package #
###########

from qt_run_engine import QRunEngine, EngineWidget
from bluesky.plans import count
from ophyd.sim import det1, det2  # two simulated detectors
from ophyd import EpicsMotor
from bluesky.plans import scan

IDLE = 0
RUNNING = 1
PAUSED = 2

show_widgets = False



def local_plan():
    yield from open_run()
    yield from sleep(1)
    yield from pause()
    yield from close_run()

def motor_plan(mtr1, mtr2, scaler):
    #first move motors to first locations
    yield from mv(mtr1, scaler * 1234, mtr2, scaler * 5773)
    #then move them to another location
    yield from mv(mtr1, scaler * 234, mtr2, scaler * 773)


def move_then_count(mtr1, mtr2, dets):
    "Move motor1 and motor2 into position; then count det."
    yield from mv(mtr1, 1456, mtr2, 5320)
    yield from count(dets)

def coarse_and_fine(detectors, motor, start, stop, steps):
    "Scan from 'start' to 'stop' in 10 steps and then again in 100 steps."
    yield from scan(detectors, motor, start, stop, steps)
    yield from scan(detectors, motor, start, stop, steps)


class QRecorder(QObject):
    """Helper object to record state change signals"""
    def __init__(self):
        super().__init__()
        self.state_changes = list()

    @pyqtSlot('QString', 'QString')
    def on_state_change(self, new, old):
        """Record all state changes"""
        self.state_changes.append((new, old))


def test_qrunengine_signals(qapp):
    # Create our Engine and recorder and connect the signal
    QRE = QRunEngine()
    qrec = QRecorder()
    QRE.state_changed.connect(qrec.on_state_change)
    # Run the plan until it pauses automatically
    try:
        QRE(local_plan())
    except RunEngineInterrupted:
        pass
    # Process our first round of events
    qapp.processEvents()
    assert qrec.state_changes[0] == ('running', 'idle')
    assert qrec.state_changes[1] == ('paused', 'running')
    QRE.resume()
    # Process our second round of events
    qapp.processEvents()
    assert qrec.state_changes[2] == ('running', 'paused')
    assert qrec.state_changes[3] == ('idle', 'running')


def test_engine_readback_state_changes(qapp):
    ew = EngineWidget()
    ew.engine.on_state_change('idle', 'running')
    qapp.processEvents()
    assert ew.label.text() == 'Idle'
    assert ew.control.currentWidget().text() == 'Start'
    ew.engine.on_state_change('running', 'idle')
    qapp.processEvents()
    assert ew.control.currentWidget().text() == 'Pause'
    assert ew.label.text() == 'Running'
    ew.engine.on_state_change('paused', 'running')
    qapp.processEvents()
    assert ew.label.text() == 'Paused'
    assert len(ew.control.currentWidget()) == len(ew.control.pause_commands)



def test_engine_plan_execution(qapp):
    # Create a widget and load plans
    ew = EngineWidget()
    # Create a plan
    ew.engine.plan_creator = lambda: local_plan()
    assert ew.engine.state == 'idle'
    # Start the RunEngine
    ew.control.state_widgets['idle'].clicked.emit()
    qapp.processEvents()
    time.sleep(1.0)
    assert ew.engine.state == 'paused'
    # Resume after a pause
    ew.control.currentWidget().activated['QString'].emit('Resume')
    qapp.processEvents()
    time.sleep(0.5)
    assert ew.engine.state == 'idle'
    return ew



def test_mtr_scan_plan_execution(qapp):
    # Create a widget and load plans
    ew = EngineWidget()
    # Create a plan
    #ew.engine.plan_creator = lambda: local_plan()

    mtr1 = EpicsMotor('IOC:m912', name='mtr_x')
    mtr2 = EpicsMotor('IOC:m913', name='mtr_y')
    dets = [det1, det2]
    print('do_scan: calling RE')

    #ew.engine.plan_creator = lambda: scan(dets, mtr, -1000, 1000, 300)
    ew.engine.plan_creator =  lambda: motor_plan(mtr1,mtr2)

    #assert ew.engine.state == 'idle'
    # Start the RunEngine, counter intuitive I know but emitting idle is connecterd to engine start
    ew.control.state_widgets['idle'].clicked.emit()
    #qapp.processEvents()
    #time.sleep(1.0)
    #assert ew.engine.state == 'paused'
    # Resume after a pause
    #ew.control.currentWidget().activated['QString'].emit('Resume')
    #qapp.processEvents()
    #time.sleep(0.5)
    #assert ew.engine.state == 'idle'
    return ew

class EngineLabel(QtWidgets.QLabel):
    """
    QLabel to display the RunEngine Status
    Attributes
    ----------
    color_map : dict
        Mapping of Engine states to color displays
    """
    changed = pyqtSignal(object)

    color_map = {'running': 'green',
                 'paused': 'yellow',
                 'idle': 'red'}

    @pyqtSlot('QString', 'QString')
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


class qt_window(QtWidgets.QWidget):

    sig_start = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.ew = EngineWidget()

        #self.ew.engine._metadata_per_call = {'user': 'bergr', 'host': 'myNotebook'}
        self.ew.engine.md['user'] = 'bergr'
        self.ew.engine.md['host'] = 'myNotebook'

        self.do_coarse_fineBtn = QtWidgets.QPushButton('Do Coarse and Fine Scan')
        self.startBtn = QtWidgets.QPushButton('Start')
        self.pauseBtn = QtWidgets.QPushButton('Pause')
        self.resumeBtn = QtWidgets.QPushButton('Resume')
        self.abortBtn = QtWidgets.QPushButton('Abort')
        self.haltBtn = QtWidgets.QPushButton('Halt')

        self.do_coarse_fineBtn.clicked.connect(self.do_coarse_and_fine)
        self.startBtn.clicked.connect(self.go)
        self.pauseBtn.clicked.connect(self.pause)
        self.resumeBtn.clicked.connect(self.resume)
        self.abortBtn.clicked.connect(self.abort)
        self.haltBtn.clicked.connect(self.halt)

        self.status_label = EngineLabel('Engine Status')
        self.status_label.connect(self.ew.engine)
        self.status_label.changed.connect(self.on_state_changed)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.status_label)
        vbox.addWidget(self.do_coarse_fineBtn)
        vbox.addWidget(self.startBtn)
        vbox.addWidget(self.pauseBtn)
        vbox.addWidget(self.resumeBtn)
        vbox.addWidget(self.abortBtn)
        vbox.addWidget(self.haltBtn)

        self.setLayout(vbox)
        self.scaler = 1

        self.cur_state = IDLE

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

            mtr1 = EpicsMotor('IOC:m912', name='mtr_x')
            mtr2 = EpicsMotor('IOC:m913', name='mtr_y')
            dets = [det1, det2]

            if(self.scaler > 0):
                self.scaler = -1
            else:
                self.scaler = 1

            # ew.engine.plan_creator = lambda: scan(dets, mtr, -1000, 1000, 300)
            self.ew.engine.plan_creator = lambda: motor_plan(mtr1, mtr2, self.scaler)

            # assert ew.engine.state == 'idle'
            # Start the RunEngine, counter intuitive I know but emitting idle is connecterd to engine start
            self.ew.control.state_widgets['idle'].clicked.emit()

    def do_coarse_and_fine(self):
        if (self.cur_state is IDLE):

            # Create a plan
            # ew.engine.plan_creator = lambda: local_plan()
            print('go: top')
            self.cur_state = RUNNING
            mtr1 = EpicsMotor('IOC:m912', name='mtr_x')
            mtr2 = EpicsMotor('IOC:m913', name='mtr_y')
            dets = [det1, det2]

            if (self.scaler > 0):
                self.scaler = -1
            else:
                self.scaler = 1

            steps = 15
            self.ew.engine.plan_creator = lambda: coarse_and_fine(dets, mtr1, self.scaler*500, self.scaler*500, steps)

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
    #application = app = PyDMApplication(use_main_window=False)
    application = app = QtWidgets.QApplication(sys.argv)
    #test_engine_plan_execution(app)
    #test_mtr_scan_plan_execution(app)
    #test_qrunengine_signals(app)
    q = qt_window()
    q.show()

    #q.go()

    sys.exit(app.exec_())