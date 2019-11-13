#!python3 
from PyQt5 import QtWidgets

import numpy as np
from guiqwt.builder import make

from cls_bsky.plotters.zmq_curveWidget import *
from cls_bsky.doc_utils import dump_args, get_detectors, get_positioners, get_num_points, get_datakeys, get_det_shape_from_md

class tst_window(QtWidgets.QWidget):

    def __init__(self, isolate_curve_nm=None):
        super(tst_window, self).__init__()
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self.md = {}
        self.isolate_curve_nm = isolate_curve_nm

        if(self.isolate_curve_nm is not None):
            self.isolate_curve = True
        else:
            self.isolate_curve = False

        self.curve_names = []

        # gridparam = make.gridparam(background="#000000",
        #                             minor_enabled=(False, False),
        #                             major_enabled=(True, True),
        #                             major_style=('DotLine', '#565656', 1.0),
        #                             minor_style=('DotLine', '#6b6b6b', 0.5))
        # # options = dict(
        #     xlabel=("um", ""),
        #     ylabel=("um", ""),
        #     gridparam=gridparam )

        self.plot = ZMQCurveViewerWidget(toolbar=True)#, options=options)
        self.plot.add_legend("TL")
        #self.plot.plot_widget.itemlist.setVisible(True)
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.plot)
        self.setLayout(vbox)
        self._data_valid = True
        self._xdata = None

    def is_valid_single_point_det(self, det_name):
        if('dev_parms' in self.md.keys()):
            data_dim = len(get_det_shape_from_md(self.md, det_name))
            if (data_dim < 1):
                return(True)
            else:
                return(False)
        return(False)

    def get_data_points(self, doc, datakeys=[]):
        data = {}
        seq_num = doc['seq_num']
        data[seq_num] = []
        if(self.isolate_curve and (self.isolate_curve_nm in datakeys)):
            k = self.isolate_curve_nm
            data[seq_num].append(
                {'det_name': k.replace('_val', ''), 'value': doc['data'][k], 'timestamp': doc['timestamps'][k]})
            return(data)
        else:
            for det in datakeys:
                # print('get_data_points: [%s]' % k)
                if(self.is_valid_single_point_det(det)):
                    data[seq_num].append({'det_name': det.replace('_val',''), 'value': doc['data'][det], 'timestamp': doc['timestamps'][det]})
            return (data)

    def closeEvent(self, ao):
        exit()

    def determine_data_type(self):
        '''
        is it a point or a line?
        :return:
        '''
        data_type = 'point'
        if (self.isolate_curve and (self.isolate_curve_nm in self.curve_names)):
            if ('det_parms' in self.md.keys()):
                data_dim = len(get_det_shape_from_md(self.md, self.isolate_curve_nm))
                if (data_dim < 1):
                    data_type = 'point'
                else:
                    data_type = 'line'
        return(data_type)

    def create_xdata(self, doc):
        if('num' in doc['plan_pattern_args'].keys()):
            npoints = doc['plan_pattern_args']['num']
            start = doc['plan_pattern_args']['args'][1]
            stop = doc['plan_pattern_args']['args'][2]
        else:
            npoints = len(doc['plan_pattern_args']['object'])
            start = doc['plan_pattern_args']['object'][1]
            stop = doc['plan_pattern_args']['object'][-1]
        self._xdata = np.linspace(start, stop, npoints)

    def create_specs(self, doc):
        remove_lst = []
        #self.curve_names = doc['detectors']
        self.curve_names = list(doc['detectors']) + list(doc['motors'])
        if(self.isolate_curve and (self.isolate_curve_nm in self.curve_names)):
            self.setWindowTitle(self.isolate_curve_nm)
            data_type = self.determine_data_type()
            self.plot.clear_plot()
            clr = get_next_color(use_dflt=True)
            style = get_basic_line_style(clr)
            self.plot.create_curve('%s' % self.isolate_curve_nm, curve_style=style)
        else:
            self.plot.clear_plot()
            for det in self.curve_names:
                if(self.is_valid_single_point_det(det)):
                    clr = get_next_color(use_dflt=False)
                    style = get_basic_line_style(clr, marker='Diamond', width=2.0, alpha=1.0)
                    # style = get_histogram_style(clr)
                    #print('create_specs: creating curve [%s]' % det)
                    self.plot.create_curve('%s' % det, curve_style=style)
                else:
                    remove_lst.append(det)

        self.create_xdata(doc)
        #remove detectors that are delivering invalid data
        for rem_det in remove_lst:
            self.curve_names.remove(rem_det)

    def add_to_spec(self, data_dct):
        '''
        data_dct =
            {1: [{'noisy_det': 0.9855252608504612, 'timestamp': 1569433874.0520704}, {'m902': 125.0, 'timestamp': 1569433919.689106}, {'m902_user_setpoint': 125.0, 'timestamp': 1569433919.689106}]}
            ...
        :param data_dct:
        :return:
        '''

        seq_num = list(data_dct.keys())[0]
        for _dct in data_dct[seq_num]:
            if(_dct['det_name'] in self.curve_names):
                
                if((type(_dct['value']) == float) or (type(_dct['value']) == int)):
                    self.plot.addXYPoint('%s' % _dct['det_name'], self._xdata[seq_num - 1], _dct['value'], update=True)

                elif (type(_dct['value']) == list):
                    if (self.isolate_curve and (self.isolate_curve_nm in self.curve_names)):
                        #only plot a line if it was asked for as an isolated curve, otherwise ignore
                        xdata = np.arange(0, len(_dct['value']))
                        self.plot.setXYData('%s' % _dct['det_name'], xdata, _dct['value'], update=True)

                else:
                    print('add_to_spec: ERROR: unknown _dct[value] type')

    def is_valid_data(self, doc):
        res = False
        valid_plan_types_list = ['list_scan', 'scan']
        if(doc['plan_name'] in valid_plan_types_list):
            return(True)
        else:
            return(False)

    def mycallback(self, *args, **dud):
        '''
        received this: ('start', {'uid': 'eb46291b-7c50-494d-bd26-4947d9320f87', 'time': 1569424382.0135844, 'scan_id': 4, 'plan_type': 'generator', 'plan_name': 'list_scan', 'detectors': ['noisy_det'], 'motors': ['m902'], 'num_points': 13, 'num_intervals': 12, 'plan_args': {'detectors': ["SynGauss(name='noisy_det', value=0.9431069812519803, timestamp=1569424245.2773852)"], 'motor': "EpicsMotor(prefix='IOC:m902', name='m902', settle_time=0.0, timeout=None, read_attrs=['user_readback', 'user_setpoint'], configuration_attrs=['user_offset', 'user_offset_dir', 'velocity', 'acceleration', 'motor_egu'])", 'steps': [-512, -300, -200, -100, -50, -48, -45, -30, -20, -10, 0, 250, 500], 'per_step': 'None'}, 'plan_pattern': 'array', 'plan_pattern_module': 'numpy', 'plan_pattern_args': {'object': [-512, -300, -200, -100, -50, -48, -45, -30, -20, -10, 0, 250, 500]}, 'hints': {'dimensions': [(['m902'], 'primary')]}}) {}
        received this: ('descriptor', {'run_start': 'eb46291b-7c50-494d-bd26-4947d9320f87', 'time': 1569424382.6910648, 'data_keys': {'noisy_det': {'source': 'SIM:noisy_det', 'dtype': 'number', 'shape': [], 'precision': 3, 'object_name': 'noisy_det'}, 'm902': {'source': 'PV:IOC:m902.RBV', 'dtype': 'number', 'shape': [], 'units': 'um', 'lower_ctrl_limit': -7000.0, 'upper_ctrl_limit': 7000.0, 'precision': 5, 'object_name': 'm902'}, 'm902_user_setpoint': {'source': 'PV:IOC:m902.VAL', 'dtype': 'number', 'shape': [], 'units': 'um', 'lower_ctrl_limit': -7000.0, 'upper_ctrl_limit': 7000.0, 'precision': 5, 'object_name': 'm902'}}, 'uid': 'ca7e6f20-b289-40bb-bcec-9db5a7782c6e', 'configuration': {'noisy_det': {'data': {'noisy_det': 0.9815140304117752}, 'timestamps': {'noisy_det': 1569424382.678056}, 'data_keys': {'noisy_det': {'source': 'SIM:noisy_det', 'dtype': 'number', 'shape': [], 'precision': 3}}}, 'm902': {'data': {'m902_user_offset': 0.0, 'm902_user_offset_dir': 0, 'm902_velocity': 10000.0, 'm902_acceleration': 1.0, 'm902_motor_egu': 'um'}, 'timestamps': {'m902_user_offset': 1569424428.277267, 'm902_user_offset_dir': 1569424428.277267, 'm902_velocity': 1569424428.277267, 'm902_acceleration': 1569424428.277267, 'm902_motor_egu': 1569424428.277267}, 'data_keys': OrderedDict([('m902_user_offset', {'source': 'PV:IOC:m902.OFF', 'dtype': 'number', 'shape': [], 'units': 'um', 'lower_ctrl_limit': -1e+300, 'upper_ctrl_limit': 1e+300, 'precision': 5}), ('m902_user_offset_dir', {'source': 'PV:IOC:m902.DIR', 'dtype': 'integer', 'shape': [], 'units': None, 'lower_ctrl_limit': None, 'upper_ctrl_limit': None, 'enum_strs': ('Pos', 'Neg')}), ('m902_velocity', {'source': 'PV:IOC:m902.VELO', 'dtype': 'number', 'shape': [], 'units': 'um/sec', 'lower_ctrl_limit': 0.0, 'upper_ctrl_limit': 0.0, 'precision': 5}), ('m902_acceleration', {'source': 'PV:IOC:m902.ACCL', 'dtype': 'number', 'shape': [], 'units': 'sec', 'lower_ctrl_limit': -1e+300, 'upper_ctrl_limit': 1e+300, 'precision': 5}), ('m902_motor_egu', {'source': 'PV:IOC:m902.EGU', 'dtype': 'string', 'shape': [], 'units': None, 'lower_ctrl_limit': None, 'upper_ctrl_limit': None})])}}, 'name': 'primary', 'hints': {'noisy_det': {'fields': []}, 'm902': {'fields': ['m902']}}, 'object_keys': {'noisy_det': ['noisy_det'], 'm902': ['m902', 'm902_user_setpoint']}}) {}
        received this: ('event', {'descriptor': 'ca7e6f20-b289-40bb-bcec-9db5a7782c6e', 'time': 1569424382.7090774, 'data': {'noisy_det': 0.9815140304117752, 'm902': -512.0, 'm902_user_setpoint': -512.0}, 'timestamps': {'noisy_det': 1569424382.678056, 'm902': 1569424428.277267, 'm902_user_setpoint': 1569424428.277267}, 'seq_num': 1, 'uid': '05163a20-4ea4-4266-84c9-501a61043ead', 'filled': {}}) {}
        received this: ('event', {'descriptor': 'ca7e6f20-b289-40bb-bcec-9db5a7782c6e', 'time': 1569424382.9802704, 'data': {'noisy_det': 0.9463840972855944, 'm902': -300.0, 'm902_user_setpoint': -300.0}, 'timestamps': {'noisy_det': 1569424382.9772694, 'm902': 1569424428.576992, 'm902_user_setpoint': 1569424428.576992}, 'seq_num': 2, 'uid': '59b3aed0-8d5f-4a9a-8c5d-8c159fee979e', 'filled': {}}) {}
        received this: ('event', {'descriptor': 'ca7e6f20-b289-40bb-bcec-9db5a7782c6e', 'time': 1569424383.2794833, 'data': {'noisy_det': 1.0769673475201391, 'm902': -200.0, 'm902_user_setpoint': -200.0}, 'timestamps': {'noisy_det': 1569424383.2764814, 'm902': 1569424428.776784, 'm902_user_setpoint': 1569424428.876704}, 'seq_num': 3, 'uid': '0f8e5d6f-e373-4774-a946-3b7d7453ff9b', 'filled': {}}) {}
        received this: ('event', {'descriptor': 'ca7e6f20-b289-40bb-bcec-9db5a7782c6e', 'time': 1569424383.579697, 'data': {'noisy_det': 1.060973625146906, 'm902': -100.0, 'm902_user_setpoint': -100.0}, 'timestamps': {'noisy_det': 1569424383.576695, 'm902': 1569424429.076514, 'm902_user_setpoint': 1569424429.176407}, 'seq_num': 4, 'uid': '4dc61aa6-1899-479d-bbd0-9a9d75ad930e', 'filled': {}}) {}
        received this: ('event', {'descriptor': 'ca7e6f20-b289-40bb-bcec-9db5a7782c6e', 'time': 1569424383.7798388, 'data': {'noisy_det': 0.9858486344504714, 'm902': -50.0, 'm902_user_setpoint': -50.0}, 'timestamps': {'noisy_det': 1569424383.776837, 'm902': 1569424429.376217, 'm902_user_setpoint': 1569424429.376217}, 'seq_num': 5, 'uid': '6085c085-fc56-429b-bcf4-aa81046da173', 'filled': {}}) {}
        received this: ('event', {'descriptor': 'ca7e6f20-b289-40bb-bcec-9db5a7782c6e', 'time': 1569424383.8799105, 'data': {'noisy_det': 0.9168681139593263, 'm902': -48.0, 'm902_user_setpoint': -48.0}, 'timestamps': {'noisy_det': 1569424383.8769078, 'm902': 1569424429.476121, 'm902_user_setpoint': 1569424429.476121}, 'seq_num': 6, 'uid': '70e8bf50-a1d3-4266-a2de-52e7714fff2e', 'filled': {}}) {}
        received this: ('event', {'descriptor': 'ca7e6f20-b289-40bb-bcec-9db5a7782c6e', 'time': 1569424383.9799805, 'data': {'noisy_det': 1.069075200134443, 'm902': -45.0, 'm902_user_setpoint': -45.0}, 'timestamps': {'noisy_det': 1569424383.976979, 'm902': 1569424429.57605, 'm902_user_setpoint': 1569424429.57605}, 'seq_num': 7, 'uid': '6cfd61e1-6d54-4cea-824e-a8ae02b158e0', 'filled': {}}) {}
        received this: ('event', {'descriptor': 'ca7e6f20-b289-40bb-bcec-9db5a7782c6e', 'time': 1569424384.0810533, 'data': {'noisy_det': 0.9086663639196696, 'm902': -30.0, 'm902_user_setpoint': -30.0}, 'timestamps': {'noisy_det': 1569424384.0770504, 'm902': 1569424429.675948, 'm902_user_setpoint': 1569424429.675948}, 'seq_num': 8, 'uid': '26ee38af-b070-4461-8355-8b90937a9ae2', 'filled': {}}) {}
        received this: ('event', {'descriptor': 'ca7e6f20-b289-40bb-bcec-9db5a7782c6e', 'time': 1569424384.1801229, 'data': {'noisy_det': 0.9489143782890307, 'm902': -20.0, 'm902_user_setpoint': -20.0}, 'timestamps': {'noisy_det': 1569424384.1771228, 'm902': 1569424429.775825, 'm902_user_setpoint': 1569424429.775825}, 'seq_num': 9, 'uid': '00f3ad4d-9e9f-4d76-981d-d57c892ad59b', 'filled': {}}) {}
        received this: ('event', {'descriptor': 'ca7e6f20-b289-40bb-bcec-9db5a7782c6e', 'time': 1569424384.280194, 'data': {'noisy_det': 1.0125769388856294, 'm902': -10.0, 'm902_user_setpoint': -10.0}, 'timestamps': {'noisy_det': 1569424384.2771926, 'm902': 1569424429.87587, 'm902_user_setpoint': 1569424429.87587}, 'seq_num': 10, 'uid': 'f5587b93-4e3d-4ef8-a47c-7551b18717fe', 'filled': {}}) {}
        received this: ('event', {'descriptor': 'ca7e6f20-b289-40bb-bcec-9db5a7782c6e', 'time': 1569424384.3812659, 'data': {'noisy_det': 0.9916295060115614, 'm902': 0.0, 'm902_user_setpoint': 0.0}, 'timestamps': {'noisy_det': 1569424384.3772626, 'm902': 1569424429.975952, 'm902_user_setpoint': 1569424429.975952}, 'seq_num': 11, 'uid': '7fc19a4e-a34a-409c-93ef-57a52de0c96e', 'filled': {}}) {}
        received this: ('event', {'descriptor': 'ca7e6f20-b289-40bb-bcec-9db5a7782c6e', 'time': 1569424384.7795503, 'data': {'noisy_det': 1.041231645862694, 'm902': 250.0, 'm902_user_setpoint': 250.0}, 'timestamps': {'noisy_det': 1569424384.776549, 'm902': 1569424430.376373, 'm902_user_setpoint': 1569424430.376373}, 'seq_num': 12, 'uid': '1139d7b7-6af7-46b6-abf5-d4972b8f7473', 'filled': {}}) {}
        received this: ('event', {'descriptor': 'ca7e6f20-b289-40bb-bcec-9db5a7782c6e', 'time': 1569424385.180835, 'data': {'noisy_det': 0.9300479061280126, 'm902': 500.0, 'm902_user_setpoint': 500.0}, 'timestamps': {'noisy_det': 1569424385.1778321, 'm902': 1569424430.776786, 'm902_user_setpoint': 1569424430.776786}, 'seq_num': 13, 'uid': 'a026bc0c-53dc-4bc4-ad44-d7847c865e8e', 'filled': {}}) {}
        received this: ('stop', {'run_start': 'eb46291b-7c50-494d-bd26-4947d9320f87', 'time': 1569424385.1878393, 'uid': '2b61e774-fc49-4e76-9cc7-712804ffceda', 'exit_status': 'success', 'reason': '', 'num_events': {'primary': 13}}) {}
        :param args:
        :param kwargs:
        :return:
        '''
        name, doc = args
        #print(doc)

        if (name.find('start') > -1):
            self.plot.clear_plot()
            self.md = doc['md']
            self._data_valid = True
            if(self.is_valid_data(doc)):
                self.create_specs(doc)
                self.posners = get_positioners(doc)
                npts = get_num_points(doc)
            else:
                self._data_valid = False

        # elif (name.find('descriptor') > -1):
        #
        #
        elif (name.find('event') > -1):
            if(self._data_valid):
                datakeys = get_datakeys(doc)
                data = self.get_data_points(doc, datakeys)
                #print(data)
                self.add_to_spec(data)
            else:
                #ignore invalid data
                pass


if __name__ == "__main__":
    """Test"""
    # -- Create QApplication

    import sys
    import argparse
    from PyQt5 import QtWidgets
    from bluesky.utils import install_qt_kicker
    from bluesky.callbacks.zmq import RemoteDispatcher

    parser = argparse.ArgumentParser(description='Start a Spectra plotter.')

    parser.add_argument('-c', '--curve_name', metavar='signal_name', type=str,
                        help='the name of a detector signal in data stream')
    args = parser.parse_args()

    app = QtWidgets.QApplication([])

    win = tst_window(isolate_curve_nm=args.curve_name)

    d = RemoteDispatcher('localhost:5578')
    d.subscribe(win.mycallback)
    install_qt_kicker(loop=d.loop)

    win.show()
    #starts the event loop for asnycio as well as it will call processEvents() for Qt
    d.start()
    #d.start()  # runs event loop forever
    #app.exec_()



