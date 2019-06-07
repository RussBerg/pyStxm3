
from PyQt5 import QtCore
from collections import deque
from bluesky.callbacks.core import CallbackBase, get_obj_fields
from cls.plotWidgets.utils import *

class MyCollectThenCompute(CallbackBase):

    def __init__(self):
        self._start_doc = None
        self._stop_doc = None
        self._events = deque()
        self._descriptors = deque()

    def start(self, doc):
        print('MyCollectThenCompute: start')
        self._start_doc = doc
        super().start(doc)

    def descriptor(self, doc):
        print('MyCollectThenCompute: descriptor')
        self._descriptors.append(doc)
        super().descriptor(doc)

    def event(self, doc):
        print('MyCollectThenCompute: event: ')
        self._events.append(doc)
        super().event(doc)

    def stop(self, doc):
        print('MyCollectThenCompute: stop')
        self._stop_doc = doc
        self.compute()
        super().stop(doc)

    def reset(self):
        print('MyCollectThenCompute: reset')
        self._start_doc = None
        self._stop_doc = None
        self._events.clear()
        self._descriptors.clear()

    def compute(self):
        print('MyCollectThenCompute Compute!!!!:')
        #raise NotImplementedError("This method must be defined by a subclass.")


class QtDataEmitter(CallbackBase, QtCore.QObject):
    new_data = QtCore.pyqtSignal(object)
    final_data = QtCore.pyqtSignal(object)
    new_plot_data = QtCore.pyqtSignal(object) # emits a standard plotter dict
    def __init__(self, epoch='run', **kwargs):
        super(QtDataEmitter, self).__init__(None)
        self._plot_dct = make_counter_to_plotter_com_dct


class BaseQtSpectraDataEmitter(QtDataEmitter):

    def __init__(self, y, x=None, epoch='run', **kwargs):
        super(BaseQtSpectraDataEmitter, self).__init__(None)
        self._start_doc = None
        self._stop_doc = None
        self._events = deque()
        self._descriptors = deque()

        if x is not None:
            self.x, *others = get_obj_fields([x])
        else:
            self.x = 'seq_num'

        self.y, *others = get_obj_fields([y])
        self._epoch_offset = None  # used if x == 'time'
        self._epoch = epoch

    def start(self, doc):
        # print('MyDataEmitter: start')
        self.x_data, self.y_data = [], []
        self._start_doc = doc
        super().start(doc)

    def descriptor(self, doc):
        # print('MyDataEmitter: descriptor')
        self._descriptors.append(doc)
        super().descriptor(doc)

    def event(self, doc):
        print('MyDataEmitter: event: ')
        self._events.append(doc)
        super().event(doc)

    def update_caches(self, x, y):
        self.y_data.append(y)
        self.x_data.append(x)

    def stop(self, doc):
        # print('MyDataEmitter: stop')
        self._stop_doc = doc
        super().stop(doc)

    def reset(self):
        # print('MyDataEmitter: reset')
        self._start_doc = None
        self._stop_doc = None
        self._events.clear()
        self._descriptors.clear()

class BaseQtImageDataEmitter(QtDataEmitter):

    def __init__(self, cntr, y=None, x=None, epoch='run', **kwargs):
        super(BaseQtImageDataEmitter, self).__init__(None)
        self._start_doc = None
        self._stop_doc = None
        self._events = deque()
        self._descriptors = deque()
        self._scan_type = None
        if ('scan_type' in kwargs.keys()):
            self._scan_type = kwargs['scan_type']

        if x is not None:
            self.x, *others = get_obj_fields([x])
        else:
            self.x = 'seq_num'

        if y is not None:
            self.y, *others = get_obj_fields([y])
        else:
            self.y = 'seq_num'

        self._epoch_offset = None  # used if x == 'time'
        self._epoch = epoch

    def start(self, doc):
        # print('MyDataEmitter: start')
        self.x_data, self.y_data = [], []
        self._start_doc = doc
        super().start(doc)

    def descriptor(self, doc):
        # print('MyDataEmitter: descriptor')
        self._descriptors.append(doc)
        super().descriptor(doc)

    def event(self, doc):
        #print('BaseQtImageDataEmitter: event: ')
        self._events.append(doc)
        super().event(doc)

    def update_caches(self, x, y):
        self.y_data.append(y)
        self.x_data.append(x)

    def stop(self, doc):
        # print('MyDataEmitter: stop')
        self._stop_doc = doc
        super().stop(doc)

    def reset(self):
        # print('MyDataEmitter: reset')
        self._start_doc = None
        self._stop_doc = None
        self._events.clear()
        self._descriptors.clear()


class SpecDataEmitter(BaseQtSpectraDataEmitter):

    def __init__(self, y, x=None, epoch='run', **kwargs):
        super(SpecDataEmitter, self).__init__(y, x=x, epoch=epoch, **kwargs)

    def event(self, doc):
        """Unpack data from the event and call self.update().
        {'descriptor': '4731a9d3-caf4-4e55-b26d-2d01b82accd9',
         'time': 1546888660.8272438,
         'data': {'det1': 5.0,
          'det2': 1.764993805169191,
          'mtr_x': -500.0,
          'mtr_x_user_setpoint': -500.0},
         'timestamps': {'det1': 1546888660.7001529,
          'det2': 1546888660.7001529,
          'mtr_x': 1546884667.758824,
          'mtr_x_user_setpoint': 1546888660.21448},
         'seq_num': 1,
         'uid': 'b389da0f-540f-427e-89bf-bd7c501ee717',
         'filled': {}}
        """
        # This outer try/except block is needed because multiple event
        # streams will be emitted by the RunEngine and not all event
        # streams will have the keys we want.
        #print('SpecDataEmitter: event: ')
        try:
            # This inner try/except block handles seq_num and time, which could
            # be keys in the data or accessing the standard entries in every
            # event.
            try:
                #dct = dict(doc)
                # print(doc['data'].keys())
                new_x = doc['data'][self.x]
            except KeyError:
                # print('SpecDataEmitter: KeyError: ')
                if self.x in ('time', 'seq_num'):
                    new_x = doc[self.x]
                else:
                    raise
            new_y = doc['data'][self.y]
        except KeyError:
            # wrong event stream, skip it
            # print('SpecDataEmitter: KeyError: ')
            return

        # Special-case 'time' to plot against against experiment epoch, not
        # UNIX epoch.
        if self.x == 'time' and self._epoch == 'run':
            new_x -= self._epoch_offset

        self.update_caches(new_x, new_y)
        print('SpecDataEmitter: emit x=%f y=%f' % (new_x, new_y))
        # self.new_data.emit(dct)
        self.new_data.emit((new_x, new_y))
        self._plot_dct[CNTR2PLOT_ROW] = 0
        self._plot_dct[CNTR2PLOT_COL] = int(new_x)
        self._plot_dct[CNTR2PLOT_VAL] = int(new_y)
        self._plot_dct[CNTR2PLOT_SCAN_TYPE] = self._scan_type
        self.new_plot_data.emit(self._plot_dct)

        # self.update_plot()
        super().event(doc)

    def update_caches(self, x, y):
        self.y_data.append(y)
        self.x_data.append(x)


class LineDataEmitter(BaseQtSpectraDataEmitter):

    def __init__(self, y, x=None, epoch='run', **kwargs):
        super(LineDataEmitter, self).__init__(y, x=x, epoch=epoch, **kwargs)

    def event(self, doc):
        """Unpack data from the event and call self.update().
        {'descriptor': '4731a9d3-caf4-4e55-b26d-2d01b82accd9',
         'time': 1546888660.8272438,
         'data': {'det1': 5.0,
          'det2': 1.764993805169191,
          'mtr_x': -500.0,
          'mtr_x_user_setpoint': -500.0},
         'timestamps': {'det1': 1546888660.7001529,
          'det2': 1546888660.7001529,
          'mtr_x': 1546884667.758824,
          'mtr_x_user_setpoint': 1546888660.21448},
         'seq_num': 1,
         'uid': 'b389da0f-540f-427e-89bf-bd7c501ee717',
         'filled': {}}
        """
        # This outer try/except block is needed because multiple event
        # streams will be emitted by the RunEngine and not all event
        # streams will have the keys we want.
        print('LineDataEmitter: event: ', doc)
        #
        # try:
        #     # This inner try/except block handles seq_num and time, which could
        #     # be keys in the data or accessing the standard entries in every
        #     # event.
        #     try:
        #         #dct = dict(doc)
        #         # print(doc['data'].keys())
        #         new_x = doc['data'][self.x]
        #     except KeyError:
        #         # print('SpecDataEmitter: KeyError: ')
        #         if self.x in ('time', 'seq_num'):
        #             new_x = doc[self.x]
        #         else:
        #             raise
        #     new_y = doc['data'][self.y]
        # except KeyError:
        #     # wrong event stream, skip it
        #     # print('SpecDataEmitter: KeyError: ')
        #     return
        #
        # # Special-case 'time' to plot against against experiment epoch, not
        # # UNIX epoch.
        # if self.x == 'time' and self._epoch == 'run':
        #     new_x -= self._epoch_offset
        #
        # self.update_caches(new_x, new_y)
        # print('SpecDataEmitter: emit x=%f y=%f' % (new_x, new_y))
        # # self.new_data.emit(dct)
        # self.new_data.emit((new_x, new_y))
        # # self.update_plot()
        super().event(doc)

    def update_caches(self, x, y):
        self.y_data.append(y)
        self.x_data.append(x)

#######################################################################################
class ImageDataEmitter(BaseQtImageDataEmitter):

    def __init__(self, det, y=None, x=None, epoch='run', **kwargs):
        super(ImageDataEmitter, self).__init__(det, y=y, x=x, epoch=epoch, **kwargs)
        self.det = det
        self.det_data = []
        self.rows = 0
        self.cols = 0
        self.x_idx = 0
        self.y_idx = 0
        self.factor_list = []

    def update_idxs(self, seq_num):
        '''
        The doc only contains a single sequence number so generate row column indexs
        :param seq_num:
        :return:
        '''
        if(seq_num in self.factor_list):
            #increment y
            self.y_idx += 1
            #reset x
            self.x_idx = 0
        else:
            # increment x
            if(seq_num is not 1):
                self.x_idx += 1

    def gen_factor_list(self, cols):
        l = [item for item in range(1, cols)]
        l2 = [(item * cols) + 1 for item in l]
        self.factor_list = l2

    def set_row_col(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.gen_factor_list(cols)

    def start(self, doc):
        # print('ImageDataEmitter: start')
        self.x_data, self.y_data , self.det_data = [], [], []
        self.x_idx = 0
        self.y_idx = 0
        self._start_doc = doc
        super().start(doc)

    def event(self, doc):
        """Unpack data from the event and call self.update().
        {{'descriptor': '9828f23d-59a1-4718-8323-562efe5b2cd9',
         'time': 1546964684.413204,
         'data': {'noisy_det': 0.9540284356575173,
          'det2': 1.764993805169191,
          'mtr_x': -5000.0,
          'mtr_x_user_setpoint': -5000.0,
          'mtr_y': -2684.2110000000002,
          'mtr_y_user_setpoint': -2684.2105263157896},
         'timestamps': {'noisy_det': 1546964684.3331559,
          'det2': 1546964684.343136,
          'mtr_x': 1546964622.432808,
          'mtr_x_user_setpoint': 1546964643.604022,
          'mtr_y': 1546964683.990624,
          'mtr_y_user_setpoint': 1546964683.990624},
         'seq_num': 2,
         'uid': '8b40c205-30d3-4c6f-808b-e88a86ca2ec9',
         'filled': {}}
        """
        # This outer try/except block is needed because multiple event
        # streams will be emitted by the RunEngine and not all event
        # streams will have the keys we want.        new_det = None
        new_x = None
        new_y = None
        try:
            # This inner try/except block handles seq_num and time, which could
            # be keys in the data or accessing the standard entries in every
            # event.
            try:
                print(doc)
                #dct = dict(doc)
                seq_num = doc['seq_num']
                self.update_idxs(seq_num)
                # print(doc['data'].keys())
                new_det = doc['data'][self.det]
                new_x = self.x_idx
                new_y = self.y_idx
                print('ImageDataEmitter: event: [%d] [%d, %d]' % (seq_num, self.x_idx, self.y_idx))
            except KeyError:
                print('ImageDataEmitter: KeyError: ')
                if self.x in ('time', 'seq_num'):
                    new_x = doc[self.x]
                else:
                    raise
            #new_y = doc['data'][self.y]
        except KeyError:
            # wrong event stream, skip it
            print('ImageDataEmitter: KeyError: ')
            return


        # Special-case 'time' to plot against against experiment epoch, not
        # UNIX epoch.
        if self.x == 'time' and self._epoch == 'run':
            new_x -= self._epoch_offset

        if(None not in [new_x, new_y, new_det]):
            self.update_caches(new_x, new_y, new_det)
            # print('ImageDataEmitter: emit x=%f y=%f' % (new_x, new_y))
            # self.new_data.emit(dct)
            self.new_data.emit((new_x, new_y, new_det))
            self._plot_dct[CNTR2PLOT_ROW] = int(new_y)
            self._plot_dct[CNTR2PLOT_COL] = int(new_x)
            self._plot_dct[CNTR2PLOT_VAL] = int(new_det)
            self._plot_dct[CNTR2PLOT_SCAN_TYPE] = self._scan_type
            self.new_plot_data.emit(self._plot_dct)
            # self.update_plot()
        super().event(doc)

    def update_caches(self, x, y, det):
        self.y_data.append(y)
        self.x_data.append(x)
        self.det_data.append(det)

    def stop(self, doc):
        print('ImageDataEmitter: stop')
        self._stop_doc = doc
        self.emit_data()
        super().stop(doc)

    def emit_data(self):
        dct = {}
        dct['x_data'] = self.x_data
        dct['y_data'] = self.y_data
        dct['det_data'] = self.det_data
        self.final_data.emit(dct)
        print('emitting data')



