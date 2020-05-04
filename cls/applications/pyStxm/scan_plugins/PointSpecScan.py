'''
Created on Sep 26, 2016

@author: bergr
'''

import os
from bcm.devices.device_names import *

from bluesky.plans import scan
import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp

from cls.applications.pyStxm.main_obj_init import MAIN_OBJ
from bcm.devices.device_names import *
from cls.scanning.BaseScan import BaseScan, SIMULATE_IMAGE_DATA, SIM_DATA
from cls.scanning.SScanClass import SScanClass
from cls.scanning.scan_cfg_utils import set_devices_for_point_scan
from cls.utils.roi_dict_defs import *
from cls.utils.dict_utils import dct_get, dct_put
from cls.utils.log import get_module_logger
from cls.utils.prog_dict_utils import make_progress_dict
from cls.types.stxmTypes import sample_fine_positioning_modes, spectra_type_scans, scan_types
from cls.scan_engine.bluesky.data_emitters import SpecDataEmitter
from cls.utils.json_utils import dict_to_json
from cls.scan_engine.bluesky.bluesky_defs import bs_dev_modes
from cls.scan_engine.bluesky.test_gate import trig_src_types
from cls.plotWidgets.utils import *

USE_E712_HDW_ACCEL = MAIN_OBJ.get_preset_as_bool('USE_E712_HDW_ACCEL', 'BL_CFG_MAIN')

_logger = get_module_logger(__name__)


class PointSpecScanClass(BaseScan):
    """ a scan for executing a positioner line pxp scan in X, """

    def __init__(self, main_obj=None):
        """
        __init__(): description

        :returns: None
        """
        super(PointSpecScanClass, self).__init__('%sstxm' % MAIN_OBJ.get_sscan_prefix(), SPDB_X, main_obj=MAIN_OBJ)

    def configure_devs(self, dets, gate):
        gate.set_dwell(self.dwell)
        gate.set_trig_src(trig_src_types.NORMAL_PXP)
        gate.set_mode(bs_dev_modes.NORMAL_PXP)

        # need to handle this better for multiple detectors, in the future todo
        dets[0].set_dwell(self.dwell)

    def add_spids_xy_setpoints(self, md={}):
        md['sp_id_setpoints'] = {}
        dct = {}
        for sp_id in self._master_sp_id_list:
            #get x and y setpoints
            x_sp = self.sp_rois[sp_id]['X']['CENTER']
            y_sp = self.sp_rois[sp_id]['Y']['CENTER']
            #these are used by the nxstxm suitcase to record the correct SAMPLE_X and SAMPLE_Y positions for the spectra
            dct[sp_id] = {'x_sp': x_sp, 'y_sp': y_sp}
        md['sp_id_setpoints'] = dict_to_json(dct)
        return(md)

    def make_pxp_scan_plan(self, dets, gate, md=None, bi_dir=False):
        dev_list = self.main_obj.main_obj[DEVICES].devs_as_list()
        self._bi_dir = bi_dir

        if (md is None):
            md = {'metadata': dict_to_json(
                self.make_standard_metadata(entry_name='entry0', scan_type=self.scan_type, override_xy_posner_nms=True))}
        #override the POSIIONER so tha nxstxm and can export properly
        #md = self.add_spids_xy_setpoints(md)
        @bpp.baseline_decorator(dev_list)
        @bpp.stage_decorator(dets)
        @bpp.run_decorator(md=md)
        def do_scan():


            mtr_ev = self.main_obj.device(DNM_ENERGY)
            # if (self.is_zp_scan):
            #     mtr_x = self.main_obj.device(DNM_ZONEPLATE_X)
            #     mtr_y = self.main_obj.device(DNM_ZONEPLATE_Y)
            #
            # else:
            #     mtr_x = self.main_obj.device(DNM_SAMPLE_FINE_X)
            #     mtr_y = self.main_obj.device(DNM_SAMPLE_FINE_Y)
            mtr_x = self.main_obj.device(DNM_SAMPLE_X)
            mtr_y = self.main_obj.device(DNM_SAMPLE_Y)
            shutter = self.main_obj.device(DNM_SHUTTER)

            yield from bps.stage(gate)
            shutter.open()

            for ev in self.ev_setpoints:
                yield from bps.mv(mtr_ev, ev)

                for sp_id, sp_db in self.sp_rois.items():
                    x_pos = dct_get(sp_db, SPDB_XSTART)
                    y_pos = dct_get(sp_db, SPDB_YSTART)
                    yield from bps.mv(mtr_x, x_pos, mtr_y, y_pos)
                    #yield from bps.mv(mtr_y, y_pos)

                    #yield from bps.create(name='primary')
                    #yield from bps.trigger(dets[0])
                    yield from bps.trigger_and_read(dets)
                    #yield from bps.read(dets[0])
                    #yield from bps.save()
                    #print('ev[%d] : done read for motor_x[%s] at %.2f' % (ev, mtr_x.get_name(), x_pos))
                    # yield from bps.sleep((1.0))

            shutter.close()

            yield from bps.unstage(gate)
            print('PositionerScanClass: make_scan_plan Leaving')

        return (yield from do_scan())

    def init_subscriptions(self, ew, func):
        '''
        Base init_subscriptions is used by most scans
        :param ew:
        :param func:
        :return:
        '''

        if (self.scan_type in spectra_type_scans):
            spid_seq_map = self.gen_spid_seq_map( self._master_sp_id_list, self.ev_setpoints)
            if(self.is_zp_scan):
                mtr_x = self.main_obj.device(DNM_ZONEPLATE_X)
            else:
                mtr_x = self.main_obj.device(self.x_roi[POSITIONER])
            # we also need to pass the sp_id because it needs to send it on to the plotter as data comes in
            self._emitter_cb = SpecDataEmitter('%s_single_value_rbv' % DNM_DEFAULT_COUNTER, x=mtr_x.get_name(), \
                                               scan_type=self.scan_type, spid_seq_map=spid_seq_map)
            self._emitter_sub = ew.subscribe_cb(self._emitter_cb)
            self._emitter_cb.new_plot_data.connect(func)
        else:
            _logger.error('Wrong scan type, needs to be a spectra scan type')

    def on_this_scan_done(self):
        #     """
        #     on_this_scan_done(): description
        #
        #     :returns: None
        #     """
        #     #stop gate and counter input tasks
        #     self.gate.stop()
        #     self.counter.stop()
        #     self.on_this_data_level_done()
        #     self.disconnect_signals()
        #     #self.save_master()
        pass

    def configure(self, wdg_com, sp_id=0, ev_idx=0, line=False, block_disconnect_emit=False):
        """
        configure(): description

        :param sp_db: sp_db description
        :type sp_db: sp_db type

        :param sp_id: sp_id description
        :type sp_id: sp_id type

        :param line=False: line=False description
        :type line=False: line=False type

        :returns: None
        """
        super(PointSpecScanClass, self).configure(wdg_com, sp_id=sp_id, line=line, z_enabled=False)
        # use base configure x y motor scan
        self.stack = False
        self.is_point_spec = True
        self.is_pxp = True
        self.is_lxl = False
        self.sp_id = sp_id

        if(USE_E712_HDW_ACCEL):
            self.main_obj.device('e712_current_sp_id').put(sp_id)

        # self.wdg_com = wdg_com
        # self.sp_rois = wdg_com[WDGCOM_SPATIAL_ROIS]
        # self.sp_db = self.sp_rois[sp_id]
        # self.set_spatial_id(sp_id)
        # self.scan_type = dct_get(self.sp_db, SPDB_SCAN_PLUGIN_TYPE)
        # self.scan_sub_type = dct_get(self.sp_db, SPDB_SCAN_PLUGIN_SUBTYPE)
        # self.numX = int(dct_get(self.sp_db, SPDB_XNPOINTS))
        # self.numY = int(dct_get(self.sp_db, SPDB_YNPOINTS))
        # self.numZ = int(dct_get(self.sp_db, SPDB_ZNPOINTS))
        # self.numE = int(dct_get(self.sp_db, SPDB_EV_NPOINTS))
        # self.numSPIDS = len(self.sp_rois)
        # self.e_rois = dct_get(self.sp_db, SPDB_EV_ROIS)
        # self.ev_setpoints = dct_get(wdg_com, SPDB_SINGLE_LST_EV_ROIS)
        # e_roi = self.e_rois[0]
        # self.numEPU = len(dct_get(e_roi, EPU_POL_PNTS))
        # if (self.numEPU < 1):
        #     self.numEPU = 1
        #
        # self.update_roi_member_vars(self.sp_db)

        dct_put(self.sp_db, SPDB_RECT, (self.x_roi[START], self.y_roi[START], self.x_roi[STOP], self.y_roi[STOP]))

        if (self.fine_sample_positioning_mode == sample_fine_positioning_modes.ZONEPLATE):
            self.is_zp_scan = True
        else:
            self.is_zp_scan = False

        self.dwell = self.e_rois[0][DWELL]

        self.reset_evidx()
        self.reset_imgidx()

        # self.stack_scan = False
        self.config_hdr_datarecorder(stack=self.stack)
        self.move_zpxy_to_its_center()

        self.seq_map_dct = self.generate_2d_seq_image_map(1, self.y_roi[NPOINTS], self.x_roi[NPOINTS], lxl=False)

        # THIS must be the last call
        self.finish_setup()



    def on_this_dev_cfg(self):
        """
        on_this_dev_cfg(): description

        :returns: None
        """
        """
        this  is an API method to configure the gate, shutter and counter devices for this scan
        """
        # add one so that the first one which will endup being 0 because of the ediff calc will be removed
        # set_devices_for_point_scan(self.sp_db, self.gate, self.counter, self.shutter)
        # set_devices_for_point_scan(self.scan_type, self.dwell, self.numE, self.numX, self.gate, self.counter, self.shutter)
        # self.gate.start()
        # self.counter.start()
        pass

        # def on_this_counter_changed(self, row, xxx_todo_changeme):
        #     """
        #     on_this_counter_changed(): description
        #
        #     :param row: row description
        #     :type row: row type
        #
        #     :param (point: (point description
        #     :type (point: (point type
        #
        #     :param val): val) description
        #     :type val): val) type
        #
        #     :returns: None
        #     """
        #     (point, val) = xxx_todo_changeme
        #     """
        #
        #     dct = self.init_counter_to_plotter_com_dct(make_counter_to_plotter_com_dct())
        #         dct[CNTR2PLOT_SP_ID] = self.sp_ids[sp_cntr]
        #         dct[CNTR2PLOT_ROW] = sp_cntr
        #         dct[CNTR2PLOT_COL] = ev
        #         dct[CNTR2PLOT_VAL] = point_val
        #     This is a slot that is connected to the counters changed signal
        #     """
        #     #counter = self.counter_dct.keys()[0]
        #     counter = DNM_DEFAULT_COUNTER
        #     _sp_id = list(self.spid_data[counter].keys())[0]
        #
        #     top_lvl_npts = self.top_level_scan.get('NPTS')
        #     #print 'on_generic_counter_changed: [%d] row=%d point=%d val=%d' % (top_lvl_npts, row, point, val)
        #     if(point >= self.numX):
        #         #this is the row switch extra point so drop it
        #         #print 'scan_counter_changed: SKIPPED [%d, %d] = %d' % (row, point, val)
        #         return
        #     if(point > -1):
        #         #print 'on_x_y_counter_changed: _evidx=%d' % _evidx
        #         if(row < top_lvl_npts):
        #             #self.data[int(point)] = val
        #             _polidx = 0
        #             _evidx = 0
        #
        #             self.spid_data[counter][_sp_id][_polidx][_evidx, row, point] = int(val)
        #             #print self.spid_data[counter][_sp_id][_polidx][_evidx]
        #
        #             dct = self.init_counter_to_plotter_com_dct(make_counter_to_plotter_com_dct())
        #             dct[CNTR2PLOT_SP_ID] = _sp_id
        #             dct[CNTR2PLOT_ROW] = row
        #             dct[CNTR2PLOT_COL] = self.x_roi[SETPOINTS][point]
        #             dct[CNTR2PLOT_VAL] = val
        #             self.sigs.changed.emit(dct)
        #
        #             prog = float(float(point + 0.75) / float(self.numX)) * 100.0
        #             prog_dct = make_progress_dict(sp_id=dct[CNTR2PLOT_SP_ID], percent=prog)
        #             self.low_level_progress.emit(prog_dct)
        pass

    def on_this_data_level_done(self):
        """
        on_this_data_level_done(): description

        :returns: None
        """
        """
        this is an API slot that gets fired when the data level scan_done signal

        The final data dict should have the main keys of:
            all_data['SSCANS']      - all fields of each sscan record, this will be a list of sscans
            all_data['SCAN_CFG']    - all params from the GUI for this scan, center, range etc, also any flags such as XMCD=True that relate to how to execute this scan
            all_data['DATA']        - counter data collected during scan, for images this will be a 2d array, for point scans this will be a 1d array

        The goal of all_data dict is to write the dict out to disk in <data dir>/master.json. Once it has been recorded to disk the data recorder
        module can open it as a json object and export it based on the scan type so that it can pick and choose what to pull out and write to the header file.   

        """
        # #_logger.debug('Generic: on_data_level_done:')
        # #AUG 30 self.save_hdr()
        # self.on_x_y_scan_data_level_done()
        # self.hdr.remove_tmp_file()
        pass

