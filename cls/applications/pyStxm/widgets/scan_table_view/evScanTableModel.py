'''
Created on Nov 16, 2016

@author: bergr
'''
from PyQt5 import QtCore, QtGui, QtWidgets
from cls.applications.pyStxm.widgets.scan_table_view.baseScanTable import *
from cls.utils.roi_dict_defs import *

#need a mapping of table columns to roi dict key
EV_COLUMN_MAP = [ID, START, STOP, RANGE, NPOINTS, ROI_STEP, DWELL]
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
                #print 'EnergyScanTableModel: setData: emitting scan_changed'
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
                self.scanListData[row][START] = newscan[START]
                self.scanListData[row][STOP] = newscan[STOP]
                self.scanListData[row][CENTER] = newscan[CENTER] 
                self.scanListData[row][RANGE] = newscan[RANGE]
                self.scanListData[row][ROI_STEP] = newscan[ROI_STEP]
                self.scanListData[row][NPOINTS] = newscan[NPOINTS]
            row += 1        