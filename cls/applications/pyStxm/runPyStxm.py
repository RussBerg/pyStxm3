import sys
import os
import time
import logging

from PyQt5 import QtWidgets

from cls.appWidgets.splashScreen import get_splash, del_splash
from cls.utils.version import get_version
from cls.utils.log import log_to_qt_and_to_file

import profile
import pstats


def clean_up():
    from cls.applications.pyStxm.bl10ID01 import MAIN_OBJ
    MAIN_OBJ.cleanup()

def determine_profile_bias_val():
    """
        determine_profile_bias_val(): description

        :param determine_profile_bias_val(: determine_profile_bias_val( description
        :type determine_profile_bias_val(: determine_profile_bias_val( type

        :returns: None
    """
    pr = profile.Profile()
    v = 0
    v_t = 0
    for i in range(5):
        v_t = pr.calibrate(100000)
        v += v_t
        print(v_t)

    bval = v / 5.0
    print('bias val = ', bval)
    profile.Profile.bias = bval
    return bval


def profile_it():
    """
        profile_it(): description

        :param profile_it(: profile_it( description
        :type profile_it(: profile_it( type

        :returns: None
    """

    #bval = determine_profile_bias_val()

    profile.Profile.bias = 1.36987840635e-05

    profile.run('go()', 'testprof.dat')

    p = pstats.Stats('testprof.dat')
    p.sort_stats('cumulative').print_stats(100)

def go():
    #kill fricken carepeater
    #os.system("taskkill /f /im  caRepeater.exe")

    debugger = sys.gettrace()
    from cls.appWidgets.dialogs import excepthook
    sys.excepthook = excepthook

    logdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    if (not os.path.exists(logdir)):
        os.makedirs(logdir)

    logfile = os.path.join(logdir, time.strftime("%Y%m%d-%H%M%S") + '.log')
    log = log_to_qt_and_to_file(logfile, level=logging.DEBUG)

    app = QtWidgets.QApplication(sys.argv)
    ver_dct = get_version()

    #create the splash screen
    splash = get_splash(ver_str=ver_dct['ver_str'])

    from cls.applications.pyStxm.stxmMain import pySTXMWindow
    if(debugger is None):
        pystxm_win = pySTXMWindow(exec_in_debugger=False, log=log)
    else:
        pystxm_win = pySTXMWindow(exec_in_debugger=True, log=log)

    didit = splash.close()
    del_splash()

    app.aboutToQuit.connect(clean_up)
    pystxm_win.show()

    try:
        #starts event loop
        sys.exit(app.exec_())
    except:
        print("runPyStxm; Exiting")

if __name__ == '__main__':
    #profile_it()
    go()
