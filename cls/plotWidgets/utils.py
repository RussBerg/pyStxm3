'''
Created on Nov 30, 2016

@author: berg
'''

#standard names to use
CNTR2PLOT_TYPE_ID = 'type_id'   #to be used to indicate what kind of counter/scan is sending this info
CNTR2PLOT_ROW = 'row'           #a y position
CNTR2PLOT_COL = 'col'           #an x position
CNTR2PLOT_VAL = 'val'           #the point or array of data
CNTR2PLOT_IMG_CNTR = 'img_cntr' #current image counter
CNTR2PLOT_EV_CNTR = 'ev_idx'    #current energy counter
CNTR2PLOT_SP_ID = 'sp_id'       #spatial id this data belongs to
CNTR2PLOT_IS_POINT = 'is_pxp'   #data is from a point by point scan
CNTR2PLOT_IS_LINE = 'is_lxl'    #data is from a line by line scan
CNTR2PLOT_SCAN_TYPE = 'scan_type' # the scan_type from types enum of this scan

def make_counter_to_plotter_com_dct():
    """
    a function to be called by code that wants to pass the current counter information 
    to a plotting widget so that it can be plotted.
    the values of this dct are to be filled out by the caller
    """
    dct = {}
    dct[CNTR2PLOT_TYPE_ID] = None   #to be used to indicate what kind of counter/scan is sending this info
    dct[CNTR2PLOT_ROW] = None       #a y position
    dct[CNTR2PLOT_COL] = None       #an x position
    dct[CNTR2PLOT_VAL] = None       #the point or array of data
    dct[CNTR2PLOT_IMG_CNTR] = None   #current image counter
    dct[CNTR2PLOT_EV_CNTR] = None    #current energy counter
    dct[CNTR2PLOT_SP_ID] = None     #spatial id this data belongs to
    dct[CNTR2PLOT_IS_POINT] = None    #data is from a point by point scan
    dct[CNTR2PLOT_IS_LINE] = None    #data is from a line by line scan
    dct[CNTR2PLOT_SCAN_TYPE] = None    # the scan_type from types enum of this scan
    
    return(dct)
    
    
    
if __name__ == '__main__':
    pass