
from cls.utils.roi_dict_defs import *
from bcm.devices.device_names import *
from cls.utils.roi_utils import get_base_roi, get_base_energy_roi, make_spatial_db_dict, on_start_changed
from cls.data_io.utils import test_eq, check_roi_for_match, get_first_entry_key, get_first_sp_db_from_entry, get_axis_setpoints_from_sp_db
from cls.utils.dict_utils import dct_get, dct_put
from cls.utils.log import get_module_logger
_logger = get_module_logger(__name__)


def init_test_sp_db():
    cx = -953.0
    cy = -16
    cz = -4722.0
    rx = 60.0
    ry = 0.0
    rz = 50.0
    nx = 228
    ny = 228
    nz = 60
    #sx = rx / float((nx + 1))
    #sy = ry / float((ny + 1))
    dwell = 1.0
    energy_pos = 695.0

    x_roi = get_base_roi(SPDB_X, DNM_ZONEPLATE_X, cx, rx, nx, None)
    on_start_changed(x_roi)
    y_roi = get_base_roi(SPDB_Y, DNM_ZONEPLATE_Y, cy, ry, ny, None)
    on_start_changed(y_roi)
    z_roi = get_base_roi(SPDB_Z, DNM_ZONEPLATE_Z, cz, rz, nz, enable=True)
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
    #self.set_fld_with_val(self.dwellFld, '%.2f' % dwell)
    self.set_fld_with_val(self.dwellFld, '%.2f' % 1.0)

    self.set_fld_with_val(self.startXFld, '%.2f' % dct_get(test_sp_db, SPDB_XSTART))
    self.set_fld_with_val(self.endXFld, '%.2f' % dct_get(test_sp_db, SPDB_XSTOP))
    self.set_fld_with_val(self.npointsXFld, '%d' % dct_get(test_sp_db, SPDB_XNPOINTS))
    self.set_fld_with_val(self.stepXFld, '%.2f' % dct_get(test_sp_db, SPDB_XSTEP))

    self.set_fld_with_val(self.startYFld, '%.2f' % dct_get(test_sp_db, SPDB_YSTART))
    self.set_fld_with_val(self.endYFld, '%.2f' % dct_get(test_sp_db, SPDB_YSTOP))

    self.set_fld_with_val(self.centerZPFld, '%.2f' % dct_get(test_sp_db, SPDB_ZCENTER))
    self.set_fld_with_val(self.rangeZPFld, '%.2f' % dct_get(test_sp_db, SPDB_ZRANGE))
    self.set_fld_with_val(self.npointsZPFld, '%d' % dct_get(test_sp_db, SPDB_ZNPOINTS))
    self.set_fld_with_val(self.stepZPFld, '%.2f' % dct_get(test_sp_db, SPDB_ZSTEP))

    #need to pass the scan panel order index
    self.test_scan.emit(self.idx)




