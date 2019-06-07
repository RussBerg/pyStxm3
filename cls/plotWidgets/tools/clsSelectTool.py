# -*- coding:utf-8 -*-
'''
Created on Jul 26, 2016

@author: bergr
'''

from PyQt5.QtCore import pyqtSignal 
from PyQt5 import QtGui, QtWidgets

from guiqwt.tools import *
from guiqwt.events import PanHandler, AutoZoomHandler, \
    ZoomHandler, MenuHandler, MoveHandler
#from guiqwt.config import _

from cls.plotWidgets.guiqwt_config import _

def _setup_standard_tool_filter(_filter, start_state):
    """Cr�ation des filtres standard (pan/zoom) sur boutons milieu/droit"""
    # Bouton du milieu
    PanHandler(_filter, Qt.MidButton, start_state=start_state)
    AutoZoomHandler(_filter, Qt.MidButton, start_state=start_state)

    # Bouton droit
    ZoomHandler(_filter, Qt.RightButton, start_state=start_state)
    MenuHandler(_filter, Qt.RightButton, start_state=start_state)

    # Autres (touches, move)
    MoveHandler(_filter, start_state=start_state)
    MoveHandler(_filter, start_state=start_state, mods=Qt.ShiftModifier)
    MoveHandler(_filter, start_state=start_state, mods=Qt.AltModifier)
    MoveHandler(_filter, start_state=start_state, mods=Qt.ControlModifier)
    return start_state


class clsMoveHandler(object):
    changed = pyqtSignal(object, object)

    def __init__(self, _filter, btn=Qt.NoButton, mods=Qt.NoModifier,
                 start_state=0):
        _filter.add_event(
            start_state,
            _filter.mouse_move(
                Qt.NoButton,
                Qt.NoModifier),
            self.move,
            start_state)
        _filter.add_event(start_state, _filter.mouse_move(btn, mods), self.move, start_state)
        #add event for emitting the center has changed 
        _filter.add_event(start_state, KeyEventMatch(((Qt.Key_C, Qt.ControlModifier),)), self.on_keypress, start_state)
            
            
        self.allow_parm_update = False

    def move(self, _filter, event):
        #pos = event.pos()
        if(self.allow_parm_update):
            self.changed.emit(filter, event)
        else:
            self.changed.emit(None, None)

    def on_keypress(self, _filter, event):
        if ((event.modifiers() and Qt.ControlModifier)
                and (event.key() == Qt.Key_C)):
            self.allow_parm_update = True
        else:
            self.allow_parm_update = False
        #print 'event.keys == ', event.key()


class clsSelectTool(InteractiveTool):
    """
    Graphical Object Selection Tool
    """
    TITLE = _("clsSelection")
    ICON = "selection.png"
    CURSOR = Qt.ArrowCursor
    changed = pyqtSignal(object, object)

    def setup_filter(self, baseplot):
        _filter = baseplot.filter
        start_state = _filter.new_state()

        ObjectHandler(_filter, Qt.LeftButton, start_state=start_state)
        ObjectHandler(
            _filter,
            Qt.LeftButton,
            mods=Qt.ControlModifier,
            start_state=start_state,
            multiselection=True)
        _filter.add_event(
            start_state,
            KeyEventMatch(
                (Qt.Key_Enter,
                 Qt.Key_Return,
                 Qt.Key_Space)),
            self.validate,
            start_state)
        _filter.add_event(start_state, KeyEventMatch(
            ((Qt.Key_A, Qt.ControlModifier),)), self.select_all_items, start_state)
        #_filter.add_event(start_state, KeyEventMatch(
        #    ((Qt.Key_A, Qt.ControlModifier),)), self.select_all_items, start_state)

        #clsMoveHandler(start_state, KeyEventMatch(((Qt.Key_S, Qt.ControlModifier),)), self.modify_params, start_state)
        self.s = clsMoveHandler(
            _filter,
            btn=Qt.LeftButton,
            mods=Qt.ControlModifier,
            start_state=start_state)
        self.s.changed = self.changed
        # s.installEventFilter(self)
        return _setup_standard_tool_filter(_filter, start_state)

    def select_all_items(self, _filter, event):
        _filter.plot.select_all()
        _filter.plot.replot()
