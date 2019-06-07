# -*- coding:utf-8 -*-
"""
Created on 2011-03-07

@author: bergr
"""
"""
Created on 2011-03-07

@author: bergr
"""
# import epics

from PyQt5 import QtGui, QtCore, QtWidgets
import queue

from bcm.devices import BaseDevice
from cls.app_data.defaults import get_style
import time


class BaseLabel(QtWidgets.QLabel):

    changed = QtCore.pyqtSignal(object)
    connected = QtCore.pyqtSignal()
    disconnected = QtCore.pyqtSignal()

    def __init__(self, pv, hdrText=None, format='%5.2f', egu='um', warn=None, alarm=None, title_color='black', var_clr='blue', sig_change_kw='value'):
        super(BaseLabel, self).__init__()
        # QtWidgets.QLabel.__init__(self)
        self.enum_strs = []
        self.setAutoFillBackground(True)
        self.fbk_enabled = False
        self.format = format
        self.egu = egu
        self.warn = warn
        self.alarm = alarm
        self.title_color = title_color
        self.var_clr = var_clr
        self.sig_change_kw = sig_change_kw
        self.updateQueue = queue.Queue()
        self.prefix = pv.get_name()
        self.hdrText = hdrText
        self.pv = pv
        #val = self.pv.get()
        #self.set_text(self.pv.get())
        # self.pv.changed.connect(self.on_val_change)
        self.pv.add_callback(self._signal_change, with_ctrlvars=False)
        self.pv.pv.connection_callbacks.append(self.on_connect)

        self.changed.connect(self.on_val_change)
        self.disconnected.connect(self.discon_fbk)
        self.connected.connect(self.init_fbk)

        #start disconnected and allow the connections to set everything up
        self.discon_fbk()


    def on_connect(self,  pvname=None, conn=None, pv=None):
        #print 'ca_aiLabelWidget: on_connect has been called'
        if(conn and pv.connected):
            self.connected.emit()
        else:
            self.disconnected.emit()

    def discon_fbk(self):
        alarm = 'WARN'
        s = format_text(self.hdrText, '_DISCON_', title_color=self.title_color, var_color=self.var_clr, alarm=alarm)
        self.setText(s)

    def stop_fbk(self):
        self.fbk_enabled = False

    # def on_timer(self):
    #     call_task_done = False
    #     while not self.updateQueue.empty():
    #         resp_dct = self.updateQueue.get()
    #         val = resp_dct[self.sig_change_kw]
    #         self.set_text(val)
    #         call_task_done = True
    #
    #     if (call_task_done):
    #         self.updateQueue.task_done()

    def init_fbk(self):
        while (not self.pv.connected):
            time.sleep(0.1)
        print('init_fbk: ')
        self.set_text(self.pv.get())


    def on_val_change(self, dct):
        #self.set_text(str(val))
        val = dct[self.sig_change_kw]
        #call the inheriting classes set_text function
        self.set_text(val)

    def _signal_change(self, *args, **kw):
        # update the labels text with the new value
        # print 'baseLabel: sig change:' ,kw
        # self.set_text(kw['char_value'])
        dct = {self.sig_change_kw: kw[self.sig_change_kw]}
        #self.updateQueue.put_nowait(dct)
        self.changed.emit(dct)

    def set_text(self, txt):
        '''
        to be over riddent by inheriting class
        :param txt:
        :return:
        '''
        print('BaseLabel: set_text: %s' % txt)
        if (self.hdrText is None):
            self.setText(txt)
        else:
            s = '| %s: %s ' % (self.hdrText, txt)
            self.setText(s)
        # print self.labelWidget.width()
        # self.update()



def format_text(title, var, title_color='black', var_color='black', alarm=None):
    bgcolor = 'transparent'
    if (alarm is not None):
        if (alarm == 'WARN'):
            # warn background color
            bgcolor = 'yellow'
            # title_color = 'black'
            var_color = 'black'
        elif (alarm == 'ALARM'):
            # alarm background color
            bgcolor = 'red'
            # title_color = 'yellow'
            var_color = 'yellow'

    s = '<a style="background-color: transparent; color: %s"><b>%s</b>\t <a border-width: 50px; style="background-color: %s; color: %s"><b>%s</b> </a>' % (
    title_color, title, bgcolor, var_color, var)
    return s


def format_text_no_title(var, title_color='black', var_color='black', alarm=None):
    bgcolor = 'transparent'
    if (alarm is not None):
        if (alarm == 'WARN'):
            # warn background color
            bgcolor = 'yellow'
            # title_color = 'black'
            var_color = title_color
        elif (alarm == 'ALARM'):
            # alarm background color
            bgcolor = 'red'
            # title_color = 'yellow'
            var_color = title_color

    s = '<a style="background-color: transparent; color: %s">\t <a style="background-color: %s; color: %s"><b>%s</b> </a>' % (
    title_color, bgcolor, var_color, var)
    return s


class ca_strLabel(BaseLabel):

    def __init__(self, pv, hdrText='', title_color=None, var_clr=None):
        super(ca_strLabel, self).__init__(pv, hdrText=hdrText, sig_change_kw='char_value')
        self.prefix = pv.get_name()
        self.hdrText = hdrText
        self.title_color = title_color
        self.var_clr = var_clr
        self.pv = pv

    def init_fbk(self):
        self.set_text(self.pv.get())

    def set_text(self, txt):
        s = format_text(self.hdrText, txt, title_color=self.title_color, var_color=self.var_clr)
        self.setText(s)

class ca_aiLabelWidget(BaseLabel):

    def __init__(self, pv, hdrText=None, egu='', format='%5.2f', title_color=None, var_clr=None, warn=None, alarm=None,
                 font=None):

        """
        caLabelWidget
        """
        super(ca_aiLabelWidget, self).__init__(pv, hdrText=hdrText, sig_change_kw='value', egu=egu, format=format, title_color=title_color, var_clr=var_clr, warn=warn, alarm=alarm)
        if (font is not None):
            # f = QtGui.QFont( "Arial", 18, QtGui.QFont.Bold)
            self.setFont(font)
        self.setContentsMargins(0, 0, 0, 0)

        self.hdrText = hdrText
        self.prefix = pv.get_name()
        self.egu = egu
        self.title_color = title_color
        self.var_clr = var_clr
        self.val = 0.0
        # self.pv = PV(prefix)
        self.warn = warn
        self.alarm = alarm

        if ((warn is not None) and (alarm is not None)):
            self.setToolTip('%s: Warn level set to %5.2f, Alarm level is %5.2f' % (hdrText, warn, alarm))
        # self.setStatusTip('Warn level set to %5.2f, Alarm level is %5.2f' % (warn, alarm))

        if(pv.connected):
            self.init_fbk()

    def init_fbk(self):
        self.set_text(self.pv.get())

    def set_text(self, val):
        # print 'ca_aiLabelWidget: set_text: %f' % val
        if (val is not None):
            self.val = val
            valStr = self.format % val
            valStr += ' %s' % self.egu
            alarm = None

            if (self.warn is not None):
                if (val <= self.warn):
                    alarm = 'WARN'

            if (self.alarm is not None):
                if (val <= self.alarm):
                    alarm = 'ALARM'

            if (self.hdrText is None):
                '| %s %s ' % (valStr, self.egu)
            else:
                # <a href="myref" style="color: red">This is sample text and <b>this is bold sample text</b></a>
                # s = '| %s: %s %s ' % (self.hdrText , valStr, self.egu)
                # s = '| %s: <a style="color: blue"><b>%s</b> </a>' % (self.hdrText , valStr)
                s = format_text(self.hdrText, valStr, title_color=self.title_color, var_color=self.var_clr, alarm=alarm)
            self.setText(s)

    def paintEvent(self, evt):
        super(ca_aiLabelWidget, self).paintEvent(evt)
        opt = QtWidgets.QStyleOption()
        opt.initFrom(self)
        p = QtGui.QPainter(self)
        s = self.style()
        s.drawPrimitive(QtWidgets.QStyle.PE_Widget, opt, p, self)


class assign_aiLabelWidget(BaseLabel):

    def __init__(self, lbl, pv, hdrText=None, format='%5.2f', egu='um', title_color=None, var_clr=None, warn=None,
                 alarm=None):

        """
        caLabelWidget
        """
        super(assign_aiLabelWidget, self).__init__(pv, hdrText=hdrText, sig_change_kw='value', egu=egu, format=format, title_color=title_color, var_clr=var_clr, warn=warn, alarm=alarm)
        self.setMinimumWidth(150)
        #self.format = format
        self.hdrText = hdrText
        self.prefix = pv.get_name()

        self.egu = egu
        self.val = 0.0
        self.title_color = title_color
        self.var_clr = var_clr

        # self.pv = PV(prefix)
        self.warn = warn
        self.alarm = alarm
        self.lbl = lbl
        self.lbl.destroyed.connect(self.stop_fbk)
        self.lbl.setToolTip(self.prefix)
        if ((warn is not None) and (alarm is not None)):
            self.setToolTip('%s: Warn level set to %5.2f, Alarm level is %5.2f' % (hdrText, warn, alarm))
        self.pv = pv
        self.fbk_enabled = True

    def get_text(self):
        return (self.val)

    def init_fbk(self):
        self.set_text(self.pv.get())

    def set_text(self, val):
        if(self.fbk_enabled):
            if (val is not None):
                # print 'set_text: %s' % txt
                self.val = val
                valStr = self.format % val
                valStr += ' %s' % self.egu
                alarm = None

                if (self.warn is not None):
                    if (val <= self.warn):
                        alarm = 'WARN'

                if (self.alarm is not None):
                    if (val <= self.alarm):
                        alarm = 'ALARM'

                if (self.hdrText is None):
                    '| %s %s ' % (valStr, self.egu)
                else:
                    # <a href="myref" style="color: red">This is sample text and <b>this is bold sample text</b></a>
                    # s = '| %s: %s %s ' % (self.hdrText , valStr, self.egu)
                    # s = '| %s: <a style="color: blue"><b>%s</b> </a>' % (self.hdrText , valStr)
                    s = format_text_no_title(valStr, title_color=self.title_color, var_color=self.var_clr, alarm=alarm)
                if(self.lbl):
                    self.lbl.setText(s)

    def paintEvent(self, evt):
        super(assign_aiLabelWidget, self).paintEvent(evt)
        opt = QtWidgets.QStyleOption()
        opt.initFrom(self)
        p = QtGui.QPainter(self)
        s = self.lbl.style()
        s.drawPrimitive(QtWidgets.QStyle.PE_Widget, opt, p, self.lbl)


class ca_mbbiLabelWidget(BaseLabel):

    def __init__(self, pv, labelWidget=None, hdrText=None, title_color=None, var_clr=None):
        super(ca_mbbiLabelWidget, self).__init__(pv, hdrText=hdrText, sig_change_kw='value')
        self.setMinimumWidth(150)
        self.hdrText = hdrText
        self.prefix = pv.get_name()
        self.title_color = title_color
        self.var_clr = var_clr

        self.fields = (
        'ZRST', 'ONST', 'TWST', 'THST', 'FRST', 'FVST', 'SXST', 'SVST', 'EIST', 'NIST', 'TEST', 'ELST', 'TVST', 'TTST',
        'FTST', 'FFST')

        self.enum_strs = []
        for fname in self.fields:
            pvName = '%s.%s' % (self.prefix, fname)
            pv = BaseDevice(pvName)
            time.sleep(0.05)
            try:
                if (pv.connected):
                    self.enum_strs.append(pv.get())

            except:
                pass

    def init_fbk(self):
        self.set_text(self.pv.get())

    def set_text(self, val):
        # print 'set_text: %s' % txt
        try:
            if (len(self.enum_strs) < val):
                pass
            else:
                enum_str = self.enum_strs[val]
                if (self.hdrText is None):
                    self.setText(enum_str)
                else:
                    # s = '| %s: %s ' % (self.hdrText , enum_str)
                    s = format_text(self.hdrText, enum_str, title_color=self.title_color, var_color=self.var_clr)
                    self.setText(s)
        except:
            pass


class ca_biLabelWidget(BaseLabel):
    #a signal specific to binary labels
    binary_change = QtCore.pyqtSignal(object)

    def __init__(self, pv, labelWidget=None, hdrText=None, title_color=None, var_clr=None, options={}):
        # QtWidgets.QLabel.__init__(self)
        super(ca_biLabelWidget, self).__init__(pv, hdrText=hdrText, sig_change_kw='value')

        if (labelWidget is None):
            self.lbl = self
        else:
            self.lbl = labelWidget

        self.lbl.setMinimumWidth(150)
        self.hdrText = hdrText
        self.prefix = pv.get_name()
        self.title_color = title_color
        self.var_clr = var_clr
        self.pv = pv
        self.fields = ('ZNAM', 'ONAM')

        if ('state_clrs' in options):
            self.state_colors = options['state_clrs']
        else:
            self.state_colors = [var_clr, var_clr]

        # self.enum_strs = []
        for fname in self.fields:
            pvName = '%s.%s' % (self.prefix, fname)
            pv = BaseDevice(pvName)
            #time.sleep(0.005)

            try:
                if(pv.connected):
                    self.enum_strs.append(pv.get())
            except:
                raise



    def init_fbk(self):
        self.set_text(self.pv.get())

    def set_text(self, val):
        if (len(self.enum_strs) > val):
            enum_str = self.enum_strs[val]
            self.var_clr = self.state_colors[val]
            dct = {}
            dct['val'] = val
            dct['val_str'] = enum_str
            dct['val_clr'] = self.var_clr
            dct['lbl'] = self
            if (self.hdrText is None):
                self.lbl.setText(enum_str)
            else:
                # s = '| %s: %s ' % (self.hdrText , enum_str)
                s = format_text(self.hdrText, enum_str, title_color=self.title_color, var_color=self.var_clr)
                self.lbl.setText(s)
            self.binary_change.emit(dct)

        else:
            print('ERROR: set_text, len of enum_strs too small')


class test(QtWidgets.QWidget):
    """Test"""

    # -- Create QApplication
    # --
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        from PyQt5.QtWidgets import QVBoxLayout
        from cls.applications.pyStxm.bl10ID01 import MAIN_OBJ
        from cls.utils.dict_utils import dct_get, dct_put
        from bcm.devices.device_names import DNM_AX2_INTERFER_VOLTS
        from bcm.devices.epics.aio import aio


        master_colors = {}
        dct_put(master_colors, "master_background_color", "rgb(115,113,115);")
        dct_put(master_colors, "app_green", "rgb(99, 142, 82);")
        dct_put(master_colors, "app_blue", "rgb(114, 148, 240);")  # 7294F0
        dct_put(master_colors, "app_ltgray", "rgb(165, 165, 165);")
        dct_put(master_colors, "app_medgray", "rgb(115, 113, 115);")  # #737173
        dct_put(master_colors, "app_meddrkgray", "rgb(100, 100, 100);")  #
        dct_put(master_colors, "app_drkgray", "rgb(66, 69, 66);")  # "#424542"

        dct_put(master_colors, "app_yellow", "rgb(236,236,0);")  #

        title_color = master_colors['app_blue']
        fbk_color = 'black'

        layout = QVBoxLayout()
        #self.shutterFbkLbl = QtWidgets.QLabel("HELLO:")
        #self.shutterFbkLbl.setToolTip('This should be the shutter QLabel')
        self.pb = QtWidgets.QPushButton("WHAT?")

        # self.shutters = ca_strLabel(MAIN_OBJ.device('SRStatus_shutters'),  hdrText='Shutter Status',  title_color=title_color, var_clr=fbk_color)
        # self.ringlabel = ca_aiLabelWidget(MAIN_OBJ.device('StorageRingCurrent'), hdrText='Ring', egu='mA',  title_color=title_color, var_clr=fbk_color, alarm=25, warn=50)
        # self.evlabel = ca_aiLabelWidget(MAIN_OBJ.device('Mono_ev_fbk'), hdrText='Energy', egu='eV', title_color=title_color, var_clr=fbk_color, alarm=25, warn=50)
        #self.tickerlabel = ca_aiLabelWidget(MAIN_OBJ.device('ticker'), hdrText='I0', title_color=title_color,
        #                                    var_clr=fbk_color, alarm=2435, warn=505455)
        # self.modelabel = ca_mbbiLabelWidget(MAIN_OBJ.device('SYSTEM:mode:fbk').get_name(), hdrText='SR Mode', title_color=title_color, var_clr=fbk_color)
        # self.modelabel = ca_mbbiLabelWidget(MAIN_OBJ.device('SYSTEM:mode:fbk'), hdrText='SR Mode',
        #                                     title_color=title_color, var_clr=fbk_color)
        # # self.modelabel = ca_biLabelWidget(MAIN_OBJ.device('SYSTEM:mode:fbk').get_name(), hdrText='SR Mode', title_color=title_color, var_clr=fbk_color)
        self.evFbkLbl = ca_aiLabelWidget(MAIN_OBJ.device('ENERGY_RBV'), hdrText='Energy', egu='eV',
                                          title_color=title_color, var_clr=fbk_color, alarm=5, warn=50)


        self.aiFbkLbl = ca_aiLabelWidget(MAIN_OBJ.device(DNM_AX2_INTERFER_VOLTS), hdrText='Ax2 Interferometer', egu='volts',
                         title_color=title_color,
                         var_clr=fbk_color, alarm=0.2, warn=0.29)

        temp_fbk_sig = aio('CCTL1610-I10:temp:fbk')
        self.temp_aiFbkLbl = ca_aiLabelWidget(temp_fbk_sig, hdrText='Gatan Rod temp', egu='degC',
                                                 title_color=title_color,
                                                 var_clr=fbk_color, alarm=10.2, warn=30.29)

        #self.shutterFbkLbl = ca_biLabelWidget(MAIN_OBJ.device('Shutter'),
        #                                 hdrText='Shutter', title_color='white',
        #                                 options=dict(state_clrs=['black', 'blue']))

        #self.hrtbeatLbl = ca_biLabelWidget(MAIN_OBJ.device('mtr_calib_hrtbt'),
        #                                 hdrText='MotorCalibrations', title_color='white',
        #                                 options=dict(state_clrs=['red', 'rgb(85,255,127)']))

        # layout.addWidget(self.shutters)
        # layout.addWidget(self.evlabel)
        # layout.addWidget(self.ringlabel)
        #layout.addWidget(self.tickerlabel)
        #layout.addWidget(self.shutterFbkLbl)
        #layout.addWidget(self.pb)
        layout.addWidget(self.evFbkLbl)
        layout.addWidget(self.aiFbkLbl)
        #layout.addWidget(self.modelabel)
        layout.addWidget(self.temp_aiFbkLbl)

        #layout.addWidget(self.hrtbeatLbl)



        styleBtn = QtWidgets.QPushButton('Set Style')
        styleBtn.clicked.connect(self.on_set_style)
        layout.addWidget(styleBtn)
        self.setLayout(layout)

        self.qssheet = get_style('dark')
        #self.setStyleSheet(self.qssheet)

    def on_set_style(self):
        self.qssheet = get_style('dark')
        self.setStyleSheet(self.qssheet)


if __name__ == "__main__":
    import guidata

    app = guidata.qapplication()

    win = test()

    win.resize(150, 30)
    win.show()
    app.exec_()
