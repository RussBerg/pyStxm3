'''
Created on 2014-10-06

@author: bergr
'''
import os, sys
from PyQt5 import QtCore, QtGui

import simplejson as json
from cls.utils.dict_utils import dct_get, dct_put, dct_key_exist
from cls.utils.dirlist import dirlist
from cls.utils.log import get_module_logger
from cls.utils.json_threadsave import ThreadJsonSave
from cls.stylesheets import base_style_sheet_dir

defaultsDir = os.path.dirname(os.path.abspath(__file__))

_logger = get_module_logger(__name__)

#master_colors = {}
# dct_put(master_colors, "master_background_color", "rgb(115,113,115);")
# dct_put(master_colors, "app_green", "rgb(99, 142, 82);")
# dct_put(master_colors, "app_blue", "rgb(114, 148, 240);") #7294F0
# dct_put(master_colors, "app_ltgray", "rgb(165, 165, 165);")
# dct_put(master_colors, "app_medgray", "rgb(115, 113, 115);") # #737173
# dct_put(master_colors, "app_meddrkgray", "rgb(100, 100, 100);") # 
# dct_put(master_colors, "app_drkgray", "rgb(66, 69, 66);") # "#424542"
# 
# dct_put(master_colors, "app_yellow", "rgb(236,236,0);") # 
# 
# #bg_clr = "#8a8a8a"
# #min_clr =  "#a2a2a2"
# #maj_clr = "#a2a2a2"
# 
# dct_put(master_colors, "plot_bckgrnd", "rgb(0,0,0);") #
# dct_put(master_colors, "plot_forgrnd", "rgb(2,116,255);") #0274ff
# dct_put(master_colors, "plot_gridmaj", "rgb(63,63,63);") #3f3f3f
# dct_put(master_colors, "plot_gridmin", "rgb(40,40,40);") #282828
# 
# 
# 
# dct_put(master_colors, "msg_color", "rgb(0, 0, 254);") #


def rgb_as_hex(rgb_str):
    """
    take an rgb string like the ones found in qss stylesheets (ex: 'rgb(0, 128,64);')
    and    return a hex version of it
    """
    #s = 
    s2 = rgb_str.strip('rgb(')
    s2 = s2.strip(');')
    s3 = s2.split(',')
    r = int(s3[0])
    g = int(s3[1])
    b = int(s3[2])
    return('#%02x%02x%02x' % (r,g,b))

def key_val_to_dct(lines):
    dct = {}
    for l in lines:
        if(len(l) > 0):
            l1 = l.split('=')
            k = l1[0].replace(' ','')
            val = l1[1].replace(' ','')
            dct[k] = val
    return(dct)


def get_style(styledir):
    baseDir = os.path.join(base_style_sheet_dir,styledir)
    sheets = dirlist(baseDir , '.qss', fname = None)
    master_colors = dirlist(baseDir , 'master_color_def.txt', fname = None)
    
    mc_dct = {}
    if(len(master_colors) > 0):
        mcFile = os.path.join(baseDir, master_colors[0])
        mf = open(mcFile,"r")
        mc_lines = mf.read().split('\n')
        mc_dct = key_val_to_dct(mc_lines)

    mf.close()
        
    ssheet_str = ''
    for f in sheets:
        #sshFile=baseDir + f
        sshFile = os.path.join(baseDir, f)
        fh = open(sshFile,"r")
        #qstr = QtCore.QString(fh.read())
        qstr = fh.read()
        #qstr = str(fh.read())
        ssheet_str += qstr
        fh.close()
    #put any replacements here    
    #ssheet_str.replace("master_background_color", "rgb(110,110,110)");
    #for clr in master_colors:
    for clr in mc_dct:
        ssheet_str = ssheet_str.replace(clr, mc_dct[clr])
        #print 'get_style: replaced [%s] with [%s]' % (clr, master_colors[clr])
    
    return(ssheet_str)

master_q_colors = {}
dct_put(master_q_colors, "black", QtGui.QColor(0,0,0))
dct_put(master_q_colors, "white", QtGui.QColor(255,255,255))

dct_put(master_q_colors, "master_background_color", QtGui.QColor(115,113,115))
dct_put(master_q_colors, "app_green", QtGui.QColor(99, 142, 82))
dct_put(master_q_colors, "app_blue", QtGui.QColor(114, 148, 240)) #7294F0
dct_put(master_q_colors, "app_ltblue", QtGui.QColor(115, 150, 247))
dct_put(master_q_colors, "app_medblue", QtGui.QColor(94,123, 209))
dct_put(master_q_colors, "app_drkblue",QtGui.QColor(0, 85, 255))
dct_put(master_q_colors, "app_ltgray", QtGui.QColor(165, 165, 165))
dct_put(master_q_colors, "app_medgray", QtGui.QColor(115, 113, 115)) # #737173
dct_put(master_q_colors, "app_meddrkgray", QtGui.QColor(100, 100, 100)) # 
dct_put(master_q_colors, "app_drkgray", QtGui.QColor(66, 69, 66)) # "#424542"
dct_put(master_q_colors, "app_yellow", QtGui.QColor(236,236,0)) # 
dct_put(master_q_colors, "app_red", QtGui.QColor(142,50,50)) #
dct_put(master_q_colors, "app_superltgray", QtGui.QColor(205, 205, 205))
dct_put(master_q_colors, "scan_sts_blue", QtGui.QColor(60, 115, 235)) #7294F0
dct_put(master_q_colors, "fbk_moving_ylw", QtGui.QColor(254, 233, 0))




master_colors = {}
dct_put(master_colors, "black", "rgb(0,0,0);")
dct_put(master_colors, "white", "rgb(255,255,255);")

dct_put(master_colors, "master_background_color", "rgb(115,113,115);")
dct_put(master_colors, "app_green", "rgb(99, 142, 82);")
dct_put(master_colors, "app_ltgreen", "rgb(85,255,127);")
dct_put(master_colors, "app_blue", "rgb(114, 148, 240);") #7294F0
dct_put(master_colors, "app_ltblue", "rgb(115, 150, 247);")
dct_put(master_colors, "app_medblue", "rgb(94,123, 209);")
dct_put(master_colors, "app_drkblue","rgb(0, 85, 255);")
dct_put(master_colors, "app_ltgray", "rgb(165, 165, 165);")
dct_put(master_colors, "app_medgray", "rgb(115, 113, 115);") # #737173
dct_put(master_colors, "app_meddrkgray", "rgb(100, 100, 100);") # 
dct_put(master_colors, "app_drkgray", "rgb(66, 69, 66);") # "#424542"
dct_put(master_colors, "app_yellow", "rgb(236,236,0);") #
dct_put(master_colors, "app_red", "rgb(142,50,50);") #
dct_put(master_colors, "app_superltgray", "rgb(205, 205, 205);")
dct_put(master_colors, "scan_sts_blue", "rgb(60, 115, 235);")
dct_put(master_colors, "fbk_moving_ylw", "rgb(254, 233, 0);")
dct_put(master_colors, "btn_pressed", "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgb(94, 128, 220), stop:1 rgb(72, 99, 174));")

#bg_clr = "#8a8a8a"
#min_clr =  "#a2a2a2"
#maj_clr = "#a2a2a2"

dct_put(master_colors, "plot_bckgrnd", "rgb(0,0,0);") #
dct_put(master_colors, "plot_forgrnd", "rgb(2,116,255);") #0274ff
dct_put(master_colors, "plot_gridmaj", "rgb(63,63,63);") #3f3f3f
dct_put(master_colors, "plot_gridmin", "rgb(40,40,40);") #282828

dct_put(master_colors, "msg_color", "rgb(0, 0, 254);") #

#default zoneplate values
zp1 = {'zp_id': 1, 'a1':-4.840,'D':100.0, 'CsD':45.0, 'OZone': 60.0}
zp2 = {'zp_id': 2, 'a1':-6.792,'D':240.0, 'CsD':90.0, 'OZone': 35.0}
zp3 = {'zp_id': 3, 'a1':-7.767,'D':240.0, 'CsD':90.0, 'OZone': 40.0}
zp4 = {'zp_id': 4, 'a1':-4.524,'D':140.0, 'CsD':60.0, 'OZone': 40.0}
zp5 = {'zp_id': 5, 'a1':-4.859,'D':240.0, 'CsD':95.0, 'OZone': 25.0}
zps = [zp1, zp2, zp3, zp4, zp5]

#default osa definitions
osa1 = {'osa_id': 1, 'D':30.0}
osa2 = {'osa_id': 2, 'D':50.0}
osa3 = {'osa_id': 3, 'D':40.0}
osas = [osa1, osa2, osa3]

class Defaults(QtCore.QObject):
    """
    This class represents the main object for the application defaults
    """
    changed = QtCore.pyqtSignal()
    
    def __init__(self, fname, new=False):
        super(Defaults, self).__init__()
        self.defdct = {}
        self.fname = os.path.join(defaultsDir, fname)
        self.new = new
        self.init_defaults(fname, new)
            
    
    def init_defaults(self, fname, new=False):
        if(new):
            self.defdct = self.init_from_template()
            self.defdct['fpath'] = self.fname
            self.save_json_obj(self.defdct, self.fname)
        else:    
            #read from disk
            self.defdct = self.loadJson(self.fname)
    
    def add_section(self, section, value):
        dct_put(self.defdct, section, value)
        self.update()
        
    
    def init_from_template(self):
        dct = {}
        dct_put(dct, 'APP.UI.COLORS', master_colors)
        
        dct_put(dct, 'PRESETS.OSA.OUT',    (-4000, None) )
        dct_put(dct, 'PRESETS.OSA.ABS_OUT',    (-4000, None) )
        dct_put(dct, 'PRESETS.OSA.CENTER',    (-2416, 882.96) )
        dct_put(dct, 'PRESETS.OSA.ABS_CENTER',    (-2416, 882.96) )
        dct_put(dct, 'PRESETS.DETECTOR.CENTER',    (586, 259) )
        dct_put(dct, 'PRESETS.DETECTOR.ABS_CENTER',    (586, 259) )
        
        dct_put(dct, 'PRESETS.ZP_PARAMS',    zps )
        
        dct_put(dct, 'PRESETS.ZP_FOCUS_PARAMS.ZP_IDX', 0)
        dct_put(dct, 'PRESETS.ZP_FOCUS_PARAMS.ZP_A1', -6.792)
        dct_put(dct, 'PRESETS.ZP_FOCUS_PARAMS.ZP_D', 240.0)
        dct_put(dct, 'PRESETS.ZP_FOCUS_PARAMS.OSA_IDX', 1)
        dct_put(dct, 'PRESETS.ZP_FOCUS_PARAMS.OSA_D', 50.0)
        dct_put(dct, 'PRESETS.ZP_FOCUS_PARAMS.OSA_A0', 534)
        dct_put(dct, 'PRESETS.ZP_FOCUS_PARAMS.OSA_A0MAX',554)
        dct_put(dct, 'PRESETS.ZP_FOCUS_PARAMS.OSA_IDEAL_A0', 534)
        
        dct_put(dct, 'PRESETS.OSA_PARAMS',    osas )
        
        #                                         (x, y, z, ev)
        dct_put(dct, 'SCAN.DETECTOR.CENTER', (586, 259, 0, 0) )
        dct_put(dct, 'SCAN.DETECTOR.RANGE',    (20, 20, 0, 0) )
        dct_put(dct, 'SCAN.DETECTOR.NPOINTS', (20, 20, 0, 0) )
        dct_put(dct, 'SCAN.DETECTOR.STEP', (1, 1, 0, 0) )
        dct_put(dct, 'SCAN.DETECTOR.DWELL',    2.0 )
        
        
        dct_put(dct, 'SCAN.OSA.CENTER',    (586, 259, 0, 0) )
        dct_put(dct, 'SCAN.OSA.RANGE',    (20, 20, 0, 0) )
        dct_put(dct, 'SCAN.OSA.NPOINTS',    (20, 20, 0, 0) )
        dct_put(dct, 'SCAN.OSA.STEP', (1, 1, 0, 0) )
        dct_put(dct, 'SCAN.OSA.DWELL',    2.0 )
        
        dct_put(dct, 'SCAN.OSA_FOCUS.CENTER',    (586, 259, 0, 0) )
        dct_put(dct, 'SCAN.OSA_FOCUS.RANGE',    (20, 20, 0, 0) )
        dct_put(dct, 'SCAN.OSA_FOCUS.NPOINTS',    (20, 20, 0, 0) )
        dct_put(dct, 'SCAN.OSA_FOCUS.STEP', (1, 1, 0, 0) )
        dct_put(dct, 'SCAN.OSA_FOCUS.DWELL',    2.0 )
    
        dct_put(dct, 'SCAN.FOCUS.CENTER',    (586, 259, 0, 0) )
        dct_put(dct, 'SCAN.FOCUS.RANGE',    (20, 20, 0, 0) )
        dct_put(dct, 'SCAN.FOCUS.NPOINTS',    (20, 20, 0, 0) )
        dct_put(dct, 'SCAN.FOCUS.STEP', (1, 1, 0, 0) )
        dct_put(dct, 'SCAN.FOCUS.DWELL',    2.0 )
    
        dct_put(dct, 'SCAN.POINT.CENTER',    (586, 259, 0, 0) )
        dct_put(dct, 'SCAN.POINT.RANGE',    (20, 20, 0, 0) )
        dct_put(dct, 'SCAN.POINT.NPOINTS',    (20, 20, 0, 0) )
        dct_put(dct, 'SCAN.POINT.STEP',    (1, 1, 0, 0) )
        dct_put(dct, 'SCAN.POINT.DWELL',    2.0 )
    
        dct_put(dct, 'SCAN.SAMPLE_PXP.CENTER',    (586, 259, 0, 0) )
        dct_put(dct, 'SCAN.SAMPLE_PXP.RANGE',    (20, 20, 0, 0) )
        dct_put(dct, 'SCAN.SAMPLE_PXP.NPOINTS',    (20, 20, 0, 0) )
        dct_put(dct, 'SCAN.SAMPLE_PXP.STEP', (1, 1, 0, 0) )
        dct_put(dct, 'SCAN.SAMPLE_PXP.DWELL',    2.0 )
    
        dct_put(dct, 'SCAN.SAMPLE_LXL.CENTER',    (586, 259, 0, 0) )
        dct_put(dct, 'SCAN.SAMPLE_LXL.RANGE',    (20, 20, 0, 0) )
        dct_put(dct, 'SCAN.SAMPLE_LXL.NPOINTS',    (20, 20, 0, 0) )
        dct_put(dct, 'SCAN.SAMPLE_LXL.STEP', (1, 1, 0, 0) )
        dct_put(dct, 'SCAN.SAMPLE_LXL.DWELL',    2.0 )
        
        dct_put(dct, 'SCAN.LINE.CENTER',    (586, 259, 0, 0) )
        dct_put(dct, 'SCAN.LINE.RANGE',    (20, 20, 0, 0) )
        dct_put(dct, 'SCAN.LINE.NPOINTS',    (20, 20, 0, 0) )
        dct_put(dct, 'SCAN.LINE.STEP', (1, 1, 0, 0) )
        dct_put(dct, 'SCAN.LINE.DWELL',    2.0 )
    
        
        return(dct)
    
    def get_default_dct(self):
        dct = {}
        dct_put(dct, 'CENTER', (0, 0, 0, 0) )
        dct_put(dct, 'RANGE', (20, 20, 0, 0) )
        dct_put(dct, 'NPOINTS',    (20, 20, 0, 0) )
        dct_put(dct, 'STEP', (1, 1, 0, 0) )
        dct_put(dct, 'DWELL', 2.0 )
        return(dct)
        
    def update(self):
        #_logger.debug('defaults.update()')
        self.save_json_obj(self.defdct, self.fname)
        
    def save_json_obj(self, dct, fname):
        dct['fpath'] = fname
        saveThread = ThreadJsonSave(dct)
        saveThread.setDaemon(True)
        saveThread.start()    
    
    def loadJson(self, filename):
        """internal load json data from disk"""
        if os.path.exists(filename):
            file = open(filename)
            js = json.loads(file.read())
            file.close()
        else:
            print("json file doesn't exist: died")
            js = {}
        return js
    
    def get_scan_def(self, section):
        _roi = self.get(section)
        
        #roi = {}
        #roi['center'] = (_roi[CENTER][0], _roi[CENTER][1])
        #roi['size'] = (_roi[RANGE][0], _roi[RANGE][1])
        #roi['npts'] = (_roi[NPOINTS][0], _roi[NPOINTS][1])
        #roi['all'] = _roi
        
        return(_roi)
    
    def get_focusscan_def(self, section):
        _roi = self.get(section)
        
        #roi = {}
        #roi['center'] = (_roi[CENTER][0], _roi[CENTER][1])
        #roi['size'] = (_roi[RANGE][0], _roi[RANGE][1])
        #roi['npts'] = (_roi[NPOINTS][0], _roi[NPOINTS][1])
        #roi['all'] = _roi
        
        return(_roi)

    def section_exists(self, section):
        if (dct_key_exist(self.defdct, section)):
            return(True)
        else:
            return(False)

    def get(self, name, create=True):
        """ get the object section by name """
        dct = dct_get(self.defdct, name)
        if((dct is None) and create):
            dct = self.get_default_dct()
            self.add_section(name, dct)
                        
        return(dct)
    
    def set(self, name, obj):
        """ get the object section by name """
        dct_put(self.defdct, name, obj)
        self.update()
        
    def get_main_obj(self):
        """ return the entire main object dict """
        return(self.defdct)
    
__all__ = ['Defaults']
