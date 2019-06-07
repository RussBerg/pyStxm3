# -*- coding:utf-8 -*-
"""
Created on 2011-03-07

@author: bergr
"""
"""
Created on 2011-03-07

@author: bergr
"""

from PyQt5 import QtGui, QtCore, QtWidgets
import queue

from bcm.devices import BaseDevice
#from cls.ophyd_tests.qt_sigs import BaseDevice
from cls.app_data.defaults import get_style
from cls.utils.log import get_module_logger
import time

_logger = get_module_logger(__name__)

class BaseLabel(QtWidgets.QLabel):

    changed = QtCore.pyqtSignal(object)
    connected = QtCore.pyqtSignal()
    disconnected = QtCore.pyqtSignal()

    def __init__(self, signal, hdrText=None, format='%5.2f', egu='um', warn=None, alarm=None, title_color='black', var_clr='blue', sig_change_kw='value'):
        super(BaseLabel, self).__init__()
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
        self.prefix = signal.get_name()
        self.hdrText = hdrText
        self.signal = signal

        self.signal.changed.connect(self.on_val_change)
        self.changed.connect(self.on_val_change)
        self.disconnected.connect(self.discon_fbk)
        self.connected.connect(self.init_fbk)
        self.signal.on_connect.connect(self.on_connect)

        #self.discon_fbk()

        self.setStyleSheet("background-color:transparent;")


    def on_connect(self,  pvname=None, conn=None, pv=None):
        #print 'ophyd_aiLabelWidget: on_connect has been called'
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

    def on_timer(self):
        call_task_done = False
        while not self.updateQueue.empty():
            resp_dct = self.updateQueue.get()
            val = resp_dct[self.sig_change_kw]
            self.set_text(val)
            call_task_done = True

        if (call_task_done):
            self.updateQueue.task_done()

    def init_fbk(self):
        while (not self.signal.connected):
            time.sleep(0.1)
        self.set_text(self.signal.get())


    def on_val_change(self, val):
        #self.set_text(str(val))
        if(type(val) is dict):
            val = val[self.sig_change_kw]
        self.set_text(val)

    def set_text(self, txt):
        if (self.hdrText is None):
            self.setText(txt)
        else:
            s = '| %s: %s ' % (self.hdrText, txt)
            self.setText(s)
        # print self.labelWidget.width()
        # self.update()



def format_text(title, var, title_color='black', var_color='black', alarm=None):
    bgcolor = 'transparent'
    if(var_color is None):
        print()
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

    s = '<a style="background-color: transparent; ' \
        'color: %s"><b>%s</b>' \
        '\t <a border-width: 50px; ' \
        'style="background-color: %s; ' \
        'color: %s;"><b>%s</b> </a>' % (title_color, title, bgcolor, var_color, var)

    #print('format_text: [%s]' % s)
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

    s = '<a style="background-color: transparent; color: %s">\t <a style="background-color: %s; color: %s;"><b>%s</b> </a>' % (
    title_color, bgcolor, var_color, var)

    #print('format_text_no_title: [%s]' % s)
    return s


class ophyd_strLabel(BaseLabel):

    def __init__(self, signal, hdrText='', title_color=None, var_clr=None):
        super(ophyd_strLabel, self).__init__(pv, hdrText=hdrText, sig_change_kw='char_value')
        self.prefix = signal.get_name()
        self.hdrText = hdrText
        self.title_color = title_color
        self.var_clr = var_clr
        self.signal = signal

    def init_fbk(self):
        self.set_text(self.signal.get())

    def set_text(self, txt):
        s = format_text(self.hdrText, txt, title_color=self.title_color, var_color=self.var_clr)
        self.setText(s)

class ophyd_aiLabelWidget(BaseLabel):

    def __init__(self, signal, hdrText=None, egu='', format='%5.2f', title_color=None, var_clr=None, warn=None, alarm=None,
                 font=None):

        """
        caLabelWidget
        """
        super(ophyd_aiLabelWidget, self).__init__(signal, hdrText=hdrText, sig_change_kw='value', egu=egu, format=format, title_color=title_color, var_clr=var_clr, warn=warn, alarm=alarm)
        if (font is not None):
            # f = QtGui.QFont( "Arial", 18, QtGui.QFont.Bold)
            self.setFont(font)
        self.setContentsMargins(0, 0, 0, 0)

        self.signal = signal
        self.hdrText = hdrText
        self.prefix = signal.get_name()
        self.egu = egu
        self.title_color = title_color
        self.var_clr = var_clr
        self.val = 0.0

        self.warn = warn
        self.alarm = alarm

        if ((warn is not None) and (alarm is not None)):
            self.setToolTip('%s: Warn level set to %5.2f, Alarm level is %5.2f' % (hdrText, warn, alarm))
        # self.setStatusTip('Warn level set to %5.2f, Alarm level is %5.2f' % (warn, alarm))

        self.signal.on_connect.connect(self.init_fbk)

        if (self.signal.is_connected()):
            self.connected.emit()
        else:
            self.disconnected.emit()

    def init_fbk(self):
        self.set_text(self.signal.get())

    def set_text(self, val):
        #check to see if the device that we are subscribed to is returning a dict or just the value
        if(type(val) is dict):
            val = val[self.sig_change_kw]

        #print 'ophyd_aiLabelWidget: set_text: %f' % val
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
                s = format_text(self.hdrText, valStr, title_color=self.title_color, var_color=self.var_clr, alarm=alarm)
            self.setText(s)


class assign_aiLabelWidget(BaseLabel):

    def __init__(self, lbl, signal, hdrText=None, format='%5.2f', egu='um', title_color=None, var_clr=None, warn=None,
                 alarm=None):

        """
        caLabelWidget
        """
        super(assign_aiLabelWidget, self).__init__(signal, hdrText=hdrText, sig_change_kw='value', egu=egu, format=format, title_color=title_color, var_clr=var_clr, warn=warn, alarm=alarm)
        self.setMinimumWidth(150)
        #self.format = format
        self.signal = signal
        self.hdrText = hdrText
        self.prefix = signal.get_name()
        self.sig_change_kw = 'value'

        self.egu = egu
        self.val = 0.0
        self.title_color = title_color
        self.var_clr = var_clr

        self.warn = warn
        self.alarm = alarm
        self.lbl = lbl
        self.lbl.destroyed.connect(self.stop_fbk)
        self.lbl.setToolTip(self.prefix)
        if ((warn is not None) and (alarm is not None)):
            self.setToolTip('%s: Warn level set to %5.2f, Alarm level is %5.2f' % (hdrText, warn, alarm))

        self.fbk_enabled = True
        self.signal.on_connect.connect(self.init_fbk)
        self.signal.changed.connect(self.on_val_change)

        if (self.signal.is_connected()):
            self.connected.emit()
        else:
            self.disconnected.emit()

    def get_text(self):
        return (self.val)

    #def init_fbk(self, sig):
    def init_fbk(self):
        self.set_text(self.signal.get())

    # def on_new_val(self, val):
    #     if(type(val) is dict):
    #         val = val[self.sig_change_kw]
    #     #print('on_new_val=%.3f'% val)
    #     self.set_text(val)

    def set_text(self, val):
        if(type(val) is dict):
            val = val[self.sig_change_kw]

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
                    s = format_text_no_title(valStr, title_color=self.title_color, var_color=self.var_clr, alarm=alarm)
                if(self.lbl):
                    self.lbl.setText(s)


class ophyd_mbbiLabelWidget(BaseLabel):

    def __init__(self, signal, labelWidget=None, hdrText=None, title_color=None, var_clr=None):
        super(ophyd_mbbiLabelWidget, self).__init__(signal, hdrText=hdrText, sig_change_kw='value')
        self.setMinimumWidth(150)
        self.hdrText = hdrText
        self.prefix = signal.get_name()
        self.title_color = title_color
        self.var_clr = var_clr

        self.fields = (
        'ZRST', 'ONST', 'TWST', 'THST', 'FRST', 'FVST', 'SXST', 'SVST', 'EIST', 'NIST', 'TEST', 'ELST', 'TVST', 'TTST',
        'FTST', 'FFST')

        self.enum_strs = []
        self.sigs = []
        for fname in self.fields:
            pvName = '%s.%s' % (self.prefix, fname)
            sig = BaseDevice(pvName)
            self.sigs.append(sig)

        #assuming the last one to be created will be the last one to connect only setup the init_fbk() for the last
        # ones connect callback
        sig.on_connect.connect(self.init_fbk)

        if (self.signal.is_connected()):
            self.connected.emit()
        else:
            self.disconnected.emit()

    def init_fbk(self):
        '''
        populate the enum_strings when the last field of the pv connects
        :return:
        '''
        i = 0
        for fname in self.fields:
            sig = self.sigs[i]
            if (sig.is_connected()):
                self.enum_strs.append(sig.get())
            i += 1

        self.set_text(self.signal.get())

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


class ophyd_biLabelWidget(BaseLabel):
    #a signal specific to binary labels
    binary_change = QtCore.pyqtSignal(object)

    def __init__(self, signal, labelWidget=None, hdrText=None, title_color=None, var_clr=None, options={}):
        super(ophyd_biLabelWidget, self).__init__(signal, hdrText=hdrText, sig_change_kw='value')

        if (labelWidget is None):
            self.lbl = self
        else:
            self.lbl = labelWidget

        self.lbl.setMinimumWidth(150)
        self.hdrText = hdrText
        self.prefix = signal.get_name()
        self.title_color = title_color
        self.var_clr = var_clr
        self.fields = ('ZNAM', 'ONAM')

        if ('state_clrs' in options):
            self.state_colors = options['state_clrs']
        else:
            self.state_colors = [var_clr, var_clr]

        self.enum_strs = []
        self.sigs = []
        for fname in self.fields:
            pvName = '%s.%s' % (self.prefix, fname)
            sig = BaseDevice(pvName)
            self.sigs.append(sig)

        # assuming the last one to be created will be the last one to connect only setup the init_fbk() for the last
        # ones connect callback
        #sig.on_connect.connect(self.init_fbk)
        self.signal.on_connect.connect(self.init_fbk)
        self.signal.changed.connect(self.on_val_change)

        if (self.signal.is_connected()):
            self.connected.emit()
        else:
            self.disconnected.emit()

    def init_fbk(self, do_set_text=True):
        '''
                populate the enum_strings when the last field of the pv connects
                :return:
                '''
        i = 0
        for fname in self.fields:
            sig = self.sigs[i]
            if (sig.is_connected()):
                self.enum_strs.append(sig.get())
            i += 1
        if(do_set_text):
            self.set_text(self.signal.get())

    # def on_new_val(self, val):
    #     if(type(val) is dict):
    #         val = val[self.sig_change_kw]
    #     #print('on_new_val=%.3f'% val)
    #     self.set_text(val)

    def set_text(self, val):
        if(type(val) is dict):
            _logger.error('ophyd_biLabelWidget: set_text: passed in val is a dict not a number???')
            val = val[self.sig_change_kw]

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
            self.init_fbk(do_set_text=False)


class test(QtWidgets.QWidget):
    """Test"""

    # -- Create QApplication
    # --
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        from PyQt5.QtWidgets import QVBoxLayout
        #from cls.applications.pyStxm.bl10ID01 import MAIN_OBJ
        from cls.utils.dict_utils import dct_get, dct_put
        #from bcm.device.device_names import DNM_AX2_INTERFER_VOLTS

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

        # self.shutters = ophyd_strLabel(MAIN_OBJ.device('SRStatus_shutters'),  hdrText='Shutter Status',  title_color=title_color, var_clr=fbk_color)
        #shutters_fbk_sig = BaseDevice('IOC:m913.RBV', val_only=True, val_kw='value')
        #self.shutters = ophyd_strLabel(MAIN_OBJ.device('SRStatus_shutters'),  hdrText='Shutter Status',  title_color=title_color, var_clr=fbk_color)


        ring_fbk_sig = BaseDevice('IOC:m110.RBV', val_only=True, val_kw='value')
        #self.ringlabel = ophyd_aiLabelWidget(MAIN_OBJ.device('StorageRingCurrent'), hdrText='Ring', egu='mA',  title_color=title_color, var_clr=fbk_color, alarm=25, warn=50)
        self.ringlabel = ophyd_aiLabelWidget(ring_fbk_sig, hdrText='Ring', egu='mA',title_color=title_color, var_clr=fbk_color, alarm=25, warn=50)

        # self.evlabel = ophyd_aiLabelWidget(MAIN_OBJ.device('Mono_ev_fbk'), hdrText='Energy', egu='eV', title_color=title_color, var_clr=fbk_color, alarm=25, warn=50)
        #self.tickerlabel = ophyd_aiLabelWidget(MAIN_OBJ.device('ticker'), hdrText='I0', title_color=title_color,
        #                                    var_clr=fbk_color, alarm=2435, warn=505455)
        # self.modelabel = ophyd_mbbiLabelWidget(MAIN_OBJ.device('SYSTEM:mode:fbk').get_name(), hdrText='SR Mode', title_color=title_color, var_clr=fbk_color)

        mode_fbk_sig = BaseDevice('SYSTEM:mode:fbk', rd_only=True, val_only=True, val_kw='value')

        self.modelabel = ophyd_mbbiLabelWidget(mode_fbk_sig, hdrText='SR Mode', title_color=title_color, var_clr=fbk_color)

        # self.modelabel = ophyd_biLabelWidget(MAIN_OBJ.device('SYSTEM:mode:fbk').get_name(), hdrText='SR Mode', title_color=title_color, var_clr=fbk_color)
        #self.evFbkLbl = ophyd_aiLabelWidget(MAIN_OBJ.device('ENERGY_RBV'), hdrText='Energy', egu='eV',
        #                                    title_color=title_color, var_clr=fbk_color, alarm=5, warn=50)
        ev_fbk_sig = BaseDevice('IOC:m914.RBV', val_only=True, val_kw='value')
        self.evFbkLbl = ophyd_aiLabelWidget(ev_fbk_sig, hdrText='Energy', egu='eV',
                                         title_color=title_color, var_clr=fbk_color, alarm=5, warn=50)

        ai_fbk_sig = BaseDevice('IOC:m103:OutputVolt_RBV', val_only=True, val_kw='value')
        self.aiFbkLbl = ophyd_aiLabelWidget(ai_fbk_sig, hdrText='Zx Interferometer', egu='volts',
                         title_color=title_color,
                         var_clr=fbk_color, alarm=0.2, warn=0.29)

        temp_fbk_sig = BaseDevice('CCTL1610-I10:temp:fbk', val_only=True, val_kw='value')
        self.temp_aiFbkLbl = ophyd_aiLabelWidget(temp_fbk_sig, hdrText='Gatan Rod temp', egu='degC',
                                            title_color=title_color,
                                            var_clr=fbk_color, alarm=10.2, warn=30.29)

        #self.shutterFbkLbl = ophyd_biLabelWidget(MAIN_OBJ.device('Shutter'),
        #                                 hdrText='Shutter', title_color='white',
        #                                 options=dict(state_clrs=['black', 'blue']))

        #self.hrtbeatLbl = ophyd_biLabelWidget(MAIN_OBJ.device('mtr_calib_hrtbt'),
        #                                 hdrText='MotorCalibrations', title_color='white',
        #                                 options=dict(state_clrs=['red', 'rgb(85,255,127)']))

        # layout.addWidget(self.shutters)
        # layout.addWidget(self.evlabel)
        layout.addWidget(self.ringlabel)
        #layout.addWidget(self.tickerlabel)
        #layout.addWidget(self.shutterFbkLbl)
        #layout.addWidget(self.pb)
        layout.addWidget(self.evFbkLbl)
        layout.addWidget(self.aiFbkLbl)
        layout.addWidget(self.modelabel)
        layout.addWidget(self.temp_aiFbkLbl)


        #layout.addWidget(self.hrtbeatLbl)

        styleBtn = QtWidgets.QPushButton('Set Style')
        styleBtn.clicked.connect(self.on_set_style)
        layout.addWidget(styleBtn)
        self.setLayout(layout)

        self.qssheet = get_style('dark')
        self.setStyleSheet(self.qssheet)

        self.ringlabel.show()

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
