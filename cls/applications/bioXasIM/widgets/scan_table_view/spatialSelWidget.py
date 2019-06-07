from PyQt5 import uic

from cls.applications.pyStxm.widgets.scan_table_view.baseScanTable import *
from cls.applications.pyStxm.widgets.scan_table_view.spatialTableView import SpatialScanTableView
from cls.utils.log import get_module_logger, log_to_qt

_logger = get_module_logger(__name__)

class SpatialSelWidget(BaseSelectionWidget):
    """
    A QWidget that contains an SpatialScanTableView, can be configured to connect to ev_sel_widget
    """
    roi_deleted = QtCore.pyqtSignal(object)
    spatial_row_changed = QtCore.pyqtSignal(object)
    
    def __init__(self, ev_sel_widget=None, use_center=True, is_point=False, is_arb_line=False, single_ev_model=False):
        """
        __init__(): description

        :param ev_sel_widget=None: ev_sel_widget=None description
        :type ev_sel_widget=None: ev_sel_widget=None type
        
        :param use_center: if True the header that is used will use CenterX CenterY, otherwise it will use StartX, StartY
        :type use_center: bool
        
        :param is_point: does the spatial roi represent a point scan?
        :type is_point: bool
        
        :param is_arb_line: does the spatial roi represent a arbitrary line scan?
        :type is_arb_line: bool
        
        
        :param single_model: this flag decides if mutiple ev_roi models are allowed, this is useful to set it to True
            in the case where I want to reuse a single ev_roi for mutiple spatial roi's
        :type single_model: boolean



        :returns: None
        """
        BaseSelectionWidget.__init__(self)
        # setGeometry(x_pos, y_pos, width, height)
        self.setGeometry(300, 200, 870, 450)
        self.setWindowTitle("Click on column title to sort")
        self.editable = False
        self.add_region_enabled = True
        self.ev_sel_widget = ev_sel_widget
        
        self.use_center = use_center
        self.single_ev_model = single_ev_model
        self.single_ev_model_id = None
        if(single_ev_model):
            self.ev_sel_widget.set_single_ev_model(True)
        else:
            self.ev_sel_widget.set_single_ev_model(False)
            
        self.table_view = SpatialScanTableView(use_center=use_center, is_point=is_point, is_arb_line=is_arb_line)
        self.scan_id = 0 #self.table_view.get_model_id_start_val()
        self.table_view.create_new_model(use_center=use_center)
        self.table_view.set_model_id_start_val(0)
        self.table_view.set_model_column_defaults()
        #self.on_new_region()
        self.xpos_name = DNM_SAMPLE_X
        self.ypos_name = DNM_SAMPLE_Y
        # set font
        # set column width to fit contents (set font first!)
        self.table_view.resizeColumnsToContents()
        self.table_view.setSortingEnabled(False)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self.table_view)
        self.setLayout(layout)
        self.clearFocus()
        
        self.ev_sel_widget.changed.connect(self.on_ev_table_changed)

        self.table_view.scan_changed.connect(self.on_scan_changed)
        self.table_view.del_region.connect(self.delete_row)
        self.table_view.row_selected.connect(self.on_row_selected)
        
        self.table_view.add_region.connect(self.on_new_region)
    
    
    def set_positioners(self, xpos_name, ypos_name):
        self.xpos_name = xpos_name
        self.ypos_name = ypos_name
        
    
    def set_spatial_range(self, qrect):
        ''' limit the size of a possible scan to be within the specified rect'''
        
        self.table_view.set_x_spatial_range(qrect.width()) #(xleft, ytop, width, height)
        self.table_view.set_y_spatial_range(qrect.height()) #(xleft, ytop, width, height)
        
    def set_spatial_startstop(self, qrect):
        ''' limit the size of a possible scan to be within the specified rect'''
        (x1, y1, x2, y2) = qrect.getCoords()
        self.table_view.set_x_spatial_startstop((x1, x2)) #(xleft, ytop, width, height)
        self.table_view.set_x_spatial_range((y1, y2)) #(xleft, ytop, width, height)
        
    
    def enable_add_region_menu(self, do=True):
        '''SpatialSelWidget'''
        self.add_region_enabled = do
    
    def on_ev_table_changed(self):
        '''SpatialSelWidget'''
        scan = self.get_row_data_by_item_id(self.scan_id)
        self.spatial_row_changed.emit(scan)
        
    
    def on_scan_changed(self, row, scan):
        '''SpatialSelWidget'''
        #print 'SpatialSelWidget: on_scan_changed row(%d) scan_id(%d)' % (row, scan[SPDB_ID_VAL])
        #_logger.debug('SpatialSelWidget: on_scan_changed, emitting spatial_row_changed sig')
        self.spatial_row_changed.emit(scan)
        self.check_if_table_empty()
    
    def deselect_all(self):
        self.table_view.clearSelection()
    
    def select_row(self, row_idx=None, item_id=None):
        if(row_idx is not None):
            self.table_view.select_row(row_idx)
        elif(item_id is not None):
            row_idx = self.table_view.tablemodel.get_scan_rowidx(item_id)
            self.table_view.select_row(row_idx)    
    
    def get_row_idx(self, item_id):
        return(self.table_view.tablemodel.get_scan_rowidx(item_id))
    
    def get_row_data_by_item_id(self, item_id):
        return(self.table_view.get_scan(item_id))
    
    def modify_row_data(self, item_id, scan):
        self.table_view.modify_scan(item_id, scan)
    
    def remove_model(self, model_id):
        """
        remove_model(): description

        :param model_id: model_id description
        :type model_id: model_id type

        :returns: None
        """
        self.table_view.remove_model(model_id)
        self.check_if_table_empty()
        self.deselect_all()
    
    def delete_row(self, sp_model_id=None):
        """
        delete_model(): description

        :param sp_model_id=None: sp_model_id=None description
        :type sp_model_id=None: sp_model_id=None type

        :returns: None
        """
        """
        This function is called by the right click menu action for deleting a row.
        
        this function takes the model_id of the desired spatial region
        that needs to be deleted. For spatial models the sequence for deletion is as folows:
            - find the model_id of the EV model that the model we are deleting is connected to ([SPDB_EV_ID])
            - call the self.ev_sel_widget 'delete_model' with the EV model_id, ([SPDB_EV_ID])
            - call 'remove_model(sp_model_id)'
            - create a new widget_com dict and set the relevant fields so that any other widget listening
            will be given all of the information required to delete this ROI from its contents, 
            - emit the sp_db dict with the command DEL_ROI
            - force an update of the table view by selecting the first row of the spatial table
        """
        if(sp_model_id is None):
            scan = self.table_view.get_cur_selected_scan()
            if(scan is None):
                #no more scans left
                return    
            sp_model_id = scan[SPDB_ID_VAL]
        
        scan = self.table_view.get_scan(sp_model_id)
        if(scan is None):
            _logger.error('delete_model: model %d does not exist' % sp_model_id)
            return
        
        
        if(self.single_ev_model):
            #only delete ev region if we are deleting the last of the spatial regions
            if(len(self.get_regions()) == 1):    
                self.ev_sel_widget.delete_model(scan[SPDB_EV_ID])
        else:
            self.ev_sel_widget.delete_model(scan[SPDB_EV_ID])
        self.on_delete_region(sp_model_id)
        #self.table_view.remove_model(sp_model_id)
        
        sp_db = make_spatial_db_dict()
        sp_db[WDGCOM_CMND] = widget_com_cmnd_types.DEL_ROI        
        dct_put(sp_db, SPDB_ID_VAL, sp_model_id)

        if(scan[SPDB_X][NPOINTS] == 1):
            scan_type = scan_types.SAMPLE_POINT_SPECTRUM
            #sp_db['SCAN_PLUGGIN']['ITEM']['TYPE'] = spatial_type_prefix.PNT
            dct_put(sp_db, SPDB_PLOT_SHAPE_TYPE, spatial_type_prefix.PNT)
        else:
            scan_type = scan_types.SAMPLE_IMAGE
            #sp_db['SCAN_PLUGGIN']['ITEM']['TYPE'] = spatial_type_prefix.ROI
            dct_put(sp_db, SPDB_PLOT_SHAPE_TYPE, spatial_type_prefix.ROI)
            
        dct_put(sp_db, SPDB_SCAN_PLUGIN_TYPE, scan_type)
        
        self.roi_deleted.emit(sp_db)
        #force an update of the view by selecting the first row after a deletion
        #self.table_view.select_row(row_idx=0)
        self.deselect_all()
        
        self.check_if_table_empty()
    
    def check_if_table_empty(self):
        if(self.table_view.get_num_rows() <= 0):
            self.ev_sel_widget.enable_add_region(False)
            self.reset_single_ev_mode_id()
        else:
            #if(not self.single_ev_model):
            self.ev_sel_widget.enable_add_region(True)    
            #self.single_ev_model_id = self.get_cur_model_id()
            self.single_ev_model_id = self.ev_sel_widget.get_cur_model_id()
    
    def reset_single_ev_mode_id(self):
        self.single_ev_model_id = None
    
    def get_data(self, model_id=None):
        """    
        get_data(): description

        :param model_id=None: model_id=None description
        :type model_id=None: model_id=None type

        :returns: None
        """
        return(self.table_view.get_scan_list(model_id))
        
    def get_cur_model_id(self):
        """
        get_cur_model_id(): description

        :returns: None
        """
        return(self.table_view.model_id)
    
    def on_row_selected(self, scan):
        """
        on_row_selected(): description

        :param scan: scan description
        :type scan: scan type

        :returns: None
        """
        #print 'SPATIAL model_ID %d selected EV_ID=%d' % (scan[SPDB_ID_VAL], scan[SPDB_EV_ID])
        self.ev_sel_widget.switch_view_model(scan[SPDB_EV_ID])
        self.ev_sel_widget.table_view.select_row()
        self.model_change.emit(scan[SPDB_ID_VAL])
        
    def switch_view_model(self, model_id):
        """
        switch_view_model(): description

        :param model_id: model_id description
        :type model_id: model_id type

        :returns: None
        """
        self.table_view.switch_models(model_id)
            
    def clear_table(self):
        """
        clear_table(): description

        :returns: None
        """
        self.reset_single_ev_mode_id()
        self.table_view.remove_all()
    
    def set_editable(self, ed):
        """
        set_editable(): description

        :param ed: ed description
        :type ed: ed type

        :returns: None
        """
        self.table_view.set_model_editable(ed)
    
    def get_regions(self):
        """
        get_regions(): description

        :returns: None
        """
        rois = self.table_view.model().get_scans() 
        return(rois)
    
    def on_new_region(self, scan=None, add_energy_roi=True):
        """
        on_new_region(): on new spatial region

        :param scan=None: scan=None description
        :type scan=None: scan=None type

        :returns: None
        """
        if(not self.add_region_enabled):
            return
        
        #scan = get_base_energy_roi('EV', DNM_ENERGY, 370, 395, 25.0, 10, 2.5, self.pol_roi, self.off_roi, stepSize=None, enable=True)
        if(scan is None):
            
            #use previous scans vals for new range
            cur_scan = copy.deepcopy(self.table_view.get_cur_selected_scan())
            slist = self.table_view.get_scan_list()
            if((cur_scan is None) and (len(slist) == 0)):
                #create a default
                x_roi = get_base_roi(SPDB_X, self.xpos_name, 0, 100, 20, stepSize=None, max_scan_range=None, enable=True)
                y_roi = get_base_roi(SPDB_Y, self.ypos_name, 0, 100, 20, stepSize=None, max_scan_range=None, enable=True)
                scan = make_spatial_db_dict(x_roi=x_roi, y_roi=y_roi)
            else:    
                #get the last one
                if(len(slist) > 0):
                    cur_scan = slist[-1]
                #else use cur_scan
                x_roi = get_base_roi(SPDB_X, self.xpos_name, cur_scan[SPDB_X][CENTER], cur_scan[SPDB_X][RANGE], cur_scan[SPDB_X][NPOINTS], stepSize=None, max_scan_range=None, enable=True)
                y_roi = get_base_roi(SPDB_Y, self.ypos_name, cur_scan[SPDB_Y][CENTER], cur_scan[SPDB_Y][RANGE], cur_scan[SPDB_Y][NPOINTS], stepSize=None, max_scan_range=None, enable=True)
                scan = make_spatial_db_dict(x_roi=x_roi, y_roi=y_roi)
            #self.scan_id += 1
            self.scan_id = self.table_view.get_next_model_id()
        else:
            self.scan_id = scan[SPDB_ID_VAL]
            
            #dct_put(scan, SPDB_SCAN_PLUGIN_ITEM_ID, self.scan_id)
        self.table_view.set_model_id_start_val(self.scan_id)
        if((add_energy_roi) and (self.ev_sel_widget is not None)):    
            #create a new ev roi model with the scan[SPDB_ID_VAL] as its key
            if(self.single_ev_model):
                if(self.single_ev_model_id is None):
                    scan[SPDB_EV_ID] = self.ev_sel_widget.table_view.create_new_model()
                    self.single_ev_model_id = scan[SPDB_EV_ID]
                    self.ev_sel_widget.enable_add_region_menu(True)
                    self.ev_sel_widget.on_new_region()
                else:
                    scan[SPDB_EV_ID] =  self.single_ev_model_id
            else:
                scan[SPDB_EV_ID] = self.ev_sel_widget.table_view.create_new_model()
                self.single_ev_model_id = scan[SPDB_EV_ID]
                self.ev_sel_widget.on_new_region()    
            #self.ev_sel_widget.on_new_region()
        self.table_view.add_scan(scan, self.scan_id)
        self.check_if_table_empty()
    
    
    def load_scan(self, loaded_scan=None):
        """
        on_new_region(): description

        :param scan=None: scan=None description
        :type scan=None: scan=None type

        :returns: None
        """
        #scan = get_base_energy_roi('EV', DNM_ENERGY, 370, 395, 25.0, 10, 2.5, self.pol_roi, self.off_roi, stepSize=None, enable=True)
        if(loaded_scan is None):
            _logger.error('SpatialSelWidget: load_scan, no scan provided')
            return
        
        #x_roi = get_base_roi(SPDB_X, loaded_scan[SPDB_X][POSITIONER], loaded_scan[SPDB_X][CENTER], loaded_scan[SPDB_X][RANGE], loaded_scan[SPDB_X][NPOINTS], stepSize=None, max_scan_range=None, enable=True)
        #y_roi = get_base_roi(SPDB_Y, loaded_scan[SPDB_Y][POSITIONER], loaded_scan[SPDB_Y][CENTER], loaded_scan[SPDB_Y][RANGE], loaded_scan[SPDB_Y][NPOINTS], stepSize=None, max_scan_range=None, enable=True)
        #scan = make_spatial_db_dict(x_roi=x_roi, y_roi=y_roi)
        #scan[SPDB_ID_VAL] = loaded_scan[SPDB_ID_VAL]
        #scan[SPDB_EV_ID] = loaded_scan[SPDB_EV_ID]
        #scan[SPDB_EV_ROIS] = loaded_scan[SPDB_EV_ROIS]
        
        self.scan_id = loaded_scan[SPDB_ID_VAL]    
        #create a new ev roi model with the scan[SPDB_EV_ID] as its key
        self.ev_sel_widget.table_view.create_new_model(model_id = loaded_scan[SPDB_EV_ID])
        #make sure that the Ev and pol widgets know they are allowed now to add a region
        if(not self.single_ev_model):
            self.ev_sel_widget.enable_add_region(True)
            self.ev_sel_widget.load_scan(loaded_scan[SPDB_EV_ROIS])
            
        elif(self.single_ev_model and (len(self.ev_sel_widget.get_ev_regions()) == 0)):
            #we still need at least 1 ev region
            self.ev_sel_widget.enable_add_region(True)
            self.ev_sel_widget.load_scan(loaded_scan[SPDB_EV_ROIS])
            #dec 6 self.ev_sel_widget.enable_add_region(False)
            
        #self.table_view.remove_all()
        self.table_view.add_scan(loaded_scan, self.scan_id)
        self.check_if_table_empty()
    
    def add_scan(self, loaded_scan=None):
        """
        add_scan(): description

        :param scan: scan description
        :type scan: scan type

        :param scan_id: scan_id description
        :type scan_id: scan_id type

        :returns: None
        """
        """ add a scan to the current model that is owned by scan_id"""
        self.scan_id = loaded_scan[SPDB_ID_VAL]
        
        #create a new ev roi model with the scan[SPDB_EV_ID] as its key
        self.ev_sel_widget.table_view.create_new_model(model_id = loaded_scan[SPDB_EV_ID])
        self.ev_sel_widget.load_scan(loaded_scan[SPDB_EV_ROIS])
        self.table_view.add_scan(loaded_scan, self.scan_id)
        self.check_if_table_empty()
    
        
        
    def on_delete_region(self, scan_id=None):
        """
        on_delete_region(): description

        :param scan_id=None: scan_id=None description
        :type scan_id=None: scan_id=None type

        :returns: None
        """
        if(scan_id is None):
            scan = self.table_view.get_cur_selected_scan()
            scan_id = scan[SPDB_ID_VAL]
        
        print('spatial deleting[%d]' % scan_id)
        self.table_view.remove_scan(scan_id)    
        self.check_if_table_empty()
            
            
    def on_single_region(self):
        """
        on_single_region(): description

        :returns: None
        """
        self.table_view.model().remove_all_except_first(self.scan_id)
    
    
    def enable_multi_spatial(self, val):
        if(val):
            self.table_view.model().set_max_rows(MAX_SPATIAL_ROWS)
        else:
            #allow only a single row
            self.table_view.model().set_max_rows(1)        
            
            
            