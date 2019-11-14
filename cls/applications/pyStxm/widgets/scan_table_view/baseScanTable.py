'''
Created on 2013-05-16

@author: bergr
'''
import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets

from cls.utils.log import get_module_logger
from cls.utils.roi_dict_defs import *
from cls.utils.roi_utils import on_range_changed, on_npoints_changed, on_step_size_changed, on_start_changed, \
    on_stop_changed, \
    on_center_changed

_logger = get_module_logger(__name__)

# this is the value that will be added to the start and end of each extra EV
# region

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
    return (arr)


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


# QTableWidget signals
# void cellActivated ( int row, int column )
# void cellChanged ( int row, int column )
# void cellClicked ( int row, int column )
# void cellDoubleClicked ( int row, int column )
# void cellEntered ( int row, int column )
# void cellPressed ( int row, int column )
# void currentCellChanged ( int currentRow, int currentColumn, int previousRow,
# int previousColumn )
# void currentItemChanged ( QTableWidgetItem * current, QTableWidgetItem *
# previous )
# void itemActivated ( QTableWidgetItem * item )
# void itemChanged ( QTableWidgetItem * item )
# void itemClicked ( QTableWidgetItem * item )
# void itemDoubleClicked ( QTableWidgetItem * item )
# void itemEntered ( QTableWidgetItem * item )
# void itemPressed ( QTableWidgetItem * item )
# void itemSelectionChanged ()

class BaseScanTableModel(QtCore.QAbstractTableModel):
    scan_changed = QtCore.pyqtSignal(int, object)

    def __init__(self, hdrList=[], datain=[[]], parent=None, *args):
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
        # QtCore.QAbstractTableModel.__init__(self, parent, *args)
        super(BaseScanTableModel, self).__init__(parent, *args)
        self.scanListData = list(datain)
        self.hdrList = list(hdrList)
        self.scanProgress = {}
        self.cur_scan_id = 0
        self.column_map = None

        self.min_rows = 0
        self.max_rows = 1

        self.valid_range = (None, None, None, None)

        # have a way to set specific rows or columns read only
        self.rd_only_rows = {}
        self.rd_only_cols = {}

        self._get_funcs = []
        self._set_funcs = []

    def is_empty(self):
        num = len(self.scanListData)
        if(num < 1):
            return(True)
        else:
            return(False)

    def is_valid_floor_ceiling_vals(self, floor_lim, ceiling_lim, val):
        '''
        a standard function to check a value that has been entered against a floor and ceiling range that has been
        specified for this particular column in the table model
        :param floor_lim:
        :param ceiling_lim:
        :param val:
        :return:
        '''
        if(floor_lim is None):
            #we dont care about floor so make a valid one

            floor_lim = val - 1

        if (ceiling_lim is None):
            # we dont care about ceiling so make a valid one
            ceiling_lim = val + 1

        if(type(floor_lim) is str):
            floor_lim = float(floor_lim)

        if (type(ceiling_lim) is str):
            floor_lim = float(ceiling_lim)

        if(floor_lim <= val <= ceiling_lim):
            return(True)
        else:
            return(False)

    def get_column_with_name(self, name):
        i = 0
        for item in self.column_map:
            if (item['hdr'] == name):
                return (i)
            i += 1
        return (None)

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
        # return a copy
        return (self.scanListData[:])

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
        # return a copy
        return (self.scanListData[:])

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
        return (str(scan[self.column_map[col]]))

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
        if (rdonly):
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
        if (rdonly):
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
            # if(hasattr(scan, SPDB_ID_VAL)):
            if (SPDB_ID_VAL in list(scan.keys())):
                if (scan[SPDB_ID_VAL] == scan_id):
                    # print '_get_scan_rowidx: returning %d' % row
                    return (False)
        return (True)

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

        if (self.rowCount() >= self.max_rows):
            return

        if (scan[SPDB_ID_VAL] is None):
            # the model is being initialized
            scan[SPDB_ID_VAL] = 0

        if (self._scan_not_exist(scan[SPDB_ID_VAL])):
            self.insertRow(scan)
            return (True)
        else:
            return (False)

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
        # self.dataChanged.emit(parent, parent)
        return (self.rowCount(parent))

    def removeRow(self, row, parent=QtCore.QModelIndex()):
        """
        removeRow(): description

        :param row: row description
        :type row: row type

        :param parent=QtCore.QModelIndex(): parent=QtCore.QModelIndex() description
        :type parent=QtCore.QModelIndex(): parent=QtCore.QModelIndex() type

        :returns: None
        """
        # row = self.get_scan_rowidx(scan_id)
        if (self.rowCount() == self.min_rows):
            return
        if (row != None):
            self.beginRemoveRows(parent, row, row)
            del (self.scanListData[row])
            self.endRemoveRows()
            self.dataChanged.emit(parent, parent)

    def removeAll(self, parent=QtCore.QModelIndex()):
        """
        removeAll(): description

        :param parent=QtCore.QModelIndex(): parent=QtCore.QModelIndex() description
        :type parent=QtCore.QModelIndex(): parent=QtCore.QModelIndex() type

        :returns: None
        """
        self.beginRemoveRows(parent, 0, len(self.scanListData))
        # self.scanListData = []
        for row in range(len(self.scanListData)):
            # the list shrinks each time so only delete from teh top
            del (self.scanListData[0])
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
            del (self.scanListData[row])
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
        # print 'checking for scan_id = %d' % scan_id
        for scan in self.scanListData:
            # print 'get_scan_rowidx: [%d] = %d' % (row, scan['ID'])
            if (scan[SPDB_ID_VAL] == scan_id):
                # print '_get_scan_rowidx: returning %d' % row
                return (row)
            row += 1
        return (None)

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
            # print 'get_scan_rowidx: [%d] = %d' % (row, scan['ID'])
            if (scan[SPDB_ID_VAL] == scan_id):
                self.scanListData[row][SPDB_X][CENTER] = newscan[SPDB_X][CENTER]
                self.scanListData[row][SPDB_Y][CENTER] = newscan[SPDB_Y][CENTER]
                self.scanListData[row][SPDB_X][RANGE] = newscan[SPDB_X][RANGE]
                self.scanListData[row][SPDB_Y][RANGE] = newscan[SPDB_Y][RANGE]
                # if(do_step_npts):
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
        # print 'checking for scan_id = %d' % scan_id
        return (self.scanListData[row])

    def get_scan(self, scan_id):
        """
        get_scan(): description

        :param scan_id: scan_id description
        :type scan_id: scan_id type

        :returns: None
        """
        """ return the row of the scan with the matching scan_id """
        # print 'checking for scan_id = %d' % scan_id
        for scan in self.scanListData:
            # print 'get_scan_rowidx: [%d] = %d' % (row, scan['ID'])
            if (scan[SPDB_ID_VAL] == scan_id):
                # print '_get_scan_rowidx: returning %d' % row
                return (scan)
        return (None)

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
            if (scan[SPDB_ID_VAL] == scan_id):
                self.scanProgress[scan_id] = progress
                self.cur_scan_id = scan_id
                # need to fire the signal so that the display role will get
                # processed
                row = self._get_scan_rowidx(scan_id)
                index = QtCore.QModelIndex()
                self.dataChanged.emit(index, index)

                # _logger.info('current scan ID [%ld] has progress %f' %
                # (scan_id, progress))

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
        # return(10)

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
                    # return QtCore.QString(self.hdrList[section])
                    return self.hdrList[section]
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
            if (col == 0):
                v = scan[SPDB_ID_VAL]
            else:
                v = scan[self.column_map[col]]

            if (type(v) is str):
                return (v)
            if (type(v) is np.float32):
                val = '%.3f' % v
                return (val)
            if (type(v) is np.float64):
                val = '%.3f' % v
                return (val)
            if (type(v) is float):
                val = '%.3f' % v
                return (val)
            if (type(v) is int):
                val = '%d' % v
                return (val)
            if (type(v) is bool):
                if (v):
                    return ('True')
                else:
                    return ('False')

            _logger.debug('basescanTable.data: QtCore.Qt.DisplayRole: OOPS, this fell through (%d, %s)' % (col, v))

        elif role == QtCore.Qt.BackgroundRole:
            if (col == 0):
                bg = QtGui.QBrush(QtCore.Qt.gray)
            elif (col < 5):
                bg = QtGui.QBrush(QtCore.Qt.lightGray)
                # pass
            else:
                if (enabled):
                    bg = QtGui.QBrush(QtCore.Qt.white)
                else:
                    bg = QtGui.QBrush(QtGui.QColor(220, 220, 220))
            return bg
        elif role == QtCore.Qt.ForegroundRole:
            if (enabled):
                fg = QtGui.QBrush(QtCore.Qt.black)
            else:
                fg = QtGui.QBrush(QtCore.Qt.blue)
            return fg
        elif role == QtCore.Qt.FontRole:
            fnt = QtGui.QFont()
            fnt.setPointSize(TABLE_FONT_SIZE)
            if (col == 0):
                fnt.setBold(True)
            return fnt
        elif role == QtCore.Qt.TextAlignmentRole:
            if (col == 0):
                return (QtCore.Qt.AlignLeft)
            else:
                # return(QtCore.Qt.AlignRight)
                return (QtCore.Qt.AlignCenter)
        else:

            # print 'returning None [%d,%d] role = %d' % (row,col, role)
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
        # print '%d, %d' % (index.row(), index.column())
        row = index.row()
        col = index.column()
        rowRdOnly = row in list(self.rd_only_rows.keys())
        colRdOnly = col in list(self.rd_only_cols.keys())
        if (rowRdOnly):
            return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsSelectable
        elif (colRdOnly):
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        else:
            return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable


def gen_spatial_model_obj(hdr_name, func, floor_val, ceiling_val):
    dct = {}
    dct['hdr'] = hdr_name
    dct['func'] = func
    dct['floor_val'] = floor_val
    dct['ceiling_val'] = ceiling_val
    return (dct)


# the C_ is for Center
C_SPATIAL_DCT = []
C_SPATIAL_DCT.append(gen_spatial_model_obj('ID', None, None, None))
C_SPATIAL_DCT.append(gen_spatial_model_obj('CENTERX', on_center_changed, None, None))
C_SPATIAL_DCT.append(gen_spatial_model_obj('RANGEX', on_range_changed, None, None))
C_SPATIAL_DCT.append(gen_spatial_model_obj('CENTERY', on_center_changed, None, None))
C_SPATIAL_DCT.append(gen_spatial_model_obj('RANGEY', on_range_changed, None, None))
C_SPATIAL_DCT.append(gen_spatial_model_obj('STEPX', on_step_size_changed, None, None))
C_SPATIAL_DCT.append(gen_spatial_model_obj('STEPY', on_step_size_changed, None, None))
C_SPATIAL_DCT.append(gen_spatial_model_obj('NPOINTSX', on_npoints_changed, 0, 20000))
C_SPATIAL_DCT.append(gen_spatial_model_obj('NPOINTSY', on_npoints_changed, 0, 20000))

# the S_ is for Start
S_SPATIAL_DCT = []
S_SPATIAL_DCT.append(gen_spatial_model_obj('ID', None, None, None))
S_SPATIAL_DCT.append(gen_spatial_model_obj('STARTX', on_start_changed, None, None))
S_SPATIAL_DCT.append(gen_spatial_model_obj('STOPX', on_stop_changed, None, None))
S_SPATIAL_DCT.append(gen_spatial_model_obj('STARTY', on_start_changed, None, None))
S_SPATIAL_DCT.append(gen_spatial_model_obj('STOPY', on_stop_changed, None, None))
S_SPATIAL_DCT.append(gen_spatial_model_obj('STEPX', on_step_size_changed, None, None))
S_SPATIAL_DCT.append(gen_spatial_model_obj('STEPY', on_step_size_changed, None, None))
S_SPATIAL_DCT.append(gen_spatial_model_obj('NPOINTSX', on_npoints_changed, 0, 20000))
S_SPATIAL_DCT.append(gen_spatial_model_obj('NPOINTSY', on_npoints_changed, 0, 20000))


def get_val_from_roi(sp_db, field, roi_key):
    if (roi_key in list(sp_db.keys())):
        roi = sp_db[roi_key]
    else:
        return (None)

    if (field in list(roi.keys())):
        return (roi[field])
    else:
        return (None)


def get_val_from_sp_db(field, sp_db):
    axis_key = field[-1]
    subfld = field[0:-1]

    return (get_val_from_roi(sp_db, subfld, axis_key))


def set_val_in_roi(sp_db, field, roi_key, val):
    if (roi_key in list(sp_db.keys())):
        roi = sp_db[roi_key]
    else:
        return (None)

    if (field in list(roi.keys())):
        roi[field] = val
    else:
        _logger.error('field [%s] doesnt exist in sp_db' % field)


def set_field_val_in_sp_db(field, val, sp_db):
    axis_key = field[-1]
    subfld = field[0:-1]
    set_val_in_roi(sp_db, subfld, axis_key, val)


def get_roi_from_sp_db(field, sp_db):
    axis_key = field[-1]
    if (axis_key in list(sp_db.keys())):
        return (sp_db[axis_key])
    else:
        _logger.error('axis_key [%s] doesnt exist in sp_db' % axis_key)


class BaseScanTableView(QtWidgets.QTableView):
    """
    This is a widget to display the parameters of individual scans, the widget responds to cell edits
    and forces a recalc of row elements if need be.
    """
    row_selected = QtCore.pyqtSignal(object)  # row data
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
        self.model_id_lst = []
        self.signals_connected = False

        self.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        self.verticalHeader().setDefaultSectionSize(20)

        self.horizontalHeader().setSectionsClickable(False)

        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setAlternatingRowColors(True)

        fnt = QtGui.QFont()
        fnt.setPointSize(TABLE_FONT_SIZE)
        self.setFont(fnt)

        self.verticalHeader().setDefaultSectionSize(15)

        self._cur_selected_scan = None
        self.tablemodel_class = tablemodel_class

        # self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectItems)
        # self.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        # self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        # self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
        # self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.stretchLastSection)
        self.scanFlags = {}
        self._block_updates = False
        # self.clicked.connect(self.on_clicked)
        # self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        # self.selectionModel().selectionChanged.connect(self.selChanged)
        self.clicked.connect(self.on_clicked)

    def get_all_data(self):
        return(self.tablemodel.get_model())

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
        # self._numHdrCols = self.tablemodel.columnCount(self)
        # self.clicked.connect(self.on_clicked)
        self.signals_connected = True

    def disconnect_signals(self):
        """
        disconnect_signals(): description

        :returns: None
        """
        try:
            if (self.signals_connected):
                self.selectionModel().selectionChanged.disconnect(self.selChanged)
                self.tablemodel.dataChanged.disconnect(self.on_cell_changed)
                self.tablemodel.scan_changed.disconnect(self.on_model_changed)
                # self.clicked.disconnect(self.on_clicked)
                self.signals_connected = False
        except:
            #raise ScanOptionError('Problem disconnecting Signals')
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
        if (self.tablemodel is not None):
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
        # self.row_selected.emit(scan)
        self._cur_selected_scan = scan

    def get_next_model_id(self):
        # m_keys = sorted(self.models.keys())
        # return(m_keys[-1] + 1)
        id_lst = []
        for scan in self.tablemodel.scanListData:
            id_lst.append(scan[SPDB_ID_VAL])
        if (len(id_lst) == 0):
            return (0)
        else:
            ids = sorted(id_lst)
            return (ids[-1] + 1)

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
        return (self.model_id_start_val)

    def dump_model_keys(self):
        """
        dump_model_keys(): description

        :returns: None
        """
        model = self.tablemodel.get_scan_list()
        # print self.tablemodel_class
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
        if (model_id is not None):
            if (model_id in list(self.models.keys())):
                return (self.models[model_id].get_scan_list())
            else:
                print('Model[%d] does not exist' % model_id)
                return []
        else:
            return (self.tablemodel.get_scan_list())

    def get_all_data(self):
        data = []
        for model_id in list(self.models.keys()):
            data.append(self.get_model(model_id).get_scans())

        return(data)


    def get_num_scans(self):
        """
        get_num_scans(): description

        :returns: None
        """
        scans = self.get_scan_list()
        return (len(scans))

    def get_scan(self, scan_id):
        """
        get_scan(): description

        :param scan_id: scan_id description
        :type scan_id: scan_id type

        :returns: None
        """
        return (self.tablemodel.get_scan(scan_id))

    def get_model(self, model_id):
        """
        get_model(): description

        :param model_id: model_id description
        :type model_id: model_id type

        :returns: None
        """
        if (model_id in list(self.models.keys())):
            return (self.models[model_id])

    def remove_model(self, model_id):
        """
        remove_model(): description

        :param model_id: model_id description
        :type model_id: model_id type

        :returns: None
        """
        if(not self.models):
            #model dict is empty so just split
            return

        if (model_id in list(self.models.keys())):
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
        return (self._cur_selected_scan)

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
        if (len(idxs) > 0):
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
        if (row is not None):
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

    # def select_row(self, scan_id=None, progress=0.0):
    def select_row(self, row_idx=None, progress=0.0):
        """
        select_row(): description

        :param scan_id=None: scan_id=None description
        :type scan_id=None: scan_id=None type

        :param progress=0.0: progress=0.0 description
        :type progress=0.0: progress=0.0 type

        :returns: None
        """
        if (row_idx is None):
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
        return (self.tablemodel.rowCount(None))

    def get_row_data(self, row):
        """
        get_row_data(): description

        :param row: row description
        :type row: row type

        :returns: None
        """
        scan = self.tablemodel.get_scan_by_row(row)
        return (scan)

    def on_cell_changed(self, idx, idx2):
        """
        on_cell_changed(): description

        :param idx: idx description
        :type idx: idx type

        :param idx2: idx2 description
        :type idx2: idx2 type

        :returns: None
        """
        d = idx.data()
        if (d is not None):
            val = float(d)
        else:
            return (None, False)

    def create_new_model(self, scans=None, model_id=None, use_center=True, single_model=False):
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
        # connect the models signal to emit the views scan_changed signal
        self.disconnect_signals()
        if (scans is None):
            scanlist = []
        else:
            scanlist = scans

        if(single_model):
            self.model_id = 0

        elif (model_id is None):
            # increment model id
            while self.model_id in list(self.models.keys()):
                 self.model_id += 1
                #self.model_id = get_unique_roi_id()
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
        return (self.model_id)

    def switch_models(self, model_id):
        """
        switch_models(): description

        :param model_id: model_id description
        :type model_id: model_id type

        :returns: None
        """
        """ set the current model to be the one owned by scan_id """
        # print 'switch_models: model_id [%d]' % model_id
        #if(not self.models):
        #    self.create_new_model(model_id=model_id)

        if (model_id in list(self.models.keys())):
            self.tablemodel = self.models[model_id]
            self.model_id = model_id
            self.setModel(self.tablemodel)
            self.disconnect_signals()
            self.connect_signals()
            return (True)
        return (False)

    def on_model_changed(self, row, scan):
        """
        on_model_changed(): description

        :param row: row description
        :type row: row type

        :param scan: scan description
        :type scan: scan type

        :returns: None
        """
        # print 'on_model_changed: emitting scan_changed'
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
        # make sure that the scan_id is an integer if it is still a string
        scan[SPDB_ID_VAL] = int(scan_id)
        success = self.tablemodel.add_scan(scan)
        self._cur_selected_scan = scan
        self.set_model_column_defaults()
        success = True
        return (success)


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
        self.add_region_enabled = True

    def get_all_data(self):
        if(self.table_view is not None):
            data = self.table_view.get_all_data()
            if(len(data) > 0):
                return(data[0])
        return(data)

    

