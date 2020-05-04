'''
Created on 2013-05-16

@author: bergr
'''
import copy

import numpy as np
from PyQt5 import QtCore, QtGui

from bcm.devices.device_names import *
from cls.applications.pyStxm.main_obj_init import MAIN_OBJ
from cls.types.stxmTypes import scan_types, spatial_type_prefix, IMAGE_LXL, IMAGE_PXP, energy_scan_order_types
from cls.utils.dict_utils import dct_put, dct_get
from cls.utils.log import get_module_logger, log_to_qt
from cls.utils.roi_dict_defs import *
from cls.utils.roi_utils import get_base_roi, get_base_energy_roi, \
    get_epu_pol_dct, make_spatial_db_dict, widget_com_cmnd_types, \
    on_range_changed, on_npoints_changed, on_step_size_changed, on_start_changed, on_stop_changed, \
    on_center_changed, get_unique_roi_id

_logger = get_module_logger(__name__)

#this is the value that will be added to the start and end of each extra EV region
EV_SCAN_EDGE_RANGE = 0.2
TABLE_FONT_SIZE = 8

SPATIAL_CNTR = 1000
EV_CNTR = 500
POL_CNTR = 0

MAX_SPATIAL_ROWS = 20
#         self.setStyleSheet("color: blue;"
#                         "background-color: rgb(114, 148, 240);"
#                         "selection-color: yellow;"
#                         "selection-background-color: blue;")


SPATIAL_SS = "QHeaderView::section {background: rgb(200,200, 200);background-color: rgb(200,200, 200); selection-background-color: ; selection-color: ;} background-color: rgb(200,200, 200); selection-background-color: ; selection-color: ;"
EV_SS = "QHeaderView::section {background: rgb(200,200, 200);background-color: rgb(200,200, 200); selection-background-color: ; selection-color: ;}background-color: rgb(220,220, 220); selection-background-color: ; selection-color: ;"
POL_SS = "QHeaderView::section {background: rgb(200,200, 200);background-color: rgb(200,200, 200); selection-background-color: ; selection-color: ;}background-color: rgb(240,240, 240); selection-background-color: ; selection-color: ;"

SPATIAL_SS = ""
EV_SS = ""
POL_SS = ""

def make_1d_array(numpts, val):
    arr = np.ones(numpts)
    arr[:] = val
    return(arr)

class ScanOptionError(Exception):
    """Base class for exceptions in this module."""
    def __init__(self, msg):
        """
        __init__(): description

        :param msg: msg description
        :type msg: msg type

        :returns: None
        """
        self.msg = msg
    def __str__(self):
        """
        __str__(): description

        :returns: None
        """
        return repr(self.msg)


#QTableWidget signals
#void    cellActivated ( int row, int column )
#void    cellChanged ( int row, int column )
#void    cellClicked ( int row, int column )
#void    cellDoubleClicked ( int row, int column )
#void    cellEntered ( int row, int column )
#void    cellPressed ( int row, int column )
#void    currentCellChanged ( int currentRow, int currentColumn, int previousRow, int previousColumn )
#void    currentItemChanged ( QTableWidgetItem * current, QTableWidgetItem * previous )
#void    itemActivated ( QTableWidgetItem * item )
#void    itemChanged ( QTableWidgetItem * item )
#void    itemClicked ( QTableWidgetItem * item )
#void    itemDoubleClicked ( QTableWidgetItem * item )
#void    itemEntered ( QTableWidgetItem * item )
#void    itemPressed ( QTableWidgetItem * item )
#void    itemSelectionChanged ()


class BaseScanTableModel(QtCore.QAbstractTableModel):
    
    scan_changed = QtCore.pyqtSignal(int, object)
    
    def __init__(self, hdrList=[], datain=[[]], parent = None, *args):
        """
        __init__(): description

        :param hdrList=[]: hdrList=[] description
        :type hdrList=[]: hdrList=[] type

        :param datain=[[]]: datain=[[]] description
        :type datain=[[]]: datain=[[]] type

        :param parent=None: parent=None description
        :type parent=None: parent=None type

        :param *args: *args description
        :type *args: *args type

        :returns: None
        """
        #QtCore.QAbstractTableModel.__init__(self, parent, *args)
        super(BaseScanTableModel, self).__init__(parent, *args)
        self.scanListData = list(datain)
        self.hdrList = list(hdrList)
        self.scanProgress = {}
        self.cur_scan_id = 0
        self.column_map = None
        
        self.min_rows = 0
        self.max_rows = 1
        
        self.valid_range = (None, None, None, None)
        
        #have a way to set specific rows or columns read only
        self.rd_only_rows = {}
        self.rd_only_cols = {}
        
        self._get_funcs = []
        self._set_funcs = []
                
    def get_column_with_name(self, name):
        i = 0
        for item in self.column_map:
            if(item['hdr'] == name):
                return(i)
            i += 1
        return(None)    
    
    def set_min_rows(self, val):
        """
        set_min_rows(): description

        :param val: val description
        :type val: val type

        :returns: None
        """
        self.min_rows = val
    
    def set_max_rows(self, val):
        """
        set_max_rows(): description

        :param val: val description
        :type val: val type

        :returns: None
        """
        self.max_rows = val
        
    def set_scan_list(self, scanList):
        """
        set_scan_list(): description

        :param scanList: scanList description
        :type scanList: scanList type

        :returns: None
        """
        self.scanListData = scanList[:]
    
    def get_scan_list(self):
        """
        get_scan_list(): description

        :returns: None
        """
        #return a copy
        return(self.scanListData[:])
    
    def set_editable(self, ed):
        """
        set_editable(): description

        :param ed: ed description
        :type ed: ed type

        :returns: None
        """
        self.editable = ed
    
    def get_scans(self):
        """
        get_scans(): description

        :returns: None
        """
        #return a copy
        return(self.scanListData[:])
    
    def get_cell(self, row, col):
        """
        get_cell(): description

        :param row: row description
        :type row: row type

        :param col: col description
        :type col: col type

        :returns: None
        """
        scan = self.scanListData[row]
        return(str(scan[self.column_map[col]]))    
        
    def set_getset_funcs(self, funclist):
        """
        set_getset_funcs(): description

        :param funclist: funclist description
        :type funclist: funclist type

        :returns: None
        """
        """ 
        the view can set a custom list of functions for 
        getting and setting each column in the table 
        """
        for f in funclist:
            self._get_funcs.append('get_' + f)
            self._set_funcs.append('set_' + f)
        
    
    def set_row_readonly(self, row, rdonly=True):
        """
        set_row_readonly(): description

        :param row: row description
        :type row: row type

        :param rdonly=True: rdonly=True description
        :type rdonly=True: rdonly=True type

        :returns: None
        """
        if(rdonly):
            self.rd_only_rows[row] = rdonly
        else:
            del self.rd_only_rows[row]
    
    def set_col_readonly(self, col, rdonly=True):
        """
        set_col_readonly(): description

        :param col: col description
        :type col: col type

        :param rdonly=True: rdonly=True description
        :type rdonly=True: rdonly=True type

        :returns: None
        """
        if(rdonly):
            self.rd_only_cols[col] = rdonly
        else:
            del self.rd_only_cols[col]

    def _scan_not_exist(self, scan_id):
        """
        _scan_not_exist(): description

        :param scan_id: scan_id description
        :type scan_id: scan_id type

        :returns: None
        """
        for scan in self.scanListData:
            #if(hasattr(scan, SPDB_ID_VAL)):
            if(SPDB_ID_VAL in list(scan.keys())):
                if(scan[SPDB_ID_VAL] == scan_id):
                    #print '_get_scan_rowidx: returning %d' % row
                    return(False)
        return(True)
            
    def add_scan(self, scan):
        """
        add_scan(): description

        :param scan: scan description
        :type scan: scan type

        :returns: None
        """
        """ if scan_id does not already exist then add this scan and return success """
        
        SPATIAL_CNTR = 10000
        EV_CNTR = 5000
        POL_CNTR = 0
        
        if(self.rowCount() >= self.max_rows):
            return
        
        if(scan[SPDB_ID_VAL] is None):
            #the model is being initialized
            scan[SPDB_ID_VAL] = 0
            
        if(self._scan_not_exist(scan[SPDB_ID_VAL])):
            self.insertRow(scan)
            return(True)
        else:
            return(False)
    
    def insertRow(self, scan, parent=QtCore.QModelIndex()):
        """
        insertRow(): description

        :param scan: scan description
        :type scan: scan type

        :param parent=QtCore.QModelIndex(): parent=QtCore.QModelIndex() description
        :type parent=QtCore.QModelIndex(): parent=QtCore.QModelIndex() type

        :returns: None
        """
        self.beginInsertRows(parent, self.rowCount(parent), self.rowCount(parent))
        self.scanListData.append(scan)
        self.endInsertRows()
        #self.dataChanged.emit(parent, parent)
        return(self.rowCount(parent))
    
    def removeRow(self, row, parent=QtCore.QModelIndex()):
        """
        removeRow(): description

        :param row: row description
        :type row: row type

        :param parent=QtCore.QModelIndex(): parent=QtCore.QModelIndex() description
        :type parent=QtCore.QModelIndex(): parent=QtCore.QModelIndex() type

        :returns: None
        """
        #row = self.get_scan_rowidx(scan_id)
        if(self.rowCount() == self.min_rows):
            return
        if(row != None):
            self.beginRemoveRows(parent, row, row)
            del(self.scanListData[row])
            self.endRemoveRows()
            self.dataChanged.emit(parent, parent)
    
    
    def removeAll(self, parent=QtCore.QModelIndex()):
        """
        removeAll(): description

        :param parent=QtCore.QModelIndex(): parent=QtCore.QModelIndex() description
        :type parent=QtCore.QModelIndex(): parent=QtCore.QModelIndex() type

        :returns: None
        """
        self.beginRemoveRows(parent, 0,  len(self.scanListData))
        #self.scanListData = []
        for row in range(len(self.scanListData)):
            #the list shrinks each time so only delete from teh top
            del(self.scanListData[0])
        self.endRemoveRows()
        self.dataChanged.emit(parent, parent)
    
    def set_scan_for_single_ev(self):
        """
        set_scan_for_single_ev(): description

        :returns: None
        """
        scan = self.scanListData[0]
        scan[STOP] = scan[START]
        scan[RANGE] = 0.0
        scan[NPOINTS] = 1
        scan[STEP] = 0.0
    
    def remove_all_except_first(self, scan_id, parent=QtCore.QModelIndex()):
        """
        remove_all_except_first(): description

        :param scan_id: scan_id description
        :type scan_id: scan_id type

        :param parent=QtCore.QModelIndex(): parent=QtCore.QModelIndex() description
        :type parent=QtCore.QModelIndex(): parent=QtCore.QModelIndex() type

        :returns: None
        """
        l = list(range(1, len(self.scanListData)))
        l.reverse()
        self.beginRemoveRows(parent, 1, len(l))
                
        for row in l:
            del(self.scanListData[row])
        self.endRemoveRows()
        self.set_scan_for_single_ev()
        self.dataChanged.emit(parent, parent)
    
    def get_scan_rowidx(self, scan_id):
        """
        get_scan_rowidx(): description

        :param scan_id: scan_id description
        :type scan_id: scan_id type

        :returns: None
        """
        """ return the row of the scan with the matching scan_id """
        row = 0
        #print 'checking for scan_id = %d' % scan_id
        for scan in self.scanListData:
            #print 'get_scan_rowidx: [%d] = %d' % (row, scan['ID'])
            if(scan[SPDB_ID_VAL] == scan_id):
                #print '_get_scan_rowidx: returning %d' % row
                return(row)
            row += 1
        return(None)
    
    def replace_scan(self, scan_id, newscan, do_step_npts=True):
        """
        replace_scan(): description

        :param scan_id: scan_id description
        :type scan_id: scan_id type

        :param newscan: newscan description
        :type newscan: newscan type

        :param do_step_npts=True: do_step_npts=True description
        :type do_step_npts=True: do_step_npts=True type

        :returns: None
        """
        """ if the scan_id already exists then replace the scan in that row with the new one """
        row = 0
        for scan in self.scanListData:
            #print 'get_scan_rowidx: [%d] = %d' % (row, scan['ID'])
            if(scan[SPDB_ID_VAL] == scan_id):
                self.scanListData[row][SPDB_X][CENTER] = newscan[SPDB_X][CENTER] 
                self.scanListData[row][SPDB_Y][CENTER] = newscan[SPDB_Y][CENTER]
                self.scanListData[row][SPDB_X][RANGE] = newscan[SPDB_X][RANGE]
                self.scanListData[row][SPDB_Y][RANGE] = newscan[SPDB_Y][RANGE]
                #if(do_step_npts):
                self.scanListData[row][SPDB_X][STEP] = newscan[SPDB_X][STEP]
                self.scanListData[row][SPDB_Y][STEP] = newscan[SPDB_Y][STEP]
                self.scanListData[row][SPDB_X][NPOINTS] = newscan[SPDB_X][NPOINTS]
                self.scanListData[row][SPDB_Y][NPOINTS] = newscan[SPDB_Y][NPOINTS]
            row += 1
        
    
    def get_scan_by_row(self, row):
        """
        get_scan_by_row(): description

        :param row: row description
        :type row: row type

        :returns: None
        """
        """ return the scan in the corresponding row """
        #print 'checking for scan_id = %d' % scan_id
        return(self.scanListData[row])
    
    def get_scan(self, scan_id):
        """
        get_scan(): description

        :param scan_id: scan_id description
        :type scan_id: scan_id type

        :returns: None
        """
        """ return the row of the scan with the matching scan_id """
        #print 'checking for scan_id = %d' % scan_id
        for scan in self.scanListData:
            #print 'get_scan_rowidx: [%d] = %d' % (row, scan['ID'])
            if(scan[SPDB_ID_VAL] == scan_id):
                #print '_get_scan_rowidx: returning %d' % row
                return(scan)
        return(None)
    
    def set_cur_scan_progress(self, progress, scan_id):
        """
        set_cur_scan_progress(): description

        :param progress: progress description
        :type progress: progress type

        :param scan_id: scan_id description
        :type scan_id: scan_id type

        :returns: None
        """
        """ sets the scan with scan_id as the current scan """
        for scan in self.scanListData:
            if(scan[SPDB_ID_VAL] == scan_id):
                self.scanProgress[scan_id] = progress
                self.cur_scan_id = scan_id
                #need to fire the signal so that the display role will get processed
                row = self._get_scan_rowidx(scan_id)
                index = QtCore.QModelIndex()
                self.dataChanged.emit(index, index)
                
                #_logger.info('current scan ID [%ld] has progress %f' % (scan_id, progress))
    
    def set_header(self, hdrList):
        """
        set_header(): description

        :param hdrList: hdrList description
        :type hdrList: hdrList type

        :returns: None
        """
        for hdr in hdrList:
            self.hdrList.append(hdr)
    
    def rowCount(self, parent=QtCore.QModelIndex()):
        """
        rowCount(): description

        :param parent=QtCore.QModelIndex(): parent=QtCore.QModelIndex() description
        :type parent=QtCore.QModelIndex(): parent=QtCore.QModelIndex() type

        :returns: None
        """
        return len(self.scanListData)

    def columnCount(self, parent=QtCore.QModelIndex()):
        """
        columnCount(): description

        :param parent=QtCore.QModelIndex(): parent=QtCore.QModelIndex() description
        :type parent=QtCore.QModelIndex(): parent=QtCore.QModelIndex() type

        :returns: None
        """
        return len(self.hdrList)
        #return(10)
    
    def headerData(self, section, orientation, role):
        """
        headerData(): description

        :param section: section description
        :type section: section type

        :param orientation: orientation description
        :type orientation: orientation type

        :param role: role description
        :type role: role type

        :returns: None
        """
        """ this gets auto called by the Qt model view framework for a role """
        try:
            if (role == QtCore.Qt.DisplayRole):
                if (orientation == QtCore.Qt.Horizontal):
                    return QtCore.QString(self.hdrList[section])
        except IndexError:
            s = "Index[%d] error in header list" % section
            raise ScanOptionError(s)
                    
        return QtCore.QVariant()

    def data(self, index, role):
        """
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
                v = scan[self.column_map[col]]
                        
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
    
    def modify_data(self, scan_id, scan):
        """
        modify_data(): description

        :param scan_id: scan_id description
        :type scan_id: scan_id type

        :param scan: scan description
        :type scan: scan type

        :returns: None
        """
        """ to be implemented by inheriting class """
        pass
    
    def setData(self, index, value, role, recalc=True):
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

        :returns: None
        """
        """ to be implemented by inheriting class """
        pass
    
    def flags(self, index):
        """
        flags(): description

        :param index: index description
        :type index: index type

        :returns: None
        """
        """ to be implemented by inheriting class """
        #print '%d, %d' % (index.row(), index.column())
        row = index.row()
        col = index.column()
        rowRdOnly = row in list(self.rd_only_rows.keys())
        colRdOnly = col in list(self.rd_only_cols.keys())
        if(rowRdOnly):
            return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsSelectable
        elif(colRdOnly):
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        else:
            return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable


def gen_spatial_model_obj(hdr_name, func, floor_val, ceiling_val):
    dct = {}
    dct['hdr'] = hdr_name
    dct['func'] = func
    dct['floor_val'] = floor_val
    dct['ceiling_val'] = ceiling_val
    return(dct)

#the C_ is for Center
C_SPATIAL_DCT = []
C_SPATIAL_DCT.append(gen_spatial_model_obj('ID',None,None,None))
C_SPATIAL_DCT.append(gen_spatial_model_obj('CENTERX', on_center_changed, None, None))
C_SPATIAL_DCT.append(gen_spatial_model_obj('RANGEX', on_range_changed, None, None))
C_SPATIAL_DCT.append(gen_spatial_model_obj('CENTERY', on_center_changed, None, None))
C_SPATIAL_DCT.append(gen_spatial_model_obj('RANGEY', on_range_changed, None, None))
C_SPATIAL_DCT.append(gen_spatial_model_obj('STEPX', on_step_size_changed, None, None))
C_SPATIAL_DCT.append(gen_spatial_model_obj('STEPY', on_step_size_changed, None, None))
C_SPATIAL_DCT.append(gen_spatial_model_obj('NPOINTSX', on_npoints_changed, 0, 20000))
C_SPATIAL_DCT.append(gen_spatial_model_obj('NPOINTSY', on_npoints_changed, 0, 20000))


#the S_ is for Start
S_SPATIAL_DCT = []
S_SPATIAL_DCT.append(gen_spatial_model_obj('ID',None,None,None))
S_SPATIAL_DCT.append(gen_spatial_model_obj('STARTX',on_start_changed, None, None))
S_SPATIAL_DCT.append(gen_spatial_model_obj('STOPX',on_stop_changed, None, None))
S_SPATIAL_DCT.append(gen_spatial_model_obj('STARTY',on_start_changed, None, None))
S_SPATIAL_DCT.append(gen_spatial_model_obj('STOPY',on_stop_changed, None, None))
S_SPATIAL_DCT.append(gen_spatial_model_obj('STEPX', on_step_size_changed, None, None))
S_SPATIAL_DCT.append(gen_spatial_model_obj('STEPY', on_step_size_changed, None, None))
S_SPATIAL_DCT.append(gen_spatial_model_obj('NPOINTSX', on_npoints_changed, 0, 20000))
S_SPATIAL_DCT.append(gen_spatial_model_obj('NPOINTSY', on_npoints_changed, 0, 20000))


def get_val_from_roi(sp_db, field, roi_key):
    if(roi_key in list(sp_db.keys())):
        roi = sp_db[roi_key]
    else:
        return(None)
        
    if(field in list(roi.keys())):
        return(roi[field])
    else:
        return(None)    

def get_val_from_sp_db(field, sp_db):
    axis_key = field[-1]
    subfld = field[0:-1]
    
    return(get_val_from_roi(sp_db, subfld, axis_key))


def set_val_in_roi(sp_db, field, roi_key, val):
    if(roi_key in list(sp_db.keys())):
        roi = sp_db[roi_key]
    else:
        return(None)
        
    if(field in list(roi.keys())):
        roi[field] = val
    else:
        _logger.error('field [%s] doesnt exist in sp_db' % field)    

def set_field_val_in_sp_db(field, val, sp_db):
    axis_key = field[-1]
    subfld = field[0:-1]
    set_val_in_roi(sp_db, subfld, axis_key, val)
    

def get_roi_from_sp_db(field, sp_db):
    axis_key = field[-1]
    if(axis_key in list(sp_db.keys())):
        return(sp_db[axis_key])
    else:
        _logger.error('axis_key [%s] doesnt exist in sp_db' % axis_key)


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
                val  = float(value)
            
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

#     def recalc_params(self, row=None):
        """
        recalc_params(): description

        :param row=None: row=None description
        :type row=None: row=None type

        :returns: None
        """
#         if(row is None):
#             row = self.model().rowCount(QtCore.QModelIndex())
#         
#         idx = row
#         for scan in self.scanListData[idx:]:
#             if(idx == 0):
#                 pass
#             else:
#                 #make sure that the start of this scan is equal to the stop of the previous
#                 scan[START] = self.scanListData[idx-1][STOP] + EV_SCAN_EDGE_RANGE
#                 scan['on_start_changed'](scan)
#             idx += 1
            


class ArbitraryLineScanTableModel(BaseScanTableModel):
    
    def __init__(self, hdrList, datain, parent = None, use_center=False, *args):
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
        super(ArbitraryLineScanTableModel, self).__init__( hdrList, datain, parent, *args)
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
                val  = float(value)
            
            #call the associated setter function for this column (this is setup in the scan definition class
            if(ok):
                #only change the value if the user entered a value
                scan = self.scanListData[row]
                roi = get_roi_from_sp_db(self.column_map[col]['hdr'], scan)
                set_field_val_in_sp_db(self.column_map[col]['hdr'], val, scan)
                func = self.column_map[col]['func']
                                
                if(self.column_map[col]['hdr'] == 'NPOINTSX'):
                    func = self.column_map[col]['func']
                    #now call the resepctive function to recalc the scan params
                    func(roi)
                    # set the NPOINTSY field to be same number of points
                    roi = get_roi_from_sp_db(self.column_map[col+1]['hdr'], scan)
                    set_field_val_in_sp_db(self.column_map[col+1]['hdr'], val, scan)
                    func = self.column_map[col+1]['func']
                    #now call the resepctive function to recalc the scan params
                    func(roi)
                    
                if(self.column_map[col]['hdr'] == 'STEPX'):
                    func = self.column_map[col]['func']
                    #now call the resepctive function to recalc the scan params
                    func(roi)
                    # set the STEPY field to be same step size
                    roi = get_roi_from_sp_db(self.column_map[col+1]['hdr'], scan)
                    set_field_val_in_sp_db(self.column_map[col+1]['hdr'], val, scan)
                    func = self.column_map[col+1]['func']
                    #now call the resepctive function to recalc the scan params
                    func(roi)
                        
                
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


            
#need a mapping of table columns to roi dict key
EV_COLUMN_MAP = ['ID', 'START', 'STOP', 'RANGE', 'NPOINTS', 'STEP', 'DWELL']
#include columns of EV_COLUMN_MAP that require a start recalculation
EV_START_CHANGED = [1]
EV_STOP_CHANGED = [2]
#include columns of EV_COLUMN_MAP that require a range recalculation
EV_RANGE_CHANGED = [3]
#include columns of EV_COLUMN_MAP that require a npoints recalculation
EV_NPOINTS_CHANGED = [4]
#include columns of EV_COLUMN_MAP that require a step size recalculation
EV_STEP_CHANGED = [5]

class EnergyScanTableModel(BaseScanTableModel):
    
    def __init__(self, hdrList, datain, parent = None, *args):
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
        super(EnergyScanTableModel, self).__init__( hdrList, datain, parent, *args)
        # a dict that will use spatial region scan_id's as key to EnergyRegionScanDef's 
        self.cur_scan_row = None
        self.scanListData = datain
        self.editable = False
        self.column_map = EV_COLUMN_MAP
        self.set_min_rows(1)
        self.set_max_rows(20)
    
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
                val  = float(value)
            #call the associated setter function for this column (this is setup in the scan definition class
            if(ok):
                #only change the value if the user entered a value
                scan = self.scanListData[row]
                scan_id = scan[SPDB_ID_VAL]
                #print 'setData[scan_id=%d] col=%d val= %f' % (scan_id, col, val)
                scan[EV_COLUMN_MAP[col]] = val
            
                #force the row to recalc
                if(recalc):
                    #now call the resepctive function to recalc the scan params
                    if(col in EV_START_CHANGED):
                        on_start_changed(scan)
                    
                    if(col in EV_STOP_CHANGED):
                        on_stop_changed(scan)
                    
                    if(col in EV_RANGE_CHANGED):
                        on_range_changed(scan)
                    
                    if(col in EV_NPOINTS_CHANGED):
                        on_npoints_changed(scan)
                        
                    if(col in EV_STEP_CHANGED):
                        on_step_size_changed(scan)
                        
                    #finally make sure all scans obey ascending eV rule
                    self.recalc_params(row+1)
                    
        if((role == QtCore.Qt.EditRole) or (role == QtCore.Qt.DisplayRole)):
            #must emit this as part of the framework support for an editable AbstractTableModel
            scan = self.scanListData[row]
            self.dataChanged.emit(index, index)
            
            if(do_signal):
                print('EnergyScanTableModel: setData: emitting scan_changed')
                self.scan_changed.emit(row, scan)
                
            return True
    

    def recalc_params(self, row=None):
        """
        recalc_params(): description

        :param row=None: row=None description
        :type row=None: row=None type

        :returns: None
        """
        if(row is None):
            row = self.model().rowCount(QtCore.QModelIndex())
        
        idx = row
        for scan in self.scanListData[idx:]:
            if(idx == 0):
                pass
            else:
                #make sure that the start of this scan is equal to the stop of the previous
                scan[START] = self.scanListData[idx-1][STOP] + EV_SCAN_EDGE_RANGE
                on_start_changed(scan)
            idx += 1
    
POLARITY_COLUMN_MAP = ['ID','POL', 'OFF', 'ANGLE']
POLARITY_POLARITY_CHANGED = [1]
POLARITY_OFFSET_CHANGED = [2]
POLARITY_LINEAR_ANGLE_CHANGED = [3]

class PolarityTableModel(BaseScanTableModel):
    
    def __init__(self, hdrList, datain, parent = None, *args):
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
        super(PolarityTableModel, self).__init__( hdrList, datain, parent, *args)
        # a dict that will use spatial region scan_id's as key to EnergyRegionScanDef's 
        self.cur_scan_row = None
        self.scanListData = datain
        self.editable = False
        self.column_map = POLARITY_COLUMN_MAP
        self.set_min_rows(0)
        self.set_max_rows(20)
        
        
    def setData(self, index, value, role, do_signal=True):
        """
        setData(): description

        :param index: index description
        :type index: index type

        :param value: value description
        :type value: value type

        :param role: role description
        :type role: role type

        :param do_signal=True: do_signal=True description
        :type do_signal=True: do_signal=True type

        :returns: None
        """
        row = index.row()
        col = index.column()
        ok = True
        print('Polarity model: role = %d' % role)
        if(role == QtCore.Qt.EditRole):
            
            if(col == 0):
                return True
                #val, ok  = value.toLongLong()
            elif(col == 1):
                #val  = str(value.toString())
                #if(len(val) < 1):
                #    ok = False
                val = value
            else:
                val  = float(value)
            
            
            #call the associated setter function for this column (this is setup in the scan definition class
            if(ok):
                #only change the value if the user entered a value
                scan = self.scanListData[row]
                scan_id = scan[SPDB_ID_VAL]
                #print 'setData[scan_id=%d] col=%d val= %f' % (scan_id, col, val)
                #if(POLARIZATION_COLUMN_MAP[col] == 'POL'):
                #    #convert polarity combobox val to stxm wrapper values
                #    val = val - 1
                    
                scan[POLARITY_COLUMN_MAP[col]] = val
            
        if((role == QtCore.Qt.EditRole) or (role == QtCore.Qt.DisplayRole)):
            #must emit this as part of the framework support for an editable AbstractTableModel
            scan = self.scanListData[row]
            self.dataChanged.emit(index, index)
            
            if(do_signal):
                #print 'EnergyScanTableModel: setData: emitting scan_changed'
                self.scan_changed.emit(row, scan)
                
            return True
    
class BaseScanTableView(QtWidgets.QTableView):
    """
    This is a widget to display the parameters of individual scans, the widget responds to cell edits
    and forces a recalc of row elements if need be.
    """
    row_selected = QtCore.pyqtSignal(object) # row data
    add_region = QtCore.pyqtSignal()
    del_region = QtCore.pyqtSignal()
    scan_changed = QtCore.pyqtSignal(int, object)
    
    def __init__(self, hdrList, scanList, tablemodel_class, parent=None):
        """
        __init__(): description

        :param hdrList: hdrList description
        :type hdrList: hdrList type

        :param scanList: scanList description
        :type scanList: scanList type

        :param tablemodel_class: tablemodel_class description
        :type tablemodel_class: tablemodel_class type

        :param parent=None: parent=None description
        :type parent=None: parent=None type

        :returns: None
        """
        super(BaseScanTableView, self).__init__(parent)
        self.hdrList = hdrList
        self.scans = scanList
        self.tablemodel = None
        self.models = {}
        self.model_id_start_val = None
        self.model_id = 0
        self.signals_connected = False
        
        self.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        self.verticalHeader().setDefaultSectionSize(20)
        
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setAlternatingRowColors(True)
        
        fnt = QtGui.QFont()
        fnt.setPointSize(TABLE_FONT_SIZE)
        self.setFont(fnt)
        
        self.verticalHeader().setDefaultSectionSize(15)
        
        self._cur_selected_scan = None
        self.tablemodel_class = tablemodel_class
        
        #self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectItems)
        #self.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        #self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        #self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
        #self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.stretchLastSection)
        self.scanFlags = {}
        self._block_updates = False
        #self.clicked.connect(self.on_clicked)
        #self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        #self.selectionModel().selectionChanged.connect(self.selChanged)
        self.clicked.connect(self.on_clicked)
        
    def contextMenuEvent(self, event):
        """
        contextMenuEvent(): description

        :param event: event description
        :type event: event type

        :returns: None
        """
        menu = QtWidgets.QMenu(self)
        addAction = menu.addAction("Add region")
        delAction = menu.addAction("Delete region")
        dmpModelAction = menu.addAction("Dump Selected Model")
        action = menu.exec_(self.mapToGlobal(event.pos()))
        if action == addAction:
            self.add_region.emit()
        elif action == delAction:
            self.del_region.emit()
        elif action == dmpModelAction:
            self.dump_model_keys()    
        
    def connect_signals(self):
        """
        connect_signals(): description

        :returns: None
        """
        self.setModel(self.tablemodel)
        self.selectionModel().selectionChanged.connect(self.selChanged)
        self.tablemodel.dataChanged.connect(self.on_cell_changed)
        self.tablemodel.scan_changed.connect(self.on_model_changed)
        #self._numHdrCols = self.tablemodel.columnCount(self)
        #self.clicked.connect(self.on_clicked)    
        self.signals_connected = True
    
    def disconnect_signals(self):
        """
        disconnect_signals(): description

        :returns: None
        """
        try:
            self.selectionModel().selectionChanged.disconnect(self.selChanged)
            self.tablemodel.dataChanged.disconnect(self.on_cell_changed)
            self.tablemodel.scan_changed.disconnect(self.on_model_changed)
            #self.clicked.disconnect(self.on_clicked)
            self.signals_connected = False
        except:
            pass
    
    def init_model(self):
        """
        init_model(): description

        :returns: None
        """
        """ to be implemented by inheriting class """
        pass
    
    def set_model_editable(self, ed):
        """
        set_model_editable(): description

        :param ed: ed description
        :type ed: ed type

        :returns: None
        """
        if(self.tablemodel is not None):
            self.tablemodel.set_editable(ed)
    
    def on_clicked(self, index):
        """
        on_clicked(): description

        :param index: index description
        :type index: index type

        :returns: None
        """
        row = index.row()
        scan = self.get_row_data(row)
        #self.row_selected.emit(scan)
        self._cur_selected_scan = scan
    
    def set_model_id_start_val(self, val):
        """
        set_model_id_start_val(): description

        :param val: val description
        :type val: val type

        :returns: None
        """
        """
        This is the value that this model will START couting from
        for the roi id's
        """
        self.model_id_start_val = val
        self.model_id = val
    
    def get_model_id_start_val(self):
        """
        get_model_id_start_val(): description

        :returns: None
        """
        """
        This is the value that this model will START couting from
        for the roi id's
        """
        return(self.model_id_start_val)
    
    def dump_model_keys(self):
        """
        dump_model_keys(): description

        :returns: None
        """
        model = self.tablemodel.get_scan_list()
        #print self.tablemodel_class
        for m in model:
            print('Model ID = %d' % self.model_id)
            print('\t [%d]' % m[SPDB_ID_VAL])
        
    def set_scan_list(self, scanList):
        """
        set_scan_list(): description

        :param scanList: scanList description
        :type scanList: scanList type

        :returns: None
        """
        self.tablemodel.set_scan_list(scanList)
    
    def get_scan_list(self, model_id=None):
        """
        get_scan_list(): description

        :param model_id=None: model_id=None description
        :type model_id=None: model_id=None type

        :returns: None
        """
        if(model_id is not None):
            if(model_id in list(self.models.keys())):
                return(self.models[model_id].get_scan_list())
            else:
                print('Model[%d] does not exist' % model_id)
                return[]
        else:        
            return(self.tablemodel.get_scan_list())
    
    def get_num_scans(self):
        """
        get_num_scans(): description

        :returns: None
        """
        scans = self.get_scan_list()
        return(len(scans))
                
    def get_scan(self, scan_id):
        """
        get_scan(): description

        :param scan_id: scan_id description
        :type scan_id: scan_id type

        :returns: None
        """
        return(self.tablemodel.get_scan(scan_id))
    
    def get_model(self, model_id):
        """
        get_model(): description

        :param model_id: model_id description
        :type model_id: model_id type

        :returns: None
        """
        if(model_id in list(self.models.keys())):
            return(self.models[model_id])
    
    def remove_model(self, model_id):
        """
        remove_model(): description

        :param model_id: model_id description
        :type model_id: model_id type

        :returns: None
        """
        if(model_id in list(self.models.keys())):
            self.models[model_id].removeAll()
            del self.models[model_id]
    
    def remove_all_models(self):
        """
        remove_all_models(): description

        :returns: None
        """
        for model_id in list(self.models.keys()):
            self.remove_model(model_id)
            
            
    def get_cur_selected_scan(self):
        """
        get_cur_selected_scan(): description

        :returns: None
        """
        return(self._cur_selected_scan)
    
    def set_getset_funcs(self, funclist):
        """
        set_getset_funcs(): description

        :param funclist: funclist description
        :type funclist: funclist type

        :returns: None
        """
        self.tablemodel.set_getset_funcs(funclist)
    
    def selChanged(self, selected, deselected):
        """
        selChanged(): description

        :param selected: selected description
        :type selected: selected type

        :param deselected: deselected description
        :type deselected: deselected type

        :returns: None
        """
        idxs = selected.indexes()
        if(len(idxs) > 0):
            idx = idxs.pop()
            row = idx.row()
            scan = self.get_row_data(row)
            self.row_selected.emit(scan)
            self._cur_selected_scan = scan
        else:
            self._cur_selected_scan = None
        
    def modify_scan(self, scan_id, newscan):
        """
        modify_scan(): description

        :param scan_id: scan_id description
        :type scan_id: scan_id type

        :param newscan: newscan description
        :type newscan: newscan type

        :returns: None
        """
        """ to be implemented by inheriting class """
        pass
        
    def remove_scan(self, scan_id):
        """
        remove_scan(): description

        :param scan_id: scan_id description
        :type scan_id: scan_id type

        :returns: None
        """
        row = self.tablemodel.get_scan_rowidx(scan_id)
        if(row is not None):
            self.tablemodel.removeRow(row)
    
    def remove_all(self):
        """
        remove_all(): description

        :returns: None
        """
        self.tablemodel.removeAll()
        
    def connect_progress_slot(self, _signal):
        """
        connect_progress_slot(): description

        :param _signal: _signal description
        :type _signal: _signal type

        :returns: None
        """
        _signal.connect(self.select_row)
    
    #def select_row(self, scan_id=None, progress=0.0):
    def select_row(self, row_idx=None, progress=0.0):
        """
        select_row(): description

        :param scan_id=None: scan_id=None description
        :type scan_id=None: scan_id=None type

        :param progress=0.0: progress=0.0 description
        :type progress=0.0: progress=0.0 type

        :returns: None
        """
        if(row_idx is None):
            row_idx = 0
        self.selectRow(row_idx)

    def disable_updates(self):
        """
        disable_updates(): description

        :returns: None
        """
        self._block_updates = True
    
    def enable_updates(self):
        """
        enable_updates(): description

        :returns: None
        """
        self._block_updates = False
    
    def get_num_rows(self):
        """
        get_num_rows(): description

        :returns: None
        """
        return(self.tablemodel.rowCount(None))
    
    def get_row_data(self, row):
        """
        get_row_data(): description

        :param row: row description
        :type row: row type

        :returns: None
        """
        scan = self.tablemodel.get_scan_by_row(row)
        return(scan)
    
    def on_cell_changed(self, idx, idx2):
        """
        on_cell_changed(): description

        :param idx: idx description
        :type idx: idx type

        :param idx2: idx2 description
        :type idx2: idx2 type

        :returns: None
        """
        val, ok = idx.data().toFloat()

    def create_new_model(self, scans=None, model_id=None, use_center=True):
        """
        create_new_model(): description

        :param scans=None: scans=None description
        :type scans=None: scans=None type

        :returns: None
        """
        """ create a new TableModel and add it to the dict of 
        table models that is indexed by the model_id passed in from the parent tableView on_new_region()
        slot
        """
        #connect the models signal to emit the views scan_changed signal
        self.disconnect_signals()
        if(scans is None):
            scanlist = []
        else:
            scanlist = scans
            
        if(model_id is None):    
            #increment model id
            while self.model_id in list(self.models.keys()):
                #self.model_id += 1
                self.model_id = get_unique_roi_id()
        else:
            self.model_id = model_id        
        
        tablemodel = self.tablemodel_class(self.hdrList, [], self)
        self.models[self.model_id] = tablemodel
        for scan in scanlist:
            self.add_scan(scan)
            
        # set the new model to be the current model
        self.switch_models(self.model_id)
        self.set_model_column_defaults()
        self.connect_signals()
        return(self.model_id)
    
    def switch_models(self, model_id):
        """
        switch_models(): description

        :param model_id: model_id description
        :type model_id: model_id type

        :returns: None
        """
        """ set the current model to be the one owned by scan_id """
        #print 'switch_models: model_id [%d]' % model_id
        if(model_id in list(self.models.keys())):
            self.tablemodel= self.models[model_id]
            self.model_id = model_id
            self.setModel(self.tablemodel)
            self.disconnect_signals()
            self.connect_signals()
            return(True)
        return(False)
    
    def on_model_changed(self, row, scan):
        """
        on_model_changed(): description

        :param row: row description
        :type row: row type

        :param scan: scan description
        :type scan: scan type

        :returns: None
        """
        #print 'on_model_changed: emitting scan_changed'
        self.scan_changed.emit(row, scan)
    
    def add_scan(self, scan, scan_id):
        """
        add_scan(): description

        :param scan: scan description
        :type scan: scan type

        :param scan_id: scan_id description
        :type scan_id: scan_id type

        :returns: None
        """
        """ add a scan to the current model that is owned by scan_id"""
        success = False
        #make sure that the scan_id is an integer if it is still a string
        scan[SPDB_ID_VAL] = int(scan_id)
        success = self.tablemodel.add_scan(scan)
        self._cur_selected_scan = scan
        self.set_model_column_defaults()
        success = True
        return(success)
    
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
        for i in range(1,len(self.hdrList)):
                self.horizontalHeader().setSectionResizeMode(i, QtWidgets.QHeaderView.Stretch)
    
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
        
        for i in range(1,len(self.hdrList)):
                self.horizontalHeader().setSectionResizeMode(i, QtWidgets.QHeaderView.Stretch)
    
    
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
        
        for i in range(1,len(self.hdrList)):
                self.horizontalHeader().setSectionResizeMode(i, QtWidgets.QHeaderView.Stretch)
    
        
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
    
class EnergyScanTableView(BaseScanTableView):
    
    def __init__(self, scanList=[], parent=None):
        """
        __init__(): description

        :param scanList=[]: scanList=[] description
        :type scanList=[]: scanList=[] type

        :param parent=None: parent=None description
        :type parent=None: parent=None type

        :returns: None
        """
        #setup the header for the top of the table
        hdrList = ['ID','Start', 'End', 'Range\n(eV)', '#Points', 'Step\n(eV)', 'Dwell\n(ms)']
        #self.func_list = ['ev_id', 'center', 'range', 'step','Npoints', 'dwell', 'pol1', 'pol2', 'off1', 'off2', 'xmcd']
        super(EnergyScanTableView, self).__init__(hdrList, scanList, EnergyScanTableModel, parent)
        self.setStyleSheet(EV_SS)
        self.evNum = 0

        #self.init_model()
        #self.set_model_id_start_val(EV_CNTR)
        
    
    def init_model(self):
        """
        init_model(): description

        :returns: None
        """
        self.tablemodel = EnergyScanTableModel(self.hdrList, self.scans, self)
        self.set_model_column_defaults()
        
    def set_model_column_defaults(self):
        """
        set_model_column_defaults(): description

        :returns: None
        """
        self.tablemodel.set_col_readonly(0)
        for i in range(1,len(self.hdrList)):
                self.horizontalHeader().setSectionResizeMode(i, QtWidgets.QHeaderView.Stretch)
        
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

    
POLARITY_COLUMN = 1

class PolComboBoxDelegate(QtWidgets.QItemDelegate):
    """
    A delegate that places a fully functioning QComboBox in every
    cell of the column to which it's applied
    """
    def __init__(self, parent):
        """
        __init__(): description

        :param parent: parent description
        :type parent: parent type

        :returns: None
        """

        QtWidgets.QItemDelegate.__init__(self, parent)
        
    def createEditor(self, parent, option, index):
        """
        createEditor(): description

        :param parent: parent description
        :type parent: parent type

        :param option: option description
        :type option: option type

        :param index: index description
        :type index: index type

        :returns: None
        """
        cbox = QtWidgets.QComboBox(parent)
        cbox.addItems(['CircLeft','CircRight','LinHor', 'IncVert-', 'IncVert+','LinInc'])
        #items = ['CircLeft','CircRight','LinHor', 'IncVert-', 'IncVert+','LinInc']
        #idx = -1
        #for item in items:
        #    cbox.addItem(item, idx)
        #    idx = idx -1
        #chkd = index.model().get_scans()[index.row()][POLARIZATION_COLUMN]
        #chkbx.setChecked(chkd)
        #self.connect(cbox, QtCore.SIGNAL("currentIndexChanged(Int)"), self, QtCore.SLOT("on_pol_changed()"))
        cbox.currentIndexChanged.connect(self.on_pol_changed)
        return cbox
        
    def setEditorData(self, editor, index):
        """
        setEditorData(): description

        :param editor: editor description
        :type editor: editor type

        :param index: index description
        :type index: index type

        :returns: None
        """
        #print 'setEditorData'
        editor.blockSignals(True)
        #editor.setCurrentIndex(int(index.model().data(index)))
        if(index.column() == POLARITY_COLUMN):
        #    editor.setChecked(index.model().data(index))
            (idx, success) = index.data().toInt() 
            editor.setCurrentIndex(idx)
        editor.blockSignals(False)
        
    def setModelData(self, editor, model, index):
        """
        setModelData(): description

        :param editor: editor description
        :type editor: editor type

        :param model: model description
        :type model: model type

        :param index: index description
        :type index: index type

        :returns: None
        """
        #user_data_val, ok = editor.itemData(editor.currentIndex()).toInt()
        #model.setData(index, user_data_val, QtCore.Qt.EditRole)
        model.setData(index, editor.currentIndex(), QtCore.Qt.EditRole)

        
    @QtCore.pyqtSlot()
    def on_pol_changed(self):
        """
        on_pol_changed(): description

        :returns: None
        """
        print('on_pol_changed [%d]' % (self.sender().currentIndex()))
        self.commitData.emit(self.sender())

class PolarityTableView(BaseScanTableView):
    
    #changed = QtCore.pyqtSignal()
    
    def __init__(self, scanList=[], parent=None):
        """
        __init__(): description

        :param scanList=[]: scanList=[] description
        :type scanList=[]: scanList=[] type

        :param parent=None: parent=None description
        :type parent=None: parent=None type

        :returns: None
        """
        #setup the header for the top of the table
        hdrList = ['ID','Polarity', 'Offset', 'Linear Angle']
        #self.func_list = ['pol_id', 'polarity', 'offset','linearAngle']
        
        super(PolarityTableView, self).__init__(hdrList, scanList, PolarityTableModel, parent)
        self.setStyleSheet(POL_SS)
        self.xyNum = 0
        #self.set_model_id_start_val(POL_CNTR)
        self.setItemDelegateForColumn(POLARITY_COLUMN, PolComboBoxDelegate(self))
        
        #turn bold off
        font = self.horizontalHeader().font()
        font.setBold(False)
        font.setPointSize(8)
        self.horizontalHeader().setFont(font)
        #self.init_model()
    
    def init_model(self):
        """
        init_model(): description

        :returns: None
        """
        self.tablemodel = PolarityTableModel(self.hdrList, self.scans, self)
        self.set_model_column_defaults()
        
    
    def get_polarity_combobox(self):
        """
        get_polarity_combobox(): description

        :returns: None
        """
        cbox = QtWidgets.QComboBox()
        # the values that need to be pushed out for these are (in order) 
        #             [-1, 0, 1]
        cbox.addItems(['Circ Left','Circ Right','Linear'])
        return(cbox)
    
        
    def set_model_column_defaults(self):
        """
        set_model_column_defaults(): description

        :returns: None
        """
        self.tablemodel.set_col_readonly(0)
        for i in range(1,len(self.hdrList)):
                self.horizontalHeader().setSectionResizeMode(i, QtWidgets.QHeaderView.Stretch)
        
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

    def update_table(self):
        """
        update_table(): description

        :returns: None
        """
        if(self.tablemodel is not None):
            for row in range(0, self.tablemodel.rowCount()):
                #table_view.openPersistentEditor(table_model.index(row, 0))
                self.openPersistentEditor(self.tablemodel.index(row, POLARITY_COLUMN))
    
    def add_scan(self, scan, scan_id):
        """
        add_scan(): description

        :param scan: scan description
        :type scan: scan type

        :param scan_id: scan_id description
        :type scan_id: scan_id type

        :returns: None
        """
        """ add a scan to the current model that is owned by scan_id"""
        success = False
        if(self.switch_models(self.model_id)):
            #scan[SPDB_ID_VAL] = self.model_id_start_val + self.get_num_scans()
            scan[SPDB_ID_VAL] = scan_id
            success = self.tablemodel.add_scan(scan)
            self._cur_selected_scan = scan
            self.select_row(scan[SPDB_ID_VAL])
            self.set_model_column_defaults()
            success = True
        
        self.update_table()
            
        return(success)

class BaseSelectionWidget(QtWidgets.QWidget):
    model_change = QtCore.pyqtSignal(object)
    changed = QtCore.pyqtSignal()
    
    def __init__(self):
        """
        __init__(): description

        :param ev_sel_widget=None: ev_sel_widget=None description
        :type ev_sel_widget=None: ev_sel_widget=None type

        :returns: None
        """
        QtWidgets.QWidget.__init__(self)
        self.add_region_enabled = False
        
    
class SpatialSelWidget(BaseSelectionWidget):
    """
    A QWidget that contains an SpatialScanTableView, can be configured to connect to ev_sel_widget
    """
    roi_deleted = QtCore.pyqtSignal(object)
    spatial_row_changed = QtCore.pyqtSignal(object)
    
    def __init__(self, ev_sel_widget=None, use_center=True, is_point=False, is_arb_line=False):
        """
        __init__(): description

        :param ev_sel_widget=None: ev_sel_widget=None description
        :type ev_sel_widget=None: ev_sel_widget=None type

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
        
        self.table_view = SpatialScanTableView(use_center=use_center, is_point=is_point, is_arb_line=is_arb_line)
        self.scan_id = 0 #self.table_view.get_model_id_start_val()
        self.table_view.create_new_model(use_center=use_center)
        
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
            - find the model_id of the EV model that the model we are deleting is connected to (['EV_ID'])
            - call the self.ev_sel_widget 'delete_model' with the EV model_id, (['EV_ID'])
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
            
        self.ev_sel_widget.delete_model(scan['EV_ID'])
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
        else:
            self.ev_sel_widget.enable_add_region(True)    
    
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
        #print 'SPATIAL model_ID %d selected EV_ID=%d' % (scan[SPDB_ID_VAL], scan['EV_ID'])
        self.ev_sel_widget.switch_view_model(scan['EV_ID'])
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
        
        #make sure that the Ev and pol widgets know they are allowed now to add a region
        self.ev_sel_widget.enable_add_region_menu(True)
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
            self.scan_id += 1
        else:
            self.scan_id = scan[SPDB_ID_VAL]
            #dct_put(scan, SPDB_SCAN_PLUGIN_ITEM_ID, self.scan_id)
        
        if((add_energy_roi) and (self.ev_sel_widget is not None)):    
            #create a new ev roi model with the scan[SPDB_ID_VAL] as its key
            scan['EV_ID'] = self.ev_sel_widget.table_view.create_new_model()
            self.ev_sel_widget.on_new_region()
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
        #scan['EV_ID'] = loaded_scan['EV_ID']
        #scan[SPDB_EV_ROIS] = loaded_scan[SPDB_EV_ROIS]
        
        self.scan_id = loaded_scan[SPDB_ID_VAL]    
        #create a new ev roi model with the scan['EV_ID'] as its key
        self.ev_sel_widget.table_view.create_new_model(model_id = loaded_scan['EV_ID'])
        #make sure that the Ev and pol widgets know they are allowed now to add a region
        self.ev_sel_widget.enable_add_region(True)
        
        self.ev_sel_widget.load_scan(loaded_scan[SPDB_EV_ROIS])
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
        
        #create a new ev roi model with the scan['EV_ID'] as its key
        self.ev_sel_widget.table_view.create_new_model(model_id = loaded_scan['EV_ID'])
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

class EnergySelWidget(BaseSelectionWidget):
    """
    A QWidget that contains an EnergyScanTableView
    """
    
    def __init__(self, pol_sel_widget=None):
        """
        __init__(): description

        :param pol_sel_widget=None: pol_sel_widget=None description
        :type pol_sel_widget=None: pol_sel_widget=None type

        :returns: None
        """
        BaseSelectionWidget.__init__(self)
        # setGeometry(x_pos, y_pos, width, height)
        self.setGeometry(300, 200, 870, 450)
        self.setWindowTitle("Click on column title to sort")
        self.editable = False
        self.pol_sel_widget = pol_sel_widget
        #self.pol_sel_widget.changed.connect(self.on_pol_table_changed)
        
        self.table_view = EnergyScanTableView()
        self.table_view.scan_changed.connect(self.changed)
        self.scan_id = 0 #self.table_view.get_model_id_start_val()
        
        self.table_view.create_new_model()
        self.table_view.set_model_column_defaults()
        # set font
        # set column width to fit contents (set font first!)
        self.table_view.resizeColumnsToContents()
        # enable sorting
        self.table_view.setSortingEnabled(False)
        
        self.scanorderComboBox = QtWidgets.QComboBox()
        self.scanorderComboBox.addItem('1. For each Energy step scan all Polarities')
        self.scanorderComboBox.addItem('2. For each Polarity step scan all Energies')
        lbl = QtWidgets.QLabel('Ev/Polarity Sequencing for scan')
        f = lbl.font()
        f.setBold(True)
        lbl.setFont(f)
        h_layout = QtWidgets.QHBoxLayout()
        h_layout.addWidget(lbl)
        h_layout.addWidget(self.scanorderComboBox)
        hspacer = QtWidgets.QSpacerItem(40,20,QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Minimum)
        h_layout.addItem(hspacer)
        
        #disconnect for now
        #self.scanorderComboBox.currentIndexChanged.connect(self.scan_order_changed)
        self.ev_polarity_scan_order = energy_scan_order_types.EV_THEN_POL
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.addLayout(h_layout)
        layout.addWidget(self.table_view)
        self.setLayout(layout)
        self.clearFocus()
        
        self.table_view.remove_all_models()
        
        self.table_view.add_region.connect(self.on_new_region)
        self.table_view.del_region.connect(self.delete_row)
        self.table_view.row_selected.connect(self.on_row_selected)
    
    def enable_add_region(self, do=True):
        self.enable_add_region_menu(do)
        self.pol_sel_widget.enable_add_region_menu(do)
    
    def enable_add_region_menu(self, do=True):
        self.add_region_enabled = do
            
    def on_pol_table_changed(self):
        '''EnergySelWidget'''
        #scan = self.get_row_data_by_item_id(self.scan_id)
        #_logger.debug('EnergySelWidget: on_pol_table_changed, emitting changed sig')
        self.changed.emit()
    
    def get_row_data_by_item_id(self, item_id):
        return(self.table_view.get_scan(item_id))
    
    def scan_order_changed(self, idx):
        if(idx == 0):
            #1. For each Energy step scan all Polarities'
            self.ev_polarity_scan_order = energy_scan_order_types.EV_THEN_POL
        else:
            #2. For each Polarity step scan all Energies
            self.ev_polarity_scan_order = energy_scan_order_types.POL_THEN_EV
    
    def get_ev_polarity_scan_order(self):
        return(self.ev_polarity_scan_order)
    
    def select_row(self, row_idx):
        self.table_view.select_row(row_idx)
    
    def get_row_data(self, item_id):
        return(self.table_view.get_scan(item_id))
        
    def delete_row(self, scan_id=None):
        """
        delete_row(): description

        :param scan_id=None: scan_id=None description
        :type scan_id=None: scan_id=None type

        :returns: None
        """
        """
        This function os called by the right click menu action for deleting a row.
        """
        if(scan_id is None):
            scan = self.table_view.get_cur_selected_scan()
            scan_id = scan[SPDB_ID_VAL]
        self.on_delete_region(scan_id)
    
    def delete_model(self, ev_model_id=None):
        """
        delete_model(): description

        :param ev_model_id=None: ev_model_id=None description
        :type ev_model_id=None: ev_model_id=None type

        :returns: None
        """
        """
        This function is called by the Spatial widget delete_model().
        
        this function takes the model_id of the desired ev model_id
        that needs to be deleted. For ev models the sequence for deletion is as folows:
            - get the POL model_id used by the parent EV scan, (['POL_ID']
            - get the list of POL scans in the model
            - for every scan in the model returned from 
            - call the self.ev_sel_widget 'delete_model' with the POL model_id, (['POL_ID'])
            - call 'remove_model(model_id)'
        """
        if(ev_model_id is None):
            scan = self.table_view.get_cur_selected_scan()
            ev_model_id = scan[SPDB_ID_VAL]
            
        ev_scans = self.table_view.get_scan_list(ev_model_id)
        #for scan in ev_scans:
        #    self.pol_sel_widget.delete_model(scan['POL_ID'])
        for scan in ev_scans:
            self.on_delete_region(scan[SPDB_ID_VAL])
        self.table_view.remove_model(ev_model_id)
        
    def get_data(self, model_id=None):
        """
        get_data(): description

        :param model_id=None: model_id=None description
        :type model_id=None: model_id=None type

        :returns: None
        """
        ev_rois = self.table_view.get_scan_list(model_id) 
        self.update_ev_pol_scan_order(ev_rois) 
        return(ev_rois)
    
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
        #print '\t\tEV model_ID %d selected: POL_ID == [%d]' % (scan[SPDB_ID_VAL], scan['POL_ID'])
        #_logger.debug('EnergySelWidget: on_row_selected, emitting model_change')
        self.model_change.emit(scan[SPDB_ID_VAL])
        self.pol_sel_widget.switch_view_model(scan['POL_ID'])
        self.pol_sel_widget.table_view.select_row()
        self.pol_sel_widget.update_table()
        
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
        self.table_view.remove_all(self.scan_id)
    
    def set_editable(self, ed):
        """
        set_editable(): description

        :param ed: ed description
        :type ed: ed type

        :returns: None
        """
        self.table_view.set_model_editable(ed)
    
    def get_ev_regions(self):
        """
        get_ev_regions(): description

        :returns: None
        """
        ev_rois = self.table_view.model().get_scans()
        self.update_ev_pol_scan_order(ev_rois) 
        return(ev_rois)
    
    def update_ev_pol_scan_order(self, ev_rois):
        ev_order = self.get_ev_polarity_scan_order()
        for e_roi in ev_rois:
            e_roi['EV_POL_ORDER'] = ev_order
    
    def on_new_region(self, scan=None, add_epu_roi=True):
        """
        on_new_region(): EnergySelWidget

        :param scan=None: scan=None description
        :type scan=None: scan=None type

        :returns: None
        """
        if(not self.add_region_enabled):
            return
        
        #let the polarity widget know that its iok to add new regions
        self.pol_sel_widget.enable_add_region_menu(True)
        
        init_ev = MAIN_OBJ.device(DNM_ENERGY).get_position()
        #scan = get_base_energy_roi('EV', DNM_ENERGY, 370, 395, 25.0, 10, 2.5, self.pol_roi, self.off_roi, stepSize=None, enable=True)
        if(scan is None):
            #use previous scans vals for new range
            ev_order = self.get_ev_polarity_scan_order()
            cur_scan = copy.deepcopy(self.table_view.get_cur_selected_scan())
            slist = self.table_view.get_scan_list()
            if((cur_scan is None) and (len(slist) == 0)):
                #create a default
                scan = get_base_energy_roi('EV', DNM_ENERGY, init_ev, init_ev, 0.0, 1, 2.5, None, stepSize=None, enable=True, energy_scan_order=ev_order)
            else:
                #get the last one
                if(len(slist) > 0):
                    cur_scan = slist[-1]
                #else use cur_scan
                scan = get_base_energy_roi('EV', DNM_ENERGY, cur_scan[START], cur_scan[STOP], cur_scan[RANGE] + EV_SCAN_EDGE_RANGE, cur_scan[NPOINTS], cur_scan[DWELL], None, stepSize=None, enable=True, energy_scan_order=ev_order)
            
        #if(self.pol_sel_widget is not None):
        if((add_epu_roi) and (self.pol_sel_widget is not None)):    
            scan['POL_ID'] = self.pol_sel_widget.table_view.create_new_model()
            #print '\t\tEV[%d] creating POL_MODEL[%d]' % (scan[SPDB_ID_VAL], scan['POL_ID'])
            self.pol_sel_widget.on_new_region()
            self.pol_sel_widget.update_table()
            
        #self.table_view.add_scan(scan, scan['POL_ID'])
        self.scan_id += 1
        self.table_view.add_scan(scan, self.scan_id)
        new_row = self.table_view.get_num_rows()
        self.table_view.model().recalc_params(new_row-1)
        
        #so that any changes will be picked up by any listening widgets
        self.on_pol_table_changed()
            
    
    def load_scan(self, ev_rois=[]):
        for cur_scan in ev_rois:
            
            scan = get_base_energy_roi('EV', DNM_ENERGY, cur_scan[START], cur_scan[STOP], cur_scan[RANGE] + EV_SCAN_EDGE_RANGE, cur_scan[NPOINTS], cur_scan[DWELL], None, stepSize=None, enable=True)
            scan[SPDB_ID_VAL] = cur_scan[SPDB_ID_VAL]
            scan['POL_ID'] = cur_scan['POL_ID']
            scan['POL_ROIS'] = cur_scan['POL_ROIS']
            
            self.pol_sel_widget.table_view.create_new_model(model_id = scan['POL_ID'])
            #print '\t\tEV[%d] creating POL_MODEL[%d]' % (scan[SPDB_ID_VAL], scan['POL_ID'])
            self.pol_sel_widget.load_scan(scan['POL_ROIS'])
            self.pol_sel_widget.update_table()
            
            self.table_view.add_scan(scan, scan[SPDB_ID_VAL])
            
    
    
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
        scan = self.table_view.get_scan(scan_id)
        if(scan):
            self.pol_sel_widget.delete_model(scan['POL_ID'])
            print('\tev deleting[%d]' % scan_id)
            self.table_view.remove_scan(scan_id)        
    
    def on_single_ev(self):
        """
        on_single_ev(): description

        :returns: None
        """
        self.table_view.model().remove_all_except_first(self.scan_id)
    
class PolaritySelWidget(BaseSelectionWidget):
    """
    A QWidget that contains an PolarizationTableView
    """
    def __init__(self,*args):
        """
        __init__(): description

        :param *args: *args description
        :type *args: *args type

        :returns: None
        """
        BaseSelectionWidget.__init__(self, *args)
        # setGeometry(x_pos, y_pos, width, height)
        self.setGeometry(300, 200, 870, 450)
        self.setWindowTitle("Click on column title to sort")
        self.editable = False
        rois = [get_epu_pol_dct(0, 0.0, angle=0.0)]
        
        
        self.scan_id = 0
        self.table_view = PolarityTableView()
        #self.scan_id = self.table_view.get_model_id_start_val()
        self.table_view.resizeColumnsToContents()
        self.table_view.setSortingEnabled(False)
        self.table_view.create_new_model()
        self.table_view.set_model_column_defaults()
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self.table_view)
        self.setLayout(layout)
        self.clearFocus()
        
        self.table_view.add_region.connect(self.on_new_region)
        self.table_view.del_region.connect(self.on_delete_region)
        self.table_view.row_selected.connect(self.on_row_selected)
        
        self.table_view.scan_changed.connect(self.changed)
        
        #self.table_view.model().scan_changed.connect(self.on_pol_scan_changed)
    def enable_add_region_menu(self, do=True):
        self.add_region_enabled = do
        
    def select_row(self, row_idx):
        self.table_view.select_row(row_idx)
    
    def get_row_data(self, item_id):
        return(self.table_view.get_scan(item_id))
                
    def delete_model(self, pol_model_id=None):
        """
        delete_model(): description

        :param pol_model_id=None: pol_model_id=None description
        :type pol_model_id=None: pol_model_id=None type

        :returns: None
        """
        """
        This function is called by the EV widget delete_model() as well as delete_row(), depends on
        why and how the row waws to be deleted.
        
        this function takes the model_id of the desired POL model_id
        that needs to be deleted. For POL models the sequence for deletion is as folows:
            - get the list of scans in the model with the same id as pol_model_id 
            - delete every scan in the list 
            - call 'remove_model(model_id)'
        """
        if(pol_model_id is None):
            scan = self.table_view.get_cur_selected_scan()
            pol_model_id = scan[SPDB_ID_VAL]
            
        pol_scans = self.table_view.get_scan_list(pol_model_id)
        for pol in pol_scans:
            self.on_delete_region(pol[SPDB_ID_VAL])
        self.table_view.remove_model(pol_model_id)
        
    def get_data(self, model_id=None):
        """
        get_data(): description

        :param model_id=None: model_id=None description
        :type model_id=None: model_id=None type

        :returns: None
        """
        return(self.table_view.get_scan_list(model_id))
    
    def update_table(self):
        """
        update_table(): description

        :returns: None
        """
        self.table_view.update_table()
    
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
        #print '\t\t\t\tPOLARITY model_ID %d selected' % (scan[SPDB_ID_VAL])
        #self.table_view.dump_model_keys()
        #_logger.debug('PolaritySelWidget: on_row_selected, emitting model_change')
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
        self.table_view.remove_all(self.scan_id)
    
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
    
    def on_new_region(self, scan=None):
        """
        on_new_region(): on new Polarity region

        :param scan=None: scan=None description
        :type scan=None: scan=None type

        :returns: None
        """
        if(not self.add_region_enabled):
            return
        
        if(scan is None):
            #use previous scans vals for new range
            cur_scan = copy.deepcopy(self.table_view.get_cur_selected_scan())
            slist = self.table_view.get_scan_list()
            if((cur_scan is None) and (len(slist) == 0)):
                #create a default
                scan = get_epu_pol_dct(0, 0.0, angle=0.0)
            else:    
                #get the last one
                if(len(slist) > 0):
                    cur_scan = slist[-1]
                #else use cur_scan
                scan = get_epu_pol_dct(cur_scan['POL'], cur_scan['OFF'], angle=cur_scan['ANGLE'])
                
        self.scan_id += 1
        self.table_view.add_scan(scan, self.scan_id)
        
        #so that any changes will be picked up by any listening widgets
        self.changed.emit()
            
    def load_scan(self, pol_rois=[]):
        for cur_scan in pol_rois:
            scan = get_epu_pol_dct(cur_scan['POL'], cur_scan['OFF'], angle=cur_scan['ANGLE'])
            
            self.on_new_region(scan)
    
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
            
        print('\t\tpol deleting[%d]' % scan_id)
        self.table_view.remove_scan(scan_id)
    
    def on_single_region(self):
        """
        on_single_region(): description

        :returns: None
        """
        self.table_view.model().remove_all_except_first(self.scan_id)



class MultiRegionWidget(BaseSelectionWidget):
    """
    A QWidget that contains Spatial, EV, and polarity selection table views
    
    Each of the 3 widgets need to support the adding and deleting of regions both
    from teh GUI (right click and select add/delete from teh menu) as well as 
    programattically because we need to be able to add/delete based on what a plotter widget
    may have done.
    
    
    """
    spatial_row_selected = QtCore.pyqtSignal(object)
    spatial_row_changed = QtCore.pyqtSignal(object)
    spatial_row_deleted = QtCore.pyqtSignal(object)
    
    def __init__(self,use_center=True, is_point=False, is_arb_line=False, enable_multi_spatial=False, *args):
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
        self.ev_polarity_scan_order = energy_scan_order_types.EV_THEN_POL
        
        self.loadScanBtn = QtWidgets.QPushButton('Load Scan')
        self.getDataBtn = QtWidgets.QPushButton('Get Data')
        self.compareDataBtn = QtWidgets.QPushButton('Compare Data')
        self.multiSpatialCheckBox = QtWidgets.QCheckBox('Multi Spatials')
          
                
        self.getDataBtn.clicked.connect(self.on_get_data_btn)
        self.loadScanBtn.clicked.connect(self.on_load_scan)
        self.compareDataBtn.clicked.connect(self.on_compare_data)
        self.multiSpatialCheckBox.clicked.connect(self.on_multi_spatial_chk)
        
        self.pol_widg = PolaritySelWidget()
        self.ev_widg = EnergySelWidget(self.pol_widg)
        self.sp_widg = SpatialSelWidget(self.ev_widg, use_center=use_center, is_point=is_point, is_arb_line=is_arb_line)
        
        self.sp_widg.table_view.row_selected.connect(self.row_was_selected)
        self.sp_widg.model_change.connect(self.on_spatial_model_changed)
        self.sp_widg.spatial_row_changed.connect(self.on_spatial_row_changed)
        self.sp_widg.roi_deleted.connect(self.on_spatial_roi_deleted)
                
        v_layout = QtWidgets.QVBoxLayout()
        v_layout.setContentsMargins(2,2,2,2)
        
        #if(enable_multi_spatial):
        #    v_layout.addWidget(self.multiSpatialCheckBox)
            
        v_layout.addWidget(self.sp_widg)
        v_layout.addWidget(self.ev_widg)
        v_layout.addWidget(self.pol_widg)
        #v_layout.addWidget(self.getDataBtn)
        #v_layout.addWidget(self.loadScanBtn)
        
        #self.multiSpatialCheckBox.setChecked(False)
        #self.on_multi_spatial_chk(False)
        if(enable_multi_spatial):
            self.multiSpatialCheckBox.setEnabled(True)
            self.multiSpatialCheckBox.setChecked(True)
            self.on_multi_spatial_chk(True)
        else:
            self.multiSpatialCheckBox.setEnabled(False)
            self.multiSpatialCheckBox.setChecked(False)
            self.on_multi_spatial_chk(False)  
        
        self.setLayout(v_layout)
        
    
    def show_load_btn(self):
        self.layout().addWidget(self.loadScanBtn)
    
    def show_getdata_btn(self):
        self.layout().addWidget(self.getDataBtn)
    
    def on_get_data_btn(self):
        #sp_regions = self.get_sp_regions()
        #print sp_regions
        self.get_sp_regions(do_print=True)
    
    def delete_spatial_row(self, sp_model_id=None):
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
        from cls.scanning.dataRecorder import STXMDataIo
        from cls.utils.fileUtils import get_file_path_as_parts
        from cls.appWidgets.dialogs import getOpenFileName
        
        datadir=r'S:\STXM-data\Cryo-STXM\2016\guest\1013'
        data_file_pfx = 'C'
        fname = getOpenFileName("Load Scan", filter_str="Scan Files (%s*.hdf5)" % data_file_pfx, search_path=datadir)
        data_dir, fprefix, fsuffix = get_file_path_as_parts(fname)
        if(fname is None):
            return
        data_io = STXMDataIo(data_dir, fprefix)
        data_dct = data_io.load()
        if(data_dct is not None):
            dct_put(data_dct,'CFG.WDG_COM.CMND', widget_com_cmnd_types.LOAD_SCAN)
            self.load_scan(dct_get(data_dct, ADO_CFG_WDG_COM))
        
        
    def load_scan(self, wdg_com):
        """
        given the scan type supports multi spatial, read in and load the respective 
        tables
        scan_types = Enum('Detector_Image','OSA_Image','OSA_Focus','Sample_Focus','Sample_Point_Spectrum', 'Sample_Line_Spectrum', 'Sample_Image', 'Sample_Image_Stack', 'Generic_Scan')
        """
        multi_scan_types = [scan_types.SAMPLE_POINT_SPECTRUM, scan_types.SAMPLE_LINE_SPECTRUM, scan_types.SAMPLE_IMAGE, scan_types.SAMPLE_IMAGE_STACK, scan_types.SAMPLE_IMAGE + IMAGE_LXL, scan_types.SAMPLE_IMAGE + IMAGE_PXP]
        
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
        self.sp_widg.clear_table()
        self.sp_widg.load_scan(sp_db)
        if(len(sp_ids) > 1):
            for sp_id in sp_ids[1:]:
                sp_roi = sp_roi_dct[sp_id]
                #self.sp_widg.load_scan(sp_roi)
                #self.sp_widg.table_view.add_scan(sp_roi, sp_id)
                self.sp_widg.add_scan(sp_roi)
                #self.print_sp_roi(sp_roi)
        
        
        
    def row_was_selected(self, scan):
        sp_db = make_spatial_db_dict()
        sp_db[WDGCOM_CMND] = widget_com_cmnd_types.SELECT_ROI
        #dct_put(sp_db, SPDB_SCAN_PLUGIN_ITEM_ID, scan[SPDB_ID_VAL])
        sp_db[SPDB_ID_VAL] =  scan[SPDB_ID_VAL] 
        
        self.spatial_row_selected.emit(sp_db)
    
    def enable_add_spatial_region_menu(self, do=True):
        self.sp_widg.enable_add_region_menu(do)
    
    def deselect_all(self):
        #_logger.debug('deselect_all: called')
        self.sp_widg.table_view.clearSelection()
        
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
    
    def on_spatial_model_changed(self, scan_id):
        cur_row_list = self.sp_widg.table_view.selectionModel().selectedRows()
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
            
            for ev_roi in self.ev_widg.get_data(sp_roi['EV_ID']):
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
                for pol_roi in self.pol_widg.get_data(ev_roi['POL_ID']):
                    if(do_print):
                        self.print_pol_roi(ev_roi[START], pol_roi)
                    #ev_setpoints.append(ev_sp)
                    #dwell_setpoints.append(dwell)
                    pol_setpoints.append(pol_roi['POL'])
                    off_setpoints.append(pol_roi['OFF'])
                    angle_setpoints.append(pol_roi['ANGLE'])
                    _pols.append(pol_roi)
                    pol_npts += 1
                ev_roi['POL_ROIS'] = _pols
                
                ev_roi['EPU_POL_PNTS'] = pol_setpoints
                ev_roi['EPU_OFF_PNTS'] = off_setpoints
                ev_roi['EPU_ANG_PNTS'] = angle_setpoints
                
                _evs.append(ev_roi)
                
            sp_roi[SPDB_EV_ROIS] = _evs
            sp_roi[SPDB_EV_NPOINTS] = e_npts
            sp_roi[SPDB_POL_NPOINTS] = pol_npts
            
            sp_regions[sp_roi[SPDB_ID_VAL]] = sp_roi     

        return(sp_regions)     
                    
    def compare_roi(self, roi_def, axis=SPDB_X):
        """
        compare_roi(): description

        :param roi: roi description
        :type roi: roi type

        :returns: None
        """
        print()
        fields = ['CENTER', 'RANGE', 'NPOINTS', 'STEP', 'START', 'STOP']
        if(axis == SPDB_X):
            ax = roi_def['SPATIAL_ROIS'][0]
        else:
            ax = roi_def['SPATIAL_ROIS'][1]    

        for k in fields:
            print('[%s] = %.2f [%s] = %.2f' % (k+axis, roi_def[k+axis], k, ax[k]))
        k = 'SETPOINTS'    
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
                EV_ROIS = ['EV_ROI', ........['POL_ROIS']]
                    POL_ROIS = [{'POL_ROI', ....}]
            sp_regions[1] = ['SPATIAL_REGION',.....[SPDB_EV_ROIS]]
                EV_ROIS = ['EV_ROI', ........['POL_ROIS']]
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
                for pol_roi in self.pol_widg.get_data(ev_roi['POL_ID']):
                    #self.print_pol_roi(ev_roi[START], pol_roi)
                    #ev_setpoints.append(ev_sp)
                    #dwell_setpoints.append(dwell)
                    pol_setpoints.append(pol_roi['POL'])
                    off_setpoints.append(pol_roi['OFF'])
                    angle_setpoints.append(pol_roi['ANGLE'])
                    _pols.append(pol_roi)
                ev_roi['POL_ROIS'] = _pols
                
                ev_roi['EPU_POL_PNTS'] = pol_setpoints
                ev_roi['EPU_OFF_PNTS'] = off_setpoints
                ev_roi['EPU_ANG_PNTS'] = angle_setpoints
                
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
#             ax = roi_def['SPATIAL_ROIS'][0]
#         else:
#             ax = roi_def['SPATIAL_ROIS'][1]    
# 
#         for k in fields:
#             print '[%s] = %.2f [%s] = %.2f' % (k+axis, roi_def[k+axis], k, ax[k])
#         k = 'SETPOINTS'    
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
        print('\tEV ROI [%d] Start[%.2f] End[%.2f] Range[%.2f] Points[%.2f] Dwell[%.2f] POL_MODEL=%d' % (roi[SPDB_ID_VAL],roi[START],roi[STOP],roi[RANGE], roi[NPOINTS], roi[DWELL], roi['POL_ID']))
        
    def print_pol_roi(self, ev_setpoint, roi):
        """
        print_pol_roi(): description

        :param ev_setpoint: ev_setpoint description
        :type ev_setpoint: ev_setpoint type

        :param roi: roi description
        :type roi: roi type

        :returns: None
        """
        print('\t\tPOL ROI [%d] [%.3f ev]  POL[%d] Offset[%.2f] Angle[%.2f]' % (roi[SPDB_ID_VAL], ev_setpoint, roi['POL'],roi['OFF'],roi['ANGLE']))
                
        
        
        
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
    
    
    
