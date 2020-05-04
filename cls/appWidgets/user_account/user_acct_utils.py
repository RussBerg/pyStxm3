'''
Created on 2013-07-29

@author: bergr
'''
import os
import bz2

#today = datetime.date.today()
#yesterday = datetime.date.today() - datetime.timedelta(1)
#dayStr = yesterday.strftime('%a').lower()
#dayNum = int(yesterday.strftime('%d'))
#monthStr = yesterday.strftime('%b').lower()
#monthNum = yesterday.strftime('%m')
#year = int(yesterday.strftime('%Y'))
#ampm = yesterday.strftime('%p').lower(
        
from cls.utils.json_threadsave import dict_to_json_string, json_string_to_dct, saveJson, loadJson
from cls.utils.cfgparser import ConfigClass
from cls.utils.log import get_module_logger, log_to_console, log_to_qt

#from cls.applications.pyStxm import abs_path_to_ini_file

from cls.appWidgets.user_account.user_object import user_obj, ACCESS_LVLS

_logger = get_module_logger(__name__)

#fix this later so that it uses a configurable path
#appConfig = ConfigClass(abs_path_to_ini_file)
#uiDir = appConfig.get_value('MAIN', 'uiDir')
#dataDir = appConfig.get_value('MAIN', 'dataDir')
#mtrcfg = appConfig.get_value('MAIN', 'mtrcfg')
#SLASH = appConfig.get_value('MAIN', 'dirslash')


class user_accnt_mgr(object):
    """ this class handles all file IO and password encryption, as well as validates user names and passwords, 
    the user account information is stored in a pickeled file (users.p) that is specified by the caller which is
    usually made from teh __init__ file of the calling application so that it is setup at startup.
    
    :param users_file: the absolute path to the picked user accounts file, if it doesnt exist it will be created
    :type users_file: string
    
    """
    def __init__(self, desired_dir=os.getcwd()):
        super(user_accnt_mgr, self).__init__()
        
        self.users = {}
        self.user_accnt_file = os.path.join(desired_dir, 'users.json')
        self.app_ini_file = os.path.join(desired_dir, 'app.ini')
        self.load_users()
    
    def create_default_user(self):
        self.add_user("guest", "welcome1")    
    
    def add_user(self, username, password, group="visitor", access_lvl=ACCESS_LVLS.GUEST):
        usr_obj = user_obj(self.app_ini_file)
        usr_obj.set_username(username)
        upass_str = username+'#'+password
        usr_obj.set_password(bz2.compress(upass_str.encode('utf-8')))
        usr_obj.set_enabled(True)
        usr_obj.set_group(group)
        if(access_lvl in ACCESS_LVLS):
            usr_obj.set_access_level(access_lvl)
        usr_obj.data_dir = None

        self.users[username] = usr_obj
# currently have this commented out because in the switch from the glitchy pickle to json I ran into the
# NOT SERIALIABLE problem associated wiht date so commenting this out for now
#        self.save_users()
        return(usr_obj)

    def get_users(self):
        return self.users

    def get_user(self, username):
        if(username in list(self.users.keys())):
            return(self.users[username])
        else:
            return(None)

    def reset_password(self, username):
        if(username in list(self.users.keys())):
            #self.users[username].password = bz2.compress(username+'#'+"welcome1")
            upass_str = username + '#' + "welcome1"
            self.users[username].password =  bz2.compress(upass_str.encode('utf-8'))

    def _dump_users(self):
        for nm in list(self.users.keys()):
            self.users[nm].print_user()


    def delete_user(self, username):
        if(username in list(self.users.keys())):
            del(self.users[username])

    def validate_usernmpassword(self, username, password):
        ''' validate a username and password against what is stored in the pickle file
        return tuple which is (the success/failure, the user object)
        '''
        stsmsg = ''
        if(username not in list(self.users.keys())):
            _logger.error("User: [%s] does not exist" % username)
            stsmsg = "User: [%s] does not exist" % username
            return (False, None, stsmsg)

        upass_str = username + '#' + password
        bz2_usrpass = bz2.compress(upass_str.encode('utf-8'))
        #now check against bz2 version from pickle
        pkl_usrpass = self.users[username].get_password()
        
        if(bz2_usrpass == pkl_usrpass):
            _logger.info("User: [%s] logged in" % username)
            result = True
            stsmsg = "Success"
        else:
            _logger.error("Password: is incorrect")
            result = False
            stsmsg = "Password: is incorrect"
        if(result):
            return (result, self.users[username], stsmsg)
        else:
            return (False, None,stsmsg)
    
    def save_users(self):
        #self._pickel_users()
        self.write_file() 
        #leave here for debugginh 
        self._dump_users()
    
    def load_users(self):
        self.load_file()
        #self._depickle_users()
        #leave here for debugginh 
        self._dump_users()
    
    def write_file(self):
        js = dict_to_json_string(self.users)
        saveJson(self.user_accnt_file, js)
            
    def load_file(self):
        if(os.path.exists(self.user_accnt_file)):
            js = loadJson(self.user_accnt_file)
            if(js):
                self.users = json_string_to_dct(js)
            else:
                _logger.error('unable to load user account file [%s]' % self.user_accnt_file)
        else:
            self.create_default_user()
    
#     def _pickel_users(self):
#         import pickle
#         f = open( self.user_accnt_file, "wb" )
#         pickle.dump( self.users, f )
#         f.close()
#     
#     def _depickle_users(self):
#         import pickle
#         if(os.path.exists(self.user_accnt_file)):
#             f = open( self.user_accnt_file, "rb" )
#             self.users = pickle.load( f )
#             f.close()
#         else:
#             self.create_default_user()


__all__ = ['user_accnt_mgr']
