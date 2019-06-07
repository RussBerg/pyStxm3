# -*- coding: utf-8 -*-
#
# Copyright © 2009-2012 CEA
# Pierre Raybaut
# Licensed under the terms of the CECILL License
# (see guiqwt/__init__.py for details)

"""Load/save items using Python's pickle protocol"""



SHOW = True # Show test in GUI-based test launcher

# WARNING:
# This script requires read/write permissions on current directory

from guidata.qt.QtGui import QFont

import os
import os.path as osp
import numpy as np

from cls.appWidgets.spyder_console import ShellWidget#, ShellDock

from guiqwt.plot import ImageDialog
from guiqwt.builder import make
from guiqwt.shapes import PolygonShape, Axes, EllipseShape
from guiqwt.tools import LoadItemsTool, SaveItemsTool, ImageMaskTool
from .beamspotShape import BeamSpotShape

def make_stars(cx, cy):

    dist_from_center = 5.0
    width_of_side = 2.5
    len_long_side = 25.0
    len_short_side = 20.0

    st1 = PolygonShape(np.array([[cx, cy + dist_from_center],
                           [cx + width_of_side, cy + len_short_side],
                           [cx, cy + len_long_side],
                           [cx - width_of_side, cy + len_short_side]]))

    st2 = PolygonShape(np.array([[cx - dist_from_center, cy],
                           [cx - len_short_side, cy + width_of_side],
                           [cx - len_long_side, cy],
                           [cx - len_short_side, cy - width_of_side]]))

    st3 = PolygonShape(np.array([[cx, cy - dist_from_center],
                           [cx - width_of_side, cy - len_short_side],
                           [cx, cy - len_long_side],
                           [cx + width_of_side, cy - len_short_side]]))

    st4 = PolygonShape(np.array([[cx + dist_from_center, cy],
                           [cx + len_short_side, cy - width_of_side],
                           [cx + len_long_side, cy],
                           [cx + len_short_side, cy + width_of_side]]))

    st1 = set_beamspot_shape_params(st1, 'beamspot_st1', clr='blue')
    st2 = set_beamspot_shape_params(st2, 'beamspot_st2', clr='blue')
    st3 = set_beamspot_shape_params(st3, 'beamspot_st3', clr='blue')
    st4 = set_beamspot_shape_params(st4, 'beamspot_st4', clr='blue')

    return(st1, st2, st3, st4)

def set_beamspot_shape_params(shape, title, clr):
    param = shape.shapeparam
    #shape.set_readonly(True)
    shape.set_resizable(False)
    #shape.set_selectable(False)
    param.label = title
    param.fill.alpha = 0.6
    param.sel_fill.alpha = 0.6
    param.symbol.alpha = 0.6
    param.sel_symbol.alpha = 0.6
    param.symbol.marker = 'NoSymbol'
    param.sel_symbol.marker = 'NoSymbol'
    param.sel_symbol.color = clr
    param.symbol.color = clr
    param.fill.color = clr
    param.sel_fill.color = clr

    param.update_shape(shape)
    #shape.set_item_parameters({"ShapeParam": shape})
    return(shape)

def make_beam_spot(cx, cy, scale=1.0):
    circ_diam = 0.5

    c1 = set_beamspot_shape_params(EllipseShape(cx, cy, cx - circ_diam, cy + circ_diam), 'beamspot_circle', clr='yellow')
    st1, st2, st3, st4 = make_stars(cx, cy)
    bsp = BeamSpotShape(x1=0, y1=0,shapeparam=None)

    items = [
              c1,
              st1, st2, st3, st4,
              #bsp]
                ]
    return items



def build_items():
    items = make_beam_spot(0.0, 0.0)
    return items

class IOTest(object):
    FNAME = None
    def __init__(self):
        self.dlg = None
        self.pythonshell = None
    
    @property
    def plot(self):
        if self.dlg is not None:
            return self.dlg.get_plot()
    
    def run(self):
        """Run test"""
        self.create_dialog()
        self.add_items()
        self.dlg.exec_()
        print("Saving items...", end=' ')
        self.save_items()
        print("OK")
        
    def create_dialog(self):
        self.dlg = dlg = ImageDialog(\
                edit=False, toolbar=True, wintitle="Load/save test",
                options=dict(title="Title", xlabel="xlabel", ylabel="ylabel"))
        dlg.add_separator_tool()
        dlg.add_tool(LoadItemsTool)
        dlg.add_tool(SaveItemsTool)
        dlg.add_tool(ImageMaskTool)


        # ns = {'self': self, 'pythonShell': self.pythonshell, 'g': globals()}
        # # msg = "Try for example: widget.set_text('foobar') or win.close()"
        # self.pythonshell = ShellWidget(parent=None, namespace=ns, commands=[], multithreaded=True)
        # dlg.layout().addWidget(self.pythonshell)
        # # self.apply_stylesheet(self.pythonshell, self.qssheet)


    def add_items(self):
        for item in build_items():
            self.plot.add_item(item)
            print("Building items and add them to plotting canvas", end=' ')
        self.plot.set_axis_font("left", QFont("Courier"))
        self.dlg.get_itemlist_panel().show()
        self.plot.set_items_readonly(False)
    
    def restore_items(self):
        raise NotImplementedError
    
    def save_items(self):
        pass
        #raise NotImplementedError
    

class PickleTest(IOTest):
    FNAME = "loadsavecanvas.pickle"
    def restore_items(self):
        f = open(self.FNAME, "rb")
        self.plot.restore_items(f)
    
    def save_items(self):
        f = open(self.FNAME, "wb")
        self.plot.save_items(f)
    

if __name__ == "__main__":
    import guidata
    _app = guidata.qapplication()
    test = IOTest()
    test.run()
