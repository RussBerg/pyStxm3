'''
Created on Jul 7, 2016

@author: bergr
'''
# setup.py
from distutils.core import setup
import py2exe
 
setup(
    console=['nxstxm_validate.py'],
    options = {
        'py2exe': {
            #'packages': ['']
            "dll_excludes": ["libzmq.pyd"],
            "excludes" : ["pywin", "pywin.debugger", "pywin.debugger.dbgcon",
                "pywin.dialogs", "pywin.dialogs.list", 
                "Tkconstants","Tkinter","tcl", "OpenGL","zmq","matplotlib", "wx"]
        }
    }
    
    
)