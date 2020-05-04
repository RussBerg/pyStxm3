# -*- coding:utf-8 -*-
########################################################
# Copyright © 2011 Canadian Light Source Inc. (CLSI) All rights reserved.
#
# Permission to use, copy, modify, and distribute this software and its
# documentation for any purpose and without fee or royalty is hereby granted,
# provided that the full text of this NOTICE appears on ALL copies of the
# software and documentation or portions thereof, including modifications,
# that you make.
#
# THIS SOFTWARE IS PROVIDED BY CLSI "AS IS" AND CLSI EXPRESSLY DISCLAIMS
# LIABILITY FOR ANY AND ALL DAMAGES AND LOSSES (WHETHER DIRECT, INCIDENTAL,
#  CONSEQUENTIAL OR OTHERWISE) ARISING FROM OR IN ANY WAY RELATED TO THE
# USE OF SOFTWARE, INCLUDING, WITHOUT LIMITATION, DAMAGES TO ANY COMPUTER,
# SOFTWARE OR DATA ARISING OR RESULTING FROM USE OF THIS SOFTWARE.
# BY WAY OF EXAMPLE, BUT NOT LIMITATION, CLSI MAKE NO REPRESENTATIONS OR
# WARRANTIES OF MERCHANTABILITY OR FITNESS FOR ANY PARTICULAR PURPOSE OR
# THAT THE USE OF THE SOFTWARE  OR DOCUMENTATION WILL NOT INFRINGE ANY THIRD
# PARTY PATENTS, COPYRIGHTS, TRADEMARKS OR OTHER RIGHTS. CLSI WILL BEAR NO
# LIABILITY FOR ANY USE OF THIS SOFTWARE OR DOCUMENTATION.
#
# Title to copyright in this software and any associated documentation will
# at all times remain with CLSI. The reproduction of CLSI and its trademarks
# is strictly prohibited, except with the prior written consent of CLSI.
#########################################################

"""
This module provides an interface to load and retrieve elements of a config file
based on the ConfigParser python mudule
"""
import sys
import configparser, os

from cls.utils.log import get_module_logger

__author__ = "bergr"
__copyright__ = "Copyright 2011, The Canadian Lightsource"
__credits__ = ["bergr", "?"]
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "bergr"
__email__ = "russ.berg@lightsource.ca"
__status__ = "Development"

# put 3rd party imports here
_logger = get_module_logger(__name__)


class ConfigClass(object):
    '''
	classdocs
	'''

    def __init__(self, filename, exit_on_fail=True):
        '''
		Constructor
		'''
        super(ConfigClass, self).__init__()
        self.config = configparser.ConfigParser()
        self.filename = filename
        self.exit_on_fail = exit_on_fail
        self.cfgDict = {}
        self.update()

    # 		if(os.path.exists(filename)):
    # 			self.config.read(filename)
    # 		else:
    # 			if(exit_on_fail):
    # 				print 'ConfigClass: Error: cannot load %s' % filename
    # 				sys.exit()
    # 			else:
    # 				f = open(filename, 'w+')
    # 				f.write('')
    # 				f.close()
    #

    # 		self.cfgDict ['MAIN'] = self.config.defaults()
    # 		self.sections = self.config.sections()
    # for section in self.sections:
    #	if(section.find('MAIN') == -1):
    #		for opt in self.config.options(section):
    #			self.cfgDict[section][opt] = self.get_value(section, opt)

    def update(self):
        if (os.path.exists(self.filename)):
            self.config.read(self.filename)
        else:
            if (self.exit_on_fail):
                print('ConfigClass: Error: cannot load %s' % self.filename)
                sys.exit()
            else:
                f = open(self.filename, 'w+')
                f.write('')
                f.close()
        self.cfgDict['MAIN'] = self.config.defaults()
        self.sections = self.config.sections()

    def get_value(self, section, option):
        # use the configParser that will perform substitutions 0, 1 is for raw
        if ((section == 'MAIN') or self.config.has_section(section)):

            if (self.config.has_option(section, option)):

                val = self.config.get(section, option)
                val = val.replace(' ', '').split(',')[0]
            else:
                _logger.error('option [%s] does not exist in section [%s]' % (option, section))
                val = None
        else:
            _logger.error('section [%s] does not exist' % section)
            val = None
        # print self.config.get(section, item, 0)
        return (val)

    def get_all(self):
        '''
        return the configuration as a dict
        :return:
        '''
        dct = {}
        #print('config has:')
        sections = self.config.sections()
        for sec in sections:
            #print('\t [%s] = ' % (sec))
            dct[sec] = {}
            for opt in self.config.options(sec):
                v = self.config.get(sec, opt)
                #print('\t\t [%s] = %s' % (opt,v))
                dct[sec][opt] = v
        return(dct)

    def set_value(self, section, option, value):
        # use the configParser that will perform substitutions 0, 1 is for raw
        self.config.set(section, option, value)

    # print self.config.set(section, item, value)

    def get_bool_value(self, section, option):
        if ((section == 'MAIN') or self.config.has_section(section)):
            if (self.config.has_option(section, option)):
                val = self.config.getboolean(section, option)
            else:
                _logger.error('option [%s] does not exist in section [%s]' % (option, section))
                val = None
        else:
            _logger.error('section [%s] does not exist' % section)
            val = None
        return (val)

    def _tst_gen_cfg_file(self):
        config = configparser.RawConfigParser()

        # When adding sections or items, add them in the reverse order of
        # how you want them to be displayed in the actual file.
        # In addition, please note that using RawConfigParser's and the raw
        # mode of ConfigParser's respective set functions, you can assign
        # non-string values to keys internally, but will receive an error
        # when attempting to write to a file or when you get it in non-raw
        # mode. SafeConfigParser does not allow such assignments to take place.
        config.add_section('Section1')
        config.set('Section1', 'int', '15')
        config.set('Section1', 'bool', 'true')
        config.set('Section1', 'float', '3.1415')
        config.set('Section1', 'baz', 'fun')
        config.set('Section1', 'bar', 'Python')
        config.set('Section1', 'foo', '%(bar)s is %(baz)s!')

        # Writing our configuration file to 'example.cfg'
        with open('example.cfg', 'wb') as configfile:
            config.write(configfile)

    def _read_cfg_file(self, fname):
        config = configparser.ConfigParser()
        config.read(fname)

        # Set the third, optional argument of get to 1 if you wish to use raw mode.
        print(config.get('MAIN', 'top', 0))
        print(config.get('MAIN', 'appDir', 0))
        print(config.get('MAIN', 'dataDir', 0))
        print(config.get('MAIN', 'uiDir', 0))
        print(config.get('MAIN', 'cfgDir', 0))
        print(config.get('MAIN', 'autoSaveData', 0))



if __name__ == "__main__":

    cfgObj = ConfigClass(r'C:\controls\github\pyStxm3\cls\applications\pyStxm\app.ini')
    #print(cfgObj.get_value('MAIN', 'uiDir'))

    cfg = cfgObj.get_all()
    print(cfg)

