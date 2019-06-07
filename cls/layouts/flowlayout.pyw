#!/usr/bin/env python

"""PyQt4 port of the layouts/flowlayout example from Qt v4.x"""

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import SIGNAL, Qt, QStringList, pyqtSignal, QRect, QSize
from PyQt4 import uic


uiDir = r'C:\controls\python26Workspace\PyQtStxmViewer\src'






class FlowLayout(QtGui.QLayout):
    def __init__(self, parent=None, margin=0, spacing=-1):
        super(FlowLayout, self).__init__(parent)

        #if parent is not None:
        #self.setMargin(margin)


        self.setSpacing(spacing)

        self.itemList = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self.itemList.append(item)

    def count(self):
        return len(self.itemList)

    def itemAt(self, index):
        if index >= 0 and index < len(self.itemList):
            return self.itemList[index]

        return None

    def takeAt(self, index):
        if index >= 0 and index < len(self.itemList):
            return self.itemList.pop(index)

        return None

    def expandingDirections(self):
        return QtCore.Qt.Orientations(QtCore.Qt.Orientation(0))

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self.doLayout(QtCore.QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        super(FlowLayout, self).setGeometry(rect)
        self.doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QtCore.QSize()

        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())

        size += QtCore.QSize(2 * self.margin(), 2 * self.margin())
        return size

    def doLayout(self, rect, testOnly):
        x = rect.x()
        y = rect.y()
        lineHeight = 0

        for item in self.itemList:
            wid = item.widget()
            spaceX = self.spacing() + wid.style().layoutSpacing(QtGui.QSizePolicy.PushButton, QtGui.QSizePolicy.PushButton, QtCore.Qt.Horizontal)
            spaceY = self.spacing() + wid.style().layoutSpacing(QtGui.QSizePolicy.PushButton, QtGui.QSizePolicy.PushButton, QtCore.Qt.Vertical)
            nextX = x + item.sizeHint().width() + spaceX
            if nextX - spaceX > rect.right() and lineHeight > 0:
                x = rect.x()
                y = y + lineHeight + spaceY
                nextX = x + item.sizeHint().width() + spaceX
                lineHeight = 0

            if not testOnly:
                item.setGeometry(QtCore.QRect(QtCore.QPoint(x, y), item.sizeHint()))

            x = nextX
            lineHeight = max(lineHeight, item.sizeHint().height())

        return y + lineHeight - rect.y()


if __name__ == '__main__':

    import sys
    from stxm_widgets.controller import ControllerField, ControllerPanel
    
    class Window(QtGui.QWidget):
        def __init__(self):
            super(Window, self).__init__()
    
            flowLayout = FlowLayout(parent = self, margin=10, spacing=5)
            #flowLayout.addWidget(QtGui.QPushButton(self.tr("Short")))
            #flowLayout.addWidget(QtGui.QPushButton(self.tr("Longer")))
            #flowLayout.addWidget(QtGui.QPushButton(self.tr("Different text")))
            #flowLayout.addWidget(QtGui.QPushButton(self.tr("More text")))
            #flowLayout.addWidget(QtGui.QPushButton(self.tr("Even longer button text")))
            
            flowLayout.addWidget(ControllerField('start', val = 10.0, parent = self))
            flowLayout.addWidget(ControllerField('stop',  val = 30.0, parent = self))
            flowLayout.addWidget(ControllerField('range', val = 20.0, parent = self))
            flowLayout.addWidget(ControllerField('points',val = 200.0, parent = self))
            flowLayout.addWidget(ControllerField('step',val = 0.05, parent = self))
            flowLayout.addWidget(ControllerField('dwell',val = 1.3, parent = self)) 
            
            self.setLayout(flowLayout)
    
            self.setWindowTitle(self.tr("Flow Layout"))

    app = QtGui.QApplication(sys.argv)
    mainWin = Window()
    mainWin.show()
    sys.exit(app.exec_())
