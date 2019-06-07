import sys
import os
import time
import logging

from PyQt5 import QtWidgets

from cls.appWidgets.splashScreen import get_splash, del_splash
from cls.utils.version import get_version
from cls.utils.log import log_to_qt_and_to_file

def clean_up():
    from cls.applications.pyStxm.bl10ID01 import MAIN_OBJ
    MAIN_OBJ.cleanup()

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
