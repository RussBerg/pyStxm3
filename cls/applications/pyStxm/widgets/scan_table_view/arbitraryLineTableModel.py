'''
Created on Nov 16, 2016

@author: bergr
'''
from PyQt5 import QtCore, QtGui, QtWidgets
from cls.applications.pyStxm.widgets.scan_table_view.baseScanTable import *
from cls.utils.roi_dict_defs import *


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
            if (len(value) == 0):
                # the user didnt enter a value
                return True

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

