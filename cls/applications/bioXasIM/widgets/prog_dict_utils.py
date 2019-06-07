'''
Created on Jan 16, 2017

@author: berg
'''
"""
a collection of utilities that are used to create a standard dictionary that is used to communicate with the scan_queue_table widget
 
"""
from cls.utils.dict_utils import dct_get, dct_put

PROG_DCT_ID = 'PROG_DICT'
PROG_DCT_SPID = 'PROG.SPID'
PROG_DCT_PERCENT = 'PROG.PERCENT'
PROG_DCT_STATE = 'PROG.STATE'

def make_progress_dict(sp_id=None, percent=0.0):
    '''
    create a standard dict that is used to send information to the scan_q_view
    '''
    
    dct = {}
    dct_put(dct, PROG_DCT_ID, PROG_DCT_ID)
    dct_put(dct, PROG_DCT_SPID, sp_id)
    dct_put(dct, PROG_DCT_PERCENT, percent)
    dct_put(dct, PROG_DCT_STATE, 0)
    
    return(dct)

        


