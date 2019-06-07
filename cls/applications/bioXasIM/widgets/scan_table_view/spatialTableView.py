'''
Created on Nov 16, 2016

@author: bergr
'''

from cls.applications.pyStxm.widgets.scan_table_view.arbitraryLineTableModel import ArbitraryLineScanTableModel
from cls.applications.pyStxm.widgets.scan_table_view.baseScanTable import *


class SpatialScanTableModel(BaseScanTableModel):
    
    scan_changed = QtCore.pyqtSignal(int, object)
    
    def __init__(self, hdrList, datain, parent = None, use_center=True, is_arb_line=False, *args):
        """
        __init__(): description

        :param hdrList: hdrList description
        :type hdrList: hdrList type

        :param datain: datain description
        :type datain: datain type

        :param parent=None: parent=None description
        :type parent=None: parent=None type

        :param *args: *args description
        :type *args: *args type

        :returns: None
        """
        #QtCore.QAbstractTableModel.__init__(self, parent, *args)
        super(SpatialScanTableModel, self).__init__( hdrList, datain, parent, *args)
        # a dict that will use spatial region scan_id's as key to EnergyRegionScanDef's 
        self.cur_scan_row = None
        self.scanListData = datain
        self.editable = False
        if('CenterX' in hdrList):
            self.column_map = C_SPATIAL_DCT
        else:
            self.column_map = S_SPATIAL_DCT

        self.set_min_rows(0)
        self.set_max_rows(20)
        
        
    def data(self, index, role):
        """
        override base table model data function
        data(): description

        :param index: index description
        :type index: index type

        :param role: role description
        :type role: role type

        :returns: None
        """
        """ this function gets called once for each Qt.Role """
        row = index.row()
        col = index.column()
        enabled = False
            
        if not index.isValid():
            print('index is invalid')
            return None
        
        flags = index.flags()
        if flags & QtCore.Qt.ItemIsEditable:
            enabled = True
        
        if role == QtCore.Qt.DisplayRole:
            scan = self.scanListData[row]
            if(col == 0):
                v = scan[SPDB_ID_VAL]
            else:
                v = get_val_from_sp_db(self.column_map[col]['hdr'], scan)
                #v = scan[self.column_map[col]['hdr']]
                        
            if(type(v) is str):
                return(v)
            if(type(v) is np.float32):
                val = '%.3f' % v
                return(val)
            if(type(v) is float):
                val = '%.3f' % v
                return(val)
            if(type(v) is int):
                val = '%d' % v
                return(val)
            if(type(v) is int):
                val = '%d' % v
                return(val)
            if(type(v) is bool):
                if(v):
                    return('True')
                else:
                    return('False')
            
        elif role == QtCore.Qt.BackgroundRole:
            if(col == 0):
                bg = QtGui.QBrush(QtCore.Qt.gray)
            elif(col < 5):
                bg = QtGui.QBrush(QtCore.Qt.lightGray)
                #pass
            else:
                if(enabled):
                    bg = QtGui.QBrush(QtCore.Qt.white)
                else:
                    bg = QtGui.QBrush(QtGui.QColor(220, 220, 220))
            return bg
        elif role == QtCore.Qt.ForegroundRole:
            if(enabled):
                fg = QtGui.QBrush(QtCore.Qt.black)
            else:
                fg = QtGui.QBrush(QtCore.Qt.blue)
            return fg
        elif role == QtCore.Qt.FontRole:
            fnt = QtGui.QFont()
            fnt.setPointSize(TABLE_FONT_SIZE)
            if(col == 0):
                fnt.setBold(True)
            return fnt
        elif role == QtCore.Qt.TextAlignmentRole:
            if (col == 0): 
                return(QtCore.Qt.AlignLeft)
            else:
                #return(QtCore.Qt.AlignRight)
                return(QtCore.Qt.AlignCenter)
        else:
                
                #print 'returning None [%d,%d] role = %d' % (row,col, role)
                return None
            
    def setData(self, index, value, role, recalc=True, do_signal=True):
        """
        setData(): description

        :param index: index description
        :type index: index type

        :param value: value description
        :type value: value type

        :param role: role description
        :type role: role type

        :param recalc=True: recalc=True description
        :type recalc=True: recalc=True type

        :param do_signal=True: do_signal=True description
        :type do_signal=True: do_signal=True type

        :returns: None
        """
        row = index.row()
        col = index.column()
        ok = True
        if(role == QtCore.Qt.EditRole):
            
            if(col == 0):
                return True
                #val, ok  = value.toLongLong()
            elif(col == 10):
                val  = str(value.toString())
                if(len(val) < 1):
                    ok = False
            else:
                if(len(value) > 0):
                    val  = float(value)
                else:
                    return(True)
            
            #call the associated setter function for this column (this is setup in the scan definition class
            if(ok):
                #only change the value if the user entered a value
                scan = self.scanListData[row]
                #    dct['hdr'] = hdr_name
                #    dct['func_str'] = func_str
                #    dct['floor_val'] = floor_val
                #    dct['ceiling_val'] = ceiling_val
#                 if((self.column_map[col]['floor_val'] != None) and (val > self.column_map[col]['floor_val'])):
#                     if((self.column_map[col]['ceiling_val'] != None) and (val <= self.column_map[col]['ceiling_val'])):
#                         #scan[self.column_map[col]['hdr']] = val
#                         roi = get_roi_from_sp_db(self.column_map[col]['hdr'], scan)
#                         set_field_val_in_sp_db(self.column_map[col]['hdr'], val, scan)
#                         func = self.column_map[col]['func']
#                     else:
#                         return    
#                 else:
#                     #dont change it
#                     return    

                #if((self.column_map[col]['floor_val'] != None) and (val > self.column_map[col]['floor_val'])):
                #    if((self.column_map[col]['ceiling_val'] != None) and (val <= self.column_map[col]['ceiling_val'])):
                #        #scan[self.column_map[col]['hdr']] = val
                roi = get_roi_from_sp_db(self.column_map[col]['hdr'], scan)
                set_field_val_in_sp_db(self.column_map[col]['hdr'], val, scan)
                func = self.column_map[col]['func']
                #    else:
                #        return    
                #else:
                #    #dont change it
                #    return    
                #print '\nsetData TOP: rect' , scan[SPDB_RECT]    
                #force the row to recalc
                if(recalc):
                    #now call the resepctive function to recalc the scan params
                    func(roi)
                    #print 'setData BTM: rect' , scan[SPDB_RECT]        
        if((role == QtCore.Qt.EditRole) or (role == QtCore.Qt.DisplayRole)):
            #must emit this as part of the framework support for an editable AbstractTableModel
            scan = self.scanListData[row]
            self.dataChanged.emit(index, index)
            
            if(do_signal):
                #print 'EnergyScanTableModel: setData: emitting scan_changed'
                self.scan_changed.emit(row, scan)
                
            return True
    
    def modify_data(self, scan_id, newscan, do_step_npts=False):
        """
        modify_data(): description

        :param scan_id: scan_id description
        :type scan_id: scan_id type

        :param newscan: newscan description
        :type newscan: newscan type

        :param do_step_npts=False: do_step_npts=False description
        :type do_step_npts=False: do_step_npts=False type

        :returns: None
        """
        ''' tpl = ((startx, starty), (rangex, rangey))'''
        self.replace_scan(scan_id, newscan, do_step_npts)
        self.dataChanged.emit(QtCore.QModelIndex(), QtCore.QModelIndex())

    
class SpatialScanTableView(BaseScanTableView):
    
    def __init__(self, scanList=[], parent=None, use_center=True, is_point=False, is_arb_line=False):
        """
        __init__(): description

        :param scanList=[]: scanList=[] description
        :type scanList=[]: scanList=[] type

        :param parent=None: parent=None description
        :type parent=None: parent=None type
        
        :param use_center=True: setup table useing center/range or start/stop
        :type use_center=None: boolean
        
        :param is_point=True: setup table with read only columnds for Range, Step, Npoints
        :type is_point=None: boolean

        :returns: None
        """
        #setup the header for the top of the table
        if(use_center):
            hdrList = ['ID','CenterX', 'RangeX', 'CenterY', 'RangeY', 'StepX', 'StepY', 'PointsX', 'PointsY']
        else:    
            hdrList = ['ID','StartX', 'StopX', 'StartY', 'StopY', 'StepX', 'StepY', 'PointsX', 'PointsY']
            #self.func_list = ['xy_id', 'centerX', 'rangeX','centerY', 'rangeY','stepX', 'stepY', 'NpointsX', 'NpointsY']
        
        if(is_arb_line):
            super(SpatialScanTableView, self).__init__(hdrList, scanList, ArbitraryLineScanTableModel, parent)
        else:    
            super(SpatialScanTableView, self).__init__(hdrList, scanList, SpatialScanTableModel, parent)
        self.xyNum = 0
        
        self.setStyleSheet(SPATIAL_SS)
        if(is_point):
            self.set_model_column_defaults = self.set_model_column_for_points
        if(is_arb_line):
            self.set_model_column_defaults = self.set_model_column_for_arbitrarty_line
            
        self.init_model(use_center, is_arb_line)
        
        #self.set_model_id_start_val(SPATIAL_CNTR)
    
    def init_model(self, use_center=True, is_arb_line=False):
        """
        init_model(): description

        :returns: None
        """
        if(is_arb_line):
            self.tablemodel = ArbitraryLineScanTableModel(self.hdrList, self.scans, self, use_center=use_center)
        else:    
            self.tablemodel = SpatialScanTableModel(self.hdrList, self.scans, self, use_center=use_center)
        self.set_model_column_defaults()
    
    def modify_scan(self, scan_id, newscan, do_step_npts=False):
        """
        modify_scan(): description

        :param scan_id: scan_id description
        :type scan_id: scan_id type

        :param newscan: newscan description
        :type newscan: newscan type

        :param do_step_npts=False: do_step_npts=False description
        :type do_step_npts=False: do_step_npts=False type

        :returns: None
        """
        ''' '''
        scan = self.tablemodel.get_scan(scan_id)
        if(scan is not None):
            self.tablemodel.modify_data(scan_id, newscan, do_step_npts)
    
    def set_max_spatial_val(self, column_name, _max):
        '''
        this function sets the ceiling_val in the model for the specified column so that
        the user cannot enter a value that the user woants deemed "OUT of RANGE"
        '''
        col = self.tablemodel.get_column_with_name(column_name)
        if(col):
            self.tablemodel.column_map[col]['ceiling_val'] = _max
        else:
            _logger.error('%s does not exist in tablemodel.column_map' % column_name)
    
    def set_min_spatial_val(self, column_name, _min):
        '''
        this function sets the ceiling_val in the model for the specified column so that
        the user cannot enter a value that the user woants deemed "OUT of RANGE"
        '''
        col = self.tablemodel.get_column_with_name(column_name)
        if(col):
            self.tablemodel.column_map[col]['floor_val'] = _min
        else:
            _logger.error('%s does not exist in tablemodel.column_map' % column_name)        
    
    def set_x_spatial_range(self, _max):
        self.set_max_spatial_val('RANGEX', _max)
        
    def set_y_spatial_range(self, _max):    
        self.set_max_spatial_val('RANGEY', _max)
        
    def set_x_spatial_startstop(self, strt_stop):    
        self.set_min_spatial_val('STARTX', strt_stop[0])    
        self.set_max_spatial_val('STARTX', strt_stop[1])
        self.set_min_spatial_val('STOPX', strt_stop[0])    
        self.set_max_spatial_val('STOPX', strt_stop[1])
        
    def set_y_spatial_startstop(self, strt_stop):    
        self.set_min_spatial_val('STARTY', strt_stop[0])    
        self.set_max_spatial_val('STARTY', strt_stop[1])
        self.set_min_spatial_val('STOPY', strt_stop[0])    
        self.set_max_spatial_val('STOPY', strt_stop[1])    
        
    def set_model_column_defaults(self):
        """
        set_model_column_defaults(): description

        :returns: None
        """
        self.tablemodel.set_col_readonly(0)
#        for i in range(1,len(self.hdrList)):
#                self.horizontalHeader().setSectionResizeMode(i, QtWidgets.QHeaderView.Stretch)
    
    def set_model_column_for_points(self):
        """
        set_model_column_defaults(): set columns of table to be read only for Range, Step, Npoints 
                     0       1       2        3         4        5        6         7          8
        hdrList = ['ID','StartX', 'StopX', 'StartY', 'StopY', 'StepX', 'StepY', 'PointsX', 'PointsY']

        :returns: None
        """
        self.tablemodel.set_col_readonly(0)
        self.tablemodel.set_col_readonly(2)
        self.tablemodel.set_col_readonly(4)
        self.tablemodel.set_col_readonly(5)
        self.tablemodel.set_col_readonly(6)
        self.tablemodel.set_col_readonly(7)
        self.tablemodel.set_col_readonly(8)
        
#        for i in range(1,len(self.hdrList)):
#                self.horizontalHeader().setSectionResizeMode(i, QtWidgets.QHeaderView.Stretch)
    
    
    def set_model_column_for_arbitrarty_line(self):
        """
        set_model_column_defaults(): set columns of table to be read only for StepY, NpointsY 
                     0       1       2        3         4        5        6         7          8
        hdrList = ['ID','StartX', 'StopX', 'StartY', 'StopY', 'StepX', 'StepY', 'PointsX', 'PointsY']

        :returns: None
        """
        self.tablemodel.set_col_readonly(0)
        self.tablemodel.set_col_readonly(6)
        self.tablemodel.set_col_readonly(8)
        
#        for i in range(1,len(self.hdrList)):
#                self.horizontalHeader().setSectionResizeMode(i, QtWidgets.QHeaderView.Stretch)
    
        
    def sizeHintForColumn(self, column):
        """
        sizeHintForColumn(): description

        :param column: column description
        :type column: column type

        :returns: None
        """
        fm = self.fontMetrics()
        max_width = 0
        for i in range(self.model().rowCount()):
            width = fm.width(self.model().get_cell(i,column)) + 10
            if  width > max_width:
                max_width = width
        return max_width
    

    





        
if __name__ == '__main__':
    import sys
    from cls.appWidgets.spyder_console import ShellWidget#, ShellDock
    
    log_to_qt()
    app = QtWidgets.QApplication(sys.argv)
    #win = EnergySelWidget()
    #win.show()
    #spatial = SpatialSelWidget()
    #spatial.show()
    
    multi = MultiRegionWidget(use_center=True, enable_multi_spatial=True)
    multi.enable_add_spatial_region_menu(True)
    multi.show_load_btn()
    multi.show_getdata_btn()
    
    ns = {'main': multi, 'g':globals() }
        #msg = "Try for example: widget.set_text('foobar') or win.close()"
    pythonshell = ShellWidget(parent=None, namespace=ns,commands=[], multithreaded=True)
    multi.layout().addWidget(pythonshell)
    
    multi.show()
    
    sys.exit(app.exec_())    
    
    
    
