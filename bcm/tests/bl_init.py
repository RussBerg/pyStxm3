# Make plots update live while scans run.
from io import StringIO
from itertools import tee
from bluesky.utils import install_kicker
from bluesky.callbacks.best_effort import BestEffortCallback
from bluesky.utils import ProgressBarManager
from bluesky import RunEngine
from cls.scan_engine.bluesky.qt_run_engine import QRunEngine
from bluesky import Msg
from ophyd.sim import det1, det2, det3, motor1, motor2, motor3, SynGauss, noisy_det
from bluesky.plans import scan, list_scan, scan_nd, spiral, spiral_fermat, spiral_square
import bluesky.preprocessors as bpp
import bluesky.plan_stubs as bps
from bluesky.plan_stubs import pause, open_run, close_run, sleep, mv, read
from bluesky.plans import count
from cycler import cycler
from bluesky.plans import list_scan, grid_scan, scan, scan_nd, count
from databroker import Broker
from bluesky.utils import install_nb_kicker, install_kicker, install_qt_kicker
from bluesky.callbacks import LiveTable
import suitcase.json_metadata as json_suitcase
import suitcase.csv as csv_suitcase
#from suitcase_tiff — image data TIFF stacks or individual TIFF files
#suitcase-csv — scalar data as Common-Separated Values
#suitcase-json-metadata

from ophyd.areadetector.detectors import SimDetector

from cls.utils.roi_utils import get_base_roi

from ophyd import EpicsMotor

def caught_doc_msg(name, doc):
    print('caught_doc_msg: [%s]' % (name))
    print(doc)
RE = QRunEngine()
#RE = RunEngine({})
db = Broker.named('mongo_databroker')
# Insert all metadata/data captured into db.
RE.subscribe(db.insert)

data_dir = r'C:\wrkshp\live_qt5\suitcase_output\json'

#RE.subscribe(caught_doc_msg)

#RE.waiting_hook = ProgressBarManager()
bec = BestEffortCallback()
# Send all metadata/data captured to the BestEffortCallback.
#RE.subscribe(bec)
install_nb_kicker()
#x_roi = get_base_roi('X', 'fake_x_mtr', 0, 50, 25, stepSize=None, max_scan_range=None, enable=True, is_point=False, src=None)
x_roi = get_base_roi('X', 'fake_x_mtr', 0, 50, 25)
y_roi = get_base_roi('Y', 'fake_y_mtr', 0, 40, 25)
#x_roi = {'START': -25}
#y_roi = {'START': -15}
#z_roi = get_base_roi('Y', 'fake_y_mtr', 0, 30, 25)
rois = [x_roi, y_roi]

x_mtr = motor1
y_mtr = motor2

#uncomment these 2 lines to see error
x_mtr = EpicsMotor('IOC:m102', name='m102')
y_mtr = EpicsMotor('IOC:m103', name='m103')

x_mtr.settle_time = 3
y_mtr.settle_time = 3

while not x_mtr.connected:
    sleep(0.1)
while not y_mtr.connected:
    sleep(0.1)

mtrs = [x_mtr, y_mtr]
dets = [noisy_det]
# #RE(count(dets))
# #RE(scan(dets, motor1, -1, 1, 10))
# #list(point_spec_scan(dets, mtrs, rois))
# RE(point_spec_scan(dets, mtrs, rois))
#
# header = db[-1]
# primary_docs = header.documents(fill=True)
# print(list(primary_docs))
# ccd_det = SimDetector('myAD', name='test')
# ccd_det.find_signal('a', f=StringIO())
# ccd_det.find_signal('a', use_re=True, f=StringIO())
# ccd_det.find_signal('a', case_sensitive=True, f=StringIO())
# ccd_det.find_signal('a', use_re=True, case_sensitive=True, f=StringIO())
# ccd_det.component_names
# ccd_det.report
#
# cam = ccd_det.cam
#
# cam.image_mode.put('Single')
# # plugins don't live on detectors now:
# # det.image1.enable.put('Enable')
# cam.array_callbacks.put('Enable')

#get data
#header = db[-1]
# docs = header.documents(fill=True)
#docs1, docs2, docs3 = tee(docs, 3)
#json_suitcase.export(docs1, data_dir, 'bl')
#csv_suitcase.export(docs2, data_dir, 'bl')
from event_model import RunRouter
from suitcase.csv import Serializer

def factory(name, start_doc):

    serializer = Serializer(data_dir)
    serializer('start', start_doc)

    return [serializer], []

rr = RunRouter([factory])
RE.subscribe(rr)

#RE(scan([noisy_det], y_mtr, -10, 50, 10), LiveTable([y_mtr, noisy_det]))


# RE(scan(dets,
#    ...:         motor1, -1.5, 1.5,  # scan motor1 from -1.5 to 1.5
#    ...:         motor2, -0.1, 0.1,  # ...while scanning motor2 from -0.1 to 0.1
#    ...:         11))  # ...both in 11 steps
#RE(scan(dets, y_mtr, -90.5, 90.5, x_mtr, -50, 50, 35), LiveTable([y_mtr, x_mtr, noisy_det]))  # ...both in 35 steps
def do_arbitrary_line(xmtr, ymtr, npoints):
    RE(scan(dets, ymtr, -20.5, 20.5, xmtr, -30, 30, npoints), LiveTable([y_mtr, x_mtr, noisy_det]))  # ...both in 25 steps

def do_list_scan(mtr):
    # Scan motor1 and motor2 jointly through a 5-point trajectory.
    RE(list_scan(dets, mtr, [-35, 1, 18, 26, 45]), LiveTable([mtr, noisy_det]))