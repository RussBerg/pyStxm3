'''
Created on Aug 9, 2016

@author: bergr
'''
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import pyqtSignal 

from guiqwt.tools import *
#from guiqwt.config import _
from guiqwt.interfaces import IShapeItemType
from cls.plotWidgets.guiqwt_config import _

from cls.utils.roi_utils import get_unique_roi_id, add_to_unique_roi_id_list
from cls.types.stxmTypes import spatial_type_prefix

class clsAverageCrossSectionTool(AverageCrossSectionTool):
    shapeNum = 0
    SWITCH_TO_DEFAULT_TOOL = True
    TITLE = _('Select 2D ROI for scan')
    ICON = "csection_a.png"
    SHAPE_STYLE_KEY = "shape/average_cross_section"
    shapeNum = 0  # used in the TITLE that is displayed to the user
    unique_id = 0  # used as the key to a dict of shapeItems, not for display
    #SHAPE_TITLE = 'ROI %d' % shapeNum
    SHAPE_TITLE = 'ROI %d' % unique_id
    enable_multi_shape = False
    spatial_type = spatial_type_prefix.ROI

    def set_enabled(self, en):
        self.action.setEnabled(en)

    # def get_num_instances(self):
    #    num_this_shape = self.manager.

    def re_init_unique_id(self):
        """
        re_init_unique_id(): description

        :returns: None
        """
        #print 're_init_unique_id: IN: %d' % self.unique_id
        self.unique_id = get_unique_roi_id()
        #print 're_init_unique_id: OUT: %d' % self.unique_id

    def activate(self):
        """Activate tool"""
        current_shape_items = self.manager.plot.get_items(item_type=IShapeItemType)
        if (self.manager.multi_region_enabled):
            self.do_activate()
        elif (len(current_shape_items) > 0):
            self.deactivate()
        elif (len(current_shape_items) is 0):
            self.do_activate()


    def do_activate(self):
        """
        activate(): description

        :returns: None
        """
        """Activate tool"""
        # This function gets called numerous times by different objects, only
        # increment the item counter if it is called by QAction (which is only called once per
        # click of the tool
        #print 'clsAverageCrossSectionTool: START: self.unique_id=%d' % self.unique_id
        if(isinstance(self.sender(), QtWidgets.QAction)):
            if(self.shapeNum > 0):
                # feb 21 2018: tomo
                add_to_unique_roi_id_list(self.unique_id)
                #
                if(self.manager.multi_region_enabled):
                    pass
                else:

                    self.action.setChecked(False)
                    self.manager.activate_default_tool()
                    return

            self.shapeNum += 1

            # get a new unique ID that will be assigned to the shape
            self.re_init_unique_id()
            #tell the main plot what teh current unique_id is so that it can ignore signals with unique_id's that
            #are not current
            self.manager._cur_shape_uid = self.unique_id

        for baseplot, start_state in list(self.start_state.items()):
            baseplot.filter.set_state(start_state, None)

        self.action.setChecked(True)
        self.manager.set_active_tool(self)
        #print 'clsAverageCrossSectionTool: END: self.unique_id=%d' % self.unique_id
        #print 'clsAverageCrossSectionTool: addr(self.unique_id)=%d' % id(self.unique_id)



    def setup_shape(self, shape):
        """
        setup_shape(): description

        :param shape: shape description
        :type shape: shape type

        :returns: None
        """
#         cur_shapes = self.manager.getShapeItemsByShapeType(AnnotatedRectangle)
#         if((not self.enable_multi_shape) and (len(cur_shapes) > 0)):
#             #only allow one shape to exist
#
#             return

        # if(self.manager.multi_region_enabled):
        #shape.setTitle('ROI %d' % self.shapeNum)
        shape.setTitle('ROI %d' % self.unique_id)
        # create a new property of the shape
        shape.unique_id = self.unique_id
        shape.shapeNum = self.shapeNum
        shape._parent_tool = self


#         Shape:
#     _styles:
#       _ShapeParam___line:
#         LineStyleParam:
#           Style: Dotted line
#           Color: #55ff4c
#           Width: 1.0
#         LineStyleParam:
#           Style: Dotted line
#           Color: #06ff02
#           Width: 1.0
#       _ShapeParam___sym:
#         SymbolParam:
#           Style: Diamond
#           Size: 7
#           Border: #00ff7f
#           Background color: #00aa7f
#           Background alpha: 0.6
#         SymbolParam:
#           Style: Diamond
#           Size: 9
#           Border: #308f30
#           Background color: #2eff00
#           Background alpha: 0.7
#       _ShapeParam___fill:
#         BrushStyleParam:
#           Style: Uniform color
#           Color: #ffffff
#           Alpha: 0.100007629511
#           Angle: 0.0
#           sx: 1.0
#           sy: 1.0
#         BrushStyleParam:
#           Style: Uniform color
#           Color: #14ff00
#           Alpha: 0.176470588235
#           Angle: 0.0
#           sx: 1.0
#           sy: 1.0
#     : False
#     : False

        # sp = shape.shape.shapeparam
        # sp.sel_line.color = '#00ff00'
        # sp.line.color = '#ffff00'
        # #shape.shape.shapeparam.sel_line.color
        #
        # shape.set_item_parameters({"ShapeParam":sp})

        self.setup_shape_appearance(shape)
        super(CrossSectionTool, self).setup_shape(shape)
        self.register_shape(shape, final=False)

    def interactive_triggered(self, action):
        if action is self.action:
            self.activate()
        else:
            self.deactivate()


    def deactivate(self):
        """Deactivate tool"""
        self.action.setChecked(False)
        