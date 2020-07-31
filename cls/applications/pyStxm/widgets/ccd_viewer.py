# arr = ccd.image.image

from PyQt5 import QtWidgets, QtCore, QtGui
from bcm.devices import SimGreatEyesCCD
from cls.utils.images import array_to_gray_qpixmap, array_to_image
from cls.app_data.defaults import master_colors, get_style, rgb_as_hex, master_q_colors

PANEL_SIZE = 256

class CCDViewerPanel(QtWidgets.QWidget):
    changed = QtCore.pyqtSignal()

    def __init__(self, ccd, parent=None):
        super(CCDViewerPanel, self).__init__()
        self.ccd = ccd
        self.ss = get_style('dark', skip_lst=['QLabel.qss'])
        self.changed.connect(self.on_changed)
        self.grab_btn = QtWidgets.QPushButton('Grab Image')
        self.imglbl = QtWidgets.QLabel()


        #self.imglbl.setToolTip('%s' % self.ccd.name)
        black_pm = QtGui.QPixmap(PANEL_SIZE, PANEL_SIZE)
        black_pm.fill(QtCore.Qt.black)
        self.imglbl.setPixmap(black_pm)

        self.cntrlbl = QtWidgets.QLabel('Image [0]')
        self.cntrlbl.setAutoFillBackground(True)
        self.cntrlbl.setObjectName('ccd_counter_label_obj')

        self.cntrlbl.setAlignment(QtCore.Qt.AlignHCenter)
        newfont = QtGui.QFont("Times", 12, QtGui.QFont.Bold)
        # self.Voltage_Label[i].setFont(newfont)
        self.cntrlbl.setFont(newfont)

        self.grab_btn.clicked.connect(self.acquire_image)
        self.img_frame = QtWidgets.QWidget()
        self.img_frame.setMinimumSize(PANEL_SIZE,PANEL_SIZE)
        vbox = QtWidgets.QVBoxLayout()
        #vbox.addWidget(self.grab_btn)
        vbox.addWidget(self.imglbl)
        vbox.addWidget(self.cntrlbl)
        self.setLayout(vbox)

        self.bg_sts_lbl_clr = None

        self.ccd.cam.detector_state.subscribe(self.on_new_image, event_type='value')
        self.ccd.file_plugin.capture.subscribe(self.on_capture, event_type='value')

        self.init_panel()
        s = self.get_image_meta()
        self.imglbl.setToolTip(s)
        self.setStyleSheet(self.ss)

    def get_image_meta(self):
        s = ''
        s += self.format_info_text('CCD Name:', self.ccd.get_name(), title_clr='blue', newline=True, start_preformat=False, end_preformat=False)
        s += self.format_info_text('CCD PV Prefix:', self.ccd.prefix, title_clr='blue', newline=True,
                                   start_preformat=False, end_preformat=False)
        s += self.format_info_text('Size X:', '%d' % self.ccd.cam.array_size.array_size_x.get(), title_clr='blue', newline=False, start_preformat=False, end_preformat=False)
        s += self.format_info_text(' Size Y:', '%d' % self.ccd.cam.array_size.array_size_y.get(), title_clr='blue', newline=True,
                                   start_preformat=False, end_preformat=False)
        s += self.format_info_text(' Acquire Time:', '%.3f sec' % self.ccd.cam.acquire_time.get(), title_clr='blue',
                                   newline=True,
                                   start_preformat=False, end_preformat=False)
        s += self.format_info_text(' Image #:', '%d' % self.ccd.cam.array_counter.get(), title_clr='blue',
                                   newline=True,
                                   start_preformat=False, end_preformat=False)
        s += self.format_info_text(' Image Size (bytes):', '%d' % self.ccd.cam.array_size_bytes.get(), title_clr='blue',
                                   newline=True,
                                   start_preformat=False, end_preformat=False)

        return(s)

    def format_info_text(self, title, msg, title_clr='blue', newline=True, start_preformat=False, end_preformat=False):
        '''
        take arguments and create an html string used for tooltips
        :param title: The title will be bolded
        :param msg: The message will be simple black text
        :param title_clr: The Title will use this color
        :param newline: A flag to add a newline at the end of the string or not
        :param start_preformat: If this is the first string we need to start the PREformat tag
        :param end_preformat: If this is the last string we need to stop the PREformat tag
        :return:
        '''
        s = ''
        if (start_preformat):
            s += '<pre>'

        if (newline):
            s += '<font size="3" color="%s"><b>%s</b></font> %s<br>' % (title_clr, title, msg)
        else:
            s += '<font size="3" color="%s"><b>%s</b></font> %s' % (title_clr, title, msg)

        if (end_preformat):
            s += '</pre>'
        return (s)

    def on_new_image(self,  **kwargs):
        '''
        when the detector state changes adjust the background color of the image label
        and if the transition is from 2 -> 0 then call an update of the image by emitting the changed signal
        :param kwargs:
        :return:
        '''
        #print('on_new_image', kwargs)
        # if (kwargs['value'] != 0):
        #     self.bg_sts_lbl_clr = 'rgb(234, 234, 0)'
        #     #self.cntrlbl.setStyleSheet('QLabel{background-color: %s;}' % self.bg_sts_lbl_clr)
        # else:
        #     # self.bg_sts_lbl_clr = 'transparent'
        #     self.bg_sts_lbl_clr = 'rgb(114, 148, 240)'
        #print('on_new_image: ', kwargs)
        if(kwargs['old_value'] != 0 and kwargs['value'] == 0):
            self.changed.emit()

    def init_panel(self):
        '''
        init the ccd panel
        :return:
        '''
        self.ccd.cam.array_counter.put(0)

    def on_capture(self, kwargs):
        if (kwargs['value'] != 0):
            self.bg_sts_lbl_clr = 'rgb(234, 234, 0)'
            #self.cntrlbl.setStyleSheet('QLabel{background-color: %s;}' % self.bg_sts_lbl_clr)
        else:
            # self.bg_sts_lbl_clr = 'transparent'
            self.bg_sts_lbl_clr = 'rgb(114, 148, 240)'

        self.cntrlbl.setStyleSheet('QLabel#ccd_counter_label_obj{color: rgb(0,0,0);background-color: %s; font: bold 12px "MS Shell Dlg 2}' % self.bg_sts_lbl_clr)



    def on_changed(self):
        '''
        when the signal changed fires take the image data and convert it to a QPixmap and display a small version of it
        :return:
        '''
        if(self.bg_sts_lbl_clr is None):
            self.on_capture({'value':0})

        pmap = array_to_gray_qpixmap(self.ccd.image.image)
        pmap = pmap.scaled(QtCore.QSize(QtCore.QSize(PANEL_SIZE, PANEL_SIZE)), QtCore.Qt.IgnoreAspectRatio)
        self.imglbl.setPixmap(pmap)
        cntr = self.ccd.cam.array_counter.get()
        #print('turn data into image # [%d] and display' % cntr)
        self.cntrlbl.setText('Image [%d]' % cntr)
        s = self.get_image_meta()
        #print(s)
        self.imglbl.setToolTip(s)
        del pmap

    def acquire_image(self):
        self.ccd.describe()
        self.ccd.trigger()




if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    ccd = SimGreatEyesCCD('SIMCCD1610-I10-02:', name='SIM_GE_CCD')
    ccd_w = CCDViewerPanel(ccd)
    ccd_w.show()

    sys.exit(app.exec_())
    ccd_w.ccd.unstage()
