'''
Created on Feb 9, 2016

@author: bergr
'''

'''
Created on Nov 2, 2015

@author: bergr
'''
import operator
import os
from PyQt5 import QtCore, QtGui, QtWidgets
import math

from cls.utils.prog_dict_utils import make_progress_dict, PROG_DCT_ID, PROG_DCT_SPID, PROG_DCT_PERCENT, PROG_DCT_STATE

from cls.data_io.stxm_data_io import STXMDataIo
from cls.app_data.defaults import rgb_as_hex, master_colors, master_q_colors, get_style
from cls.utils.roi_utils import get_base_roi, get_base_energy_roi, get_unique_roi_id, \
                    get_epu_pol_dct, make_spatial_db_dict, widget_com_cmnd_types, \
                    on_range_changed, on_npoints_changed, on_step_size_changed, on_start_changed, on_stop_changed, \
                    on_center_changed, recalc_setpoints, get_sp_ids_from_wdg_com, get_sp_db_from_wdg_com

from cls.types.stxmTypes import scan_status_types, scan_image_types, scan_types
from cls.utils.roi_dict_defs import *

from cls.utils.dict_utils import dct_get, dct_put
from cls.utils.fileUtils import get_file_path_as_parts
from cls.utils.list_utils import merge_to_one_list
from cls.utils.log import get_module_logger


from bcm.devices.epu import convert_wrapper_epu_to_str

iconsDir = os.path.join( os.path.dirname(os.path.abspath(__file__)), 'icons', 'png')

#setup module logger with a default do-nothing handler
_logger = get_module_logger(__name__)

HDR_FONT_SIZE = 8.0
TABLE_FONT_SIZE = 8.0


DEFAULT_PIXMAP_COLUMN = 5
DEFAULT_PROGESS_BAR_COLUMN = 6

#table column width definitions
FILENAME_WIDTH = 120
STACK_FILENAME_WIDTH = 170
EV_WIDTH = 60
START_WIDTH = 100
POLARITY_WIDTH = 100
CENTER_WIDTH = 150
NPOINTS_WIDTH = 100
PMAP_WIDTH = 16
PROGRESS_WIDTH = 150
TOMO_WIDTH = 200

det_scan_prog_dct = {'PROG': {'STATE': 0, 'PERCENT': 40.56, 'SPID': 0}, 'PROG_DICT': 'PROG_DICT'}
osa_scan_prog_dct = {'PROG': {'STATE': 0, 'PERCENT': 6.0, 'SPID': 3}, 'PROG_DICT': 'PROG_DICT'}
osa_focus_scan_prog_dct = {'PROG': {'STATE': 0, 'PERCENT': 5.0, 'SPID': 2}, 'PROG_DICT': 'PROG_DICT'}
focus_scan_prog_dct = {'PROG': {'STATE': 0, 'PERCENT': 27.500000000000004, 'SPID': 1}, 'PROG_DICT': 'PROG_DICT'}
point_scan_prog_dct = {'PROG': {'STATE': 0, 'PERCENT': 97.5, 'SPID': 0}, 'PROG_DICT': 'PROG_DICT'}
image_scan_prog_dct = {'PROG': {'STATE': 0, 'PERCENT': 89.5, 'SPID': 0}, 'PROG_DICT': 'PROG_DICT'}
image_stack_scan_prog_dct = {'PROG': {'STATE': 0, 'PERCENT': 99.5, 'SPID': 0}, 'PROG_DICT': 'PROG_DICT'} # no pol or ev idx, always spid=0
tomo_scan_prog_dct = {'PROG': {'STATE': 0, 'PERCENT': 99.5, 'SPID': 0}, 'PROG_DICT': 'PROG_DICT'} # no pol or ev idx, always spid=0
positioner_scan_prog_dct = {'PROG': {'STATE': 0, 'PERCENT': 98.75, 'SPID': 4}, 'PROG_DICT': 'PROG_DICT'}
line_scan_prog_dct = {'PROG': {'STATE': 0, 'PERCENT': 103.75000000000001, 'SPID': 0}, 'PROG_DICT': 'PROG_DICT'}



class BaseModel(QtCore.QObject):
    changed = QtCore.pyqtSignal()

    def __init__(self):
        QtCore.QAbstractTableModel.__init__(self)
        self.model_data = []

    def get_model_data(self):
        return(self.model_data)

    def set_data(self, row, col, val):
        '''
        Users must use this set_data function if they want to see the changes because the changes
        are dependant on the changed signal being emitted
        '''
        try:
            if(len(self.model_data) > 0):
                self.model_data[row][col] = val
                self.changed.emit()
        except IndexError:
            #print ''
            pass


class ScanQueueModel(BaseModel):
    def __init__(self):
        BaseModel.__init__(self)

scan_q_model_class = ScanQueueModel()

class ScanQTableModel(QtCore.QAbstractTableModel):
    def __init__(self, parent, model_d, header, *args):
        #global model_data
        QtCore.QAbstractTableModel.__init__(self, parent, *args)
        self.header = header
        self.scan_q_model_class = scan_q_model_class
        self.model_data = scan_q_model_class.get_model_data()
        self.set_pmap_col(DEFAULT_PIXMAP_COLUMN)
        self.set_prog_col(DEFAULT_PROGESS_BAR_COLUMN)

        #connect to the changed signal so that changes to the model from anywhere will be signaled back here
        self.scan_q_model_class.changed.connect(self._emit_changed)

    def _emit_changed(self):
        self.dataChanged.emit(QtCore.QModelIndex(), QtCore.QModelIndex())

    def set_pmap_col(self, col):
        #print('ScanQTableModel: setting self.pmap_col = %d' % col)
        self.pmap_col = col

    def set_prog_col(self, col):
        #print('ScanQTableModel: setting self.prog_col = %d' % col)
        self.prog_col = col

    def set_header(self, hdr_list):
        self.header = hdr_list

    def set_model(self, model):
        self.model_data = self.scan_q_model_class.get_model_data()
        for r in model:
            self.insertRow(r)

    def insertRow(self, item, parent=QtCore.QModelIndex()):
        """
        insertRow(): description

        :param scan: scan description
        :type scan: scan type

        :param parent=QtCore.QModelIndex(): parent=QtCore.QModelIndex() description
        :type parent=QtCore.QModelIndex(): parent=QtCore.QModelIndex() type

        :returns: None
        """
        self.model_data = self.scan_q_model_class.get_model_data()
        self.beginInsertRows(parent, self.rowCount(parent), self.rowCount(parent))
        self.model_data.append(item)
        self.endInsertRows()
        self.dataChanged.emit(parent, parent)
        return(self.rowCount(parent))

    def removeAll(self, parent=QtCore.QModelIndex()):
        self.model_data = self.scan_q_model_class.get_model_data()
        if self.rowCount() > 0:
            self.beginRemoveRows(parent, 0,  len(self.model_data))
            for i in range(0,  self.rowCount()) :
                del(self.model_data[0])
            self.removeRows(0, self.rowCount())
            self.endRemoveRows()
        self.dataChanged.emit(parent, parent)
        self.model_data = self.scan_q_model_class.get_model_data()


    def get_all_rows_sum_of_column(self, col=DEFAULT_PROGESS_BAR_COLUMN):
        ttl = 0.0
        for i in range(self.rowCount()):
            ttl += self.model_data[i][col]
        return(ttl)

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.model_data)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return(len(self.header))

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()
        sts = self.model_data[row][self.pmap_col]

        if(row > self.rowCount()):
            return(None)

        if((col == 0) and (role == QtCore.Qt.TextAlignmentRole)):
            return QtCore.Qt.AlignLeft

        elif((col > 0) and (role == QtCore.Qt.TextAlignmentRole)):
            return QtCore.Qt.AlignCenter


        elif role == QtCore.Qt.BackgroundRole:
            # scan_status_types = 'STOPPED', 'PAUSED', 'RUNNING', 'ABORTED'
            if(sts == scan_status_types.STOPPED):
                bg = master_q_colors['app_medgray']
            elif(sts == scan_status_types.PAUSED):
                bg = master_q_colors['app_yellow']
            elif(sts == scan_status_types.RUNNING):
                bg = master_q_colors['scan_sts_blue']
            elif(sts == scan_status_types.ABORTED):
                bg = master_q_colors['app_red']
            else:
                bg = master_q_colors['app_drkgray']

            return bg

        elif role == QtCore.Qt.ForegroundRole:
            if(sts == scan_status_types.STOPPED):
                fg = master_q_colors['app_superltgray']
            elif(sts == scan_status_types.PAUSED):
                fg = QtGui.QBrush(QtCore.Qt.black)
            elif(sts == scan_status_types.RUNNING):
                fg = QtGui.QBrush(QtCore.Qt.white)
            elif(sts == scan_status_types.ABORTED):
                fg = QtGui.QBrush(QtCore.Qt.white)
            elif(sts == scan_status_types.DONE):
                fg = master_q_colors['app_blue']
            else:
                _logger.error('unknown scan status[%d]' % sts)
                fg = None
            return fg

        elif role == QtCore.Qt.DisplayRole:

            return self.model_data[row][col]
        else:
            return None


    def headerData(self, col, orientation, role=QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.header[col]
        return None

    def setData(self, index, value, role=QtCore.Qt.DisplayRole):
        row = index.row()
        col = index.column()
        if((col == self.prog_col) and (self.model_data[row][self.prog_col] == 100.0)):
            print('')
        else:
            self.model_data[row][col] = value
        return True

    def modify_data(self, row, col, value):
        self.model_data[row][col] = value
        self.dataChanged.emit(QtCore.QModelIndex(), QtCore.QModelIndex())

    def flags(self, index):
        return  QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

class ScanQTableView(QtWidgets.QTableView):
    """
    A simple table
    """
    def __init__(self, header, **kwargs):
        #QtWidgets.QTableView.__init__(self)
        super(ScanQTableView, self).__init__()
        self.setObjectName('ScanQTableView')

        if('prog_col' in list(kwargs.keys())):
            self.prog_col = kwargs['prog_col']
        else:
            self.prog_col = DEFAULT_PROGESS_BAR_COLUMN

        if('pmap_col' in list(kwargs.keys())):
            self.set_pmap_col(kwargs['pmap_col'])
        else:
            self.set_pmap_col(DEFAULT_PIXMAP_COLUMN)

        self.hdr_list = header
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.verticalHeader().setDefaultSectionSize(15)

        #turn bold off
        font = self.horizontalHeader().font()
        font.setBold(False)
        font.setPointSize(HDR_FONT_SIZE)
        self.horizontalHeader().setFont(font)
        self.horizontalHeader().setHighlightSections(False)

        self.init_delegates()
        #self.setAlternatingRowColors(True)
        #self.setContentsMargins(1, 10, 10, 1)

    def set_pmap_col(self, col):
        #print('ScanQTableView: set_pmap_col=%d' % col)
        self.pmap_col = col

    def set_prog_col(self, col):
        #print('ScanQTableView: set_prog_col=%d' % col)
        self.prog_col = col

    def set_progress(self, row, prog):
        self.model().modify_data(row, self.prog_col, prog)

    def get_total_progress(self):
        ttl = self.model().get_all_rows_sum_of_column(self.prog_col)
        return(ttl)

    def set_pixmap(self, row, pmap):
        self.model().modify_data(row, self.pmap_col, pmap)

    def init_delegates(self):
        #num_cols = len(self.hdr_list)
        #always the last 2
        # self.setItemDelegateForColumn(num_cols -1, ProgressBarDelegate(self))
        # self.setItemDelegateForColumn(num_cols -2 , PixmapDelegate(self))
        self.setItemDelegateForColumn(self.pmap_col, PixmapDelegate(self))
        self.setItemDelegateForColumn(self.prog_col, ProgressBarDelegate(self))


    def set_header(self, hdr_list):
        self.model().set_header(hdr_list)
        self.hdr_list = hdr_list
        self.init_delegates()

    def remove_model(self):
        self.model().removeAll()

    def set_model(self, model):
        self.model().set_model(model)

    def set_model_column_defaults(self):
        """
        set_model_column_defaults(): description

        :returns: None
        """
        self.model().set_col_readonly(0)
        for i in range(1,len(self.hdr_list)):
            self.horizontalHeader().setSectionResizeMode(i, QtWidgets.QHeaderView.Stretch)


class ProgressBarDelegate(QtWidgets.QItemDelegate):
    """
    A delegate that places a fully functioning QProgressBar in every
    cell of the column to which it's applied

    The formatting of the scan_prog progress bar is done in teh QProgresbar stylesheet
    """
    def __init__(self, parent):

        QtWidgets.QItemDelegate.__init__(self, parent)
        self.prog_status = scan_status_types.STOPPED

    def createEditor(self, parent, option, index):
        pbar = QtWidgets.QProgressBar(parent)
        pbar.setObjectName('scan_progbar')
        pbar.setMinimumWidth(150)
        pbar.setMaximumHeight(15)
        pbar.setRange(0,100)
        #pbar.textAlignment = Qt.AlignCenter
        pbar.setValue(10)
        #self.connect(pbar, SIGNAL("toggled(bool)"), self, SLOT("on_toggled()"))
        return pbar


    def setEditorData(self, editor, index):
        editor.blockSignals(True)
        data = index.model().data(index, QtCore.Qt.DisplayRole)
        editor.setValue(data)

        if(data == 0.0):
            editor.setStyleSheet("*::chunk{ background-color: %s }" % master_colors['app_drkgray'])
            editor.setStyleSheet("*{ color: %s }" % master_colors['white'])
        elif(data < 100.0):
            editor.setStyleSheet("*::chunk{ background-color: %s }" % master_colors['scan_sts_blue'])
            editor.setStyleSheet("*{ color: %s }" % master_colors['white'])

        elif(data >= 100.0):
            editor.setStyleSheet("*{ color: %s } \n *::chunk{ background-color: %s }" % (master_colors['app_blue'], master_colors['app_drkgray']))
            #editor.setStyleSheet("*{ color: %s }" % master_colors['app_blue'])
        else:
            pass

        editor.blockSignals(False)

    def setModelData(self, editor, model, index):
        data = index.model().data(index, QtCore.Qt.DisplayRole)
        model.setData(index, data, QtCore.Qt.EditRole)

    @QtCore.pyqtSlot()
    def on_toggled(self):
        self.commitData.emit(self.sender())


def get_pixmap(fname):
    pmap = QtGui.QPixmap(fname)
    #pmap.scaled(64, 64)#, aspectRatioMode=Qt_IgnoreAspectRatio, transformMode=Qt_FastTransformation)
    pmap = pmap.scaled(QtCore.QSize(16,16),  QtCore.Qt.KeepAspectRatio)
    return(pmap)

class PixmapDelegate(QtWidgets.QItemDelegate):
    """
    A delegate that places a fully functioning QProgressBar in every
    cell of the column to which it's applied

    need an icon for each status
    scan_status_types = Enum('STOPPED', 'PAUSED', 'RUNNING', 'ABORTED', 'DONE')
    """
    def __init__(self, parent):

        QtWidgets.QItemDelegate.__init__(self, parent)

        self.dir = iconsDir
        self.psize = '64x64'
        self.pause_clr = 'yellow'
        self.running_clr = 'blue'
        self.stopped_clr = 'gray'
        self.aborted_clr = 'red'
        self.done_clr = 'blue'

        self.paused_pmap = get_pixmap(os.path.join(self.dir, self.pause_clr, self.psize, 'pause.png'))
        self.running_pmap = get_pixmap(os.path.join(self.dir, self.running_clr, self.psize, 'loop.png'))
        self.stopped_pmap = get_pixmap(os.path.join(self.dir, self.stopped_clr, self.psize, 'stop.png'))
        self.aborted_pmap = get_pixmap(os.path.join(self.dir, self.aborted_clr, self.psize, 'flag.png'))
        self.done_pmap = get_pixmap(os.path.join(self.dir, self.done_clr, self.psize, 'check.png'))

        self.pmap = self.paused_pmap

    def createEditor(self, parent, option, index):
        label = QtWidgets.QLabel(parent)
        label.setMaximumHeight(15)
        self.pmap = self.paused_pmap
        label.setPixmap(self.pmap)
        return(label)

    def get_cur_pixmap(self):
        return(self.pmap)

    def set_cur_pixmap(self, pmap):
        self.pmap = pmap

    def setEditorData(self, editor, index):
        '''
        scan_status_types = Enum('STOPPED', 'PAUSED', 'RUNNING', 'ABORTED', 'DONE')
        '''
        editor.blockSignals(True)
        data = int(index.model().data(index, QtCore.Qt.DisplayRole))
        if(data == scan_status_types.STOPPED):
            editor.setPixmap(self.stopped_pmap)
        elif(data == scan_status_types.PAUSED):
            editor.setPixmap(self.paused_pmap)
        elif(data == scan_status_types.RUNNING):
            editor.setPixmap(self.running_pmap)
        elif(data == scan_status_types.ABORTED):
            editor.setPixmap(self.aborted_pmap)
        elif(data == scan_status_types.DONE):
            editor.setPixmap(self.done_pmap)
        else:
            _logger.error('scan status [%d] not supported' % data)
        editor.update()
        editor.blockSignals(False)

    def setModelData(self, editor, model, index):
        data = index.model().data(index, QtCore.Qt.DisplayRole)
        model.setData(index, data, QtCore.Qt.EditRole)



class ScanQueueTableWidget(QtWidgets.QWidget):
    #def __init__(self, parent=None, **kwargs):
    #    QtWidgets.QWidget.__init__(parent)
    total_prog = QtCore.pyqtSignal(float)

    def __init__(self, kwargs={}, parent=None):
        super(ScanQueueTableWidget, self).__init__(parent)
        
        # setGeometry(x_pos, y_pos, width, height)
        self.setGeometry(300, 200, 870, 450)
        header = [' File', ' eV', 'Pol', 'Range', '# Points', '', ' Progress']

        # self.set_pixmap_column(DEFAULT_PIXMAP_COLUMN)
        # self.set_progress_column(DEFAULT_PROGESS_BAR_COLUMN)

        self.max_progress_val = 0.0
        self.total_progress_cntr = 0.0

        self.fname_list = []
        self.spid_to_row_dct = {}
        # use numbers for numeric data to sort properly
        data_list = []
        table_model = ScanQTableModel(self, data_list, header)
        table_view = ScanQTableView(header, prog_col=DEFAULT_PROGESS_BAR_COLUMN, pmap_col=DEFAULT_PIXMAP_COLUMN)
        table_view.setModel(table_model)

        for row in range(0, table_model.rowCount()):
            table_view.openPersistentEditor(table_model.index(row, self.prog_col))
            table_view.openPersistentEditor(table_model.index(row, self.pmap_col))
            table_view.setRowHeight(row, 15)

            #['A1-00001.hdf5', 383.0, 'Circ Left', '50.7,46.4', '100x100', 11, 0],
            table_view.setColumnWidth(0, FILENAME_WIDTH)
            table_view.setColumnWidth(1, EV_WIDTH)
            table_view.setColumnWidth(2, POLARITY_WIDTH)
            table_view.setColumnWidth(3, CENTER_WIDTH)
            table_view.setColumnWidth(4, NPOINTS_WIDTH)
            table_view.setColumnWidth(5, PMAP_WIDTH)
            table_view.setColumnWidth(6, PROGRESS_WIDTH)

        self.table_view = table_view
        # set font
        #font = table_view.font()
        #font.setPointSizeF(7)
        font = QtGui.QFont("Courier New", TABLE_FONT_SIZE)
        table_view.setFont(font)
        # set column width to fit contents (set font first!)
        #table_view.resizeColumnsToContents()
        # enable sorting
        table_view.setSortingEnabled(False)

        self.set_pixmap_column(DEFAULT_PIXMAP_COLUMN)
        self.set_progress_column(DEFAULT_PROGESS_BAR_COLUMN)

        self.styleBtn = QtWidgets.QPushButton('Update Style')
        self.styleBtn.clicked.connect(self.on_update_style)

        self.loadScanBtn = QtWidgets.QPushButton('Load Scan')
        self.loadScanBtn.clicked.connect(self.openfile)

        self.dirLabel = QtWidgets.QLabel('Directory: ')
        font = self.dirLabel.font()
        font.setBold(True)
        self.dirLabel.setFont(font)

        #self.thumbnailLbl = QtWidgets.QLabel()
        #self.thumbnailLbl.setMinimumSize(150, 150)
        #pmap = QtGui.QPixmap(r'C:\\controls\\py2.7\\Beamlines\\sm\\stxm_control\\widgets\\icons\\black.jpg')
        #pmap = pmap.scaled(QtCore.QSize(150,150),  QtCore.Qt.KeepAspectRatio)
        #self.thumbnailLbl.setPixmap(pmap)

        layout = QtWidgets.QVBoxLayout(self)
        hlayout = QtWidgets.QHBoxLayout()

        hlayout.addWidget(table_view)
        hlayout.setContentsMargins(0,0,0,0)
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self.dirLabel)
        layout.addLayout(hlayout)

        if('local_test' in list(kwargs.keys())):
            self.rowFld = QtWidgets.QLineEdit("0")
            self.rowFld.setToolTip('Row Field')
            self.rowFld.returnPressed.connect(self.on_set_row)
            self.progFld = QtWidgets.QLineEdit("0")
            self.progFld.setToolTip('Progress Field')
            self.progFld.returnPressed.connect(self.on_set_progress)
            self.pmapFld = QtWidgets.QLineEdit("0")
            self.pmapFld.setToolTip('Pixmap Field')
            self.pmapFld.returnPressed.connect(self.on_set_pixmap)

            layout.addWidget(self.loadScanBtn)
            layout.addWidget(self.rowFld)
            layout.addWidget(self.progFld)
            layout.addWidget(self.pmapFld)

        #table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        table_view.horizontalHeader().setStretchLastSection(True)

        self.file_suffix = 'hdf5'

    def on_set_row(self):
        row = int(str(self.rowFld.text()))
        self.scroll_to_row(row)

    def on_set_progress(self):
        row = int(str(self.rowFld.text()))
        val = float(str(self.progFld.text()))
        self.set_progress(row, val)
        self.update_total_progress()

    def update_total_progress(self):
        ttl = self.table_view.get_total_progress()
        #print 'ttl=', ttl
        #print 'self.max_progress_val=',self.max_progress_val
        prcnt = float(ttl/self.max_progress_val) * 100.0
        self.total_prog.emit(prcnt)

    def on_set_pixmap(self):
        row = int(str(self.rowFld.text()))
        val = int(str(self.pmapFld.text()))
        self.set_pixmap(row, val)

    def set_directory_label(self, dirname):
        self.dirLabel.setText('Directory: %s' % dirname)

    def set_progress_column(self, col):
        """
        set it for both the TableView and the Model
        """
        #print('ScanQueueTableWidget: set_progress_column=%d' % col)
        self.blockSignals(True)
        self.table_view.set_prog_col(col)
        model = self.table_view.model()
        model.set_prog_col(col)
        self.prog_col = col
        self.blockSignals(False)

    def set_pixmap_column(self, col):
        #print('ScanQueueTableWidget: set_pixmap_column=%d' % col)
        self.blockSignals(True)
        self.table_view.set_pmap_col(col)
        model = self.table_view.model()
        model.set_pmap_col(col)
        self.pmap_col = col
        self.blockSignals(False)


    def set_queue_file_list(self, fnames):
        '''
    	assign the file names that will be displayed in th table. Sometimes the filenames are generated

    	'''
        self.fname_list = fnames

    def on_update_style(self):
        """ handler for interactive button """
        self.qssheet = get_style('dark')
        self.setStyleSheet(self.qssheet)

    def scroll_to_row_with_spid(self, sp_id):
        if(sp_id in list(self.spid_to_row_dct.keys())):
            row = self.spid_to_row_dct[sp_id]
            #print 'scroll_to_row_with_spid: row=%d' % row
            self.scroll_to_row(row)
            return(row)
        else:
            #hack
            if(len(list(self.spid_to_row_dct.keys()) ) is 1):
                self.scroll_to_row(0)
                return (0)
            else:
                _logger.error('scroll_to_row_with_spid: sp_id[%d] does not exist in table' % sp_id)
                #print self.spid_to_row_dct

    def scroll_to_row(self, row):
        if row > -1:
            h = self.table_view.horizontalHeader()
            for i in range(h.count()):
                if not h.isSectionHidden(i) and h.sectionViewportPosition(i) >= 0:
                    self.table_view.scrollTo(self.table_view.model().index(row, i), self.table_view.PositionAtCenter)
                    self.table_view.setCurrentIndex(self.table_view.model().index(row, i))
                    break

    def set_progress(self, row, val):
        '''
        examples of setting a global model and it will signal the tablemodel and tableview that it has changed
        '''
        global scan_q_model_class

#         sp_id=0
#         row = self.scroll_to_row_with_spid(sp_id)
#         dct = make_progress_dict(sp_id=sp_id, percent=val)
#         self.set_progress_by_spid(dct)

        self.scroll_to_row(row)
        scan_q_model_class.set_data(row, self.prog_col, val)
        if(val > 90.0):
            scan_q_model_class.set_data(row, self.pmap_col, scan_status_types.DONE)

        self.update_total_progress()
        #always change focus off of widget
        #self.dirLabel.setFocus()

    def set_progress_by_spid(self, sp_id, val, idx=0):
#    def set_progress_by_spid(self, prog_dct={PROG_DCT_ID: 'INVALID'}):
        '''
        dct_put(dct, PROG_DCT_ID, PROG_DCT_ID)
        dct_put(dct, PROG_DCT_SPID, sp_id)
        dct_put(dct, PROG_DCT_PERCENT, percent)

        examples of setting a global model and it will signal the tablemodel and tableview that it has changed
        '''
        global scan_q_model_class
#         if(dct_get(prog_dct, PROG_DCT_ID) is not PROG_DCT_ID):
#             _logger.error('Unsupported dict type')
#             return
#         sp_id = dct_get(prog_dct, PROG_DCT_SPID)
#         val = dct_get(prog_dct, PROG_DCT_PERCENT)
        #val = float(str(self.progFld.text()))
        #self.table_view.set_progress(0, val)
        #m_markersProjectionTableView->scrollTo( indexList[0], QAbstractItemView::EnsureVisible);
        row = self.scroll_to_row_with_spid(sp_id)
        if(row > -1):
            scan_q_model_class.set_data(row, self.prog_col, val)
            if(val > 90.0):
                scan_q_model_class.set_data(row, self.pmap_col, scan_status_types.DONE)

        # always change focus off of widget
        #self.dirLabel.setFocus()

    def set_pixmap(self, row, val):
        '''
        examples of setting a global model and it will signal the tablemodel and tableview that it has changed
        scan_status_types = Enum('STOPPED', 'RUNNING', 'PAUSED', 'DONE', 'ABORTED')
        '''

        global scan_q_model_class

        self.scroll_to_row(row)
        choices = scan_status_types.get_choices()
        if(val < 0):
            val = 0
        if(val > len(choices)):
            val = len(choices)
        #self.table_view.set_pixmap(0, val)
        scan_q_model_class.set_data(row, self.pmap_col, val)
        # always change focus off of widget
        #self.dirLabel.setFocus()


    def set_pixmap_by_spid(self, sp_id, val):
        '''
        examples of setting a global model and it will signal the tablemodel and tableview that it has changed
        scan_status_types = Enum('STOPPED', 'RUNNING', 'PAUSED', 'DONE', 'ABORTED')
        '''

        global scan_q_model_class

        row = self.scroll_to_row_with_spid(sp_id)
        if(row):
            #val = int(str(self.pmapFld.text()))
            choices = scan_status_types.get_choices()
            if(val < 0):
                val = 0
            if(val > len(choices)):
                val = len(choices)
            #self.table_view.set_pixmap(0, val)
            scan_q_model_class.set_data(row, self.pmap_col, val)
            # always change focus off of widget
            #self.dirLabel.setFocus()


    def openfile(self):
        """
        openfile(): description

        :param fname: fname description
        :type fname: fname type

        :param addimages=False: addimages=False description
        :type addimages=False: addimages=False type

        :returns: None
        """
        from cls.appWidgets.dialogs import getOpenFileName

        fname = getOpenFileName("Open hdf5 file", filter_str="hdf5 Files (*.hdf5)", search_path=r'S:\STXM-data\Cryo-STXM\2019\guest\0207')
        if(fname):

            fname = str(fname)
            data_dir, fprefix, fsuffix = get_file_path_as_parts(fname)
            if(data_dir is None):
                _logger.error('Problem with file [%s]' % fname)
                return
            self.set_directory_label(data_dir)
            self.file_suffix = fsuffix[1:]

            data_io = STXMDataIo(data_dir, fprefix)
            entry_dct = data_io.load()
            ekey = list(entry_dct.keys())[0]
            wdg_com = data_io.get_wdg_com_from_entry(entry_dct, ekey)
            #wdg_com = dct_get(ado_obj, ADO_CFG_WDG_COM)
            self.load_wdg_com(wdg_com, sp_ids=list(wdg_com['SPATIAL_ROIS'].keys()))

    def clear_table(self):
        self.table_view.remove_model()

    def get_row_count(self):
        return(self.table_view.model().rowCount())

    def load_wdg_com(self, wdg_com, sp_ids=[]):
        '''
        take an widget communications obj and create a scan queue which is a list of
        '''
        #return
        #sp_roi_dct = dct_get(wdg_com, WDGCOM_SPATIAL_ROIS)
        #sp_ids = sp_roi_dct.keys()

        scan_q_list, scan_type = self.wdg_com_to_scan_queue(wdg_com, sp_ids)
        if(scan_q_list):
            self.table_view.remove_model()
            self.table_view.set_model(scan_q_list)
            self.set_delegates(scan_type)
            #print scan_q_list

    def wdg_com_to_scan_queue(self, wdg_com, sp_ids=[]):
        '''
        take a list of sp_ids and creat eall of hte rows that we need in the table view,
        if there are more than one sp_id then it is a multi region scan so the sp_dbs need to be interleaved in the
        list because the way the scan is executed is that the beamline optics are set (ev, pol, etc) then each
        spatial region is scanned, so the spatial regions need to appear one after the other
        :param wdg_com:
        :param sp_ids:
        :return:
        '''
        self.max_progress_val = 0.0
        spdb_lst = []
        scan_queue_list = []
        scan_type = None
        if(wdg_com is not None):

            for sp_id in sp_ids:
                sp_db = get_sp_db_from_wdg_com(wdg_com, sp_id)
                #sp_ids = get_sp_ids_from_wdg_com(wdg_com)
                scan_queue_list = []
                self.spid_to_row_dct = {}
                row = 0
                # sp_db = get_sp_db_from_wdg_com(wdg_com, sp_id)
                row_entry_list, scan_type = self.make_scan_queue_list(sp_db)
                spdb_lst.append(row_entry_list)
                if(row_entry_list):
                    ado = dct_get(sp_db, SPDB_ACTIVE_DATA_OBJECT)
                    fname = dct_get(ado, ADO_CFG_DATA_FILE_NAME)
                    self.spid_to_row_dct[sp_db[SPDB_ID_VAL]] = row
                    scan_queue_list = scan_queue_list + row_entry_list
                    row += 1
                else:
                    return(None, scan_type)



        if(len(spdb_lst) > 1):
            if (scan_type == scan_types.TOMOGRAPHY_SCAN):
                scan_queue_list = []
                for i in range(len(spdb_lst)):
                    sp = spdb_lst[i]
                    for j in range(len(sp)):
                        scan_queue_list.append(sp[j])

            else:
                scan_queue_list = merge_to_one_list(spdb_lst)

            _cntr = 0
            for l in scan_queue_list:
                # the filename is the first in the list
                fname = l[0]
                f_idx = fname.find('img/')
                if(f_idx > -1):
                    #replace img index
                    l[0] = fname[:f_idx] + 'img/%d' % _cntr
                _cntr += 1
            #now modify the fnames so that they are sequentially correct


        return(scan_queue_list, scan_type)

    def set_delegates(self, scan_type):
        '''
        the delegate setting function, using the scan_type call the appropriate delegate setter function
        '''
        if(scan_type == scan_types.DETECTOR_IMAGE):
            self.set_delegates_ev()

        elif(scan_type == scan_types.OSA_IMAGE):
            self.set_delegates_ev()

        elif(scan_type == scan_types.OSA_FOCUS):
            self.set_delegates_focus()

        elif(scan_type == scan_types.SAMPLE_FOCUS):
            self.set_delegates_focus()

        elif(scan_type == scan_types.SAMPLE_IMAGE):
            self.set_delegates_multi_ev()

        elif(scan_type == scan_types.SAMPLE_IMAGE_STACK):
            self.set_delegates_multi_ev()

        elif(scan_type == scan_types.TOMOGRAPHY_SCAN):
            self.set_delegates_tomo()

        elif(scan_type == scan_types.SAMPLE_POINT_SPECTRUM):
            self.set_delegates_point_spec()

        elif(scan_type == scan_types.COARSE_IMAGE_SCAN):
            self.set_delegates_ev()

        elif (scan_type == scan_types.COARSE_GONI_SCAN):
            self.set_delegates_ev()

        elif(scan_type == scan_types.SAMPLE_LINE_SPECTRUM):
            self.set_delegates_line_spec()

        elif(scan_type == scan_types.GENERIC_SCAN):
            self.set_delegates_ev()
        else:
            print('set_delegates: scan type not supported yet [%d]' % scan_type)
            return

    def make_scan_queue_list(self, sp_db):
        '''
        take an entire spatial region and create the appropriate number of row entries
        scan_types = Enum('Detector_Image', \
                'OSA_Image', \
                'OSA_Focus', \
                'Sample_Focus', \
                'Sample_Point_Spectrum', \
                'Sample_Line_Spectrum', \
                'Sample_Image', \
                'Sample_Image_Stack', \
                'Tomography_Scan', \
                'Generic_Scan', \
                'Coarse_Image_Scan')
        '''

        scan_type = dct_get(sp_db, SPDB_SCAN_PLUGIN_TYPE)


        if(scan_type == scan_types.DETECTOR_IMAGE):
            rows = self.make_single_ev_row_entries(sp_db)

        elif(scan_type == scan_types.OSA_IMAGE):
            rows = self.make_single_ev_row_entries(sp_db)

        elif(scan_type == scan_types.OSA_FOCUS):
            rows = self.make_focus_row_entries(sp_db)

        elif(scan_type == scan_types.SAMPLE_FOCUS):
            rows = self.make_focus_row_entries(sp_db)

        elif(scan_type == scan_types.SAMPLE_IMAGE):
            rows = self.make_single_ev_row_entries(sp_db)

        elif(scan_type == scan_types.SAMPLE_IMAGE_STACK):
            rows = self.make_multi_ev_row_entries(sp_db, stack_dir=True)

        elif (scan_type == scan_types.TOMOGRAPHY_SCAN):
            rows = self.make_multi_ev_with_theta_row_entries(sp_db, stack_dir=True)

        elif(scan_type == scan_types.COARSE_IMAGE_SCAN):
            rows = self.make_single_ev_row_entries(sp_db)

        elif (scan_type == scan_types.COARSE_GONI_SCAN):
            rows = self.make_single_ev_row_entries(sp_db)

        elif(scan_type == scan_types.SAMPLE_POINT_SPECTRUM):
            rows = self.make_point_scan_row_entries(sp_db)

        elif(scan_type == scan_types.SAMPLE_LINE_SPECTRUM):
            rows = self.make_single_ev_row_entries(sp_db, show_ev_range=True)
            #return None, scan_type

        elif(scan_type == scan_types.GENERIC_SCAN):
            rows = self.make_single_ev_row_entries(sp_db)
        else:
            print('make_scan_queue_list: scan type not supported yet [%d]' % scan_type)
            return None, scan_type


        for r in rows:
            self.max_progress_val += 100.0
        self.total_progress_cntr = 0.0

        return(rows, scan_type)

    def set_delegates_ev(self):
        '''
        header = ['Filename', ' eV', 'Pol', 'Range', '# Points', '', ' Progress']

        ['A1-00001.hdf5', 383.0, 'Circ Left', '50.7 x 46.4 um', '100x100', 0, 11],
        '''
        tm = self.table_view.model()
        for row in range(0, tm.rowCount()):
            self.table_view.openPersistentEditor(tm.index(row, self.prog_col))
            self.table_view.openPersistentEditor(tm.index(row, self.pmap_col))
            #self.table_view.setRowHeight(row, 15)

        #['A1-00001.hdf5', 383.0, 'Circ Left', '50.7,46.4', '100x100', 11, 0],
        self.table_view.setColumnWidth(0, FILENAME_WIDTH)
        self.table_view.setColumnWidth(1, EV_WIDTH)
        self.table_view.setColumnWidth(2, POLARITY_WIDTH)
        self.table_view.setColumnWidth(3, CENTER_WIDTH)
        self.table_view.setColumnWidth(4, NPOINTS_WIDTH)
        self.table_view.setColumnWidth(self.pmap_col, PMAP_WIDTH)
        self.table_view.setColumnWidth(self.prog_col, PROGRESS_WIDTH)

    def set_delegates_multi_ev(self):
        '''
        header = ['Filename', ' eV', 'Pol', 'Range', '# Points', '', ' Progress']

        ['A1-00001.hdf5', 383.0, 'Circ Left', '50.7 x 46.4 um', '100x100', 0, 11],
        '''
        tm = self.table_view.model()
        for row in range(0, tm.rowCount()):
            self.table_view.openPersistentEditor(tm.index(row, self.prog_col))
            self.table_view.openPersistentEditor(tm.index(row, self.pmap_col))
            #self.table_view.setRowHeight(row, 15)

        #['A1-00001.hdf5', 383.0, 'Circ Left', '50.7,46.4', '100x100', 11, 0],
        self.table_view.setColumnWidth(0, STACK_FILENAME_WIDTH)
        self.table_view.setColumnWidth(1, EV_WIDTH)
        self.table_view.setColumnWidth(2, POLARITY_WIDTH)
        self.table_view.setColumnWidth(3, CENTER_WIDTH)
        self.table_view.setColumnWidth(4, NPOINTS_WIDTH)
        self.table_view.setColumnWidth(self.pmap_col, PMAP_WIDTH)
        self.table_view.setColumnWidth(self.prog_col, PROGRESS_WIDTH)

    def set_delegates_tomo(self):
        '''
        header = ['Filename', ' eV', 'Pol', 'Range', '# Points', '', ' Progress']

        ['A1-00001.hdf5', 383.0, 'Circ Left', '50.7 x 46.4 um', '100x100', 0, 11],
        '''
        tm = self.table_view.model()
        for row in range(0, tm.rowCount()):
            self.table_view.openPersistentEditor(tm.index(row, self.prog_col))
            self.table_view.openPersistentEditor(tm.index(row, self.pmap_col))
            #self.table_view.setRowHeight(row, 15)

        #['A1-00001.hdf5', 383.0, 'Circ Left', '50.7,46.4', '100x100', 11, 0],
        self.table_view.setColumnWidth(0, STACK_FILENAME_WIDTH)
        self.table_view.setColumnWidth(1, EV_WIDTH)
        self.table_view.setColumnWidth(2, POLARITY_WIDTH)
        self.table_view.setColumnWidth(3, TOMO_WIDTH)
        self.table_view.setColumnWidth(4, NPOINTS_WIDTH)
        self.table_view.setColumnWidth(self.pmap_col, PMAP_WIDTH)
        self.table_view.setColumnWidth(self.prog_col, PROGRESS_WIDTH)

    def set_delegates_point_spec(self):
        '''
        header = [' File', ' Start eV', 'Stop eV', 'Pol', 'Center', '# Points', '', ' Progress']

        ['A1-00001.hdf5', 383.0, 393.0, 'Circ Left', '50.7 x 46.4 um', '100x100', 0, 11],
        '''
        tm = self.table_view.model()
        for row in range(0, tm.rowCount()):
            self.table_view.openPersistentEditor(tm.index(row, self.prog_col))
            self.table_view.openPersistentEditor(tm.index(row, self.pmap_col))
            #self.table_view.setRowHeight(row, 15)

        #['A1-00001.hdf5', 383.0, 'Circ Left', '50.7,46.4', '100x100', 11, 0],
        self.table_view.setColumnWidth(0, FILENAME_WIDTH)
        self.table_view.setColumnWidth(1, EV_WIDTH)
        self.table_view.setColumnWidth(2, EV_WIDTH)
        self.table_view.setColumnWidth(3, POLARITY_WIDTH)
        self.table_view.setColumnWidth(4, CENTER_WIDTH)
        self.table_view.setColumnWidth(5, NPOINTS_WIDTH)
        self.table_view.setColumnWidth(self.pmap_col, PMAP_WIDTH)
        self.table_view.setColumnWidth(self.prog_col, PROGRESS_WIDTH)

    def set_delegates_line_spec(self):
        '''
        header = [' File', ' Start eV', 'Stop eV', 'Pol', 'Center', '# Points', '', ' Progress']

        ['A1-00001.hdf5', 383.0, 393.0, 'Circ Left', '50.7 x 46.4 um', '100x100', 0, 11],
        '''
        tm = self.table_view.model()
        for row in range(0, tm.rowCount()):
            self.table_view.openPersistentEditor(tm.index(row, self.prog_col))
            self.table_view.openPersistentEditor(tm.index(row, self.pmap_col))
            #self.table_view.setRowHeight(row, 15)

        #['A1-00001.hdf5', 383.0, 'Circ Left', '50.7,46.4', '100x100', 11, 0],
        self.table_view.setColumnWidth(0, FILENAME_WIDTH)
        self.table_view.setColumnWidth(1, 2.5 * EV_WIDTH)
        self.table_view.setColumnWidth(2, EV_WIDTH)
        self.table_view.setColumnWidth(3, POLARITY_WIDTH + 35)
        self.table_view.setColumnWidth(4, CENTER_WIDTH + 25)
        self.table_view.setColumnWidth(5, NPOINTS_WIDTH)
        self.table_view.setColumnWidth(self.pmap_col, PMAP_WIDTH)
        self.table_view.setColumnWidth(self.prog_col, PROGRESS_WIDTH)

    def set_delegates_focus(self):
        '''
        ['A1-00001.hdf5', -2100.00, '-1900.00', '1.235', '100', 0, 11],
        header = ['Filename', ' Z Start', 'Z Stop', 'Z Step', 'Z #pts', '', ' Progress']
        '''
        tm = self.table_view.model()
        for row in range(0, tm.rowCount()):
            #self.table_view.setRowHeight(row, 15)
            self.table_view.openPersistentEditor(tm.index(row, self.prog_col))
            self.table_view.openPersistentEditor(tm.index(row, self.pmap_col))
            #['A1-00001.hdf5', 383.0, 'Circ Left', '50.7,46.4', '100x100', 11, 0],

        self.table_view.setColumnWidth(0, FILENAME_WIDTH)
        self.table_view.setColumnWidth(1, START_WIDTH)
        self.table_view.setColumnWidth(2, START_WIDTH)
        self.table_view.setColumnWidth(3, START_WIDTH)
        self.table_view.setColumnWidth(4, NPOINTS_WIDTH)
        self.table_view.setColumnWidth(self.pmap_col, PMAP_WIDTH)
        self.table_view.setColumnWidth(self.prog_col, PROGRESS_WIDTH)

    def make_focus_row_entries(self, sp_db, sample_pos=1):
        '''
        Take an focus (OSA or sample) sp_db and create a row entry for a detector scan
        The results should be a single row entry:
        ['A1-00001.hdf5', 383.0, 'Circ Left', '50.7 x 46.4 um', '100x100', 0, 11],
        '''
        header = [' File', ' Zpz Start', 'Zpz Stop', 'Zpz Step', 'Zpz #Points', '', ' Progress']
        self.set_progress_column(6)
        self.set_pixmap_column(5)
        self.table_view.set_header(header)
        self.table_view.update()

        lst = []
        x_roi = dct_get(sp_db, SPDB_X)
        y_roi = dct_get(sp_db, SPDB_Y)
        #z_roi = dct_get(sp_db, SPDB_Z)
        zz_roi = dct_get(sp_db, SPDB_ZZ)
        e_rois = dct_get(sp_db, SPDB_EV_ROIS)
        # e_roi = e_rois[0]
        # numX = int(x_roi[NPOINTS])
        # numY = int(y_roi[NPOINTS])
        # numZ = int(zz_roi[NPOINTS])
        # numEpnts = int(dct_get(sp_db, SPDB_EV_NPOINTS))

        row_num = 0

        prfx = dct_get(sp_db, SPDB_SCAN_PLUGIN_DATAFILE_PFX)
        fname = self.make_fname(prfx, row_num, sample_pos)

        lst.append(fname)
        lst.append('%.2f' % zz_roi[START])
        lst.append('%.2f' % zz_roi[STOP])
        lst.append('%.2f um' % (zz_roi[STEP]))
        lst.append('%d' % (zz_roi[NPOINTS]))
        lst.append(0)
        lst.append(row_num)
        return([lst])

    def make_single_ev_row_entries(self, sp_db, sample_pos=1, show_ev_range=False):
        '''
        Take an single ev sp_db (detector, osa) and create a row entry for a detector scan
        The results should be a single row entry:
        ['A1-00001.hdf5', 383.0, 'Circ Left', '50.7 x 46.4 um', '100x100', 0, 11],
        '''
        header = [' File', ' eV', 'Pol', 'Range', '# Points', '', ' Progress']
        self.set_progress_column(6)
        self.set_pixmap_column(5)
        self.table_view.set_header(header)

        self.table_view.update()

        lst = []
        x_roi = dct_get(sp_db, SPDB_X)
        y_roi = dct_get(sp_db, SPDB_Y)
        #z_roi = dct_get(sp_db, SPDB_Z)
        e_rois = dct_get(sp_db, SPDB_EV_ROIS)
        first_e_roi = e_rois[0]
        last_e_roi = e_rois[-1]

        e_start = first_e_roi[START]

        # numX = int(x_roi[NPOINTS])
        # numY = int(y_roi[NPOINTS])
        # #numZ = int(z_roi[NPOINTS])
        # numEpnts = int(dct_get(sp_db, SPDB_EV_NPOINTS))

        row_num = 0

        #prfx = dct_get(sp_db, SPDB_SCAN_PLUGIN_DATAFILE_PFX)
        ado_obj = dct_get(sp_db, SPDB_ACTIVE_DATA_OBJECT)
        fname = dct_get(ado_obj, ADO_CFG_DATA_FILE_NAME)

        #fname = self.make_fname(prfx, row_num, sample_pos)

        if(not math.isnan(e_start)):

            lst.append(fname)
            if (show_ev_range):
                e_stop = last_e_roi[STOP]
                lst.append('%.2f -> %.2f' % (e_start, e_stop))
            else:
                lst.append('%.2f' % e_start)

            epu_str = convert_wrapper_epu_to_str(first_e_roi[EPU_POL_PNTS][0])
            lst.append('%s' % epu_str)
            lst.append('%.2f x %.2f um' % (x_roi[RANGE], y_roi[RANGE]))
            lst.append('%dx%d ' % (x_roi[NPOINTS], y_roi[NPOINTS]))
            lst.append(0)
            lst.append(row_num)

        return([lst])

    def make_point_scan_row_entries(self, sp_db, sample_pos=1):
        '''
        Take an single ev sp_db (detector, osa) and create a row entry for a detector scan
        The results should be a single row entry:
        ['A1-00001.hdf5', 383.0, 440.0, 'Circ Left', '50.7 x 46.4 um', '100', 0, 11],
        '''
        header = [' File', ' Start eV', 'Stop eV', 'Pol', 'Center', '# Points', '', ' Progress']

        self.set_progress_column(7)
        self.set_pixmap_column(6)

        self.table_view.set_header(header)
        # self.set_progress_column(7)
        # self.set_pixmap_column(6)
        # self.table_view.update()

        x_roi = dct_get(sp_db, SPDB_X)
        y_roi = dct_get(sp_db, SPDB_Y)
        #z_roi = dct_get(sp_db, SPDB_Z)
        e_rois = dct_get(sp_db, SPDB_EV_ROIS)

        # numX = int(x_roi[NPOINTS])
        # numY = int(y_roi[NPOINTS])
        # numZ = int(z_roi[NPOINTS])
        numEpnts = int(dct_get(sp_db, SPDB_EV_NPOINTS))

        row_num = 0

        prfx = dct_get(sp_db, SPDB_SCAN_PLUGIN_DATAFILE_PFX)
        ado_obj = dct_get(sp_db, SPDB_ACTIVE_DATA_OBJECT)
        fname = dct_get(ado_obj, ADO_CFG_DATA_FILE_NAME)

        if(len(e_rois) == 0):
            _logger.error('something wrong with teh e_roi here')
            return

        estart = e_rois[0][START]
        estop = e_rois[-1][STOP]
        pol  = e_rois[0][EPU_POL_PNTS][0]

        lst = []
        lst.append(fname)
        lst.append('%.2f' % estart)
        lst.append('%.2f' % estop)
        epu_str = convert_wrapper_epu_to_str(pol)
        lst.append('%s' % epu_str)
        lst.append('%.2f x %.2f um' % (x_roi[CENTER], y_roi[CENTER]))
        lst.append('%d ' % (numEpnts))
        lst.append(0)
        lst.append(row_num)

        return([ lst ])

    def make_multi_ev_row_entries(self, sp_db, sample_pos=1, is_point=False, stack_dir=False):
        '''
        Take an single ev sp_db (detector, osa) and create a row entry for a detector scan
        The results should be a single row entry:
        ['A1-00001.hdf5', 383.0, 'Circ Left', '50.7 x 46.4 um', '100x100', 0, 11],
        '''
        if (is_point):
            header = [' File', ' eV', 'Pol', 'Center', '# Points', '', ' Progress']

        else:
            header = [' File', ' eV', 'Pol', 'Range', '# Points', '', ' Progress']

        self.set_progress_column(6)
        self.set_pixmap_column(5)

        self.table_view.set_header(header)
        self.table_view.update()

        main_lst = []
        # scan_type = dct_get(sp_db, SPDB_SCAN_PLUGIN_TYPE)
        x_roi = dct_get(sp_db, SPDB_X)
        y_roi = dct_get(sp_db, SPDB_Y)
        # z_roi = dct_get(sp_db, SPDB_Z)
        e_rois = dct_get(sp_db, SPDB_EV_ROIS)

        # numX = int(x_roi[NPOINTS])
        # numY = int(y_roi[NPOINTS])
        # numZ = int(z_roi[NPOINTS])
        # numEpnts = int(dct_get(sp_db, SPDB_EV_NPOINTS))

        row_num = 0

        # prfx = dct_get(sp_db, SPDB_SCAN_PLUGIN_DATAFILE_PFX)
        ado_obj = dct_get(sp_db, SPDB_ACTIVE_DATA_OBJECT)
        # datafile_name = dct_get(ado_obj, ADO_CFG_DATA_FILE_NAME)

        idx = 0
        for e_roi in e_rois:
            for e in e_roi[SETPOINTS]:
                for pol in e_roi[EPU_POL_PNTS]:
                    lst = []
                    if (len(self.fname_list) > 0):
                        lst.append(self.fname_list[idx])
                    else:
                        lst.append('spatial_id %d' % sp_db[SPDB_ID_VAL])
                    # hack
                    if (type(e) is list):
                        e = e[0]
                    lst.append('%.2f' % e)
                    epu_str = convert_wrapper_epu_to_str(pol)
                    lst.append('%s' % epu_str)
                    if (is_point):
                        lst.append('%.2f x %.2f um' % (x_roi[CENTER], y_roi[CENTER]))
                    else:
                        lst.append('%.2f x %.2f um' % (x_roi[RANGE], y_roi[RANGE]))
                    lst.append('%dx%d ' % (x_roi[NPOINTS], y_roi[NPOINTS]))
                    lst.append(0)
                    lst.append(row_num)
                    main_lst.append(lst)
                    idx += 1
        return (main_lst)

    def make_multi_ev_with_theta_row_entries(self, sp_db, sample_pos=1, stack_dir=False):
        '''
        Take an single ev sp_db (detector, osa) and create a row entry for a detector scan
        The results should be a single row entry:
        ['A1-00001.hdf5', 383.0, 'Circ Left', '50.7 x 46.4 um', '100x100', 0, 11],
        '''
        header = [' File', ' eV', ' Pol', '(Gx, Gy,  Gtheta)', ' # Points', ' ', ' Progress']
        self.set_progress_column(6)
        self.set_pixmap_column(5)

        self.table_view.set_header(header)
        self.table_view.update()

        main_lst = []
        # scan_type = dct_get(sp_db, SPDB_SCAN_PLUGIN_TYPE)
        x_roi = dct_get(sp_db, SPDB_X)
        y_roi = dct_get(sp_db, SPDB_Y)
        # z_roi = dct_get(sp_db, SPDB_Z)
        e_rois = dct_get(sp_db, SPDB_EV_ROIS)
        gt_roi = dct_get(sp_db, SPDB_GT)

        # numX = int(x_roi[NPOINTS])
        # numY = int(y_roi[NPOINTS])
        # numZ = int(z_roi[NPOINTS])
        # numEpnts = int(dct_get(sp_db, SPDB_EV_NPOINTS))

        row_num = 0

        # prfx = dct_get(sp_db, SPDB_SCAN_PLUGIN_DATAFILE_PFX)
        #ado_obj = dct_get(sp_db, SPDB_ACTIVE_DATA_OBJECT)
        # datafile_name = dct_get(ado_obj, ADO_CFG_DATA_FILE_NAME)

        idx = 0
        for e_roi in e_rois:
            for e in e_roi[SETPOINTS]:
                for pol in e_roi[EPU_POL_PNTS]:
                    for gt in gt_roi[SETPOINTS]:
                        lst = []
                        if (len(self.fname_list) > 0):
                            lst.append(self.fname_list[idx])
                        else:
                            lst.append('spatial_id %d' % sp_db[SPDB_ID_VAL])
                        # hack
                        if (type(e) is list):
                            e = e[0]
                        lst.append('%.2f' % e)
                        epu_str = convert_wrapper_epu_to_str(pol)
                        lst.append('%s' % epu_str)
                        #lst.append('%.2f x %.2f um' % (x_roi[RANGE], y_roi[RANGE]))
                        lst.append('(%.2f, %.2f, %.2f' % (x_roi[CENTER], y_roi[CENTER], gt))
                        #if(gt_roi):
                        #    lst.append('%.2f deg' % (gt))

                        lst.append('%dx%d ' % (x_roi[NPOINTS], y_roi[NPOINTS]))
                        lst.append(0)
                        lst.append(row_num)
                        main_lst.append(lst)
                        idx += 1
        return (main_lst)

    def make_fname(self, prfx, row_num, sample_pos=1):
        fname = '%s%d-%05d%s' % (prfx, sample_pos, row_num, self.file_suffix)
        if (row_num < len(self.fname_list)):
            fname = self.fname_list[row_num]
            # fname = '%s' % (prfx,  row_num, self.file_suffix)
        return (fname)

    def make_image_fname(self, prfx, row_num, sample_pos=1):
        fname = '%s%d-%05d%s img/%d' % (prfx, sample_pos, 0, self.file_suffix, row_num)
        if (row_num < len(self.fname_list)):

    # fn = self.fname_list[row_num]

            fname = self.fname_list[row_num]
            #fname = '%s img/%d' % (fn, row_num)
        return(fname)



if __name__=="__main__":

    app = QtWidgets.QApplication([])

    win = ScanQueueTableWidget(kwargs={'local_test':True})
    #win = ScanQueueTableWidget()
    qssheet = get_style('dark')
    win.setStyleSheet(qssheet)
    win.show()
    #win.openfile()
    app.exec_()
