
# Make plots update live while scans run.
from bluesky.utils import install_kicker
from bluesky.callbacks.best_effort import BestEffortCallback
from bluesky import RunEngine
from bluesky import Msg
from ophyd.sim import det1, det2, det3, motor1, motor2, motor3, SynGauss, noisy_det
from bluesky.plans import scan
import bluesky.preprocessors as bpp
import bluesky.plan_stubs as bps
from bluesky.plan_stubs import pause, open_run, close_run, sleep, mv, read
from cycler import cycler
from bluesky.plans import list_scan, grid_scan, scan, scan_nd, count
from databroker import Broker

from ophyd import EpicsMotor

#from cls.utils.roi_utils import get_base_roi

def point_spec_scan(dets, motors, rois, num_ev_pnts=4, md={'scan_type': 'point_spec_scan'}):
    @bpp.run_decorator(md=md)
    def do_scan():
        ev_mtr = motor3

        for ev in range(num_ev_pnts):
            yield from mv(ev_mtr, ev)
            for i in range(len(mtrs)):
                yield from mv(motors[i], rois[i]['START'])

                yield from bps.create(name='primary')
                yield from read(dets[0])
                yield from bps.save()
                print('ev[%d] : done read for motor[%d] at %.2f' % (ev, i,rois[i]['START']))
                #yield from bps.sleep((1.0))

    return(yield from do_scan())

if __name__ =='__main__':

    def caught_doc_msg(name, doc):
        print('caught_doc_msg: [%s]' % (name))
        print(doc)

    RE = RunEngine({})
    db = Broker.named('mongo_databroker')
    # Insert all metadata/data captured into db.
    RE.subscribe(db.insert)
    RE.subscribe(caught_doc_msg)
    bec = BestEffortCallback()
    # Send all metadata/data captured to the BestEffortCallback.
    RE.subscribe(bec)
    #x_roi = get_base_roi('X', 'fake_x_mtr', 0, 50, 25, stepSize=None, max_scan_range=None, enable=True, is_point=False, src=None)
    #x_roi = get_base_roi('X', 'fake_x_mtr', 0, 50, 25)
    #y_roi = get_base_roi('Y', 'fake_y_mtr', 0, 40, 25)
    x_roi = {'START': -25}
    y_roi = {'START': -15}
    #z_roi = get_base_roi('Y', 'fake_y_mtr', 0, 30, 25)
    rois = [x_roi, y_roi]

    x_mtr = motor1
    y_mtr = motor2

    #uncomment these 2 lines to see error
    x_mtr = EpicsMotor('IOC:m102', name='zone.x')
    y_mtr = EpicsMotor('IOC:m103', name='zone.y')

    x_mtr.settle_time = 3
    y_mtr.settle_time = 3

    while not x_mtr.connected:
        sleep(0.1)
    while not y_mtr.connected:
        sleep(0.1)

    mtrs = [x_mtr, y_mtr]
    dets = [noisy_det]
    #RE(count(dets))
    #RE(scan(dets, motor1, -1, 1, 10))
    #list(point_spec_scan(dets, mtrs, rois))
    RE(point_spec_scan(dets, mtrs, rois))
    header = db[-1]
    primary_docs = header.documents(fill=True)
    print(list(primary_docs))

