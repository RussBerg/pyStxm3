'''
Created on Feb 3, 2017

@author: bergr
'''
from PyQt5 import QtCore, QtGui, uic

from PyQt5.QtCore import pyqtSignal 

import numpy as np

from guiqwt.geometry import (compute_center, compute_rect_size,
                             compute_distance, compute_angle)
from guiqwt.tools import *
#from guiqwt.config import _
from cls.plotWidgets.guiqwt_config import _
from guiqwt.annotations import AnnotatedShape

class AnnotatedHorizontalSegment(AnnotatedShape):
    """
    Construct an annotated segment between coordinates (x1, y1) and 
    (x2, y1) with properties set with *annotationparam* 
    (see :py:class:`guiqwt.styles.AnnotationParam`)
    """
    SHAPE_CLASS = SegmentShape
    LABEL_ANCHOR = "C"
    unique_id = -1  # used as the key to a dict of shapeItems, not for display
    SHAPE_TITLE = 'SEGG %d' % unique_id
    def __init__(self, x1=0, y1=0, x2=0, y2=0, annotationparam=None):
        AnnotatedShape.__init__(self, annotationparam)
        self.set_rect(x1, y1, x2, y1)
        
    #----Public API-------------------------------------------------------------
    def set_rect(self, x1, y1, x2, y2):
        """
        Set the coordinates of the shape's top-left corner to (x1, y1), 
        and of its bottom-right corner to (x2, y1).
        """
        self.shape.set_rect(x1, y1, x2, y1)
        self.set_label_position()

    def get_rect(self):
        """
        Return the coordinates of the shape's top-left and bottom-right corners
        """
        return self.shape.get_rect()
        
    def get_tr_length(self):
        """Return segment length after applying transform matrix"""
        return compute_distance(*self.get_transformed_coords(0, 1))
    
    #----AnnotatedShape API-----------------------------------------------------
    def set_label_position(self):
        """Set label position, for instance based on shape position"""
        x1, y1, x2, y2 = self.get_rect()
        self.label.set_pos(*compute_center(x1, y1, x2, y1))
        
    #----AnnotatedShape API-----------------------------------------------------
    def get_infos(self):
        """Return formatted string with informations on current shape"""
        return _("Distance:") + " " + self.x_to_str(self.get_tr_length())
    
    def get_center(self, x1, y1, x2, y2):
        xc = (x1+x2)/2.0
        yc = (y1+y2)/2.0
        return((xc,yc))
    
    def get_delta(self, old_pos, new_pos):
        x = old_pos[0] - new_pos[0]
        y = old_pos[1] - new_pos[1]
        return((x,y))
    
    def new_center(self, pos, delta_pos):
        x1, y1, x2, y2 = self.get_rect()
        dx, dy = delta_pos
        x1 += dx
        x2 += dx
        y1 -= dy
        y2 -=dy
        return((x1, y1, x2, y2))
    
    def move_point_to(self, handle, pos, ctrl=None):
        nx, ny = pos
        x1, y1, x2, y2 = self.get_rect()
        line_len = (x2 - x1)/2.0
        
        #print 'STXMSegmentShape: move_point_to: handle=%d X1=%.3f X2=%.3f Y=%.3f' % (handle, x1, x2, y2)
        
        if handle == 0:
            self.set_rect(nx, ny, x2, y2)
        elif handle == 1:
            self.set_rect(x1, y1, nx, ny)
        elif handle in (2, -1):
            #delta = (nx, ny)-self.points.mean(axis=0)
            x1 = pos[0] - line_len
            x2 = pos[0] + line_len
            y1 = pos[1]
            y2 = pos[1]
            #old_center = self.get_center(x1, y1, x2, y2)
            #delta = self.get_delta(old_center, pos)
            #(x1, y1, x2, y2) = self.new_center(pos, delta)
            self.set_rect(x1, y1, x2, y2 )
        
        if self.plot():
            #self.plot().emit(SIG_ANNOTATION_CHANGED, self)
            self.plot().SIG_ANNOTATION_CHANGED.emit(self)

    def __reduce__(self):
        state = (self.shapeparam, self.points, self.z())
        return (self.__class__, (0, 0, 0, 0), state)

    def __setstate__(self, state):
        param, points, z = state
        #----------------------------------------------------------------------
        # compatibility with previous version of SegmentShape:
        x1, y1, x2, y2, x3, y3 = points.ravel()
        v12 = np.array((x2-x1, y2-y1))
        v13 = np.array((x3-x1, y3-y1))
        if np.linalg.norm(v12) < np.linalg.norm(v13):
            # old pickle format
            points = np.flipud(np.roll(points, -1, axis=0))
        #----------------------------------------------------------------------
        self.points = points
        self.setZ(z)
        self.shapeparam = param
        self.shapeparam.update_shape(self)


    def setup_shape(self, shape):
        """
        setup_shape(): description

        :param shape: shape description
        :type shape: shape type

        :returns: None
        """
        """To be reimplemented"""
        title = 'HEEYYYY %d' % self.unique_id
        shape.setTitle(title)
        # create a new property of the shape
        shape.unique_id = self.unique_id
        shape.shapeNum = self.shapeNum
        shape._parent_tool = self

        if self.setup_shape_cb is not None:
            self.setup_shape_cb(shape)
        