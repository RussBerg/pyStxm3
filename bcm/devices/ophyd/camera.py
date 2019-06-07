'''
Created on Oct 5, 2016

@author: bergr
'''
import time

from PyQt5.QtCore import pyqtSignal
import numpy as np

from bcm.devices import BaseObject


class camera(BaseObject):
    acquire_frame = pyqtSignal(int)
    """
     Represents a very basic camera as defined in the epics database calib_camera.db which is
     a part of the blApi epics application, these pv's are merley placeholders that will be filled
     in by an application that wants to read and write to this epics calibration camera instance. 
     
        CCD1610-I10:uhv:serial_num:fbk
        CCD1610-I10:uhv:start_cap
        CCD1610-I10:uhv:fw_version:fbk
        CCD1610-I10:uhv:model:fbk
        CCD1610-I10:uhv:sensor:fbk
        CCD1610-I10:uhv:vendor:fbk
        CCD1610-I10:uhv:calib_cam:wv:fbk
        
     """

    def __init__(self, base_signal_name, width=640, ht=480):
        super(camera, self).__init__(base_signal_name)

        self.cb_idx = []
        self.width = width
        self.height = ht
        self.data = []
        # only monitor the data if we are the client
        # only monitor the start_cap pv if we are the server,
        # the opposite is true if we are the client
        # self.data_pv = PV(self.p_prefix + ':calib_cam:wv:fbk')#, auto_monitor=True, verbose=True)

        self.data_pv = self.add_device(self.base_signal_name + ':calib_cam:wv:fbk')  # , auto_monitor=True, verbose=True)
        self.start_cap_pv = self.add_device(self.base_signal_name + ':start_cap')

        # self.cb_idx.append(self.data_pv.add_callback(self.on_new_data))
        self.data_pv.changed.connect(self.on_changed)
        # self.changed.connect(self.on_copy_data)
        # time.sleep(0.2)

    def start_capture(self):
        self.start_cap_pv.put(1)


    def stop_capture(self):
        self.start_cap_pv.put(0)


    # def set_image_data(self, _1d_data):
    #     #self.put('calib_cam:wv_rbv', _1d_data)
    #     if(self.data_pv):
    #         self.data_pv.put(_1d_data)

    # def get_image_data(self):
    #     #self.put('calib_cam:wv_rbv', _1d_data)
    #     if(self.data_pv):
    #         data = self.data_pv.get()
    #         if((data is not None) and (data.size > 0)):
    #             if(len(data.shape) == 1):
    #                 data = data.reshape((self.height, self.width))
    #             else:
    #                 data = None
    #         else:
    #             data = None
    #     return(data)

    def get_single_frame(self, numpts=None):
        self.start_capture()
        time.sleep(0.15)
        self.stop_capture()
        return (self.get_image_data(numpts))


    def get_image_data(self, numpts=None):
        if (numpts):
            data = self.data_pv.get(numpts)
        else:
            # get all
            data = self.data_pv.get()

        if ((data is not None) and (data.size > 0)):

            if (len(data.shape) == 1):
                data = data.reshape((self.height, self.width))
                data = np.flipud(data)
            else:
                data = None

        return (data)


    def on_copy_data(self, data):
        #print('ophyd camera:on_copy_data')
        self.data = np.copy(data)


    # def on_start_cap(self, **kwargs):
    #     self.acquire_frame.emit(kwargs['value'])

    def get_name(self):
        return self.p_prefix + ':start_cap'


    def on_changed(self, data):
        #print('ophyd camera: on_changed')
        pass

    # def on_new_data(self, **kwargs):
    #     data = kwargs['value']
    #     print('on_new_data \n', data[0:10])
    #     self.changed.emit(data)


if __name__ == "__main__":
    import sys
    from PyQt5 import QtWidgets


    def on_new_cam_data(data):
        print('on_new_cam_data \n', data[0:10])


    def on_press(checked):
        global cam
        if (checked):
            cam.start_capture()
        else:
            cam.stop_capture()


    def on_do_reads():
        global cam
        for i in range(10):
            print(cam.get_single_frame(10))
            time.sleep(0.15)
            QtWidgets.QApplication.processEvents()


    app = QtWidgets.QApplication(sys.argv)
    w = QtWidgets.QWidget()
    startstopBtn = QtWidgets.QPushButton("Start")
    startstopBtn.setCheckable(True)
    startstopBtn.clicked.connect(on_press)
    layout = QtWidgets.QVBoxLayout()
    layout.addWidget(startstopBtn)

    doReadBtn = QtWidgets.QPushButton("do reads")
    doReadBtn.setCheckable(True)
    doReadBtn.clicked.connect(on_do_reads)
    layout.addWidget(doReadBtn)

    w.setLayout(layout)

    cam = camera('CCD1610-I10:uhv')
    # cam.stop_capture()
    # cam.changed.connect(on_new_cam_data)

    w.show()
    # cam.set_color_depth(33)
    # print cam.get_color_depth()

    # print data
    app.exec_()
