'''
Created on Dec 2, 2016

@author: control
'''
import os 
import time
from datetime import date

#from cls.applications.pyStxm import abs_path_to_ini_file

from cls.utils.cfgparser import ConfigClass
from cls.appWidgets.user_account.sample_holder_object import sample_holder_obj
from cls.appWidgets.enum import Enum

ACCESS_LVLS = Enum(["GUEST","USER", "STAFF", "ADMIN"])

class user_obj(object):
    def __init__(self, abs_path_to_ini_file):
        super(user_obj, self).__init__()
        appConfig = ConfigClass(abs_path_to_ini_file)
        dataDir = appConfig.get_value('DEFAULT', 'dataDir')

        self._userName = None
        self._password = None
        self._access_lvl = ACCESS_LVLS.GUEST #default
        self._description = ""
        self._date_created = date.fromtimestamp(time.time())
        self._enabled = False
        self._group = None
        self._base_data_dir = dataDir
        self._data_dir = None
        self._sample_ids = {}
        self._cur_sample_id = None
        self._seq_num = 0
    
    def get_seq_num(self):
        return(self._seq_num)
        self._seq_num += 1        
    
    def create_new_sampleholder(self, id='H110212'):
        self._cur_sample_id = id
        shobj = sample_holder_obj(self._userName, id, self._data_dir)
        self._sample_ids[id] = shobj
        
    
    def print_user(self):
        print('username: %s' % self._userName)
        #print 'password: %s' % self.password
        print('access_lvl: %s' % self._access_lvl)
        print('description: %s' % self._description)
        print('date_created: %s' % self._date_created)
        print('enabled: %s' % self._enabled)
        print('group: %s' % self._group)
        print('base_data_dir: %s' % os.path.join(self._base_data_dir, self._userName))
        #print 'data_dir: %s' % self._data_dir

    
    def set_username(self, name):

        self._userName = name
    
    def get_username(self):
        return self._userName

    def set_password(self, password):
        self._password = password
    
    def get_password(self):
        return self._password
        
    def set_access_level(self, new_lvl):
        self._access_lvl = new_lvl
    
    def get_access_level(self):
        return self._access_lvl
    
    def set_description(self, desc):
        self._description = desc
        
    def get_description(self):
        return self._description
        
    def set_enabled(self, en):
        self._enabled = en
    
    def is_enabled(self):
        return self._enabled
    
    def set_group(self, group):
        self._group = group
    
    def get_group(self):
        return self._group
    
    def get_data_dir(self, pos=None):
        return self._data_dir
        # if(pos is None):
        #     return self._data_dir
        # else:
        #     ddir = self._sample_ids[self._cur_sample_id].get_pos_dir(pos)
        #     return(ddir)

    def get_scan_defs_dir(self):
        return os.path.join(self._base_data_dir,self._userName,"scan_defs")

    def create_data_dir(self):
        """
        generate a standard data directory for the user for taoday, 
        result should be :
            <base_data_dir>/<username>/MonSep2013/,<sample holder id>/<pos1 - pos6>
        """
        import os, datetime
        t = datetime.datetime.now()
        
        today = date.today()
        monthStr = today.strftime('%b')
        dayStr = today.strftime('%a')
        year = int(today.strftime('%Y'))
        dayNum = int(today.strftime('%d'))
        
        #self._data_dir = dataDir + "/" + self._userName + "/" + dayStr + monthStr + str(year) 
        #self._data_dir = dataDir + "/" + self._userName + "/" + dayStr + monthStr + str(dayNum) + str(year)
        #self._data_dir = dataDir + "/" + self._userName + "/" + monthStr + str(dayNum)
        #self._data_dir = self._base_data_dir + "/" + self._userName + "/" + '%s' % t.strftime("%m%d")

        _usrDir = os.path.join(self._base_data_dir, self._userName)
        # first see if the users directory is exists, if not make it
        self.ensure_dir(_usrDir)
        # now make actual data directory
        self._data_dir = os.path.join(_usrDir, '%s' % t.strftime("%m%d"))
        self.ensure_dir(self._data_dir)
        #self._data_dir = dataDir + "/" + self._userName + "/" + '%s' % (t.strftime("%Y%m%d"))
        #self.make_basedata_dir()
        #self.create_new_sampleholder()

    def ensure_dir(self, dir):
        if os.path.exists(dir):
            pass
        else:
            os.mkdir(dir)

    def make_basedata_dir(self):
        if os.path.exists(self._data_dir):
            pass
        else:
            os.mkdir(self._data_dir)
            

if __name__ == '__main__':
    pass
