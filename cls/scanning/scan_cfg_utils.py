'''
Created on Mar 30, 2015

@author: bergr
'''
from cls.utils.time_utils import make_timestamp_now
from cls.types.stxmTypes import scan_types

from cls.utils.dict_utils import dct_put
from cls.utils.thread_logger import doprint

from cls.appWidgets.dialogs import notify
from cls.appWidgets.dialogs import notify
from cls.types.stxmTypes import scan_types
from cls.utils.dict_utils import dct_put
from cls.utils.thread_logger import doprint
from cls.utils.time_utils import make_timestamp_now


def set_scan_start_time(dct):
    """
    This function assumes that the dct['ID'] is ACTIVE_DATA_DICT
    """
    dct_put(dct, 'SCAN.START_TIME', make_timestamp_now())


def set_scan_end_time(dct):
    """
    This function assumes that the dct['ID'] is ACTIVE_DATA_DICT
    """
    dct_put(dct, 'SCAN.END_TIME', make_timestamp_now())


def do_point_test():
    from bcm.device.counter import BaseGate, BaseCounter
    cntr = BaseCounter('testCI:counter')
    gate = BaseGate('testCO:gate')
    TEST_set_devices_for_point_scan(gate, cntr, None)


def do_line_test():
    from bcm.device.counter import BaseGate, BaseCounter
    cntr = BaseCounter('uhvCI:counter')
    gate = BaseGate('uhvCO:gate')
    set_devices_for_line_scan(2.0, 20, gate, cntr)


def do_e712_wavegen_point_test():
    from bcm.device.counter import BaseCounter
    cntr = BaseCounter('uhvCI:counter')  # set_devices_for_e712_wavegen_point_scan(dwell, numX, gate, counter, shutter=None)
    set_devices_for_e712_wavegen_point_scan(1.0, 50, cntr)


def do_e712_wavegen_line_unidir_test():
    from bcm.device.counter import BaseGate, \
        BaseCounter
    gate = BaseGate('uhvCO:gate')
    cntr = BaseCounter('uhvCI:counter')

    # set_devices_for_e712_wavegen_point_scan(dwell, numX, gate, counter, shutter=None)
    set_devices_for_e712_wavegen_line_scan(1.0, 50, gate, cntr)  # for testing

def TEST_set_devices_for_point_scan(gate, counter, shutter, type='point'):
    """ a convienience function to have a single place to configure the devices to acquire single points """

    trig_src_pfi = 4

    dwell = 1.0
    numE = 1
    numX = 50
    # num_points=1, dwell=2.0, duty=0.5, soft_trig=False, trig_delay=0.0
    gate.configure(1, dwell=dwell, duty=0.999, trig_delay=0.0)
    gate.trig_src_select.put(trig_src_pfi)  # /PFI 4  this will need to be part of a configuration at some point
    gate.retrig.put(1)

    # TO FIX shutter.configure( 1, dwell=roi['X'][NPOINTS] * roi['EV'][DWELL], duty=0.99)

    counter.configure(dwell, num_points=numX, row_mode='Point')
    counter.trig_src_select.put(trig_src_pfi)  # /PFI 4  this will need to be part of a configuration at some point
    counter.trig_type.put(3)  # Digital_EDge
    counter.sample_mode.put(2)  # DAQmx_HWTimedSinglePoint
    # counter.max_points.put(roi['X'][NPOINTS]) #X points
    counter.max_points.put(2)  # X points, so that the waveform returns <row> <point> <value> <pad>
    counter.row_mode.put(1)  # 1 point
    counter.retriggerable.put(True)

    if (type == 'point_spec'):
        counter.points_per_row.put(numE)  # EV point spectra
    else:
        counter.points_per_row.put(numX)  # X points


def set_devices_for_point_scan(scan_type, dwell, numE, numX, gate, counter, shutter=None):
    """ a convienience function to have a single place to configure the devices to acquire single points """

    trig_src_pfi = 4
    gate.configure(1, dwell=dwell, duty=0.999, trig_delay=0.0)
    gate.trig_src_select.put(trig_src_pfi)  # /PFI 4  this will need to be part of a configuration at some point
    gate.retrig.put(1)

    counter.configure(dwell, num_points=numX, row_mode='Point')
    counter.trig_src_select.put(trig_src_pfi)  # /PFI 4  this will need to be part of a configuration at some point
    counter.signal_src_clock_select.put(12)  # /PFI 12
    counter.trig_type.put(3)  # Digital_EDge
    counter.sample_mode.put(2)  # DAQmx_HWTimedSinglePoint
    # counter.max_points.put(roi['X'][NPOINTS]) #X points
    # counter.max_points.put(2)  # X points, so that the waveform returns <row> <point> <value> <pad>
    if (scan_type == scan_types.SAMPLE_LINE_SPECTRUM):
        counter.max_points.put(1)  # X points, so that the waveform returns <row> <point> <value> <pad>
    else:
        counter.max_points.put(2)  # X points, so that the waveform returns <row> <point> <value> <pad>
    counter.row_mode.put(1)  # 1 point
    counter.retriggerable.put(True)


    if (scan_type == scan_types.SAMPLE_POINT_SPECTRUM):
        counter.points_per_row.put(numE)  # EV point spectra
    else:
        counter.points_per_row.put(numX)  # X points


def set_devices_for_line_scan(dwell, numX, gate, counter, shutter=None):
    """ a convienience function to have a single place to configure the devices to acquire single points """

    trig_src_pfi = 3
    # _dwell = roi[EV_ROIS][0][DWELL]
    # numX = roi['X'][NPOINTS]

    xnpoints = numX + 2

    gate.configure(xnpoints, dwell=dwell, duty=0.5)
    gate.trig_src_select.put(trig_src_pfi)  # /PFI 3  connect PFI4 to the interferometer "pixelclock" wire

    # TO FIX shutter.configure( 1, dwell=roi['X'][NPOINTS] * roi['EV'][DWELL], duty=0.99)

    counter.configure(dwell, num_points=xnpoints, row_mode='Line')  # , row_mode='LINE')
    counter.trig_src_select.put(trig_src_pfi)  # /PFI 3  connect PFI3 to the interferometer "pixelclock" wire
    counter.trig_type.put(3)  # DAQmx_Val_DigPattern
    counter.signal_src_clock_select.put(12)  # /PFI 12
    counter.sample_mode.put(0)  # DAQmx_Val_FiniteSamps
    counter.max_points.put(xnpoints)  #
    counter.row_mode.put(0)  # 0 LINE
    counter.points_per_row.put(numX)
    counter.retriggerable.put(False)


# def set_devices_for_e712_wavegen_point_scan(scan_type, dwell, numE, numX, counter, numE=0):
def set_devices_for_e712_wavegen_point_scan(scan_type, dwell, numX, counter, numE=0):
    """ a convienience function to have a single place to configure the devices to acquire a line of points
    while scanning using the E712's wave form generator
    """
    NUM_FOR_EDIFF = 2
    #NUM_FOR_EDIFF = 0
    trig_src_pfi = 3
    xnpoints = numX + NUM_FOR_EDIFF

    # gate.configure(xnpoints, dwell=dwell, duty=0.5)
    # gate.trig_src_select.put(trig_src_pfi)  # /PFI 3  connect PFI4 to the interferometer "pixelclock" wire

    counter.configure(dwell, num_points=xnpoints, row_mode='Line')  # , row_mode='LINE')
    counter.trig_src_select.put(trig_src_pfi)  # /PFI 3  connect PFI3 to the interferometer "pixelclock" wire

    # counter.trig_type.put(3)  # DAQmx_Val_DigPattern
    counter.trig_type.put(6)  # Pause Trigger
    counter.signal_src_clock_select.put(3)  # /PFI 3 this is connected to the E712 OUT1

    counter.sample_mode.put(1)  # DAQmx_Val_ContSamps
    if(scan_type == scan_types.SAMPLE_LINE_SPECTRUM):
        #dont need the extra points
        counter.max_points.put(numX + 1)  #
    else:
        counter.max_points.put(xnpoints)  #
    counter.row_mode.put(0)  # 0 LINE
    counter.points_per_row.put(numX)
    counter.retriggerable.put(False)

    if (scan_type == scan_types.SAMPLE_POINT_SPECTRUM):
        counter.points_per_row.put(numE)  # EV point spectra
    else:
        counter.points_per_row.put(numX)  # X points


def set_devices_for_e712_wavegen_line_scan(dwell, numX, gate, counter, shutter=None):
    """ a convienience function to have a single place to configure the devices to acquire single line of points """
    NUM_FOR_EDIFF = 2
    trig_src_pfi = 3

    xnpoints = numX + 2

    gate.configure(xnpoints, dwell=dwell, duty=0.5)
    gate.sample_mode.put(0)  # DAQmx_Val_FiniteSamps
    gate.trig_src_select.put(trig_src_pfi)  # /PFI 3  connect PFI4 to the interferometer "pixelclock" wire

    # TO FIX shutter.configure( 1, dwell=roi['X'][NPOINTS] * roi['EV'][DWELL], duty=0.99)

    counter.configure(dwell, num_points=xnpoints, row_mode='Line')  # , row_mode='LINE')
    counter.trig_src_select.put(trig_src_pfi)  # /PFI 3  connect PFI3 to the interferometer "pixelclock" wire
    counter.trig_type.put(3)  # DAQmx_Val_DigPattern
    counter.signal_src_clock_select.put(12)  # /PFI 12
    counter.sample_mode.put(0)  # DAQmx_Val_FiniteSamps
    counter.max_points.put(xnpoints)  #
    counter.row_mode.put(0)  # 0 LINE
    counter.points_per_row.put(numX)
    counter.retriggerable.put(False)


def calc_scan_velo(start, stop, dwell, npts, max_velo):
    """ dwell is given in ms and used as seconds
    """
    lineTime = npts * (dwell * 0.001)  # sec
    ttlDist = (stop - start)  # um
    velo = (abs(ttlDist / lineTime))  # um /sec
    if (velo > max_velo):
        doprint('info', 'calc_velo: range=%.2f, dwell=%.2f, npts=%d' % (stop - start, dwell, npts))
        doprint('info', 'MAX_VELO EXCEEDED  %.3f > %.3f\n' % (velo, max_velo))
        velo = None
    else:
        doprint('info', 'calc_scan_velo: %.4f um/s\n' % velo)
        doprint('info', 'calc_scan_velo: lineTime %.4f s\n' % lineTime)
    return (velo)


def calc_scan_dwell(max_velo, rng, npts):
    """ dwell is given in ms and used as seconds
    """
    sec = float(rng) / float(max_velo)
    dwell = float(sec / float(npts)) * 1000.0
    doprint('info', 'calc_scan_dwell: max_velo=%.2f, range=%.2f um , npts=%d' % (max_velo, rng, npts))
    doprint('info', 'DWELL = %.2f ms' % (dwell))
    notify("Desired Velocity > max Velocity of motor",
           "calc_scan_dwell: max_velo=%.2f, range=%.2f um , npts=%d \n In order for scan to use max velo of motor the dwell has been automatically adjusted to %.2f ms" % (
           max_velo, rng, npts, dwell), accept_str="OK")
    return (dwell)


def calc_scan_npts(max_velo, rng, dwell):
    """ dwell is given in ms and used as seconds
    """
    sec = rng / max_velo
    npts = sec / (dwell / 1000.0)

    doprint('info', 'calc_scan_npts: max_velo=%.2f, range=%.2f um , dwell=%d' % (max_velo, rng, dwell))
    doprint('info', 'NPTS = %.2f ' % (npts))
    return (npts)


def ensure_valid_values(start, stop, dwell, npts, max_velo, do_points=True):
    rng = stop - start
    velo = calc_scan_velo(start, stop, dwell, npts, max_velo)
    if (velo is None):
        if (do_points):
            new_dwell = calc_scan_dwell(max_velo, rng, npts)
            # velo = calc_scan_velo(start, stop, new_dwell, npts, max_velo)
            velo = max_velo
            dwell = new_dwell
        else:
            new_npts = calc_scan_npts(max_velo, rng, dwell)
            velo = calc_scan_velo(start, stop, dwell, new_npts, max_velo)
            npts = new_npts

    return (velo, npts, dwell)


def calc_accRange(positioner, scan_type, scan_rng, velo, dwell, accTime=0.01):
    if (scan_type == 'COARSE'):
        # a fudge factor
        # accR = 2.0 * (velo * accTime) + (dwell * 0.2)
        # accR = 8.0 * (velo * accTime) + (dwell * 0.2)
        # accR = 75
        # accR = 300
        # accR = 300
        # accR = 700
        # accR = 600
        accR = velo * (accTime + 0.1)

    else:
        # as of Jan 19 2017, slope is 0.16 with a min of 1.0
        # so m=0.16, b=-1.0
        # accR = 2.0
        m = 0.16
        b = -1.0

        accR = m * (scan_rng) + b
        if (accR < 1.5):
            accR = 1.5
        # 		if(scan_rng >= 20.0):
        # 			accR = 7.0
        # 		elif(scan_rng >= 10.0):
        # 			accR = 3.0
        # 		elif(scan_rng <= 2.0):
        # 			#accR = 0.45 * scan_rng
        # 			accR = 0.65 * scan_rng
        # 		else:
        # 			accR = 3.0

    if (positioner == 'DetectorX.X'):
        accR = 700

    print('accRange is %.2f um' % accR)

    return (accR)


def calc_trig_delay(positioner, scan_type, scan_rng, velo, dwell, accTime=0.005):
    dly = 0.0
    if (positioner == 'DetectorX.X'):
        dly = 0.500

    print('calc_trig_delay is %.2f um' % dly)

    return (dly)


if __name__ == '__main__':
    # do_point_test()
    # start = 0
    # stop = 125
    # dwell = 2.578
    # npts = 50
    # max_velo = 3500
    # ensure_valid_values(start, stop, dwell, npts, max_velo)
    # do_line_test()

    # do_e712_wavegen_point_test()
    do_e712_wavegen_line_unidir_test()
