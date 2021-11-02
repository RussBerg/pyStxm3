'''
Created on Dec 5, 2016

@author: control
'''
from PyQt5 import QtCore

import numpy as np

from guiqwt.builder import make

from cls.scanning.dataRecorder import DataIo
from cls.utils.fileUtils import get_file_path_as_parts

class curve_Obj(QtCore.QObject):

    changed = QtCore.pyqtSignal(object)
    
    def __init__(self, name, 
                 x=None, 
                 y=None, 
                 num_points = 1, 
                 curve_style='Steps'):
        
        super(curve_Obj, self).__init__()
        
        self.name = name
        self.max_points = 50000
        self.plotDataCntr = 0
        self.range = None
        self.comp1 = None
        self.xData = x
        self.yData = y        
        self.curve_item = None
        self.enableRange = False
        self.resetting = False
        #the following is in seconds
        self.min_rolling_window = 0
        self.max_rolling_window = self.max_points
        self.curve_style = curve_style
        
        
        if((x is not None) and (y is not None)):
            self.initXYCurve(num_points)
            self.setXYData(x,y)
        else:
            self.init_data(num_points)
            self.initXYCurve(num_points)
    
        
    
    def range_enable(self, enable=False):
        self.enableRange = enable  
    
    def set_time_window(self, val):
        val = int(val)
        if(val <= self.max_rolling_window):
            if(self.plotDataCntr < val):
                self.max_rolling_window = val
                self.xData = np.resize(self.xData,(val,))
                self.yData = np.resize(self.yData,(val,))
                #self.xData = self.roll_left(self.xData,n = self.max_rolling_window - val)
                #self.yData = self.roll(self.yData,n = self.max_rolling_window - val)
            else:
                #roll data to the left so that we have the last window size worth of data
                self.xData = self.roll_left(self.xData,n =  val )
                self.yData = self.roll_left(self.yData,n =  val )
                
        else:
            self.max_rolling_window = val
            self.xData = np.resize(self.xData,(val,))
            self.yData = np.resize(self.yData,(val,))

    def roll_left(self, a, n=1):
        startIdx = self.plotDataCntr - n
        a = a[startIdx : self.plotDataCntr]
        self.plotDataCntr = a.shape[0]
        self.max_rolling_window = n
        return(a)    
    
    def init_data(self, num_points):
        self.xData = np.zeros(self.max_rolling_window, dtype=np.float)
        self.yData = np.zeros(self.max_rolling_window, dtype=np.float)
    
    def reset_curve(self):
        self.resetting = True
        self.plotDataCntr = 0
        
        
    def get_curve_item(self):
        return(self.curve_item)
    
    def setXYData(self, x, y):
        #print 'setXYData'
        #this is used to assign a complete array to a plot, like loading a file
        #newer versions of guiqwt require these points to be float64
        self.xData = np.array(x).astype('float64')
        self.yData = np.array(y).astype('float64')

        self.plotDataCntr = len(x)
        self.update_plot()
        #self.initXYCurve(len(x))
        self.changed.emit(None)
        
    def adjust_range(self):
        
        bufr = (self.xData.max() - self.xData.min()) * 0.01
        #print 'adjust_range(%f,%f)' % (self.xData.min()-bufr, self.xData.max()+bufr)
        self.range.set_range(self.xData.min()-bufr, self.xData.max()+bufr)
    
    
        # Curve:
#     Title: Histogram #1
#     LineStyleParam:
#       Style: No line
#       Color: blue
#       Width: 1
#     SymbolParam:
#       Style: No symbol
#       Size: 0
#       Border: white
#       Background color: black
#       Background alpha: 1.0
#     Shadow: 0.85
#     Fitting: False
#     Curve style: Steps
#     Curve type: Draws y as a function of x
#     Baseline: 0.0
   
    
    
    
    
    def apply_style(self, curve_item, style_dct):
        
        sections = list(style_dct.keys())
        for section in sections:
            if(section in dir(curve_item)):
                sect_item = getattr(curve_item, '_%s' % section)
                if(type(style_dct[section]) == dict):
                    for _attr in list(style_dct[section].keys()):
                        val = style_dct[section][_attr]
                        setattr(sect_item, '_%s' % _attr, style_dct[section][_attr])
                else:
                    setattr(curve_item, '_%s' % section, style_dct[section])
            
    def initXYCurve(self, num_points):
        #print 'initXYCurve'
        #this is used to init a curve, as well as setup an initial curve that will be dynamically plotted
        #make curve with the next color in line 
        if(num_points == 1):
            self.plotDataCntr = 0
        
        #color=get_next_color()
        #color = self.curve_style['line']['color'][0]
        #print 'color = %s' % color
        #self.curve_item = make.curve(self.xData[0:num_points], self.yData[0:num_points], color=color, linewidth=1.0, title=self.name)
        self.curve_item = make.curve(self.xData[0:num_points], self.yData[0:num_points],linewidth=1.0, title=self.name)
        self.apply_style(self.curve_item.curveparam, self.curve_style)
        #print self.curve_item.curveparam
        #self.curve_item.curveparam._curvestyle = self.curve_style
        #self.curve_item.curveparam._shade = 0.75
#        self.curve_item.curveparam.line._color = rgb_as_hex(master_colors['plot_forgrnd'])

#         hist.curveparam.line
#             LineStyleParam:
#                 Style: No line
#                 Color: blue
#                 Width: 1
#             hist.curveparam.line._style
#             NoPen
#             hist.curveparam.line._color
#             blue
#             hist.curveparam.line._width
#             1

# Curve:
#     Title: Histogram #1
#     LineStyleParam:
#       Style: No line
#       Color: blue
#       Width: 1
#     SymbolParam:
#       Style: No symbol
#       Size: 0
#       Border: white
#       Background color: black
#       Background alpha: 1.0
#     Shadow: 0.85
#     Fitting: False
#     Curve style: Steps
#     Curve type: Draws y as a function of x
#     Baseline: 0.0


        #self.curve_item.curveparam.line._style = 'NoPen'
        #self.curve_item.curveparam.line._color = 'blue'
        #self.curve_item.curveparam.line._width = 1
        
        #self.curve_item.curveparam._symbol.marker='Triangle'
        self.curve_item.update_params()

        self.changed.emit(None)
        x = self.xData
        y = self.yData
        #the following makes an HRANGE tool, default range will be x[start] to x[start] + 2
        #print 'first point of range=%f' % x[0]
        if(self.enableRange):
            self.range = make.range(x.min(), x.max())
        #self.disp1 = make.computation(range, "BL", "trapz=%f", self.curve_item, lambda x,y: trapz(y,x))
#        self.comp1 = make.computations(self.range, "TL",
#                              [(self.curve_item, "Xmin=%.5f", lambda x,y: x.min()),
#                               (self.curve_item, "Xavg=%.5f", lambda x,y: x.mean()),
#                               (self.curve_item, "Xmax=%.5f", lambda x,y: x.max()),
#                               (self.curve_item, "Ymin=%.5f", lambda x,y: y.min()),
#                               (self.curve_item, "Yavg=%.5f", lambda x,y: y.mean()),
#                               (self.curve_item, "Ymax=%.5f", lambda x,y: y.max())])
#   
    def incr_plot_counter(self):
        self.plotDataCntr += 1
        
       
        
    def roll(self, a, val):
        b = a
        sz = b.shape[0]
        c = np.resize(b,(sz+1,))
        c = c[1:]
        c[-1] = val
        return(c)     

    def add_x_point(self, point, update=False):
        #add a point to the end of the array
        
        if(self.plotDataCntr < self.max_points):
            sz = self.xData.shape[0]
            self.xData[self.plotDataCntr] = point
            self.xData = np.resize(self.xData, (sz+1,))
            self.yData = np.resize(self.yData, (sz+1,))
            if(self.enableRange):
                self.adjust_range()
            #print '[%s] adding x point [%d] = %f' % (self.name, self.plotDataCntr, point)
            
        else: 
            pass

        
        
    def add_point(self, point, update=False):
        #add a point to the end of the array
        if(self.plotDataCntr < self.max_points):
            self.yData[self.plotDataCntr] = point
            
            self.incr_plot_counter()
            #print '[%s] adding y point [%d] = %f' % (self.name, self.plotDataCntr, point)
            if(self.plotDataCntr > self.max_rolling_window):
                self.min_rolling_window += 1
            
            if(self.enableRange):
                self.adjust_range()
            
        else: 
            pass
        
        if(update):
            self.update_plot()
    
    def add_xy_point(self, xpoint, point, update=False):
        ''' used when plotting multiple series with a single x axis 
        '''
        
        if(self.resetting):
            self.yData = np.multiply(self.yData, 0)
            self.yData = np.multiply(self.yData, point)
            self.resetting = False
        
        #add a point to the end of the array
        if(self.plotDataCntr >= self.max_rolling_window):
                
            self.xData = self.roll(self.xData,xpoint)
            self.yData = self.roll(self.yData,point)
                
            if(self.enableRange):
                self.adjust_range()
    
            self.plotDataCntr = self.max_rolling_window
            #print '[%s] adding y point [%d] = %f' % (self.name, self.plotDataCntr, point)
                
        else: 
            #print 'max points(%d) reached' % self.maxPoints
            #print 'setting xData[%d] to [%d]' % (self.plotDataCntr, xpoint)
            self.xData[self.plotDataCntr] = xpoint
            self.yData[self.plotDataCntr] = point
            self.incr_plot_counter()
        
        if(update):
            self.update_plot()
            
    def update_plot(self):
        self.curve_item.set_data(self.xData[0 : self.plotDataCntr], self.yData[0 : self.plotDataCntr])
        #self.curve_item.plot().replot()
        self.changed.emit(None)
        
        
    
    def openfile(self, fname, addimages=False):
        """
        openfile(): description

        :param fname: fname description
        :type fname: fname type

        :param addimages=False: addimages=False description
        :type addimages=False: addimages=False type

        :returns: None
        """

        fname = str(fname)
        data_dir, fprefix, fsuffix = get_file_path_as_parts(fname)
        if(data_dir is None):
            _logger.error('Problem with file [%s]' % fname)
            return
        data_io = DataIo(data_dir, fprefix, fsuffix)
        #ado_obj = data_io.load(only_roi_and_data=True)
        entry_dct = data_io.load()
        ekey = list(entry_dct.keys())[0]
        data = data_io.get_NXdatas_from_entry(entry_dct, ekey)
        wdg_com = data_io.get_wdg_com_from_entry(entry_dct, ekey)
        
        self.load_image_data(fname, wdg_com, data, addimages, flipud=True)
        
        self.on_set_aspect_ratio(True)
        self.update_contrast()