# -*- coding:utf-8 -*-
"""
Created on 2011-07-26

@author: bergr
"""
import time

import datetime
import os, sys
import simplejson as json
import queue
import threading
from PIL import Image

from PyQt5.QtCore import QObject, pyqtSignal
import numpy as np


from cls.utils.arrays import flip_data_upsdown
from cls.utils.fileUtils import get_file_path_as_parts
from cls.utils.log import get_module_logger
from cls.utils.dict_utils import dct_get #, dct_put
from cls.utils.roi_dict_defs import *
from cls.utils.json_threadsave import ThreadJsonSave, loadJson

from cls.scanning.nexus.nxstxm import create_NXstxm_file, create_entry_in_NXstxm_file, load_single_entry_from_NXstxm_file, \
        update_data_with_openclose, update_point_with_openclose, load_NXstxm_file, update_attrs, update_data
from cls.scanning.nexus.nxstxm import get_NXdatas_from_entry, get_wdg_com_from_entry, get_data_from_NXdatas, update_data_with_openclose, \
                    update_tmp_data

from cls.scanning.nexus.nxxas import create_NXxas_file, create_entry_in_NXxas_file, load_single_entry_from_NXxas_file, \
        update_data_with_openclose, update_point_with_openclose, load_NXxas_file

from cls.data_utils.jsonEncoder import NumpyAwareJSONEncoder

_logger = get_module_logger(__name__)

def convert_to_non_unicode(data):
    """
    NOTE: the nd array detection has to be before the  collections.Iterable
    """
    import collections
    
    if isinstance(data, str):
        return str(data)
    elif isinstance(data, collections.Mapping):
        return dict(list(map(convert_to_non_unicode, iter(data.items()))))
    elif isinstance(data, np.ndarray):
        return data        
    elif isinstance(data, collections.Iterable):
        return type(data)(list(map(convert_to_non_unicode, data)))
        
    else:
        return data    

        
class DataRecError(Exception):
    """Base class for exceptions in this module."""
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return repr(self.msg)

class ThreadNexusSave(threading.Thread):
    """Threaded file Save"""
    def __init__(self, data_dct, name=''):
        threading.Thread.__init__(self, name=name)
        self.data_dct = data_dct
        self.name = 'NXstxm-SV.' + name
        #jpeg thumbnail size
        self.size = (128, 128)
        #print 'ThreadImageSave: [%s] started' % self.name
        
    def run(self):
        if self.data_dct != None:
            #datadir = self.data_dct['CFG']['DATA_DIR']
            #fprefix = self.data_dct['CFG']['DATA_FILE_NAME']
            #stype = self.data_dct['CFG']['SCAN_TYPE']
            
            datadir = dct_get(self.data_dct, ADO_CFG_DATA_DIR)
            fname = dct_get(self.data_dct, ADO_CFG_DATA_FILE_NAME)
            stype = dct_get(self.data_dct, ADO_CFG_SCAN_TYPE)
            fstr = os.path.join(datadir, fname, '.hdf5')
            (save_success, fname) = create_NXstxm_file(fstr, stype, self.data_dct)
            _logger.info('ThreadNexusSave: saved[%s]' % fname)

class ThreadXSPSave(threading.Thread):
    """Threaded file Save"""
    def __init__(self, data_dct, name=''):
        threading.Thread.__init__(self, name=name)
        self.data_dct = data_dct
        self.name = 'Xsp-SV.' + name
        
    def run(self):
        if self.data_dct != None:
            fname = self.data_dct['fname']
            data = self.data_dct['data']
            datadir = self.data_dct['datadir']
            fstr = os.path.join(datadir, fname)
            np.savetxt(fstr, data, delimiter='\t', fmt='%.3f')   # use exponential notation
            _logger.info('ThreadXSPSave: [%s] saved [%s]' % ( self.name, os.path.join(datadir, fname)))
        #_logger.info('ThreadXSPSave:[%s] DONE' % self.name) 
        


        
    

class ThreadImageSave(threading.Thread):
    """Threaded file Save"""
    def __init__(self, data_dct, name=''):
        threading.Thread.__init__(self, name=name)
        self.data_dct = data_dct
        self.name = 'Image-SV.' + name
        #jpeg thumbnail size
        self.size = (128, 128)
        #print 'ThreadImageSave: [%s] started' % self.name
        
    def run(self):
        import scipy
        try:
            if self.data_dct != None:
                fname = dct_get(self.data_dct, ADO_CFG_DATA_THUMB_NAME) + '.jpg'
                data = dct_get(self.data_dct, ADO_DATA_POINTS)
                datadir = dct_get(self.data_dct, ADO_CFG_DATA_DIR)
                #print 'ThreadImageSave'
                if(data is not None):
                    #print 'ThreadImageSave:run: data.shape = ', data.shape

                    # flip upside down: because the data is stored in numpy array orientation where the rows are upside
                    # down from the plotter orientation, flip the data upside down so that when a jpg is created it will be
                    # oriented correctly
                    if(data.ndim is 3):
                        _data = data[0]
                    else:
                        _data = data

                    if (_data.ndim is 2):
                        _data = flip_data_upsdown(_data)

                        im = scipy.misc.toimage(_data, cmin=np.min(_data), cmax=np.max(_data)).resize(self.size, Image.NEAREST)
                        fstr = os.path.join(datadir, fname)
                        im.save(fstr)
        except ValueError:
            print('ERROR')


#@QTasync
def remove_tmp_file(dud=None, kwargs=(None)):
    from cls.utils.file_system_tools import is_locked
    #cleanup tmp file if it exists
    #print args
    #return
    time.sleep(0.25)
    fname = kwargs['args']
        
    iters = 0
    while ((iters < 10) and (is_locked(fname))):
        time.sleep(0.25)
        iters += 1
    
    if(iters >= 10):
        print('error waiting for tmp file to become free')
        return
    
    try:       
        if(os.path.exists(fname)):
            os.remove(fname)

#    except:
#        #print 'couldnt remove tmp file because it was still in use'
#        pass
    except:
        sys.excepthook(*sys.exc_info())
        


class JSONDataIo(QObject):
    """
    A class to encapsulate the interface between the application and the data on disk
    
    attribs :  a dict that contains some information that 
    """
    
    def __init__(self, file_prefix, attribs={'entry': 'entry1', 'counter': 'counter0'}):
        super(JSONDataIo, self).__init__()
        self.file_name = file_prefix + '.json'
        self.file = None
        self.attribs = attribs
    
    def read(self, only_roi_and_data=False):
        #dct = load_single_entry_from_NXstxm_file(self.file_name, only_roi_and_data=only_roi_and_data)
        f=open(self.file_name,"r")
        dct = json.load(f)
        f.close()
        return(dct)
    
    def write(self, dct):
        datadir = dct_get(dct, ADO_CFG_DATA_DIR)
        #fprefix = dct_get(dct, ADO_CFG_DATA_FILE_NAME)
        stype = dct_get(dct, ADO_CFG_SCAN_TYPE)
        #(save_success, fname) = create_NXstxm_file(datadir + '/' + self.file_name, stype, data_dct=dct)
        j=json.dumps(dct, sort_keys=True, indent=4, cls=NumpyAwareJSONEncoder)
        fstr = os.path.join(datadir, self.file_name)
        f=open(fstr,"w")
        f.write(j)
        f.close()
        _logger.info('Saved[%s]' % self.file_name)
        return(True)
    
    def add_entry(self, entry_num, dct):
        datadir = dct_get(dct, ADO_CFG_DATA_DIR)
        #fprefix = dct_get(dct, ADO_CFG_DATA_FILE_NAME)
        stype = dct_get(dct, ADO_CFG_SCAN_TYPE)
        #(save_success, fname) = create_entry_in_NXstxm_file(datadir + '/' + self.file_name, stype, data_dct=dct, entry_num=entry_num)
        j=json.dumps(dct, sort_keys=True, indent=4, cls=NumpyAwareJSONEncoder)
        fstr = os.path.join(datadir, self.file_name)
        f=open(fstr,"w")
        f.write(j)
        f.close()
        _logger.info('Saved[%s]' % self.file_name)
        return(True)
    
    def update_data(self, data, use_tmpfile=False):
        _logger.error('not implemented yet')
        
    def add_data_point(self, entry_num, counter, row, col, val):
        _logger.error('add_data_point: not currently supported')
        
    def update(self, dct):
        pass

class NexusDataIo(QObject):
    """
    A class to encapsulate the interface between the application and the data on disk
    
    attribs :  a dict that contains some information that 
    """
    
    def __init__(self, file_prefix, nx_def='nxstxm', attribs={'entry': 'entry1', 'counter': 'counter0'}):
        super(NexusDataIo, self).__init__()
        data_dir, fprefix, fsuffix = get_file_path_as_parts(file_prefix)
        self.file_name = file_prefix + '.hdf5'
        self.tmp_file_name = file_prefix + '.tmp'
        self.nx_file = None
        self.attribs = attribs

        #rough in support for other nexus definitions
        if(nx_def == 'nxstxm'):
            self.load_nexus_file = load_NXstxm_file
            self.create_nexus_file = create_NXstxm_file
            self.add_nexus_entry = create_entry_in_NXstxm_file
            self.add_nexus_data_point = update_point_with_openclose
            #self.update_nexus_data = update_data_with_openclose
            self.update_nexus_data = update_data
            self.update_nexus_tmp_data = update_tmp_data

            self.update_nexus_attrs = update_attrs
        elif(nx_def == 'nxxas'):
            self.load_nexus_file = load_NXxas_file
            self.create_nexus_file = create_NXxas_file
            self.add_nexus_entry = create_entry_in_NXxas_file
            self.add_nexus_data_point = update_point_with_openclose
            self.update_nexus_data = update_data_with_openclose
        
        else:
            self.load_nexus_file = load_NXstxm_file
            self.create_nexus_file = create_NXstxm_file
            self.add_nexus_entry = create_entry_in_NXstxm_file
            self.add_nexus_data_point = update_point_with_openclose

    def update_file_path(self, fpath):
        data_dir, fprefix, fsuffix = get_file_path_as_parts(fpath)
        self.file_name = fpath
        self.tmp_file_name = fpath + '.tmp'
    
    def read(self, only_roi_and_data=False):
        #entry_dct = load_NXstxm_file(self.file_name)
        entry_dct = self.load_nexus_file(self.file_name)
        return(entry_dct)
    
    def write(self, dct, use_tmpfile=False, allow_tmp_rename=False):
        save_success = False
        datadir = dct_get(dct, ADO_CFG_DATA_DIR)
        stype = dct_get(dct, ADO_CFG_SCAN_TYPE)
        #(save_success, fname) = create_NXstxm_file(datadir + '/' + self.file_name, stype, data_dct=dct)
        if(use_tmpfile):
            #this is an update
            #(save_success, fname) = self.create_nexus_file(self.tmp_file_name, stype, data_dct=dct)
            (save_success, fname) = self.create_nexus_file(self.tmp_file_name, stype, data_dct=dct)
        else:

            if(allow_tmp_rename):
                if(os.path.exists(self.tmp_file_name)):
                    #the tmp file exists so just rename it to *.hdf5
                    os.rename(self.tmp_file_name, self.file_name)
                    _logger.info('Renamed tmp file to [%s]' % self.file_name)
                    save_success = True
            else:
                (save_success, fname) = self.create_nexus_file(self.file_name, stype, data_dct=dct)
                _logger.info('Saved [%s]' % fname)
                self.remove_tmp_file()
            
            #self.remove_tmp_file()
            
        return(save_success)
    
    def remove_tmp_file(self, file=None):
        if(file is not None):
            fname = file
        else:
            fname = self.tmp_file_name

        remove_tmp_file(kwargs={'args':fname} )

    def add_entry(self, entry_num, dct, use_tmpfile=False):
        datadir = dct_get(dct, ADO_CFG_DATA_DIR)
        #fprefix = dct_get(dct, ADO_CFG_DATA_FILE_NAME)
        stype = dct_get(dct, ADO_CFG_SCAN_TYPE)
        #(save_success, fname) = create_entry_in_NXstxm_file(datadir + '/' + self.file_name, stype, data_dct=dct, entry_num=entry_num)

        #hack fix for point spectra scans, point scans on completion write 1 entry per spatial point into a temp file, then when all done that
        #temp file is renamed to <>.hdf5 so that thumbnail viewer doesnt hermorage seeing a partial .hdf5 file
        tmp_file_name = self.file_name + '.tmp'
        if(use_tmpfile):
            #(save_success, fname) = self.add_nexus_entry(self.tmp_file_name, stype, data_dct=dct, entry_num=entry_num)
            (save_success, fname) = self.add_nexus_entry(tmp_file_name, stype, data_dct=dct, entry_num=entry_num)
        else:
            (save_success, fname) = self.add_nexus_entry(self.file_name, stype, data_dct=dct, entry_num=entry_num)
            
#             self.remove_tmp_file()
            _logger.info('Updated [%s]' % fname)
        return(save_success)
    
    def add_data_point(self, entry_num, row, col, val, counter='counter0'):
        point = (row, col)
        #update_point_with_openclose(self.file_name, 'entry%d' % entry_num, point, counter=counter)
        self.add_nexus_data_point(self.file_name, 'entry%d' % entry_num, point, counter=counter)
    
    def update(self, dct):
        pass
    
    def update_data(self, entry, data, counter='counter0', use_tmpfile=False):
        
        if(use_tmpfile):
            #update_data_with_openclose(self.tmp_file_name, entry, data, counter=counter)
            self.update_nexus_data(self.tmp_file_name, entry, data, counter=counter)
        else:
            #update_data_with_openclose(self.file_name, entry, data, counter=counter)
            self.update_nexus_data(self.file_name, entry, data, counter=counter)

    def update_tmp_data(self, idx, tmp_data_dct):
        self.update_nexus_tmp_data(self.file_name + '.nxstxm_tmp', idx, tmp_data_dct)


    def update_attrs(self, attr_dct, use_tmpfile=False):
        if (use_tmpfile):
            # update_data_with_openclose(self.tmp_file_name, entry, data, counter=counter)

            self.update_nexus_attrs(self.tmp_file_name, attr_dct)
        else:
            # update_data_with_openclose(self.file_name, entry, data, counter=counter)
            self.update_nexus_attrs(self.file_name, attr_dct)


class DataIo(QObject):
    """
    A class to encapsulate the interface between the application and the data on disk
    
    supported standards are:
        nexus
                supported nexus definitions are:
                    nxstxm
        
        future to do supports:
            json
            csv
            txt
    """
     
    def __init__(self, data_dir, file_prefix,  options={}):
        super(DataIo, self).__init__()
        self.data_dir = data_dir
        self.file_prefix = file_prefix
        self.data_io = None
        #based on file extension create an instance of the importer and exporter
        if('standard' in list(options.keys())):
            if(options['standard'] is 'nexus'):
                if(options['def'] is 'nxstxm'):
                    #if(file_extension.find('.hdf5') > -1):
                    fstr = os.path.join(self.data_dir, self.file_prefix)
                    self.data_io = NexusDataIo(fstr, nx_def='nxstxm')
                    self.file_extension='.hdf5'
                elif(options['def'] is 'nxxas'):
                    #if(file_extension.find('.hdf5') > -1):
                    fstr = os.path.join(self.data_dir, self.file_prefix)
                    self.data_io = NexusDataIo(fstr, nx_def='nxxas')
                    self.file_extension='.hdf5'
                else:
                    raise DataRecError("DataIo %s not supported NEXUS definition [%s]" % options['def'] )
                
            elif(options['standard'] is 'json'):
                fstr = os.path.join(self.data_dir, self.file_prefix)
                self.data_io = JSONDataIo(fstr)
                self.file_extension='.json'
            elif(options['standard'] is 'csv'):
                print('DataIo: csv type not supported yet')
                self.file_extension='.csv'
            elif(options['standard'] is 'txt'):
                print('DataIo: txt type not supported yet')
                self.file_extension='.txt'
            else:
                raise DataRecError("DataIo %s not supported" % options['standard'] )
        else:
            raise DataRecError("No standard defined")

    def update_file_path(self, fpath):
        self.data_io.update_file_path(fpath)

    def update_data_dir(self, data_dir):
        self.data_dir = data_dir

    def update_file_prefix(self, file_prefix):
        self.file_prefix = file_prefix


    def read(self, only_roi_and_data=False):
        ''' to be implemented by inheriting class
        
        
            #entry_dct = load_NXstxm_file(self.file_name)
            entry_dct = self.load_nexus_file(self.file_name)
            return(entry_dct)
        '''
        pass
    
    def write(self, dct, use_tmpfile=False):
        ''' to be implemented by inheriting class
        
        datadir = dct_get(dct, ADO_CFG_DATA_DIR)
        stype = dct_get(dct, ADO_CFG_SCAN_TYPE)
        #(save_success, fname) = create_NXstxm_file(datadir + '/' + self.file_name, stype, data_dct=dct)
        if(use_tmpfile):
            (save_success, fname) = self.create_nexus_file(self.tmp_file_name, stype, data_dct=dct)
        else:
            (save_success, fname) = self.create_nexus_file(self.file_name, stype, data_dct=dct)
            _logger.info('Saved[%s]' % fname)
            self.remove_tmp_file()
            
        return(save_success)
        '''
        pass
    
    def remove_tmp_file(self):
        err = None
        if(self.data_io is not None):
            err = self.data_io.remove_tmp_file()
        return(err)

    def load(self, fname=None):
        """ read data through the configured data importer, and return a standard dict
            call:
                importer.read()
        """
        dct = None
        if(self.data_io is not None):
            if(self.file_prefix is not None):
                dct = self.data_io.read()
        #dct = convert_to_non_unicode(dct)    
        return(dct)
     
      
    def save(self, data_dct, use_tmpfile=False, allow_tmp_rename=False):
        """ save data through the configured data exporter
            call:
                importer.write()
        """
        if(data_dct['ID'] != 'ACTIVE_DATA_DICT'):
            _logger.error('Invalid data dictionary type [%s] should be type ACTIVE_DATA_DICT' % data_dct['ID'])
        err = None
        if(self.data_io is not None):
            err = self.data_io.write(data_dct, use_tmpfile=use_tmpfile, allow_tmp_rename=allow_tmp_rename)
        return(err)
     
    def add_entry(self, entry_num, data_dct, use_tmpfile=False):
        """ save data through the configured data exporter
            call:
                importer.write()
        """
        if(data_dct['ID'] != 'ACTIVE_DATA_DICT'):
            _logger.error('Invalid data dictionary type [%s] should be type ACTIVE_DATA_DICT' % data_dct['ID'])
        err = None
        if(self.data_io is not None):
            err = self.data_io.add_entry(entry_num, data_dct, use_tmpfile=use_tmpfile)
             
        return(err)
 
    def add_data_point(self, entry_num, row, col, val, counter='counter0'):
        err = None
        if(self.data_io is not None):
            err = self.data_io.add_data_point(entry_num, row, col, val, counter=counter)
             
        return(err)

    def update_attrs(self, attr_dct, use_tmpfile=False):
        err = None
        if (self.data_io is not None):
            err = self.data_io.update_attrs(attr_dct, use_tmpfile=use_tmpfile)

        return (err)

    
class DataRecorder(QObject):
    '''
    description = Attribute("""Name or description of device.""")
    dataObj = Attribute("""Object that contains the data""")
    dirty = Attribute("""True if object contains data not yet saved to disk""")
    '''
    #signals emitted by all DataRecorders
    data_changed = pyqtSignal(object)
    field_changed = pyqtSignal(str, float)
    data_saved = pyqtSignal(object)
    
    def __init__(self, data_dir, fname, name='', data_format='stxm'):
        super(DataRecorder, self).__init__()
        self.name = name
        self.dataType = None
        self.dirty = False
        self.data_dir = data_dir
        self.filename = fname
        self.data_format = data_format
        
        #here put different data format types
        if(data_format == 'stxm'):
            from cls.data_io.stxm_data_io import STXMDataIo
            self.data_io = STXMDataIo(data_dir, fname)
        elif(data_format == 'bioxas'):
            from cls.data_io.bioxas_im_data_io import BioxasDataIo
            self.data_io = BioxasDataIo(data_dir, fname)
        else:
            _logger.error('Unsupported data format [%s]' % data_format)
        
    def set_data_dir(self, directory):
        """ set the dataDir variable to specified directory, directory will be created if doesn't exist """
        self.data_dir = directory
        
    def save_json_obj(self, dct):
        saveThread = ThreadJsonSave(dct, self.name)
        saveThread.setDaemon(True)
        saveThread.start()
    
    def save_image_obj(self, dct):
        saveImageThread = ThreadImageSave(dct, self.name)
        saveImageThread.setDaemon(True)
        saveImageThread.start()
    
    def save_xsp_obj(self, dct):
        saveThread = ThreadXSPSave(dct, self.name)
        saveThread.setDaemon(True)
        saveThread.start()
    
    #def save_nxstxm_obj(self, dct, use_tmpfile=False):
    def save(self, dct, use_tmpfile=False, allow_tmp_rename=False):
#        data_dir = dct_get(dct,ADO_CFG_DATA_DIR)
#        fname = dct_get(dct,ADO_CFG_DATA_FILE_NAME)
        #data_io = STXMDataIo(data_dir, fname, '.hdf5')
        self.data_io.save(dct, use_tmpfile=use_tmpfile, allow_tmp_rename=allow_tmp_rename)
    
    #def save_nxstxm_entry(self, entry_num, dct):
    def save_entry(self, entry_num, dct, use_tmpfile=False):
#        data_dir = dct_get(dct,ADO_CFG_DATA_DIR)
#        fname = dct_get(dct,ADO_CFG_DATA_FILE_NAME)
        #data_io = STXMDataIo(data_dir, fname, '.hdf5')
        self.data_io.add_entry(entry_num, dct, use_tmpfile)
        #self.entry_cntr += 1
    
    def update_data(self, entry, data, counter='counter0', use_tmpfile=False):
        self.data_io.update_data(entry, data, counter=counter, use_tmpfile=use_tmpfile)

    def update_attrs(self, attr_dct, use_tmpfile=False):
        self.data_io.update_attrs(attr_dct, use_tmpfile=use_tmpfile)

    def update_tmp_data(self, idx, tmp_data_dct):
        self.data_io.update_attrs(idx, tmp_data_dct)
        
    def remove_tmp_file(self):
        self.data_io.remove_tmp_file()


    def save_1D_plot_image(self, dct):
        import numpy as np
        import pyplot as plt
        
        # Make a quick sin plot
        pnts = dct_get( dct, ADO_DATA_POINTS)
        #x = dct_get( dct, ADO_DATA_POINTS)
        #y = np.sin(x)
        #plt.plot(x, y)
        #plt.xlabel("Time")
        #plt.ylabel("Amplitude")
        
        # Save it in png and svg formats
        #save("signal", ext="png", close=False, verbose=True)
        #save("signal", ext="svg", close=True, verbose=True)

    
        
    def create_dir(self, directory):
        if os.path.exists(directory):
            pass
        else:
            os.mkdir(directory)
    
    def get_data_dir(self):
        return(self.data_dir)

#     def _loadJson(self, filename):
#         """internel load json data from disk"""
#         #get info from BaseHeader
#         if os.path.exists(filename):
#             js = json.loads(file(filename).read())
#         else:
#             #print "json file doesn't exist: died"
#             raise DataRecError("dataRecorder:_loadJson: json file [%s] doesn't exist: died" % filename)
#            
#        return js

    def load(self, filename):
        """Load data from disk into the data object"""
        self.dataObj = loadJson(filename)
        self.data_changed.emit(self.dataObj)
    

class HdrData(DataRecorder):

    """
    A class to create then configure based on dataType
    API calls used by BaseScan:
        save_image_jpg         - for saving a thumbnail
        save                   - saves the entire file
        save_image_nxdf        - for saving point spec image (currently unused )
        save_entry             - saves an individual entry into a data file
        set_data_dir           - sets the data directory for any file operations
        remove_tmp_file        - deletes a tmp file from the disk
        create_dir             - creates the data directory
        
    """
    
    #def __init__(self, scan_type, num_cols, num_rows, sequence=0, num_energies=1, dataType=None,filename='A102030####'):
    def __init__(self, data_dir, fname, data_format):
        super(HdrData, self).__init__(data_dir, fname, data_format=data_format)
        self.remove_tmp_file()

    def save_image_jpg(self, data_dct):
        self.save_image_obj(data_dct)
    

def go():
    saveQueue = queue.Queue()
    saveThread = ThreadJsonSave(saveQueue)
    saveThread.setDaemon(True)
    saveThread.start()
    
    dct = {}
    dct['fpath'] = r'C:\controls\py2.7\Beamlines\sm\data\guest\Sep12\A110217/test.json'
    dct['datetime'] = datetime.datetime.now()
    saveQueue.put_nowait(dct)
    
def test_HdrData(data_dir, fname):
    hdr = HdrData(data_dir, fname)
    print(hdr)


if __name__ == "__main__":
    from PyQt5 import QtGui, QtWidgets
    
    app = QtWidgets.QApplication(sys.argv)
    
    #go()
    #data_dir = r'C:\tmp'
    fname = r'S:\STXM-data\Cryo-STXM\2017\guest\0126\C170126008\C170126008.tmp'
    
    #test_HdrData(data_dir, fname)
    remove_tmp_file(args=(fname))
    
    
    app.exec_()
    
    
