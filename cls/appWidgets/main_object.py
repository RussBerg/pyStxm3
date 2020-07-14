
from PyQt5 import QtCore, QtWidgets
from datetime import datetime

from cls.appWidgets.splashScreen import get_splash
from cls.utils.dict_utils import dct_put, dct_get, dct_merge
from cls.utils.version import get_version
# from cls.zeromq.epics.qt5_epics_client import zmq_epicsClient
from cls.zeromq.epics.qt5_cepics_client_pubsub import qt5_zmqClientWidget, compression_types
from cls.utils.roi_dict_defs import *
from cls.utils.log import get_module_logger
from cls.utils.fileUtils import get_module_name
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

        dct_put(self.main_obj, 'PRESETS', {})
        
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
        self.rot_angle_dev = None

        self.engine_widget = EngineWidget()

    def set_presets(self, preset_dct):
        self.main_obj['PRESETS'] = preset_dct

    def is_device_supported(self, devname):
        '''
        check through all of the configured devices and return True if device exists and False if it doesnt
        :param devname:
        :return:
        '''
        ret = self.device(devname, do_warn=False)
        return(ret)

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

    def set_rot_angle_device(self, dev):
        '''
        set the device to be used to retrieve the rsample rotation angle
        :param dev:
        :return:
        '''
        self.rot_angle_dev = dev

    def get_sample_rotation_angle(self):
        if(self.rot_angle_dev is None):
            return(0.0)
        else:
            return(self.rot_angle_dev.get_position())

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

    def get_scan_panel_order(self, fname):
        '''
        from the beamline configuration file get teh enumeration for the scan_name, the scan_name should match the
        name of the module
        return enumeration if scan_name exists, None if it doesnt
        :param scan_name:
        :return:
        '''
        scan_mod_name = get_module_name(fname)

        idx = self.get_preset_as_int(scan_mod_name, 'SCAN_PANEL_ORDER')
        return(idx)

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
    
    def device(self, name, do_warn=True):
        """ return the device if it exists"""
        dev = self.main_obj['DEVICES'].device(name, do_warn=do_warn)
        if(dev is None):
            if(do_warn):
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
        
    # def get_preset(self, name):
    #     devices = self.get_devices()
    #     if(name in list(devices['PRESETS'].keys())):
    #         return(devices['PRESETS'][name])
    #     else:
    #         _logger.warn('PRESET [%s] not found in device configuration' % name)
    #         return(None)
    def get_preset(self, name, section=None):
        '''
        search through all sections looking for the FIRST instance of the desired preset, this is case insensitive
        :param name:
        :param section: is section is None, then search entire PRESET dict
        :return:
        '''
        result = None
        name_upper = name.upper()
        name_lower = name.lower()

        presets = self.main_obj['PRESETS']
        sections = presets.keys()
        if(section):
            if(section in sections):
                if(name_upper in presets[section].keys()):
                    result = presets[section][name_upper]
                elif(name_lower in presets[section].keys()):
                    result = presets[section][name_lower]
                else:
                    _logger.debug('PRESET [%s][%s] not found in presets' % (section, name))
        else:
            for s in sections:
                if(name_upper in list(presets[s].keys())):
                    result = presets[s][name_upper]
                    break
                if (name_lower in list(presets[s].keys())):
                    result = presets[s][name_lower]
                    break
        if(result is None):
            _logger.debug('PRESET [%s] not found in presets' % name)

        return(result)
    
    def get_preset_as_float(self, name, section=None):
        val = self.get_preset(name, section)
        if(val is not None):
            return(float(val))
        else:
            return(None)

    def get_preset_as_int(self, name, section=None):
        val = self.get_preset(name, section)
        if(val is not None):
            return(int(val))
        else:
            return(None)

    def get_preset_as_bool(self, name, section=None):
        val = self.get_preset(name, section)
        if(val is not None):
            if(val.find('true') > -1):
                return(True)
            else:
                return(False)
        else:
            return(False)
    
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
        #self.devices['PRESETS'] = {}
        self.devices['ACTUATORS'] = {}
        self.devices['WIDGETS'] = {}
        
        self.snapshot = {}
        self.snapshot['POSITIONERS'] = {}

        #provide a variable that will hold a list of positioners that are excluded from being offered on the GUI
        self.exclude_list = []

        self.sscan_rec_prfx = None    #either 'ambient' or 'uhv'
        self.es_id = None #needs to be defined by inheriting class

        self.posner_reverse_lookup_dct = {}

    def parse_cainfo_stdout_to_dct(self, s):
        dct = {}
        s2 = s.split('\n')
        for l in s2:
            l2 = l.replace(' ', '')
            l3 = l2.split(':')
            if (len(l3) > 1):
                dct[l3[0]] = l3[1]
        return (dct)

    def do_pv_conn_check(self, num_pvs, pvname, verbose=False):
        import subprocess
        proc = subprocess.Popen('cainfo %s' % pvname, stdout=subprocess.PIPE)
        stdout_str = proc.stdout.read()
        _dct = self.parse_cainfo_stdout_to_dct(stdout_str.decode('utf-8'))
        if(verbose):
            if(self.check_cainfo(_dct)):
                print('[%d] pv connection check [%s] is connected and ready' % (num_pvs, pvname))
        else:
            if (self.check_cainfo(_dct)):
                print('', end=".")
            else:
                #just make a new line for the error that will be printed shortly
                print()
        return (_dct)

    def perform_device_connection_check(self, verbose=False):

        print('Performing individual device connection check, this may take a few minutes depending:')
        skip_lst = ['PVS_DONT_RECORD', 'PRESETS', 'DETECTORS_NO_RECORD', 'WIDGETS']
        dev_dct = {}
        num_pvs = 0
        num_fail_pvs = 0
        sections = list(self.devices.keys())
        for section in sections:
            keys = []
            if (section not in skip_lst):
                keys = list(self.devices[section].keys())
                # check to see if this is a subsectioned section that has pvs for BL (beamline) and ES (endstation)
                # if so do those
                if (keys == ['BL', 'ES']):
                    dev_dct[section] = {}
                    for subsec in keys:
                        for pvname in list(self.devices[section][subsec].keys()):
                            num_pvs += 1
                            _dct = self.do_pv_conn_check(num_pvs, self.build_pv_name(pvname), verbose)
                            dev_dct[section][pvname] = {}
                            dev_dct[section][pvname]['dev'] = self.devices[section][subsec][pvname]
                            dev_dct[section][pvname]['cainfo'] = _dct
                            if(not self.check_cainfo(_dct)):
                                num_fail_pvs += 1
                                print('[%d][%s] does not appear to exist' % (num_pvs, k))

                else:
                    for k in keys:
                        dev = self.devices[section][k]
                        dev_dct[section] = {}
                        dev_dct[section][k] = {}
                        if type(dev) is dict:
                            for kk in dev.keys():
                                num_pvs += 1
                                dev_dct[section][k][kk] = {}
                                dev_dct[section][k][kk]['dev'] = dev[kk]
                                _dct = self.do_pv_conn_check(num_pvs, self.build_pv_name(dev[kk]), verbose)
                                dev_dct[section][k][kk]['cainfo'] = _dct
                                if(not self.check_cainfo(_dct)):
                                    num_fail_pvs += 1
                                    print('[%d][%s] does not appear to exist' % (num_pvs, dev[kk].prefix))

                        else:
                            num_pvs += 1
                            _dct = self.do_pv_conn_check(num_pvs, self.build_pv_name(dev), verbose)
                            dev_dct[section][k]['cainfo'] = _dct
                            if(not self.check_cainfo(_dct)):
                                num_fail_pvs += 1
                                print('[%d][%s] does not appear to exist' % (num_pvs, dev.prefix))


        #report
        if(num_fail_pvs > 0):
            print('\n%d devices failed to connect out of a total of %d' % (num_fail_pvs, num_pvs))
            exit()
        else:
            print('\nall %d devices are connected' % (num_pvs))

    def build_pv_name(self, dev):
        pvname = None
        if hasattr(dev, 'component_names'):
            #just use the first one
            a = getattr(dev, dev.component_names[0])
            pvname = a.pvname
        else:
            pvname = dev.prefix
        return(pvname)

    def check_cainfo(self, d):
        if d is None:
            return(False)
        if len(d) == 0:
            return(False)
        if (d['State'].find('dis') > -1):
            return(False)
        return(True)

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

        now = datetime.now()  # current date and time
        date_time = now.strftime("%m/%d/%Y, %H:%M:%S")
        print('%s: %s' % (date_time, msg))
        # return
        if (self.splash):
            # self.splash.showMessage(self.splash.tr(msg), QtCore.Qt.AlignBottom,QtCore.Qt.white)
            self.splash.show_msg(self.splash.tr(msg))
            # QtWidgets.QApplication.processEvents(QtCore.QEventLoop.AllEvents, 50)
            # time.sleep(0.05)

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


    # def device(self, name, do_warn=True):
    #     if(name in list(self.devices['POSITIONERS'].keys())):
    #         return(self.devices['POSITIONERS'][name])
    #     elif(name in list(self.devices['DETECTORS'].keys())):
    #         return(self.devices['DETECTORS'][name])
    #     elif(name in list(self.devices['DETECTORS_NO_RECORD'].keys())):
    #         return(self.devices['DETECTORS_NO_RECORD'][name])
    #     elif(name in list(self.devices['DIO'].keys())):
    #         return(self.devices['DIO'][name])
    #     elif(name in list(self.devices['SSCANS'].keys())):
    #         return(self.devices['SSCANS'][name])
    #     elif(name in list(self.devices['PVS'].keys())):
    #         return(self.devices['PVS'][name])
    #     elif(name in list(self.devices['PVS_DONT_RECORD'].keys())):
    #         return(self.devices['PVS_DONT_RECORD'][name])
    #     elif(name in list(self.devices['ACTUATORS'].keys())):
    #         return(self.devices['ACTUATORS'][name])
    #     elif (name in list(self.devices['WIDGETS'].keys())):
    #         return (self.devices['WIDGETS'][name])
    #     else:
    #         if(do_warn):
    #             _logger.debug('Device [%s] not found in device configuration' % name)
    #         return(None)

    def devs_exist(self, devlist=[]):
        '''
        check to see if a list of devices exist in the device database

        :param devlist:
        :return:
        '''
        for dev in devlist:
            if(self.device(dev) is None):
                return(False)
        return(True)

    def device(self, name, do_warn=True):
        '''
            search entire device database looking for device
        :param name:
        :param do_warn:
        :return:
        '''

        for cat in list(self.devices.keys()):
            if (name in list(self.devices[cat].keys())):
                return (self.devices[cat][name])
        if(do_warn):
            _logger.debug('Device [%s] not found in device configuration' % name)
        return(None)


    def device_report(self):
        '''
        dump a report of all devices
        :return:
        '''
        skip_list = ['PRESETS', 'WIDGETS','ACTUATORS']
        for category in list(self.devices.keys()):
            print('[%s]' % category)
            if(category in skip_list):
                continue
            for name in list(self.devices[category].keys()):
                if((name.find('ES') > -1) or (name.find('BL') > -1)):
                    for _name in list(self.devices[category][name].keys()):
                        self.devices[category][name][_name].report()
                elif(name.find('HEARTBEATS') > -1):
                    for _name in list(self.devices[category][name].keys()):
                        self.devices[category][name][_name]['dev'].report()

                else:
                    #print('NAME=[%s]' % name)
                    if(type(self.devices[category][name]) == list):
                        for _dev in list(self.devices[category][name]):
                            _dev.report()
                    else:
                        self.devices[category][name].report()


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

