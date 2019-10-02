

from cls.plotWidgets.imageWidget import *
from cls.appWidgets.spyder_console import ShellWidget#, ShellDock


class tst_window(QtWidgets.QWidget):


    def __init__(self):
        super(tst_window, self).__init__()
        self.setMinimumWidth(1200)
        # ns = {'main': self, 'pythonShell': self.pythonshell, 'g': globals(), 'MAIN_OBJ': MAIN_OBJ,
        #       'scans_plgins': self.scan_tbox_widgets}
        # # msg = "Try for example: widget.set_text('foobar') or win.close()"
        # # self.pythonshell = ShellWidget(parent=None, namespace=ns, commands=[], multithreaded=True, exitfunc=exit)
        # self.pythonshell = ShellWidget(parent=None, namespace=ns, commands=[], multithreaded=True)
        # self.pyconsole_layout.addWidget(self.pythonshell)
        # # self.apply_stylesheet(self.pythonshell, self.qssheet)


def beam_spot_demo():
    from cls.utils.roi_utils import on_centerxy_changed
    ss = get_style('dark')
    app = guidata.qapplication()
    sys.excepthook = excepthook

    win = tst_window()

    qobj = qobj_OBJ()
    # win = make_default_stand_alone_stxm_imagewidget()
    # win = make_default_stand_alone_stxm_imagewidget(_type='analyze')
    #(-1000, 1000), QPointF(1000, -1000)
    bndg_rect = (-5.0, 10.0, 10.0, -5.0)
    plot = make_default_stand_alone_stxm_imagewidget(bndg_rect=bndg_rect)
    plot.create_beam_spot(0.0, 0.0, size=0.35)
    qobj.new_beam_pos.connect(plot.on_new_direct_beam_pos)
    plot.setStyleSheet(ss)
    #plot.show()
    upd_styleBtn = QtWidgets.QPushButton('Update Style')
    vbox = QtWidgets.QVBoxLayout()
    vbox.addWidget(upd_styleBtn)
    #upd_styleBtn.clicked.connect(win.update_style)
    plot.layout().addLayout(vbox)
    # testing beam spot feedback
    # win.move_beam_spot(5, 10)
    plot.enable_menu_action('Clear Plot', True)

    # ns = {'main': self, 'pythonShell': self.pythonshell, 'g': globals(), 'MAIN_OBJ': MAIN_OBJ,
    #       'scans_plgins': self.scan_tbox_widgets}

    # msg = "Try for example: widget.set_text('foobar') or win.close()"
    # self.pythonshell = ShellWidget(parent=None, namespace=ns, commands=[], multithreaded=True, exitfunc=exit)

    ns = {'win': win, 'g': globals(), 'plot': plot}
    pythonshell = ShellWidget(parent=None, namespace=ns, commands=['from bl_init import *'], multithreaded=False)
    #pythonshell = ShellWidget(parent=None, namespace=ns, commands=[], multithreaded=False)
    vbox2 = QtWidgets.QVBoxLayout()
    vbox2.addWidget(plot)
    vbox2.addWidget(pythonshell)
    win.setLayout(vbox2)
    win.show()

    app.exec_()

if __name__ == "__main__":
    """Test"""
    # -- Create QApplication
    import guidata
    from PyQt5 import QtWidgets
    from cls.app_data.defaults import  get_style
    from bcm.devices import Motor_Qt as apsMotor
    from PyQt5.QtCore import pyqtSignal, QObject
    from cls.utils.profiling import determine_profile_bias_val, profile_it

    #profile_it('go', bias_val=7.40181638985e-07)
    #go()
    beam_spot_demo()



