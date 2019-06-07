import os, sys

from PyQt5 import QtGui, QtCore, uic, QtWidgets
#from bcm.epics_devices.scan import Scan
from cls.app_data.defaults import rgb_as_hex, master_colors, get_style

uiDir = os.path.dirname(os.path.abspath(__file__))

faze_str_dct = {
    0: 'IDLE', #    Nothing is going on.
    1: 'INIT_SCAN',    #A scan is starting
    2: 'DO:BEFORE_SCAN',    #The next thing to do is trigger the before-scan link.
    3: 'WAIT:BEFORE_SCAN',    #The before-scan link has been triggered. We're waiting for its callback to come in.
    4: 'MOVE_MOTORS',    #The next thing to do is to write to positioners.
    5: 'WAIT:MOTORS',    #We've told motors to move. Now we're waiting for their callbacks to come in.
    6: 'TRIG_DETECTORS',    #The next thing to do is to trigger detectors.
    7: 'WAIT:DETECTORS',    #We've triggered detectors. Now we're waiting for their callbacks to come in.
    8: 'RETRACE_MOVE',    #The next thing to do it send positioners to their post-scan positions.
    9: 'WAIT:RETRACE',    #We've told positioners to go to their post-scan positions. Now we're waiting for their callbacks to come in.
    10: 'DO:AFTER_SCAN',    #The next thing to do is trigger the after-scan link.
    11: 'WAIT:AFTER_SCAN',    #The after-scan link has been triggered. We're waiting for its callback to come in.
    12: 'SCAN_DONE',    #The scan is finished.
    13: 'SCAN_PENDING',    #A scan has been commanded, but has not yet started
    14: ' PREVIEW',    #We're doing a preview of the scan.
    15: 'RECORD SCALAR DATA'#    Record scalar data.
}



idle_states = [0,12]
_fbk_not_moving = master_colors['app_ltblue']
_fbk_moving = master_colors['fbk_moving_ylw']



class SScanStatusWidget(QtWidgets.QWidget):
    """
    classdocs
    """
    update = QtCore.pyqtSignal(object)
    def __init__(self, dev_sscans):
        QtWidgets.QWidget.__init__(self)
        uic.loadUi(os.path.join(uiDir, 'sscan_status.ui'), self)
        self.setGeometry(550, 550, 500, 500)
        if(dev_sscans is None):
            print('SScanStatusWidget: dev_sscans can not be None')
            exit()
        self.dev_sscans = dev_sscans
        self.sscans = []
        self.faze_lbls = [self.fazeLbl_1, self.fazeLbl_2, self.fazeLbl_3, self.fazeLbl_4, self.fazeLbl_5, self.fazeLbl_6, self.fazeLbl_7, self.fazeLbl_8]
        i = 0
        for s_key in sorted(self.dev_sscans.keys()):
            self.connect_sscan(s_key, ss_id=i)
            i += 1

        self.update.connect(self.on_update)

    def on_update(self, tpl_obj):
        lbl, msg, val = tpl_obj
        lbl.setText(msg)
        if(lbl in self.faze_lbls):
            if(val not in idle_states):
                lbl.setStyleSheet("background-color: %s; color: black;" % (_fbk_moving))
            else:
                lbl.setStyleSheet("background-color: %s; color: black;" % (_fbk_not_moving))

    def connect_sscan(self, sscan_nm, ss_id):
        ss = self.dev_sscans[sscan_nm]
        # dev_dct['SSCANS']['%sstxm:scan1' % prfx]
        #ss = Scan('%s' % sscan_nm)
        ss.add_callback('SMSG', self.on_smsg)
        ss.add_callback('CPT', self.on_cpt)
        ss.add_callback('FAZE', self.on_faze)
        ss.add_callback('NPTS', self.on_npts)
        self.sscans.append(ss)

    def on_smsg(self, kwargs):
        #print('on_smsg: [%s]' % kwargs)
        val = kwargs['value']
        s = kwargs['obj'].name
        idx = s.find('.')

        id = int(s[idx - 1]) - 1
        #
        # #print 'ss_id=%d' % id
        if(id is 0):
            lbl = self.sscan_status_label_1
        elif(id is 1):
            lbl = self.sscan_status_label_2
        elif (id is 2):
            lbl = self.sscan_status_label_3
        elif (id is 3):
            lbl = self.sscan_status_label_4
        elif (id is 4):
            lbl = self.sscan_status_label_5
        elif (id is 5):
            lbl = self.sscan_status_label_6
        elif (id is 6):
            lbl = self.sscan_status_label_7
        elif (id is 7):
            lbl = self.sscan_status_label_8
        else:
            print('on_smsg: error: unknown id')
            return
        #lbl.setText(msg)
        self.update.emit((lbl, val, val))

    def on_cpt(self, kwargs):
        #print('on_cpt: [%s]' % msg)
        val = kwargs['value']
        s = kwargs['obj'].name
        idx = s.find('.')

        id = int(s[idx - 1]) - 1
        # msg = kw['value']
        # id = kw['ss_id']
        # #print 'on_cpt: ss_id=%d' % id
        # #print type(msg)
        # #return
        if(id is 0):
            lbl = self.cptLbl_1
        elif(id is 1):
            lbl = self.cptLbl_2
        elif (id is 2):
            lbl = self.cptLbl_3
        elif (id is 3):
            lbl = self.cptLbl_4
        elif (id is 4):
            lbl = self.cptLbl_5
        elif (id is 5):
            lbl = self.cptLbl_6
        elif (id is 6):
            lbl = self.cptLbl_7
        elif (id is 7):
            lbl = self.cptLbl_8
        else:
            print('on_cpt: error: unknown id')
            return
        #lbl.setText(msg)
        self.update.emit((lbl, str(val), val))

    def on_npts(self, kwargs):
        #print('on_npts: [%s]' % msg)
        val = kwargs['value']
        s = kwargs['obj'].name
        idx = s.find('.')

        id = int(s[idx - 1]) - 1
        # msg = kw['value']
        # id = kw['ss_id']
        # #print 'on_cpt: ss_id=%d' % id
        # #print type(msg)
        # #return
        if(id is 0):
            lbl = self.nptsLbl_1
        elif(id is 1):
            lbl = self.nptsLbl_2
        elif (id is 2):
            lbl = self.nptsLbl_3
        elif (id is 3):
            lbl = self.nptsLbl_4
        elif (id is 4):
            lbl = self.nptsLbl_5
        elif (id is 5):
            lbl = self.nptsLbl_6
        elif (id is 6):
            lbl = self.nptsLbl_7
        elif (id is 7):
            lbl = self.nptsLbl_8
        else:
            print('on_npts: error: unknown id')
            return
        #lbl.setText(msg)
        self.update.emit((lbl, str(val), val))

    def on_faze(self, kwargs):
        #print('on_faze: [%s]' % kwargs)
        val = kwargs['value']
        s = kwargs['obj'].name
        idx = s.find('.')

        id = int(s[idx - 1]) - 1
        # val = kw['value']
        # id = kw['ss_id']
        if(val in list(faze_str_dct.keys())):
            msg = faze_str_dct[val]
        else:
            msg = 'UNKNOWN'
        #print 'on_faze: ss_id=%d' % id
        #print type(msg)

        if(id is 0):
            lbl = self.fazeLbl_1
        elif(id is 1):
            lbl = self.fazeLbl_2
        elif (id is 2):
            lbl = self.fazeLbl_3
        elif (id is 3):
            lbl = self.fazeLbl_4
        elif (id is 4):
            lbl = self.fazeLbl_5
        elif (id is 5):
            lbl = self.fazeLbl_6
        elif (id is 6):
            lbl = self.fazeLbl_7
        elif (id is 7):
            lbl = self.fazeLbl_8
        else:
            print('on_faze: error: unknown id')
            return
        #print 'on_faze: fazeLbl_%d = %s' % (id+1, msg)
        self.update.emit((lbl, msg, val))



if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    window = SScanStatusWidget('uhvstxm')
    window.show()
    sys.exit(app.exec_())