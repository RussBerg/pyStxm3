'''
Created on Sep 26, 2016

@author: bergr
'''
import time
import os
import numpy as np

from bcm.devices.device_names import *

from cls.applications.pyStxm import abs_path_to_ini_file
from cls.applications.pyStxm.bl10ID01 import MAIN_OBJ
from cls.scanning.BaseScan import BaseScan, SIMULATE_SPEC_DATA
from cls.scanning.SScanClass import SScanClass
from cls.utils.prog_dict_utils import make_progress_dict
from cls.scanning.scan_cfg_utils import set_devices_for_point_scan, set_devices_for_line_scan
from cls.utils.roi_dict_defs import *

from cls.scanning.scan_cfg_utils import set_devices_for_point_scan, set_devices_for_line_scan, \
    set_devices_for_e712_wavegen_point_scan, set_devices_for_e712_wavegen_line_scan, make_timestamp_now

from cls.types.stxmTypes import scan_types, scan_sub_types, \
                                        energy_scan_order_types, sample_positioning_modes, sample_fine_positioning_modes

from cls.utils.dict_utils import dct_get, dct_put
from cls.utils.log import get_module_logger
from cls.utils.cfgparser import ConfigClass

from cls.plotWidgets.utils import *
from cls.scanning.e712_wavegen.e712 import X_WAVE_TABLE_ID

_logger = get_module_logger(__name__)
appConfig = ConfigClass(abs_path_to_ini_file)

class LineSpecSSCAN(BaseScan):
    '''
    This class 
    '''
    
    def __init__(self):
        """
        __init__(): description

        :returns: None
        """
        super(LineSpecSSCAN, self).__init__('%sstxm'% MAIN_OBJ.get_sscan_prefix(),'LINESPEC', main_obj=MAIN_OBJ)
        self.e712_wg = MAIN_OBJ.device('E712ControlWidget')
        self.use_hdw_accel = True
        self.x_auto_ddl = True
        self.x_use_reinit_ddl = False

    
    def init_sscans(self):

        self.cb_idxs = []
        self.ttl_pnts = 0
        self.final_data_dir = None
        
        self.setupScan = SScanClass('%s:scan5' % self.scan_prefix, 'SETUP', main_obj=MAIN_OBJ)
        self._scan4 = SScanClass('%s:scan4' % self.scan_prefix, SPDB_EV_EV, main_obj=MAIN_OBJ)
        self._scan3 = SScanClass('%s:scan3' % self.scan_prefix, SPDB_EV_POL, main_obj=MAIN_OBJ)
        self._scan2 = SScanClass('%s:scan2' % self.scan_prefix, SPDB_Y, main_obj=MAIN_OBJ)
        self._scan1 = SScanClass('%s:scan1' % self.scan_prefix, SPDB_X, main_obj=MAIN_OBJ)
        self.gateCntrCfgScan = SScanClass('%s:scan2' % self.scan_prefix, 'GATECOUNT_CFG', main_obj=MAIN_OBJ)

        lxl_scan = {}
        pxp_scan = {}
        
        if(self.sample_positioning_mode == sample_positioning_modes.GONIOMETER):
            lxl_scan['cmd_file'] = '%s/goni_line_spec_lxl_wg.cmd'  % self.script_dir
            pxp_scan['cmd_file'] = '%s/goni_line_spec_pxp_wg.cmd'  % self.script_dir
        else:
            lxl_scan['cmd_file'] = '%s/line_spec_lxl_wg.cmd'  % self.script_dir
            pxp_scan['cmd_file'] = '%s/line_spec_pxp_wg.cmd'  % self.script_dir

        
        lxl_scan['ev_section_id'] = SPDB_EV_EV
        lxl_scan['pol_section_id'] = SPDB_EV_POL
        #lxl_scan['setup_scan'] = self.setupScan
        lxl_scan['setup_scan'] = None
        lxl_scan['pol_scan'] = self._scan4
        lxl_scan['ev_scan'] = self._scan3
        lxl_scan['y_scan'] = None
        lxl_scan['x_scan'] = None
        lxl_scan['xy_scan'] = self._scan1
        lxl_scan['top_lvl_scan'] = self._scan4
        lxl_scan['data_lvl_scan'] = self._scan3
        lxl_scan['btm_lvl_scan'] = self._scan1
        lxl_scan['on_counter_changed'] = self.linespec_counter_changed
        lxl_scan['on_data_level_done'] = self.on_data_level_done
        lxl_scan['on_scan_done'] = self.chk_for_more_evregions
        lxl_scan['on_abort_scan'] = self.on_abort_scan
        lxl_scan['on_dev_cfg'] = self.on_this_dev_cfg
        lxl_scan['modify_config'] = self.modify_config_for_hdw_accel
        lxl_scan['scanlist'] = [ self._scan1 , self._scan2, self._scan3, self._scan4]
        
        
        #pxp_scan['cmd_file'] = '%s/line_spec_pxp.cmd'
        
        #pxp_scan['scan3_section_id'] = SPDB_EV_EV
        #pxp_scan['scan2_section_id'] = SPDB_EV_POL
        #pxp_scan['scan1_section_id'] = SPDB_XY



        pxp_scan['ev_section_id'] = SPDB_EV_EV
        pxp_scan['pol_section_id'] = SPDB_EV_POL
        # pxp_scan['setup_scan'] = self.setupScan
        pxp_scan['setup_scan'] = None
        pxp_scan['pol_scan'] = self._scan4
        pxp_scan['ev_scan'] = self._scan3
        pxp_scan['y_scan'] = None
        pxp_scan['x_scan'] = None
        pxp_scan['xy_scan'] = self._scan1
        pxp_scan['top_lvl_scan'] = self._scan4
        pxp_scan['data_lvl_scan'] = self._scan3
        pxp_scan['btm_lvl_scan'] = self._scan1
        pxp_scan['on_counter_changed'] = self.linespec_counter_changed
        pxp_scan['on_data_level_done'] = self.on_data_level_done
        pxp_scan['on_abort_scan'] = self.on_abort_scan
        pxp_scan['on_scan_done'] = self.chk_for_more_evregions
        pxp_scan['on_dev_cfg'] = self.on_this_dev_cfg
        pxp_scan['modify_config'] = self.modify_config_for_hdw_accel
        pxp_scan['scanlist'] = [ self._scan1 , self._scan2, self._scan3, self._scan4]
        

        
        #self.pnt_line_cmdfile_parms = [lxl_scan, pxp_scan]
        
        self.cmdfile_parms = {}
        self.cmdfile_parms['lxl_scan'] = lxl_scan
        self.cmdfile_parms['pxp_scan'] = pxp_scan
        
        zmtr = MAIN_OBJ.device(DNM_ZONEPLATE_Z)
        ymtr = MAIN_OBJ.device(DNM_SAMPLE_Y)
        xmtr = MAIN_OBJ.device(DNM_SAMPLE_X)
        
        self.evScan = self._scan3
        self.polScan = self._scan2
        self.xyScan = self._scan1
        self.xScan = self._scan1
        self.yScan = self._scan1
        
        self.evScan.set_positioner(1, MAIN_OBJ.device('ENERGY'))
        
        self.polScan.set_positioner(1, MAIN_OBJ.device(DNM_EPU_POLARIZATION))
        self.polScan.set_positioner(2, MAIN_OBJ.device(DNM_EPU_OFFSET))
        self.polScan.set_positioner(3, MAIN_OBJ.device(DNM_EPU_ANGLE))
                
        self.xyScan.set_positioner(1, MAIN_OBJ.device(DNM_SAMPLE_X))
        self.xyScan.set_positioner(2, MAIN_OBJ.device(DNM_SAMPLE_Y))
        
        self.scanlist = [ ]
        self.mtr_list = [ ]
    
#     def init_devices(self):
#         self.gate = MAIN_OBJ.device('Gate')
#         self.counter = MAIN_OBJ.device('Counter')
#         self.shutter = MAIN_OBJ.device('Shutter')  
    
    def init_set_scan_levels(self):
        self.set_top_level_scan(self.evScan)
        self.set_data_level_scan(self.evScan)
        self.set_btm_level_scan(self.xyScan)
        self.set_top_level_scan(self.setupScan)
    
    def init_signals(self):
        self.set_config_devices_func(self.on_this_dev_cfg)
        self.set_on_counter_changed_func(self.linespec_pxp_counter_changed)
        self.set_on_scan_done_func(self.chk_for_more_evregions)
        
        
    def on_abort_scan(self):
        """
        on_abort_scan(): description

        :returns: None
        """
        self._abort = True
        self.e712_wg.stop_wave_generator()
    

    def set_sscan_rec(self, sp_roi, e_roi):
        """
        set_line_sscan_rec(): description

        :param sp_roi: sp_roi description
        :type sp_roi: sp_roi type

        :param e_roi: e_roi description
        :type e_roi: e_roi type

        :returns: None
        """
        try:

            #reset total point counter
            #pol
            self.polScan.put('NPTS', len(self.setpointsPol))
            self.polScan.put('P1PA', self.setpointsPol)
            self.polScan.put('P1SM', 1) #table
            #off
            self.polScan.put('P2PA', self.setpointsOff)
            self.polScan.put('P2SM', 1) #table
            #angle
            self.polScan.put('P3PA', self.setpointsAngle)
            self.polScan.put('P3SM', 1) #table

            #EV
            self.evScan.put('NPTS', e_roi[NPOINTS])
            self.evScan.put('P1SP', e_roi[START])
            self.evScan.put('P1EP', e_roi[STOP])

            #self.setupScan.put('P4CP', e_roi[START])

        except:
            _logger.error('set_sscan_rec: failed a write to a PV')

    def set_LineSpecScan_use_hdw_accel_sscan_rec(self, single_lsts):
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

        # EV
        # here write all energies to table of setpoints
        self.evScan.put('NPTS', len(evs))
        self.evScan.put('P1PA', evs)
        self.evScan.put('P1SM', 1)  # table


        # load the wavefr
        MAIN_OBJ.device('e712_dwells').put(dwells)

    def configure(self, wdg_com, sp_id=0, ev_idx=0, line=True, spectra=False, block_disconnect_emit=False):
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
        _logger.info('configure: LineSpecSScanWithE712Wavegen %d' % sp_id)
        self.set_spatial_id(sp_id)
        self.wdg_com = wdg_com
        self.sp_rois = wdg_com[WDGCOM_SPATIAL_ROIS]
        self.sp_db = self.sp_rois[sp_id]
        self.sp_ids = list(self.sp_rois.keys())
        self.scan_type = dct_get(self.sp_db, SPDB_SCAN_PLUGIN_TYPE)
        self.scan_sub_type = dct_get(self.sp_db, SPDB_SCAN_PLUGIN_SUBTYPE)
        
        self.is_lxl = False
        self.is_pxp = False
        self.is_point_spec = False
        self.is_line_spec = False
        self.file_saved = False
        
        if(self.scan_sub_type == scan_sub_types.LINE_UNIDIR):
            self.is_lxl = True
            parms = self.cmdfile_parms['lxl_scan']
        else:
            self.is_pxp = True
            parms = self.cmdfile_parms['pxp_scan']
        
        self.set_cmdfile_params(parms)
        
        self.reload_base_scan_config()
        ########################
        
                
        if(ev_idx == 0):
            self.reset_evidx()
            self.reset_imgidx()
            self.final_data_dir = None
            self.line_column_cntr = 0

        self.update_roi_member_vars(self.sp_db)

        e_roi = self.e_rois[ev_idx]
        dct_put(self.sp_db, SPDB_RECT, ( e_roi[START], self.x_roi[START],  self.e_rois[-1][STOP], self.x_roi[STOP]))
        
        self.configure_sample_motors_for_scan()

        self.setpointsDwell = dct_get(e_roi, DWELL)
        #convert the Polarization QComboBox index values to the STXM Wrapper equivelants
        #self.setpointsPol = self.convert_polarity_points(dct_get(e_roi, 'EPU_POL_PNTS'))
        self.setpointsPol = dct_get(e_roi, EPU_POL_PNTS)
        self.setpointsOff = dct_get(e_roi, EPU_OFF_PNTS)
        self.setpointsAngle = dct_get(e_roi, EPU_ANG_PNTS)

        sps = dct_get(self.wdg_com, SPDB_SINGLE_LST_SP_ROIS)
        evs = dct_get(self.wdg_com, SPDB_SINGLE_LST_EV_ROIS)
        pols = dct_get(self.wdg_com, SPDB_SINGLE_LST_POL_ROIS)
        dwells = dct_get(self.wdg_com, SPDB_SINGLE_LST_DWELLS)
        
        self.dwell = e_roi[DWELL]
        
        #data shape for LineSPec scan = (  numEpu, numEv, numX)
        #                                  #images, #rows, #cols 
        self.numEPU = len(self.setpointsPol)
        self.numE = int(self.sp_db[SPDB_EV_NPOINTS])
        self.numSPIDS = len(self.sp_rois)
        self.numImages = 1
        
        self.numZX = self.zx_roi[NPOINTS]
        self.numZY = self.zy_roi[NPOINTS]
        
        # NOTE! currently only arbitrary line is supported when equal number of x and e points so use E points
        #self.numY = self.e_roi[NPOINTS]
        self.numX = self.numE
        self.numY = self.x_roi[NPOINTS]
        
        if(self.scan_type ==  scan_types.SAMPLE_LINE_SPECTRA):
            self.is_line_spec = True    
        else:
            _logger.error('LineSpecSSCAN: unable to determine scan type [%d]' % self.scan_type)
            return
        
        #reset signals so we can start clean
        if(block_disconnect_emit):
            self.blockSignals(True)
            
        self.disconnect_signals()
        
        if(block_disconnect_emit):
            self.blockSignals(False)
            
        dct = self.determine_samplexy_posner_pvs()
        
        accRange = 0
        #self.set_LineSpecScan_use_hdw_accel_sscan_rec(single_lsts={'sps': sps, 'evs': evs, 'pols': pols, 'dwells': dwells})
        self.set_sscan_rec(self.sp_db, e_roi)


        if(self.numImages > 1):
            self.stack = True
        else:        
            self.stack = False
            
        # depending on the current samplpositioning_mode perform a different configuration
        if (self.sample_positioning_mode == sample_positioning_modes.GONIOMETER):
            if (self.use_hdw_accel):
                self.config_for_goniometer_scan_hdw_accel(dct)
            else:
                self.config_for_goniometer_scan(dct)
        else:
            if (self.sample_positioning_mode == sample_positioning_modes.GONIOMETER):
                # goniometer_zoneplate mode
                self.configure_for_zxzy_fine_scan_hdw_accel(dct)
            elif ((self.sample_positioning_mode == sample_positioning_modes.COARSE) and (self.fine_sample_positioning_mode == sample_fine_positioning_modes.ZONEPLATE)):
                self.configure_for_coarse_zoneplate_fine_scan_hdw_accel(dct)
            else:
                # coarse_samplefine mode
                self.configure_for_samplefxfy_fine_scan_hdw_accel(dct)



        
        #self.data_shape = ('numImages', 'numY', 'numE')
        self.config_hdr_datarecorder(self.stack)
        #self.stack_scan = stack
        
        #THIS must be the last call
        self.finish_setup()
        self.new_spatial_start.emit(ev_idx)


    def configure_for_coarse_zoneplate_fine_scan_hdw_accel(self, dct):
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
        self.main_obj.device(DNM_ZONEPLATE_X).put('ServoPower', 1)
        self.main_obj.device(DNM_ZONEPLATE_Y).put('ServoPower', 1)

        self.main_obj.device(DNM_ZONEPLATE_X).put('velocity', 1000000.0)
        self.main_obj.device(DNM_ZONEPLATE_Y).put('velocity', 1000000.0)

        #this scan is used with and without the goniometer so setupScan maybe None
        if(self.setupScan):
            self.setupScan.set_positioner(1, self.main_obj.device(DNM_SAMPLE_X))
            self.setupScan.set_positioner(2, self.main_obj.device(DNM_SAMPLE_Y))

        #these are the SampleX SampleY motors
        #cx_mtr = self.main_obj.device(dct['cx_name'])
        #cy_mtr = self.main_obj.device(dct['cy_name'])

        #cx_mtr.put('Mode', 0)  # MODE_NORMAL
        #cy_mtr.put('Mode', 0)  # MODE_NORMAL

        self.set_config_devices_func(self.on_this_dev_cfg)
        self.sample_mtrx = self.sample_finex = self.main_obj.device(DNM_SAMPLE_X)
        self.sample_mtry = self.sample_finey = self.main_obj.device(DNM_SAMPLE_Y)

        self.sample_mtrx.put('Mode', 0)  # MODE_NORMAL
        self.sample_mtry.put('Mode', 0)  # MODE_NORMAL

        # Sx is moving to scan center nd fx is centered around 0, so move Sx to scan center
        #cx_mtr.move(self.x_roi[CENTER])
        #self.sample_finex.put('user_setpoint', self.x_roi[CENTER])
        self.sample_mtrx.put('user_setpoint', self.x_roi[CENTER])

        #cy_mtr.move(self.y_roi[CENTER])
        self.sample_mtry.put('user_setpoint', self.y_roi[CENTER])


        # config the sscan that makes sure to move goni xy and osa xy to the correct position for scan
        # the setupScan will be executed as the top level but not monitored
        self.num_points = self.numY



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
            # # pxp
            # self.gate.start()
            # time.sleep(0.25)
            # # here the gate is the clock src so make sure its running
            # self.gate.soft_trigger.put(1)
            # self.gate.wait_till_running()
            #
            # self.counter.start()
            # self.counter.wait_till_running()
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

        y_startatend_flags = []

        y_start_mode = []

        sp_roi_ids = []

        for sp_id in self.sp_rois:
            sp_db = self.sp_rois[sp_id]
            e_rois = dct_get(sp_db, SPDB_EV_ROIS)
            ev_idx = self.get_evidx()
            dwell = e_rois[ev_idx][DWELL]

            if (sample_positioning_mode == sample_positioning_modes.GONIOMETER):
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
            y_startatend_flags.append(0)

            if (self.is_pxp):
                mode = 0
                # program waveforms into tables
                self.e712_wg.send_wave(sp_id, x_roi, y_roi, dwell, mode, x_auto_ddl=self.x_auto_ddl, x_force_reinit=self.x_use_reinit_ddl, y_is_pxp=True)
                x_useddl_flags.append(0)
                x_reinitddl_flags.append(0)
                x_startatend_flags.append(0)
            else:
                mode = 1
                # program waveforms into tables
                #modify y_roi to reflect that the number of y points is only 1, this number is written into the num of cycles to execute per wavegen execution
                y_roi[NPOINTS] = 1
                ddl_data = self.e712_wg.send_wave(sp_id, x_roi, y_roi, dwell, mode, x_auto_ddl=self.x_auto_ddl, x_force_reinit=self.x_use_reinit_ddl, y_is_pxp=False)


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

        # VERY IMPORTANT: make sure that the WG only executes 1 time for each X line
        #remember the spec line is only 1 time per wavegen execution, this pv is read by the gate_cntr_cfg EPICS application(SNL)
        # to set the number of cycles to execute
        MAIN_OBJ.device('e712_y_npts').put([1])

        MAIN_OBJ.device('e712_x_useddl').put(x_useddl_flags)
        MAIN_OBJ.device('e712_x_usereinit').put(x_reinitddl_flags)
        MAIN_OBJ.device('e712_x_strtatend').put(x_startatend_flags)

        # 0 = OFF, 1=ON
        self.main_obj.device('e712_y_strtatend').put(y_startatend_flags)

        MAIN_OBJ.device('e712_x_start_mode').put(x_start_mode)
        MAIN_OBJ.device('e712_y_start_mode').put(y_start_mode)

        MAIN_OBJ.device('e712_sp_ids').put(sp_roi_ids)

        self.gateCntrCfgScan.put('NPTS', ttl_wavtables)
        #make sure that the num of cycles is always 1
        self.e712_wg.set_num_cycles(1)

        _logger.info('Estemated time to complete scan is: %s' % self.e712_wg.get_new_time_estemate())

    def on_this_dev_cfg(self):
        """
        on_this_dev_cfg(): description

        :returns: None
        this is an API method to configure the gate, shutter and counter devices for this scan
        """
        # if((self.is_pxp) or (self.is_point_spec)):
        if (self.is_pxp):
            if (self.use_hdw_accel):
                #numY == the number of X points but numX is the energies
                set_devices_for_e712_wavegen_point_scan(self.scan_type, self.dwell, self.numY, self.counter,numE=self.numE)
                # set_devices_for_e712_wavegen_point_scan(scan_type, dwell, numX, counter, numE=0)
            else:
                # set_devices_for_point_scan(self.roi, self.gate, self.counter, self.shutter)
                set_devices_for_point_scan(self.scan_type, self.dwell, self.numE, self.numX, self.gate, self.counter,
                                           self.shutter)
        else:
            if(self.use_hdw_accel):
                set_devices_for_e712_wavegen_line_scan(self.dwell, self.numX, self.gate, self.counter)
            else:
                set_devices_for_line_scan(self.dwell, self.numX, self.gate, self.counter, self.shutter)

        #make sure they are started
        self.gate.start()
        self.counter.start()
    
    def linespec_pxp_counter_changed(self, col, xxx_todo_changeme):
        """
        linespec_counter_changed(): description

        :param row: row description
        :type row: row type

        :param (x: (x description
        :type (x: (x type

        :param y): y) description
        :type y): y) type

        :returns: None
        """
        (row, val) = xxx_todo_changeme
        """
        Used to override the sampleImageScanWithEnergy.on_changed handler.
        This is a slot that is connected to the counters changed signal        
        """
        if((self.ttl_pnts % self.numY) == 0):
            if(self.ttl_pnts is not 0):
                self.line_column_cntr += 1
        #print 'linespec_pxp_counter_changed: line_column_cntr=%d row=%d val=%d' % (self.line_column_cntr, row, val)
        #print 'linespec_pxp_counter_changed: ttl_pnts=%d' % (self.ttl_pnts)
        self.ttl_pnts += 1
        
        dct = self.init_counter_to_plotter_com_dct(make_counter_to_plotter_com_dct())
#         _imgidx = self.get_imgidx()
        #1, 10, 40
        _imgidx = self.get_imgidx()
        self.data[_imgidx, row, self.line_column_cntr] = val
        
        dct[CNTR2PLOT_ROW] = int(row)
        dct[CNTR2PLOT_COL] = int(self.line_column_cntr)
        dct[CNTR2PLOT_VAL] = int(val)
        self.sigs.changed.emit(dct)

    def linespec_counter_changed(self, col, data, counter_name=DNM_DEFAULT_COUNTER):
        """
        linespec_counter_changed(): description
        :param row: row description
        :type row: row type
        :param (x: (x description
        :type (x: (x type

        :param y): y) description
        :type y): y) type
        :returns: None
            Used to override the sampleImageScanWithEnergy.on_changed handler.
            This is a slot that is connected to the counters changed signal

            The line scan data is opposit to all the other scans in that the axis' are
                |                    |
            X/Y |            NOT  eV |
                |                    |
                |__________          |__________
                    eV                    X/Y
        """
        sp_id = int(self.main_obj.device('e712_current_sp_id').get_position())
        self.set_spatial_id(sp_id)

        dct = self.init_counter_to_plotter_com_dct(make_counter_to_plotter_com_dct())
        # print 'linespec_pxp_counter_changed: line_column_cntr=%d row=%d val=%d' % (self.line_column_cntr, row, val)
        # print 'linespec_pxp_counter_changed: ttl_pnts=%d' % (self.ttl_pnts)
        self.ttl_pnts += 1

        _imgidx = self.get_imgidx()
        _imgidx = 0

        _dct = self.get_img_idx_map(_imgidx)
        pol_idx = _dct['pol_idx']
        e_idx = _dct['e_idx']

        if (sp_id not in list(self.spid_data[counter_name].keys())):
            _logger.error('sp_id[%d] does not exist in self.spid_data keys' % sp_id)
            print('sp_id[%d] does not exist in self.spid_data keys' % sp_id)
            print('self.spid_data.keys=', list(self.spid_data[counter_name].keys()))
            return

        # self.spid_data[counter_name][sp_id][pol_idx][_imgidx, :, self.line_column_cntr] = np.flipud( data[0:int(self.numY)])
        #self.spid_data[counter_name][sp_id][pol_idx][_imgidx, :, self.line_column_cntr] = data[0:self.numY]

        #print self.spid_data[counter_name][sp_id][pol_idx].shape
        #print data.shape
        #print data[0:self.numY]
        self.spid_data[counter_name][sp_id][pol_idx][_imgidx, :, self.line_column_cntr] = data[0:self.numY]


        dct[CNTR2PLOT_ROW] = None
        dct[CNTR2PLOT_COL] = int(self.line_column_cntr)
        dct[CNTR2PLOT_VAL] = data[0:self.numY]
        dct[CNTR2PLOT_IS_LINE] = True
        dct[CNTR2PLOT_IS_POINT] = False

        self.line_column_cntr += 1
        self.sigs.changed.emit(dct)

        prog = float(float(self.line_column_cntr + 0.75) / float(self.numE)) * 100.0
        prog_dct = make_progress_dict(sp_id=dct[CNTR2PLOT_SP_ID], percent=prog)
        self.low_level_progress.emit(prog_dct)



        #     def linespec_counter_changed(self, col, data):
#         """
#         linespec_counter_changed(): description
#
#         :param row: row description
#         :type row: row type
#
#         :param (x: (x description
#         :type (x: (x type
#
#         :param y): y) description
#         :type y): y) type
#
#         :returns: None
#         """
#         """
#         Used to override the sampleImageScanWithEnergy.on_changed handler.
#         This is a slot that is connected to the counters changed signal
#
#         The line scan data is opposit to all the other scans in that the axis' are
#             |                    |
#         X/Y |            NOT  eV |
#             |                    |
#             |__________          |__________
#                 eV                    X/Y
#         """
#         dct = self.init_counter_to_plotter_com_dct(make_counter_to_plotter_com_dct())
# #         _imgidx = self.get_imgidx()
# #         _evidx = self.get_evidx()
# #         #self.data[_imgidx, row, :] = data[0:self.numX]
# #         #self.data[_imgidx, :, col] = data[0:int(self.numY)]
# #         #self.data[_imgidx, :, col] = data[0:int(self.numX)]
# #         #self.data[_imgidx, :, col] = data[0:int(self.numX)]
# #         #print self.data.shape
# #         #print 'linespec_counter_changed: col=%d numX=%d' % (col, int(self.numY))
# #         #self.data[_imgidx, :, col] = data[0:int(self.numY)]
# #         #self.data[_imgidx, :, col] = data[0:int(self.numY)]
# #         self.data[_imgidx, :, col] = np.flipud(data[0:int(self.numY)])
# #         dct = {}
# #         dct['row'] = None
# #         dct['col'] = col
# #         dct['val'] = data[0:self.numY]
# #         dct['img_idx'] = _imgidx
# #         dct['ev_idx'] = _evidx
# #         dct['is_pxp'] = self.is_pxp
#
#         #print 'linespec_pxp_counter_changed: line_column_cntr=%d row=%d val=%d' % (self.line_column_cntr, row, val)
#         #print 'linespec_pxp_counter_changed: ttl_pnts=%d' % (self.ttl_pnts)
#         self.ttl_pnts += 1
#
#         _imgidx = self.get_imgidx()
#         #self.data[_imgidx, :, col] = np.flipud(data[0:int(self.numY)])
#         self.data[_imgidx, :, self.line_column_cntr] = np.flipud(data[0:int(self.numY)])
#         dct[CNTR2PLOT_ROW] = None
#         #dct[CNTR2PLOT_COL] = int(col)
#         dct[CNTR2PLOT_COL] = int(self.line_column_cntr)
#         dct[CNTR2PLOT_VAL] = data[0:self.numY]
#         self.line_column_cntr += 1
#         self.sigs.changed.emit(dct)



    # def modify_config_for_hdw_accel(self):
    #     '''
    #     Here I need to make the calls to send the commands that generate the waveform on the E712 for the current E_roi, by the end
    #     of this function everything should be ready  (as far as the E712 is concerned) to just call
    #         IOCE712:ExecWavgen by the sscan record
    #
    #     This function needs to :
    #      - program the E712 with all sp_roi's for each dwell time using 1 wavtable per dwell time
    #     and spatial region.
    #      - set the number of points in the sscan record that starts the E712 wavegenerator to the number of wavtables used above
    #      - set the P1(x) and P2(y) PxPA tables in the sscan record that starts the E712 wavegenerator with the wavtable
    #      numbers that were used above
    #
    #
    #     :return:
    #     '''
    #     sample_positioning_mode = self.main_obj.get_sample_positioning_mode()
    #     fine_sample_positioning_mode = self.main_obj.get_fine_sample_positioning_mode()
    #     #start gate and counters
    #     if (self.is_pxp):
    #         mode = 0
    #         # pxp
    #         self.gate.start()
    #         time.sleep(0.25)
    #         # here the gate is the clock src so make sure its running
    #         self.gate.soft_trigger.put(1)
    #         self.gate.wait_till_running()
    #
    #         self.counter.start()
    #         self.counter.wait_till_running()
    #     else:
    #         mode = 1
    #         #self.gate.start()
    #         #self.gate.wait_till_running()
    #
    #         #self.counter.start()
    #         #self.counter.wait_till_running()
    #
    #     # create usetable map
    #     wavtable_map = self.e712_wg.create_wavgen_usetable_map(self.sp_ids)
    #     # clear previous wavetables
    #     self.e712_wg.clear_wavetables()
    #
    #     #for the current ev index
    #     #for each sp_db in sp_rois call sendwave() to create the wavetable on the E712 and add wavtable ID to list,
    #     #keep a running total of number of wavtables used starting from 1
    #     #set the NPTS of the btm sscan to equal the total number of wavtables used above
    #     #for each P1 and P2 of the bottom level sscan record write the list of each wavtable ID's to the sscan rec
    #
    #     #self.img_data = {}
    #
    #     IMMEDIATELY = 1
    #
    #     ttl_wavtables = 0
    #     #the following lists are populated and then written to placeholder waveform PV's that will be used
    #     #by SNL code to load the next set of params for the next spatial region as they are being executed
    #     x_wavtbl_id_lst = []
    #     y_wavtbl_id_lst = []
    #
    #     x_npnts_lst = []
    #     y_npnts_lst = []
    #
    #     x_reset_posns = []
    #     y_reset_posns = []
    #
    #     x_start_mode = []
    #     x_useddl_flags = []
    #     x_reinitddl_flags = []
    #     x_startatend_flags = []
    #
    #     y_start_mode = []
    #
    #     sp_roi_ids = []
    #
    #     for sp_id in self.sp_rois:
    #         sp_db = self.sp_rois[sp_id]
    #         e_rois = dct_get(sp_db, SPDB_EV_ROIS)
    #         ev_idx = self.get_evidx()
    #         dwell = e_rois[ev_idx][DWELL]
    #
    #
    #         if(fine_sample_positioning_mode == sample_fine_positioning_modes.ZONEPLATE):
    #             x_roi = dct_get(sp_db, SPDB_ZX)
    #             y_roi = dct_get(sp_db, SPDB_ZY)
    #             x_npnts = x_roi[NPOINTS]
    #             y_npnts = y_roi[NPOINTS]
    #
    #         else:
    #             x_roi = dct_get(sp_db, SPDB_X)
    #             y_roi = dct_get(sp_db, SPDB_Y)
    #             x_npnts = x_roi[NPOINTS]
    #             y_npnts = y_roi[NPOINTS]
    #
    #         #new data struct inparrallel with orig self.data, self.numImages = total numEv and num Pol
    #         #self.img_data[sp_id] = np.zeros((self.numImages, y_npnts, x_npnts), dtype=np.float32)
    #
    #
    #         # self.spid_data[sp_id] = {}
    #         # #make a set of arrays for final data
    #         # for q in range(self.numEPU):
    #         #     self.spid_data[sp_id][q] = np.zeros((self.numE, y_npnts, x_npnts), dtype=np.float32)
    #
    #
    #         x_reset_pos = x_roi[START]
    #         y_reset_pos = y_roi[START]
    #         x_axis_id = self.base_zero(self.e712_wg.get_x_axis_id())
    #         y_axis_id = self.base_zero(self.e712_wg.get_y_axis_id())
    #
    #         sp_roi_ids.append(sp_id)
    #         # build a list of wavtable IDs used for this scan
    #         x_wavtbl_id_lst.append( wavtable_map[sp_id][x_axis_id])
    #         y_wavtbl_id_lst.append( wavtable_map[sp_id][y_axis_id])
    #         x_npnts_lst.append(int(x_npnts))
    #         y_npnts_lst.append(int(y_npnts))
    #         x_reset_posns.append(x_reset_pos)
    #         y_reset_posns.append(y_reset_pos)
    #
    #         x_start_mode.append(IMMEDIATELY)
    #         y_start_mode.append(IMMEDIATELY)
    #
    #         ddl_data = None
    #         if (self.is_pxp):
    #             mode = 0
    #             # program waveforms into tables
    #             self.e712_wg.send_wave(sp_id, x_roi, y_roi, dwell, mode, x_auto_ddl=self.x_auto_ddl,
    #                                    x_force_reinit=self.x_use_reinit_ddl)
    #             x_useddl_flags.append(0)
    #             x_reinitddl_flags.append(0)
    #             x_startatend_flags.append(0)
    #         else:
    #             mode = 1
    #             # program waveforms into tables
    #             ddl_data = self.e712_wg.send_wave(sp_id, x_roi, y_roi, dwell, mode, x_auto_ddl=self.x_auto_ddl,
    #                                        x_force_reinit=self.x_use_reinit_ddl)
    #
    #
    #             #ddl_data = self.e712_wg.get_stored_ddl_table()
    #             ddl_tbl_pv = MAIN_OBJ.device('e712_ddl_tbls')
    #             if(ddl_data is not None):
    #                 print 'load this ddl table into the pvs for this spatial region'
    #
    #                 ddl_tbl_pv[ttl_wavtables].put(ddl_data)
    #                 x_useddl_flags.append(1)
    #                 x_reinitddl_flags.append(0)
    #                 x_startatend_flags.append(0)
    #             else:
    #                 print 'set the ddl pv waveform to 0s'
    #                 ddl_tbl_pv[ttl_wavtables].put([0,0,0,0,0,0])
    #                 x_useddl_flags.append(0)
    #                 x_reinitddl_flags.append(1)
    #                 x_startatend_flags.append(0)
    #
    #         #keep running total
    #         ttl_wavtables += 1
    #
    #     #map_lst, self.spid_data = self.make_stack_data_map(numEv=self.numE, numPol=self.numEPU, numSp=self.numSPIDS, x_npnts_lst=x_npnts_lst, y_npnts_lst=y_npnts_lst)
    #
    #     # write the x motor reset positions to the waveform pv
    #     MAIN_OBJ.device('e712_xresetposns').put(x_reset_posns)
    #     MAIN_OBJ.device('e712_yresetposns').put(y_reset_posns)
    #     #write the wavtable ids to the waveform pv
    #     MAIN_OBJ.device('e712_x_wavtbl_ids').put(x_wavtbl_id_lst)
    #     MAIN_OBJ.device('e712_y_wavtbl_ids').put(y_wavtbl_id_lst)
    #
    #     MAIN_OBJ.device('e712_x_npts').put(x_npnts_lst)
    #     MAIN_OBJ.device('e712_y_npts').put(y_npnts_lst)
    #
    #     MAIN_OBJ.device('e712_x_useddl').put(x_useddl_flags)
    #     MAIN_OBJ.device('e712_x_usereinit').put(x_reinitddl_flags)
    #     MAIN_OBJ.device('e712_x_strtatend').put(x_startatend_flags)
    #
    #     MAIN_OBJ.device('e712_x_start_mode').put(x_start_mode)
    #     MAIN_OBJ.device('e712_y_start_mode').put(y_start_mode)
    #
    #     MAIN_OBJ.device('e712_sp_ids').put(sp_roi_ids)
    #
    #
    #     self.gateCntrCfgScan.put('NPTS', ttl_wavtables)
    #
    #
    #     #need to make sure that the gate and counter are running before leaving here
    #     _logger.info('Estemated time to complete scan is: %s' % self.e712_wg.get_new_time_estemate())

