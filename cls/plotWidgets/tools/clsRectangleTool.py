'''
Created on Aug 9, 2016

@author: bergr
'''

#from guiqwt.config import _
from guiqwt.tools import *

from cls.plotWidgets.guiqwt_config import _
from cls.types.stxmTypes import spatial_type_prefix


class clsRectangleTool(AverageCrossSectionTool):
    SWITCH_TO_DEFAULT_TOOL = True
    TITLE = _('')
    ICON = "rectangle.png"
    SHAPE_STYLE_KEY = "shape/average_cross_section"
    SHAPE_TITLE = TITLE
    spatial_type = spatial_type_prefix.ROI
    
    def set_enabled(self, en):
        self.action.setEnabled(en)
