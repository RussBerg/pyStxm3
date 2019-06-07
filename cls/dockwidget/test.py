#!/usr/bin/env python
#-*- coding: utf-8 -*-
from PyQt5.Qt import *
from PyQt5.QtGui import (QMainWindow, QWidget, QListWidget, QFrame, QDockWidget, QPushButton)
from PyQt5.QtCore import SIGNAL, Qt, QStringList, pyqtSignal, QRect, QSize
from PyQt5 import uic

uiDir = r'C:\controls\python26Workspace\PyQtStxmViewer\src'

class ControllerField(QWidget):
    
    changed = pyqtSignal(float)
    
    def __init__(self, title, val = 0.0, parent = None):
        QWidget.__init__(self)
        self.parent = parent
        self.name = title
        self.stepSize = 0.1
        self.val = val
        
        uic.loadUi(uiDir + '\\ui\\controllerFld.ui', self)
        self.setToolTip(title)
        self.update_label(self.val)
        
        self.connect(self.incrementBtn, SIGNAL("clicked()"), self.on_increment)
        self.connect(self.decrementBtn, SIGNAL("clicked()"), self.on_decrement)
        self.changed.connect(self.update_label)
        
        #self.show()
        
    
    def update_label(self, val):
        self.lineEdit.setText(str(self.val))
    
    def setVal(self, newVal):
        self.val = newVal
        self.changed.emit(newVal)
        
    def on_increment(self):
        self.setVal(self.val + self.stepSize)

    def on_decrement(self):
        self.setVal(self.val - self.stepSize)

        
    def get_panel_name(self):
            return self.name



class TwirlPanel(QWidget):
    
    changed_size = pyqtSignal(QSize)
    
    def __init__(self, title, parent = None):
        QWidget.__init__(self)
        self.parent = parent
        self.title = title
        self.showMax = False

        uic.loadUi(uiDir + '\\ui\\twirlPanel.ui', self)

        #self.label.setText(title)
        
        #add some widgets
        self.widgetList = []
        self.widgetList.append(ControllerField('start', val = 10.0))
        self.widgetList.append(ControllerField('start', val = 10.0))
        self.widgetList.append(ControllerField('stop',  val = 30.0))
        self.widgetList.append(ControllerField('range', val = 20.0))
        self.widgetList.append(ControllerField('points',val = 200.0))
        self.widgetList.append(ControllerField('step',val = 0.05))
        self.widgetList.append(ControllerField('dwell',val = 1.3))     
                            
        self.addControllerWidgets(self.widgetList)

        maxSize = self.maximumSize()
        maxHt = self.calcMaxHeight(self.widgetList)
        self.maxSize = QSize(maxSize.width(),maxHt)
        self.minSize = QSize(maxSize.width(),40)
        self.setMaximumSize(self.maxSize)
        #self.setMinimumSize(self.minSize)
        
        #self.setFixedSize(self.__minSize)

        
        #self.connect(self.twirlBtn, SIGNAL("clicked(bool)"), self.on_twirl)
    
    def calcMaxHeight(self, widgetList):
        h = 0
        for w in widgetList:
            h += w.maximumSize().height()
        
        #add a small buffer so it doesn't clip the bottom 
        h += 5
        return h
    
        
    #re implemented:  as per documentation http://doc.qt.nokia.com/latest/layout.html    
    def sizeHint(self):
        if(self.showMax):
            return(self.maxSize)
        else:
            return(self.minSize)
    
    #re implemented:  as per documentation http://doc.qt.nokia.com/latest/layout.html
    def minimumSizeHint(self):
        return(self.minSize)
    
    
    def on_twirl(self, on):
        if(on):
            #print 'on_twirl: maximizing'
            self.twirlBtn.setArrowType(Qt.DownArrow) 
            self.setFixedSize(self.maxSize)
            self.showMax = True
            
        else:
            #print 'on_twirl: minimizing'
            self.twirlBtn.setArrowType(Qt.RightArrow)
            self.setFixedSize(self.minSize)
            self.showMax = False

        # as per documentation http://doc.qt.nokia.com/latest/layout.html
        self.updateGeometry()
        
    def addControllerWidget(self, widget):
        #self.addWidget(widget)
        self.propertyLayout.addWidget(widget)
        widget.setVisible(True)
    
    def addControllerWidgets(self, widgetList):
        for w in widgetList:
            self.addControllerWidget(w)
            
        
    def get_panel_name(self):
            return self.name
            


class QAutoHideDockWidgets(QToolBar):
    """
    QMainWindow "mixin" which provides auto-hiding support for dock widgets
    (not toolbars).
    """
    DOCK_AREA_TO_TB = {
        Qt.LeftDockWidgetArea: Qt.LeftToolBarArea,
        Qt.RightDockWidgetArea: Qt.RightToolBarArea,
        Qt.TopDockWidgetArea: Qt.TopToolBarArea,
        Qt.BottomDockWidgetArea: Qt.BottomToolBarArea,
    }

    def __init__(self, area, parent, name="AUTO_HIDE"):
        QToolBar.__init__(self, parent)
        assert isinstance(parent, QMainWindow)
        assert area in self.DOCK_AREA_TO_TB
        self._area = area
        self.setObjectName(name)
        self.setWindowTitle(name)
        
        self.setFloatable(False)
        self.setMovable(False)
        w = QWidget(None)
        w.resize(10, 100)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.MinimumExpanding))
        self.addWidget(w)

        self.setAllowedAreas(self.DOCK_AREA_TO_TB[self._area])
        self.parent().addToolBar(self.DOCK_AREA_TO_TB[self._area], self)
        #self.parent().centralWidget().installEventFilter(self)
        self.parent().installEventFilter(self)
        
        self.setVisible(False)
        self.hideDockWidgets()

    def _dockWidgets(self):
        mw = self.parent()
        for w in mw.findChildren(QDockWidget):
            if mw.dockWidgetArea(w) == self._area and not w.isFloating():
                yield w

    def paintEvent(self, event):
        p = QPainter(self)
        p.setPen(Qt.black)
        p.setBrush(Qt.black)
        if self._area == Qt.LeftDockWidgetArea:
            p.translate(QPointF(0, self.height() / 2 - 5))
            p.drawPolygon(QPointF(2,0), QPointF(8,5), QPointF(2,10))
        elif self._area == Qt.RightDockWidgetArea:
            p.translate(QPointF(0, self.height() / 2 - 5))
            p.drawPolygon(QPointF(8,0), QPointF(2,5), QPointF(8,10))

    def _multiSetVisible(self, widgets, state):
        if state:
            self.setVisible(False)

        for w in widgets:
            w.setUpdatesEnabled(False)
        for w in widgets:
            w.setVisible(state)
        for w in widgets:
            w.setUpdatesEnabled(True)

        if not state and widgets:
            self.setVisible(True)

    def enterEvent(self, event):
        self.showDockWidgets()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Enter:
            assert obj == self.parent().centralWidget()
            self.hideDockWidgets()
        return False

    def setDockWidgetsVisible(self, state):
        self._multiSetVisible(list(self._dockWidgets()), state)

    def showDockWidgets(self): self.setDockWidgetsVisible(True)
    def hideDockWidgets(self): self.setDockWidgetsVisible(False)
    
    
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    win = QMainWindow()
    dock1 = QAutoHideDockWidgets(Qt.LeftDockWidgetArea, win)
    #dock1 = DockWidget("1st dockwidget", win)
    #combo =  QComboBox(dock1)
    combo = TwirlPanel('russ1', parent = dock1)
    dock1.setWidget(combo)
    win.addDockWidget(Qt.LeftDockWidgetArea, dock1)
    
    
    win.show()
    app.exec_()
    