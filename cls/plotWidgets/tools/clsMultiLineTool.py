'''
Created on Aug 9, 2016

@author: bergr
'''

from PyQt5 import QtCore, QtWidgets

from guiqwt.tools import *
#from guiqwt.config import _

from cls.plotWidgets.guiqwt_config import _
from cls.types.stxmTypes import spatial_type_prefix

class clsMultiLineTool(MultiLineTool):
    TITLE = _("STXM multiline tool")
    shapeNum = 0  # used in the TITLE that is displayed to the user
    unique_id = 0  # used as the key to a dict of shapeItems, not for display
    spatial_type = spatial_type_prefix.SEG

    def set_enabled(self, en):
        self.action.setEnabled(en)

    def create_shape(self, _filter, pt):
        pts = self.get_box_points_in_plot_coordinates(pt)
        self.shape = PolygonShape(pts, closed=True)
        _filter.plot.add_item_with_z_offset(self.shape, SHAPE_Z_OFFSET)
        self.shape.setVisible(True)
        self.shape.set_style(self.shape_style_sect, self.shape_style_key)
        # self.shape.add_local_point(pt)
        #pt = self.draw_box(pt)
        #self.shape.closed = len(self.shape.points) > 2

        return QtCore.QPoint(pts[0][0], pts[0][1])

    def get_box_points_in_plot_coordinates(self, qpt):
        x1 = 0  # qpt.x()
        y1 = 0  # qpt.y()
        x2 = x1 + 100
        y2 = y1 + 50
        pts = []
        pts.append((x1, y1))
        pts.append((x1, y2))
        pts.append((x2, y2))
        pts.append((x2, y1))
        return(pts)

    def mouse_press(self, _filter, event):
        """We create a new shape if it's the first point
        otherwise we add a new point
        """

        if self.shape is None:
            self.init_pos = event.pos()
            self.current_handle = self.create_shape(_filter, event.pos())
            _filter.plot.replot()
        else:
            pass
            #self.current_handle = self.shape.add_local_point(event.pos())

    def move(self, _filter, event):
        """moving while holding the button down lets the user
        position the last created point
        """
        if self.shape is None or self.current_handle is None:
            # Error ??
            return
        #self.shape.move_local_point_to(self.current_handle, event.pos())
        # _filter.plot.replot()

    def mouse_release(self, _filter, event):
        """Releasing the mouse button validate the last point position"""
        if self.current_handle is None:
            return
        if self.init_pos is not None and self.init_pos == event.pos():
            self.shape.del_point(-1)
        else:
            #self.shape.move_local_point_to(self.current_handle, event.pos())
            pass
        self.init_pos = None
        self.current_handle = None
        # _filter.plot.replot()
        
        