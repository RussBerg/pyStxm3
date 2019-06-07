
import sys
import matplotlib
matplotlib.use('qt5agg')

from cls.plotWidgets.curveWidget import CurveViewerWidget, get_next_color, get_basic_line_style
from cls.plotWidgets.imageWidget import make_image_widget_window

from bluesky.plans import count, scan, grid_scan
from bluesky.plan_stubs import pause, open_run, close_run, sleep, mv
from bluesky.callbacks.zmq import Proxy
from bluesky.callbacks import LiveTable, LivePlot
from bluesky.callbacks.best_effort import BestEffortCallback


from ophyd.sim import det1, det2, SynGauss, noisy_det
from ophyd.sim import motor1, motor2
from ophyd import EpicsMotor

from PyQt5 import QtWidgets, QtCore

from qt_run_engine import QRunEngine, EngineWidget
from my_callback import MyCollectThenCompute, SpecDataEmitter, ImageDataEmitter


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

def basic_1mtr_scan(detectors, motor, start, stop, steps):
    "Scan from 'start' to 'stop' in 10 steps and then again in 100 steps."
    yield from scan(detectors, motor, start, stop, steps)
    #yield from scan(detectors, motor, start, stop, steps*4)

def basic_2mtr_scan(detectors, motors, starts, stops, stepss, bi_dir=False):
    '''

    :param detectors: a list of detectors
    :param motors: list of 2 motors
    :param starts: list of starts [ mtr1_start, mtr2_start]
    :param stops: list of stops [ mtr1_stop, mtr2_stop]
    :param stepss: list of steps [ mtr1_steps, mtr2_steps]
    :return:
    '''
    return(grid_scan(detectors,
        motors[1], starts[1], stops[1], stepss[1],
        motors[0], starts[0], stops[0], stepss[0], bi_dir) )

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
        super(Example, self).__init__()

        #init devices
        self.motor1 = EpicsMotor('IOC:m912', name='mtr_x')
        self. motor2 = EpicsMotor('IOC:m913', name='mtr_y')
        #self.motor1 = motor1
        #self.motor2 = motor2
        self.motors = [self.motor1, self.motor2]
        self.dets = [noisy_det, det2]

        #init plotter
        self.spec_plot = CurveViewerWidget(toolbar=True)
        self.spec_plot.regTools()
        self.spec_plot.add_legend("TL")

        self.image_plot = make_image_widget_window()

        self.tabs = QtWidgets.QTabWidget()
        self.tab1 = QtWidgets.QWidget()
        self.tab2 = QtWidgets.QWidget()
        self.tabs.setMinimumSize(QtCore.QSize(400, 400))

        # Add tabs
        self.tabs.addTab(self.tab1, "Spec Plot")
        self.tabs.addTab(self.tab2, "Image Plot")

        self.tab1.layout = QtWidgets.QVBoxLayout()
        self.tab2.layout = QtWidgets.QVBoxLayout()

        self.tab1.layout.addWidget(self.spec_plot)
        self.tab2.layout.addWidget(self.image_plot)

        self.tab1.setLayout(self.tab1.layout)
        self.tab2.setLayout(self.tab2.layout)

        clr = get_next_color(use_dflt=False)
        style = get_basic_line_style(clr)
        #style = get_histogram_style(clr)
        self.spec_plot.create_curve('point_spectra_%d' % 0, curve_style=style)

        self.ew = EngineWidget()
        #self.sub_id = self.ew.engine.subscribe(MyCollectThenCompute, name='event')
        #self.sub_id = self.ew.engine.subscribe(self.on_engine_doc)
        #this worked   self.sub_id2 = self.ew.engine.subscribe(LiveTable(['motor']))
        # this also worked self.sub_id2 = self.ew.engine.subscribe(MyCollectThenCompute())

        self.sub_id = self.ew.subscribe_cb(self.on_update_label)

        self.spec_cb = SpecDataEmitter('noisy_det', x='mtr_x')
        self.spec_cb.new_data.connect(self.on_new_spec_data)
        self.spec_sub = None

        #self.image_cb = ImageDataEmitter('noisy_det',y='mtr_y', x='mtr_x')
        self.image_cb = ImageDataEmitter('noisy_det')
        self.image_cb.new_data.connect(self.on_new_image_data)
        self.image_cb.final_data.connect(self.on_final_image_data)
        self.image_sub = None

        #bec = BestEffortCallback()
        #self.sub_id3 = self.ew.engine.subscribe(bec)

        #self.ew.engine._metadata_per_call = {'user': 'bergr', 'host': 'myNotebook'}
        self.ew.engine.md['user'] = 'bergr'
        self.ew.engine.md['host'] = 'myNotebook'

        self.do_coarse_fineBtn = QtWidgets.QPushButton('Do Coarse and Fine Scan')
        self.do_2mtr_scanBtn = QtWidgets.QPushButton('Do 2D scan')
        self.startBtn = QtWidgets.QPushButton('Start')
        self.pauseBtn = QtWidgets.QPushButton('Pause')
        self.stopBtn = QtWidgets.QPushButton('Stop')
        self.resumeBtn = QtWidgets.QPushButton('Resume')
        self.haltBtn = QtWidgets.QPushButton('Halt')
        self.lbl = QtWidgets.QLabel('here is the label')

        self.do_coarse_fineBtn.clicked.connect(self.do_basic_1mtr_scan)
        self.do_2mtr_scanBtn.clicked.connect(self.do_2mtr_scan)
        self.startBtn.clicked.connect(self.go)
        self.stopBtn.clicked.connect(self.stop)
        self.pauseBtn.clicked.connect(self.pause)
        self.resumeBtn.clicked.connect(self.resume)
        self.haltBtn.clicked.connect(self.halt)

        self.status_label = EngineLabel('Engine Status')
        self.status_label.connect(self.ew.engine)
        self.status_label.changed.connect(self.on_state_changed)

        self.changed.connect(self.on_new_msg)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.tabs)
        #vbox.addWidget(self.image_plot)
        vbox.addWidget(self.status_label)
        vbox.addWidget(self.do_2mtr_scanBtn)
        vbox.addWidget(self.do_coarse_fineBtn)
        vbox.addWidget(self.startBtn)
        vbox.addWidget(self.stopBtn)
        vbox.addWidget(self.pauseBtn)
        vbox.addWidget(self.resumeBtn)
        vbox.addWidget(self.haltBtn)
        vbox.addWidget(self.lbl)

        self.setLayout(vbox)
        self.start_scaler = 1
        self.stop_scaler = -1

        self.cur_state = IDLE

    def do_clear_spec_plot(self):
        self.spec_plot.reset_curve()

    def do_clear_image_plot(self):
        self.image_plot.delImagePlotItems()

    def on_new_spec_data(self, tpl):
        #print('ON_NEW_SPECTRA_DATA')
        #print(dct)
        self.spec_plot.addXYPoint('point_spectra_%d' % 0, tpl[0], tpl[1], update=True)

    def on_new_image_data(self, tpl):
        #print('ON_NEW_IMAGE_DATA')
        print(tpl)
        self.image_plot.addPoint(tpl[1], tpl[0], tpl[2], show=True)

    def on_final_image_data(self, dct):
        print('on_final_image_data:')
        print(dct)

    def on_update_label(self, name, doc):
        #print('on_update_label: [%s]\n' % name)
        self.changed.emit(name)

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

            self.clear_cb_subscriptions()
            self.spec_sub = self.ew.subscribe_cb(self.spec_cb)

            self.do_clear_spec_plot()
            # Create a plan
            self.cur_state = RUNNING

            steps = 50
            # ew.engine.plan_creator = lambda: scan(dets, mtr, -1000, 1000, 300)
            self.ew.engine.plan_creator = lambda: basic_1mtr_scan(self.dets, self.motor1, -3500, 3500, steps)

            # assert ew.engine.state == 'idle'
            # Start the RunEngine, counter intuitive I know but emitting idle is connecterd to engine start
            self.ew.control.state_widgets['idle'].clicked.emit()

    def clear_cb_subscriptions(self):
        if (self.image_sub):
            self.ew.unsubscribe_cb(self.image_sub)

        if (self.spec_sub):
            self.ew.unsubscribe_cb(self.spec_sub)

        self.image_sub = None
        self.spec_sub = None

    def do_basic_1mtr_scan(self):
        if (self.cur_state is IDLE):

            self.clear_cb_subscriptions()

            self.spec_sub = self.ew.subscribe_cb(self.spec_cb)

            self.do_clear_spec_plot()
            # Create a plan
            self.cur_state = RUNNING

            steps = 15
            #self.ew.engine.plan_creator = lambda: basic_1mtr_scan(dets, mtr1, self.scaler*3500, self.scaler*3500, steps)
            self.ew.engine.plan_creator = lambda: scan(self.dets, self.motor1, -3500, 3500, steps)

            # Start the RunEngine, counter intuitive I know but emitting idle is connecterd to engine start
            self.ew.control.state_widgets['idle'].clicked.emit()


    def do_2mtr_scan(self):
        if (self.cur_state is IDLE):
            rows = 20
            cols = 20
            image_type = 0

            self.clear_cb_subscriptions()

            self.image_cb.set_row_col(rows, cols)
            self.image_sub = self.ew.subscribe_cb(self.image_cb)

            self.do_clear_image_plot()

            # Create a plan
            self.cur_state = RUNNING

            (x1, y1, x2, y2) = (-5000, -3000, 5000, 3000)

            self.image_plot.initData(image_type, rows, cols, {'RECT': (x1, y1, x2, y2)})
            self.image_plot.set_autoscale(fill_plot_window=False)

            self.ew.engine.plan_creator = lambda: basic_2mtr_scan(self.dets, self.motors, [y1, y2], [x1, x2], [cols, rows])

            # Start the RunEngine, counter intuitive I know but emitting idle is connecterd to engine start
            self.ew.control.state_widgets['idle'].clicked.emit()



    def pause(self):
        if(self.cur_state is RUNNING):
            print('pause: top')
            self.cur_state = PAUSED
            #request a pause
            self.ew.control.state_widgets['running'].clicked.emit()

    def stop(self):
        if (self.cur_state is PAUSED):
            print('stop: top')
            self.cur_state = RUNNING
            #resume
            self.ew.control.state_widgets['stop'].clicked.emit()

    def resume(self):
        if (self.cur_state is PAUSED):
            print('resume: top')
            self.cur_state = RUNNING
            #resume
            self.ew.control.state_widgets['paused'].clicked.emit()

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
