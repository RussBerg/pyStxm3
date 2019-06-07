'''
Created on Sep 26, 2016

@author: bergr
'''
import os
import numpy as np

from bluesky.plans import count, scan, grid_scan, scan_nd
import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp
from cycler import cycler

from bcm.devices.device_names import *

from cls.applications.pyStxm import abs_path_to_ini_file
from cls.applications.pyStxm.bl10ID01 import MAIN_OBJ
from cls.scanning.BaseScan import BaseScan, SIMULATE_SPEC_DATA
from cls.utils.roi_dict_defs import *
from cls.utils.prog_dict_utils import make_progress_dict

from cls.types.stxmTypes import scan_types, scan_sub_types, \
                                        energy_scan_order_types, sample_positioning_modes

from cls.utils.dict_utils import dct_get, dct_put
from cls.utils.log import get_module_logger
from cls.utils.cfgparser import ConfigClass
from cls.utils.json_utils import dict_to_json
from cls.scan_engine.bluesky.data_emitters import ImageDataEmitter

from cls.plotWidgets.utils import *

_logger = get_module_logger(__name__)
appConfig = ConfigClass(abs_path_to_ini_file)

class LineSpecScanClass(BaseScan):
    '''
    This class 
    '''
    
    def __init__(self, main_obj=None):
        """
        __init__(): description

        :returns: None
        """
        super(LineSpecScanClass, self).__init__('%sstxm'% MAIN_OBJ.get_sscan_prefix(),'LINESPEC', main_obj=main_obj)

    
    def init_subscriptions(self, ew, func):
        '''
        over ride the base init_subscriptions because we need to use the number of rows from the self.zz_roi instead of
        self.y_roi
        :param ew:
        :param func:
        :return:
        '''

        if(self.is_pxp):
            self._emitter_cb = ImageDataEmitter('%s_single_value_rbv' % DNM_DEFAULT_COUNTER, y=DNM_ZONEPLATE_Z_BASE, x=DNM_SAMPLE_X,
                                                    scan_type=self.scan_type, bi_dir=self._bi_dir)
            self._emitter_cb.set_row_col(rows=self.zz_roi[NPOINTS], cols=self.x_roi[NPOINTS])
            self._emitter_sub = ew.subscribe_cb(self._emitter_cb)
            self._emitter_cb.new_plot_data.connect(func)
        else:
            self._emitter_cb = ImageDataEmitter('%s_single_value_rbv' % DNM_DEFAULT_COUNTER, y=DNM_ZONEPLATE_Z_BASE,
                                                x=DNM_SAMPLE_X,
                                                scan_type=self.scan_type, bi_dir=self._bi_dir)
            self._emitter_cb.set_row_col(rows=self.zz_roi[NPOINTS], cols=self.x_roi[NPOINTS])
            self._emitter_sub = ew.subscribe_cb(self._emitter_cb)
            self._emitter_cb.new_plot_data.connect(func)

    def make_pxp_scan_plan(self, dets, gate, md=None, bi_dir=False):
        '''
            gate and counter need to be staged for pxp
        :param dets:
        :param gate:
        :param bi_dir:
        :return:
        '''
        dev_list = self.main_obj.main_obj[DEVICES].devs_as_list()
        self._bi_dir = bi_dir
        if (md is None):
            md = {'metadata': dict_to_json(
                self.make_standard_data_metadata(entry_name='entry0', scan_type=self.scan_type))}
        mtr_dct = self.determine_samplexy_posner_pvs()

        @bpp.baseline_decorator(dev_list)
        @bpp.stage_decorator(dets)
        # @bpp.run_decorator(md={'entry_name': 'entry0', 'scan_type': scan_types.DETECTOR_IMAGE})
        def do_scan():

            #mtr_x = self.main_obj.device(DNM_SAMPLE_X)
            #mtr_y = self.main_obj.device(DNM_SAMPLE_Y)
            mtr_x = self.main_obj.device(mtr_dct['cx_name'])
            mtr_y = self.main_obj.device(mtr_dct['cy_name'])
            mtr_ev = self.main_obj.device(DNM_ENERGY)
            shutter = self.main_obj.device(DNM_SHUTTER)

            x_traj = cycler(mtr_x, self.x_roi[SETPOINTS])
            y_traj = cycler(mtr_y, self.y_roi[SETPOINTS])
            zz_traj = cycler(mtr_ev, self.zz_roi[SETPOINTS])

            yield from bps.stage(gate)
            # this starts the wavgen and waits for it to finish without blocking the Qt event loop
            # the detector will be staged automatically by the grid_scan plan
            shutter.open()
            yield from scan_nd(dets, zz_traj * (y_traj + x_traj),
                               md=md)

            shutter.close()
            # yield from bps.wait(group='e712_wavgen')
            yield from bps.unstage(gate)

            print('LineSpecClass PxP: make_scan_plan Leaving')

        return (yield from do_scan())

    def make_lxl_scan_plan(self, dets, gate, md=None, bi_dir=False):
        '''

        this needs to be adapted to be a fly scan, setup SampleX to trigger at correct location, set scan velo and acc range
        and then call scan, gate an d counter need to be staged for lxl
        :param dets:
        :param gate:
        :param bi_dir:
        :return:
        '''
        dev_list = self.main_obj.main_obj[DEVICES].devs_as_list()
        self._bi_dir = bi_dir

        if (md is None):
            md = {'metadata': dict_to_json(
                self.make_standard_data_metadata(entry_name='entry0', scan_type=self.scan_type))}

        @bpp.baseline_decorator(dev_list)
        @bpp.stage_decorator(dets)
        def do_scan():

            mtr_x = self.main_obj.device(DNM_SAMPLE_X)
            mtr_y = self.main_obj.device(DNM_SAMPLE_Y)
            mtr_ev = self.main_obj.device(DNM_ENERGY)
            shutter = self.main_obj.device(DNM_SHUTTER)

            yield from bps.stage(gate)

            shutter.open()
            bps.open_run(md=md)

            # go to start of line
            yield from bps.mv(mtr_x, self.x_roi[START], mtr_y, self.y_roi[CENTER])

            #now do a horizontal line for every new zoneplate Z setpoint
            for sp in self.zz_roi[SETPOINTS]:
                yield from bps.mv(mtr_ev, sp)
                yield from bps.mv(mtr_x, self.x_roi[STOP])
                yield from bps.mv(mtr_x, self.x_roi[START])

            shutter.close()
            # yield from bps.wait(group='e712_wavgen')
            yield from bps.unstage(gate)
            bps.close_run()
            print('LineSpecClass LxL: make_scan_plan Leaving')

        return (yield from do_scan())
                            
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
        _logger.info('configure: LineScan %d' % sp_id)
        self.set_spatial_id(sp_id)
        self.wdg_com = wdg_com
        self.sp_rois = wdg_com[WDGCOM_SPATIAL_ROIS]
        self.sp_db = self.sp_rois[sp_id]
        self.scan_type = dct_get(self.sp_db, SPDB_SCAN_PLUGIN_TYPE)
        self.scan_sub_type = dct_get(self.sp_db, SPDB_SCAN_PLUGIN_SUBTYPE)
        
        self.is_lxl = False
        self.is_pxp = False
        self.is_point_spec = False
        self.is_line_spec = False
        self.file_saved = False

        self.main_obj.device('e712_current_sp_id').put(sp_id)
        
        if(self.scan_sub_type == scan_sub_types.LINE_UNIDIR):
            self.is_lxl = True
            parms = self.cmdfile_parms['lxl_scan']
        else:
            self.is_pxp = True
            parms = self.cmdfile_parms['pxp_scan']
        
        #self.set_cmdfile_params(parms)
        
        #self.reload_base_scan_config()
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
        #convert the Polarity QComboBox index values to the STXM Wrapper equivelants
        #self.setpointsPol = self.convert_polarity_points(dct_get(e_roi, 'EPU_POL_PNTS'))
        self.setpointsPol = dct_get(e_roi, EPU_POL_PNTS)
        self.setpointsOff = dct_get(e_roi, EPU_OFF_PNTS)
        self.setpointsAngle = dct_get(e_roi, EPU_ANG_PNTS)
        
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
        self.numX = int(self.numE)
        self.numY = int(self.x_roi[NPOINTS])
        
        if(self.scan_type ==  scan_types.SAMPLE_LINE_SPECTRUM):
            self.is_line_spec = True    
        else:
            _logger.error('LineSpecSSCAN: unable to determine scan type [%d]' % self.scan_type)
            return
        
        #reset signals so we can start clean
        # if(block_disconnect_emit):
        #     self.blockSignals(True)
        #
        # self.disconnect_signals()
        #
        # if(block_disconnect_emit):
        #     self.blockSignals(False)
            
        dct = self.determine_samplexy_posner_pvs()
        
        accRange = 0
        # if(self.is_lxl):
        #     self.set_line_sscan_rec(self.sp_db, e_roi)
        #     #self.set_on_counter_changed_func(self.linespec_lxl_counter_changed)
        #     #NOV6 self.set_optimize_scan_func(self.optimize_lxl_linespec_scan)
        # else:
        #     self.set_point_sscan_rec(self.sp_db, e_roi)
        #     #self.set_on_counter_changed_func(self.linespec_pxp_counter_changed)
        #     #NOV6 self.set_optimize_scan_func(self.optimize_pxp_linespec_scan)
        #
        # #self.set_on_scan_done_func(self.chk_for_more_evregions)
        #

        if(self.numImages > 1):
            self.stack = True
        else:        
            self.stack = False
            
        #self.scanlist = [ self.xScan , self.yScan, self.polScan, self.evScan]
        #self.mtr_list = [ self.xScan.P1 , self.yScan.P1, self.polScan.P1, self.polScan.P2, self.polScan.P3, self.evScan.P1]
        
        if(self.sample_positioning_mode == sample_positioning_modes.GONIOMETER):
            self.config_for_goniometer_scan(dct)
        
        else:
            self.config_for_sample_holder_scan(dct)
        
        #self.data_shape = ('numImages', 'numY', 'numE')
        self.config_hdr_datarecorder(self.stack)
        #self.stack_scan = stack
        
        #THIS must be the last call
        self.finish_setup()
        self.new_spatial_start.emit(ev_idx)
        
    def on_this_dev_cfg(self):
        """
        on_this_dev_cfg(): description

        :returns: None
        """
        """
        this is an API method to configure the gate, shutter and counter devices for this scan
        """
        # if(self.is_lxl):
        #     #set_devices_for_line_scan(self.dwell, self.numX, self.gate, self.counter, self.shutter)
        #     #remember that the number of points per line is plotted on the vertical axis so use numY for the number of points
        #     set_devices_for_line_scan(self.dwell, self.numY, self.gate, self.counter, self.shutter)
        # else:
        #     #set_devices_for_point_scan(self.roi, self.gate, self.counter, self.shutter)
        #     #NOTE using numY to set thenumber of rows in this case the number of columns but it is "rows" according to the CI task
        #     set_devices_for_point_scan(self.scan_type, self.dwell, self.numE, self.numY, self.gate, self.counter, self.shutter)
        pass
    
#     def linespec_pxp_counter_changed(self, col, (row, val), counter_name='counter0'):
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
#         """
#         sp_id = int(self.main_obj.device('e712_current_sp_id').get_position())
#         if (sp_id not in self.spid_data[counter_name].keys()):
#             _logger.error('sp_id[%d] does not exist in self.spid_data keys' % sp_id)
#             print 'sp_id[%d] does not exist in self.spid_data keys' % sp_id
#             print 'self.spid_data.keys=', self.spid_data[counter_name].keys()
#             return
#
#         self.set_spatial_id(sp_id)
#         _imgidx = self.get_imgidx()
#         _imgidx = 0
#         _dct = self.get_img_idx_map(_imgidx)
#         pol_idx = _dct['pol_idx']
#         e_idx = _dct['e_idx']
#
#         if((self.ttl_pnts % self.numY) == 0):
#             if(self.ttl_pnts is not 0):
#                 self.line_column_cntr += 1
#         #print 'linespec_pxp_counter_changed: line_column_cntr=%d row=%d val=%d' % (self.line_column_cntr, row, val)
#         #print 'linespec_pxp_counter_changed: ttl_pnts=%d' % (self.ttl_pnts)
#         self.ttl_pnts += 1
#
#         dct = self.init_counter_to_plotter_com_dct(make_counter_to_plotter_com_dct())
# #       #sept11        self.data[_imgidx, row, self.line_column_cntr] = val
#
#         self.spid_data[counter_name][sp_id][pol_idx][_imgidx, row, self.line_column_cntr] = val
#
#         dct[CNTR2PLOT_ROW] = int(row)
#         dct[CNTR2PLOT_COL] = int(self.line_column_cntr)
#         dct[CNTR2PLOT_VAL] = int(val)
#         self.sigs.changed.emit(dct)
#
#
#
#     def linespec_lxl_counter_changed(self, col, data, counter_name=DNM_DEFAULT_COUNTER):
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
#         sp_id = int(self.main_obj.device('e712_current_sp_id').get_position())
#         self.set_spatial_id(sp_id)
#
#         dct = self.init_counter_to_plotter_com_dct(make_counter_to_plotter_com_dct())
#         #print 'linespec_pxp_counter_changed: line_column_cntr=%d row=%d val=%d' % (self.line_column_cntr, row, val)
#         #print 'linespec_pxp_counter_changed: ttl_pnts=%d' % (self.ttl_pnts)
#         self.ttl_pnts += 1
#
#         _imgidx = self.get_imgidx()
#         _imgidx = 0
#
#         _dct = self.get_img_idx_map(_imgidx)
#         pol_idx = _dct['pol_idx']
#         e_idx = _dct['e_idx']
#
#         if(sp_id not in self.spid_data[counter_name].keys()):
#             _logger.error('sp_id[%d] does not exist in self.spid_data keys' % sp_id)
#             print 'sp_id[%d] does not exist in self.spid_data keys' % sp_id
#             print 'self.spid_data.keys=', self.spid_data[counter_name].keys()
#             return
#
#         #self.spid_data[counter_name][sp_id][pol_idx][_imgidx, :, self.line_column_cntr] = np.flipud( data[0:int(self.numY)])
#         self.spid_data[counter_name][sp_id][pol_idx][_imgidx, :, self.line_column_cntr] = data[0:self.numY]
#
#         dct[CNTR2PLOT_ROW] = None
#         dct[CNTR2PLOT_COL] = int(self.line_column_cntr)
#         dct[CNTR2PLOT_VAL] = data[0:self.numY]
#         self.line_column_cntr += 1
#         self.sigs.changed.emit(dct)
#
#
#         prog = float(float(self.line_column_cntr + 0.75) / float(self.numE)) * 100.0
#         prog_dct = make_progress_dict(sp_id=dct[CNTR2PLOT_SP_ID], percent=prog)
#         self.low_level_progress.emit(prog_dct)


