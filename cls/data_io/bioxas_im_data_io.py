'''
Created on Feb 13, 2017

@author: bergr
'''

from cls.utils.log import get_module_logger
from cls.scanning.dataRecorder import DataIo
from cls.scanning.nexus.nxstxm import get_NXdatas_from_entry, get_wdg_com_from_entry, get_data_from_NXdatas, update_data_with_openclose

_logger = get_module_logger(__name__)

class BioxasDataIo(DataIo):
    """
    A class to encapsulate the interface between the application and the data on disk that is specific
    to STXM data, any specifics should override the DataIo definitions here
    """
    
    def __init__(self, data_dir, file_prefix):
        options={'standard': 'nexus', 'def': 'nxxas'}
        super(BioxasDataIo, self).__init__(data_dir, file_prefix, options=options)
    
    def get_data_from_NXdatas(self, nx_datas, counter_name):
        """ returns the data from counter_name in the nx_)datas dict """
        data = get_data_from_NXdatas(nx_datas, counter_name)
        return(data)
    
    def get_NXdatas_from_entry(self, entry_dct, entry_name):
        """ finds the NXdata groups in the entry and returns a dict that contains the data """
        data = get_NXdatas_from_entry(entry_dct, entry_nm=entry_name)
        return(data)    
    
    def get_wdg_com_from_entry(self, entry_dct, entry_name):
        """ finds the WDG_COM dict in the entry and returns it """
        wdg_com = get_wdg_com_from_entry(entry_dct, entry_nm=entry_name)
        return(wdg_com)    
        
    def update_data_only(self, data_dct):
        """ update data sections only through the configured data exporter
            call:
                importer.update()
        """
        if(data_dct['ID'] != 'ACTIVE_DATA_DICT'):
            _logger.error('Invalid data dictionary type [%s] should be type ACTIVE_DATA_DICT' % data_dct['ID'])
        err = None
        if(self.data_io is not None):
            err = self.data_io.update(data_dct)
        return(err)
    
    def update_data(self, entry, data, counter='counter0', use_tmpfile=False):
        if(self.data_io is not None):
            self.data_io.update_data(entry, data, counter=counter, use_tmpfile=use_tmpfile)
        
    def get_axes_list_from_NXdata(self, nx_datas, counter_name):
        """
        get_axes_list_from_NXdata(): convenience function to pull the axes list in the 
        order that they were written and return it

        :param nx_datas: a dict that is returned from a call to get_NXdatas_from_entry()
        :type nx_datas: dict
        
        :param counter_name: name of counter in the nx_datas dict
        :type counter_name: string

        :returns: a list of axes names
        """
        axes = nx_datas[counter_name]['axes']
        return(axes)
    
    def get_axes_data_by_index_in_NXdata(self, nx_datas, counter_name, index):
        """
        get_axes_data_by_index_in_NXdata(): convenience function to pull the data from 
        an index into the list version of the data found in the NXdatas dict

        :param nx_datas: a dict that is returned from a call to get_NXdatas_from_entry()
        :type nx_datas: dict
        
        :param counter_name: name of counter in the nx_datas dict
        :type counter_name: string
        
        :param index: index into the list of data
        :type index: integer

        :returns: array of data
        """
        data = nx_datas[counter_name]['axes_data'][index]
        return(data)
    
    def get_signal_data_from_NXdata(self, nx_datas, counter_name):
        """
        get_signal_data_from_NXdata(): convenience function to pull the signal data from 
        the data found in the NXdatas dict

        :param nx_datas: a dict that is returned from a call to get_NXdatas_from_entry()
        :type nx_datas: dict
        
        :param counter_name: name of counter in the nx_datas dict
        :type counter_name: string

        :returns: array of data
        """
        data = nx_datas[counter_name]['signal']
        return(data)
    