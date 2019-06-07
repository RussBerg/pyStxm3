'''
Created on Oct 5, 2016

@author: bergr
'''
import time

from PyQt5.QtCore import pyqtSignal, QObject
#from bcm.protocol.epics.pv import PV
from epics.pv import PV
#from epics import PV

from epics.device import Device

from bcm.device.base import BaseDevice


class camera_ORIG(BaseDevice):
    changed = pyqtSignal(object)
    acquire_frame = pyqtSignal(int)
    """
     Represents a very basic camera as defined in the epics database calib_camera.db which is
     a part of the blApi epics application, these pv's are merley placeholders that will be filled
     in by an application that wants to read and write to this epics calibration camera instance. 
     """
   
    
    
    #def __init__(self, prefix, num_points=1):
    def __init__(self, prefix, width=640, ht=480, server=True):
        super(camera, self).__init__(prefix)
        self.p_prefix = prefix
        self.cb_idx = []
        self.width = width
        self.height = ht
        #only monitor the data if we are the client
        #only monitor the grab_frame pv if we are the server, 
        #the opposite is true if we are the client
        if(server):
            self.data_pv = PV(self.p_prefix + ':calib_cam:wv_rbv', auto_monitor=False)
            self.grab_frame_pv = PV(self.p_prefix + ':calib_cam:grab_frame')
            self.cb_idx.append(self.grab_frame_pv.add_callback(self.on_grab_frame))
        else:
            self.data_pv = PV(self.p_prefix + ':calib_cam:wv_rbv')#, auto_monitor=True, verbose=True)
            self.grab_frame_pv = PV(self.p_prefix + ':calib_cam:grab_frame')
            #self.cb_idx.append(self.data_pv.add_callback(self.on_new_data))
            self.data_pv.add_callback(self.on_new_data)
        time.sleep(0.2)    
        
    
    def set_image_data(self, _1d_data):
        #self.put('calib_cam:wv_rbv', _1d_data)
        if(self.data_pv):
            self.data_pv.put(_1d_data)
    
    def get_image_data(self):
        #self.put('calib_cam:wv_rbv', _1d_data)
        if(self.data_pv):
            data = self.data_pv.get()
            if((data is not None) and (data.size > 0)):
                if(len(data.shape) == 1):
                    data = data.reshape((self.height, self.width))
                else:
                    data = None
            else:
                data = None
        return(data)    

    def grab_frame(self):
        self.grab_frame_pv.put(1)
    
    def on_grab_frame(self, **kwargs):
        self.acquire_frame.emit(kwargs['value'])
        
    def get_name(self):
        return self.p_prefix
    
    def on_new_data(self, **kwargs):
            
        data = kwargs['value']
        print('on_new_data \n', data[0:10])
        self.changed.emit(data)
    

# class camera(epics.Device):
#     
#     changed = pyqtSignal(object)
#     """
#     Represents a very basic camera as defined in the epics database calib_camera.db which is
#     a part of the blApi epics application, these pv's are merley placeholders that will be filled
#     in by an application that wants to read and write to this epics calibration camera instance. 
#     """
#     #attrs = (':calib_cam:wv_rbv', ':calib_cam:width', ':calib_cam:height', ':calib_cam:clr_depth')
#     
#     def __init__(self, prefix, **kwargs):
#         if prefix.endswith('.'):
#             prefix = prefix[:-1]
#         #epics.Device.__init__(self, prefix, **kwargs)
#         #epics.Device.__init__(self, prefix, delim=':', attrs=self.attrs, **kwargs)
#         #super(camera, self).__init__()
#         #super(camera, self).__init__(prefix)
#         epics.Device.__init__(self, prefix, delim=':', 
#                                attrs=[],
#                                timeout=3.0)
#         
#         self.wv_rbv = epics.PV(prefix + ':calib_cam:wv_rbv', callback=self.on_new_data, auto_monitor=True)
#         #self.ticker_rbv = epics.PV('TRG2400:cycles')
#         #self.width = self.add_pv(prefix + ':calib_cam:width')
#         #self.height = self.add_pv(prefix + ':calib_cam:height')
#         #self.clr_depth = self.add_pv(prefix + ':calib_cam:clr_depth')
#         self.cb_idx = [0,0,0,0,0]
#         #self.wv_rbv.changed.connect(self.changed)
#         #self.cb_idx[0] = self.wv_rbv.add_callback(self.on_new_data)
#         #self.cb_idx[1] = self.ticker_rbv.add_callback(self.on_new_data)
#         #self.wv_rbv.changed.connect(self.on_new_data)
#     
#     def on_new_data(self, **kwargs):
#         data = kwargs['value']
#         #print 'on_new_data ', data[0:50]
#         #print 'on_new_data \n', data
#         #self.changed.emit(kwargs['value'])
#         self.changed.emit(data)
#     
#     def set_image_data(self, _1d_data):
#         #self.put('calib_cam:wv_rbv', _1d_data)
#         self.wv_rbv.put(_1d_data)
#     
#     def set_height(self, ht):
#         #self.put('calib_cam:height', ht)
#         self.height.put(ht)
#     
#     def set_width(self, wd):
#         #self.put('calib_cam:width', wd)
#         self.width.put(wd)
#         
#     def set_color_depth(self, clr_depth):
#         #self.put('calib_cam:clr_depth', clr_depth)
#         self.clr_depth.put(clr_depth)
#         
#     def get_image_data(self):
#         #return(self.get('calib_cam:wv_rbv'))
#         return(self.wv_rbv.get())
#     
#     def get_height(self):
#         #return(self.get('calib_cam:height'))
#         return(self.height.get())
#     
#     def get_width(self):
#         #return(self.get('calib_cam:width'))
#         return(self.width.get())
#         
#     def get_color_depth(self):
#         #return(self.get('calib_cam:clr_depth'))    
#         return(self.clr_depth.get())
#         
        
    
            

if __name__ == "__main__":
    import sys
    
    cam = camera('BL1610-I10:uhv')
    #cam.set_color_depth(33)
    #print cam.get_color_depth()
    
    