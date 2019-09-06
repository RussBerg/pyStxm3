'''
Created on Jun 3, 2016

@author: bergr
'''

import sys
from PyQt5 import QtCore, QtGui, QtWidgets

#invalid_ss = 'QLineEdit{background: rgb(140, 177, 255);}'
invalid_ss = 'QLineEdit{background: rgb(195, 195, 195);}'
valid_ss = 'QLineEdit{background: rgb(255, 255, 255);}'

############################################################
class intParamValidator(QtGui.QIntValidator):
    #state_changed = pyqtSignal(object)
    def __init__(self, _min, _max, prec, qobj=None,lineFld=None):
        QtGui.QIntValidator.__init__(self)
        self.setRange(_min, _max)
        self.changes_locked = False
    
    def is_done(self):
        return(self.changes_locked)
        
    def lock_changes(self, lock):
        self.changes_locked = lock
        
#     def do_validate(self, input, pos):
#         state, pos = QtGui.QIntValidator.validate(self, input, pos)
#         if(input.isEmpty()):
#             return QtWidgets.QValidator.Intermediate, pos
#         
#         if((state == QtWidgets.QValidator.Intermediate) and input == '-'):
#             return QtWidgets.QValidator.Intermediate, pos
#         
#         if(state != QtWidgets.QValidator.Acceptable):
#             #print 'input invalid'
#             return QtWidgets.QValidator.Invalid, pos
#         else:
#             #print 'input acceptable'
#             return QtWidgets.QValidator.Acceptable, pos
                    
##############################################################
class dblParamValidator(QtGui.QDoubleValidator):
    #state_changed = pyqtSignal(object)
    def __init__(self, _min, _max, prec, qobj=None,lineFld=None):
        QtGui.QDoubleValidator.__init__(self)
        if((_min is None) or (_max is None)):
            print('dblParamValidator: _min or _max or both are None')
        else:
            self.setRange(_min, _max, prec)
        self.changes_locked = False
    
    def is_done(self):
        return(self.changes_locked)
        
    def lock_changes(self, lock):
        self.changes_locked = lock
        
#     def do_validate(self, input, pos):
#         state, pos = QtGui.QDoubleValidator.validate(self, input, pos)
#         if(input.isEmpty() or input == '.'):
#             return QtWidgets.QValidator.Intermediate, pos
#         
#         if((state == QtWidgets.QValidator.Intermediate) and input == '-'):
#             return QtWidgets.QValidator.Intermediate, pos
#         
#         if(state != QtWidgets.QValidator.Acceptable):
#             #print 'input invalid'
#             return QtWidgets.QValidator.Invalid, pos
#         else:
#             #print 'input acceptable'
#             return QtWidgets.QValidator.Acceptable, pos

##################################################################
class intLineEditParamObj(QtCore.QObject):
    valid_returnPressed = QtCore.pyqtSignal()
    
    def __init__(self, id, _min, _max, prec=0, parent=None):
        QtCore.QObject.__init__(self)
        self.parent = parent
        self.id = id
        self.cur_val = (_min + _max)/2.0
        self.prec = prec
        self._min = _min
        self._max = _max
        
        #self.parent.setText('%d' % ((_min + _max)/2.0))
        self.parent.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.parent.customContextMenuRequested.connect(self.contextMenuEvent)
        self.fmt = '%d'

        self.parent.focusInEvent = self.focusInEvent
        self.parent.focusOutEvent = self.focusOutEvent
        
        #self.parent.setToolTip('Valid range: from %d to %d' % (_min, _max))
        
        self.parent.returnPressed.connect(self.on_int_parent_rtrn_pressed)
        self.parent.textEdited.connect(self.on_int_parent_changed)
        
        v = intParamValidator(_min, _max, None)
        self.parent.setValidator(v)
    
    def contextMenuEvent(self, event):
        fld = self.sender()
        if(fld):
            if((self._min is not None) and (self._max is not None)):
                ma_str = 'valid range is between %d and %d' % (self._min, self._max)
            else:
                ma_str = 'Motor not connected'
                
            self.menu = QtWidgets.QMenu(self.parent)
            renameAction = QtWidgets.QAction(ma_str, self.parent)
            renameAction.triggered.connect(self.renameSlot)
            self.menu.addAction(renameAction)
            # add other required actions
            self.menu.popup(QtGui.QCursor.pos())
    
    def renameSlot(self):
        print("renaming slot called")
        # get the selected cell and perform renaming    
                
    def focusInEvent(self, event):
        ''' when focus goes into field copy current value'''
        self.cur_val = int(str(self.parent.text())) 
        #self.cur_val = float(str(self.text()))
        QtWidgets.QLineEdit.focusInEvent(self.parent, event)
        
    def focusOutEvent(self, event):
        ''' if user has not hit enter on the value in the field when 
        focus is lost on this field then return the value to its previous value
        and set the background color'''
        v = self.parent.validator()
        if(v.is_done()):
            #value is accepted
            self.cur_val = int(str(self.parent.text()))
        else:
            #value has not been accepted
            self.parent.setText(self.fmt % self.cur_val)
            
        self.parent.setStyleSheet(valid_ss) 
        QtWidgets.QLineEdit.focusOutEvent(self.parent, event)    
    
    def on_int_parent_rtrn_pressed(self):
        self.cur_val = int(str(self.parent.text()))
        #print 'saving [%.3f]' % self.cur_val
        v = self.parent.validator()
        v.lock_changes(True)
        self.parent.setStyleSheet(valid_ss)
        self.valid_returnPressed.emit()
    
    def on_int_parent_changed(self):
        v = self.parent.validator()
        v.lock_changes(False)
        ss = invalid_ss
        self.parent.setStyleSheet(ss)
        
####################################################################        
class dblLineEditParamObj(QtCore.QObject):
    valid_returnPressed = QtCore.pyqtSignal()
    
    def __init__(self, id, _min, _max, prec, parent=None):
        QtCore.QObject.__init__(self)
        self.parent = parent
        self.id = id
        if((_min is not None) and (_max is not None)):
            self.cur_val = (_min + _max)/2.0
        else:
            self.cur_val = 0.0
        self.prec = prec
        self._min = _min
        self._max = _max
        
        self.parent.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.parent.customContextMenuRequested.connect(self.contextMenuEvent)
        
        #self.parent.setText('%.2f' % ((_min + _max)/2.0))
        self.fmt = '%.' + '%df' % (self.prec)

        self.parent.focusInEvent = self.focusInEvent
        self.parent.focusOutEvent = self.focusOutEvent
        
        #self.parent.setToolTip('Valid range: from %.2f to %.2f' % (_min, _max))
        
        self.parent.returnPressed.connect(self.on_dbl_parent_rtrn_pressed)
        self.parent.textEdited.connect(self.on_dbl_parent_changed)
        
        v = dblParamValidator(_min, _max, self.prec, None)
        self.parent.setValidator(v)

    def contextMenuEvent(self, event):
        fld = self.sender()
        if(fld):
            if((self._min is not None) and (self._max is not None)):
                ma_str = 'valid range is between %.2f and %.2f' % (self._min, self._max)
            else:
                ma_str = 'Motor not connected'
                
            self.menu = QtWidgets.QMenu(self.parent)
            renameAction = QtWidgets.QAction(ma_str, self.parent)
            renameAction.triggered.connect(self.renameSlot)
            self.menu.addAction(renameAction)
            # add other required actions
            self.menu.popup(QtGui.QCursor.pos())
    
    def renameSlot(self):
        print("renaming slot called")
        # get the selected cell and perform renaming  
        
    def focusInEvent(self, event):
        ''' when focus goes into field copy current value'''
        self.cur_val = float(str(self.parent.text())) 
        #self.cur_val = float(str(self.text()))
        QtWidgets.QLineEdit.focusInEvent(self.parent, event)
        
    def focusOutEvent(self, event):
        ''' if user has not hit enter on the value in the field when 
        focus is lost on this field then return the value to its previous value
        and set the background color'''
        v = self.parent.validator()
        if(v.is_done()):
            #value is accepted
            self.cur_val = float(str(self.parent.text()))
        else:
            #value has not been accepted
            self.parent.setText(self.fmt % self.cur_val)
        self.parent.update()    
        self.parent.setStyleSheet(valid_ss) 
        QtWidgets.QLineEdit.focusOutEvent(self.parent, event)    
    
    def on_dbl_parent_rtrn_pressed(self):
        self.cur_val = float(str(self.parent.text()))
        #make sure that the value is displayed with the specified prec
        #even if the user didnt type it in with the prec
        self.parent.setText(self.fmt % self.cur_val)
        #print 'saving [%.3f]' % self.cur_val
        v = self.parent.validator()
        v.lock_changes(True)
        self.parent.setStyleSheet(valid_ss)
        self.valid_returnPressed.emit()
    
    def on_dbl_parent_changed(self):
        v = self.parent.validator()
        v.lock_changes(False)
        ss = invalid_ss
        self.parent.setStyleSheet(ss)


############################################################
class charParamValidator(QtGui.QRegExpValidator):
    # state_changed = pyqtSignal(object)
    def __init__(self, qobj=None, lineFld=None):
        QtGui.QRegExpValidator.__init__(self)
        self.changes_locked = False
        validator = QtGui.QRegExpValidator(QtCore.QRegExp("[0 - 9A - Za - z_ + -.,!@  # $%^&*();\\:/|<>']"), None)

    def is_done(self):
        return (self.changes_locked)

    def lock_changes(self, lock):
        self.changes_locked = lock


class charLineEditParamObj(QtCore.QObject):
    valid_returnPressed = QtCore.pyqtSignal()

    def __init__(self, id, valid_values=None, parent=None):
        QtCore.QObject.__init__(self)
        self.parent = parent
        self.id = id
        if(type(valid_values) is dict):
            s = ''
            idx = 0
            for k in list(valid_values.keys()):
                s += '%s = %s, ' % (k, valid_values[k])

            self.valid_values = s
        elif(type(valid_values) is list):
            s = ''
            for l in valid_values:
                s += '%s, ' % (l)
            self.valid_values = s
        else:
             self.valid_values = valid_values


        self.parent.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.parent.customContextMenuRequested.connect(self.contextMenuEvent)
        self.fmt = '%s'

        self.parent.focusInEvent = self.focusInEvent
        self.parent.focusOutEvent = self.focusOutEvent

        # self.parent.setToolTip('Valid range: from %d to %d' % (_min, _max))

        self.parent.returnPressed.connect(self.on_char_parent_rtrn_pressed)
        self.parent.textEdited.connect(self.on_char_parent_changed)

        v = charParamValidator()
        self.parent.setValidator(v)

    def contextMenuEvent(self, event):
        fld = self.sender()
        if (fld):
            self.menu = QtWidgets.QMenu(self.parent)
            if ((self.valid_values is not None)):
                ma_str = 'valid set of values are: %s' % (self.valid_values)
            else:
                ma_str = 'No retrictions on what you can put here'
            renameAction = QtWidgets.QAction(ma_str, self.parent)
            renameAction.triggered.connect(self.renameSlot)
            self.menu.addAction(renameAction)
            # add other required actions
            self.menu.popup(QtGui.QCursor.pos())

    def renameSlot(self):
        print("renaming slot called")
        # get the selected cell and perform renaming

    def focusInEvent(self, event):
        ''' when focus goes into field copy current value'''
        self.cur_val = str(self.parent.text())
        # self.cur_val = float(str(self.text()))
        QtWidgets.QLineEdit.focusInEvent(self.parent, event)

    def focusOutEvent(self, event):
        ''' if user has not hit enter on the value in the field when
        focus is lost on this field then return the value to its previous value
        and set the background color'''
        v = self.parent.validator()
        if (v.is_done()):
            # value is accepted
            self.cur_val = str(self.parent.text())
        else:
            # value has not been accepted
            self.parent.setText(self.fmt % self.cur_val)

        self.parent.setStyleSheet(valid_ss)
        QtWidgets.QLineEdit.focusOutEvent(self.parent, event)

    def on_char_parent_rtrn_pressed(self):
        self.cur_val = str(self.parent.text())
        # print 'saving [%.3f]' % self.cur_val
        v = self.parent.validator()
        v.lock_changes(True)
        self.parent.setStyleSheet(valid_ss)
        self.valid_returnPressed.emit()

    def on_char_parent_changed(self):
        v = self.parent.validator()
        v.lock_changes(False)
        ss = invalid_ss
        self.parent.setStyleSheet(ss)


class testWindow(QtWidgets.QWidget):
    '''
    classdocs
    '''
    def __init__(self):
        super(testWindow, self).__init__()



        scanning_modes_dct = {'0':'COARSE_SAMPLEFINE', \
                          '1':'GONI_ZONEPLATE', \
                          '2':'COARSE_ZONEPLATE'}

        scanning_modes_lst = ['COARSE_SAMPLEFINE', 'GONI_ZONEPLATE', 'COARSE_ZONEPLATE']

        self.e1 = QtWidgets.QLineEdit("0.0")
        self.e2 = QtWidgets.QLineEdit("0.0")
        self.e3 = QtWidgets.QLineEdit("0.0")
        self.e4 = QtWidgets.QLineEdit(r'S:\STXM-data\Cryo-STXM\2017')
        self.e5 = QtWidgets.QLineEdit(r'scanning_mode.COARSE_SAMPLEFINE')
        
        self.e1.dpo = dblLineEditParamObj('e1', -3500.0, 123.5, 3, parent=self.e1)
        self.e2.dpo = dblLineEditParamObj('e2', 0.0, 4123.5, 3, parent=self.e2)
        self.e3.dpo = dblLineEditParamObj('e3', 0.0, 63.5, 3, parent=self.e3)
        self.e4.dpo = charLineEditParamObj('e4', valid_values='Any valid directory', parent=self.e4)
        #self.e5.dpo = charLineEditParamObj('e5', valid_values=scanning_modes_dct, parent=self.e5)
        self.e5.dpo = charLineEditParamObj('e5', valid_values=scanning_modes_lst, parent=self.e5)
        
        
        self.e1.dpo.valid_returnPressed.connect(self.recalc_roi)
        self.e2.dpo.valid_returnPressed.connect(self.recalc_roi)
        self.e3.dpo.valid_returnPressed.connect(self.recalc_roi)
        self.e4.dpo.valid_returnPressed.connect(self.recalc_str)
        self.e5.dpo.valid_returnPressed.connect(self.recalc_str)
        
        flo = QtWidgets.QFormLayout()
        flo.addRow("Double validator 1",self.e1)
        flo.addRow("Double validator 2",self.e2)
        flo.addRow("Double validator 3",self.e3)
        flo.addRow("Char validator 4",self.e4)
        flo.addRow("Char validator 5", self.e5)
        self.setLayout(flo)
        
    def recalc_roi(self):
        fld = self.sender()
        print('recalcing roi for [%s] range %.2f to %.2f' % (fld.id, fld._min, fld._max))

    def recalc_str(self):
        fld = self.sender()
        print('recalcing str for [%s]' % (fld.id))
             
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    win = testWindow()
    
    win.show()
    win.setWindowTitle("PyQt")
    sys.exit(app.exec_())