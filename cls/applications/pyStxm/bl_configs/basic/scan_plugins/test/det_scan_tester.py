
from random import randint

from cls.utils.roi_dict_defs import *
from bcm.devices.device_names import *
from cls.utils.roi_utils import get_base_roi, get_base_energy_roi, make_spatial_db_dict, on_start_changed
from cls.data_io.utils import test_eq, check_roi_for_match, get_first_entry_key, get_first_sp_db_from_entry, get_axis_setpoints_from_sp_db
from cls.utils.dict_utils import dct_get, dct_put
from cls.utils.log import get_module_logger
_logger = get_module_logger(__name__)

# cx = 0.0
# cy = 0.0
# rx = 150.0
# ry=150.0
# nx = 10
# ny = 10
# sx = rx / float((nx + 1))
# sy = ry / float((ny + 1))
# dwell = 1.0
# energy_pos = 680.0
#
# x_roi = get_base_roi(SPDB_X, DNM_DETECTOR_X, cx, rx, nx, sx)
# on_start_changed(x_roi)
# y_roi = get_base_roi(SPDB_Y, DNM_DETECTOR_Y, cy, ry, ny, sy)
# on_start_changed(y_roi)
# z_roi = get_base_roi(SPDB_Z, DNM_DETECTOR_Z, 0, 0, 0, enable=False)
# on_start_changed(z_roi)
# e_roi = get_base_energy_roi(SPDB_EV, DNM_ENERGY, energy_pos, energy_pos, 0, 1, dwell, None, enable=False)
# on_start_changed(e_roi)
#
# test_sp_db = make_spatial_db_dict(x_roi=x_roi, y_roi=y_roi, z_roi=z_roi, e_roi=e_roi)
#test_sp_db = None

def init_test_sp_db():
    cx = 0.0
    cy = 0.0
    rx = 150.0
    ry = 150.0

    npnts = randint(5, 25)

    nx = npnts
    ny = npnts
    sx = rx / float((nx + 1))
    sy = ry / float((ny + 1))
    dwell = 1.0
    energy_pos = 680.0

    x_roi = get_base_roi(SPDB_X, DNM_DETECTOR_X, cx, rx, nx, sx)
    on_start_changed(x_roi)
    y_roi = get_base_roi(SPDB_Y, DNM_DETECTOR_Y, cy, ry, ny, sy)
    on_start_changed(y_roi)
    z_roi = get_base_roi(SPDB_Z, DNM_DETECTOR_Z, 0, 0, 0, enable=False)
    on_start_changed(z_roi)
    e_roi = get_base_energy_roi(SPDB_EV, DNM_ENERGY, energy_pos, energy_pos, 0, 1, dwell, None, enable=False)
    on_start_changed(e_roi)

    test_sp_db = make_spatial_db_dict(x_roi=x_roi, y_roi=y_roi, z_roi=z_roi, e_roi=e_roi)
    return(test_sp_db)


def do_test(self, test_sp_db):
    '''
    set the fields of the scan and emit a 'test_scan' signal
    :return:
    '''
    #global test_sp_db

    self.set_fld_with_val(self.centerXFld, '%.2f' % dct_get(test_sp_db, SPDB_XCENTER))
    self.set_fld_with_val(self.rangeXFld, '%.2f' % dct_get(test_sp_db, SPDB_XRANGE))
    self.set_fld_with_val(self.npointsXFld, '%d' % dct_get(test_sp_db, SPDB_XNPOINTS))

    self.set_fld_with_val(self.centerYFld, '%.2f' % dct_get(test_sp_db, SPDB_YCENTER))
    self.set_fld_with_val(self.rangeYFld, '%.2f' % dct_get(test_sp_db, SPDB_YRANGE))
    self.set_fld_with_val(self.npointsYFld, '%d' % dct_get(test_sp_db, SPDB_YNPOINTS))

    # need to pass the scan panel order index
    self.test_scan.emit(self.idx)




