
'''
Created on Jan 11, 2019

@author: bergr
'''
ID = 'ID'
ID_VAL = 'ID_VAL'
CMND = 'CMND'
NAME = 'NAME'
START = 'START'
STOP = 'STOP'
STEP = 'STEP'
RANGE = 'RANGE'
CENTER = 'CENTER'
NPOINTS = 'NPOINTS'
ROI_STEP = 'STEP'
DWELL = 'DWELL'
SETPOINTS = 'SETPOINTS'
EV_ROIS = 'EV_ROIS'
ENERGY = 'ENERGY'
COARSE = 'COARSE'
FINE = 'FINE'
DEVICES = 'DEVICES'

RBV = 'RBV'

SCAN_RES = 'SCAN_RES'
IS_POINT = 'IS_POINT'
OFFSET = 'OFFSET'
UNITS = 'UNITS'
ENABLED = 'ENABLED'
POSITIONER = 'POSITIONER'
SRC = 'SRC'
TOP_LEVEL = 'TOP_LEVEL'
DATA_LEVEL = 'DATA_LEVEL'

SPATIAL_DB_DICT = 'SPATIAL_DB_DICT'
BASE_ROI = 'BASE_ROI'
BASE_START_STOP_ROI = 'BASE_START_STOP_ROI'
EV_ROI = 'EV_ROI'
EPU_POL = 'EPU_POL'

POL_POSITIONER = 'POL_POSITIONER'
OFF_POSITIONER = 'OFF_POSITIONER'

EV = 'EV'
POL = 'POL'
OFF = 'OFF'
ANGLE = 'ANGLE'

EPU_POL = 'EPU_POL'

SCAN_IDX = 'SCAN_IDX'
POL_ID = 'POL_ID'
POL_ROIS = 'POL_ROIS'
XMCD_EN = 'XMCD_EN'
EV_POL_ORDER = 'EV_POL_ORDER'

EPU_POL_PNTS = 'EPU_POL_PNTS'
EPU_OFF_PNTS = 'EPU_OFF_PNTS'
EPU_ANG_PNTS = 'EPU_ANG_PNTS'

DATA_STATUS_NOT_FINISHED = 'NOT_FINISHED'
DATA_STATUS_FINISHED = 'FINISHED'

_ENABLED = lambda x: str(x + '.ENABLED')
_START = lambda x: str(x + '.START')
_STOP = lambda x: str(x + '.STOP')
_RANGE = lambda x: str(x + '.RANGE')
_STEP = lambda x: str(x + '.STEP')
_CENTER = lambda x: str(x + '.CENTER')
_NPOINTS = lambda x: str(x + '.NPOINTS')
_SETPOINTS = lambda x: str(x + '.SETPOINTS')
_SCAN_RES = lambda x: str(x + '.SCAN_RES')
_POSITIONER = lambda x: str(x + '.POSITIONER')

#widget communications dict
WDGCOM = 'WDG_COM'
WDGCOM_CMND = 'CMND'
WDGCOM_SPATIAL_ROIS = 'SPATIAL_ROIS'

#definitions of dict paths for the dict created by make_spatial_db_dict()
SPDB_ID_VAL = 'ID_VAL'
#SPDB_CMND = 'CMND'

SPDB_X = 'X'
SPDB_Y = 'Y'
SPDB_XY = 'XY'
SPDB_WG = 'WG' # stands for the E712 Wave Generator
SPDB_Z = 'Z'
SPDB_ZP = 'ZP'
SPDB_T = 'T'
SPDB_GONI = 'GONI'
SPDB_ZPZ_ADJUST = 'ZPZ_ADJUST'
SPDB_GX = 'GONI.X' #goni X
SPDB_GY = 'GONI.Y' #goni Y
SPDB_GZ = 'GONI.Z' #goni Z
SPDB_GT = 'GONI.T' #goni Theta
SPDB_G_ZPZ_ADJUST = 'GONI.ZPZ_ADJUST' #goni Theta focus adjustments

SPDB_OX = 'OSA.X' #osa X
SPDB_OY = 'OSA.Y' #osa Y
SPDB_OZ = 'OSA.Z' #osa Z
SPDB_ZX = 'ZP.X' #zoneplate X
SPDB_ZY = 'ZP.Y' #zoneplate Y
SPDB_ZZ = 'ZP.Z' #zoneplate Z

SPDB_EV = 'EV'

SPDB_EV_EV = 'EV.EV'
SPDB_EV_POL = 'EV.POL'

SPDB_EV_ROIS = 'EV_ROIS' #holds a list of energy roi's
SPDB_EV_ID = 'EV_ID' #holds the ev roi id in the spatial roi

SPDB_SINGLE_LST_SP_ROIS = 'SINGLE_LST.SP_ROIS' # for multi region supported scans, this holds the list of sp_rois
SPDB_SINGLE_LST_EV_ROIS = 'SINGLE_LST.EV_ROIS' # for multi region supported scans, this holds the list of ev_rois
SPDB_SINGLE_LST_POL_ROIS = 'SINGLE_LST.POL_ROIS' # for multi region supported scans, this holds the list of pol_rois
SPDB_SINGLE_LST_DWELLS = 'SINGLE_LST.DWELL' #  for multi region supported scans, this holds the list of dwell values for each of the N number of ev_roi's


SPDB_SUB_SPATIAL_ROIS = 'SUB_SPATIAL_ROIS' #this is meant to be used by scans for zoneplate scanning in a tiling mode
SPDB_SPATIAL_ROIS = 'SPATIAL_ROIS' # holds a dict of sp_roi's using the sp_id of each as the keys
SPDB_SPATIAL_ROIS_CENTER = 'SPATIAL_ROIS_CENTER' # holds the physical center of all of the spatial rois
SPDB_EV_NPOINTS = 'EV_NPOINTS'    #holds total number of EV points
SPDB_POL_NPOINTS = 'POL_NPOINTS' #holds total number of Polarity points
SPDB_RECT = 'RECT'    #holds total number of EV points
SPDB_PLOT_ITEM_ID = 'PLOT.ITEM.ID'    #the plotItem id, to be set by caller
SPDB_PLOT_ITEM_TITLE = 'PLOT.ITEM.TITLE'    #the plotItem title, to be set by caller
SPDB_PLOT_KEY_PRESSED = 'PLOT.KEY_PRESSED'    #the plotItem id, to be set by caller
SPDB_PLOT_IMAGE_TYPE = 'PLOT.IMAGE_TYPE'    #used to help determine what to plot when a scan is loaded. image_types-> Enum('focus', 'osafocus','image', 'line_plot')
SPDB_PLOT_SHAPE_TYPE = 'PLOT.SHAPE_TYPE'     #the plot shape item type: spatial_type_prefix-> ROI, SEG, PNT
SPDB_SCAN_PLUGIN_PANEL_IDX = 'SCAN_PLUGIN.SCAN_PANEL_IDX'     #the scan panel idx: scan_panel_order = Enum('Detector_Scan','OSA_Scan','OSA_Focus_Scan','Focus_Scan','Point_Scan', 'Image_Scan', 'ZP_Image_Scan', 'Positioner_Scan', 'Line_Scan', 'Image_Scan_Mainobj')
SPDB_SCAN_PLUGIN_TYPE = 'SCAN_PLUGIN.SCAN_TYPE'     #the scan type: scan_types-> Enum('Detector_Image','OSA_Image','OSA_Focus','Sample_Focus','Sample_Point_Spectrum', 'Sample_Line_Spectrum', 'Sample_Image', 'Sample_Image_Stack', 'Generic_Scan')
SPDB_SCAN_PLUGIN_SUBTYPE = 'SCAN_PLUGIN.SCAN_SUBTYPE'     #the scan sub type: scan_sub_types = Enum('Point_by_Point', 'Line_Unidir')
SPDB_SCAN_PLUGIN_SECTION_ID = 'SCAN_PLUGIN.SECTION_ID'    #a string saying with the scan section ID is, used for determining
SPDB_SCAN_PLUGIN_DATAFILE_PFX = 'SCAN_PLUGIN.DATA_FILE_PFX'    #a one character prefix for the scan type, using this to save files with a
SPDB_SCAN_PLUGIN_MAX_SCANRANGE = 'SCAN_PLUGIN.MAX_SCANRANGE' #scans like teh zp image scan have a max scan range of 100x100um
SPDB_SCAN_PLUGIN_EST_SCAN_TIME_SEC = 'SCAN_PLUGIN.EST_SCAN_TIME_SEC' # each scan should have an estemate of how long it will take to execute, in seconds
SPDB_SCAN_PLUGIN_EST_SCAN_TIME_STR = 'SCAN_PLUGIN.EST_SCAN_TIME_STR' # each scan should have an estemate of how long it will take to execute, as a string


SPDB_ACTIVE_DATA_OBJECT = 'ACTIVE_DATA_OBJ'

SPDB_HDW_ACCEL_USE = 'HDW_ACCEL_USE'
SPDB_HDW_ACCEL_AUTO_DDL = 'HDW_ACCEL_AUTO'
SPDB_HDW_ACCEL_REINIT_DDL = 'HDW_ACCEL_REINIT'

SPDB_XENABLED = _ENABLED(SPDB_X)
SPDB_XSTART = _START(SPDB_X)
SPDB_XSTOP = _STOP(SPDB_X)
SPDB_XCENTER = _CENTER(SPDB_X)
SPDB_XRANGE = _RANGE(SPDB_X)
SPDB_XSTEP = _STEP(SPDB_X)
SPDB_XNPOINTS = _NPOINTS(SPDB_X)
SPDB_XSCAN_RES = _SCAN_RES(SPDB_X)
SPDB_XPOSITIONER = _POSITIONER(SPDB_X)
SPDB_XSETPOINTS = _SETPOINTS(SPDB_X)

SPDB_YENABLED = _ENABLED(SPDB_Y)
SPDB_YSTART = _START(SPDB_Y)
SPDB_YSTOP = _STOP(SPDB_Y)
SPDB_YCENTER = _CENTER(SPDB_Y)
SPDB_YRANGE = _RANGE(SPDB_Y)
SPDB_YSTEP = _STEP(SPDB_Y)
SPDB_YNPOINTS = _NPOINTS(SPDB_Y)
SPDB_YSCAN_RES = _SCAN_RES(SPDB_Y)
SPDB_YPOSITIONER = _POSITIONER(SPDB_Y)
SPDB_YSETPOINTS = _SETPOINTS(SPDB_Y)

SPDB_ZENABLED = _ENABLED(SPDB_Z)
SPDB_ZSTART = _START(SPDB_Z)
SPDB_ZSTOP = _STOP(SPDB_Z)
SPDB_ZCENTER = _CENTER(SPDB_Z)
SPDB_ZRANGE = _RANGE(SPDB_Z)
SPDB_ZSTEP = _STEP(SPDB_Z)
SPDB_ZNPOINTS = _NPOINTS(SPDB_Z)
SPDB_ZSCAN_RES = _SCAN_RES(SPDB_Z)
SPDB_ZPOSITIONER = _POSITIONER(SPDB_Z)
SPDB_ZSETPOINTS = _SETPOINTS(SPDB_Z)

SPDB_ZXENABLED = _ENABLED(SPDB_ZX)
SPDB_ZXSTART = _START(SPDB_ZX)
SPDB_ZXSTOP = _STOP(SPDB_ZX)
SPDB_ZXCENTER = _CENTER(SPDB_ZX)
SPDB_ZX_RANGE = _RANGE(SPDB_ZX)
SPDB_ZXTEP = _STEP(SPDB_ZX)
SPDB_ZXNPOINTS = _NPOINTS(SPDB_ZX)
SPDB_ZXSCAN_RES = _SCAN_RES(SPDB_ZX)
SPDB_ZXPOSITIONER = _POSITIONER(SPDB_ZX)
SPDB_ZXSETPOINTS = _SETPOINTS(SPDB_ZX)

SPDB_ZYENABLED = _ENABLED(SPDB_ZY)
SPDB_ZYSTART = _START(SPDB_ZY)
SPDB_ZYSTOP = _STOP(SPDB_ZY)
SPDB_ZYCENTER = _CENTER(SPDB_ZY)
SPDB_ZYRANGE = _RANGE(SPDB_ZY)
SPDB_ZYSTEP = _STEP(SPDB_ZY)
SPDB_ZYNPOINTS = _NPOINTS(SPDB_ZY)
SPDB_ZYSCAN_RES = _SCAN_RES(SPDB_ZY)
SPDB_ZYPOSITIONER = _POSITIONER(SPDB_ZY)
SPDB_ZYSETPOINTS = _SETPOINTS(SPDB_ZY)

SPDB_ZZENABLED = _ENABLED(SPDB_ZZ)
SPDB_ZZSTART = _START(SPDB_ZZ)
SPDB_ZZSTOP = _STOP(SPDB_ZZ)
SPDB_ZZCENTER = _CENTER(SPDB_ZZ)
SPDB_ZZRANGE = _RANGE(SPDB_ZZ)
SPDB_ZZSTEP = _STEP(SPDB_ZZ)
SPDB_ZZNPOINTS = _NPOINTS(SPDB_ZZ)
SPDB_ZZSCAN_RES = _SCAN_RES(SPDB_ZZ)
SPDB_ZZPOSITIONER = _POSITIONER(SPDB_ZZ)
SPDB_ZZSETPOINTS = _SETPOINTS(SPDB_ZZ)


SPDB_GXENABLED = _ENABLED('GONI.X')
SPDB_GXSTART = _START('GONI.X')
SPDB_GXSTOP = _STOP('GONI.X')
SPDB_GXCENTER = _CENTER('GONI.X')
SPDB_GXRANGE = _RANGE('GONI.X')
SPDB_GXNPOINTS = _NPOINTS('GONI.X')
SPDB_GXSETPOINTS = _SETPOINTS('GONI.X')


SPDB_GYENABLED = _ENABLED('GONI.Y')
SPDB_GYSTART = _START('GONI.Y')
SPDB_GYSTOP = _STOP('GONI.Y')
SPDB_GYCENTER = _CENTER('GONI.Y')
SPDB_GYRANGE = _RANGE('GONI.Y')
SPDB_GYNPOINTS = _NPOINTS('GONI.Y')
SPDB_GYSETPOINTS = _SETPOINTS('GONI.Y')

SPDB_GZENABLED = _ENABLED('GONI.Z')
SPDB_GZSTART = _START('GONI.Z')
SPDB_GZSTOP = _STOP('GONI.Z')
SPDB_GZCENTER = _CENTER('GONI.Z')
SPDB_GZRANGE = _RANGE('GONI.Z')
SPDB_GZNPOINTS = _NPOINTS('GONI.Z')
SPDB_GZSETPOINTS = _SETPOINTS('GONI.Z')

SPDB_GTENABLED = _ENABLED('GONI.T')
SPDB_GTSTART = _START('GONI.T')
SPDB_GTSTOP = _STOP('GONI.T')
SPDB_GTCENTER = _CENTER('GONI.T')
SPDB_GTRANGE = _RANGE('GONI.')
SPDB_GTNPOINTS = _NPOINTS('GONI.T')
SPDB_GTSETPOINTS = _SETPOINTS('GONI.T')

#defs for the Active Data Object dictionary
ADO_CFG = 'CFG'
ADO_CFG_X = 'CFG.ROI.X'
ADO_CFG_Y = 'CFG.ROI.Y'
ADO_CFG_Z = 'CFG.ROI.Z'
#zpz
ADO_CFG_ZZ = 'CFG.ROI.ZZ'

ADO_CFG_GX = 'CFG.ROI.GX'
ADO_CFG_GY = 'CFG.ROI.GY'
ADO_CFG_GZ = 'CFG.ROI.GZ'
ADO_CFG_GT = 'CFG.ROI.GT'


ADO_START_TIME = 'START_TIME'
ADO_END_TIME = 'END_TIME'
ADO_DEVICES = 'DEVICES'
ADO_VERSION = 'VERSION'
ADO_DATA_SSCANS = 'DATA.SSCANS'
ADO_DATA_POINTS = 'DATA.POINTS'
ADO_STACK_DATA_POINTS = 'STACK_DATA.POINTS'
ADO_STACK_DATA_UPDATE_DEV_POINTS = 'STACK_DATA.UPDATE_DEV_POINTS'
ADO_SP_ROIS = 'STACK_DATA.SP_ROIS'
#ADO_POL_DATA_POINTS = 'POL.DATA.POINTS'

ADO_CFG_WDG_COM = 'CFG.WDG_COM'
ADO_CFG_WDG_COM_CMND = 'CFG.WDG_COM.CMND'
ADO_CFG_ROI = 'CFG.ROI'
ADO_CFG_POL_ROI = 'CFG.ROI.POL_ROI'
ADO_CFG_EV_ROIS = 'CFG.ROI.EV_ROIS'
ADO_CFG_SCAN_TYPE = 'CFG.SCAN_TYPE'
ADO_CFG_CUR_EV_IDX = 'CFG.CUR_EV_IDX'
ADO_CFG_CUR_SPATIAL_ROI_IDX = 'CFG.CUR_SPATIAL_ROI_IDX'
ADO_CFG_CUR_SAMPLE_POS = 'CFG.CUR_SAMPLE_POS'
ADO_CFG_CUR_SEQ_NUM = 'CFG.CUR_SEQ_NUM'
ADO_CFG_DATA_DIR = 'CFG.DATA_DIR'
ADO_CFG_DATA_FILE_NAME = 'CFG.DATA_FILE_NAME'     #the data file name WITHOUT the extension, that is determined by the
ADO_CFG_DATA_THUMB_NAME = 'CFG.DATA_THUMB_NAME'     #the data file thumbnail file name
ADO_CFG_DATA_THUMB_NAMES_LIST = 'CFG.DATA_THUMB_NAMES_LIST'
ADO_CFG_UNIQUEID = 'CFG.UNIQUEID'
ADO_CFG_PREFIX = 'CFG.PREFIX'
ADO_CFG_DATA_EXT = 'CFG.DATA_EXT'
ADO_CFG_STACK_DIR = 'CFG.STACK_DIR'
ADO_CFG_THUMB_EXT = 'CFG.THUMB_EXT'
ADO_CFG_DATA_IMG_IDX = 'CFG.DATA_IMG_IDX'
ADO_CFG_IMG_IDX_MAP = 'CFG.IMG_IDX_MAP'

ADO_CFG_DATA_STATUS = 'CFG.DATA_STATUS'




