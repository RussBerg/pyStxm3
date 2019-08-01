############
# Standard #
############
import logging
import time

from time import localtime, gmtime

############
# External #
############
from bluesky import RunEngine
from bluesky.utils import RunEngineInterrupted, install_qt_kicker
from bluesky.preprocessors import SupplementalData
from ophyd.log import set_handler

from databroker import list_configs
from databroker import Broker

from PyQt5.QtWidgets import QVBoxLayout, QLabel, QComboBox, QGroupBox
from PyQt5.QtWidgets import QStackedWidget, QPushButton
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

from cls.utils.log import get_module_logger

_logger = get_module_logger(__name__)


class QRunEngine(QObject, RunEngine):
    state_changed = pyqtSignal(str, str)
    msg_changed = pyqtSignal(object)
    exec_result = pyqtSignal(object)
    prog_changed = pyqtSignal(object)
    update_rate = 0.02
    command_registry = {'Halt': RunEngine.halt,
                        'Abort': RunEngine.abort,
                        'Resume': RunEngine.resume,
                        'Pause': RunEngine.request_pause,
                        'Stop': RunEngine.stop}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Attach the state_hook to emit signals
        self.state_hook = self.on_state_change
        self._execution_result = None
        #self.msg_hook = self.on_msg_hook
        self.subscribe(self.update_progess)
        self.subscribe(self.print_msg)
        #self.waiting_hook = self.check_progress
        #self.waiting_hook = MyProgressBar
        # Create a kicker, not worried about doing this multiple times as this
        # is checked by `install_qt_kicker` itself
        install_qt_kicker(update_rate=self.update_rate)
        # Allow a plan to be stored on the RunEngine
        self.plan_creator = None
        #self.log.setLevel(logging.DEBUG)
        #self.log.addHandler(file='debugging_bluesky.txt')
        #fh = logging.FileHandler(r'C:\wrkshp\live_qt5\bs_plan_studio\debugging_bluesky.txt')
        #fh.setLevel(logging.DEBUG)
        #_logger.addHandler(fh)
        self.meters = []
        self._max_prog_pnts = 0
        self._event_uid = 0
        self._master_start_time = 0
        self._start_time = 0
        self._stop_time = 0
        self._scan_idx = -1

    def create_prog_dict(self, scan_idx, start_time, stop_time, prog):
        elapsed_tm = gmtime(stop_time - start_time)
        elapsed_tm_str = time.strftime("Elapsed time %H:%M:%S", elapsed_tm)
        mstr_elapsed_tm = gmtime(stop_time - self._master_start_time)
        mstr_elapsed_tm_str = time.strftime("%H:%M:%S", mstr_elapsed_tm)

        dct = {}
        dct['scan_idx'] = scan_idx
        dct['prog'] = prog
        dct['elapsed_tm_str'] = elapsed_tm_str
        dct['elapsed_tm'] = elapsed_tm
        dct['mstr_elapsed_tm_str'] = mstr_elapsed_tm_str
        dct['mstr_elapsed_tm'] = mstr_elapsed_tm
        return(dct)

    def print_msg(self, name, doc):
        _logger.info('PRINT_MSG: name=%s' % name)
        print(doc)

    def update_progess(self, name, doc):
        '''
        update_progress subscribes to the msgs from the runengine and pulls out th eparts needed to determine the
        progress of the current scan
        :param name:
        :param doc:
        :return:
        '''
        if(name.find('start') > -1):
            if(self._master_start_time == 0):
                self._master_start_time = doc['time']

            self._start_time = doc['time']
            self._scan_idx += 1
            if('num_points' in list(doc.keys())):
                self._max_prog_pnts = doc['num_points']
            else:
                #indicate that the scan is a flyer
                self._max_prog_pnts = -1
                print('Scan progress: Flyer scan in progress...')
                if (self._stop_time <= self._start_time):
                    #elapsed_tm = gmtime((self._start_time + 1.0) - self._start_time)
                    #elapsed_tm_str = time.strftime("Elapsed time %H:%M:%S", elapsed_tm)
                    #d = self.create_prog_dict((self._start_time + 1.0), self._start_time)
                    #self.prog_changed.emit({'scan_idx': self._scan_idx, 'prog': 0.0, 'elapsed_tm_str': elapsed_tm_str, 'elapsed_tm': elapsed_tm})
                    d = self.create_prog_dict(self._scan_idx, (self._start_time + 1.0), self._start_time, prog=0.0)
                    self.prog_changed.emit(d)

                else:
                    # elapsed_tm = gmtime(self._stop_time - self._start_time)
                    # elapsed_tm_str = time.strftime("Elapsed time %H:%M:%S", elapsed_tm)
                    # # print('Scan progress: %d/%d %.2f complete| %s ' % (seq_num, self._max_prog_pnts, prog, elapsed_tm_str))
                    # self.prog_changed.emit({'scan_idx': self._scan_idx, 'prog': 0.0, 'elapsed_tm_str': elapsed_tm_str,
                    #                         'elapsed_tm': elapsed_tm})
                    d = self.create_prog_dict(self._scan_idx, self._stop_time, self._start_time, prog=0.0)
                    self.prog_changed.emit(d)

        if (name.find('bulk_events') > -1):
            #keep updating the stop time from teh first of the bulk events
            #self._event_uid = list(doc.keys())[0]
            #self._stop_time = doc[self._event_uid][0]['time']
            #print(name, doc)
            #self._stop_time = time.time()
            #self._scan_idx = doc['scan_id']
            pass



        elif (name.find('event') > -1):
            seq_num = doc['seq_num']
            if (seq_num == 1):
                #print('Scan progress: 0.0% complete')
                #self.prog_changed.emit(0.0)
                return
            elif(seq_num <= self._max_prog_pnts):
                self._stop_time = doc['time']
                if(self._event_uid is 0):
                    #these are the events we want to look at for progress, all others skipped
                    self._event_uid = doc['descriptor']
                if(doc['descriptor'] == self._event_uid):
                    prog = (float(seq_num) / float(self._max_prog_pnts)) * 100.0
                    # elapsed_tm = gmtime(self._stop_time - self._start_time)
                    # elapsed_tm_str = time.strftime("Elapsed time %H:%M:%S", elapsed_tm)
                    # #print('Scan progress: %d/%d %.2f complete| %s ' % (seq_num, self._max_prog_pnts, prog, elapsed_tm_str))
                    # self.prog_changed.emit({'scan_idx': self._scan_idx, 'prog':prog, 'elapsed_tm_str':elapsed_tm_str, 'elapsed_tm': elapsed_tm})
                    d = self.create_prog_dict(self._scan_idx, self._stop_time, self._start_time, prog=prog)
                    self.prog_changed.emit(d)

        if (name.find('stop') > -1):
            self._stop_time = doc['time']
            #time_str = time.strftime("%H:%M:%S", localtime(self._stop_time))
            #print('Scan progress: 100% complete | %s ' % (time_str))
            if (self._stop_time <= self._start_time):
                # elapsed_tm = gmtime((self._start_time + 1.0) - self._start_time)
                # elapsed_tm_str = time.strftime("Elapsed time %H:%M:%S", elapsed_tm)
                # self.prog_changed.emit(
                #     {'scan_idx': self._scan_idx, 'prog': 0.0, 'elapsed_tm_str': elapsed_tm_str, 'elapsed_tm': elapsed_tm})
                d = self.create_prog_dict(self._scan_idx, (self._start_time + 1.0), self._start_time, prog=0.0)
                self.prog_changed.emit(d)

            else:
                # elapsed_tm = gmtime(self._stop_time - self._start_time)
                # elapsed_tm_str = time.strftime("Elapsed time %H:%M:%S", elapsed_tm)
                # #print('Scan progress: complete | %s ' % (elapsed_tm_str))
                #self.prog_changed.emit({'scan_idx': self._scan_idx, 'prog': 100.0, 'elapsed_tm_str': elapsed_tm_str, 'elapsed_tm': elapsed_tm})
                d = self.create_prog_dict(self._scan_idx, self._stop_time, self._start_time, prog=100.0)
                self.prog_changed.emit(d)

            self._max_prog_pnts = 0


        #print(name, doc)

    # def check_progress(self, status_objs):
    #
    #     if(status_objs is not None):
    #         for st in status_objs:
    #             if hasattr(st, 'watch') and not st.done:
    #                 #if hasattr(st, 'finish_pos') and not st.done:
    #                 pos = len(self.meters)
    #                 print('[%d]' % pos)
    #                 print(dir(st))
    #                 #print(st.start_pos, st.pos, st.finish_pos)
    #
    #                 self.meters.append('')
    #     #         #self.status_objs.append(st)
    #     #         #st.watch(partial(self.update, pos))

    def on_state_change(self, state, old_state):
        """
        Report a state change of the RunEngine
        This is added directly to the `RunEngine.state_hook` and emits the
        `engine_state_change` signal.
        Parameters
        ----------
        state: str
        old_state: str
        """
        _logger.info('on_state_change: %s, %s'% (state, old_state))
        self.state_changed.emit(state, old_state)

    def on_msg_hook(self, msg):
        """
        """
        #self.msg_changed.emit(msg)
        _logger.debug(msg)
        #pass


    @pyqtSlot()
    def start(self):
        """Start the RunEngine"""
        self._max_prog_pnts = 0
        self._event_uid = 0
        self._start_time = 0
        self._stop_time = 0
        self._scan_idx = -1
        self._master_start_time = 0
        if not self.plan_creator:
            _logger.error("Commanded RunEngine to start but there "
                         "is no source for a plan")
            return
        # Execute our loaded function
        try:
            self._execution_result = None
            self._execution_result = self.__call__(self.plan_creator())
            self.exec_result.emit(self._execution_result)
            # print(ret)
        # Pausing raises an exception
        # except RunEngineInterrupted as exc:
        #     _logger.debug("RunEngine paused")
        except RunEngineInterrupted as exc:
            _logger.debug("RunEngine interrupted")
            self.exec_result.emit(self._run_start_uids)

    @pyqtSlot()
    def pause(self):
        """Pause the RunEngine"""
        self.request_pause()

    @pyqtSlot('QString')
    def command(self, command):
        """
        Accepts commands and instructs the RunEngine accordingly
        Parameters
        ----------
        command : str
            Name of the command in the :attr:`.command_registry:`
        """
        _logger.info("Requested command %s for RunEngine", command)
        # Load the function from registry
        try:
            func = self.command_registry[command]
        # Catch commands that we have no idea how to obey
        except KeyError as exc:
            _logger.exception('Unrecognized command for RunEngine -> %s',
                             exc)
        # Execute the command
        else:
            try:
                func(self)
            except RunEngineInterrupted as exc:
                _logger.debug("RunEngine paused")

class EngineLabel(QLabel):
    """
    QLabel to display the RunEngine Status
    Attributes
    ----------
    color_map : dict
        Mapping of Engine states to color displays
    """
    color_map = {'running': 'red',
                 'paused': 'yellow',
                 'idle': 'green'}

    @pyqtSlot('QString', 'QString')
    def on_state_change(self, state, old_state):
        """Update the display Engine"""
        # Update the label
        self.setText(state.capitalize())
        # Update the background color
        color = self.color_map[state]
        self.setStyleSheet('QLabel {background-color: %s}' % color)

    def connect(self, engine):
        """Connect an existing QRunEngine"""
        engine.state_changed.connect(self.on_state_change)
        self.on_state_change(engine.state, None)

class EngineControl(QStackedWidget):
    """
    RunEngine through a QComboBox
    Listens to the state of the RunEngine and shows the available commands for
    the current state.
    Attributes
    ----------
    state_widgets: dict
    pause_commands: list
        Available RunEngine commands while the Engine is Paused
    """

    pause_commands = ['Abort', 'Halt',  'Resume', 'Stop']

    # def __init__(self, parent=None):
    #     super().__init__(parent=parent)
    #     # Create our widgets
    #     # self.state_widgets = {'idle': QPushButton('Start'),
    #     #                       'running': QPushButton('Pause'),
    #     #                       'paused': QPushButton('Resume'),
    #     #                       'stop': QPushButton('Stop'),
    #     #                       'halt': QPushButton('Halt')}
    #     #                       #'paused': QComboBox()}
    #     self.state_widgets = {'start': QPushButton('Start'),
    #                           'pause': QPushButton('Pause'),
    #                           'resume': QPushButton('Resume'),
    #                           'stop': QPushButton('Stop'),
    #                           'halt': QPushButton('Halt')}
    #     # 'paused': QComboBox()}
    #     # Add the options to QComboBox
    #     #self.state_widgets['paused'].insertItems(0, self.pause_commands)
    #     ## Add all the widgets to the stack
    #     for widget in self.state_widgets.values():
    #         self.addWidget(widget)

    def __init__(self, engine, parent=None):
        super().__init__(parent=parent)
        # Create our widgets
        self.engine = engine
        self.startBtn = QPushButton('Start')
        self.pauseBtn = QPushButton('Pause')
        self.resumeBtn = QPushButton('Resume')
        self.stopBtn = QPushButton('Stop')
        self.haltBtn = QPushButton('Halt')

        self.state_widgets = {'start': self.startBtn,
                              'pause': self.pauseBtn,
                              'resume': self.resumeBtn,
                              'stop': self.stopBtn,
                              'halt': self.haltBtn}
        # 'paused': QComboBox()}
        # Add the options to QComboBox
        # self.state_widgets['paused'].insertItems(0, self.pause_commands)
        self._cur_state = None
        ## Add all the widgets to the stack
        for widget in self.state_widgets.values():
            self.addWidget(widget)

    @pyqtSlot('QString', 'QString')
    def on_state_change(self, state, old_state):
        """Update the control widget based on the state"""
        #self.setCurrentWidget(self.state_widgets[state])
        self._cur_state = (state, old_state)

    def connect(self, engine):
        """Connect a QRunEngine object"""
        # Connect all the control signals to the engine slots
        # self.state_widgets['start'].clicked.connect(engine.start)
        # self.state_widgets['pause'].clicked.connect(engine.request_pause)
        # self.state_widgets['resume'].clicked.connect(engine.resume)
        # self.state_widgets['halt'].clicked.connect(engine.halt)
        # self.state_widgets['stop'].clicked.connect(engine.stop)

        self.state_widgets['start'].clicked.connect(self.on_start_clicked)
        self.state_widgets['pause'].clicked.connect(self.on_pause_clicked)
        self.state_widgets['resume'].clicked.connect(self.on_resume_clicked)
        self.state_widgets['halt'].clicked.connect(self.on_halt_clicked)
        self.state_widgets['stop'].clicked.connect(self.on_stop_clicked)

        #self.state_widgets['paused'].activated['QString'].connect(engine.command)
        # Update our control widgets based on this engine
        engine.state_changed.connect(self.on_state_change)
        # Set the current widget correctly
        self.on_state_change(engine.state, None)

    def on_start_clicked(self):
        self.engine.start()

    def on_pause_clicked(self):
        self.engine.pause()

    def on_resume_clicked(self):
        self.engine.resume()

    def on_halt_clicked(self):
        self.engine.halt()

    def on_stop_clicked(self):
        #if(not self._cur_state[0].find('idle')):
        print('on_stop_clicked: ', self._cur_state)
        uids = self.engine.stop()
        #self.engine.exec_result.emit(uids)



class EngineWidget(QGroupBox):
    """
    RunEngine Control Widget
    Parameters
    ----------
    engine : RunEngine, optional
        The underlying RunEngine object. A basic version wil be instatiated if
        one is not provided
    plan_creator : callable, optional
        A callable  that takes no parameters and returns a generator. If the
        plan is meant to be called repeatedly the function should make sure
        that a refreshed generator is returned each time
    """
    def __init__(self, engine=None, plan_creator=None, parent=None):
        # Instantiate widget information and layout
        super().__init__('Engine Control', parent=parent)
        # Create a new RunEngine if we were not provided one
        self._engine = None
        self.control = None
        self.engine = engine or QRunEngine()

        self.setStyleSheet('QLabel {qproperty-alignment: AlignCenter}')
        self.label = EngineLabel(parent=self)
        self.command_label = QLabel('Available Commands')
        self.status_label = QLabel('Engine Status')



        lay = QVBoxLayout()
        lay.addWidget(self.status_label)
        lay.addWidget(self.label)
        lay.addWidget(self.command_label)
        lay.addWidget(self.control)
        self.setLayout(lay)

        #self.db = Broker.named('temp')
        self.db = Broker.named('mongo_databroker')
        #self.db = Broker.named('my_databroker')
        #list_configs()
        # Insert all metadata/data captured into db.
        self.engine.subscribe(self.db.insert)

        self.sd = SupplementalData()
        self.engine.preprocessors.append(self.sd)
        #install a metadata validator
        #self.engine.md_validator = self.ensure_sample_number


        if plan_creator:
            self.engine.plan_creator = plan_creator

    # def ensure_sample_number(self, md):
    #     '''
    #     a scan metadata validator function to make sure required info is in the md dict
    #     :param md:
    #     :return:
    #     '''
    #     if 'sample_number' not in md:
    #         raise ValueError("You forgot the sample number.")

    @property
    def engine(self):
        """
        Underlying QRunEngine object
        """
        return self._engine

    @engine.setter
    def engine(self, engine):
        _logger.debug("Storing a new RunEngine object")
        # Do not allow engine to be swapped while RunEngine is active
        if self._engine and self._engine.state != 'idle':
            raise RuntimeError("Can not change the RunEngine while the "
                               "RunEngine is running!")
        self.control = EngineControl(engine=engine)
        # Connect signals
        self._engine = engine
        #self.label.connect(self._engine)
        self.control.connect(self._engine)

    def subscribe_cb(self, func, filter='all'):
        '''
        subscribe a function to the engine on a particular filter
        :param func:
        :param filter:
        :return:
        '''
        _id = self.engine.subscribe(func)
        return(_id)

    def unsubscribe_cb(self, _id):
        '''
        unsubscribe a function with cb id _id
        :param _id:
        :return:
        '''
        self.engine.unsubscribe(_id)

    def assign_baseline_devs(self, devs):
        if(type(devs) is list):
            self.sd.baseline = devs
        else:
            print('assign_baseline_devs: arg devs must be a list')



