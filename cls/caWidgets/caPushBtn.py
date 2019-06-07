# -*- coding:utf-8 -*-
"""
Created on 2011-03-07

@author: bergr
"""

from PyQt5 import QtGui, QtCore, QtWidgets
import queue
import time


from bcm.devices import BaseDevice
from bcm.devices import Mbbi

# from epics.pv import PV
from epics import PV

from cls.app_data.defaults import get_style

from bcm.devices.device_names import *
from cls.caWidgets.caLabelWidget import format_text_no_title
from cls.app_data.defaults import master_colors
from cls.applications.pyStxm.widgets.button_small_wbtn import Ui_Form as btn_small_pass_a_btn
from cls.utils.enum_utils import Enum

# BTN STATE colors
# In color
zero_color = 'rgb(79, 255, 144);'
# Out color
one_color = 'rgb(79, 255, 144);'
# Moving color
two_color = 'rgb(79, 255, 144);'

def format_btn(title_color='black', bgcolor='transparent'):

    s = 'color: %s; background-color: %s;' % (title_color, bgcolor)
    return s


class caPushBtn(QtWidgets.QPushButton):

    changed = QtCore.pyqtSignal(object)
    connected = QtCore.pyqtSignal()
    disconnected = QtCore.pyqtSignal()

    def __init__(self, pv, off_val, on_val, off_str, on_str, cb=None, sig_change_kw='value', btn=None, fbk_dev=None):
        super(caPushBtn, self).__init__(off_str)

        if(btn is not None):
            #the user has passed in a different button for us to use so clone it
            #skiplist = ['staticMetaObject', '__weakref__', 'parent', 'parentWidget']
            self.btn = btn
            # for attr in dir(btn):
            #     if(attr in skiplist):
            #         pass
            #     else:
            #         a = getattr(self, attr)
            #         setattr(self.btn, attr, a)
            # self.setParent(btn.parent())
        else:
            self.btn = self

        self.prefix = pv.get_name()
        self.pv = pv
        self.update_counter = 0
        self.btn.setAutoFillBackground(True)
        self.btn.setCheckable(True)
        self.btn.setChecked(False)

        self.btn.setToolTip(self.prefix)

        self.fbk_dev = fbk_dev
        self.sig_change_kw = sig_change_kw
        self.on_val = on_val
        self.off_val = off_val
        self.on_str = on_str
        self.off_str = off_str

        id = pv.get_name() + '_btn'
        self.btn.setObjectName(id)

        if (cb is None):
            self.btn.clicked.connect(self.on_btn_dev_push)
        else:
            self.btn.clicked.connect(cb)

        if(self.fbk_dev):
            self.fbk_dev.add_callback(self._signal_change)
        else:
            self.pv.add_callback(self._signal_change, with_ctrlvars=False)

        self.pv.pv.connection_callbacks.append(self.on_connect)

        self.changed.connect(self.on_val_change)
        self.disconnected.connect(self.discon_fbk)
        self.connected.connect(self.init_fbk)
        #dct = {self.sig_change_kw: pv.get()}
        #print 'emiting changed[%d]' % init_val
        #self.changed.emit(dct)
        #self.discon_fbk()
        if(self.pv.pv.connected):
            self.init_fbk()



    def on_connect(self,  pvname=None, conn=None, pv=None):
        #print 'ca_aiLabelWidget: on_connect has been called'
        if(conn):
            self.connected.emit()
        else:
            self.disconnected.emit()

    def discon_fbk(self):
        #alarm = 'WARN'
        self.btn.setEnabled(False)
        #s = format_text(self.hdrText, '_DISCON_', title_color=self.title_color, var_color=self.var_clr, alarm=alarm)
        s = '_DISCON_'
        self.btn.setText(s)

    def init_fbk(self):
        self.btn.setEnabled(True)
        dct = {self.sig_change_kw: self.pv.get()}
        # print 'emiting changed[%d]' % init_val
        self.changed.emit(dct)

    def on_btn_dev_push(self, chkd):
        '''
        what happens when the button is clicked
        :param chkd:
        :return:
        '''
        if (chkd):
            val = self.on_val
        else:
            val = self.off_val

        self.update_counter = 1
        self.pv.put(val)

    def on_connect(self,  pvname=None, conn=None, pv=None):
        '''
        a connection callback
        :param pvname:
        :param conn:
        :param pv:
        :return:
        '''
        if(conn):
            self.connected.emit()
        else:
            self.disconnected.emit()

    def on_val_change(self, dct):
        '''
        this is a Qt slot so go ahead and update the widget
        :param dct:
        :return:
        '''
        val = dct[self.sig_change_kw]
        self.btn.blockSignals(True)
        if(val == self.on_val):
            self.on_btn_dev_push(True)
            txt_str = self.on_str
            chkd = True
        else:
            self.on_btn_dev_push(False)
            txt_str = self.off_str
            chkd = False

        self.btn.setText(txt_str)
        self.btn.setChecked(chkd)
        self.btn.blockSignals(False)

    def _signal_change(self, **kw):
        '''
        this is an epics callback, gets the cur value and emits a Qt signal so the widget can be updated
        :param kw:
        :return:
        '''
        if(self.update_counter > 0):
            self.update_counter -= 1
            dct = {self.sig_change_kw: kw[self.sig_change_kw]}
            #print 'emiting changed[%d]' % kw[self.sig_change_kw]
            self.changed.emit(dct)

    # def paintEvent(self, evt):
    #     super(caPushBtn, self).paintEvent(evt)
    #     opt = QtWidgets.QStyleOption()
    #     opt.initFrom(self)
    #     p = QtGui.QPainter(self)
    #     s = self.btn.style()
    #     s.drawPrimitive(QtWidgets.QStyle.PE_PanelButtonCommand, opt, p, self.btn)

class caPushBtnWithFbk(QtWidgets.QPushButton):

    changed = QtCore.pyqtSignal(object)
    connected = QtCore.pyqtSignal()
    disconnected = QtCore.pyqtSignal()

    def __init__(self, pv, off_val, on_val, off_str, on_str, cb=None, sig_change_kw='value', btn=None, fbk_dev=None, toggle=True):
        super(caPushBtnWithFbk, self).__init__(off_str)

        if(btn is not None):
            #the user has passed in a different button for us to use so clone it
            #skiplist = ['staticMetaObject', '__weakref__', 'parent', 'parentWidget']
            self.btn = btn
        else:
            self.btn = self

        self.prefix = pv.get_name()
        self.pv = pv
        self.update_counter = 0
        self.btn.setAutoFillBackground(True)
        self.toggle = toggle

        self.btn_state = False

        if(toggle):
            self.btn.setCheckable(True)
            self.btn.setChecked(False)
        else:
            self.btn.setCheckable(False)

        self.btn.setToolTip(self.prefix)

        self.fbk_dev = fbk_dev
        self.sig_change_kw = sig_change_kw
        self.on_val = on_val
        self.off_val = off_val
        self.on_str = on_str
        self.off_str = off_str

        id = pv.get_name() + '_btn'
        self.btn.setObjectName(id)

        if (cb is None):
            if(toggle):
                self.btn.clicked.connect(self.on_btn_dev_push)
            else:
                self.btn.clicked.connect(self.on_btn_dev_push_no_toggle)
        else:
            self.btn.clicked.connect(cb)

        if(self.fbk_dev):
            self.fbk_dev.add_callback('setpoint',self._signal_change)
            val = self.fbk_dev.get('VAL')

            if(val == 0):
                val_str = self.fbk_dev.get('ZRST')
            else:
                val_str = self.fbk_dev.get('ONST')
            self.btn.blockSignals(True)
            if(val == self.on_val):
                self.btn.setText(val_str)
                self.make_checked(True)
                self.btn_state = True
            else:
                self.btn.setText(val_str)
                self.make_checked(False)
                self.btn_state = False
            self.btn.blockSignals(False)
        else:
            self.pv.add_callback(self._signal_change)

        self.pv.pv.connection_callbacks.append(self.on_connect)

        self.change_btn_color(val)

        self.changed.connect(self.on_val_change)
        self.disconnected.connect(self.discon_fbk)
        self.connected.connect(self.init_fbk)
        #dct = {self.sig_change_kw: pv.get()}
        #print 'emiting changed[%d]' % init_val
        #self.changed.emit(dct)
        #self.discon_fbk()

        #if(self.pv.pv.connected):
        #    self.init_fbk()


    def make_checked(self, chkd):
        if(self.toggle):
            #skip it
            return

        self.btn.setChecked(chkd)

    def on_connect(self,  pvname=None, conn=None, pv=None):
        #print 'ca_aiLabelWidget: on_connect has been called'
        if(conn):
            self.connected.emit()
        else:
            self.disconnected.emit()

    def discon_fbk(self):
        #alarm = 'WARN'
        self.btn.setEnabled(False)
        #s = format_text(self.hdrText, '_DISCON_', title_color=self.title_color, var_color=self.var_clr, alarm=alarm)
        s = '_DISCON_'
        self.btn.setText(s)

    def init_fbk(self):
        self.btn.setEnabled(True)
        if(self.fbk_dev):
            dct = {self.sig_change_kw: self.fbk_dev.get()}
        else:
            dct = {self.sig_change_kw: self.pv.get()}
        # print 'emiting changed[%d]' % init_val
        self.changed.emit(dct)

    def on_btn_dev_push(self, chkd):
        '''
        what happens when the button is clicked
        :param chkd:
        :return:
        '''
        if (chkd):
            val = self.on_val
        else:
            val = self.off_val

        self.update_counter = 1
        print('putting [%d] ' % val)
        self.pv.put(val)

    def on_btn_dev_push_no_toggle(self):
        if (self.btn_state):
            val = self.off_val
            self.btn_state = False
        else:
            val = self.on_val
            self.btn_state = True

        self.update_counter = 1
        print('on_btn_dev_push_no_toggle: putting [%d] ' % val)
        self.pv.put(val)

    def on_connect(self,  pvname=None, conn=None, pv=None):
        '''
        a connection callback
        :param pvname:
        :param conn:
        :param pv:
        :return:
        '''
        if(conn):
            self.connected.emit()
        else:
            self.disconnected.emit()

    def on_val_change(self, dct):
        '''
        this is a Qt slot so go ahead and update the widget
        :param dct:
        :return:
        '''
        val = dct[self.sig_change_kw]
        #print val
        txt_str = val
        self.btn.setText(txt_str)
        self.btn.blockSignals(True)
        if(val.find(self.on_str) > -1):
            self.make_checked(True)
        else:
            self.make_checked(False)

        self.btn.blockSignals(False)
        self.change_btn_color(dct['value'])


    def change_btn_color(self, val):

        if(val  == 0):
            #in=0
            s = format_btn(title_color='white', bgcolor=master_colors['btn_pressed'])
        elif(val  == 1):
            # out =1
            s = format_btn(title_color='black', bgcolor=master_colors['btn_pressed'])
        else:
            #moving
            s = format_btn(title_color='black', bgcolor=master_colors['fbk_moving_ylw'])
        self.btn.setStyleSheet(s)


    def _signal_change(self, **kw):
        '''
        this is an epics callback, gets the cur value and emits a Qt signal so the widget can be updated
        :param kw:
        :return:
        '''
        print()
        #print kw[self.sig_change_kw]
        dct = {}
        dct[self.sig_change_kw] = kw[self.sig_change_kw]
        dct['value'] = kw['value']
        self.changed.emit(dct)



class test(QtWidgets.QWidget):
    """Test"""

    # -- Create QApplication
    # --
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        from PyQt5.QtWidgets import QVBoxLayout, QPushButton

        widg = QtWidgets.QWidget()
        dev_ui = btn_small_pass_a_btn()
        dev = BaseDevice('BL1610-I10:ENERGY:uhv:osay_track_enabled')

        pBtn = caPushBtn(dev, off_val=0, on_val=1, off_str='Disabled', on_str='Enabled')
        dev_ui.setupUi(widg, pBtn)


        dev_ui.mtrNameFld.setText('TEST')
        id = dev.get_name() + '_btn'
        dev_ui.pushBtn.setObjectName(id)

        fl_mode_dev = BaseDevice('BL1610-I10:ENERGY:uhv:zp:scanselflag')
        # pv, init_val, off_val, on_val, off_str, on_str, cb=None):
        self.mode_pb = caPushBtn(fl_mode_dev, off_val=1, on_val=0, off_str='Sample Focused',
                            on_str='OSA Focused')

        discon_dev = BaseDevice('BL1610-I10:ENERGY:uhv:zp:scansel')
        # pv, init_val, off_val, on_val, off_str, on_str, cb=None):
        self.discon_pb = caPushBtn(discon_dev, off_val=0, on_val=1, off_str='Some PV Off',
                                 on_str='Some PV On')

        zp_inout_dev = BaseDevice('BL1610-I10:uhv:zp_inout')
        zp_inoutfbk_dev = Mbbi('BL1610-I10:uhv:zp_inout:fbk')
        # pv, init_val, off_val, on_val, off_str, on_str, cb=None):
        self.zp_pb = caPushBtnWithFbk(zp_inout_dev, sig_change_kw='char_value', off_val=0, on_val=1, off_str='ZP_IN',
                                   on_str='ZP_OUT', fbk_dev=zp_inoutfbk_dev, toggle=False)


        layout = QVBoxLayout()



        #layout.addWidget(self.pb)
        layout.addWidget(widg)
        layout.addWidget(self.mode_pb)
        layout.addWidget(self.discon_pb)
        layout.addWidget(self.zp_pb)

        self.setLayout(layout)



if __name__ == "__main__":

    app = QtWidgets.QApplication([])

    win = test()
    win.resize(150, 150)
    win.show()
    app.exec_()

