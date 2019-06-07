'''
Created on May 4, 2016

@author: bergr
'''
import os, sys
path_sep = ';'
epicsPath = r'C:\controls\epics\R3.14.12.4\base\bin\win32-x86;C:\controls\epics\R3.14.12.4\lib\win32-x86;C:\controls\py2.7\cls;C:\controls\py2.7\blctl'
mypypath = r'C:\\controls\\py2.7\\cls;C:\\controls\\py2.7\\blctl;C:\\eclipse\\plugins\\org.python.pydev_3.4.1.201403181715\\pysrc\\pydev_sitecustomize;C:\\controls\\py2.7\\blctl;C:\\controls\\py2.7\\Beamlines;C:\\controls\\py2.7\\cls;C:\\Python27\\DLLs;C:\\Python27\\lib;C:\\Python27\\lib\\lib-tk;C:\\Python27;C:\\Python27\\lib\\site-packages;C:\\Python27\\lib\\site-packages\\PIL;C:\\Python27\\lib\\site-packages\\win32;C:\\Python27\\lib\\site-packages\\win32\\lib;C:\\Python27\\lib\\site-packages\\Pythonwin;C:\\Python27\\lib\\site-packages\\setuptools-0.6c11-py2.7.egg-info;c:\\nix-mapsaw-ed43276;C:\\Python27\\lib\\site-packages\\yapsy-1.10.423-py2.7.egg;C:\\Python27\\lib\\site-packages\\nexpy-0.5.4-py2.7-win32.egg;C:\\Python27\\lib\\site-packages\\matplotlib-1.4.3-py2.7-win32.egg;C:\\Python27\\lib\\site-packages\\mayavi-4.3.0-py2.7-win32.egg;C:\\Python27\\lib\\site-packages\\traitsui-4.3.0-py2.7.egg;C:\\Python27\\lib\\site-packages\\traits-4.3.0-py2.7-win32.egg;C:\\Python27\\lib\\site-packages\\apptools-4.2.0-py2.7.egg;C:\\Python27\\lib\\site-packages\\pyface-4.3.0-py2.7.egg;C:\\Python27\\lib\\site-packages\\configobj-4.7.2-py2.7.egg;C:\\Python27\\lib\\site-packages\\pydaqmx-1.2.5.2-py2.7.egg;C:\\Python27\\lib\\site-packages\\sqlalchemy-0.7.11dev-py2.7-win32.egg;C:\\Python27\\lib\\site-packages\\pyepics-3.2.4-py2.7.egg;C:\\Python27\\lib\\site-packages\\pyside-1.2.2-py2.7-win32.egg;C:\\Python27\\lib\\site-packages\\pyparsing-2.0.3-py2.7-win32.egg;C:\\Python27\\lib\\site-packages\\pytz-2014.10-py2.7.egg;C:\\Python27\\lib\\site-packages\\python_dateutil-2.4.0-py2.7.egg;C:\\Python27\\lib\\site-packages\\six-1.9.0-py2.7.egg;C:\\Python27\\lib\\site-packages\\xmlutils-1.1-py2.7.egg;C:\\Program Files\\NeXus Data Format\\bin;C:\\Python27\\lib\\site-packages\\ipython-3.0.0-py2.7.egg'
    
path  = [os.environ['PATH']]
path.extend(epicsPath.split(';'))
os.environ['PATH'] = path_sep.join(path)
    
pypath = os.environ['PYTHONPATH'] + ';' + mypypath
os.environ['PYTHONPATH'] = pypath
