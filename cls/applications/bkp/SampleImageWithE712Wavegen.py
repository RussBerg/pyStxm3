
'''
Created on Apr 26, 2017

@author: bergr
'''
import os
import copy
import atexit
import numpy as np
import time

from bcm.devices.device_names import *

from cls.applications.pyStxm import abs_path_to_ini_file
from cls.applications.pyStxm.bl10ID01 import MAIN_OBJ

from cls.scanning.BaseScan import BaseScan, SIM_SPEC_DATA, SIMULATE_SPEC_DATA
from cls.scanning.SScanClass import SScanClass
from cls.scanning.scan_cfg_utils import set_devices_for_point_scan, set_devices_for_line_scan, \
    set_devices_for_e712_wavegen_point_scan, set_devices_for_e712_wavegen_line_scan, make_timestamp_now
from cls.types.stxmTypes import scan_types, scan_sub_types, \
    energy_scan_order_types, sample_positioning_modes, sample_fine_positioning_modes
from cls.scanning.scan_cfg_utils import ensure_valid_values, calc_accRange
from cls.utils.roi_dict_defs import *
from cls.utils.dict_utils import dct_get
from cls.utils.log import get_module_logger
from cls.utils.cfgparser import ConfigClass
from cls.utils.dict_utils import dct_put, dct_get
from cls.types.beamline import BEAMLINE_IDS
from cls.utils.prog_dict_utils import make_progress_dict
from cls.utils.json_utils import dict_to_json

from cls.scanning.e712_wavegen.e712 import X_WAVE_TABLE_ID
from cls.scanning.e712_wavegen.e712 import E712ControlWidget
from cls.scanning.e712_wavegen.ddl_store import gen_ddl_database_key

from cls.zeromq.epics.epics_api import *

from cls.plotWidgets.utils import *

_logger = get_module_logger(__name__)

appConfig = ConfigClass(abs_path_to_ini_file)


class SampleImageWithE712Wavegen(BaseScan):
    '''
    This class is based on SampleImageWithEnergySSCAN and modified to support the E712 waveform generator
    for executing the low level scan and triggering, the main scan is still controlled by SSCAN records but instead of using sscan records and motor
    positioners to move the motors it uses the E712 waveform generator which must be configured first here.

    The standard BaseScan api will be followed and hte E712 wave generator will only be used if it is :
        - a fine scan
        - the E712 is available
    if the scan is a coarse scan it will not be used, this should work for both zoneplate and standard sample fine scans.

    Note: the configuration is the only thing that changes in order to execute pxp or lxl scans, the data from a pxp scans when using the
    waveform generator are received as a complete line just like lxl scans
    '''


    def __init__(self):
        """
        __init__(): description

        :returns: None
        """
        super(SampleImageWithE712Wavegen, self).__init__('%sstxm' % MAIN_OBJ.get_sscan_prefix(), 'SAMPLEXY_EV_WG',
                                                         main_obj=MAIN_OBJ)
        self.x_use_reinit_ddl = False
        # self.x_use_ddl = False
        # self.x_use_reinit_ddl = False
        # self.x_start_end_pos = False
        # self.x_force_reinit = False
        self.x_auto_ddl = True
        #self.spid_data = None
        self.img_idx_map = {}
        self.spid_data = {}


    def init_update_dev_lst(self):
        '''
         populate the list of devices I want snapshotted on each data_level_done signal, I dont like that the nexus path
         is specified here, needs to be handled in a more standard way
        :return:
        '''
        self.update_dev_lst = []
        self.update_dev_lst.append(DNM_ENERGY)

        self.update_dev_lst.append(DNM_EPU_POLARIZATION)
        self.update_dev_lst.append(DNM_EPU_ANGLE)
        self.update_dev_lst.append(DNM_EPU_GAP)
        self.update_dev_lst.append(DNM_EPU_HARMONIC)
        self.update_dev_lst.append(DNM_EPU_OFFSET)

        self.update_dev_lst.append(DNM_PMT)
        self.update_dev_lst.append(DNM_RING_CURRENT)
        self.update_dev_lst.append(DNM_TYCHO_CAMERA)

        #self.main_obj.zmq_register_upd_list(self.update_dev_lst)


    def init_sscans(self):

        self.cb_idxs = []
        self.ttl_pnts = 0
        self.final_data_dir = None

        self.setupScan = SScanClass('%s:scan5' % self.scan_prefix, 'SETUP', main_obj=MAIN_OBJ)
        self._scan5 = SScanClass('%s:scan5' % self.scan_prefix, 'SSETUP', main_obj=MAIN_OBJ)
        self._scan4 = SScanClass('%s:scan4' % self.scan_prefix, SPDB_EV_EV, main_obj=MAIN_OBJ)
        self._scan3 = SScanClass('%s:scan3' % self.scan_prefix, SPDB_EV_POL, main_obj=MAIN_OBJ)


        self.gateCntrCfgScan = SScanClass('%s:scan2' % self.scan_prefix, 'GATECOUNT_CFG', main_obj=MAIN_OBJ)

        self._scan2 = SScanClass('%s:scan2' % self.scan_prefix, SPDB_Y, posner=MAIN_OBJ.device(DNM_SAMPLE_Y),
                                 main_obj=MAIN_OBJ)
        self._scan1 = SScanClass('%s:scan1' % self.scan_prefix, SPDB_X, posner=MAIN_OBJ.device(DNM_SAMPLE_X),
                                 main_obj=MAIN_OBJ)

        #self.e712_wg = E712ControlWidget('IOCE712:', counter=self.counter, gate=self.gate)
        self.e712_wg = MAIN_OBJ.device('E712ControlWidget')
        #self.e712_wg.show()
        # self.evScan = SScanClass('%s:image:scan4' % self.scan_prefix, SPDB_EV_EV)
        self.evScan = self._scan4
        self.evScan.set_positioner(1, MAIN_OBJ.device('ENERGY'))

        #self.gate_cntr_sscan = self._scan3

        # self.polScan = SScanClass('%s:image:scan3' % self.scan_prefix, SPDB_EV_POL)
        self.polScan = self._scan3
        self.polScan.set_positioner(1, MAIN_OBJ.device(DNM_EPU_POLARIZATION))
        self.polScan.set_positioner(2, MAIN_OBJ.device(DNM_EPU_OFFSET))
        self.polScan.set_positioner(3, MAIN_OBJ.device(DNM_EPU_ANGLE))
        
        ev_pol_lxl = {}
        ev_pol_lxl['cmd_file'] = '%s/image_ev_then_pol.cmd' % self.script_dir
        ev_pol_lxl['ev_section_id'] = SPDB_EV_EV
        ev_pol_lxl['pol_section_id'] = SPDB_EV_POL
        ev_pol_lxl['setup_scan'] = self.setupScan
        ev_pol_lxl['ev_scan'] = self._scan4
        ev_pol_lxl['pol_scan'] = self._scan3
        ev_pol_lxl['y_scan'] = self._scan2
        ev_pol_lxl['x_scan'] = self._scan1
        ev_pol_lxl['xy_scan'] = None
        ev_pol_lxl['top_lvl_scan'] = self._scan4
        ev_pol_lxl['data_lvl_scan'] = self._scan2
        ev_pol_lxl['btm_lvl_scan'] = self._scan1
        #ev_pol_lxl['on_counter_changed'] = self.on_sample_scan_counter_changed
        ev_pol_lxl['on_counter_changed'] = self.on_coarse_sample_scan_counter_changed
        #        ev_pol_lxl['on_data_level_done'] = self.on_save_sample_image
        #ev_pol_lxl['on_data_level_done'] = self.on_done_save_jpg_and_tmp_file
        ev_pol_lxl['on_data_level_done'] = self.on_done_save_jpg_and_tmp_file
        ev_pol_lxl['on_abort_scan'] = self.on_abort_scan
        ev_pol_lxl['on_scan_done'] = self.chk_for_more_evregions
        ev_pol_lxl['on_dev_cfg'] = self.on_this_dev_cfg
        ev_pol_lxl['scanlist'] = [self._scan1, self._scan2, self._scan3, self._scan4]

        pol_ev_lxl = {}
        pol_ev_lxl['cmd_file'] = '%s/image_pol_then_ev.cmd' % self.script_dir
        pol_ev_lxl['pol_section_id'] = SPDB_EV_POL
        pol_ev_lxl['ev_section_id'] = SPDB_EV_EV
        pol_ev_lxl['setup_scan'] = self.setupScan
        pol_ev_lxl['pol_scan'] = self._scan4
        pol_ev_lxl['ev_scan'] = self._scan3
        pol_ev_lxl['y_scan'] = self._scan2
        pol_ev_lxl['x_scan'] = self._scan1
        pol_ev_lxl['xy_scan'] = None
        pol_ev_lxl['top_lvl_scan'] = self._scan4
        pol_ev_lxl['data_lvl_scan'] = self._scan2
        pol_ev_lxl['btm_lvl_scan'] = self._scan1
        pol_ev_lxl['on_counter_changed'] = self.on_sample_scan_counter_changed
        pol_ev_lxl['on_data_level_done'] = self.on_done_save_jpg_and_tmp_file
        pol_ev_lxl['on_abort_scan'] = self.on_abort_scan
        pol_ev_lxl['on_scan_done'] = self.chk_for_more_evregions
        pol_ev_lxl['on_dev_cfg'] = self.on_this_dev_cfg
        pol_ev_lxl['modify_config'] = None
        pol_ev_lxl['scanlist'] = [self._scan1, self._scan2, self._scan3, self._scan4]

        # E712 Wavegenerator
        ev_pol_wg = {}
        ev_pol_wg['cmd_file'] = '%s/image_ev_then_pol_wg.cmd' % self.script_dir
        ev_pol_wg['ev_section_id'] = SPDB_EV_EV
        ev_pol_wg['pol_section_id'] = SPDB_EV_POL
        ev_pol_wg['setup_scan'] = self.setupScan
        ev_pol_wg['setup_scan'] = self._scan5
        ev_pol_wg['ev_scan'] = self._scan4
        ev_pol_wg['pol_scan'] = self._scan3
        #ev_pol_wg['y_scan'] = self._scan1
        #ev_pol_wg['x_scan'] = self._scan1
        ev_pol_wg['y_scan'] = None
        ev_pol_wg['x_scan'] = None
        ev_pol_wg['xy_scan'] = self._scan1
        ev_pol_wg['top_lvl_scan'] = self._scan5
        #ev_pol_wg['data_lvl_scan'] = self._scan2
        ev_pol_wg['data_lvl_scan'] = self._scan1
        ev_pol_wg['btm_lvl_scan'] = None
        #ev_pol_wg['on_counter_changed'] = self.on_sample_scan_counter_changed
        ev_pol_wg['on_counter_changed'] = self.on_sample_scan_counter_changed_hdw_accel
        #        ev_pol_lxl['on_data_level_done'] = self.on_save_sample_image
        #ev_pol_wg['on_data_level_done'] = self.on_done_save_jpg_and_tmp_file
        ev_pol_wg['on_data_level_done'] = self.on_single_image_scan_done

        ev_pol_wg['on_abort_scan'] = self.on_abort_scan
        #ev_pol_wg['on_scan_done'] = self.hdw_accel_chk_for_more_evregions
        ev_pol_wg['on_scan_done'] = self.on_scan_done_discon_sigs

        ev_pol_wg['on_dev_cfg'] = self.on_this_dev_cfg
        ev_pol_wg['modify_config'] = self.modify_config_for_hdw_accel
        #DEC 8 RUSS ev_pol_wg['modify_config'] = None
        #ev_pol_wg['scanlist'] = [self._scan1, self._scan2, self._scan3, self._scan4]
        ev_pol_wg['scanlist'] = [self._scan1, self._scan2, self._scan4, self._scan5]

        pol_ev_wg = {}
        pol_ev_wg['cmd_file'] = '%s/image_pol_then_ev_wg.cmd' % self.script_dir
        pol_ev_wg['ev_section_id'] = SPDB_EV_EV
        pol_ev_wg['pol_section_id'] = SPDB_EV_POL
        pol_ev_wg['setup_scan'] = self.setupScan
        pol_ev_wg['pol_scan'] = self._scan3
        pol_ev_wg['ev_scan'] = self._scan2
        pol_ev_wg['y_scan'] = self._scan1
        pol_ev_wg['x_scan'] = self._scan1
        pol_ev_wg['xy_scan'] = None
        pol_ev_wg['top_lvl_scan'] = self._scan3
        pol_ev_wg['data_lvl_scan'] = self._scan2
        pol_ev_wg['btm_lvl_scan'] = self._scan1
        pol_ev_wg['on_counter_changed'] = self.on_sample_scan_counter_changed
        #        ev_pol_lxl['on_data_level_done'] = self.on_save_sample_image
        pol_ev_wg['on_data_level_done'] = self.on_done_save_jpg_and_tmp_file
        pol_ev_wg['on_abort_scan'] = self.on_abort_scan
        pol_ev_wg['on_scan_done'] = self.chk_for_more_evregions
        pol_ev_wg['on_dev_cfg'] = self.on_this_dev_cfg
        pol_ev_wg['modify_config'] = self.modify_config_for_hdw_accel
        pol_ev_wg['scanlist'] = [self._scan1, self._scan2, self._scan3]

        ev_pol_pxp = {}
        ev_pol_pxp['cmd_file'] = '%s/image_ev_then_pol_pxp.cmd' % self.script_dir
        ev_pol_pxp['ev_section_id'] = SPDB_EV_EV
        ev_pol_pxp['pol_section_id'] = SPDB_EV_POL
        ev_pol_pxp['setup_scan'] = self.setupScan
        ev_pol_pxp['ev_scan'] = self._scan3
        ev_pol_pxp['pol_scan'] = self._scan2
        ev_pol_pxp['xy_scan'] = self._scan1
        ev_pol_pxp['x_scan'] = None
        ev_pol_pxp['y_scan'] = None
        ev_pol_pxp['top_lvl_scan'] = self._scan3
        ev_pol_pxp['data_lvl_scan'] = self._scan1
        ev_pol_pxp['btm_lvl_scan'] = None
        ev_pol_pxp['on_counter_changed'] = self.on_sample_scan_counter_changed
        ev_pol_pxp['on_data_level_done'] = self.on_done_save_jpg_and_tmp_file
        ev_pol_pxp['on_abort_scan'] = self.on_abort_scan
        ev_pol_pxp['on_scan_done'] = self.chk_for_more_evregions
        ev_pol_pxp['on_dev_cfg'] = self.on_this_dev_cfg
        #DEC 8 ev_pol_pxp['modify_config'] = None
        ev_pol_pxp['modify_config'] = self.modify_config_for_hdw_accel
        ev_pol_pxp['scanlist'] = [self._scan1, self._scan2, self._scan3]

        ev_pol_pxp_2recs = {}
        ev_pol_pxp_2recs['cmd_file'] = '%s/image_evpol_pxp.cmd' % self.script_dir
        ev_pol_pxp_2recs['ev_section_id'] = SPDB_EV_EV
        ev_pol_pxp_2recs['pol_section_id'] = SPDB_EV_POL
        ev_pol_pxp_2recs['setup_scan'] = self.setupScan
        ev_pol_pxp_2recs['ev_scan'] = self._scan4
        ev_pol_pxp_2recs['pol_scan'] = self._scan3
        ev_pol_pxp_2recs['xy_scan'] = None
        ev_pol_pxp_2recs['y_scan'] = self._scan2
        ev_pol_pxp_2recs['x_scan'] = self._scan1
        ev_pol_pxp_2recs['top_lvl_scan'] = self._scan4
        ev_pol_pxp_2recs['data_lvl_scan'] = self._scan2
        ev_pol_pxp_2recs['btm_lvl_scan'] = self._scan1
        ev_pol_pxp_2recs['on_counter_changed'] = self.on_sample_scan_counter_changed
        ev_pol_pxp_2recs['on_data_level_done'] = self.on_done_save_jpg_and_tmp_file
        ev_pol_pxp_2recs['on_abort_scan'] = self.on_abort_scan
        ev_pol_pxp_2recs['on_scan_done'] = self.chk_for_more_evregions
        ev_pol_pxp_2recs['on_dev_cfg'] = self.on_this_dev_cfg
        ev_pol_pxp_2recs['modify_config'] = None
        ev_pol_pxp_2recs['scanlist'] = [self._scan1, self._scan2, self._scan3, self._scan4]

        pol_ev_pxp = {}
        pol_ev_pxp['cmd_file'] = '%s/image_polev_pxp.cmd' % self.script_dir
        pol_ev_pxp['pol_section_id'] = SPDB_EV_POL
        pol_ev_pxp['ev_section_id'] = SPDB_EV_EV
        pol_ev_pxp['setup_scan'] = self.setupScan
        pol_ev_pxp['pol_scan'] = self._scan3
        pol_ev_pxp['ev_scan'] = self._scan2
        pol_ev_pxp['xy_scan'] = self._scan1
        pol_ev_pxp['x_scan'] = None
        pol_ev_pxp['y_scan'] = None
        pol_ev_pxp['top_lvl_scan'] = self._scan3
        pol_ev_pxp['data_lvl_scan'] = self._scan1
        pol_ev_pxp['btm_lvl_scan'] = None
        pol_ev_pxp['on_counter_changed'] = self.on_sample_scan_counter_changed
        pol_ev_pxp['on_data_level_done'] = self.on_done_save_jpg_and_tmp_file
        pol_ev_pxp['on_abort_scan'] = self.on_abort_scan
        pol_ev_pxp['on_scan_done'] = self.chk_for_more_evregions
        pol_ev_pxp['on_dev_cfg'] = self.on_this_dev_cfg
        pol_ev_pxp['modify_config'] = None
        pol_ev_pxp['scanlist'] = [self._scan1, self._scan2, self._scan3]

        ev_pol_pnt_spec = {}
        ev_pol_pnt_spec['cmd_file'] = '%s/point_spec_V2.cmd' % self.script_dir
        ev_pol_pnt_spec['ev_section_id'] = SPDB_EV_EV
        ev_pol_pnt_spec['pol_section_id'] = SPDB_EV_POL
        ev_pol_pnt_spec['setup_scan'] = None
        ev_pol_pnt_spec['y_scan'] = None
        ev_pol_pnt_spec['x_scan'] = None
        ev_pol_pnt_spec['ev_scan'] = self._scan3
        ev_pol_pnt_spec['pol_scan'] = self._scan2
        ev_pol_pnt_spec['xy_scan'] = self._scan1
        ev_pol_pnt_spec['top_lvl_scan'] = self._scan3
        ev_pol_pnt_spec['data_lvl_scan'] = self._scan2
        ev_pol_pnt_spec['btm_lvl_scan'] = self._scan1
        ev_pol_pnt_spec['on_counter_changed'] = self.on_point_spec_scan_counter_changed
        ev_pol_pnt_spec['on_data_level_done'] = self.on_data_level_done
        ev_pol_pnt_spec['on_abort_scan'] = self.on_abort_scan
        ev_pol_pnt_spec['on_scan_done'] = self.chk_for_more_evregions
        ev_pol_pnt_spec['on_dev_cfg'] = self.on_this_dev_cfg
        ev_pol_pnt_spec['modify_config'] = None
        ev_pol_pnt_spec['scanlist'] = [self._scan1, self._scan2, self._scan3]

        goni_ev_pol_pnt_spec = {}
        goni_ev_pol_pnt_spec['cmd_file'] = '%s/goni_point_spec.cmd' % self.script_dir
        goni_ev_pol_pnt_spec['ev_section_id'] = SPDB_EV_EV
        goni_ev_pol_pnt_spec['pol_section_id'] = SPDB_EV_POL
        #goni_ev_pol_pnt_spec['setup_scan'] = self.setupScan
        goni_ev_pol_pnt_spec['setup_scan'] = self._scan4
        goni_ev_pol_pnt_spec['y_scan'] = None
        goni_ev_pol_pnt_spec['x_scan'] = None
        goni_ev_pol_pnt_spec['ev_scan'] = self._scan3
        goni_ev_pol_pnt_spec['pol_scan'] = self._scan2
        goni_ev_pol_pnt_spec['xy_scan'] = self._scan1
        goni_ev_pol_pnt_spec['top_lvl_scan'] = self._scan3
        goni_ev_pol_pnt_spec['data_lvl_scan'] = self._scan2
        goni_ev_pol_pnt_spec['btm_lvl_scan'] = self._scan1
        goni_ev_pol_pnt_spec['on_counter_changed'] = self.on_point_spec_scan_counter_changed
        goni_ev_pol_pnt_spec['on_data_level_done'] = self.on_data_level_done
        goni_ev_pol_pnt_spec['on_abort_scan'] = self.on_abort_scan
        goni_ev_pol_pnt_spec['on_scan_done'] = self.chk_for_more_evregions
        goni_ev_pol_pnt_spec['on_dev_cfg'] = self.on_this_dev_cfg
        goni_ev_pol_pnt_spec['modify_config'] = None
        goni_ev_pol_pnt_spec['scanlist'] = [self._scan1, self._scan2, self._scan3]

        pol_ev_pnt_spec = {}
        pol_ev_pnt_spec['cmd_file'] = '%s/pol_ev_pnt_spec.cmd' % self.script_dir
        pol_ev_pnt_spec['ev_section_id'] = SPDB_EV_EV
        pol_ev_pnt_spec['pol_section_id'] = SPDB_EV_POL
        pol_ev_pnt_spec['setup_scan'] = self.setupScan
        pol_ev_pnt_spec['y_scan'] = self._scan4
        pol_ev_pnt_spec['x_scan'] = self._scan3
        pol_ev_pnt_spec['pol_scan'] = self._scan2
        pol_ev_pnt_spec['ev_scan'] = self._scan1
        pol_ev_pnt_spec['xy_scan'] = None
        pol_ev_pnt_spec['top_lvl_scan'] = self._scan4
        pol_ev_pnt_spec['data_lvl_scan'] = self._scan2
        pol_ev_pnt_spec['btm_lvl_scan'] = self._scan1
        pol_ev_pnt_spec['on_counter_changed'] = self.on_point_spec_scan_counter_changed
        pol_ev_pnt_spec['on_data_level_done'] = self.on_data_level_done
        pol_ev_pnt_spec['on_abort_scan'] = self.on_abort_scan
        pol_ev_pnt_spec['on_scan_done'] = self.chk_for_more_evregions
        pol_ev_pnt_spec['on_dev_cfg'] = self.on_this_dev_cfg
        pol_ev_pnt_spec['modify_config'] = None
        pol_ev_pnt_spec['scanlist'] = [self._scan1, self._scan2, self._scan3, self._scan4]



        self.cmdfile_parms = {}
        self.cmdfile_parms['ev_pol_lxl'] = ev_pol_lxl
        self.cmdfile_parms['pol_ev_lxl'] = pol_ev_lxl
        self.cmdfile_parms['ev_pol_pxp'] = ev_pol_pxp
        self.cmdfile_parms['pol_ev_pxp'] = pol_ev_pxp
        self.cmdfile_parms['ev_pol_pnt_spec'] = ev_pol_pnt_spec
        self.cmdfile_parms['pol_ev_pnt_spec'] = pol_ev_pnt_spec
        self.cmdfile_parms['goni_ev_pol_pnt_spec'] = goni_ev_pol_pnt_spec
        self.cmdfile_parms['ev_pol_pxp_2recs'] = ev_pol_pxp_2recs
        self.cmdfile_parms['ev_pol_wg'] = ev_pol_wg

        self.xyScan = self._scan1

        self.lxl_yScan = self._scan2
        self.lxl_xScan = self._scan1

        self.pxp_yScan = self._scan2
        self.pxp_xScan = self._scan1

        self.pnt_yScan = self._scan2
        self.pnt_xScan = self._scan1

    def on_this_scan_done(self):
        self.shutter.close()
        self.gate.stop()
        self.counter.stop()
        self.save_hdr()
        self.on_save_sample_image()

    def on_scan_done_discon_sigs(self):
        """
        on_scan_done(): fires when the top level scan is done, calls on_child_scan_done() if one has been
        configured by parent scan plugin

        :returns: None
        """

        if (self.signals_connected):
            # _logger.debug('BaseScan: on_scan_done_discon_sigs: emitted all_done sig')
            self.all_done.emit()
        else:
            _logger.debug('BaseScan: on_scan_done_discon_sigs: ELSE: sigs were not connected')
        # if(done):
        self.disconnect_signals()

    def on_single_image_scan_done(self):
        '''
        THis is called on_scan_done if there are only 1 images being acquired
        :return:
        '''
        self.shutter.close()
        self.gate.stop()
        self.counter.stop()

        #counter = self.counter_dct.keys()[0]
        counter = DNM_DEFAULT_COUNTER
        _sp_id = list(self.spid_data[counter].keys())[0]
        sp_db = self.sp_rois[_sp_id]
        self.data_dct = self.data_obj.get_data_dct()

        ado_obj = dct_get(sp_db, SPDB_ACTIVE_DATA_OBJECT)
        data_file_prfx = dct_get(ado_obj, ADO_CFG_PREFIX)
        datadir = dct_get(ado_obj, ADO_CFG_DATA_DIR)
        datafile_name = dct_get(ado_obj, ADO_CFG_DATA_FILE_NAME)
        thumb_name = dct_get(ado_obj, ADO_CFG_DATA_THUMB_NAME)

        if (not self.check_if_save_all_data(datafile_name)):
            return
        else:
            cur_idx = self.get_consecutive_scan_idx()
            _logger.debug('SampleImageWithE712Wavegen: on_single_image_scan_done() called [%d]' % cur_idx)

            _dct = self.get_img_idx_map(cur_idx)
            sp_id = _dct['sp_id']
            sp_idx = _dct['sp_idx']
            pol_idx = _dct['pol_idx']

            # for now just use the first counter
            #counter = self.counter_dct.keys()[0]
            counter = DNM_DEFAULT_COUNTER
            self._data = self.spid_data[counter][sp_id][pol_idx]

            # self.on_save_sample_image(_data=self._data)
            self.on_save_sample_image(_data=self.img_data[sp_id])

            _dct = self.get_snapshot_dict(cur_idx)
            self.main_obj.zmq_save_dict_to_tmp_file(_dct)

            #added this conditional when working on coarse scans
            # not sure why I would need this incremented for fine scans
            if(self.is_fine_scan):
                self.incr_consecutive_scan_idx()

            # THIS IS CRITICAL
            # now that we have all of the data from all of the detectors, tell the sscan rec to continue
            self._scan2.sscan.put('WAIT', 0)
            ###############################

            self.save_hdr(do_check=False)
            self.on_scan_done_discon_sigs()

    def on_sampleimage_data_level_done(self):
        # _logger.debug('SampleImageWithEnergySSCAN: SampleImageWithEnergySSCAN() called')
        self.on_save_sample_image()
        if (self.stack):
            self.update_data(stack=True)
        #self.incr_consecutive_scan_idx()


    def on_done_save_jpg_and_tmp_file(self):
        '''
        this is a handler for data_ready signal from SscanClass if there are more than one images being acquired
        the done here is for data_level_done, where we want to save a jpg, update the tmp file and continue IFF
        the current image idx does not qual the last image index
        :return:
        '''
        cur_idx = self.get_consecutive_scan_idx()

        _logger.debug('SampleImageWithE712Wavegen: on_done_save_jpg_and_tmp_file() called [%d]' % cur_idx)

        _dct = self.get_img_idx_map(cur_idx)
        sp_id = _dct['sp_id']
        sp_idx = _dct['sp_idx']
        pol_idx = _dct['pol_idx']

        # for now just use the first counter
        #counter = self.counter_dct.keys()[0]
        counter = DNM_DEFAULT_COUNTER
        self._data = self.spid_data[counter][sp_id][pol_idx]

        #self.on_save_sample_image(_data=self._data)
        self.on_save_sample_image(_data=self.img_data[sp_id])

        _dct = self.get_snapshot_dict(cur_idx)
        self.main_obj.zmq_save_dict_to_tmp_file(_dct)

        # added this conditional when working on coarse scans
        # not sure why I would need this incremented for fine scans
        if (self.is_fine_scan):
            self.incr_consecutive_scan_idx()

        # THIS IS CRITICAL
        # now that we have all of the data from all of the detectors, tell the sscan rec to continue
        self._scan2.sscan.put('WAIT', 0)
        ###############################
        if (cur_idx == self.numImages - 1):
            print('hey! I think this is the scan_done')
            self.shutter.close()
            self.on_scan_done_discon_sigs()
            self.save_hdr()

    def on_done_save_jpg_and_tmp_file_no_check_for_done(self):
        '''
        this is a handler for data_ready signal from SscanClass if there are more than one images being acquired
        the done here is for data_level_done, where we want to save a jpg, update the tmp file and continue IFF
        the current image idx does not qual the last image index
        :return:
        '''
        cur_idx = self.get_consecutive_scan_idx()

        _logger.debug('SampleImageWithE712Wavegen: on_done_save_jpg_and_tmp_file_no_check_for_done() called [%d]' % cur_idx)

        _dct = self.get_img_idx_map(cur_idx)
        sp_id = _dct['sp_id']
        sp_idx = _dct['sp_idx']
        pol_idx = _dct['pol_idx']

        # for now just use the first counter
        #counter = self.counter_dct.keys()[0]
        counter = DNM_DEFAULT_COUNTER
        self._data = self.spid_data[counter][sp_id][pol_idx]

        #self.on_save_sample_image(_data=self._data)
        self.on_save_sample_image(_data=self.img_data[sp_id])

        _dct = self.get_snapshot_dict(cur_idx)
        self.main_obj.zmq_save_dict_to_tmp_file(_dct)

        if (cur_idx < self.numImages - 1):
            self.incr_consecutive_scan_idx()

        # THIS IS CRITICAL
        # now that we have all of the data from all of the detectors, tell the sscan rec to continue
        self._scan2.sscan.put('WAIT', 0)


    def update_tmp_file(self):
        '''
                    this is a handler for data_ready signal from SscanClass
                    :return:

                    tmp_data_dct = {}
            tmp_data_dct['devs']['energy'] = 685.0
            tmp_data_dct['devs']['epu_gap'] = 235.8
            tmp_data_dct['devs']['epu_polarization'] = 1
            tmp_data_dct['devs']['epu_offset'] = 0.0
            tmp_data_dct['devs']['epu_angle'] = 0.0
            ...
            tmp_data_dct['dets']['counter0'] = [[356, 403 ...]]  # a numpy arrray of shape (100,100) for a 100x100 pt image
            tmp_data_dct['dets']['ring_current'] = 221.56  # a single value
            tmp_data_dct['dets']['ccd0'] = [[[356, 403 ...]]]  # a numpy arrray of shape (480,640) for a 640x480 pt image

        '''
        tmp_data_dct = {}

        # if (self.stack):
        cur_idx = self.get_consecutive_scan_idx()
        _logger.debug('SampleImageWithEnergySSCAN: update_tmp_file() called [%d]' % cur_idx)
        # print 'self.do_update_devs:'
        attr_dct = self.update_dev_data[cur_idx]
        print(attr_dct)

        # print self.img_idx_map
        # only support one detector for now
        for counter in list(self.counter_dct.keys()):
            # for each configured counter, get the data and send it to the dataIO
            _dct = self.get_img_idx_map(cur_idx)
            entry = _dct['entry']
            sp_id = _dct['sp_id']
            sp_idx = _dct['sp_idx']
            pol_idx = _dct['pol_idx']
            data = self.spid_data[counter][sp_id][pol_idx]
            self.hdr.update_tmp_data(cur_idx, tmp_data_dct)
        # if(not self.stack):
        #    self.save_hdr()





    def optimize_sample_line_scan(self):
        '''
        To be implemented by the inheriting class
        This function is meant to retrieve from the ini file the section for its scan and set any PDLY's
        and any other settings required to optimize the scan for speed.
        Typically this is used by the scans that move the fine piezo stages as their status response can greatly
        mprove the performance if it is optimized.

        appConfig.get_value('SAMPLE_IMAGE', 'whatever')
        c_scan1_pdly=0.0
        c_scan2_pdly=0.0
        f_scan2_pdly=0.0
        f_scan1_pdly=0.15
        # force done values are: 0=NORMAL, 1=FORCED, 2=INTERNAL_TIMED
        f_fx_force_done=2
        f_fy_force_done=1
        '''
        appConfig.update()
        c_scan1_pdly = float(appConfig.get_value('SAMPLE_IMAGE_LXL', 'c_scan1_pdly'))
        c_scan2_pdly = float(appConfig.get_value('SAMPLE_IMAGE_LXL', 'c_scan2_pdly'))
        f_scan1_pdly = float(appConfig.get_value('SAMPLE_IMAGE_LXL', 'f_scan1_pdly'))
        f_scan2_pdly = float(appConfig.get_value('SAMPLE_IMAGE_LXL', 'f_scan2_pdly'))
        c_fx_force_done = float(appConfig.get_value('SAMPLE_IMAGE_LXL', 'c_fx_force_done'))
        c_fy_force_done = float(appConfig.get_value('SAMPLE_IMAGE_LXL', 'c_fy_force_done'))
        f_fx_force_done = float(appConfig.get_value('SAMPLE_IMAGE_LXL', 'f_fx_force_done'))
        f_fy_force_done = float(appConfig.get_value('SAMPLE_IMAGE_LXL', 'f_fy_force_done'))
        fx_done = MAIN_OBJ.device(DNM_FX_FORCE_DONE)
        fy_done = MAIN_OBJ.device(DNM_FY_FORCE_DONE)

        if (self.x_roi[SCAN_RES] == 'COARSE'):
            self.xScan.put('PDLY', c_scan1_pdly)
            fx_done.put(c_fx_force_done)
        else:
            self.xScan.put('PDLY', f_scan1_pdly)
            fx_done.put(f_fx_force_done)

        if (self.y_roi[SCAN_RES] == 'COARSE'):
            self.yScan.put('PDLY', c_scan2_pdly)
            fy_done.put(c_fy_force_done)
        else:
            self.yScan.put('PDLY', f_scan2_pdly)
            fy_done.put(f_fy_force_done)

    def optimize_sample_point_scan(self):
        '''
        To be implemented by the inheriting class
        This function is meant to retrieve from the ini file the section for its scan and set any PDLY's
        and any other settings required to optimize the scan for speed.
        Typically this is used by the scans that move the fine piezo stages as their status response can greatly
        mprove the performance if it is optimized.

        appConfig.get_value('SAMPLE_IMAGE', 'whatever')
        c_scan1_pdly=0.0
        c_scan2_pdly=0.0
        f_scan2_pdly=0.0
        f_scan1_pdly=0.15
        # force done values are: 0=NORMAL, 1=FORCED, 2=INTERNAL_TIMED
        f_fx_force_done=2
        f_fy_force_done=1
        '''
        appConfig.update()
        c_scan1_pdly = float(appConfig.get_value('SAMPLE_IMAGE_PXP', 'c_scan1_pdly'))
        c_scan2_pdly = float(appConfig.get_value('SAMPLE_IMAGE_PXP', 'c_scan2_pdly'))
        f_scan1_pdly = float(appConfig.get_value('SAMPLE_IMAGE_PXP', 'f_scan1_pdly'))
        f_scan2_pdly = float(appConfig.get_value('SAMPLE_IMAGE_PXP', 'f_scan2_pdly'))
        c_fx_force_done = float(appConfig.get_value('SAMPLE_IMAGE_PXP', 'c_fx_force_done'))
        c_fy_force_done = float(appConfig.get_value('SAMPLE_IMAGE_PXP', 'c_fy_force_done'))
        f_fx_force_done = float(appConfig.get_value('SAMPLE_IMAGE_PXP', 'f_fx_force_done'))
        f_fy_force_done = float(appConfig.get_value('SAMPLE_IMAGE_PXP', 'f_fy_force_done'))
        fx_done = MAIN_OBJ.device(DNM_FX_FORCE_DONE)
        fy_done = MAIN_OBJ.device(DNM_FY_FORCE_DONE)

        if (self.x_roi[SCAN_RES] == 'COARSE'):
            # self.xyScan.put('PDLY', c_scan1_pdly)
            self.xScan.put('PDLY', c_scan1_pdly)
            fx_done.put(c_fx_force_done)
        else:
            # self.xyScan.put('PDLY', f_scan1_pdly)
            self.xScan.put('PDLY', f_scan1_pdly)
            fx_done.put(f_fx_force_done)

        if (self.y_roi[SCAN_RES] == 'COARSE'):
            self.yScan.put('PDLY', c_scan2_pdly)
            fy_done.put(c_fy_force_done)
        else:
            self.yScan.put('PDLY', f_scan2_pdly)
            fy_done.put(f_fy_force_done)

    def optimize_sample_pointspec_scan(self):
        '''
        To be implemented by the inheriting class
        This function is meant to retrieve from the ini file the section for its scan and set any PDLY's
        and any other settings required to optimize the scan for speed.
        Typically this is used by the scans that move the fine piezo stages as their status response can greatly
        mprove the performance if it is optimized.

        appConfig.get_value('SAMPLE_IMAGE', 'whatever')
        c_scan1_pdly=0.0
        c_scan2_pdly=0.0
        f_scan2_pdly=0.0
        f_scan1_pdly=0.15
        # force done values are: 0=NORMAL, 1=FORCED, 2=INTERNAL_TIMED
        f_fx_force_done=2
        f_fy_force_done=1
        '''
        appConfig.update()
        c_scan1_pdly = float(appConfig.get_value('SAMPLE_POINT_SPEC_SCAN', 'c_scan1_pdly'))
        c_scan2_pdly = float(appConfig.get_value('SAMPLE_POINT_SPEC_SCAN', 'c_scan2_pdly'))
        f_scan1_pdly = float(appConfig.get_value('SAMPLE_POINT_SPEC_SCAN', 'f_scan1_pdly'))
        f_scan2_pdly = float(appConfig.get_value('SAMPLE_POINT_SPEC_SCAN', 'f_scan2_pdly'))
        c_fx_force_done = float(appConfig.get_value('SAMPLE_POINT_SPEC_SCAN', 'c_fx_force_done'))
        c_fy_force_done = float(appConfig.get_value('SAMPLE_POINT_SPEC_SCAN', 'c_fy_force_done'))
        f_fx_force_done = float(appConfig.get_value('SAMPLE_POINT_SPEC_SCAN', 'f_fx_force_done'))
        f_fy_force_done = float(appConfig.get_value('SAMPLE_POINT_SPEC_SCAN', 'f_fy_force_done'))
        fx_done = MAIN_OBJ.device(DNM_FX_FORCE_DONE)
        fy_done = MAIN_OBJ.device(DNM_FY_FORCE_DONE)

        if (self.x_roi[SCAN_RES] == 'COARSE'):
            self.xyScan.put('PDLY', c_scan1_pdly)
            fx_done.put(c_fx_force_done)
            fy_done.put(c_fy_force_done)
        else:
            self.xyScan.put('PDLY', f_scan1_pdly)
            fx_done.put(f_fx_force_done)
            fy_done.put(f_fy_force_done)


    def optimize_hdw_accel_scan(self):
        pass

    def on_abort_scan(self):
        """
        on_abort_scan(): description

        :returns: None
        """
        if (self.main_obj.device('Shutter').is_auto()):
            self.main_obj.device('Shutter').close()
        self._abort = True
        if(self.use_hdw_accel):
            #tell E712 wavegen to stop
            self.e712_wg.stop_wave_generator()


    def validate_scan_assignments(self):
        """ a simple checker to verify that the scans are assigned to the correct epics sscan records
        """

        pass_tst = True
        if (self.scan_type == scan_types.SAMPLE_POINT_SPECTRUM):
            if (self.evScan.get_name() != '%s:scan3' % self.scan_prefix):
                pass_tst = False
            if (self.polScan.get_name() != '%s:scan2' % self.scan_prefix):
                pass_tst = False
            if (self.xyScan.get_name() != '%s:scan1' % self.scan_prefix):
                pass_tst = False
        return (pass_tst)

    def configure(self, wdg_com, sp_id=0, ev_idx=0, line=True, block_disconnect_emit=False):
        """
        configure(): This is the configure routine that is required to be defined by every scan plugin. the main goal of the configure function is to
            - extract into member variables the scan param data from the wdg_com (widget communication) dict
            - configure the sample motors for the correct Mode for the upcoming scan
            - reset any relevant member variable counters
            - decide if it is a line by line, point by point or point spectrum scan
            - set the optimization function for this scan (which is used later to fine tune some key params of the sscan record before scan)
            - decide if this is a goniometer scan and set a flag accordingly
            - set the start/stop/npts etc fields of the relevant sscan records for a line or point scan by calling either:
                set_ImageLineScan_line_sscan_rec() or set_ImageLineScan_point_sscan_rec()
            - determine the positioners that will be used in this scan (they depend on the size of the scan range, coarse or fine etc)
            - call either config_for_goniometer_scan() or config_for_sample_holder_scan() depending on if a goniometer scan or not
            - create the numpy array in self.data by calling config_hdr_datarecorder()
            - then call final_setup() which must be called at the end of every configure() function

        :param wdg_com: wdg_com is a "widget Communication dictionary" and it is used to relay information to/from widgets regarding current regions of interest
        :type wdg_com: wdg_com is a dictionary comprised of 2 keys: WDGCOM_CMND and SPDB_SPATIAL_ROIS, both of which are strings defined in roi_dict_defs.py
                WDGCOM_CMND       : is a command that identifys what should be done with the rois listed in the next field
                SPDB_SPATIAL_ROIS : is a list of spatial roi's or spatial databases (sp_db)

        :param sp_id: sp_id is the "spatial ID" of the sp_db
        :type sp_id: integer

        :param ev_idx: ev_idx is the index into the e_rois[] list of energy regions of interest, this configure() function could be called again repeatedly if there are more than one
                energy regions of interest, this index is the index into that list, when the scan is first configured/called the index is always the first == 0
        :type ev_idx: integer

        :param line: line is a boolean flag indicating if the scan to be configured is a line by line scan or not
        :type line: bool

        :param block_disconnect_emit: because configure() can be called repeatedly by check_more_spatial_regions() I need to be able to control
                how the main GUI will react to a new scan being executed in succession, this flag if False will not blocking the emission of the 'disconnect' signals signal
                and if True it will block teh emission of the 'disconnect' that the main GUI is listening to
        :type block_disconnect_emit: bool

        :returns: None

        """
        _logger.info('\n\nSampleImageWithE712Wavegen: configuring sp_id [%d]' % sp_id)
        self.new_spatial_start_sent = False
        # initial setup and retrieval of common scan information
        self.set_spatial_id(sp_id)
        self.wdg_com = wdg_com
        self.sp_rois = wdg_com[WDGCOM_SPATIAL_ROIS]
        self.sp_ids = list(self.sp_rois.keys())
        self.sp_db = self.sp_rois[sp_id]
        self.scan_type = dct_get(self.sp_db, SPDB_SCAN_PLUGIN_TYPE)
        self.scan_sub_type = dct_get(self.sp_db, SPDB_SCAN_PLUGIN_SUBTYPE)
        self.sample_positioning_mode = MAIN_OBJ.get_sample_positioning_mode()
        self.sample_fine_positioning_mode = MAIN_OBJ.get_fine_sample_positioning_mode()

        self.update_roi_member_vars(self.sp_db)

        # test fix
        # if (self.scan_type == scan_types.SAMPLE_POINT_SPECTRUM):
        #     dct_put(self.sp_db, SPDB_ZENABLED, False)
        #     dct_put(self.sp_db, SPDB_ZZNPOINTS, False)

        #the wavegenerator does both axis in one sscan record by calling the wavegenerator to execute,
        # this is done in sscan2
        self.xyScan = self._scan2

        self.determine_scan_res()

        # dct_put(self.sp_db, SPDB_RECT, (self.x_roi[START], self.y_roi[START], self.x_roi[STOP], self.y_roi[STOP]))
        # the sample motors have different modes, make a call to handle that they are setup correctly for this scan
        self.configure_sample_motors_for_scan()

        if (ev_idx == 0):
            self.reset_evidx()
            self.reset_imgidx()
            self.reset_pnt_spec_spid_idx()
            self.final_data_dir = None
            self.update_dev_data = []

        if(len(self.sp_ids) > 1):
            self.is_multi_spatial = True
            #if multi spatial then just save everything without prompting
            self.set_save_all_data(True)
        else:
            self.is_multi_spatial = False
            self.set_save_all_data(False)

        # get the energy and EOU related setpoints
        e_roi = self.e_rois[ev_idx]
        self.setpointsDwell = dct_get(e_roi, DWELL)
        # self.setpointsPol = self.convert_polarity_points(dct_get(e_roi, 'EPU_POL_PNTS'))
        self.setpointsPol = dct_get(e_roi, EPU_POL_PNTS)
        self.setpointsOff = dct_get(e_roi, EPU_OFF_PNTS)
        self.setpointsAngle = dct_get(e_roi, EPU_ANG_PNTS)
        self.ev_pol_order = dct_get(e_roi, EV_POL_ORDER)

        sps = dct_get(self.wdg_com, SPDB_SINGLE_LST_SP_ROIS)
        evs = dct_get(self.wdg_com, SPDB_SINGLE_LST_EV_ROIS)
        pols = dct_get(self.wdg_com, SPDB_SINGLE_LST_POL_ROIS)
        dwells = dct_get(self.wdg_com, SPDB_SINGLE_LST_DWELLS)

        self.use_hdw_accel = dct_get(self.sp_db, SPDB_HDW_ACCEL_USE)

        ###################################
        #DEC 8, 2017: for now FORCE THIS to BE FINE SCAN
        self.is_fine_scan = True
        dct_put(self.sp_db, SPDB_XSCAN_RES, FINE)
        ####################################


        #override
        if(not self.is_fine_scan):
            #coarse scan so turn hdw accel flag off
            self.use_hdw_accel = False

        if(self.use_hdw_accel):
            self.save_hdr = self.hdw_accel_save_hdr

            #set the DDL flags
            if(dct_get(self.sp_db, SPDB_HDW_ACCEL_AUTO_DDL)):
                self.x_auto_ddl = True
                self.x_use_reinit_ddl = False
            else:
                #Reinit DDL for the current scan
                self.x_auto_ddl = False
                self.x_use_reinit_ddl = True

        # setup some convienience member variables
        self.dwell = e_roi[DWELL]
        self.numX = int(self.x_roi[NPOINTS])
        self.numY = int(self.y_roi[NPOINTS])
        self.numZX = int(self.zx_roi[NPOINTS])
        self.numZY = int(self.zy_roi[NPOINTS])
        self.numEPU = len(self.setpointsPol)
        # self.numE = self.sp_db[SPDB_EV_NPOINTS] * len(self.setpointsPol)
        self.numE = int(self.sp_db[SPDB_EV_NPOINTS])
        self.numSPIDS = len(self.sp_rois)

        if (self.scan_type != scan_types.SAMPLE_POINT_SPECTRUM):
            self.numImages = int(self.sp_db[SPDB_EV_NPOINTS] * self.numEPU * self.numSPIDS)
        else:
            # is a sample point spectrum
            self.numImages = 1

        # set some flags that are used elsewhere
        if (self.numImages > 1):
            self.stack = True
        else:
            self.stack = False

        self.is_lxl = False
        self.is_pxp = False
        self.is_point_spec = False
        self.file_saved = False
        self.sim_point = 0

        if ((self.scan_type == scan_types.SAMPLE_IMAGE) or (self.scan_type == scan_types.SAMPLE_IMAGE_STACK)):
            if (self.scan_sub_type == scan_sub_types.LINE_UNIDIR):
                # LINE_UNIDIR
                self.is_lxl = True
            else:
                # POINT_BY_POINT
                self.is_pxp = True

        elif (self.scan_type == scan_types.SAMPLE_POINT_SPECTRUM):
            self.is_point_spec = True

        else:
            _logger.error('SampleImageWithEnergySSCAN: unable to determine scan type [%d]' % self.scan_type)
            return

        # users can request that the the ev and polarity portions of the scan can be executed in different orders
        # based on the order that requires a certain what for the sscan clases to be assigned in terms of their "level" so handle that in
        # another function
        # self.set_ev_pol_order(self.ev_pol_order)
        if (self.ev_pol_order == energy_scan_order_types.EV_THEN_POL):

            if (self.is_point_spec):
                if (self.sample_positioning_mode == sample_positioning_modes.GONIOMETER):
                    _id = 'goni_ev_pol_pnt_spec'
                else:
                    _id = 'ev_pol_pnt_spec'
            elif (self.is_lxl):
                if(self.use_hdw_accel):
                    #use the wavegen config
                    _id = 'ev_pol_wg'
                else:
                    _id = 'ev_pol_lxl'
            else:
                if (self.use_hdw_accel):
                    # use the wavegen config
                    _id = 'ev_pol_wg'
                else:
                    # _id = 'ev_pol_pxp'
                    _id = 'ev_pol_pxp_2recs'

        elif (self.ev_pol_order == energy_scan_order_types.POL_THEN_EV):
            if (self.is_point_spec):
                _id = 'pol_ev_pnt_spec'
            elif (self.is_lxl):
                if (self.use_hdw_accel):
                    # use the wavegen config
                    _id = 'pol_ev_wg'
                else:
                    _id = 'pol_ev_lxl'
            else:
                _id = 'pol_ev_pxp'

        else:
            _logger.error('unsupported ev polarity order [%d]' % self.ev_pol_order)
            return

        parms = self.cmdfile_parms[_id]

        #adjust params so that the data_done and scan_done signals work properly
        #only change the image params leave point spec as default
        if(not self.is_point_spec):
            if(self.stack or (self.numSPIDS > 1)):
                if (self.is_fine_scan):
                    parms['on_data_level_done'] = self.on_done_save_jpg_and_tmp_file
                    parms['on_scan_done'] = self.on_single_image_scan_done
                else:
                    # coarse scan, dont change defaults
                    parms['on_data_level_done'] = self.on_done_save_jpg_and_tmp_file_no_check_for_done
                    parms['on_scan_done'] = self.chk_for_more_evregions
            else:
                if(self.is_fine_scan):
                    #single image scan
                    parms['on_data_level_done'] = self.on_single_image_scan_done
                    #parms['on_scan_done'] = self.on_scan_done_discon_sigs
                    parms['on_scan_done'] = None
                else:
                    #coarse scan, dont change defaults
                    parms['on_data_level_done'] = self.on_single_image_scan_done
                    #parms['on_data_level_done'] = self.save_hdr
                    #parms['on_data_level_done'] = self.chk_for_more_evregions
                    #parms['on_scan_done'] = self.chk_for_more_evregions
                    parms['on_scan_done'] = None


        self.set_cmdfile_params(parms)

        if (not self.validate_scan_assignments()):
            _logger.error('Scans are not correctly assigned')
            return

        # cause the low level sscan records to clear their previous values and reload their common settings
        #self.setupScan.reload_base_scan_config()
        self.reload_base_scan_config()

        # set the function that will be called to make fine adjustments to the scan performance before scan starts
        # these optimization values are taken dynamically from tehj stxmMain.ini file so that they can be tested without restarting pySTXM

        # reset to the default then decide if to change it
        self.set_optimize_scan_func(None)

        if (self.use_hdw_accel):
            self.set_optimize_scan_func(self.optimize_hdw_accel_scan)

        elif((self.scan_type == scan_types.SAMPLE_IMAGE) or (self.scan_type == scan_types.SAMPLE_IMAGE_STACK)):
            if (self.scan_sub_type == scan_sub_types.LINE_UNIDIR):
                # LINE_UNIDIR
                # if(self.sample_positioning_mode == sample_positioning_modes.GONIOMETER):
                #    self.set_optimize_scan_func(self.optimize_goni_scan)
                # else:
                self.set_optimize_scan_func(self.optimize_sample_line_scan)
            else:
                # POINT_BY_POINT
                self.set_optimize_scan_func(self.optimize_sample_point_scan)

        elif (self.scan_type == scan_types.SAMPLE_POINT_SPECTRUM):
            # self.pdlys = {'scan2': 0.05, 'scan1': 0.05}
            self.set_optimize_scan_func(self.optimize_sample_pointspec_scan)

        else:
            _logger.error(
                'SampleImageWithEnergySSCAN: set optimize:  unable to determine scan type [%d]' % self.scan_type)
            return

        if (self.sample_positioning_mode == sample_positioning_modes.GONIOMETER):
            zp_scan = True
        else:
            zp_scan = False
            # determine and setup for line or point by point
        if (self.is_lxl):
            if (self.use_hdw_accel):
                #self.set_ImageLineScan_use_hdw_accel_sscan_rec(self.sp_db, e_roi, zp_scan)
                self.set_ImageLineScan_use_hdw_accel_sscan_rec(self.sp_db, e_roi, zp_scan, single_lsts={'sps':sps, 'evs':evs, 'pols':pols, 'dwells':dwells})
            else:
                self.set_ImageLineScan_line_sscan_rec(self.sp_db, e_roi, zp_scan)
        else:
            if (self.is_point_spec):
                self.set_sample_point_spec_sscan_rec(self.sp_db, e_roi, zp_scan)
            else:
                if (self.use_hdw_accel):
                    #self.set_ImageLineScan_use_hdw_accel_sscan_rec(self.sp_db, e_roi, zp_scan)
                    self.set_ImageLineScan_use_hdw_accel_sscan_rec(self.sp_db, e_roi, zp_scan,
                                                                   single_lsts={'sps': sps, 'evs': evs, 'pols': pols,
                                                                                'dwells': dwells})
                else:
                    self.set_ImageLineScan_point_sscan_rec(self.sp_db, e_roi, zp_scan)

        self.ttl_pnts = 0
        # reset signals so we can start clean
        if (block_disconnect_emit):
            self.blockSignals(True)

        self.disconnect_signals()

        if (block_disconnect_emit):
            self.blockSignals(False)

        # depending on the scan size the positioners used in the scan will be different, use a singe
        # function to find out which we are to use and return those names in a dct
        dct = self.determine_samplexy_posner_pvs()

        # depending on the current samplpositioning_mode perform a different configuration
        if (self.sample_positioning_mode == sample_positioning_modes.GONIOMETER):
            if(self.use_hdw_accel):
                self.config_for_goniometer_scan_hdw_accel(dct)
            else:
                self.config_for_goniometer_scan(dct)

        else:
            if(self.is_fine_scan):
                #FINE
                if (self.use_hdw_accel):
                    if(self.sample_fine_positioning_mode == sample_fine_positioning_modes.ZONEPLATE):
                        self.configure_for_zxzy_fine_scan_hdw_accel(dct)
                    else:
                        self.configure_for_samplefxfy_fine_scan_hdw_accel(dct)
                else:
                    self.config_for_sample_holder_scan(dct)
            else:
                #COARSE
                self.configure_for_coarse_scan(dct)

        self.final_data_dir = self.config_hdr_datarecorder(self.stack, self.final_data_dir)
        # self.stack_scan = stack

        # make sure OSA XY is in its center
        self.move_osaxy_to_its_center()

        # THIS must be the last call
        self.finish_setup()
        self.new_spatial_start.emit(sp_id)



    def configure_for_coarse_scan(self, dct):
        '''
        if this is executed the assumption is that the zoneplate will be stationary and the Fx Fy stages will be off
        because the scan will be accomplished by moving the sample with the coarse motors only
        :return:
        '''
        self.xScan = self._scan1
        self.yScan = self._scan2
        self.xyScan = None
        self.config_for_sample_holder_scan(dct)


    def configure_for_zxzy_fine_scan_hdw_accel(self, dct, is_focus=False):
        """
        For a goniometer scan this will always be a fine scan of max range 100x100um (actually less)
        and the sequence to configure a scan is to position the goniometer at teh center of the scan everytime
        and set the +/- scan range to be about Zoneplate XY center (0,0)

        Need to take into account that this could be a LxL scan (uses xScan, yScan, zScan) or a PxP (uses xyScan, zScan)

        Because this scan uses the waveform generator on the E712 there are no positioners set for X and Y scan only the
        triggering of the waveform generator, will still need to do something so that save_hdr has something to get data
        from, not sure how to handle this yet.

        """
        ### VERY IMPORTANT the current PID tune for ZX is based on a velo (SLew Rate) of 1,000,000
        self.main_obj.device(DNM_ZONEPLATE_X).put('velocity', 1000000.0)
        self.main_obj.device(DNM_ZONEPLATE_Y).put('velocity', 1000000.0)

        self.set_config_devices_func(self.on_this_dev_cfg)

        self.sample_mtrx = self.sample_finex = self.main_obj.device(DNM_ZONEPLATE_X)
        self.sample_mtry = self.sample_finey = self.main_obj.device(DNM_ZONEPLATE_Y)

        # move Gx and Gy to center of scan, is it within a um?
        if (self.zx_roi[CENTER] != 0.0):
            # zx is moving to scan center
            pass
        else:
            # Gx is moving to scan center nd zx is centered around 0, so move Gx to scan center
            self.main_obj.device(dct['cx_name']).put('user_setpoint', self.gx_roi[CENTER])

        # if(self.is_within_dband( gy_mtr.get_position(), self.gy_roi[CENTER], 15.0)):
        if (self.zy_roi[CENTER] != 0.0):
            # zy is moving to scan center
            pass
        else:
            # Gy is moving to scan center nd zy is centered around 0, so move Gy to scan center
            self.main_obj.device(dct['cy_name']).put('user_setpoint', self.gy_roi[CENTER])

        # config the sscan that makes sure to move goni xy and osa xy to the correct position for scan
        # the setupScan will be executed as the top level but not monitored
        self.num_points = self.numY

        self.sample_mtrx.put('Mode', 0)

        #setup the E712 wavtable's and other relevant params
        #d=DEC 8 self.modify_config_for_hdw_accel()

    def configure_for_samplefxfy_fine_scan_hdw_accel(self, dct):
        '''
        if this is executed the assumption is that the the scan will be a sampleFx Fy fine scan, it should make sure the
        SampleX and SampleY stages are in their start positions the wavegen tables and set the starting offset (which
        will be the big difference)
        :return:
        '''
        """
                For a fine scan this will always be a scan of max range 100x100um (actually less)
                and the sequence to configure a scan is to position the goniometer at teh center of the scan everytime
                and set the +/- scan range to be about Fine XY center (0,0)

                Need to take into account that this could be a LxL scan (uses xScan, yScan, zScan) or a PxP (uses xyScan, zScan)

                Because this scan uses the waveform generator on the E712 there are no positioners set for X and Y scan only the
                triggering of the waveform generator.

                """
        ### VERY IMPORTANT the current PID tune for ZX is based on a velo (SLew Rate) of 1,000,000
        # must be FxFy
        self.main_obj.device(DNM_SAMPLE_FINE_X).put('ServoPower', 1)
        self.main_obj.device(DNM_SAMPLE_FINE_Y).put('ServoPower', 1)

        #self.main_obj.device(DNM_SAMPLE_FINE_X).put('velocity', 1000000.0)
        #self.main_obj.device(DNM_SAMPLE_FINE_Y).put('velocity', 1000000.0)

        self.main_obj.device(DNM_SAMPLE_X).put('velocity', 1000000.0)
        self.main_obj.device(DNM_SAMPLE_Y).put('velocity', 1000000.0)

        self.setupScan.set_positioner(1, self.main_obj.device(DNM_SAMPLE_X))
        self.setupScan.set_positioner(2, self.main_obj.device(DNM_SAMPLE_Y))

        #these are the SampleX SampleY motors
        cx_mtr = self.main_obj.device(dct['cx_name'])
        cy_mtr = self.main_obj.device(dct['cy_name'])

        cx_mtr.put('Mode', 0)  # MODE_NORMAL
        cy_mtr.put('Mode', 0)  # MODE_NORMAL

        self.set_config_devices_func(self.on_this_dev_cfg)
        self.sample_mtrx = self.sample_finex = self.main_obj.device(DNM_SAMPLE_FINE_X)
        self.sample_mtry = self.sample_finey = self.main_obj.device(DNM_SAMPLE_FINE_Y)

        # move Gx and Gy to center of scan, is it within a um?
        # Sx is moving to scan center nd fx is centered around 0, so move Sx to scan center
        cx_mtr.move(self.x_roi[CENTER])
        #self.main_obj.device(dct['cx_name']).put('user_setpoint', self.x_roi[CENTER])

        # if(self.is_within_dband( gy_mtr.get_position(), self.gy_roi[CENTER], 15.0)):
        # Sy is moving to scan center nd fy is centered around 0, so move Sy to scan center
        #self.main_obj.device(dct['cy_name']).put('user_setpoint', self.gy_roi[CENTER])
        cy_mtr.move(self.y_roi[CENTER])

        # config the sscan that makes sure to move goni xy and osa xy to the correct position for scan
        # the setupScan will be executed as the top level but not monitored
        self.num_points = self.numY

        # setup the E712 wavtable's and other relevant params
        #DEC 8 self.modify_config_for_hdw_accel()

    def on_this_dev_cfg(self):
        """
        on_this_dev_cfg(): description

        :returns: None
        this is an API method to configure the gate, shutter and counter devices for this scan
        """
        # if((self.is_pxp) or (self.is_point_spec)):
        if (self.is_pxp):
            if(self.use_hdw_accel):
                set_devices_for_e712_wavegen_point_scan(self.scan_type, self.dwell, self.numX, self.counter, numE=self.numE)
                #set_devices_for_e712_wavegen_point_scan(scan_type, dwell, numX, counter, numE=0)
            else:
                # set_devices_for_point_scan(self.roi, self.gate, self.counter, self.shutter)
                set_devices_for_point_scan(self.scan_type, self.dwell, self.numE, self.numX, self.gate, self.counter,
                                       self.shutter)
        elif (self.is_point_spec):
            # set_devices_for_point_scan(self.roi, self.gate, self.counter, self.shutter)
            # numE is used for the number of points for a point spec, here we dont want to use Row etc because
            # we handle that here on hte counter handler for point spec
            if(self.use_hdw_accel):
                #set_devices_for_e712_wavegen_point_scan(self.scan_type, self.dwell, self.numE, self.numX, self.counter)
                set_devices_for_e712_wavegen_point_scan(self.scan_type, self.dwell, 99999999, self.numX, self.counter)
            else:
                set_devices_for_point_scan(self.scan_type, self.dwell, 99999999, self.numX, self.gate, self.counter,
                                       self.shutter)
        else:
            if(self.use_hdw_accel):
                set_devices_for_e712_wavegen_line_scan(self.dwell, self.numX, self.gate, self.counter)
            else:
                set_devices_for_line_scan(self.dwell, self.numX, self.gate, self.counter, self.shutter)

    def on_point_spec_scan_counter_changed(self, row, data):
        """
        on_sample_scan_counter_changed(): Used by SampleImageWithEnergySSCAN
        :param row: row
        :type row: row integer

        :param data: data is a tuple of 2 values (x, counts)
        :type data: data tuple

        :returns: None

                The on counter_changed slot will take data cquired by line and point scans but it must treat each differently.
                The point scan still arrives as a one demensiotnal array but there are only 3 elements, data[row, point, value].
                The point scan has been programmed to acquire num_x_points + 1 so that the counter can increment the row value, thus this
                slot during a point scan will receive a point+1 and in that case it should be ignored.

                LIne scan data arrives in the form data[row, < number of x points of values >]

                This slot has to handle

        """
        num_spids = len(self.sp_rois)
        sp_cntr = self.get_pnt_spec_spid_idx()
        # print point_val[0:10]
        point_val = data[1]
        if (self.ttl_pnts < self.numE):
            # ev = self.evScan.P1.get('RBV')
            ev = MAIN_OBJ.device(DNM_ENERGY).get_position()
            # print 'pointscan_counter_changed: on_counter_changed:[%d] x=%.2f point_val=%d len(data)=%d' % (self.ttl_pnts, ev, point_val, len(self.data))

            # self.data[self.ttl_pnts, 0] = point_val
            self.data[0, sp_cntr, self.ttl_pnts] = point_val
            #             dct = {}
            #             dct['sp_id'] = self.sp_ids[sp_cntr]
            #             dct['img_idx'] = 0
            #             dct['row'] = sp_cntr
            #             dct['col'] = ev
            #             dct['val'] = point_val

            dct = self.init_counter_to_plotter_com_dct(make_counter_to_plotter_com_dct())
            dct[CNTR2PLOT_SP_ID] = self.sp_ids[sp_cntr]
            dct[CNTR2PLOT_ROW] = sp_cntr
            dct[CNTR2PLOT_COL] = ev
            dct[CNTR2PLOT_VAL] = point_val

            # print 'pointscan_counter_changed: on_counter_changed: num_spids = %d' % num_spids
            print('pointscan_counter_changed: on_counter_changed: [%d] row=%.2f col=%d val=%d' % (self.ttl_pnts, sp_cntr, self.ttl_pnts, point_val))

            # self.sigs.changed.emit(int(0), (ev, y))
            self.sigs.changed.emit(dct)
            # self.ttl_pnts += 1

            prog = float(float(self.ttl_pnts + 0.75) / float(self.numE)) * 100.0
            prog_dct = make_progress_dict(sp_id=dct[CNTR2PLOT_SP_ID], percent=prog)
            self.low_level_progress.emit(prog_dct)

            self.incr_pnt_spec_spid_idx()

            if (self.get_pnt_spec_spid_idx() >= num_spids):
                # print 'resetting get_spec_spid_idx() [%d]' % self.get_pnt_spec_spid_idx()
                self.reset_pnt_spec_spid_idx()
                self.ttl_pnts += 1

    # def set_ImageLineScan_use_hdw_accel_sscan_rec(self, sp_roi, e_roi, zp_scan=False):
    #     """
    #     set_ImageLineScan_line_sscan_rec(): description
    # 
    #     :param sp_roi: sp_roi description
    #     :type sp_roi: sp_roi type
    # 
    #     :param e_roi: e_roi description
    #     :type e_roi: e_roi type
    # 
    #     :returns: None
    #     """
    #     # pol
    #     self.polScan.put('NPTS', len(self.setpointsPol))
    #     self.polScan.put('P1PA', self.setpointsPol)
    #     self.polScan.put('P1SM', 1)  # table
    #     # off
    #     self.polScan.put('P2PA', self.setpointsOff)
    #     self.polScan.put('P2SM', 1)  # table
    #     # angle
    #     self.polScan.put('P3PA', self.setpointsAngle)
    #     self.polScan.put('P3SM', 1)  # table
    # 
    #     # EV
    #     self.evScan.put('NPTS', e_roi[NPOINTS])
    #     self.evScan.put('P1SP', e_roi[START])
    #     self.evScan.put('P1EP', e_roi[STOP])
    
    def set_ImageLineScan_use_hdw_accel_sscan_rec(self, sp_roi, e_roi, zp_scan=False, single_lsts={}):
        """
        set_ImageLineScan_line_sscan_rec(): description

        :param sp_roi: sp_roi description
        :type sp_roi: sp_roi type

        :param e_roi: e_roi description
        :type e_roi: e_roi type

        :returns: None
        """
        evs = single_lsts['evs']
        pols = single_lsts['pols']
        dwells = single_lsts['dwells']
        sps = single_lsts['sps']
        # pol
        self.polScan.put('NPTS', len(self.setpointsPol))
        self.polScan.put('P1PA', self.setpointsPol)
        self.polScan.put('P1SM', 1)  # table
        # off
        self.polScan.put('P2PA', self.setpointsOff)
        self.polScan.put('P2SM', 1)  # table
        # angle
        self.polScan.put('P3PA', self.setpointsAngle)
        self.polScan.put('P3SM', 1)  # table

        #     # EV
        #     self.evScan.put('NPTS', e_roi[NPOINTS])
        #     self.evScan.put('P1SP', e_roi[START])
        #     self.evScan.put('P1EP', e_roi[STOP])

        # EV
        #here write all energies to table of setpoints
        self.evScan.put('NPTS', len(evs))
        self.evScan.put('P1PA', evs)
        self.evScan.put('P1SM', 1)  # table

        #load the wavefr
        MAIN_OBJ.device('e712_dwells').put(dwells)
        

    # def set_ImageLineScan_point_use_hdw_accel_sscan_rec(self, sp_roi, e_roi, zp_scan=False):
    #     """
    #     set_ImageLineScan_line_sscan_rec(): description
    # 
    #     :param sp_roi: sp_roi description
    #     :type sp_roi: sp_roi type
    # 
    #     :param e_roi: e_roi description
    #     :type e_roi: e_roi type
    # 
    #     :returns: None
    #     """
    #     # XY
    #     # only 1 points because X is only calling IOCE712:ExecWavgen for an entire image
    #     self.xScan.put('NPTS', 1)
    # 
    #     # pol
    #     self.polScan.put('NPTS', len(self.setpointsPol))
    #     self.polScan.put('P1PA', self.setpointsPol)
    #     self.polScan.put('P1SM', 1)  # table
    #     # off
    #     self.polScan.put('P2PA', self.setpointsOff)
    #     self.polScan.put('P2SM', 1)  # table
    #     # angle
    #     self.polScan.put('P3PA', self.setpointsAngle)
    #     self.polScan.put('P3SM', 1)  # table
    # 
    #     # EV
    #     self.evScan.put('NPTS', e_roi[NPOINTS])
    #     self.evScan.put('P1SP', e_roi[START])
    #     self.evScan.put('P1EP', e_roi[STOP])

    def config_for_goniometer_scan_hdw_accel(self, dct, is_focus=False):
        """
        For a goniometer scan this will always be a fine scan of max range 100x100um (actually less)
        and the sequence to configure a scan is to position the goniometer at teh center of the scan everytime
        and set the +/- scan range to be about Zoneplate XY center (0,0)

        Need to take into account that this could be a LxL scan (uses xScan, yScan, zScan) or a PxP (uses xyScan, zScan)

        Because this scan uses the waveform generator on the E712 there are no positioners set for X and Y scan only the
        triggering of the waveform generator, will still need to do something so that save_hdr has something to get data
        from, not sure how to handle this yet.

        """
        ### VERY IMPORTANT the current PID tune for ZX is based on a velo (SLew Rate) of 1,000,000
        self.main_obj.device(DNM_ZONEPLATE_X).put('velocity', 1000000.0)
        self.main_obj.device(DNM_ZONEPLATE_Y).put('velocity', 1000000.0)

        self.setupScan.set_positioner(1, self.main_obj.device(DNM_GONI_X))
        self.setupScan.set_positioner(2, self.main_obj.device(DNM_GONI_Y))
        self.setupScan.set_positioner(3, self.main_obj.device(DNM_OSA_X))
        # self.setupScan.set_positioner(4,  self.main_obj.device(DNM_OSA_Y))

        gx_mtr = self.main_obj.device(dct['cx_name'])
        gy_mtr = self.main_obj.device(dct['cy_name'])

        self.set_config_devices_func(self.on_this_dev_cfg)

        self.sample_mtrx = self.sample_finex = self.main_obj.device(DNM_ZONEPLATE_X)
        self.sample_mtry = self.sample_finey = self.main_obj.device(DNM_ZONEPLATE_Y)

        # move Gx and Gy to center of scan, is it within a um?
        if (self.zx_roi[CENTER] != 0.0):
            # zx is moving to scan center
            pass
        else:
            # Gx is moving to scan center nd zx is centered around 0, so move Gx to scan center
            self.main_obj.device(dct['cx_name']).put('user_setpoint', self.gx_roi[CENTER])

        # if(self.is_within_dband( gy_mtr.get_position(), self.gy_roi[CENTER], 15.0)):
        if (self.zy_roi[CENTER] != 0.0):
            # zy is moving to scan center
            pass
        else:
            # Gy is moving to scan center nd zy is centered around 0, so move Gy to scan center
            self.main_obj.device(dct['cy_name']).put('user_setpoint', self.gy_roi[CENTER])

        # config the sscan that makes sure to move goni xy and osa xy to the correct position for scan
        # the setupScan will be executed as the top level but not monitored
        self.setupScan.put('NPTS', 1)
        self.setupScan.put('P1PV', '%s.VAL' % self.main_obj.device(DNM_GONI_X).get_name())
        self.setupScan.put('R1PV', '%s.RBV' % self.main_obj.device(DNM_GONI_X).get_name())
        self.setupScan.put('P1SP', self.gx_roi[CENTER])
        self.setupScan.put('P1EP', self.gx_roi[CENTER])


        self.setupScan.put('P2PV', '%s.VAL' % self.main_obj.device(DNM_GONI_Y).get_name())
        self.setupScan.put('R2PV', '%s.RBV' % self.main_obj.device(DNM_GONI_Y).get_name())
        self.setupScan.put('P2SP', self.gy_roi[CENTER])
        self.setupScan.put('P2EP', self.gy_roi[CENTER])


        self.setupScan.put('P3PV', '%s.VAL' % self.main_obj.device(DNM_OSA_X).get_name())
        self.setupScan.put('R3PV', '%s.RBV' % self.main_obj.device(DNM_OSA_X).get_name())
        self.setupScan.put('P3SP', self.ox_roi[CENTER])
        self.setupScan.put('P3EP', self.ox_roi[CENTER])

        self.num_points = self.numY

        self.sample_mtrx.put('Mode', 0)

        #setup the E712 wavtable's and other relevant params
        #DEC 8 self.modify_config_for_hdw_accel()

    def config_for_sample_holder_scan_hdw_accel(self, dct):
        """
        configure for using
        """
        # set the X Y positioners for the scan
        # if(hasattr(self,'xyScan')):
        # if(self.is_pxp and hasattr(self,'xyScan')):
        if ((self.is_point_spec or self.is_pxp) and (self.xyScan is not None)):
            self.xyScan.set_positioner(1, self.main_obj.device(dct['sx_name']))
            self.xyScan.set_positioner(2, self.main_obj.device(dct['sy_name']))

        else:

            self.xScan.set_positioner(1, self.main_obj.device(dct['sx_name']))
            self.yScan.set_positioner(1, self.main_obj.device(dct['sy_name']))

        self.set_config_devices_func(self.on_this_dev_cfg)

        self.sample_mtrx = self.main_obj.device(DNM_SAMPLE_X)
        self.sample_mtry = self.main_obj.device(DNM_SAMPLE_Y)
        self.sample_finex = self.main_obj.device(DNM_SAMPLE_FINE_X)
        self.sample_finey = self.main_obj.device(DNM_SAMPLE_FINE_Y)

        # setup X positioner
        self.sample_mtrx.put('Mode', MODE_SCAN_START)
        self.main_obj.device(dct['sx_name']).put('user_setpoint', dct['xstart'])
        _logger.info('Waiting for SampleX to move to start')
        self.confirm_stopped([self.sample_mtrx])

        # setup Y positioner
        self.sample_mtry.put('Mode', MODE_SCAN_START)
        self.main_obj.device(dct['sy_name']).put('user_setpoint', dct['ystart'])
        _logger.info('Waiting for SampleY to move to start')
        self.confirm_stopped([self.sample_mtry])

        # setup X
        if (self.is_pxp or self.is_point_spec):
            if (self.x_roi[SCAN_RES] == 'COARSE'):
                scan_velo = self.get_mtr_max_velo(self.xScan.P1)
            else:
                scan_velo = self.get_mtr_max_velo(self.main_obj.device(DNM_SAMPLE_FINE_X))

            # x needs one extra to switch the row
            npts = self.numX
            dwell = self.dwell
            accRange = 0
            deccRange = 0
            line = False
        else:
            _ev_idx = self.get_evidx()
            e_roi = self.e_rois[_ev_idx]
            vmax = self.get_mtr_max_velo(self.xScan.P1)
            # its not a point scan so determine the scan velo and accRange
            (scan_velo, npts, dwell) = ensure_valid_values(self.x_roi[START], self.x_roi[STOP], self.dwell,
                                                           self.numX, vmax, do_points=True)
            if (self.x_roi[SCAN_RES] == 'COARSE'):
                accRange = calc_accRange(dct['sx_name'], self.x_roi[SCAN_RES], self.x_roi[RANGE], scan_velo, dwell,
                                         accTime=0.04)
                deccRange = accRange
            else:
                appConfig.update()
                if (self.is_lxl):
                    section = 'SAMPLE_IMAGE_LXL'
                else:
                    section = 'SAMPLE_IMAGE_PXP'

                accRange = float(appConfig.get_value(section, 'f_acc_rng'))
                deccRange = float(appConfig.get_value(section, 'f_decc_rng'))

            # the number of points may have changed in order to satisfy the dwell the user wants
            # so update the number of X points and dwell
            # self.numX = npts
            # self.x_roi[NPOINTS] = npts

            line = True
            e_roi[DWELL] = dwell
            self.dwell = dwell

        print('accRange=%.2f um' % (accRange))
        print('deccRange=%.2f um' % (deccRange))

        # move X to start
        # self.sample_mtrx.put('Mode', MODE_SCAN_START)
        # self.sample_mtrx.put('Mode', MODE_NORMAL)
        if (self.is_lxl):
            # self.config_samplex_start_stop(dct['xpv'], self.x_roi[START], self.x_roi[STOP], self.numX, accRange=accRange, line=line)
            if (self.x_roi[SCAN_RES] == 'COARSE'):
                self.config_samplex_start_stop(dct['sample_pv_nm']['X'], self.x_roi[START], self.x_roi[STOP],
                                               self.numX, accRange=accRange, deccRange=deccRange, line=line)
            else:
                # if it is a fine scan then dont use the abstract motor for the actual scanning
                # because the status fbk timing is currently not stable
                self.config_samplex_start_stop(dct['fine_pv_nm']['X'], self.x_roi[START], self.x_roi[STOP],
                                               self.numX, accRange=accRange, deccRange=deccRange, line=line)

                # testing
                # self.sample_mtrx.put('Mode', MODE_MOVETO_SET_CPOS)
                # self.sample_mtrx.put('Mode', MODE_NORMAL)
                #         self.sample_mtrx.put('Mode', MODE_SCAN_START)
                #         #endtesting
                #         self.main_obj.device( dct['sx_name'] ).put('user_setpoint', dct['xstart'])

        self.set_x_scan_velo(scan_velo)
        # self.confirm_stopped([self.sample_mtrx, self.sample_mtry])

        self.num_points = self.numY

        # self.confirm_stopped(self.mtr_list)
        # set teh velocity in teh sscan rec for X
        if (self.is_pxp or self.is_point_spec):
            # force it to toggle, not sure why this doesnt just work
            if (self.x_roi[SCAN_RES] == 'COARSE'):
                self.sample_mtrx.put('Mode', MODE_COARSE)
            # self.xScan.put('BSPV', dct['sample_pv_nm']['X'] + '.VELO')
            # self.main_obj.device( DNM_CX_AUTO_DISABLE_POWER ).put(0) #disabled
            # self.set_sample_posner_mode(self.sample_mtrx, self.sample_finex, MODE_COARSE)


            else:
                self.sample_mtrx.put('Mode', MODE_POINT)
                # self.xScan.put('BSPV', dct['fine_pv_nm']['X'] + '.VELO')
            #                self.xScan.put('BSPV', dct['sample_pv_nm']['X'] + '.VELO')
            # self.main_obj.device( DNM_CX_AUTO_DISABLE_POWER ).put(1) #enabled
            # self.set_sample_posner_mode(self.sample_mtrx, self.sample_finex, MODE_POINT)

            if (self.y_roi[SCAN_RES] == 'COARSE'):
                # self.set_sample_posner_mode(self.sample_mtrx, self.sample_finex, MODE_COARSE)
                self.sample_mtry.put('Mode', MODE_COARSE)
            else:

                # self.set_sample_posner_mode(self.sample_mtrx, self.sample_finex, MODE_LINE_UNIDIR)
                # self.sample_mtry.put('Mode', MODE_NORMAL)
                self.sample_mtry.put('Mode', MODE_LINE_UNIDIR)

        else:
            # force it to toggle, not sure why this doesnt just work
            if (self.x_roi[SCAN_RES] == 'COARSE'):
                self.sample_mtrx.put('Mode', MODE_COARSE)
                self.xScan.put('P1PV', dct['coarse_pv_nm']['X'] + '.VAL')
                self.xScan.put('R1PV', dct['coarse_pv_nm']['X'] + '.RBV')
            # self.xScan.put('BSPV', dct['sample_pv_nm']['X'] + '.VELO')
            # self.main_obj.device( DNM_CX_AUTO_DISABLE_POWER ).put(0) #disabled
            # self.set_sample_posner_mode(self.sample_mtrx, self.sample_finex, MODE_COARSE)
            else:
                self.sample_mtrx.put('Mode', MODE_LINE_UNIDIR)
                self.xScan.put('P1PV', dct['fine_pv_nm']['X'] + '.VAL')
                self.xScan.put('R1PV', dct['fine_pv_nm']['X'] + '.RBV')
                # self.xScan.put('BSPV', dct['fine_pv_nm']['X'] + '.VELO')
            #                self.xScan.put('BSPV', dct['sample_pv_nm']['X'] + '.VELO')
            # self.xScan.put('BSPV', dct['fine_pv_nm']['X'] + '.VELO')

            # self.main_obj.device( DNM_CX_AUTO_DISABLE_POWER ).put(1) #enabled
            # self.set_sample_posner_mode(self.sample_mtrx, self.sample_finex, MODE_LINE_UNIDIR)

            # set Y's scan mode
            if (self.y_roi[SCAN_RES] == 'COARSE'):
                # self.set_sample_posner_mode(self.sample_mtrx, self.sample_finex, MODE_COARSE)
                self.sample_mtry.put('Mode', MODE_COARSE)
                # self.sample_mtry.put('Mode', 6)
                # self.main_obj.device( DNM_CY_AUTO_DISABLE_POWER ).put(0) #disabled
                self.yScan.put('P1PV', dct['coarse_pv_nm']['Y'] + '.VAL')
                self.yScan.put('R1PV', dct['coarse_pv_nm']['Y'] + '.RBV')

            else:

                # self.set_sample_posner_mode(self.sample_mtrx, self.sample_finex, MODE_LINE_UNIDIR)
                # self.sample_mtry.put('Mode', MODE_NORMAL)
                self.sample_mtry.put('Mode', MODE_LINE_UNIDIR)
                self.yScan.put('P1PV', dct['fine_pv_nm']['Y'] + '.VAL')
                self.yScan.put('R1PV', dct['fine_pv_nm']['Y'] + '.RBV')

                # self.main_obj.device( DNM_CY_AUTO_DISABLE_POWER ).put(1) #enabled

        # setup the E712 wavtable's and other relevant params
        #DEC 8 self.modify_config_for_hdw_accel()


    def modify_config_for_hdw_accel(self):
        '''
        Here I need to make the calls to send the commands that generate the waveform on the E712 for the current E_roi, by the end
        of this function everything should be ready  (as far as the E712 is concerned) to just call
            IOCE712:ExecWavgen by the sscan record

        This function needs to :
         - program the E712 with all sp_roi's for each dwell time using 1 wavtable per dwell time
        and spatial region.
         - set the number of points in the sscan record that starts the E712 wavegenerator to the number of wavtables used above
         - set the P1(x) and P2(y) PxPA tables in the sscan record that starts the E712 wavegenerator with the wavtable
         numbers that were used above


        :return:
        '''
        sample_positioning_mode = self.main_obj.get_sample_positioning_mode()
        fine_sample_positioning_mode = self.main_obj.get_fine_sample_positioning_mode()
        #start gate and counters
        if (self.is_pxp):
            mode = 0
            # pxp
            #self.gate.start()
            #time.sleep(0.25)
            # here the gate is the clock src so make sure its running
            #self.gate.soft_trigger.put(1)
            #self.gate.wait_till_running()

            #self.counter.start()
            #self.counter.wait_till_running()
        else:
            mode = 1
            #self.gate.start()
            #self.gate.wait_till_running()

            #self.counter.start()
            #self.counter.wait_till_running()

        # create usetable map
        wavtable_map = self.e712_wg.create_wavgen_usetable_map(self.sp_ids)
        # clear previous wavetables
        self.e712_wg.clear_wavetables()
        self.e712_wg.clear_wavgen_use_tbl_ids()
        self.e712_wg.clear_start_modes()


        #for the current ev index
        #for each sp_db in sp_rois call sendwave() to create the wavetable on the E712 and add wavtable ID to list,
        #keep a running total of number of wavtables used starting from 1
        #set the NPTS of the btm sscan to equal the total number of wavtables used above
        #for each P1 and P2 of the bottom level sscan record write the list of each wavtable ID's to the sscan rec

        #self.img_data = {}

        IMMEDIATELY = 1

        ttl_wavtables = 0
        #the following lists are populated and then written to placeholder waveform PV's that will be used
        #by SNL code to load the next set of params for the next spatial region as they are being executed
        x_wavtbl_id_lst = []
        y_wavtbl_id_lst = []

        x_npnts_lst = []
        y_npnts_lst = []

        x_reset_posns = []
        y_reset_posns = []

        x_start_mode = []
        x_useddl_flags = []
        x_reinitddl_flags = []
        x_startatend_flags = []

        y_start_mode = []

        sp_roi_ids = []

        for sp_id in self.sp_rois:
            sp_db = self.sp_rois[sp_id]
            e_rois = dct_get(sp_db, SPDB_EV_ROIS)
            ev_idx = self.get_evidx()
            dwell = e_rois[ev_idx][DWELL]


            if(fine_sample_positioning_mode == sample_fine_positioning_modes.ZONEPLATE):
                x_roi = dct_get(sp_db, SPDB_ZX)
                y_roi = dct_get(sp_db, SPDB_ZY)
                x_npnts = x_roi[NPOINTS]
                y_npnts = y_roi[NPOINTS]

            else:
                x_roi = dct_get(sp_db, SPDB_X)
                y_roi = dct_get(sp_db, SPDB_Y)
                x_npnts = x_roi[NPOINTS]
                y_npnts = y_roi[NPOINTS]

            #new data struct inparrallel with orig self.data, self.numImages = total numEv and num Pol
            #self.img_data[sp_id] = np.zeros((self.numImages, y_npnts, x_npnts), dtype=np.float32)


            # self.spid_data[sp_id] = {}
            # #make a set of arrays for final data
            # for q in range(self.numEPU):
            #     self.spid_data[sp_id][q] = np.zeros((self.numE, y_npnts, x_npnts), dtype=np.float32)


            x_reset_pos = x_roi[START]
            y_reset_pos = y_roi[START]
            x_axis_id = self.base_zero(self.e712_wg.get_x_axis_id())
            y_axis_id = self.base_zero(self.e712_wg.get_y_axis_id())

            sp_roi_ids.append(sp_id)
            # build a list of wavtable IDs used for this scan
            x_wavtbl_id_lst.append( wavtable_map[sp_id][x_axis_id])
            y_wavtbl_id_lst.append( wavtable_map[sp_id][y_axis_id])
            x_npnts_lst.append(int(x_npnts))
            y_npnts_lst.append(int(y_npnts))
            x_reset_posns.append(x_reset_pos)
            y_reset_posns.append(y_reset_pos)

            x_start_mode.append(IMMEDIATELY)
            y_start_mode.append(IMMEDIATELY)

            ddl_data = None
            if (self.is_pxp):
                mode = 0
                # program waveforms into tables
                self.e712_wg.send_wave(sp_id, x_roi, y_roi, dwell, mode, x_auto_ddl=self.x_auto_ddl,
                                       x_force_reinit=self.x_use_reinit_ddl)
                x_useddl_flags.append(0)
                x_reinitddl_flags.append(0)
                x_startatend_flags.append(0)
            else:
                mode = 1
                # program waveforms into tables
                ddl_data = self.e712_wg.send_wave(sp_id, x_roi, y_roi, dwell, mode, x_auto_ddl=self.x_auto_ddl,
                                           x_force_reinit=self.x_use_reinit_ddl)


                #ddl_data = self.e712_wg.get_stored_ddl_table()
                ddl_tbl_pv = MAIN_OBJ.device('e712_ddl_tbls')
                if(ddl_data is not None):
                    print('load this ddl table into the pvs for this spatial region')

                    ddl_tbl_pv[ttl_wavtables].put(ddl_data)
                    x_useddl_flags.append(1)
                    x_reinitddl_flags.append(0)
                    x_startatend_flags.append(0)
                else:
                    print('set the ddl pv waveform to 0s')
                    ddl_tbl_pv[ttl_wavtables].put([0,0,0,0,0,0])
                    x_useddl_flags.append(0)
                    x_reinitddl_flags.append(1)
                    x_startatend_flags.append(0)

            #keep running total
            ttl_wavtables += 1

        #map_lst, self.spid_data = self.make_stack_data_map(numEv=self.numE, numPol=self.numEPU, numSp=self.numSPIDS, x_npnts_lst=x_npnts_lst, y_npnts_lst=y_npnts_lst)

        # write the x motor reset positions to the waveform pv
        MAIN_OBJ.device('e712_xresetposns').put(x_reset_posns)
        MAIN_OBJ.device('e712_yresetposns').put(y_reset_posns)
        #write the wavtable ids to the waveform pv
        MAIN_OBJ.device('e712_x_wavtbl_ids').put(x_wavtbl_id_lst)
        MAIN_OBJ.device('e712_y_wavtbl_ids').put(y_wavtbl_id_lst)

        MAIN_OBJ.device('e712_x_npts').put(x_npnts_lst)
        MAIN_OBJ.device('e712_y_npts').put(y_npnts_lst)

        MAIN_OBJ.device('e712_x_useddl').put(x_useddl_flags)
        MAIN_OBJ.device('e712_x_usereinit').put(x_reinitddl_flags)
        MAIN_OBJ.device('e712_x_strtatend').put(x_startatend_flags)

        MAIN_OBJ.device('e712_x_start_mode').put(x_start_mode)
        MAIN_OBJ.device('e712_y_start_mode').put(y_start_mode)

        MAIN_OBJ.device('e712_sp_ids').put(sp_roi_ids)


        self.gateCntrCfgScan.put('NPTS', ttl_wavtables)


        #need to make sure that the gate and counter are running before leaving here
        _logger.info('Estemated time to complete scan is: %s' % self.e712_wg.get_new_time_estemate())

    def on_sample_scan_counter_changed_hdw_accel(self, row, data, counter_name='counter0'):
        """
        on_sample_scan_counter_changed_hdw_accel(): Used by SampleImageWithEnergySSCAN

        :param row: row description
        :type row: row type

        :param data: data description
        :type data: data type

        :returns: None
        """
        """
        The on counter_changed slot will take data cquired by line and point scans but it must treat each differently.
        The point scan still arrives as a one demensiotnal array but there are only 3 elements, data[row, point, value].
        The point scan has been programmed to acquire num_x_points + 1 so that the counter can increment the row value, thus this
        slot during a point scan will receive a point+1 and in that case it should be ignored.

        LIne scan data arrives in the form data[row, < number of x points of values >]

        This slot has to handle

        """

        if(row < 0):
            print()
            row = 0

        sp_id =  int(MAIN_OBJ.device('e712_current_sp_id').get_position())
        self.set_spatial_id(sp_id)

        if ((self.scan_type == scan_types.OSA_FOCUS) or (self.scan_type == scan_types.SAMPLE_FOCUS)):
            nptsy = self.numZ
        else:
            nptsy = self.numY

        _evidx = self.get_evidx()
        _imgidx = MAIN_OBJ.device('e712_image_idx').get_position()
        #print 'on_sample_scan_counter_changed_hdw_accel: _imgidx=%d row=%d' % (_imgidx, row)

        if (self.is_pxp and (not self.use_hdw_accel)):
            # Image point by point
            point = int(data[0])
            val = data[1]

            # print 'SampleImageWithEnergySSCAN: on_counter_changed: _imgidx=%d row=%d point=%d, data = %d' % (_imgidx, row, point, val)
            self.data[_imgidx, row, point] = val

        else:
            # print 'SampleImageWithEnergySSCAN: LXL on_counter_changed: _imgidx, row and data[0:10]=', (_imgidx, row, data[0:10])
            point = 0
            (wd,) = data.shape
            val = data[0:(wd - 1)]

        dct = self.init_counter_to_plotter_com_dct(make_counter_to_plotter_com_dct())
        dct[CNTR2PLOT_ROW] = int(row)
        dct[CNTR2PLOT_COL] = int(point)
        dct[CNTR2PLOT_VAL] = val
        #because we could be multi spatial override the default
        dct[CNTR2PLOT_SP_ID] = sp_id

        _dct = self.get_img_idx_map(_imgidx)
        _sp_id = _dct['sp_id']
        pol_idx = _dct['pol_idx']
        e_idx = _dct['e_idx']

        self.img_data[_sp_id][int(row), :] = val

        self.spid_data[counter_name][sp_id][pol_idx][e_idx, int(row), :] = val
        self.sigs.changed.emit(dct)

        #now emit progress information
        prog = float(float(row + 0.75) / float(nptsy)) * 100.0
        if (self.stack):
            prog_dct = make_progress_dict(sp_id=sp_id, percent=prog)
        else:
            prog_dct = make_progress_dict(sp_id=sp_id, percent=prog)

        self.low_level_progress.emit(prog_dct)


    def on_coarse_sample_scan_counter_changed(self, row, data, counter_name='counter0'):
        """
        on_sample_scan_counter_changed_hdw_accel(): Used by SampleImageWithEnergySSCAN

        :param row: row description
        :type row: row type

        :param data: data description
        :type data: data type

        :returns: None
        """
        """
        The on counter_changed slot will take data cquired by line and point scans but it must treat each differently.
        The point scan still arrives as a one demensiotnal array but there are only 3 elements, data[row, point, value].
        The point scan has been programmed to acquire num_x_points + 1 so that the counter can increment the row value, thus this
        slot during a point scan will receive a point+1 and in that case it should be ignored.

        LIne scan data arrives in the form data[row, < number of x points of values >]

        This slot has to handle

        """

        if(row < 0):
            print()
            row = 0

        sp_id =  int(MAIN_OBJ.device('e712_current_sp_id').get_position())
        self.set_spatial_id(sp_id)

        if ((self.scan_type == scan_types.OSA_FOCUS) or (self.scan_type == scan_types.SAMPLE_FOCUS)):
            nptsy = self.numZ
        else:
            nptsy = self.numY

        _evidx = self.get_evidx()
        #_imgidx = MAIN_OBJ.device('e712_image_idx').get_position()
        _imgidx = self.base_zero(self.get_imgidx())
        _dct = self.get_img_idx_map(_imgidx)
        _sp_id = _dct['sp_id']
        pol_idx = _dct['pol_idx']
        e_idx = _dct['e_idx']

        #set the spatial id so that save_hdr can use it
        self.set_spatial_id(_sp_id)
        #print 'on_sample_scan_counter_changed_hdw_accel: _imgidx=%d row=%d' % (_imgidx, row)

        if (self.is_pxp and (not self.use_hdw_accel)):
            # Image point by point
            point = int(data[0])
            val = data[1]

            # print 'SampleImageWithEnergySSCAN: on_counter_changed: _imgidx=%d row=%d point=%d, data = %d' % (_imgidx, row, point, val)
            self.data[_imgidx, row, point] = val

        else:
            # print 'SampleImageWithEnergySSCAN: LXL on_counter_changed: _imgidx, row and data[0:10]=', (_imgidx, row, data[0:10])
            point = 0
            (wd,) = data.shape
            val = data[0:(wd - 1)]

        dct = self.init_counter_to_plotter_com_dct(make_counter_to_plotter_com_dct())
        dct[CNTR2PLOT_ROW] = int(row)
        dct[CNTR2PLOT_COL] = int(point)
        dct[CNTR2PLOT_VAL] = val
        #because we could be multi spatial override the default
        dct[CNTR2PLOT_SP_ID] = _sp_id

        self.img_data[_sp_id][int(row), :] = val

        #print 'self.spid_data[%s][%d][%d][%d, %d, :]' % (counter_name,_sp_id,pol_idx,e_idx, int(row))
        self.spid_data[counter_name][_sp_id][pol_idx][e_idx, int(row), :] = val
        self.sigs.changed.emit(dct)

        #now emit progress information
        prog = float(float(row + 0.75) / float(nptsy)) * 100.0
        if (self.stack):
            prog_dct = make_progress_dict(sp_id=_sp_id, percent=prog)
        else:
            prog_dct = make_progress_dict(sp_id=_sp_id, percent=prog)

        self.low_level_progress.emit(prog_dct)

    def hdw_accel_save_hdr(self, update=False, do_check=True):
        """
        save_hdr(): This is the main datafile savinf function, it is called at the end of every completed scan

        :param update: update is a flag set to True when save_hdr() is first called during the configure() portion of the scan
                    it allows the data file to be created before data collection has started and then updated as the data is collected,
                    when the scan has finished this flag is False which indicates that all final processing of the save should take place
                    (ie: prompt the user if they want to save this data etc)

        :returns: None

        If this function takes a long time due to grabbing a snapshot of all
        the positioners it should maybe be moved to its own thread and just have the
        GUI wait until it is finished, that seems reasonable for the user to wait a couple seconds
        for the file to save as long as the GUI is not hung


        This function is used by:
            - sample Image PXP
            - sample Image LXL
            - sample Image point Spectra
        None stack scans should yield the following per scan:
            one header file
            one image thumbnail (jpg)

        Stack scans should yield:
            one header file
            numE * numEpu thumbnail images per stack

        The image thumbnails are saved in the on_sampleImage_data_done signal handler

        The header file is saved on the scan_done signal of the top level scan
        """
        if (update):
            _logger.info('Skipping save_hdr() update = True')
            return
        upside_dwn_scans = [scan_types.SAMPLE_LINE_SPECTRUM, scan_types.SAMPLE_IMAGE]
        # _logger.info('save_hdr: starting')
        if (self.is_point_spec):
            self.save_point_spec_hdr(update)
            return



        # self.gate.stop()
        # self.counter.stop()
        self.data_obj.set_scan_end_time()

        # self.main_obj.update_zmq_posner_snapshot()
        # self.main_obj.update_zmq_detector_snapshot()
        # self.main_obj.update_zmq_pv_snapshot()
        upd_list = []
        for s in self.scanlist:
            upd_list.append(s.get_name())
        # self.main_obj.update_zmq_sscan_snapshot(upd_list)

        _ev_idx = self.get_evidx()
        _img_idx = self.get_imgidx() - 1
        _spatial_roi_idx = self.get_spatial_id()
        sp_db = self.sp_rois[_spatial_roi_idx]
        sample_pos = 1

        # data_name_dct = master_get_seq_names(datadir, prefix_char=data_file_prfx, thumb_ext=thumb_file_sffx, dat_ext='hdf5', stack_dir=self.stack)
        # hack
        if (_img_idx < 0):
            _img_idx = 0
        self.data_dct = self.data_obj.get_data_dct()

        ado_obj = dct_get(sp_db, SPDB_ACTIVE_DATA_OBJECT)
        #        data_file_prfx = dct_get(ado_obj, ADO_CFG_PREFIX)
        #        thumb_file_ext = dct_get(ado_obj, ADO_CFG_THUMB_EXT)
        datadir = dct_get(ado_obj, ADO_CFG_DATA_DIR)
        datafile_name = dct_get(ado_obj, ADO_CFG_DATA_FILE_NAME)
        datafile_prfx = dct_get(ado_obj, ADO_CFG_PREFIX)
        #        thumb_name = dct_get(ado_obj, ADO_CFG_DATA_THUMB_NAME)
        stack_dir = dct_get(ado_obj, ADO_CFG_STACK_DIR)

#        if (not update):
#            if (not self.check_if_save_all_data(datafile_name)):
#                return
        if(self.use_hdw_accel):
            if (self.e712_wg.save_this_ddl()):
                self.e712_wg.get_ddl_table(X_WAVE_TABLE_ID, cb=self.e712_wg.save_ddl_data)

        self.saving_data.emit('Saving...')

        if (self.stack):
            datadir = stack_dir

        # alldata = self.main_obj.get_zmq_sscan_snapshot(upd_list)
        for scan in self.scanlist:
            sname = scan.get_name()
            #    #ask each scan to get its data and store it in scan.scan_data
            if (scan.section_name == SPDB_XY):
                # this is a sscan where P1 is X and P2 is Y, separate them such that they look like two separate scans
                # alldata = self.take_sscan_snapshot(scan.name)

                if(self.use_hdw_accel):
                    alldata = {}
                    alldata['P1RA'] = self.x_roi[SETPOINTS]
                    alldata['P2RA'] = self.y_roi[SETPOINTS]
                    alldata['NPTS'] = self.x_roi[NPOINTS]
                    alldata['CPT'] = self.x_roi[NPOINTS]
                    p1data = alldata['P1RA']
                    npts = alldata['NPTS']
                    cpt = alldata['CPT']
                    p2data = alldata['P2RA']
                else:
                    alldata = scan.get_all_data()
                    p1data = alldata['P1RA']
                    npts = alldata['NPTS']
                    cpt = alldata['CPT']
                    p2data = alldata['P2RA']
                    dct_put(self.data_dct, 'DATA.SSCANS.XY', alldata)

                dct_put(self.data_dct, 'DATA.SSCANS.XY', alldata)
                dct_put(self.data_dct, 'DATA.SSCANS.X', {'P1RA': p1data, 'NPTS': npts, 'CPT': cpt})
                dct_put(self.data_dct, 'DATA.SSCANS.Y', {'P1RA': p2data, 'NPTS': npts, 'CPT': cpt})
            else:
                all_data = scan.get_all_data()
                if (self.use_hdw_accel and (scan.section_name == (SPDB_X or SPDB_Y))):
                    # there will not be any P1RA key in all_data because there are no positioners specified so
                    # the data must be generated for X and Y in
                    p1data = np.linspace(self.x_roi[START], self.x_roi[STOP], self.x_roi[NPOINTS])
                    p2data = np.linspace(self.y_roi[START], self.y_roi[STOP], self.y_roi[NPOINTS])
                    all_data['P1RA'] = p1data
                    all_data['P2RA'] = p2data
                    xnpts = self.x_roi[NPOINTS]
                    ynpts = self.y_roi[NPOINTS]
                    xcpt = xnpts
                    ycpt = ynpts
                    all_data['NPTS'] = self.x_roi[NPOINTS]
                    all_data['CPT'] = self.x_roi[NPOINTS]
                    dct_put(self.data_dct, 'DATA.SSCANS.XY', all_data)
                    dct_put(self.data_dct, 'DATA.SSCANS.X', {'P1RA': p1data, 'NPTS': xnpts, 'CPT': xcpt})
                    dct_put(self.data_dct, 'DATA.SSCANS.Y', {'P1RA': p2data, 'NPTS': ynpts, 'CPT': ycpt})
                else:
                    dct_put(self.data_dct, 'DATA.SSCANS.' + scan.section_name, scan.get_all_data())
                    # dct_put(self.data_dct,'DATA.SSCANS.' + scan.section_name, alldata[sname])

        # if (self.scan_type in upside_dwn_scans and not update):
        #     # the data for these scans needs to be flipped upside down, but because this function is called multiple times
        #     #depending on where the scan is at we need to make sure we are only flipping the data 1 time, so here
        #     #we are doing it at the end (the last time it is called) when update is False
        #     _data = self.flip_data_upsdown(self.data[_img_idx - 1])
        #     self.data[_img_idx - 1] = np.copy(_data)
        #
        # elif(self.scan_type is scan_types.SAMPLE_IMAGE_STACK and not update):
        #     #stack scan save individual images during an update, so flip during an update for a stack scan
        #     #but then the issue is the very last image because it will get flipped multiple times
        #     _data = self.flip_data_upsdown(self.data[_img_idx - 1])
        #     self.data[_img_idx - 1] = np.copy(_data)
        #
        # elif (self.scan_type is scan_types.SAMPLE_IMAGE_STACK and update):
        #     # stack scan save individual images during an update, so flip during an update for a stack scan
        #     # but then the issue is the very last image because it will get flipped multiple times
        #     _data = self.flip_data_upsdown(self.data[_img_idx - 1])
        #     self.data[_img_idx - 1] = np.copy(_data)

        # _logger.info('grabbing devices snapshot')
        devices = self.main_obj.get_devices()

        # get the current spatial roi and put it in the dct as a dict with its sp_id as the key
        _wdgcom = {}
        dct_put(_wdgcom, WDGCOM_CMND, self.wdg_com[CMND])
        _sprois = {}
        _sprois[_spatial_roi_idx] = self.wdg_com['SPATIAL_ROIS'][_spatial_roi_idx]
        dct_put(_wdgcom, SPDB_SPATIAL_ROIS, _sprois)
        dct_put(self.data_dct, ADO_CFG_WDG_COM, _wdgcom)

        testing_polarity_entries = False
        if (testing_polarity_entries):
            t_dct = {}

            dct_put(t_dct, 'POSITIONERS', self.take_positioner_snapshot(devices['POSITIONERS']))
            dct_put(t_dct, 'DETECTORS', self.take_detectors_snapshot(devices['DETECTORS']))
            dct_put(t_dct, 'TEMPERATURES', self.take_temps_snapshot(devices['TEMPERATURES']))
            dct_put(t_dct, 'PRESSURES', self.take_pressures_snapshot(devices['PRESSURES']))
            dct_put(t_dct, 'PVS', self.take_pvs_snapshot(devices['PVS']))
            # _logger.info('DONE grabbing devices snapshot')
            # dct_put(t_dct, ADO_CFG_WDG_COM, self.wdg_com)
            dct_put(self.data_dct, ADO_CFG_WDG_COM, _wdgcom)

            dct_put(t_dct, ADO_CFG_SCAN_TYPE, self.scan_type)
            dct_put(t_dct, ADO_CFG_CUR_EV_IDX, _ev_idx)
            dct_put(t_dct, ADO_CFG_CUR_SPATIAL_ROI_IDX, _spatial_roi_idx)
            dct_put(t_dct, ADO_CFG_CUR_SAMPLE_POS, sample_pos)
            dct_put(t_dct, ADO_CFG_CUR_SEQ_NUM, 0)
            dct_put(t_dct, ADO_CFG_DATA_DIR, datadir)
            dct_put(t_dct, ADO_CFG_DATA_FILE_NAME, datafile_prfx)
            dct_put(t_dct, ADO_CFG_UNIQUEID, datafile_prfx)
            dct_put(t_dct, ADO_CFG_X, self.x_roi)
            dct_put(t_dct, ADO_CFG_Y, self.y_roi)
            dct_put(t_dct, ADO_CFG_Z, self.z_roi)
            dct_put(t_dct, ADO_CFG_EV_ROIS, self.e_rois)
            dct_put(t_dct, ADO_DATA_POINTS, self.data)

            images_data = np.zeros((self.numEPU, self.numE, self.numY, self.numX))
            image_idxs = []
            for i in range(self.numEPU):
                image_idxs.append(np.arange(i, self.numImages, self.numEPU))

            # for idxs in image_idxs:
            for i in range(self.numEPU):
                idxs = image_idxs[i]
                y = 0
                for j in idxs:
                    images_data[i][y] = self.data[j]
                    y += 1

            new_e_rois = self.turn_e_rois_into_polarity_centric_e_rois(self.e_rois)
            pol_rois = []
            for e_roi in self.e_rois:
                for pol in range(self.numEPU):
                    pol_rois.append(e_roi['POL_ROIS'][pol])

            for pol in range(self.numEPU):
                self.data_dct['entry_%d' % pol] = copy.deepcopy(t_dct)
                dct_put(self.data_dct['entry_%d' % pol], ADO_DATA_POINTS, copy.deepcopy(images_data[pol]))
                dct_put(self.data_dct['entry_%d' % pol], ADO_DATA_SSCANS,
                        copy.deepcopy(self.data_dct['DATA']['SSCANS']))
                dct_put(self.data_dct['entry_%d' % pol], ADO_CFG_EV_ROIS, [new_e_rois[pol]])
        else:

            if ((self.data_dct['TIME'] != None) and update):
                # we already have already set these and its not the end of the scan sp skip
                pass
            else:
                dct_put(self.data_dct, 'TIME', make_timestamp_now())
                dct_put(self.data_dct, 'POSITIONERS', self.take_positioner_snapshot(devices['POSITIONERS']))
                dct_put(self.data_dct, 'DETECTORS', self.take_detectors_snapshot(devices['DETECTORS']))
                dct_put(self.data_dct, 'TEMPERATURES', self.take_temps_snapshot(devices['TEMPERATURES']))
                dct_put(self.data_dct, 'PRESSURES', self.take_pressures_snapshot(devices['PRESSURES']))
                dct_put(self.data_dct, 'PVS', self.take_pvs_snapshot(devices['PVS']))

            # _logger.info('DONE grabbing devices snapshot')
            # dct_put(self.data_dct, ADO_CFG_WDG_COM, self.wdg_com)
            dct_put(self.data_dct, ADO_CFG_WDG_COM, _wdgcom)

            if (update):
                dct_put(self.data_dct, ADO_CFG_DATA_STATUS, DATA_STATUS_NOT_FINISHED)
            else:
                dct_put(self.data_dct, ADO_CFG_DATA_STATUS, DATA_STATUS_FINISHED)

            dct_put(self.data_dct, ADO_CFG_SCAN_TYPE, self.scan_type)
            dct_put(self.data_dct, ADO_CFG_CUR_EV_IDX, _ev_idx)
            dct_put(self.data_dct, ADO_CFG_CUR_SPATIAL_ROI_IDX, _spatial_roi_idx)
            dct_put(self.data_dct, ADO_CFG_CUR_SAMPLE_POS, sample_pos)
            dct_put(self.data_dct, ADO_CFG_CUR_SEQ_NUM, 0)
            dct_put(self.data_dct, ADO_CFG_DATA_DIR, datadir)
            dct_put(self.data_dct, ADO_CFG_DATA_FILE_NAME, datafile_prfx)
            dct_put(self.data_dct, ADO_CFG_UNIQUEID, datafile_prfx)
            dct_put(self.data_dct, ADO_CFG_X, self.x_roi)
            dct_put(self.data_dct, ADO_CFG_Y, self.y_roi)
            dct_put(self.data_dct, ADO_CFG_Z, self.z_roi)
            dct_put(self.data_dct, ADO_CFG_EV_ROIS, self.e_rois)
            #dct_put(self.data_dct, ADO_DATA_POINTS, self.data)

            cur_idx = self.get_consecutive_scan_idx()
            _dct = self.get_img_idx_map(cur_idx)
            sp_idx = _dct['sp_idx']
            pol_idx = _dct['pol_idx']

            #for now just use the first counter
            #counter = self.counter_dct.keys()[0]
            counter = DNM_DEFAULT_COUNTER
            self._data = self.spid_data[counter][sp_idx][pol_idx]
            dct_put(self.data_dct, ADO_DATA_POINTS, self._data)

            dct_put(self.data_dct, ADO_STACK_DATA_POINTS, self.spid_data)
            dct_put(self.data_dct, ADO_STACK_DATA_UPDATE_DEV_POINTS, self.update_dev_data)

            dct_put(self.data_dct, ADO_SP_ROIS, self.sp_rois)


        if (update):
            self.hdr.save(self.data_dct, use_tmpfile=True)
        else:
            pass
            #Sept 8
            # if(self.stack or (len(self.sp_rois) > 1)):
            #     self.hdr.save(self.data_dct, allow_tmp_rename=True)
            #     self.clean_up_data()
            # else:
            #     self.hdr.save(self.data_dct)
            #end Sept 8

            #update stop time in tmp file
            self.main_obj.zmq_stoptime_to_tmp_file()

            #now send the Active Data Object (ADO) to the tmp file under the section 'ADO'
            dct = {}
            dct['cmd'] = CMD_SAVE_DICT_TO_TMPFILE
            wdct = {'WDG_COM':dict_to_json(_wdgcom), 'SCAN_TYPE': self.scan_type}
            data_dct_str = dict_to_json(self.data_dct)
            dct['dct'] = {'SP_ROIS': dict_to_json(self.sp_rois), 'CFG': wdct, 'numEpu': self.numEPU, 'numSpids':self.numSPIDS, 'numE':self.numE, \
                          'DATA_DCT':data_dct_str}

            self.main_obj.zmq_save_dict_to_tmp_file(dct)

            dct = {}
            dct['cmd'] = CMD_EXPORT_TMP_TO_NXSTXMFILE
            self.main_obj.zmq_save_dict_to_tmp_file(dct)

        self.on_save_sample_image(_data=self.img_data[_spatial_roi_idx])

        # _logger.info('save_hdr: done')
        if (self.main_obj.get_beamline_id() is BEAMLINE_IDS.STXM):
            self.main_obj.device(DNM_CX_AUTO_DISABLE_POWER).put(1)  # enabled
            self.main_obj.device(DNM_CY_AUTO_DISABLE_POWER).put(1)  # enabled

    def hdw_accel_chk_for_more_evregions(self):
        """
        chk_for_more_evregions(): description

        :returns: None
        """
        """
        this slot handles the end of scan, when the default on_scan_done() is called in the
        base scan class it will check for an installed child on_scan_done slot (this one)
        once this has been called it returns True or False
            return True if there are no more ev regions and you want the default on_scan_done(0) to finish and clean everything up

            return False if there are more ev Regions and you dont want everything stopped and cleaned up
        """
        multi_ev_single_image_scans = [scan_types.SAMPLE_LINE_SPECTRUM, scan_types.SAMPLE_POINT_SPECTRUM]

        _logger.info('hdw_accel_chk_for_more_evregions: checking')

        if (self._abort):
            _logger.info('hdw_accel_chk_for_more_evregions: scan aborting')
            # make sure to save current scan
            if (self.main_obj.get_beamline_id() is BEAMLINE_IDS.STXM):
                self.gate.stop()
                self.counter.stop()
            # self.on_save_sample_image()
            self.on_data_level_done()
            self.save_hdr()
            self.hdr.remove_tmp_file()

            return (True)

        # increment the index into ev regions
        self.incr_evidx()

        # if(self._current_ev_idx < len(self.e_rois)):
        if (self.get_evidx() < len(self.e_rois)):
            _logger.info('hdw_accel_chk_for_more_evregions: yes there is, loading and starting')
            if (self.main_obj.get_beamline_id() is BEAMLINE_IDS.STXM):
                if(not self.is_point_spec):
                    self.gate.stop()
                    self.counter.stop()

            if (self.scan_type not in multi_ev_single_image_scans):
                # signal plotter to start a new image
                # sp_id = self.get_next_spatial_id()
                # self.new_spatial_start.emit(sp_id)
                self.new_spatial_start.emit(self.sp_db[SPDB_ID_VAL])

            e_roi = self.e_rois[self._current_ev_idx]
            # configure next ev sscan record with next ev region start/stop
            self._config_start_stop(self.evScan, 1, e_roi[START], e_roi[STOP], e_roi[NPOINTS])

            # prev_dwell = self.dwell
            self.dwell = e_roi[DWELL]

            if (self.use_hdw_accel):
            #     # need to check to see if dwell changed, if it did we need to re-configure the wavetables
            #     # if(prev_dwell != self.dwell):
            #     # _logger.debug('dwell changed [%.2f] so reconfiguring the hardware accel' % self.dwell)
                 self.modify_config()
                 # wait for gate and counter to start
            #     time.sleep(2.0)
            #    pass


            # need to determine the scan velocity if there is a change in Dwell for this next ev region
            elif (not self.is_point_spec):
                # the dwell ime for the new ev region could have changed so determine the scan velo and accRange
                # need to determine the scan velocity if there is a change in Dwell for this next ev region
                if (self.is_line_spec and self.is_pxp):
                    scan_velo = self.get_mtr_max_velo(self.xyScan.P1)
                    # vmax = self.get_mtr_max_velo(self.xyScan.P1)
                else:
                    vmax = self.get_mtr_max_velo(self.xScan.P1)
                    (scan_velo, npts, dwell) = ensure_valid_values(self.x_roi[START], self.x_roi[STOP], self.dwell,
                                                                   self.numX, vmax, do_points=True)
                    # need the range of scan to be passed to calc_accRange()
                    rng = self.x_roi[STOP] - self.x_roi[START]
                    accRange = calc_accRange('SampleX', 'Fine', rng, scan_velo, dwell, accTime=0.04)
                    # reassign dwell because it ay have changed on return from ensure_valid_values()
                    self.dwell = dwell
                    _logger.debug('set_sample_scan_velocity Image scan: scan_velo=%.2f um/s accRange=%.2f um' % (
                    scan_velo, accRange))

                self.set_x_scan_velo(scan_velo)
                # ok now finish configuration and start it
                self.on_this_dev_cfg()
                if (self.main_obj.get_beamline_id() is BEAMLINE_IDS.STXM):
                    self.gate.start()
                    self.counter.start()


            elif (self.is_point_spec):
                # ok now finish configuration and start it
                self.on_this_dev_cfg()
                if (self.main_obj.get_beamline_id() is BEAMLINE_IDS.STXM):
                    self.gate.start()
                    self.counter.start()

            self.start()
            # let caller know were not done
            return (False)
        else:
            _logger.info('chk_for_more_evregions: Nope no more')
            if (self.main_obj.get_beamline_id() is BEAMLINE_IDS.STXM):
                self.gate.stop()
                self.counter.stop()

            # ok scan is all done now, so save final header file
            if (not self.file_saved):
                _logger.debug('chk_for_more_evregions: calling on_save_sample_image()')
                self.on_save_sample_image()
            self.save_hdr()

            # ok there are no more ev regions to execute
            return (True)

    def coarse_chk_for_more_evregions(self):
        """
        chk_for_more_evregions(): description

        :returns: None
        """
        """
        this slot handles the end of scan, when the default on_scan_done() is called in the 
        base scan class it will check for an installed child on_scan_done slot (this one)
        once this has been called it returns True or False
            return True if there are no more ev regions and you want the default on_scan_done(0) to finish and clean everything up

            return False if there are more ev Regions and you dont want everything stopped and cleaned up 
        """
        multi_ev_single_image_scans = [scan_types.SAMPLE_LINE_SPECTRUM, scan_types.SAMPLE_POINT_SPECTRUM]

        # Sept 6 if(TEST_SAVE_INITIAL_FILE):
        # Sept 6     self.save_hdr(update=True)
        _logger.info('chk_for_more_evregions: checking')

        if (self._abort):
            _logger.info('chk_for_more_evregions: scan aborting')
            # make sure to save current scan
            if (self.main_obj.get_beamline_id() is BEAMLINE_IDS.STXM):
                self.gate.stop()
                self.counter.stop()
            # self.on_save_sample_image()
            # self.on_data_level_done()
            self.save_hdr()
            self.hdr.remove_tmp_file()

            return (True)

        # increment the index into ev regions
        self.incr_evidx()

        # if(self._current_ev_idx < len(self.e_rois)):
        if (self.get_evidx() < len(self.e_rois)):
            _logger.info('chk_for_more_evregions: yes there is, loading and starting')
            if (self.main_obj.get_beamline_id() is BEAMLINE_IDS.STXM):
                if (not self.is_point_spec):
                    self.gate.stop()
                    self.counter.stop()

                    # sept 11
                    self.counter.wait_till_stopped()

            if (self.scan_type not in multi_ev_single_image_scans):
                # signal plotter to start a new image
                # sp_id = self.get_next_spatial_id()
                # self.new_spatial_start.emit(sp_id)
                self.new_spatial_start.emit(self.sp_db[SPDB_ID_VAL])

            e_roi = self.e_rois[self._current_ev_idx]
            # configure next ev sscan record with next ev region start/stop
            self._config_start_stop(self.evScan, 1, e_roi[START], e_roi[STOP], e_roi[NPOINTS])

            # prev_dwell = self.dwell
            self.dwell = e_roi[DWELL]

            if (self.use_hdw_accel):
                # need to check to see if dwell changed, if it did we need to re-configure the wavetables
                # if(prev_dwell != self.dwell):
                # _logger.debug('dwell changed [%.2f] so reconfiguring the hardware accel' % self.dwell)
                self.modify_config()
                # wait for gate and counter to start
                time.sleep(2.0)

            # need to determine the scan velocity if there is a change in Dwell for this next ev region
            elif (not self.is_point_spec):
                # the dwell ime for the new ev region could have changed so determine the scan velo and accRange
                # need to determine the scan velocity if there is a change in Dwell for this next ev region
                if (self.is_line_spec and self.is_pxp):
                    scan_velo = self.get_mtr_max_velo(self.xyScan.P1)
                    # vmax = self.get_mtr_max_velo(self.xyScan.P1)
                else:
                    vmax = self.get_mtr_max_velo(self.xScan.P1)
                    (scan_velo, npts, dwell) = ensure_valid_values(self.x_roi[START], self.x_roi[STOP], self.dwell,
                                                                   self.numX, vmax, do_points=True)
                    # need the range of scan to be passed to calc_accRange()
                    rng = self.x_roi[STOP] - self.x_roi[START]
                    accRange = calc_accRange('SampleX', 'Fine', rng, scan_velo, dwell, accTime=0.04)
                    # reassign dwell because it ay have changed on return from ensure_valid_values()
                    self.dwell = dwell
                    _logger.debug('set_sample_scan_velocity Image scan: scan_velo=%.2f um/s accRange=%.2f um' % (
                    scan_velo, accRange))

                self.set_x_scan_velo(scan_velo)
                # ok now finish configuration and start it
                self.on_this_dev_cfg()
                if (self.main_obj.get_beamline_id() is BEAMLINE_IDS.STXM):
                    self.gate.start()
                    self.counter.start()
                    # sept 11
                    self.counter.wait_till_running()


            elif (self.is_point_spec):
                # ok now finish configuration and start it
                self.on_this_dev_cfg()
                if (self.main_obj.get_beamline_id() is BEAMLINE_IDS.STXM):
                    if (not self.is_point_spec):
                        self.gate.start()
                        self.counter.start()
                        # sept 11
                        self.counter.wait_till_running()

            self.start()
            # let caller know were not done
            return (False)
        else:
            _logger.info('chk_for_more_evregions: Nope no more')
            if ((not self.is_point_spec) and self.coarse_chk_for_more_spatial_regions()):
                # were not done
                return (False)
            else:
                if (self.main_obj.get_beamline_id() is BEAMLINE_IDS.STXM):
                    self.gate.stop()
                    self.counter.stop()

                # ok scan is all done now, so save final header file
                if (not self.file_saved):
                    _logger.debug('chk_for_more_evregions: calling on_save_sample_image()')
                    self.on_save_sample_image()
                self.save_hdr()

                # ok there are no more spatial regions to execute
                return (True)

    def coarse_chk_for_more_spatial_regions(self):
        """
        chk_for_more_spatial_regions(): this slot handles the end of scan, when the default on_scan_done() is called in the
            base scan class it will check for an installed child on_scan_done slot (this one)
            once this has been called it returns True or False

            return True if there are more spatial Regions and you dont want everything stopped and cleaned up

            return False if there are no more spatial regions and you want the default on_scan_done(0 to finish and clean everything up

        :returns: True if there are more spatial Regions and you dont want everything stopped and cleaned up
                return False if there are no more spatial regions and you want the default on_scan_done(0 to finish and clean everything up

        """
        _logger.info('chk_for_more_spatial_regions: checking')

        if (self._abort):
            _logger.info('chk_for_more_spatial_regions: scan aborting')
            self.save_hdr()
            self.hdr.remove_tmp_file()
            return (True)

        # get the next spatial ID in the list of spatial regions we are to scan
        sp_id = self.get_next_spatial_id()
        if (sp_id is not None):
            # save the current one and then go again
            self.save_hdr()

            _logger.info('chk_for_more_spatial_regions: found sp_id=%d, loading and starting' % sp_id)

            # because we will be starting a new scan that will have new self.data created we need to reinit the index to the data
            # because imgidx is what is used as the first dimension of the data
            _logger.info('chk_for_more_spatial_regions: resetting the data image index')
            self.reset_imgidx()

            if (self.is_lxl):
                self.configure(self.wdg_com, sp_id, ev_idx=0, line=True, block_disconnect_emit=True)
            else:
                if (self.is_point_spec):
                    self.configure(self.wdg_com, sp_id, ev_idx=0, line=False, block_disconnect_emit=True)
                else:
                    self.configure(self.wdg_com, sp_id, ev_idx=0, line=False, block_disconnect_emit=True)
            self.start()
            return (True)
        else:
            _logger.info('chk_for_more_spatial_regions: nope all done')
            return (False)