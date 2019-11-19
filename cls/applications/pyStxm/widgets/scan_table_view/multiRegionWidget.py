
from PyQt5 import QtCore, QtGui, QtWidgets

from cls.applications.pyStxm.widgets.scan_table_view.baseScanTable import *
from cls.data_io.stxm_data_io import STXMDataIo
from cls.applications.pyStxm.widgets.scan_table_view.spatialSelWidget import SpatialSelWidget
from cls.applications.pyStxm.widgets.scan_table_view.evSelWidget import EnergySelWidget
from cls.applications.pyStxm.widgets.scan_table_view.polarizationSelWidget import PolarizationSelWidget
from cls.utils.roi_utils import make_spatial_db_dict, widget_com_cmnd_types
from cls.utils.fileUtils import get_file_path_as_parts
from cls.utils.log import get_module_logger, log_to_qt
from cls.utils.dict_utils import dct_get, dct_put
from cls.types.stxmTypes import energy_scan_order_types, scan_types, IMAGE_LXL, IMAGE_PXP, spatial_type_prefix
from cls.utils.roi_dict_defs import *
from cls.app_data.defaults import get_style

_logger = get_module_logger(__name__)

class MultiRegionWidget(BaseSelectionWidget):
    """
    A QWidget that contains Spatial, EV, and polarity selection table views
    
    Each of the 3 widgets need to support the adding and deleting of regions both
    from teh GUI (right click and select add/delete from teh menu) as well as 
    programattically because we need to be able to add/delete based on what a plotter widget
    may have done.
    
    
    """
    spatial_row_added = QtCore.pyqtSignal(object)
    spatial_row_selected = QtCore.pyqtSignal(object)
    spatial_row_changed = QtCore.pyqtSignal(object)
    spatial_row_deleted = QtCore.pyqtSignal(object)

    def __init__(self,use_center=True, is_point=False, is_arb_line=False, enable_multi_spatial=False, single_ev_model=True, max_range=100, use_hdw_accel=True,
                 min_sp_rois=0, x_cntr=None, y_cntr=None, main_obj=None, *args):
        """
        __init__(): description

        :param *args: *args description
        :type *args: *args type

        :returns: None
        """
        BaseSelectionWidget.__init__(self, *args)
        self.setGeometry(300, 200, 870, 850)
        
        self.use_center = use_center
        self.enable_multi_spatial = enable_multi_spatial
        self.min_sp_rois = min_sp_rois
        self.main_obj = main_obj
        self.ev_polarity_scan_order = energy_scan_order_types.EV_THEN_POL
        
        self.loadScanBtn = QtWidgets.QPushButton('Load Scan')
        self.getDataBtn = QtWidgets.QPushButton('Get Data')
        self.compareDataBtn = QtWidgets.QPushButton('Compare Data')
        #self.multiSpatialCheckBox = QtWidgets.QCheckBox('Multi Spatials')
        self.getAllSpBtn = QtWidgets.QPushButton('Get all SP regions')
        self.getAllEvBtn = QtWidgets.QPushButton('Get all EV regions')
        self.getAllPolBtn = QtWidgets.QPushButton('Get all POL regions')
          
                
        self.getDataBtn.clicked.connect(self.on_get_data_btn)
        self.loadScanBtn.clicked.connect(self.on_load_scan)
        self.compareDataBtn.clicked.connect(self.on_compare_data)
        #self.multiSpatialCheckBox.clicked.connect(self.on_multi_spatial_chk)
        self.getAllSpBtn.clicked.connect(self.get_just_sp_regions)
        self.getAllEvBtn.clicked.connect(self.get_just_ev_regions)
        self.getAllPolBtn.clicked.connect(self.get_just_pol_regions)
        
        self.pol_widg = PolarizationSelWidget()
        self.ev_widg = EnergySelWidget(self.pol_widg, main_obj=self.main_obj)

        if(self.enable_multi_spatial):
            single_sp = False
        else:
            single_sp = True

        # self.sp_widg = SpatialSelWidget(self.ev_widg, use_center=use_center, is_point=is_point, is_arb_line=is_arb_line, \
        #                                 single_ev_model=single_ev_model, max_range=max_range, use_hdw_accel=use_hdw_accel, \
        #                                 single_sp_region=single_sp)
        self.sp_widg = SpatialSelWidget(self.ev_widg, use_center=use_center, is_point=is_point, is_arb_line=is_arb_line,
                                        single_ev_model=single_ev_model, max_range=max_range,
                                        use_hdw_accel=use_hdw_accel, single_sp_region=single_sp,
                                        min_sp_rois=min_sp_rois, x_cntr=x_cntr, y_cntr=y_cntr)

        #self.dark_ss = get_style('dark')
        #self.sp_widg.setStyleSheet(self.dark_ss)
        #self.ev_widg.setStyleSheet(self.dark_ss)
        #self.pol_widg.setStyleSheet(self.dark_ss)
        
        self.sp_widg.table_view.row_selected.connect(self.row_was_selected)
        self.sp_widg.model_change.connect(self.on_spatial_model_changed)
        self.sp_widg.roi_added.connect(self._on_new_spatial_region)
        self.sp_widg.spatial_row_changed.connect(self.on_spatial_row_changed)
        if(self.enable_multi_spatial):
            #only allow a deletion of the spatial row if multi spatial is enabled
            self.sp_widg.roi_deleted.connect(self.on_spatial_roi_deleted)
                
        v_layout = QtWidgets.QVBoxLayout()
        v_layout.setContentsMargins(2,2,2,2)
        
        #if(enable_multi_spatial):
        #    v_layout.addWidget(self.multiSpatialCheckBox)

        v_layout.addWidget(self.sp_widg)
        v_layout.addWidget(self.ev_widg)
        v_layout.addWidget(self.pol_widg)
        #v_layout.addWidget(self.getAllSpBtn)
        #v_layout.addWidget(self.getAllEvBtn)
        #v_layout.addWidget(self.getAllPolBtn)
        #v_layout.addWidget(self.getDataBtn)
        #v_layout.addWidget(self.loadScanBtn)

        #self.multiSpatialCheckBox.setChecked(False)
        #self.on_multi_spatial_chk(False)
        if(enable_multi_spatial):
            #self.multiSpatialCheckBox.setEnabled(True)
            #self.multiSpatialCheckBox.setChecked(True)
            self.on_multi_spatial_chk(True)
        else:
            self.on_multi_spatial_chk(False)
            # trim size of spatial region widget and give proper space to the other widgets
            self.sp_widg.setMaximumHeight(45)
            self.ev_widg.setMinimumHeight(100)
            self.pol_widg.setMinimumHeight(60)

        #default is enabled
        self.disable_polarization_table(False)
        self.setLayout(v_layout)

    def disable_polarization_table(self, val):
        if(val):
            self.pol_widg.setEnabled(False)
            #shrink how much vertial space it occupies
            self.pol_widg.setMaximumHeight(50)
        else:
            self.pol_widg.setEnabled(True)
            self.pol_widg.setMaximumHeight(16777215)

    def init_polarization_values(self, polarization, offset, angle):
        '''
        set the default values for polarization widget, these are usually assigned the current feedback values
        of the EPU by the parent widget
        :param polarization:
        :param offset:
        :param angle:
        :return:
        '''
        self.pol_widg.set_default_values(polarization, offset, angle)

    def is_spatial_list_empty(self):
        return(self.sp_widg.is_empty())


    def show_load_btn(self):
        self.layout().addWidget(self.loadScanBtn)
    
    def show_getdata_btn(self):
        self.layout().addWidget(self.getDataBtn)
    
    def on_get_data_btn(self):
        #sp_regions = self.get_sp_regions()
        #print sp_regions
        self.get_sp_regions(do_print=True)
    
    def get_spatial_model(self):
        return(self.sp_widg.table_view.model())
    
    def get_energy_model(self):
        return(self.ev_widg.table_view.model())
    
    
    def delete_spatial_row(self, sp_model_id=None):
        if(self.enable_multi_spatial):
            self.sp_widg.delete_row(sp_model_id)
    
    def modify_spatial_row_data(self, item_id, scan):
        self.sp_widg.modify_row_data(item_id, scan)
    
    def get_spatial_row_data(self, scan_id):
        return(self.sp_widg.get_row_data_by_item_id(scan_id))
    
    def creat_new_spatial_region(self, scan=None, add_energy_roi=True):
        if(self.enable_multi_spatial or (self.sp_widg.table_view.get_num_scans() == 0)):
            self.sp_widg.on_new_region(scan=scan, add_energy_roi=add_energy_roi)
    
    def set_spatial_positioners(self, xpos_name, ypos_name):
        self.sp_widg.set_positioners(xpos_name, ypos_name)
    
    def clear_spatial_table(self):
        self.sp_widg.clear_table()
    
    def set_roi_limits(self, limit_def):
        qrect = limit_def.get_alarm_def(as_qrect=True)
        self._set_spatial_range(qrect)
    
    def _set_spatial_range(self, qrect):
        ''' limit the size of a possible scan to be within the specified rect'''
        self.sp_widg.set_spatial_range(qrect)
        
        if(not self.use_center):
            self.sp_widg.set_spatial_startstop(qrect)
        
    def on_compare_data(self):
        self.compare_roi(roi_def, axis=SPDB_X)
    
    def on_load_scan(self ):
        from cls.applications.pyStxm.bl10ID01 import MAIN_OBJ
        from cls.data_io.stxm_data_io import STXMDataIo
        from cls.utils.fileUtils import get_file_path_as_parts
        from cls.appWidgets.dialogs import getOpenFileName
        
        datadir=r'S:\STXM-data\Cryo-STXM\2019\guest\0207'
        data_file_pfx = 'C'
        fname = getOpenFileName("Load Scan", filter_str="Scan Files (%s*.hdf5)" % data_file_pfx, search_path=datadir)
        self.openfile(fname)
#         data_dir, fprefix, fsuffix = get_file_path_as_parts(fname)
#         if(fname is None):
#             return
#         data_io = STXMDataIo(data_dir, fprefix, fsuffix)
#         data_dct = data_io.load()
#         if(data_dct is not None):
#             dct_put(data_dct,ADO_CFG_WDG_COM_CMND, widget_com_cmnd_types.LOAD_SCAN)
#             self.load_scan(dct_get(data_dct, ADO_CFG_WDG_COM))
        
    def openfile(self, fname):    
        """
        check_for_cur_scan_tab: this call was originally used by the load_scan buttons on each scan pluggin
        tab which would only load a scan that matched the scan pluggin you were loading from, but to 
        support drag and drop operations we will allow the skipping of this check so that the main app
        can automatically make the dropped scan the curent scan pluggin tab
        """
        if(fname is None):
            return
        data_dir, fprefix, fsuffix = get_file_path_as_parts(fname)
        data_io = STXMDataIo(data_dir, fprefix)
        entry_dct = data_io.load()
        if(entry_dct is None):
            return
        append = False
        for ekey in list(entry_dct.keys()):
            #ekey = entry_dct.keys()[0]
            nx_datas = data_io.get_NXdatas_from_entry(entry_dct, ekey)
            #currently only support 1 counter
            counter_name = list(nx_datas.keys())[0]
            data = data_io.get_signal_data_from_NXdata(nx_datas, counter_name)
            wdg_com = data_io.get_wdg_com_from_entry(entry_dct, ekey)
            
            if(not append):
                self.load_scan(wdg_com, append=append)
                append = True
            else:
                self.load_scan(wdg_com, append=append)
            
                
            ##else:
            #    _logger.error('unable to load scan, wrong scan type')
    
        
    def load_scan(self, wdg_com, append=False, ev_only=False, sp_only=False):
        """
        given the scan type supports multi spatial, read in and load the respective 
        tables
        scan_types = Enum('Detector_Image','OSA_Image','OSA_Focus','Sample_Focus','Sample_Point_Spectrum', 'Sample_Line_Spectrum', 'Sample_Image', 'Sample_Image_Stack', 'Generic_Scan')
        """
        multi_scan_types = [scan_types.SAMPLE_POINT_SPECTRA, scan_types.SAMPLE_LINE_SPECTRA, scan_types.SAMPLE_IMAGE, \
                            scan_types.SAMPLE_IMAGE_STACK, scan_types.SAMPLE_IMAGE + IMAGE_LXL, \
                            scan_types.SAMPLE_IMAGE + IMAGE_PXP, scan_types.TOMOGRAPHY_SCAN]
        
        sp_roi_dct = dct_get(wdg_com, WDGCOM_SPATIAL_ROIS)
        sp_ids = list(sp_roi_dct.keys())
        sp_id = sp_ids[0]
        sp_db = sp_roi_dct[sp_id]
        scan_type = dct_get(sp_db, SPDB_SCAN_PLUGIN_TYPE)

        if(scan_type not in multi_scan_types):
            _logger.error('Incorrect scan type [%d], not a multi spatial region scan' % scan_type)
            return
            
        _logger.info('[%d] scan loaded' % scan_type)
        
        #if(len(sp_ids) > 1):
        #    self.multiSpatialCheckBox.setChecked(True)
        #    self.on_multi_spatial_chk(True)
        #else:
        #    self.multiSpatialCheckBox.setChecked(False)
        #    self.on_multi_spatial_chk(False)
        if(not sp_only):
            if(not append):
                self.sp_widg.load_scan(sp_db, ev_only=ev_only)
            else:
                self.sp_widg.add_scan(sp_db, ev_only=ev_only)

        if(not ev_only):
            if(len(sp_ids) > 1):
                for sp_id in sp_ids[1:]:
                    sp_roi = sp_roi_dct[sp_id]
                    #self.sp_widg.load_scan(sp_roi)
                    #self.sp_widg.table_view.add_scan(sp_roi, sp_id)
                    self.sp_widg.add_scan(sp_roi, ev_only=ev_only, sp_only=sp_only)
                    #self.print_sp_roi(sp_roi)
            else:
                sp_roi = sp_roi_dct[sp_id]
                self.sp_widg.add_scan(sp_roi, ev_only=ev_only, sp_only=sp_only)
        
        
        
    def row_was_selected(self, scan):

        #sp_db = make_spatial_db_dict()
        # make_spatial_db_dict(x_roi=None, y_roi=None, z_roi=None, e_roi=None, goni_rois={}, osa_rois={}, zp_rois={},sp_id=None):
        sp_db = make_spatial_db_dict(x_roi=scan[SPDB_X], y_roi=scan[SPDB_Y], z_roi=scan[SPDB_Z], sp_id=scan[SPDB_ID_VAL])
        sp_db[WDGCOM_CMND] = widget_com_cmnd_types.SELECT_ROI
        #dct_put(sp_db, SPDB_SCAN_PLUGIN_ITEM_ID, scan[SPDB_ID_VAL])
        #sp_db[SPDB_ID_VAL] =  scan[SPDB_ID_VAL]
        
        self.spatial_row_selected.emit(sp_db)
    
    def enable_add_spatial_region_menu(self, do=True):
        self.sp_widg.enable_add_region_menu(do)
    
    def deselect_all(self):
        #_logger.debug('deselect_all: called')
        self.sp_widg.table_view.clearSelection()

    def deslect_all_energies(self):
        # _logger.debug('deselect_all: called')
        self.ev_widg.table_view.clearSelection()

    def deslect_all_polarizations(self):
        # _logger.debug('deselect_all: called')
        self.pol_widg.table_view.clearSelection()

    def set_polarization_table_visible(self, val):
        self.pol_widg.setVisible(val)
        
    def select_spatial_row(self, scan_id):
        self.sp_widg.blockSignals(True)
        self.sp_widg.select_row(item_id=scan_id)
        self.sp_widg.blockSignals(False)
    
    def on_multi_spatial_chk(self, checked):
        if(checked):
            self.enable_multi_spatial = True
        else:
            self.enable_multi_spatial = False    
        
        self.sp_widg.enable_multi_spatial(self.enable_multi_spatial)    
    
    def is_multi_region_enabled(self):
        return(self.enable_multi_spatial)

    def _on_new_spatial_region(self, scan):
        # dct = make_spatial_db_dict()
        # dct_put(dct, WDGCOM_CMND, cmnd=widget_com_cmnd_types.ROI_CHANGED)
        # # dct_put(dct, SPDB_SCAN_PLUGIN_ITEM_ID, self.inputState.plotitem_id)
        # dct_put(dct, SPDB_PLOT_ITEM_ID, self.inputState.plotitem_id)
        # dct_put(dct, SPDB_PLOT_ITEM_TITLE, self.inputState.plotitem_title)
        # dct_put(dct, SPDB_PLOT_SHAPE_TYPE, self.inputState.plotitem_type)
        # #dct_put(dct, SPDB_PLOT_KEY_PRESSED, self.inputState.keyisPressed)
        # dct_put(dct, SPDB_ID_VAL, scan[SPDB_ID_VAL])
        # dct_put(dct, SPDB_X, scan[SPDB_X])
        # dct_put(dct, SPDB_Y, scan[SPDB_Y])
        # dct_put(dct, SPDB_Z, scan[SPDB_Z])
        # _logger.debug('on_spatial_row_changed:')
        sp_rois_dct = self.get_sp_regions()
        self.spatial_row_changed.emit(sp_rois_dct)



    def on_spatial_model_changed(self, scan_id):
        cur_row_list = self.sp_widg.table_view.selectionModel().selectedRows()
        if(len(cur_row_list) is 0):
            return
        cur_row = cur_row_list[0].row()
        #get row ID of this scan
        new_row = self.sp_widg.get_row_idx(scan_id)
        if(cur_row == new_row):
            #we have been called programatically so break signal cycle
            return
        
        scan = self.sp_widg.get_row_data(scan_id)
        if(scan is not None):
            x_roi = scan[SPDB_X]
            y_roi = scan[SPDB_Y]
            
            sp_db = make_spatial_db_dict(x_roi=x_roi, y_roi=y_roi)
            sp_db[WDGCOM_CMND] = widget_com_cmnd_types.ROI_CHANGED
            #dct_put(sp_db, SPDB_SCAN_PLUGIN_ITEM_ID, scan[SPDB_ID_VAL])
            
            if(x_roi[NPOINTS] == 1):
                dct_put(sp_db, SPDB_PLOT_SHAPE_TYPE, spatial_type_prefix.PNT)
            else:
                dct_put(sp_db, SPDB_PLOT_SHAPE_TYPE, spatial_type_prefix.ROI)
            
            self.spatial_row_selected.emit(sp_db)
        
        
#     def on_spatial_row_changed(self, scan):
#         if(scan is not None):
#             #print 'on_spatial_row_changed: scan_id(%d)' % scan[SPDB_ID_VAL]
#             sp_db = make_spatial_db_dict()
#             sp_db[WDGCOM_CMND] = widget_com_cmnd_types.ROI_CHANGED
#             
#             #set the SINGLE_SPATIAL fields so that the plotter can update
#             sp_db[SPDB_X][START] = scan[SPDB_X][START]
#             sp_db[SPDB_X][STOP] = scan[SPDB_X][STOP]
#             sp_db[SPDB_Y][START] = scan[SPDB_Y][START]
#             sp_db[SPDB_Y][STOP] = scan[SPDB_Y][STOP]
#             sp_db[SPDB_X][CENTER] = scan[SPDB_X][CENTER]
#             sp_db[SPDB_Y][CENTER] = scan[SPDB_Y][CENTER]
#             sp_db[SPDB_X][RANGE] = scan[SPDB_X][RANGE]
#             sp_db[SPDB_Y][RANGE] = scan[SPDB_Y][RANGE]
#             sp_db[SPDB_X][NPOINTS] = scan[SPDB_X][NPOINTS]
#             sp_db[SPDB_Y][NPOINTS] = scan[SPDB_Y][NPOINTS]
#             
#             sp_db[SPDB_EV_ROIS] = scan[SPDB_EV_ROIS]
#             
#             #rect = (scan['STARTX'], scan['STARTY'], scan['STOPX'], scan['STOPY'])
#             rect = scan[SPDB_RECT]
#             #print 'on_spatial_row_changed: rect =' , rect
#             #dct_put(sp_db, SPDB_SCAN_PLUGIN_ITEM_ID, scan[SPDB_ID_VAL])
#             if(scan[SPDB_X][NPOINTS] == 1):
#                 #sp_db['SCAN_PLUGGIN']['ITEM']['TYPE'] = spatial_type_prefix.PNT
#                 dct_put(sp_db, SPDB_PLOT_SHAPE_TYPE, spatial_type_prefix.PNT)
#             else:
#                 #sp_db['SCAN_PLUGGIN']['ITEM']['TYPE'] = spatial_type_prefix.ROI    
#                 dct_put(sp_db, SPDB_PLOT_SHAPE_TYPE, spatial_type_prefix.ROI)
#             
#             sp_db[SPDB_ID_VAL] = scan[SPDB_ID_VAL] 
#             self.spatial_row_changed.emit(sp_db)
#             
#             #sp_roi = self.get_sp_regions()
#             #self.tables_changed.emit()
    
    
    #def update_multi_spatial_wdg_com(self):
    def on_spatial_row_changed(self, scan):
        """
        This is a standard function that all scan pluggins have that is called to 
        get the data from the pluggins UI widgets and write them into a dict returned by 
        get_base_scanparam_roi(), this dict is emitted by all scan pluggins to be used by 
        the scan classes configure() functions
    
        :returns: None
     
        """
        #_logger.debug('on_spatial_row_changed:')
        sp_rois_dct = self.get_sp_regions()
        self.spatial_row_changed.emit(sp_rois_dct)
        
    
    def on_spatial_roi_deleted(self, scan):
        self.spatial_row_deleted.emit(scan)
        
    
    def get_sp_regions(self, do_print=False):
        """
        get_sp_regions(): description

        :returns: None
        """
        '''
                                                    
        '''
        
        sp_regions = {}
        for sp_roi in self.sp_widg.get_data():
            if(do_print):
                self.print_sp_roi(sp_roi)
                #self.compare_roi(sp_roi, axis=SPDB_X)
                #self.compare_roi(sp_roi, axis=SPDB_Y)
                
            xstart = dct_get(sp_roi, SPDB_XSTART)
            xstop = dct_get(sp_roi, SPDB_XSTOP)
            ystart = dct_get(sp_roi, SPDB_YSTART)
            ystop = dct_get(sp_roi, SPDB_YSTOP)
            sp_roi[SPDB_RECT] = (xstart, ystart, xstop, ystop)

            _evs = []
            e_npts = 0
            pol_npts = 0
            ev_setpoints = []
            dwell_setpoints = []
            
            #print 'sp_id=%d EV_ID=%d' % (sp_roi[SPDB_ID_VAL], sp_roi[SPDB_EV_ID])
            for ev_roi in self.ev_widg.get_data(sp_roi[SPDB_EV_ID]):
                if(do_print):
                    self.print_ev_roi(ev_roi)
                    
                dwell = ev_roi[DWELL]
                e_npts += ev_roi[NPOINTS]
                dwell_setpoints.append(dwell)
                _pols = []
                pol_setpoints = []
                off_setpoints = []
                angle_setpoints = []
                #for ev_sp in ev_roi[SETPOINTS]:
                for pol_roi in self.pol_widg.get_data(ev_roi[POL_ID]):
                    if(do_print):
                        self.print_pol_roi(ev_roi[START], pol_roi)
                    #ev_setpoints.append(ev_sp)
                    #dwell_setpoints.append(dwell)
                    pol_setpoints.append(pol_roi[POL])
                    off_setpoints.append(pol_roi[OFF])
                    angle_setpoints.append(pol_roi[ANGLE])
                    _pols.append(pol_roi)
                    pol_npts += 1
                ev_roi[POL_ROIS] = _pols
                
                ev_roi[EPU_POL_PNTS] = pol_setpoints
                ev_roi[EPU_OFF_PNTS] = off_setpoints
                ev_roi[EPU_ANG_PNTS] = angle_setpoints
                
                _evs.append(ev_roi)
                
            sp_roi[SPDB_EV_ROIS] = _evs
            sp_roi[SPDB_EV_NPOINTS] = e_npts
            sp_roi[SPDB_POL_NPOINTS] = pol_npts
            
            sp_regions[sp_roi[SPDB_ID_VAL]] = sp_roi     

        return(sp_regions)

    def get_just_sp_regions(self, do_print=False):
        """
        get_ev_regions(): description

        :returns: a list of all of the ev data
        """
        '''

        '''
        data = self.sp_widg.get_all_data()
        if(do_print):
            for d in data:
                print(d)
        return (data)

    def get_just_ev_setpoints(self, do_print=False):
        """
        get_ev_regions(): description

        :returns: a list of all of the ev data
        """
        '''

        '''
        data = self.ev_widg.get_all_data()
        evs = []
        for d in data:
            if(type(d[SETPOINTS]) is tuple):
                ev_pnts = d[SETPOINTS][0]
            else:
                ev_pnts = d[SETPOINTS]

            #evs.extend(d[SETPOINTS])
            evs.extend(ev_pnts)
        if (do_print):
            for d in data:
                print(d)
        return(evs)

    def get_just_ev_regions(self, do_print=False):
        """
        get_ev_regions(): description

        :returns: a list of all of the ev data
        """
        '''

        '''
        data = self.ev_widg.get_all_data()
        evs = []
        for d in data:
            evs.append(d)
        if (do_print):
            for d in data:
                print(d)
        return(evs)

    def get_just_dwells(self, do_print=False):
        """
        get_ev_regions(): description

        :returns: a list of all of the ev data
        """
        '''

        '''
        dwells = []
        ev_rois = self.ev_widg.get_all_data()
        for ev_roi in ev_rois:
            for i in range(int(ev_roi[NPOINTS])):
                dwells.append(ev_roi[DWELL])
            if (do_print):
                print(dwells)
        return(dwells)

    def get_just_pol_regions(self, do_print=False):
        """
        get_ev_regions(): description
        :returns: a list of all of the polarity data
        """
        '''
        '''
        data = self.pol_widg.get_all_data()
        if (do_print):
            for d in data:
                print(d)
        return (data)


    def compare_roi(self, roi_def, axis=SPDB_X):
        """
        compare_roi(): description

        :param roi: roi description
        :type roi: roi type

        :returns: None
        """
        print()
        fields = [CENTER, RANGE, NPOINTS, STEP, START, STOP]
        if(axis == SPDB_X):
            ax = roi_def[SPDB_SPATIAL_ROIS][0]
        else:
            ax = roi_def[SPDB_SPATIAL_ROIS][1]    

        for k in fields:
            print('[%s] = %.2f [%s] = %.2f' % (k+axis, roi_def[k+axis], k, ax[k]))
        k = SETPOINTS
        print('[%s%s' % (k, axis) + '] =', roi_def[k+axis]) 
        print('[%s'% (k) + ']=', ax[k]) 
    
    def get_sp_regions_orig(self):
        """
        get_sp_regions(): description

        :returns: None
        """
        '''
        This function grabs all the regions group like this:
        sp_regions = []
            sp_regions[0] = ['SPATIAL_REGION',.....[SPDB_EV_ROIS]]
                EV_ROIS = ['EV_ROI', ........[POL_ROIS]]
                    POL_ROIS = [{'POL_ROI', ....}]
            sp_regions[1] = ['SPATIAL_REGION',.....[SPDB_EV_ROIS]]
                EV_ROIS = ['EV_ROI', ........[POL_ROIS]]
                    POL_ROIS = [{'POL_ROI', ....}]
            ...        
        
        I also want to return all of the EV regions for a particular spatial ROI such that
        the resulting arrays are already to be sent to the sscan record in TABLE mode, meaning
        I want an array that contains all of the EV setpoints such that it is correct for the
        number of polarity settings for each energy point.
        if fore SPATIAL_ROI 1:
            EV_ROI 1 = 395ev to 405ev for 2 pts, POL_ROI's = [{pol1e1}, {pol2e1}, {pol3e1}]
            EV_ROI 2 = 395ev to 405ev for 3 pts, POL_ROI's = [{pol1e2}, {pol2e2}]
        I want to generate the following 2 arrays    
        
        EV array sent to energy sscan                POL array sent to polarity sscan
            [     e1.1,                                    [    pol1e1,
                e1.1,                                        pol2e1,
                e1.1,                                        pol3e1,
                e1.2,                                        pol1e1,
                e1.2,                                        pol2e1,
                e1.2,                                        pol3e1,
                e2.1,                                        pol2e1,
                e2.1,                                        pol2e2,
                e2.2,                                        pol2e1,
                e2.2,                                        pol2e2,
                e2.3,                                        pol2e1,
                e2.3                                        pol2e2
            ]                                            ]
        Both sscan NPTS will be 12
            NPTS EV_ROI 1 = 2 ev pts x 3 pol points = 6
            NPTS EV_ROI 2 = 3 ev pts x 2 pol points = 6
                                                    = 12
        '''
        sp_db = make_spatial_db_dict()
        
        sp_regions = {}
        for sp_roi in self.sp_widg.get_data():
            #self.print_sp_roi(sp_roi)
            #self.compare_roi(sp_roi, axis=SPDB_X)
            #self.compare_roi(sp_roi, axis=SPDB_Y)
            _evs = []
            e_npts = 0
            ev_setpoints = []
            dwell_setpoints = []
            
            for ev_roi in self.ev_widg.get_data(sp_roi['EV_ID']):
                #self.print_ev_roi(ev_roi)
                dwell = ev_roi[DWELL]
                e_npts += ev_roi[NPOINTS]
                dwell_setpoints.append(dwell)
                _pols = []
                pol_setpoints = []
                off_setpoints = []
                angle_setpoints = []
                #for ev_sp in ev_roi[SETPOINTS]:
                for pol_roi in self.pol_widg.get_data(ev_roi[POL_ID]):
                    #self.print_pol_roi(ev_roi[START], pol_roi)
                    #ev_setpoints.append(ev_sp)
                    #dwell_setpoints.append(dwell)
                    pol_setpoints.append(pol_roi[POL])
                    off_setpoints.append(pol_roi[OFF])
                    angle_setpoints.append(pol_roi[ANGLE])
                    _pols.append(pol_roi)
                ev_roi[POL_ROIS] = _pols
                
                ev_roi[EPU_POL_PNTS] = pol_setpoints
                ev_roi[EPU_OFF_PNTS] = off_setpoints
                ev_roi[EPU_ANG_PNTS] = angle_setpoints
                
                _evs.append(ev_roi)
                
            sp_roi[SPDB_EV_ROIS] = _evs
            sp_roi[SPDB_EV_NPOINTS] = e_npts
            
            x_setpoints = sp_roi[SPDB_X][SETPOINTS]
            y_setpoints = sp_roi[SPDB_Y][SETPOINTS]
            
            numE = len(ev_roi[SETPOINTS])
            numX = len(x_setpoints)
            numY = len(y_setpoints)
            numP = numE * numY * numX
            
            x_setpoints2 =  np.tile(x_setpoints, numY)
            xpnts =  np.tile(x_setpoints2, numE)
            y_setpoints2 = np.repeat(y_setpoints, numX)
            ypnts = np.tile(y_setpoints2, numE)
            
            epnts = np.repeat(ev_setpoints, (numY * numX))
            dwell_pnts = np.repeat(dwell_setpoints, (numY * numX))
            pol_pnts = np.repeat(pol_setpoints, (numY * numX))
            off_pnts = np.repeat(off_setpoints, (numY * numX))
            angle_pnts = np.repeat(angle_setpoints, (numY * numX))
            
            sp_roi['1D_SETPOINTS'][SPDB_X] = xpnts
            sp_roi['1D_SETPOINTS'][SPDB_Y] = ypnts
            sp_roi['1D_SETPOINTS']['EV'] = ev_roi[SETPOINTS]
            sp_roi['1D_SETPOINTS'][DWELL] = dwell_setpoints
            sp_roi['1D_SETPOINTS']['EPU_POL'] = pol_setpoints
            sp_roi['1D_SETPOINTS']['EPU_OFF'] = off_setpoints
            sp_roi['1D_SETPOINTS']['EPU_ANGLE'] = angle_setpoints
            #sp_regions.append(sp_roi)
            sp_regions[sp_roi[SPDB_ID_VAL]] = sp_roi     
            
        sp_db['SPATIAL_IDS'] = list(sp_regions.keys())
        sp_db['MULTI_SPATIAL'] = sp_regions
        return(sp_db)     
                    
#     def compare_roi(self, roi_def, axis=SPDB_X):
#         """
#         compare_roi(): description
# 
#         :param roi: roi description
#         :type roi: roi type
# 
#         :returns: None
#         """
#         print
#         fields = ['CENTER', 'RANGE', 'NPOINTS', 'STEP', 'START', 'STOP']
#         if(axis == SPDB_X):
#             ax = roi_def[SPATIAL_ROIS][0]
#         else:
#             ax = roi_def[SPATIAL_ROIS][1]    
# 
#         for k in fields:
#             print '[%s] = %.2f [%s] = %.2f' % (k+axis, roi_def[k+axis], k, ax[k])
#         k = SETPOINTS    
#         print '[%s%s' % (k, axis) + '] =', roi_def[k+axis] 
#         print '[%s'% (k) + ']=', ax[k] 
                    
    def print_sp_roi(self, roi):
        """
        print_sp_roi(): description

        :param roi: roi description
        :type roi: roi type

        :returns: None
        """
        print('Spatial ROI [%d] CenterX[%.2f] RangeX[%.2f] CenterY[%.2f] RangeY[%.2f] EV_MODEL=%d' % (roi[SPDB_ID_VAL], roi['X'][CENTER],roi['X'][RANGE],roi['Y'][CENTER], roi['Y'][RANGE], roi['EV_ID']))
        print('Spatial ROI [%d] StartX[%.2f] StopX[%.2f] StartY[%.2f] StopY[%.2f]' % (roi[SPDB_ID_VAL], roi['X'][START],roi['X'][STOP],roi['Y'][START], roi['Y'][STOP]))
        
    def print_ev_roi(self, roi):
        """
        print_ev_roi(): description

        :param roi: roi description
        :type roi: roi type

        :returns: None
        """
        print('\tEV ROI [%d] Start[%.2f] End[%.2f] Range[%.2f] Points[%.2f] Dwell[%.2f] POL_MODEL=%d' % (roi[SPDB_ID_VAL],roi[START],roi[STOP],roi[RANGE], roi[NPOINTS], roi[DWELL], roi[POL_ID]))
        
    def print_pol_roi(self, ev_setpoint, roi):
        """
        print_pol_roi(): description

        :param ev_setpoint: ev_setpoint description
        :type ev_setpoint: ev_setpoint type

        :param roi: roi description
        :type roi: roi type

        :returns: None
        """
        print('\t\tPOL ROI [%d] [%.3f ev]  POL[%d] Offset[%.2f] Angle[%.2f]' % (roi[SPDB_ID_VAL], ev_setpoint, roi[POL],roi[OFF],roi[ANGLE]))
                
        
if __name__ == '__main__':
    import sys
    from cls.appWidgets.splashScreen import get_splash, del_splash
    from cls.appWidgets.spyder_console import ShellWidget#, ShellDock
    
    log_to_qt()
    app = QtWidgets.QApplication(sys.argv)
    #win = EnergySelWidget()
    #win.show()
    #spatial = SpatialSelWidget()
    #spatial.show()
    
    #multi = MultiRegionWidget(use_center=True, enable_multi_spatial=True)
    # multi = MultiRegionWidget(use_center=True, enable_multi_spatial=True, is_point=False, single_ev_model=False)
    multi = MultiRegionWidget(use_center=True, enable_multi_spatial=True, is_point=False, single_ev_model=False,
                              min_sp_rois=1)
    multi.disable_polarization_table(True)
    #multi.enable_add_spatial_region_menu(True)
    multi.show_load_btn()
    multi.show_getdata_btn()
    
    #ns = {'main': multi, 'g':globals() }
    #    #msg = "Try for example: widget.set_text('foobar') or win.close()"
    #pythonshell = ShellWidget(parent=None, namespace=ns,commands=[], multithreaded=True)
    #multi.layout().addWidget(pythonshell)

    #splash = get_splash()
    #didit = splash.close()
    #del_splash()

    multi.show()
    
    sys.exit(app.exec_())    
    
    
    
