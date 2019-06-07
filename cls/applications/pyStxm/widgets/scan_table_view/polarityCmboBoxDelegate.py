'''
Created on Nov 16, 2016

@author: bergr
'''

from PyQt5 import QtCore, QtGui, QtWidgets

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
        #chkd = index.model().get_scans()[index.row()][POLARITY_COLUMN]
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
            idx = int(index.data()) 
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
