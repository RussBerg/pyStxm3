# -*- coding:utf-8 -*-
"""
 Copyright © 2011 Canadian Light Source Inc. (CLSI) All rights reserved.

 Permission to use, copy, modify, and distribute this software and its
 documentation for any purpose and without fee or royalty is hereby granted,
 provided that the full text of this NOTICE appears on ALL copies of the
 software and documentation or portions thereof, including modifications,
 that you make.

 THIS SOFTWARE IS PROVIDED BY CLSI "AS IS" AND CLSI EXPRESSLY DISCLAIMS
 LIABILITY FOR ANY AND ALL DAMAGES AND LOSSES (WHETHER DIRECT, INCIDENTAL,
  CONSEQUENTIAL OR OTHERWISE) ARISING FROM OR IN ANY WAY RELATED TO THE
 USE OF SOFTWARE, INCLUDING, WITHOUT LIMITATION, DAMAGES TO ANY COMPUTER,
 SOFTWARE OR DATA ARISING OR RESULTING FROM USE OF THIS SOFTWARE.
 BY WAY OF EXAMPLE, BUT NOT LIMITATION, CLSI MAKE NO REPRESENTATIONS OR
 WARRANTIES OF MERCHANTABILITY OR FITNESS FOR ANY PARTICULAR PURPOSE OR
 THAT THE USE OF THE SOFTWARE  OR DOCUMENTATION WILL NOT INFRINGE ANY THIRD
 PARTY PATENTS, COPYRIGHTS, TRADEMARKS OR OTHER RIGHTS. CLSI WILL BEAR NO
 LIABILITY FOR ANY USE OF THIS SOFTWARE OR DOCUMENTATION.

 Title to copyright in this software and any associated documentation will
 at all times remain with CLSI. The reproduction of CLSI and its trademarks
 is strictly prohibited, except with the prior written consent of CLSI.

-----------------------------------------------
wireCurveWidget provides <WHAT DOES THIS PROVIDE?>, classes for <WHAT?>.

<PUT A DESCRITION HERE OF WHAT THIS DOES>
"""
#put builtin imports here
import os, sys

__author__ = "bergr"
__copyright__ = "Copyright 2011, The Canadian Lightsource"
__credits__ = ["bergr", "?"]
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "bergr"
__email__ = "russ.berg@lightsource.ca"
__status__ = "Development"

#put 3rd party imports here
# -*- coding:utf-8 -*-
"""
Created on 2011-03-09

@author: bergr
This widget is used to either import .dat files created by the data acquisition
library or to simply connect the plot to a PV and plot the changing value, the
test() function shows how to use the widget
"""
from PyQt5 import Qt
from PyQt5 import QtGui, QtCore, QtWidgets

import qwt as Qwt

import numpy as np

from guiqwt.config import _
from guiqwt.styles import COLORS,  GridParam #MARKERS,LINESTYLES,
from guiqwt.builder import make
from guiqwt.plot import CurveDialog
from guiqwt.tools import *

from bcm.devices.device_names import *

from cls.plotWidgets import tools

from cls.utils.log import get_module_logger
from cls.utils.json_threadsave import mime_to_dct
#from cls.utils.fileUtils import loadDatToArray, readColumnStrs  
from cls.app_data.defaults import rgb_as_hex
from cls.scanning.dataRecorder import DataIo
from cls.utils.fileUtils import get_file_path_as_parts
from cls.app_data.defaults import  get_style
from cls.plotWidgets.curve_object import curve_Obj
from cls.types.stxmTypes import scan_types
#setup module logger with a default do-nothing handler
_logger = get_module_logger(__name__)

uiDir = r'./'
icoDir = os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','icons')

#print 'uiDir = %s' % uiDir

import copy

color_list = {}
for k in list(COLORS.keys()):
    color_list[k] = {}
    color_list[k]['clr'] = COLORS[k]
    color_list[k]['used'] = False
#don't use black
color_list['k']['used'] = True
    
def get_next_color(use_dflt=True):
    global color_list
#    clr_keys = color_list.keys()
    clr_str='blue'
    if(use_dflt):
        clr_str='blue'
    else:    
        #print 'get_next_color: clr_idx = %d' % color_idx
        for k in list(color_list.keys()):
            if(color_list[k]['used'] == False):
                clr_str = color_list[k]['clr']
                color_list[k]['used'] = True
                break
    return(clr_str)
    
def reset_color_idx():
    global color_list
    for k in list(color_list.keys()):
        color_list[k]['used'] = False
    #don't use black
    color_list['k']['used'] = True

def dump_curve_styles():
    """
    Curve styles [0] = Lines
    Curve styles [1] = Sticks
    Curve styles [2] = Steps
    Curve styles [3] = Dots
    Curve styles [4] = NoCurve
    """
    from guiqwt.styles import CURVESTYLE_CHOICES
    i = 0
    for s in CURVESTYLE_CHOICES:
        print('Curve styles [%d] = %s' % (i, s[0])) 
        i += 1
    print()

def dump_curve_types():
    """
    Curve Types[0] = "Yfx"     ("Draws y as a function of x")
    Curve Types[1] = "Xfy"     ("Draws x as a function of y")

    """
    from guiqwt.styles import CURVETYPE_CHOICES
    i = 0
    for s in CURVETYPE_CHOICES:
        print('Curve types [%d] = %s' % (i, s[0])) 
        i += 1
    print()
 
def dump_line_styles():
    """
    Line styles [0] = SolidLine
    Line styles [1] = DashLine
    Line styles [2] = DotLine
    Line styles [3] = DashDotLine
    Line styles [4] = DashDotDotLine
    Line styles [5] = NoPen
       
    """
    from guiqwt.styles import LINESTYLE_CHOICES
    i = 0
    for s in LINESTYLE_CHOICES:
        print('Line styles [%d] = %s' % (i, s[0])) 
        i += 1
    print()

def dump_marker_choices():
    """
    Marker Choices [0] = Cross
    Marker Choices [1] = Ellipse
    Marker Choices [2] = Star1
    Marker Choices [3] = XCross
    Marker Choices [4] = Rect
    Marker Choices [5] = Diamond
    Marker Choices [6] = UTriangle
    Marker Choices [7] = DTriangle
    Marker Choices [8] = RTriangle
    Marker Choices [9] = LTriangle
    Marker Choices [10] = Star2
    Marker Choices [11] = NoSymbol
    
    """
    from guiqwt.styles import MARKER_CHOICES
    i = 0
    for s in MARKER_CHOICES:
        print('Marker Choices [%d] = %s' % (i, s[0])) 
        i += 1
    print()
    
def dump_marker_style_choices():
    """
    Brush style Choices [0] = NoBrush
    Brush style Choices [1] = SolidPattern
    Brush style Choices [2] = Dense1Pattern
    Brush style Choices [3] = Dense2Pattern
    Brush style Choices [4] = Dense3Pattern
    Brush style Choices [5] = Dense4Pattern
    Brush style Choices [6] = Dense5Pattern
    Brush style Choices [7] = Dense6Pattern
    Brush style Choices [8] = Dense7Pattern
    Brush style Choices [9] = HorPattern
    Brush style Choices [10] = VerPattern
    Brush style Choices [11] = CrossPattern
    Brush style Choices [12] = BDiagPattern
    Brush style Choices [13] = FDiagPattern
    Brush style Choices [14] = DiagCrossPattern
    
    """
    from guiqwt.styles import MARKERSTYLE_CHOICES
    i = 0
    for s in MARKERSTYLE_CHOICES:
        print('Marker Style Choices [%d] = %s' % (i, s[0])) 
        i += 1
    print()
    
def dump_brushstyle_choices():
    """
    Marker Style Choices [0] = NoLine
    Marker Style Choices [1] = HLine
    Marker Style Choices [2] = VLine
    Marker Style Choices [3] = Cross
    
    """
    from guiqwt.styles import BRUSHSTYLE_CHOICES
    i = 0
    for s in BRUSHSTYLE_CHOICES:
        print('Brush style Choices [%d] = %s' % (i, s[0])) 
        i += 1
    print()
        
def dump_style_options(self):
    self.dump_curve_styles()
    self.dump_line_styles()
    self.dump_marker_choices()
    self.dump_brushstyle_choices()
    self.dump_marker_style_choices()
    
def get_histogram_style(color):
    dct = {}
    dct['line'] = {}
    dct['line']['style'] = 'SolidLine'
    dct['line']['color'] = color
    dct['line']['width'] = 1.0
    
    dct['symbol'] = {}
    dct['symbol']['size'] = 8
    dct['symbol']['alpha'] = 0.0
    dct['symbol']['edgecolor'] =  color
    dct['symbol']['facecolor'] =  color
    
    #dct['symbol']['edgecolor'] =  rgb_as_hex('rgb(128, 128, 128)')
    #dct['symbol']['facecolor'] =  rgb_as_hex(master_colors['plot_forgrnd'])
    dct['symbol']['marker'] = 'NoSymbol'
    
    #dct['curvestyle'] = 'Lines'
    dct['curvestyle'] = 'Steps'
    dct['curvetype'] = 'Yfx'
    
    dct['shade'] = 0.75
    dct['fitted'] = False
    dct['baseline'] = 0.0
    
    
    return(dct)
    
def get_basic_line_style(color, marker='NoSymbol', width=1.0):
    dct = {}
    
#   refer to CurveParam in guiqwt.styles
    dct['line'] = {}
    dct['line']['style'] = 'SolidLine'
    dct['line']['color'] = color
    dct['line']['width'] = width
    
    dct['symbol'] = {}
    dct['symbol']['size'] = 7
    dct['symbol']['alpha'] = 0.0
    dct['symbol']['edgecolor'] =  color
    dct['symbol']['facecolor'] =  color
    #dct['symbol']['marker'] = 'Diamond'
    #dct['symbol']['marker'] = 'NoSymbol'
    #dct['symbol']['marker'] = 'Star1'
    dct['symbol']['marker'] = marker
    
    dct['curvestyle'] = 'Lines'
    dct['curvetype'] = 'Yfx'
    
    
    dct['shade'] = 0.00
    dct['fitted'] = False
    dct['baseline'] = 0.0
    
    return(dct)


def get_trigger_line_style(color, marker='NoSymbol'):
    dct = {}

    #   refer to CurveParam in guiqwt.styles
    dct['line'] = {}
    dct['line']['style'] = 'NoPen'
    dct['line']['color'] = color
    dct['line']['width'] = 1.0

    dct['symbol'] = {}
    dct['symbol']['size'] = 7
    dct['symbol']['alpha'] = 0.0
    dct['symbol']['edgecolor'] = color
    dct['symbol']['facecolor'] = color
    # dct['symbol']['marker'] = 'Diamond'
    # dct['symbol']['marker'] = 'NoSymbol'
    # dct['symbol']['marker'] = 'Star1'
    dct['symbol']['marker'] = marker

    dct['curvestyle'] = 'Lines'
    dct['curvetype'] = 'Yfx'

    dct['shade'] = 0.40
    dct['fitted'] = False
    dct['baseline'] = 0.0

    return (dct)


def make_gridparam(rgb_color):
    hex_str = rgb_as_hex(rgb_color)
    gridparam = make.gridparam(background="%s" % hex_str, 
                                       minor_enabled=(False, False), 
                                       major_enabled=(True,True))
            #self.gridparam.maj_line.color = '#626262'
            #self.gridparam.min_line.color = '#626262'
    return(gridparam)

class AutoScaleTool(ToggleTool):
    changed = QtCore.pyqtSignal(object)
    #def __init__(self, manager, icon="move.png", toolbar_id=DefaultToolbarID):
    def __init__(self, manager, icon=os.path.join(icoDir, 'autoScale.ico'), toolbar_id=DefaultToolbarID):
        super(AutoScaleTool,self).__init__(manager, _("AutoScale"),
                                        icon=icon,
                                        toolbar_id=toolbar_id)
        self.action.setCheckable(True)
        self.action.setChecked(True)
        
    def activate_command(self, plot, checked):
        """Activate tool"""
        self.changed.emit(checked)    

class ClearPlotTool(ToggleTool):
    changed = QtCore.pyqtSignal(object)
    #def __init__(self, manager, icon="xcursor", toolbar_id=DefaultToolbarID):
    def __init__(self, manager, icon=os.path.join(icoDir, 'restart.ico'), toolbar_id=DefaultToolbarID):

        super(ClearPlotTool,self).__init__(manager, _("Clear Plot"),
                                        icon=icon,
                                        toolbar_id=toolbar_id)
        self.action.setCheckable(True)
        
    def activate_command(self, plot, checked):
        """Activate tool"""
        self.changed.emit(checked)    

class DataAcqSaveAsTool(SaveAsTool):
    filename = QtCore.pyqtSignal(object)
    
    def __init__(self, manager):
        super(DataAcqSaveAsTool,self).__init__(manager)
    def activate_command(self, plot, checked):
        """Activate tool"""
        #print 'myData saver tool called'
        formats = '\n%s (*.dat)' % _('Data Acquisition data')
        fname = getsavefilename(plot,  _("Save as"), _('untitled'), formats)
        if fname:
            print('saving csv file [%s]' % fname)
            self.filename.emit(fname)

class CurveViewerWidget(CurveDialog):
    
    save_file = QtCore.pyqtSignal(object)
    right_mouse_click = QtCore.pyqtSignal(object)
    dropped = QtCore.pyqtSignal(QtCore.QMimeData)
    
    def __init__(self, winTitleStr = "Plot Viewer", 
                 toolbar = False,
                 type='basic',
                 filtStr="*.hdf5",  
                 options = {},
				 parent=None):
        
        if('gridparam' not in list(options.keys())):
            #then use a default one
            options['gridparam'] = gridparam = make.gridparam(background="#3e3e3e",
                                       minor_enabled=(False, False),
                                       major_enabled=(True,True))
        self.parent = parent
        CurveDialog.__init__(self, edit=False, toolbar=toolbar, wintitle = winTitleStr,
                      #options=dict(title="", xlabel="xlabel", ylabel="ylabel"))
                      options=options, parent=parent)
        
        # a list variable that will hold all of the plot items so that I can 
        #easily clear them for another plot
        self._plot_items = []
        self.fileFilterStr = filtStr
        self.addtoplot = False
        self.plot = self.get_plot()
        pcan = self.plot.canvas()
        pcan.setObjectName('plotBgrnd')
        pcan.setStyleSheet('background-color: rgb(5,5,5);')
        self.plot.set_axis_font("left", QtGui.QFont("Courier"))
        #self.get_itemlist_panel().show()
        #self.plot.set_items_readonly(False)
        
        self.setMinimumSize(100,150)
        self.curve = None
        self.datFileData = None
        self.plotData = None
        self.plotDataCntr = 0
        self.xData = None
        self.yData = None
        self.maxPoints = 0
        self.curve_item = None
        self.plotTimer = None
        self.timerEnabled = False
        self.setAcceptDrops(True)
        self.drop_enabled = True
        self.max_seconds = 300 #5 minute rolling window
        self.autoscale_enabled = True
        self._data_dir = ""
        self.data_io = None
        self.type = type
        if(self.type == 'basic'):
            self.regTools = self.register_basic_tools
        elif(self.type == 'viewer'):
            self.regTools = self.register_viewer_tools
        else:
            self.regTools = self.register_basic_tools
        
        #legend = make.legend("TL") 
        #self._addItems(legend)
        
        self.plot.SIG_ITEMS_CHANGED.connect(self.items_changed)
        #self.connect(self.plot, SIG_RANGE_CHANGED, self.range_changed)
        self.dropped.connect(self.updateFormatsTable)
        
        self.curve_objs = {}

        self.style_btn = QtWidgets.QPushButton('Set Style')
        self.style_btn.clicked.connect(self.update_style)

        #vbox = QtWidgets.QVBoxLayout()
        #vbox.addWidget(self.plot)
        #self.layout().addWidget(self.style_btn)
        #self.setLayout()
    def set_enable_drop_events(self, en):
        self.drop_enabled = en

    def dragEnterEvent(self, event):
        if(self.drop_enabled):
            event.acceptProposedAction()
            self.dropped.emit(event.mimeData())

    def dragMoveEvent(self, event):
        if(self.drop_enabled):
            event.acceptProposedAction()

    def dropEvent(self, event):
        if(self.drop_enabled):
            #import simplejson as json
            mimeData = event.mimeData()
            if mimeData.hasImage():
                # self.setPixmap(QtGui.QPixmap(mimeData.imageData()))
                #print 'dropEvent: mime data has an IMAGE'
                pass
            elif mimeData.hasHtml():
                # self.setText(mimeData.html())
                # self.setTextFormat(QtCore.Qt.RichText)
                #print 'dropEvent: mime data has HTML'
                pass
            elif mimeData.hasText():
                # self.setText(mimeData.text())
                # self.setTextFormat(QtCore.Qt.PlainText)
                # print 'dropEvent: mime data has an TEXT = \n[%s]' %
                # mimeData.text()
                dct = mime_to_dct(mimeData)
                #print 'dropped file is : %s' % dct['file']
                self.blockSignals(True)

                self.openfile(dct['file'], scan_type=dct['scan_type_num'])
                self.blockSignals(False)
            elif mimeData.hasUrls():
                #self.setText("\n".join([url.path() for url in mimeData.urls()])){"polarity": "CircLeft", "angle": 0.0, "center": [-419.172, 5624.301], "energy": 1029.0, "step": [110.86591666666668, 114.90791666666667], "scan_type": "coarse_image_scan Line_Unidir", "range": [2660.782, 2757.79], "file": "S:\\STXM-data\\Cryo-STXM\\2017\\guest\\1207\\C171207014.hdf5", "offset": 0.0, "npoints": [25, 25], "dwell": 30.408937142857148, "scan_panel_idx": 8}
                #print 'dropEvent: mime data has URLs'
                pass
            else:
                #self.setText("Cannot display data")
                #print 'dropEvent: mime data Cannot display data'
                pass

            # self.setBackgroundRole(QtGui.QPalette.Dark)
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        if(self.drop_enabled):
            event.accept()

    def updateFormatsTable(self, mimeData=None):
        # self.formatsTable.setRowCount(0)
        if(self.drop_enabled):
            if mimeData is None:
                return

            for format in mimeData.formats():
                formatItem = QtWidgets.QTableWidgetItem(format)
                formatItem.setFlags(QtCore.Qt.ItemIsEnabled)
                formatItem.setTextAlignment(
                    QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)

                if format == 'text/plain':
                    text = mimeData.text()  # .strip()
                elif format == 'text/html':
                    text = mimeData.html()  # .strip()
                elif format == 'text/uri-list':
                    text = " ".join([url.toString()
                                     for url in mimeData.urls()])
                else:
                    text = " ".join(["%02X" % ord(datum)
                                     for datum in mimeData.data(format)])

                #row = self.formatsTable.rowCount()
                # self.formatsTable.insertRow(row)
                #self.formatsTable.setItem(row, 0, QtWidgets.QTableWidgetItem(format))
                #self.formatsTable.setItem(row, 1, QtWidgets.QTableWidgetItem(text))
                # print text

            # self.formatsTable.resizeColumnToContents(0)

    def update_style(self):
        ss = get_style('dark')
        self.setStyleSheet(ss)


    def set_dataIO(self, data_io_cls):
        self.data_io = data_io_cls
    
    def set_data_dir(self, ddir):
        """
        set_data_dir(): description

        :param ddir: ddir description
        :type ddir: ddir type

        :returns: None
        """
        """
        set a durectory to use when calling openfile()
        """
        self._data_dir = ddir
        #self.opentool.set_directory(self._data_dir)
    
        
    def register_basic_tools(self):
        """
        register_basic_tools(): description

        :returns: None
        """
        self.opentool = self.add_tool(tools.clsOpenFileTool, formats=self.fileFilterStr)
        self.opentool.set_directory(self._data_dir)
        #self.connect(self.opentool, SIGNAL("openfile(QString*)"), self.openfile)
        self.opentool.openfile.connect(self.openfile)
        self.selectTool = self.add_tool(SelectTool)
        #self.selectTool = self.add_tool(tools.clsSelectTool)
        ast = self.add_tool(AutoScaleTool)
        ast.changed.connect(self.enable_auto_scale)
        
        cpt = self.add_tool(ClearPlotTool)
        cpt.changed.connect(self.do_clear_plot)
        #self.selectTool.changed.connect(self.on_select_tool_changed)
        self.add_separator_tool()
        self.add_tool(PrintTool)

        self.set_default_tool(self.selectTool)
        self.get_default_tool().activate()

    def register_viewer_tools(self):
        """
        register_viewer_tools(): description

        :returns: None
        """
        self.opentool = self.add_tool(tools.clsOpenFileTool, formats=self.fileFilterStr)
        self.opentool.set_directory(self._data_dir)
        # self.connect(self.opentool, SIGNAL("openfile(QString*)"), self.openfile)
        self.opentool.openfile.connect(self.openfile)
        self.selectTool = self.add_tool(SelectTool)
        # self.selectTool = self.add_tool(tools.clsSelectTool)

        cpt = self.add_tool(ClearPlotTool)
        cpt.changed.connect(self.do_clear_plot)
        # self.selectTool.changed.connect(self.on_select_tool_changed)
        self.add_separator_tool()
        self.add_tool(PrintTool)

        self.set_default_tool(self.selectTool)
        self.get_default_tool().activate()

    def set_grid_parameters(self, bkgrnd_color, min_color, maj_color):
        """ 
        .. todo::
        there are man other image params that could be set in teh future, for now only implemented min/max
        GridParam:
            Grid:
                Background color: #eeeeee
                maj:
                  : True
                  : True
                  LineStyleParam:
                    Style: Dotted line
                    Color: #121212
                    Width: 1
                min:
                  : False
                  : False
                  LineStyleParam:
                    Style: Dotted line
                    Color: #121212
                    Width: 1
                                
        """
        aplot = self.plot
        gparam = GridParam()
        gparam.background = bkgrnd_color
        gparam.maj_line.color = maj_color
        gparam.min_line.color = min_color
        aplot.grid.set_item_parameters({"GridParam":gparam})
        
    def enable_auto_scale(self, val):
        #if(val):
        #    print 'enable_auto_scale is ON'
        #else:
        #    print 'enable_auto_scale is OFF'    
        self.autoscale_enabled = bool(val)
        
    def do_clear_plot(self, val):
        self.reset_curve()
            
    def add_legend(self, location="TL"):
        """
        options for location are (from guiqwt/styles.py):
            "TL"  = Top left
            "TR" = Top right
            "BL" = Bottom left
            "BR" = Bottom right
            "L" = Left
            "R" = Right
            "T" = Top
            "B" = Bottom
            "C" = Center
            
        """
        options = ['TL', 'TR', 'BL', 'BR', 'L', 'R','T', 'B', 'C']
        if(location not in options):
            _logger.error('location [%s] is not valid' % location)
            return
        legend = make.legend(location) 
        self._addItems(legend)
    
    def set_time_window(self, curve_names_list, val):
        self.max_seconds = val
        for curve_name in curve_names_list:
            self.curve_objs[curve_name].set_time_window(val)
    
    def addXPoint(self,curve_name, point, update=False):
        self.curve_objs[curve_name].add_x_point(point, update)
        if(update):
            self.set_autoscale()
    
    def addPoint(self, curve_name, point, update=False):
        self.curve_objs[curve_name].add_point(point, update)
        if(update):
            self.set_autoscale()
    
    def addXYPoint(self,curve_name, xpoint, point, update=False):
        #print 'cureviewer: addXYPoint: %s, x=%d, point=%d' % (curve_name, xpoint, point)
        self.curve_objs[curve_name].add_xy_point(xpoint, point, update)  
        if(update):
            self.set_autoscale()

    
    def setXYData(self, curve_name, x, y, update=False):
        self.curve_objs[curve_name].setXYData(x, y)  
        if(update):
            self.set_autoscale()
    
    def incr_plot_counter(self):
        self.plotDataCntr += 1
    
    def update_curve(self):
        self.plot.replot()
    
    def create_curve(self, curve_name, x=None, y=None, curve_style=None):
        if(y is None):
            num_points = 0
        else:
            num_points = len(y)
        
        if(curve_style is None):
            curve_style = get_basic_line_style(get_next_color(use_dflt=False))
                
        self.curve_objs[curve_name] = curve_Obj(curve_name,x,y,num_points=num_points,curve_style=curve_style)
        self.curve_objs[curve_name].changed.connect(self.update_curve)
        self._addItems(self.curve_objs[curve_name].curve_item)
        #self._addItems(self.curve_objs[curve_name].range)        
        #self._addItems(self.curve_objs[curve_name].comp1)
        #self.curve_objs[curve_name].adjust_range()
    
    def reset_curve(self, curve_name=None):
        if(curve_name is None):
            curve_name = list(self.curve_objs.keys())[0]
                
        self.curve_objs[curve_name].reset_curve()
            
    def set_add_to_plot(self, on):
        self.addtoplot = on
            
#     def openfile(self, fileName):
#         #print 'openfile called for file: %s' % fileName 
#         if(self.addtoplot == False):
#             self.clear_plot()
#             
#         if fileName: 
#             self.datFilename = fileName
#             t = fileName.split('/')
#             titleName = t[-1]
#             datStrs = readColumnStrs(str(fileName))
#             idx = 0
#             arr = loadDatToArray(str(fileName))
#             xdata = arr.take([1],axis=1)
#             sz = xdata.shape[0]
#             #make a 1d array of appropriate size
#             xdata = np.reshape(xdata,(sz,))
#             
#             for i in range(2,len(arr[0])):
#                 ydata = arr.take([i],axis=1)
#                 ydata = np.reshape(ydata,(sz,))
#                 curve_name = datStrs[i-1]
#                 self.create_curve(curve_name, xdata,ydata)
#             
#             self.setPlotAxisStrs(titleName, datStrs[0], 'units')
#             self.set_autoscale()
    
    def install_data_io_handler(self, data_io_hndlr):
        self.data_io = data_io_hndlr
    
    def openfile(self, fname, scan_type=scan_types.SAMPLE_POINT_SPECTRA):
        """
        openfile(): currently only supports 1 counter per entry

        :param fname: full path to the desired file
        :type fname: string

        :returns: None
        """
        if(self.data_io is None):
            _logger.error('No data IO module registered')
            return
            
        fname = str(fname)
        data_dir, fprefix, fsuffix = get_file_path_as_parts(fname)
        if(data_dir is None):
            _logger.error('Problem with file [%s]' % fname)
            return
        self.clear_plot()
        #data_io = DataIo(data_dir, fprefix, fsuffix)
        data_io = self.data_io(data_dir, fprefix)
        entry_dct = data_io.load()
        if(entry_dct is None):
            _logger.error('No entry in datafile')
            return
        ekeys = sorted(entry_dct.keys())
        for ekey in ekeys:
            entry = entry_dct[ekey]
            nx_datas = data_io.get_NXdatas_from_entry(entry_dct, ekey)
            #currently only support 1 counter
            #counter_name = nx_datas.keys()[0]
            counter_name = DNM_DEFAULT_COUNTER
            nx_data_dct = data_io.get_data_from_NXdatas(nx_datas, counter_name)
            axes = data_io.get_axes_list_from_NXdata(nx_datas, counter_name)

            if(scan_type is scan_types.GENERIC_SCAN):
                xdata, ydata = self.get_xydata_from_generic_scan(entry, data_io, counter_name)
            else:
                xdata = data_io.get_axes_data_by_index_in_NXdata(nx_datas, counter_name, 0)
                ydata = data_io.get_signal_data_from_NXdata(nx_datas, counter_name)
            
                if((xdata.ndim is not 1) or (ydata.ndim is not 1)):
                    _logger.error('Data in file [%s] is of wrong dimension, is [%d, %d] should be [1, 1]' % (fname, xdata.ndim, ydata.ndim))
                    print('Data in file [%s] is of wrong dimension, is [%d, %d] should be [1, 1]' % (fname, xdata.ndim, ydata.ndim))
                    return
            
            
            #data.shape
            wdg_com = data_io.get_wdg_com_from_entry(entry_dct, ekey)
            
            self.create_curve(ekey, xdata, ydata)

        self.plot.set_title('%s%s' % (fprefix, fsuffix))
        self.setPlotAxisStrs('counts', axes[0])
        self.set_autoscale()

    def get_xydata_from_generic_scan(self, entry_dct, data_io, counter):
        '''
        ekey = get_first_entry_key(self.dct)
        entry_dct = self.dct['entries'][ekey]
        sp_db = get_first_sp_db_from_entry(entry_dct)
        xdata = get_axis_setpoints_from_sp_db(sp_db, axis='X')
        ydatas = get_generic_scan_data_from_entry(entry_dct, counter=DNM_DEFAULT_COUNTER)

        :param entry_dct:
        :param data_io:
        :param counter:
        :return:
        '''
        sp_db = data_io.get_first_sp_db_from_entry(entry_dct)
        xdata = data_io.get_axis_setpoints_from_sp_db(sp_db, axis='X')
        ydata = data_io.get_generic_scan_data_from_entry(entry_dct, counter=DNM_DEFAULT_COUNTER)[0]

        #if ((xdata.ndim is not 1) or (ydata.ndim is not 1)):
        if (len(xdata) is len(ydata)):
            _logger.error(
                'Data is of unequal lengths xdata=%d ydata=%d' % (len(xdata), len(ydata)))
            print('Data is of unequal lengths xdata=%d ydata=%d' % (len(xdata), len(ydata)))
            return (None, None)
        return(xdata, ydata)


        
        
    
    def set_autoscale(self):
        plot = self.get_plot()
        if(self.autoscale_enabled):
            plot.do_autoscale(replot=True)
        #else:
        #    plot.do_autoscale(replot=False)
        
    def saveFile(self, filename):
        #this will save the file as was received from the data acquisition, the files
        #should look the same
        print('CurveViewerWidget: saveFile called [%s]' % filename)
        self.save_file.emit(filename)

    
    def clear_actions(self):
        tb = self.get_toolbar()
        actions = tb.actions()
        for action in actions:
            tb.removeAction(action)
        
    def reg_striptool_tools(self):
        self.clear_actions()
        #opentool = self.add_tool(OpenFileTool, "*.dat")
        #self.connect(opentool, SIGNAL("openfile(QString*)"), self.openfile)
        #opentool.openfile.connect(self.openfile)
        
        self.opentool = self.add_tool(tools.clsOpenFileTool, formats=self.fileFilterStr)
        self.opentool.set_directory(self._data_dir)
        #self.connect(self.opentool, SIGNAL("openfile(QString*)"), self.openfile)
        self.opentool.openfile.connect(self.openfile)
        
        
        saveTool = self.add_tool(DataAcqSaveAsTool)
        saveTool.filename.connect(self.saveFile)
        
        ast = self.add_tool(AutoScaleTool)
        ast.changed.connect(self.enable_auto_scale)
        
        cpt = self.add_tool(ClearPlotTool)
        cpt.changed.connect(self.do_clear_plot)
        #self.set_default_tool(self.selectTool)
        #self.get_default_tool().activate()
    
#     def regTools(self):
#         self.clear_actions()
#         opentool = self.add_tool(OpenFileTool, "*.dat")
#         self.connect(opentool, SIGNAL("openfile(QString*)"), self.openfile)
#         saveTool = self.add_tool(DataAcqSaveAsTool)
#         saveTool.filename.connect(self.saveFile)
#         
#         ast = self.add_tool(AutoScaleTool)
#         ast.changed.connect(self.enable_auto_scale)
#         
#         cpt = self.add_tool(ClearPlotTool)
#         cpt.changed.connect(self.do_clear_plot)
#         #self.set_default_tool(self.selectTool)
#         #self.get_default_tool().activate()    
        
    def items_changed(self, plot):
        #disable region select tool
        self.get_default_tool().activate()
        
    def range_changed(self, rnge, min, max):
        #SIG_RANGE_CHANGED = SIGNAL("range_changed(PyQt_PyObject,double,double)")
        #print 'SIG_RANGE_CHANGED: caught with values (%f, %f)' % (min, max)
        pass
    
    def show_items_panel(self):
        self.get_itemlist_panel().show()
        self.plot.set_items_readonly(False)
    
    def addTool(self, toolstr):
        """ a function that allows inheriting widgets to add tools
        where tool is a valid guiqwt tool """
        
        if(toolstr == 'LabelTool'):
            self.add_tool(LabelTool)
        elif(toolstr == 'SegmentTool'):
            self.add_tool(SegmentTool)
        elif(toolstr == 'RectangleTool'):
            self.add_tool(RectangleTool)
        elif(toolstr == 'CircleTool'):
            self.add_tool(CircleTool)
        elif(toolstr == 'EllipseTool'):
            self.add_tool(EllipseTool)
        elif(toolstr == 'MultiLineTool'):
            self.add_tool(MultiLineTool)
        elif(toolstr == 'FreeFormTool'):
            self.add_tool(FreeFormTool)
        elif(toolstr == 'PlaceAxesTool'):
            self.add_tool(PlaceAxesTool)
        elif(toolstr == 'HRangeTool'):
            self.add_tool(HRangeTool)
        elif(toolstr == 'AnnotatedRectangleTool'):
            self.add_tool(AnnotatedRectangleTool)
        elif(toolstr == 'AnnotatedCircleTool'):
            self.add_tool(AnnotatedCircleTool)
        elif(toolstr == 'AnnotatedEllipseTool'):
            self.add_tool(AnnotatedEllipseTool)
        elif(toolstr == 'AnnotatedSegmentTool'):
            self.add_tool(AnnotatedSegmentTool)
        elif(toolstr == 'AnnotatedPointTool'):
            self.add_tool(AnnotatedPointTool)

    def _setCurveItem(self, item):
        self.curve_item = item
        self.plot = self.get_plot()
        if self.plot is not None:
            self.plot.add_item(self.curve_item)
        
    def _signal_change(self, **kw):
        point = kw['value']
        #print 'signal(%d)' % point
        self.addPoint(point)
        
    #update curve is called by the timer, it will take the data that was
    #delivered and updated by the callback '_signal_change()', the plotting
    #Painter complains with teh following:
    #error message: 'Cannot send posted events for objects in another thread'
    #so to handle plotting updates then when connecting to data from a pv
    #I use a timer that calls this function to update the plotting curve    
    def _update_curve(self):
        #---Update curve
        if(self.curve_item is not None):
            # here only update the 
            #self.curve_item.set_data(self.xData, self.yData)
            self.curve_item.set_data(self.xData[0:self.plotDataCntr], self.yData[0:self.plotDataCntr])
            self.curve_item.plot().replot()
        #---
        if(self.plotTimer is not None):
            if(self.timerEnabled == False):
                self.plotTimer.stop()


    def clear_plot(self):
        reset_color_idx()
        for item in self._plot_items:
            self.delPlotItem(item, replot = True)      
        
        self.set_autoscale()  

    #add the items to the plot 
    def _addItems(self, *items):
        plot = self.get_plot()
        for item in items:
            plot.add_item(item)
            self._plot_items.append(item)
            
    def delPlotItem(self, item, replot=True):
        #Don't delete the legend
        try:
            #print 'item: %s'  % item.title().text()
            if(item.title().text() != 'Legend'):
                #print 'deleting %s'  % item.title().text()
                self.plot.del_item(item)
                if(replot):
                    self.plot.replot()
        except:
            pass
        
    #set the X and Y axis strings        
    def setPlotAxisStrs(self, ystr=None, xstr=None):
        self.plot = self.get_plot()
        # set axis titles
        if(ystr != None):
            self.plot.setAxisTitle(Qwt.QwtPlot.yLeft, ystr)
        if(xstr != None):
            self.plot.setAxisTitle(Qwt.QwtPlot.xBottom,xstr)
            
        self.plot.setAxisTitle(Qwt.QwtPlot.xTop, '')    
        self.plot.setAxisTitle(Qwt.QwtPlot.yRight, '')    
    
    def setPlotTitleAndAxisStrs(self, title=None, xstr=None, ystr=None):
        self.plot = self.get_plot()
        if(title != None):
            self.plot.set_title(title)
        # set axis titles
        if(xstr != None):
            self.plot.setAxisTitle(Qwt.QwtPlot.xBottom,xstr)
        if(ystr != None):
            self.plot.setAxisTitle(Qwt.QwtPlot.yLeft, ystr)            
 
    def mousePressEvent(self, ev):
        #print 'StxmImageWidget: mouse pressed'
        if ev.buttons() == Qt.LeftButton:
#            #print 'left mouse button pressed'
#            #check to see if the user is using one of the selection tools, if so
#            # then set the name of the active plot item, if you can
#            tool = self.plot.manager.get_active_tool()
#            if(isinstance(tool, AverageCrossSectionTool)):
#                #print 'Average selection tool selected'
#                self.roiNum += 1
#            elif(isinstance(tool, AnnotatedSegmentTool)):
#                #print 'AnnotatedSegmentTool tool selected'
#                self.segNum += 1
#            elif(isinstance(tool, AnnotatedPointTool)):
#                #print 'AnnotatedPointTool tool selected'
#                self.pntNum += 1
#                
            return
        if ev.buttons() == Qt.RightButton:
            #print 'right mouse button pressed'
            self.right_mouse_click.emit(self.sender())

#    def mouseReleaseEvent(self, ev):
#        #print 'StxmImageWidget: mouse released'
#        
#        if ev.button() == Qt.LeftButton:
#            #print 'StxmImageWidget: mouse moved with left button pressed'
#            plot = self.get_plot()
#            #pan = plot.get_itemlist_panel()
#            #get all the shapes and turn off their size texts
#            active_item = plot.get_active_item()
#            items = self.plot.get_items(item_type=IShapeItemType)
#            for item in items:
#                if item.is_label_visible() and (item != active_item):
#                    item.set_label_visible(False)
#                #item.position_and_size_visible = False
#                    #pass
#        
#            self.plot.replot()
#            return

    
    #note: these handlers are using Qt4.5 syntax, it changes in Qt4.8.3
#    def mouseMoveEvent(self, ev):
#        
#        if ev.button() == Qt.MidButton:
#            #print 'StxmImageWidget: mouse moved with middle button pressed'
#            return
#        elif ev.button() == Qt.LeftButton:
#            #print 'StxmImageWidget: mouse moved with left button pressed'
#            #self.manager.update_cross_sections()
#            
#            return
#        elif ev.button() == Qt.RightButton:
#            #print 'StxmImageWidget: mouse moved with right button pressed'
#            return
#        
#        
#    def wheelEvent(self, ev):
#        pass
#        #print 'StxmImageWidget: wheel event'    
    
 
def make_spectra_viewer_window(data_io=None):
    if (data_io is None):
        from cls.data_io.stxm_data_io import STXMDataIo
        data_io = STXMDataIo

    win = CurveViewerWidget(toolbar=True, type='viewer')
    win.set_dataIO(data_io)
    return(win)


if __name__ == "__main__":

    import sys
    from cls.appWidgets.spyder_console import ShellWidget#, ShellDock
    from cls.data_io.stxm_data_io import STXMDataIo
    from guiqwt.builder import make
    
    app = QtWidgets.QApplication(sys.argv)
    #show_std_icons()
    win = CurveViewerWidget(toolbar=True)
    win.set_data_dir(r'S:\STXM-data\Cryo-STXM\2017\guest\0106')
    win.regTools()
    win.add_legend("TL")
    win.set_dataIO(STXMDataIo)
    
    num_specs = 8
    num_spec_pnts = 100
    
    for i in range(num_specs):
        clr = get_next_color(use_dflt=False)
        style = get_basic_line_style(clr)
        #style = get_histogram_style(clr)
        win.create_curve('point_spectra_%d' % i,curve_style=style)
    
    #data = np.linspace(0.0, 30.0, num=num_spec_pnts)
    x = np.linspace(-np.pi, np.pi, 201)
    data = np.sin(x)

    for i in range(num_spec_pnts):
        for j in range(num_specs):
            win.addXYPoint('point_spectra_%d' % j, i, data[i]*j, update=True)
            
    
    ns = {'win': win, 'g':globals() }
        #msg = "Try for example: widget.set_text('foobar') or win.close()"
    #pythonshell = ShellWidget(parent=None, namespace=ns,commands=[], multithreaded=True)
    #win.layout().addWidget(pythonshell)
    
    win.show()
    
    sys.exit(app.exec_())
    #print "all done"
