from PyQt5 import QtCore, QtGui, QtWidgets
from cls.applications.pyStxm.widgets.scan_table_view.baseScanTable import *
    
POLARIZATION_COLUMN_MAP = ['ID', 'POL', 'OFF', 'ANGLE']
POLARIZATION_POLARITY_CHANGED = [1]
POLARIZATION_OFFSET_CHANGED = [2]
POLARIZATION_LINEAR_ANGLE_CHANGED = [3]

class PolarizationTableModel(BaseScanTableModel):
    
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
        super(PolarizationTableModel, self).__init__(hdrList, datain, parent, *args)
        # a dict that will use spatial region scan_id's as key to EnergyRegionScanDef's 
        self.cur_scan_row = None
        self.scanListData = datain
        self.editable = False
        self.column_map = POLARIZATION_COLUMN_MAP
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
        print('Polarization model: role = %d' % role)
        if(role == QtCore.Qt.EditRole):
            if(type(value) is str):
                if (len(value) == 0):
                    # the user didnt enter a value
                    return True

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
                    
                scan[POLARIZATION_COLUMN_MAP[col]] = val
            
        if((role == QtCore.Qt.EditRole) or (role == QtCore.Qt.DisplayRole)):
            #must emit this as part of the framework support for an editable AbstractTableModel
            scan = self.scanListData[row]
            self.dataChanged.emit(index, index)
            
            if(do_signal):
                #print 'EnergyScanTableModel: setData: emitting scan_changed'
                self.scan_changed.emit(row, scan)
                
            return True
