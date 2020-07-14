'''
Created on Dec 2, 2016

@author: bergr
'''
import simplejson as json
import numpy as np
import datetime

class NumpyAwareJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        #try:
        #print type(obj)
        if isinstance(obj, np.ndarray) and obj.ndim == 1:
            return obj.tolist()
        elif isinstance(obj, np.ndarray) and obj.ndim == 2:
            return obj.tolist()
        elif isinstance(obj, np.ndarray) and obj.ndim == 3:
            return obj.tolist()
        elif isinstance(obj, np.generic):
            return obj.item()
        elif isinstance(obj, set):
            return list(obj)
        elif isinstance(obj, datetime.date):
            str = obj.isoformat()
            #str = unicode(str, errors='replace')
            str = str(str, errors='ignore')
            return str
            
        #elif isinstance(obj, dev_config_sim_v2):
        #    #return(obj.__dict__) 
        #    return("DEVICE_OBJ_NOT_SAVED")
        else:
            return json.JSONEncoder.default(self, obj)
        
        #except TypeError:
        #    _logger.debug('dataRecorder.py: NumpyAwareJSONEncoder: TypeError')
        
