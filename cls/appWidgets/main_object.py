
from PyQt5 import QtCore, QtWidgets

from cls.appWidgets.splashScreen import get_splash
from cls.utils.dict_utils import dct_put, dct_get, dct_merge
from cls.utils.version import get_version
# from cls.zeromq.epics.qt5_epics_client import zmq_epicsClient
from cls.zeromq.epics.qt5_cepics_client_pubsub import qt5_zmqClientWidget, compression_types
from cls.utils.roi_dict_defs import *
from cls.utils.log import get_module_logger

from cls.types.stxmTypes import scan_types, scan_sub_types, sample_fine_positioning_modes, sample_positioning_modes


from cls.scan_engine.bluesky.qt_run_engine import EngineWidget
from bcm.devices.device_names import *

POS_TYPE_BL = 'BL'
POS_TYPE_ES = 'ES'


USE_ZMQ = False

_logger = get_module_logger(__name__)

def gen_session_obj():
    """
    this function is meant to be the one stop location that defines what teh session object will
    consist of that exists in the MAIN_OBJ
    """
    ses_obj = {}
    dct_put(ses_obj, 'AO', 500) #default AO
    dct_put(ses_obj, 'ZP', 2) #default Zoneplate selected is #2
    dct_put(ses_obj, 'FL', 0) #calculated focal length
    dct_put(ses_obj, 'DWELL', 1) #current dwell
    dct_put(ses_obj, 'SAMPLE_HLDR', 12131) #unique ID for the 6 position sample holder, maybe from a barcode? 
    dct_put(ses_obj, 'SAMPLE_POS', 1) #current sample position (1 - 6)
    return(ses_obj)


class main_object_base(QtCore.QObject):
    """
    This class represents the main object for the application where all 
    information is stored, it is designed thisway so that any module can import
    the main object and have access to its sections:
        main[APP]
                APP/STATUS
                APP/UI
                APP/USER
                
        main[SCAN]
                SCAN/CFG            all info required to recreate the scan if loaded from disk
                     CFG/TYPE        type of scan (the main scan class)
                     CFG/ROIS        list of ROI dicts used to create the scan
                SCAN/DATA
                     DATA/CHANNELS  list of channel(s) counter data
                     DATA/POINTS    2d np array of points for the current being acquired
                     DATA/SSCAN        list of sscan classes used in this scan
                     DATA/DEVICES    dict of devices found in devices and their feedback values at the time of the scan
    
    """
    changed = QtCore.pyqtSignal()
    
    def __init__(self, name, endstation, beamline_id=None, splash=None):
        
        super(main_object_base, self).__init__()
        
        self.beamline = name
        self.endstation = endstation
        self.beamline_id = beamline_id
        self.main_obj = {}
        self.endstation_prefix = 'uhv' #for default

        
        #ver_dct = get_mks_project_rev(r'C:/controls/py2.7/project.pj')
        # filename = r'./version.json'
        # if os.path.exists(filename):
        #     ver_dct = json.loads(file(filename).read())
        #
        # else:
        #     ver_dct = {}
        #     ver_dct['ver'] = '1.9'
        #     ver_dct['major_ver'] = '1'
        #     ver_dct['minor_ver'] = '9'
        #     ver_dct['auth'] = 'Russ Berg'
        #     ver_dct['date'] = 'Jan 26 2017'
        #
        ver_dct = get_version()
        
        dct_put(self.main_obj, 'APP.STATUS', 'THIS IS THE STATUS')
        dct_put(self.main_obj, 'APP.UI', 'THIS IS THE UI')
        dct_put(self.main_obj, 'APP.USER', 'THIS IS THE USER')
        dct_put(self.main_obj, 'APP.SESSION', gen_session_obj())
        dct_put(self.main_obj, 'APP.VER', ver_dct['ver'])
        dct_put(self.main_obj, 'APP.MAJOR_VER', ver_dct['major_ver'])
        dct_put(self.main_obj, 'APP.MINOR_VER', ver_dct['minor_ver'])
        dct_put(self.main_obj, 'APP.AUTHOR', ver_dct['auth'])
        dct_put(self.main_obj, 'APP.DATE', ver_dct['date'])
        dct_put(self.main_obj, 'APP.COMMIT', ver_dct['commit'])

        
        dct_put(self.main_obj, 'SCAN.CFG.SCAN_TYPE', 'THIS IS THE SCAN CFG TYPE')
        dct_put(self.main_obj, 'SCAN.CFG.UNIQUEID', 0)
        dct_put(self.main_obj, 'SCAN.CFG.ROI', None)
        dct_put(self.main_obj, 'SCAN.DATA.CHANNELS', [])
        dct_put(self.main_obj, 'SCAN.DATA.POINTS', {})
        dct_put(self.main_obj, 'SCAN.DATA.SSCANS', {})
        
        dct_put(self.main_obj, 'DEVICES', {})
        
        self.sample_positioning_mode = None
        self.sample_fine_positioning_mode = None
        self.enable_multi_region = True
        
        #created to be a central location for all scan params and data
        # that can be used by any widget class or function, the keys for this
        # dict will be spatial_id's
        dct_put(self.main_obj, 'SCAN_DB', {})
        #self.init_zmq_socket()
        self.zmq_client = None
        #if(self.zmq_sock is not None):
        #self.zmq_client = qt5_zmqClientWidget(compression_type=compression_types.PICKLE)
        self.zmq_client = None
        #self.zmq_client = qt5_zmqClientWidget(compression_type=compression_types.MSGPACK)
            #self.zmq_client = zmq_epicsClient(self.zmq_sock)

        self.engine_widget = EngineWidget()

    def get_sample_positioner(self, axis='X'):
        '''
        return based on the sample positioning mode which sample positioner
        :return:
        '''

        # self.sample_positioning_mode
        # self.sample_fine_positioning_mode
        if(axis.find('X') > -1):
            if(self.sample_positioning_mode == sample_positioning_modes.GONIOMETER):
                posner = self.device(DNM_GONI_X)
            else:
                posner = self.device(DNM_SAMPLE_X)
        else:
            if (self.sample_positioning_mode == sample_positioning_modes.GONIOMETER):
                posner = self.device(DNM_GONI_Y)
            else:
                posner = self.device(DNM_SAMPLE_Y)
        return(posner)

    def get_sample_fine_positioner(self, axis='X'):
        '''
        return based on the sample positioning mode which sample positioner
        :return:
        '''

        # self.sample_positioning_mode
        # self.sample_fine_positioning_mode
        if(axis.find('X') > -1):
            if(self.sample_fine_positioning_mode == sample_fine_positioning_modes.ZONEPLATE):
                posner = self.device(DNM_ZONEPLATE_X)
            else:
                posner = self.device(DNM_SAMPLE_FINE_X)
        else:
            if (self.sample_positioning_mode == sample_positioning_modes.GONIOMETER):
                posner = self.device(DNM_ZONEPLATE_Y)
            else:
                posner = self.device(DNM_SAMPLE_FINE_Y)
        return(posner)

    def get_device_reverse_lu_dct(self):
        return(self.main_obj['DEVICES'].device_reverse_lookup_dct)

    def cleanup(self):
        #self.zmq_client.terminate()
        pass

    def engine_assign_baseline_devs(self, baseline_dev_lst):
        '''
        a list of ophyd devices that will be read and recorded in the data stream 'baseline' once at start of
        scan and once agan at stop

        :param baseline_dev_lst:
        :return:
        '''
        self.engine_widget.assign_baseline_devs(baseline_dev_lst)

    def engine_subscribe(self, func):
        sub_id = self.engine_widget.subscribe_cb(func)
        return(sub_id)

    def set_engine_metadata(self, md_dct):
        '''
        pass a dict that will be included in the scan meta data
        :param md_dct:
        :return:
        '''
        for k, v in md_dct.items():
            self.engine_widget.engine.md[k] = v

    #def zmq_client_new_scan(self, fname=None, upd_lst=[]):
    # self.zmq_client.init_new_scan(fname=fname,upd_lst=upd_lst)
    def zmq_client_new_scan(self, fname=None, subdir=None):
        #self.zmq_client.set_new_filename(fname=fname, subdir=subdir)
        pass

    def zmq_set_new_subdir(self, subdir=None):
        #self.zmq_client.set_new_subdir(subdir=subdir)
        pass

    def zmq_save_dict_to_tmp_file(self, dct):
        #self.zmq_client.send_dict_to_tmp_file(dct)
        pass
    def zmq_starttime_to_tmp_file(self):
        #self.zmq_client.starttime_to_tmp_file()
        pass

    def zmq_stoptime_to_tmp_file(self):
        #self.zmq_client.stoptime_to_tmp_file()
        pass

    def zmq_rename_tmp_to_final(self):
        #self.zmq_client.rename_tmp_to_final()
        pass

    def zmq_save_img_idx_map(self, img_idx_map=None):
        #self.zmq_client.send_img_idx_map(img_idx_map)
        pass

    def get_beamline_id(self):
        return(self.beamline_id)

    def get_sample_positioning_mode(self):
        return(self.sample_positioning_mode)
    
    def set_sample_positioning_mode(self, mode):
        self.sample_positioning_mode = mode
        
    def set_fine_sample_positioning_mode(self, mode):
        self.sample_fine_positioning_mode = mode

    def set_sample_scanning_mode_string(self, mode_str):
        self.sample_scanning_mode_string = mode_str

    def get_sample_scanning_mode_string(self):
        return(self.sample_scanning_mode_string)
    
    def get_fine_sample_positioning_mode(self):
        return(self.sample_fine_positioning_mode)
    
    def set_datafile_prefix(self, prfx):
        self.datafile_prfx = prfx
    
    def get_datafile_prefix(self):
        return(self.datafile_prfx)
    
    def set_thumbfile_suffix(self, sffx):
        self.thumbfile_suffix = sffx
    
    def get_thumbfile_suffix(self):
        return(self.thumbfile_suffix)
    
    def get_spatial_region(self, sp_id):
        if(sp_id in list(self.main_obj['SCAN_DB'].keys())):
            return(self.main_obj['SCAN_DB'][sp_id])
        else:
            return({})
    
    def set_spatial_region(self, sp_id, dct):
        self.main_obj['SCAN_DB'][sp_id] = dct
    
    def get_is_multi_region_enabled(self):
        return(self.enable_multi_region)
    
    def get_beamline_name(self):
        return(self.beamline)    
    
    def get_endstation_name(self):
        return(self.endstation)


    def get(self, name):
        """ get the object section by name """
        obj = dct_get(self.main_obj, name)
        return(obj)
    
    def set(self, name, obj):
        """ get the object section by name """
        dct_put(self.main_obj, name, obj)
        
    def get_main_obj(self):
        """ return the entire main object dict """
        return(self.main_obj)

    def set_endstation_prefix(self, prfx='uhv'):
        self.endstation_prefix = prfx

    def get_endstation_prefix(self):
        return(self.endstation_prefix)
            
    def get_main_as_master(self, with_devices=True):
        """ for saving to disk we might not want the entire main object
        this mthod returns a subset of the main object that is used to 
        be saved as teh master object for a scan (where all teh parameters and data are kept
        """
        dct = {}
        dct_put(dct, 'APP.STATUS', self.get('APP.STATUS'))
        dct_put(dct, 'APP.UI', self.get('APP.UI'))
        dct_put(dct, 'SCAN.CFG.TYPE', self.get('SCAN.CFG.TYPE'))
        dct_put(dct, 'SCAN.CFG.ROI', self.get('SCAN.CFG.ROI'))
        dct_put(dct, 'SCAN.CFG.UNIQUEID', self.get('SCAN.CFG.UNIQUEID'))
        dct_put(dct, 'SCAN.DATA.CHANNELS', self.get('SCAN.DATA.CHANNELS'))
        dct_put(dct, 'SCAN.DATA.POINTS', self.get('SCAN.DATA.POINTS'))
        dct_put(dct, 'SCAN.DATA.SSCANS', self.get('SCAN.DATA.SSCANS'))
        if(with_devices):
            dct_put(dct, 'DEVICES', self.get_devices())
        return(dct)
    
    def set_devices(self, dev_cls):
        """ assign the device section of themain object """
        self.main_obj['DEVICES'] = dev_cls
        self.changed.emit()
    
    def device(self, name):
        """ call the device method from the devices class """
        dev = self.main_obj['DEVICES'].device(name)
        if(dev is None):
            _logger.error('Error: dev [%s] does not exist in master object' % name)

        return(dev)
    
    def get_device_obj(self):
        return(self.main_obj['DEVICES'])
    
    def get_devices(self):
        """ call the device method from the devices class """
        return(self.main_obj['DEVICES'].get_devices())
    
    def get_sscan_prefix(self):
        return(self.main_obj['DEVICES'].sscan_rec_prfx)
            
    def get_device_list(self, detectors=False):
        return(self.main_obj['DEVICES'].get_device_list(detectors))
    
    def add_scan(self, scan):
        """ add a scan to the list of scans to execute """
        self.main_obj['SSCANS'].append(scan)
        self.changed.emit()
    
    def clear_scans(self):
        """ delete all scans from list of scans to execeute """
        self.main_obj['SSCANS'] = []
        self.changed.emit()
        
    def get_preset(self, name):
        devices = self.get_devices()
        if(name in list(devices['PRESETS'].keys())):
            return(devices['PRESETS'][name])
        else:
            _logger.error('PRESET [%s] not found in device configuration' % name)
            return(None)    
    
    def get_preset_as_float(self, name):
        val = self.get_preset(name)
        if(val is not None):
            return(float(val))
        else:
            return(None)

    def get_preset_as_int(self, name):
        val = self.get_preset(name)
        if(val is not None):
            return(int(val))
        else:
            return(None)
    
    def init_zmq_socket(self):
        import zmq
        self.zmq_context = zmq.Context()
        
        #  Socket to talk to server
        #print('Connecting to hello world server')
        self.zmq_sock = self.zmq_context.socket(zmq.REQ)
        self.zmq_sock.RCVTIMEO = 1000
        self.zmq_sock.connect("tcp://localhost:5555")
        #self.check_zmq_server()

    
    def check_zmq_server(self):
        global app
        _logger.debug('check_zmq_server: is server running?')
        try:
            resp = snd_rcv(self.zmq_sock, CMD_CHECK_IF_RUNNING)
            if(resp == 'YES'):
                _logger.debug('Yes it is')
            else:
                _logger.debug('NO it isnt')
            
        except:
            _logger.error('NO it isnt, zmq_epics_server must be running first, exiting')
            app.quit()

            
    
    def get_zmq_posner_list(self):
        slist = snd_rcv(self.zmq_sock, CMD_DISC_POSNER_LIST)
        pos_keys = process_str_to_list(slist)
        #print pos_keys
        return(pos_keys)
    
    def update_zmq_posner_snapshot(self):
        resp = snd_rcv(self.zmq_sock, CMD_UPDATE_POSNER_SNAPSHOT)
        #print resp    
    
    def _get_zmq_posner_snapshot(self):
        snap_dct = snd_rcv(self.zmq_sock, CMD_GET_POSNER_SNAPSHOT)
        snapshot_dct = process_str_to_dict(snap_dct)
        #print pos_snapshot_dct['OSAX.X']['VELO']
        return(snapshot_dct)
    
    def update_zmq_detector_snapshot(self):
        resp = snd_rcv(self.zmq_sock, CMD_UPDATE_DETECTOR_SNAPSHOT)
        #print resp    
    
    def _get_zmq_detector_snapshot(self):
        snap_dct = snd_rcv(self.zmq_sock, CMD_GET_DETECTOR_SNAPSHOT)
        snapshot_dct = process_str_to_dict(snap_dct)
        #print pos_snapshot_dct['OSAX.X']['VELO']
        return(snapshot_dct)
    
    def update_zmq_pv_snapshot(self):
        resp = snd_rcv(self.zmq_sock, CMD_UPDATE_PV_SNAPSHOT)
        #print resp    
    
    def _get_zmq_pv_snapshot(self):
        snap_dct = snd_rcv(self.zmq_sock, CMD_GET_PV_SNAPSHOT)
        snapshot_dct = process_str_to_dict(snap_dct)
        #print pos_snapshot_dct['OSAX.X']['VELO']
        return(snapshot_dct)
        
    def take_zmq_sscan_snapshot(self, sscan_name):
        if(USE_ZMQ):
            dct = self._get_zmq_sscan_snapshot(sscan_name)
        else:
            _logger.error('_get_zmq_sscan_snapshot: Not currently supported without using ZMQ')
            dct = {}
        return(dct)
                        
    def update_zmq_sscan_snapshot(self, upd_list):
        #resp = snd_rcv(self.zmq_sock, CMD_UPDATE_SSCAN_SNAPSHOT)
        send_update_list_msg(self.zmq_sock, CMD_UPDATE_SSCAN_SNAPSHOT, upd_list)
    
    def _get_zmq_sscan_snapshot(self, upd_list):
        snapshot_dct = send_get_sscan_msg(self.zmq_sock, CMD_GET_SSCAN_SNAPSHOT, upd_list)
        #print snapshot_dct
        #print pos_snapshot_dct['OSAX.X']['VELO']
        return(snapshot_dct)
    
    def take_positioner_snapshot(self, posners_dct):
        """
        take_positioner_snapshot(): description

        :param posners_dct: posners_dct description
        :type posners_dct: posners_dct type

        :returns: None
        """
        """
        This function grabs the current values of all positioners for the 
        data saving thread to use
        
        """
        if(USE_ZMQ):
            dct = self._get_zmq_posner_snapshot()
            #print 'take_positioner_snapshot: Done'
        else:
            dct = {}
            for k in list(posners_dct.keys()):
                dct[k] = {}
                dct[k]['VELO'] = posners_dct[k].get('velocity')
                dct[k]['VAL'] = posners_dct[k].get('user_setpoint')
                dct[k]['DESC'] = posners_dct[k].get('description')
                dct[k]['NAME'] = posners_dct[k].get_name()
                dct[k]['ACCL'] = posners_dct[k].get('acceleration')
                #dct[k]['RRBV'] = posners_dct[k].get('raw_readback')
                dct[k]['LLM'] = posners_dct[k].get_low_limit()
                dct[k]['HLM'] = posners_dct[k].get_high_limit()
                #dct[k]['RDBD'] = posners_dct[k].get('retry_deadband')
                dct[k][RBV] = posners_dct[k].get('user_readback')
                
        return(dct)
    
    
    def take_detectors_snapshot(self, detectors_dct):
        """
        take_detectors_snapshot(): description

        :param detectors_dct: detectors_dct description
        :type detectors_dct: detectors_dct type

        :returns: None
        """
        """
        This function grabs the current values of all positioners for the 
        data saving thread to use
        
        """
        if(USE_ZMQ):
            dct = self._get_zmq_detector_snapshot()
            #print 'take_detectors_snapshot: Done'
            return(dct)
        else:
            dct = {}
            for k in list(detectors_dct.keys()):
                dct[k] = {}
                dct[k][RBV] = detectors_dct[k].get_position()
                   
        return(dct)

    def take_pvs_snapshot(self, pvs_dct):
        """
        take_pvs_snapshot(): description

        :param pvs_dct: pvs_dct description
        :type pvs_dct: pvs_dct type

        :returns: None
        """
        """
        This function grabs the current values of all positioners for the 
        data saving thread to use
        
        """
        try:
            if(USE_ZMQ):
                dct = self._get_zmq_pv_snapshot()
                #print 'take_pvs_snapshot: Done'
            else:
                dct = {}
                for k in list(pvs_dct.keys()):
                    dct[k] = {}
                    dct[k][RBV] = pvs_dct[k].get_position()
                    dct[k]['PVNAME'] = pvs_dct[k].get_name()

            return(dct)
        except:
            print('Problem connecting to pv [%s]' % k)


    def take_temps_snapshot(self, pvs_dct):
        """
        take_temps_snapshot(): description

        :param pvs_dct: pvs_dct description
        :type pvs_dct: pvs_dct type

        :returns: None
        """
        """
        This function grabs the current values of all temperatures for the
        data saving thread to use

        """
        if(USE_ZMQ):
            dct = self._get_zmq_pv_snapshot()
            #print 'take_pvs_snapshot: Done'
        else:
            dct = {}
            for k in list(pvs_dct.keys()):
                dct[k] = {}
                rbv = pvs_dct[k].get_position()
                if(rbv is None):
                    dct[k][RBV] = -99999.0
                else:
                    dct[k][RBV] = rbv

                desc = pvs_dct[k].get_desc()
                if(desc is None):
                    dct[k]['DESC'] = 'Not Connected'
                else:
                    dct[k]['DESC'] = desc

                egu = pvs_dct[k].get_egu()
                if(egu is None):
                    dct[k]['EGU'] = 'Unknown'
                else:
                    dct[k]['EGU'] = egu

        return(dct)

    def take_pressures_snapshot(self, pvs_dct):
        """
        take_pressures_snapshot(): description

        :param pvs_dct: pvs_dct description
        :type pvs_dct: pvs_dct type

        :returns: None
        """
        """
        This function grabs the current values of all pressures for the
        data saving thread to use

        """
        if(USE_ZMQ):
            dct = self._get_zmq_pv_snapshot()
            #print 'take_pvs_snapshot: Done'
        else:
            dct = {}
            for k in list(pvs_dct.keys()):
                dct[k] = {}
                rbv = pvs_dct[k].get_position()
                desc = pvs_dct[k].get_desc()
                egu = pvs_dct[k].get_egu()
                if (rbv is None):
                    dct[k][RBV] = -99999.0
                else:
                    dct[k][RBV] = rbv

                dct[k]['DESC'] = desc
                dct[k]['EGU'] = egu

        return(dct)
    


class dev_config_base(QtCore.QObject):
    def __init__(self, splash=None):
        super(dev_config_base, self).__init__()

        if(splash is None):
            #self.splash = CSplashScreen("Starting to connect devices:")
            #self.splash = SplashScreen()
            self.splash = get_splash()
        else:
            self.splash = splash
        self.devices = {}
        self.devices['POSITIONERS'] = {}
        self.devices['TEMPERATURES'] = {}
        self.devices['TEMPERATURES'][POS_TYPE_ES] = {}    # Endstation temperatures
        self.devices['TEMPERATURES'][POS_TYPE_BL] = {}    # Beamline temperatures
        self.devices['PRESSURES'] = {}
        self.devices['PRESSURES'][POS_TYPE_ES] = {}    # Endstation pressures
        self.devices['PRESSURES'][POS_TYPE_BL] = {}    # Beamline pressures
        
        self.devices['DETECTORS'] = {}
        self.devices['DETECTORS_NO_RECORD'] = {}
        self.devices['DIO'] = {}
        self.devices['SSCANS'] = {}
        self.devices['PVS'] = {}
        self.devices['PVS_DONT_RECORD'] = {}
        self.devices['PVS_DONT_RECORD']['HEARTBEATS'] = {}
        self.devices['PRESETS'] = {}
        self.devices['ACTUATORS'] = {}
        self.devices['WIDGETS'] = {}
        
        self.snapshot = {}
        self.snapshot['POSITIONERS'] = {}

        #provide a variable that will hold a list of positioners that are excluded from being offered on the GUI
        self.exclude_list = []

        self.sscan_rec_prfx = None    #either 'ambient' or 'uhv'
        self.es_id = None #needs to be defined by inheriting class

        self.posner_reverse_lookup_dct = {}

    def devs_as_list(self, skip_lst=[]):
        '''

        :return:
        '''
        _logger.debug('devs_as_list: returning list of Devices')
        dlst = []
        for t in self.devices['TEMPERATURES'].keys():
            for k, dev in self.devices['TEMPERATURES'][t].items():
                #print('devs_as_list: [%s]' % k)
                if(k in skip_lst):
                    #skip it
                    continue
                ophyd_dev = dev.get_ophyd_device()
                if (ophyd_dev is not None):
                    dlst.append(ophyd_dev)

        for t in self.devices['PRESSURES'].keys():
           for k, dev in self.devices['PRESSURES'][t].items():
               #print('devs_as_list: [%s]' % k)
               if (k in skip_lst):
                   # skip it
                   continue
               ophyd_dev = dev.get_ophyd_device()
               if (ophyd_dev is not None):
                   dlst.append(ophyd_dev)

        for k, ophyd_dev in self.devices['POSITIONERS'].items():
            #print('devs_as_list: [%s]' % k)
            if (k in skip_lst):
                # skip it
                continue
            if (ophyd_dev is not None):
                dlst.append(ophyd_dev)

        for k, dev in self.devices['PVS'].items():
            if (k in skip_lst):
                # skip it
                continue
            dev_nm = dev.get_name()
            if(dev_nm.find('.') > -1):
                #skip pv's with a .field cause they screwup BlueSky
                #print('devs_as_list: SKIPPING: [%s]' % k)
                continue
            if(hasattr(dev, 'get_ophyd_device')):
                ophyd_dev = dev.get_ophyd_device()
                if (ophyd_dev is not None):
                    #print('devs_as_list: [%s]' % k)
                    dlst.append(ophyd_dev)

        # for t in self.devices['DETECTORS'].keys():
        #    for k, ophyd_dev in self.devices['DETECTORS'].items():
        #        #print('devs_as_list: [%s]' % k)
        #        if (ophyd_dev is not None):
        #            dlst.append(ophyd_dev)

        return (dlst)

    def close_splash(self):
        self.splash.close()

    def on_timer(self):
        QtWidgets.QApplication.processEvents()
    
    def msg_splash(self, msg):
        print(msg)
        #return
        # if(self.splash):
        #     #self.splash.showMessage(self.splash.tr(msg), QtCore.Qt.AlignBottom,QtCore.Qt.white)
        #     self.splash.show_msg(self.splash.tr(msg))
        #     #QtWidgets.QApplication.processEvents()
        #     #QtWidgets.QApplication.processEvents(QtCore.QEventLoop.AllEvents, 50)
        #     #time.sleep(0.05)

    def set_exclude_positioners_list(self, excl_lst):
        self.exclude_list = excl_lst

    def get_exclude_positioners_list(self):
        return(self.exclude_list)

    def get_all_pvs_of_type(self, category_name=None):
        pv_devs = self.devices['PVS_DONT_RECORD']
        if(category_name in list(pv_devs.keys())):
            return(pv_devs[category_name])
        else:
            _logger.warning('Pvs of type [%s] not found in PVS_DONT_RECORD configuration' % category_name)
            return(None)

    def get_all_temperatures(self, category_name=None):
        if(category_name is None):
            return(dct_merge(self.devices['TEMPERATURES'][POS_TYPE_ES], self.devices['TEMPERATURES'][POS_TYPE_BL]))
        
        elif(category_name == POS_TYPE_ES):
            return(self.devices['TEMPERATURES'][POS_TYPE_ES])
        elif(category_name == POS_TYPE_BL):
            return(self.devices['TEMPERATURES'][POS_TYPE_BL])
        else:
            _logger.warning('Temperature Category [%s] not found in temperature configuration' % category_name)
            return(None)
    
    def get_tm(self, name):
        if(name in list(self.devices['TEMPERATURES'][POS_TYPE_ES].keys())):
            return(self.devices['TEMPERATURES'][POS_TYPE_ES][name])
        elif(name in list(self.devices['TEMPERATURES'][POS_TYPE_BL].keys())):
            return(self.devices['TEMPERATURES'][POS_TYPE_BL][name])
        else:
            _logger.warning('Temperature [%s] not found in temperature configuration' % name)
            return(None)
        
    def get_all_pressures(self, category_name=None):
        if(category_name is None):
            return(dct_merge(self.devices['PRESSURES'][POS_TYPE_ES], self.devices['PRESSURES'][POS_TYPE_BL]))
        
        elif(category_name == POS_TYPE_ES):
            return(self.devices['PRESSURES'][POS_TYPE_ES])
        elif(category_name == POS_TYPE_BL):
            return(self.devices['PRESSURES'][POS_TYPE_BL])
        else:
            _logger.warning('Pressure Category [%s] not found in pressures configuration' % name)
            return(None)    
    
    def get_pressure(self, name):
        if(name in list(self.devices['PRESSURES'][POS_TYPE_ES].keys())):
            return(self.devices['PRESSURES'][POS_TYPE_ES][name])
        elif(name in list(self.devices['PRESSURES'][POS_TYPE_BL].keys())):
            return(self.devices['PRESSURES'][POS_TYPE_BL][name])
        else:
            _logger.warning('Pressure [%s] not found in pressures configuration' % name)
            return(None)


    def get_widget(self, name):
        if(name in list(self.devices['WIDGETS'].keys())):
            return(self.devices['WIDGETS'][name])
        else:
            _logger.warning('Widget [%s] not found in widgets configuration' % name)
            return(None)


    def device(self, name):
        if(name in list(self.devices['POSITIONERS'].keys())):
            return(self.devices['POSITIONERS'][name])
        elif(name in list(self.devices['DETECTORS'].keys())):
            return(self.devices['DETECTORS'][name])
        elif(name in list(self.devices['DETECTORS_NO_RECORD'].keys())):
            return(self.devices['DETECTORS_NO_RECORD'][name])
        elif(name in list(self.devices['DIO'].keys())):
            return(self.devices['DIO'][name])
        elif(name in list(self.devices['SSCANS'].keys())):
            return(self.devices['SSCANS'][name])
        elif(name in list(self.devices['PVS'].keys())):
            return(self.devices['PVS'][name])
        elif(name in list(self.devices['PVS_DONT_RECORD'].keys())):
            return(self.devices['PVS_DONT_RECORD'][name])
        elif(name in list(self.devices['ACTUATORS'].keys())):
            return(self.devices['ACTUATORS'][name])
        elif (name in list(self.devices['WIDGETS'].keys())):
            return (self.devices['WIDGETS'][name])
        else:
            _logger.warning('Device [%s] not found in device configuration' % name)
            return(None)


    def device_report(self):
        '''
        dump a report of all devices
        :return:
        '''
        for name in list(self.devices['POSITIONERS'].keys()):
            self.devices['POSITIONERS'][name].report()

        for name in list(self.devices['DETECTORS'].keys()):
            self.devices['DETECTORS'][name].report()

        for name in list(self.devices['DETECTORS_NO_RECORD'].keys()):
            self.devices['DETECTORS_NO_RECORD'][name].report()

        for name in list(self.devices['DIO'].keys()):
            self.devices['DIO'][name].report()

        for name in list(self.devices['SSCANS'].keys()):
            self.devices['SSCANS'][name].report()

        for name in list(self.devices['PVS'].keys()):
            self.devices['PVS'][name].report()

        for name in list(self.devices['PVS_DONT_RECORD'].keys()):
            print(self.devices['PVS_DONT_RECORD'][name].report())

        for name in list(self.devices['ACTUATORS'].keys()):
            self.devices['ACTUATORS'][name].report()

        for name in list(self.devices['WIDGETS'].keys()):
            self.devices['WIDGETS'][name].report()


#     def device(self, name):
#         for k in self.devices.keys():
#             d = dct_get(self.devices[k], name)
#             if(d is not None):
#                 return(d)
#         return(None)
#        
#     def do_connection_check(self):
#         
#         for k1 in self.devices.keys():
#             
#             
#             
#         self.devices['POSITIONERS'][DNM_SAMPLE_FINE_Y]._pvs['DESC'].connected
    def init_snapshot(self):
        self.snapshot = dict.copy(self.devices)
    
    def get_posner_snapshot(self):
        return(self.snapshot['POSITIONERS'])
    
    def get_devices(self):
        return(self.devices)
    
    def get_device_list(self, detectors=False):
        if(detectors):
            return(list(self.devices['DETECTORS'].keys()))
        else:
            return(list(self.devices['POSITIONERS'].keys()))

    
    def init_scans(self, scan_prefix):
        scans = []
        for i in range(1,17):
            scans.append(Scan(scan_prefix + ':scan%d' % (i)))
        
        return(scans)
