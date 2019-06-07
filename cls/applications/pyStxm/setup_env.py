'''
Created on Oct 3, 2016

@author: bergr
'''
import os


path_sep = ';'
epicsPath = r'C:\controls\epics\R3.14.12.4\base\bin\win32-x86;C:\controls\epics\R3.14.12.4\lib\win32-x86;'
mypypath = r'.\\cls;.\\blctl;C:\\eclipse\\plugins\\org.python.pydev_3.4.1.201403181715\\pysrc\\pydev_sitecustomize;.\\blctl;.\\Beamlines;.\\cls;'

path  = [os.environ['PATH']]
path.extend(epicsPath.split(';'))
os.environ['PATH'] = path_sep.join(path)

#pypath = os.environ['PYTHONPATH'] + ';' + mypypath
#pypath = os.environ['PYTHONPATH'] + ';' + mypypath
#import sys
#sys.path.append(mypypath)
#os.environ['PYTHONPATH'] = pypath
#print os.environ['PYTHONPATH']
os.environ['EPICS_CA_MAX_ARRAY_BYTES'] = "10000000"

if __name__ == '__main__':
    pass