
from cls.utils.roi_dict_defs import *
from bcm.devices.device_names import *
from cls.utils.roi_utils import get_base_roi, get_base_energy_roi, make_spatial_db_dict, on_start_changed

cx = 0.0
cy = 0.0
rx = 150.0
ry=150.0
nx = 25
ny = 25
sx = rx / float((nx + 1))
sy = ry / float((ny + 1))
dwell = 1.0
energy_pos = 680.0

x_roi = get_base_roi(SPDB_X, DNM_OSA_X, cx, rx, nx, sx)
on_start_changed(x_roi)
y_roi = get_base_roi(SPDB_Y, DNM_OSA_Y, cy, ry, ny, sy)
on_start_changed(y_roi)
z_roi = get_base_roi(SPDB_Z, DNM_OSA_Z, -1000, 0, 1, enable=False)
on_start_changed(z_roi)
e_roi = get_base_energy_roi(SPDB_EV, DNM_ENERGY, energy_pos, energy_pos, 0, 1, dwell, None, enable=False)
on_start_changed(e_roi)

test_sp_db = make_spatial_db_dict(x_roi=x_roi, y_roi=y_roi, z_roi=z_roi, e_roi=e_roi)





