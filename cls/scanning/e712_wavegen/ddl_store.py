import os
from PyQt5 import QtCore, QtWidgets
import time
import copy
import h5py

from cls.utils.log import get_module_logger
from cls.scanning.nexus.cls_nx_api import _dataset, _string_attr

ddl_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ddl_data')

_logger = get_module_logger(__name__)

# def gen_ddl_table_key(tune_dct):
#     '''
#     dct = {}
#         dct['dwell'] = float(self.dwellFld.text())
#         dct['max_rcv_bytes'] = float(self.maxRcvBytesFld.text())
#         dct['max_sock_timeout'] = float(self.maxSockTimeoutFld.text())
#         dct['line_accrange'] = float(self.lineAccRangeFld.text())
#         dct['line_step_time'] = float(self.lineStepTimeFld.text())
#         dct['line_updown_time'] = float(self.lineUpDownTimeFld.text())
#         dct['line_return_time'] = float(self.returnTimeFld.text())
#         dct['pnt_step_time'] = float(self.pntStepTimeFld.text())
#         dct['pnt_updown_time'] = float(self.pntUpDownTimeFld.text())
#
#
#         dct['mode'] = int(self.modeComboBox.currentIndex())
#         dct['numX'] = int(self.xnpointsFld.text())
#         dct['numY'] = int(self.ynpointsFld.text())
#         dct['startX'] = float(self.xstartFld.text())
#         dct['stopX'] = float(self.xstopFld.text())
#         dct['startY'] = float(self.ystartFld.text())
#         dct['stopY'] = float(self.ystopFld.text())
#
#     :param dct:
#     :return:
#     '''
#     s = 'DW:%.4f' % tune_dct['dwell']
#     s += 'AR:%.4f' % tune_dct['line_accrange']
#     s += 'LS:%.4f' % tune_dct['line_step_time']
#     s += 'LU:%.4f' % tune_dct['line_updown_time']
#     s += 'PS:%.4f' % tune_dct['pnt_step_time']
#     s += 'PU:%.4f' % tune_dct['pnt_updown_time']
#     s += 'X:%.4f' % tune_dct['startX']
#     s += 'SX:%.4f' % tune_dct['stopX']
#     s += 'Y:%.4f' % tune_dct['startY']
#     s += 'SY:%.4f' % tune_dct['stopY']
#     s += 'NX:%d' % tune_dct['numX']
#     s += 'NY:%d' % tune_dct['numY']
#
#     return(s)

def gen_ddl_database_key(tune_dct):
    '''
    take a dict of parameters that were used for a particular scan and gnerate a key that is used 
    to store the DDL table for that scan in the ddl_database.hdf5 file.
    
    It creates a long string, who cares, its human readable and its really on the software that uses it 
    so use this solution for now
    
    dct = {}
        dct['dwell'] = float(self.dwellFld.text())
        dct['max_rcv_bytes'] = float(self.maxRcvBytesFld.text())
        dct['max_sock_timeout'] = float(self.maxSockTimeoutFld.text())
        dct['line_accrange'] = float(self.lineAccRangeFld.text())
        dct['line_step_time'] = float(self.lineStepTimeFld.text())
        dct['line_updown_time'] = float(self.lineUpDownTimeFld.text())
        dct['line_return_time'] = float(self.returnTimeFld.text())
        dct['pnt_step_time'] = float(self.pntStepTimeFld.text())
        dct['pnt_updown_time'] = float(self.pntUpDownTimeFld.text())


        dct['mode'] = int(self.modeComboBox.currentIndex())
        dct['numX'] = int(self.xnpointsFld.text())
        dct['numY'] = int(self.ynpointsFld.text())
        dct['startX'] = float(self.xstartFld.text())
        dct['stopX'] = float(self.xstopFld.text())
        dct['startY'] = float(self.ystartFld.text())
        dct['stopY'] = float(self.ystopFld.text())
        
        dct['DigFltBWidth'] = self.get('DigFltBWidth_RBV')
        dct['DigFltParm1'] = self.get('DigFltParm1_RBV')
        dct['DigFltParm2'] = self.get('DigFltParm2_RBV')
        dct['DigFltParm3'] = self.get('DigFltParm3_RBV')
        dct['DigFltParm4'] = self.get('DigFltParm4_RBV')
        dct['DigFltParm5'] = self.get('DigFltParm5_RBV')
        dct['CapSensBParm'] = self.get('CapSensBParm_RBV')
        dct['CapSensMParm'] = self.get('CapSensMParm_RBV')
        dct['PTerm'] = self.get('PTerm_RBV')
        dct['ITerm'] = self.get('ITerm_RBV')
        dct['DTerm'] = self.get('DTerm_RBV')
        dct['SlewRate'] = self.get('SlewRate_RBV')
        dct['NotchFreq1'] = self.get('NotchFreq1_RBV')
        dct['NotchFreq2'] = self.get('NotchFreq2_RBV')
        dct['NotchReject1'] = self.get('NotchReject1_RBV')
        dct['NotchReject2'] = self.get('NotchReject2_RBV')
        dct['NotchBW1'] = self.get('NotchBW1_RBV')
        dct['NotchBW2'] = self.get('NotchBW2_RBV')

    :param dct: 
    :return: 
    '''
    s = 'DW:%.4f' % tune_dct['dwell']
    s += 'RX:%.4f' % abs(tune_dct['stopX'] - tune_dct['startX'])
    #s += 'RY:%.4f' % abs(tune_dct['stopY'] - tune_dct['startY'])
    s += 'NX:%d' % tune_dct['numX']
    # s += 'NY:%d' % tune_dct['numY']

    s += 'AR:%.4f' % tune_dct['line_accrange']
    s += 'LS:%.4f' % tune_dct['line_step_time']
    s += 'LU:%.4f' % tune_dct['line_updown_time']
    s += 'PS:%.4f' % tune_dct['pnt_step_time']
    s += 'PU:%.4f' % tune_dct['pnt_updown_time']
    s += 'PT:%.4f' % tune_dct['PTerm']
    s += 'IT:%.4f' % tune_dct['ITerm']
    s += 'DT:%.4f' % tune_dct['DTerm']
    s += 'NF1:%.4f' % tune_dct['NotchFreq1']
    s += 'NR1:%.4f' % tune_dct['NotchReject1']
    s += 'NBW1:%.4f' % tune_dct['NotchBW1']
    s += 'NF2:%.4f' % tune_dct['NotchFreq2']
    s += 'NR2:%.4f' % tune_dct['NotchReject2']
    s += 'NBW2:%.4f' % tune_dct['NotchBW2']
    s += 'SR:%.4f' % tune_dct['SlewRate']
    s += 'DFBW:%d' % tune_dct['DigFltBWidth']

    return (s)




class DDL_Store(QtCore.QObject):

    changed = QtCore.pyqtSignal(object)


    def __init__(self, fname=None, dataDir=ddl_data_dir):
        super(DDL_Store, self).__init__()
        if(fname is None):
            fname = 'ddl_data.hdf5'
        self.filepath = os.path.join(dataDir, fname)
        if(not os.path.exists(self.filepath)):
            #create it
            nf = h5py.File(self.filepath, 'a')
            nf.close()

        #self.open_ddl_database(self.filepath)



    def close_database(self):
        self.ddl_db.flush()
        self.ddl_db.close()

    def key_exists(self, key):
        '''
        check to see if the key aready exists in database
        :param key: 
        :return: True is key exists, False if it doesn't 
        '''
        if(self.open_ddl_database(self.filepath)):
            keys = list(self.ddl_db.keys())
            self.close_database()
            for k in keys:
                if(k == key):
                    return(True)

        #there is no match
        return(False)

    def get_ddl_table(self, key):
        '''
        find if the key exists in the ddl database, if so return the ddl table
        
        :param key: 
        :return: 
        '''
        data = {}
        self.open_ddl_database(self.filepath)
        if(key in list(self.ddl_db.keys())):
            data = copy.copy(self.ddl_db[key][()])
            _logger.info('Retrieved DDL table')
            _logger.info('DDL KEY [%s]' % key)
        self.close_database()
        return(data)


    def save_ddl_table(self, key, ddl_data, dct):
        '''
        if the key exists in the ddl database then overwrite this ddl table
         otherwise create a new entry
         
        :param key: 
        :return: 
        '''
        if(self.open_ddl_database(self.filepath)):
            if(key in list(self.ddl_db.keys())):
                del self.ddl_db[key]
            dset_grp = _dataset(self.ddl_db, key, ddl_data, 'NX_FLOAT')
            self.add_param_detail_str_attrs(dset_grp, dct)
            _logger.info('Saved DDL table for this scan')
            _logger.info('using key [%s]' % key)

        self.close_database()


    def add_param_detail_str_attrs(self, dset_grp, dct):
        _string_attr(dset_grp, 'dwell', dct['dwell'])
        _string_attr(dset_grp, 'rangeX', abs(dct['stopX'] - dct['startX']))
        _string_attr(dset_grp, 'numX', dct['numX'])
        _string_attr(dset_grp, 'elapsed_tstr', dct['elapsed_tstr'])
        _string_attr(dset_grp, 'estimated_tstr', dct['estimated_tstr'])
        #_string_attr(dset_grp, 'line_accrange', dct['line_accrange'])
        #_string_attr(dset_grp, 'line_step_time', dct['line_step_time'])
        #_string_attr(dset_grp, 'line_updown_time', dct['line_updown_time'])
        #_string_attr(dset_grp, 'line_return_time', dct['line_return_time'])
        #_string_attr(dset_grp, 'pnt_step_time', dct['pnt_step_time'])
        #_string_attr(dset_grp, 'pnt_updown_time', dct['pnt_updown_time'])
        _string_attr(dset_grp, 'PTerm', dct['PTerm'])
        _string_attr(dset_grp, 'ITerm', dct['ITerm'])
        _string_attr(dset_grp, 'DTerm', dct['DTerm'])
        _string_attr(dset_grp, 'NotchFreq1', dct['NotchFreq1'])
        _string_attr(dset_grp, 'NotchReject1', dct['NotchReject1'])
        _string_attr(dset_grp, 'NotchBW1', dct['NotchBW1'])
        _string_attr(dset_grp, 'NotchFreq2', dct['NotchFreq2'])
        _string_attr(dset_grp, 'NotchReject2', dct['NotchReject2'])
        _string_attr(dset_grp, 'NotchBW2', dct['NotchBW2'])
        _string_attr(dset_grp, 'SlewRate', dct['SlewRate'])
        _string_attr(dset_grp, 'DigFltBWidth', dct['DigFltBWidth'])
        _string_attr(dset_grp, 'TimeStamp', time.strftime("%Y-%m-%d, %H:%M:%S"))



    def open_ddl_database(self, filepath):
        '''
        open ddl database file from disk,
        h5py flags:
            r	Readonly, file must exist
            r+	Read/write, file must exist
            w	Create file, truncate if exists
            w- or x	Create file, fail if exists
            a	Read/write if exists, create otherwise (default)
        :return: 
        '''

        self.ddl_db = h5py.File(filepath, 'a')
        #self.ddl_db.swmr_mode = True
        if (self.ddl_db is None):
            _logger.error('error opening ddl database file [%s]' % filepath)
            return(False)
        return(True)








