'''
Created on Sep 6, 2016
@author: control
'''
import numpy as np
from cls.plotWidgets.curveWidget import CurveViewerWidget
from cls.scanning.e712_wavegen.e712_errors import e712_errors

def pnts_per_seg(linetime):
    '''
    2 points = 0.1ms
    20 points == 1ms
    200 points == 10ms
    100ms == 2000 pts
    pnts = (linetime / 0.010) * 200
    '''
    pnts = int((linetime / 0.010) * 200)
    return (pnts)

def gen_seg_str(tblid, start, stop, dwell=1.0, num_wv_points=10, accRange=2, _new=False):
    if (start < 0):
        rng = float(stop + start)
    else:
        rng = float(stop - start)
    if (rng == 0.0):
        linetime = dwell * 0.001
        velo = 1000
        acctime = accRange / velo
    else:
        linetime = rng * (dwell * num_wv_points * 0.001)
        velo = rng / linetime
        acctime = accRange / velo
    speedupdown_pnts = pnts_per_seg(acctime)
    wavtype = 'LIN'
    seglen = pnts_per_seg(linetime)
    amp = rng
    offset = start
    wavlen = seglen + speedupdown_pnts
    startpoint = 0
    speedupdown = speedupdown_pnts
    s = gen_wav_table_strs(tblid, seglen, amp, offset, wavlen, startpoint, speedupdown, wavtype='LIN', _new=_new)
    return (s)

# def gen_X_waveform_strs(start, stop, accRange):
#     '''
#     WAV <TableID> <AppendWave> <WaveType> <SegLength_Npts> <Amp> <Offset> <Wavelength> <Startpoint> <Speedupdown_Npts>
#
#     '''
#     if(start < 0):
#         rng = float(stop + start)
#     else:
#         rng = float(stop - start)
#
#     _start = start - accRange
#     _stop = stop + accRange
#     _rng = rng + 2*(accRange)
#
#     s = []
#     s.append('WCL 1')
#     s.append('WAV 1 X LIN 100 0 %.3f 100 0 20' % (_start))
#     s.append('WAV 1 & LIN 10000 %.3f %.3f 10000 0 100' % (_rng, _start))
#
#     s.append('WAV 1 & LIN 200 0 %.3f 200 0 50' % (_rng - accRange))
#     s.append('WAV 1 & LIN 200 %.3f %.3f 200 0 50' % (-1.0*_rng, _rng - accRange))
#     s.append('WAV 1 & LIN 10 0 %.3f 10 0 50' % (-1.0*accRange))
#     s.append('WAV 1 & LIN 200 0 %.3f 200 0 50' % (-1.0*accRange))
#     return(s)
def line_time(rng, dwell, num_points):
    # linetime = rng * (dwell * num_points * 0.001)
    linetime = (dwell * num_points * 0.001)
    return (linetime)

def scan_velo(rng, linetime):
    velo = rng / linetime
    return (velo)

def accel_time(accRange, velo):
    acctime = accRange / velo
    return (acctime)

# def gen_seg2_str(tblid, start, stop, dwell=1.0, num_points=10, accRange=2):
#     '''
#     2 points = 0.1ms
#     20 points == 1ms
#     200 points == 10ms
#
#     '''
#     if(start < 0):
#         rng = float(stop + start)
#     else:
#         rng = float(stop - start)
#     linetime = line_time(rng, dwell, num_points)
#     velo = scan_velo(rng, linetime)
#     acctime = accel_time(accRange, velo)
#     speedupdown_pnts = pnts_per_seg(acctime)
#
#
#     wavtype = 'LIN'
#     seglen = pnts_per_seg(linetime)
#     amp = rng
#     offset = start
#     wavlen = seglen + speedupdown_pnts
#     startpoint = 0
#     speedupdown = speedupdown_pnts
#
#     s = gen_wav_table_strs(tblid, seglen, amp, offset, wavlen, startpoint, speedupdown, wavtype='LIN')
#     return(s)

def gen_wav_table_strs(tblid, seglen_npts, amp, offset, wavlen, startpoint, speedupdown_npts, wavtype='LIN',
                       _new=False):
    '''
    WAV <TableID> <AppendWave> <WaveType> <SegLength> <Amp> <Offset> <Wavelength> <Startpoint> <Speedupdown>
    <TableID>: integer betwen 1 and 120
    <AppendWave>:   'X' clears the table and starts with 1st point
                    '&' appends to the existing table
    <WaveType>: 'PNT' user defined curve
                'SIN_P' inverted cosine curve
                'RAMP' ramp curve
                'LIN' single scan line curve
    <SegLength>: the length of the wave table segment in points, only the number of points
                given by seglen will be written to the wave table
    <Amp>:     The amplitude of the scan in EGU
    <Offset>:  the offset of the scan line in EGU
    <Wavelength>: the length of the single scan line in curve points
    <Startpoint>: the index of the starting point of the scan line in the segment.
                    lowest possible value is 0
    <Speedupdown>: the number of points for speed up and slow down
    NOTE: for SIN_P, RAMP and LIN wave types: if the SegLen values is larger than the WaveLength value, the missing points in hte segment
        are filled with the endpoint value
        - # 200 points == 10ms

    l = []
    l.append('WAV %d X %s %d %.3f %.3f %d %d %d' % (tblid, wavtype, seglen, amp, offset, wavlen, startpoint, speedupdown ))
    #WAV 1 X LIN 100 0 0 100 0 20
    #this is a line of 500pts over 3um with a dwell of 2ms, so the line time should be 1second, speedup/down is 50ms
    # WAV <TableID> <AppendWave> <WaveType> <SegLength> <Amp> <Offset> <Wavelength> <Startpoint> <Speedupdown>
    WAV 1 & LIN 10000 12 -1 10000 0 100
    WAV 1 & LIN 200 0 12 200 0 50
    WAV 1 & LIN 200 -12 12 200 0 50
    WAV 1 & LIN 10 0 0 10 0 50
    WAV 1 & LIN 200 0 0 200 0 50
    WAV 2 X LIN 9500 0.1 0 1000 0 10
    WAV 2 X LIN 200 0.1 0.1 2000 0 10
    WAV 2 X LIN 9500 0.1 0 2000 0 10
    WAV 2 & LIN 9500 0.1 0.1 2000 0 10
    #WGO 1 1 2 257
    #WOS 2 0
    #MOV 2 0
    #WGO 1 1 2 257
    #WOS 2 0
    #MOV 2 0

    ### ORIGINAL FROM ANDREAS
    #  WAV 1 X LIN 800 100 0 800 0 20
    #  WAV 1 & LIN 200 0 100 200 0 20
    #  WAV 1 & LIN 800 -100 100 800 0 20
    #  WAV 1 & LIN 200 0 0 200 0 20
    #  WAV 2 X LIN 1000 1 0 100 900 10
    #  WAV 2 X LIN 1000 1 1 100 900 10
    #  WAV 2 X LIN 1000 1 0 100 900 10
    #  WAV 2 & LIN 1000 1 1 100 900 10
    #  WGO 1 1 2 257
    #  WOS 2 0
    #  MOV 2 0
    #  WGO 1 1 2 257
    #  WOS 2 0
    #  MOV 2 0
    '''
    if (_new):
        append_wv = 'X'
    else:
        append_wv = '&'
    s = 'WAV %d %s %s %d %.3f %.3f %d %d %d' % (
    tblid, append_wv, wavtype, seglen_npts, amp, offset, wavlen, startpoint, speedupdown_npts)
    return (s)

def gen_pxp_line_trig_str(dwell, npoints, accRange, velo):
    '''
    1 ms == 20 points, so if the line is made of of n points with a dwell of m ms then I should be
    able to calc the point for each point on the line
    using the TWS command
        TWS <TrigOutputId> <point number> <switch hi/low>
    '''
    output_id = 1
    pts_per_dwell = dwell * 20
    # linetime = line_time(rng, dwell, npoints)
    # velo = scan_velo(rng, linetime)
    acctime = accel_time(accRange, velo)
    speedupdown_pnt = pnts_per_seg(acctime)
    l = []
    l.append('TWC')
    for i in range(1, npoints + 1):
        # pnt_num = i * int(pts_per_dwell)
        pnt_num = i * int(speedupdown_pnt)
        l.append('TWS %d %d 1' % (output_id, pnt_num))
        for j in range(10):
            l.append('TWS %d %d 1' % (output_id, pnt_num + j))
    # now set teh trigger mode to Generator Trigger
    l.append('CTO %d 3 4' % (output_id))
    return (l)

def sock_send(sock, msg, do_rcv=True, verbose=True):
    term_char = '\n'
    data = None
    if (verbose):
        print('sock_send: sending: [%s]' % msg)
    sock.sendall(msg + term_char)
    # while amount_received < amount_expected:
    # <<1=1.711897402e-001
    if (do_rcv):
        data = sock.recv(500)
    return (data)

def check_for_error(sock):
    err = sock_send(sock, 'ERR?', do_rcv=True, verbose=False)
    i = int(err)
    if (i == 0):
        # no error
        pass
    else:
        e_msg = e712_errors[i][1]
        print(e_msg)
        exit()

def get_wav_datatbl(sock, tblid, amount_expected):
    amount_received = 0
    n_dat = []
    start_idx = 1
    num_bytes_expected = amount_expected * 9
    while amount_received < amount_expected:
        sock_send(sock, 'GWD? %d %d %d' % (start_idx, amount_expected, tblid))
        # check_for_error(sock)
        # <<1=1.711897402e-001
        # data = sock.recv(500 * 12)v
        # data = sock.recv(500)
        data = sock.recv(num_bytes_expected)
        #       # TYPE = 1
        #       # SEPARATOR = 9
        #       # DIM = 1
        #       # SAMPLE_TIME = 0.000050
        #       # NDATA = 500
        #       # NAME0 = Wave Table3
        #       # END_HEADER
        # skip the header
        data = data.split('\n')
        data = data[1:]
        # amount_received += 500
        amount_received += amount_expected
        # start_idx += 500
        start_idx += amount_expected
    return (data)

def plot_data(xdat, ystr_dat):
    import numpy as np
    ystrs = np.array(ystr_dat, dtype='|S8')
    ydat = ystrs.astype(np.float)
    plot = CurveViewerWidget()
    plot.clear_plot()
    plot.create_curve('point_spectra', curve_style='Lines')
    x = 0
    for y in ydat:
        plot.addXYPoint('point_spectra', x, y, update=False)
        x += 1
    plot.addXYPoint('point_spectra', x, y, update=True)
    plot.show()

def socket_test():
    import socket
    import sys
    # Create a TCP/IP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = '192.168.168.10'
    port = 50000
    # Connect the socket to the port where the server is listening
    server_address = (host, port)
    print('connecting to %s port %s' % server_address, file=sys.stderr)
    sock.connect(server_address)
    try:
        # Send data
        data = sock_send(sock, '*IDN?')
        print('received "%s"' % data, file=sys.stderr)
    finally:
        print('closing socket', file=sys.stderr)
        sock.close()

def gen_y_step_wav_strs(start, stop, step, npoints, dwell, do_clear=True, tbl_id=2):
    '''
    s = define_seg_by_time(0.1, 0.02, 0.05, 0.0, _new=True, tblid=4)
    '''
    l = []
    if (do_clear):
        l.append('WCL %d' % tbl_id)
    # stay at first position for dwell time
    done = False
    _start = start
    _stop = stop
    _step = step
    pos = start
    l.append(gen_seg_str(1, pos, pos, dwell=dwell, num_wv_points=20, accRange=0, _new=True))
    l.append(gen_seg_str(1, pos, pos + _step, dwell=1, num_wv_points=5, accRange=0))
    pos += _step
    for i in range(npoints):
        # gen_seg_str(tblid, start, stop, dwell=1.0, num_points=10, accRange=2, _new=False):
        l.append(gen_seg_str(tbl_id, pos, pos, dwell=dwell, num_wv_points=20, accRange=1))
        # move to next step
        l.append(gen_seg_str(tbl_id, pos, pos + _step, dwell=1, num_wv_points=5, accRange=1))
        pos += _step
    ##stay
    # l.append(gen_seg_str(1, 0.1, 0.1, dwell=2.0, num_points=10, accRange=1))
    return (l)

def get_npoints_from_ms(ms):
    return (ms * 20)

def gen_x_line_wav_strs(start, stop, step, npoints, dwell, do_clear=False, tbl_id=1):
    """
    WAV 3 X LIN 6400 8 -1.5 6400 0 1200
    WAV 3 & LIN 1200 -8 6.5 1200 0 400
    """
    l = []
    if (do_clear):
        l.append('WCL %d' % tbl_id)
    # stay at first position for dwell time
    done = False
    _start = start
    _stop = stop
    _step = step
    pos = start
    rng = stop - start
    # speedup/slowdown time
    speedupdown = 0.06  # 10ms
    returntime = 0.1  # 50ms
    if (start < 0):
        rng = float(stop + start)
    else:
        rng = float(stop - start)
    if (rng == 0.0):
        linetime = dwell * 0.001
        velo = 1000
        acctime = accRange / velo
        segtime = linetime + (2.0 * speedupdown)
    else:
        linetime = (dwell * npoints * 0.001)
        velo = rng / linetime
        acctime = accRange / velo
        segtime = linetime + (2.0 * speedupdown)
    speedupdown_npnts = pnts_per_seg(acctime)
    seglen_npts = pnts_per_seg(segtime)
    amp = rng + (2.0 * accRange)
    return_npts = pnts_per_seg(returntime)
    offset = start - accRange
    l.append(gen_wav_table_strs(tblid, seglen_npts, amp, offset, seglen_npts, 0, speedupdown_npnts, wavtype='LIN',
                                _new=True))
    l.append(
        gen_wav_table_strs(tblid, return_npts, -1.0 * amp, amp + offset, return_npts, 0, return_npts, wavtype='LIN',
                           _new=False))
    rng = pos - start
    return (l)

def define_seg_by_time(seg_time, speedupdown_time, step_size, offset, _new=True, tblid=1):
    seglen_npts = pnts_per_seg(seg_time)
    speedupdown_npnts = pnts_per_seg(speedupdown_time)
    amp = step_size
    s = gen_wav_table_strs(tblid, seglen_npts, amp, offset, seglen_npts, 0, speedupdown_npnts, wavtype='LIN', _new=_new)
    return (s)

# def gen_y_line_wav_strs(start, stop, step, npoints, dwell, do_clear=False, tbl_id=2):
def gen_y_line_wav_strs(start, stop, step, step_time, sit_time, do_clear=False, tbl_id=2):
    """
    """
    l = []
    if (do_clear):
        l.append('WCL %d' % tbl_id)
    # stay at first position for dwell time
    done = False
    _start = start
    _stop = stop
    _step = step
    pos = start
    rng = stop - start
    # speedup/slowdown time
    segtime = step_time
    speedupdown_npnts = pnts_per_seg(acctime)
    seglen_npts = pnts_per_seg(segtime)
    amp = rng + (2.0 * accRange)
    return_npts = pnts_per_seg(returntime)
    offset = start - accRange
    # l.append(gen_wav_table_strs(tblid, seglen_npts, amp, offset, seglen_npts, 0, speedupdown_npnts, wavtype='LIN', _new=True))
    # l.append(gen_wav_table_strs(tblid, return_npts, -1.0*amp, amp+offset, return_npts, 0, return_npts, wavtype='LIN', _new=False))
    l.append(define_seg_by_time(0.1, 0.02, step, 0.0, _new=True, tblid=4))
    l.append(define_seg_by_time(segtime, 0.02, 0.00, step, _new=False, tblid=4))
    rng = pos - start
    return (l)

if __name__ == '__main__':
    import socket
    import sys
    import guidata
    tblid = 3
    x_tbl_id = 3
    y_tbl_id = 4
    dwell = 2.0
    num_points = 100
    #     l = []
    #     l.append(define_seg_by_time(0.1, 0.02, 0.05, 0.0, _new=True, tblid=4))
    #     l.append(define_seg_by_time(0.32, 0.02, 0.00, 0.05, _new=False, tblid=4))
    #
    app = guidata.qapplication()
    # socket_test()
    # s = gen_wav_table_str(tblid, start, stop, dwell, num_points, accRange)
    accRange = 1.5
    # Create a TCP/IP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = '192.168.168.10'
    port = 50000
    # Connect the socket to the port where the server is listening
    server_address = (host, port)
    print('connecting to %s port %s' % server_address, file=sys.stderr)
    sock.connect(server_address)
    try:
        data = sock_send(sock, '*IDN?')
        print('received "%s"' % data, file=sys.stderr)
        # start, stop, step, npoints, dwell, do_clear=False, tbl_id=1)
        start = 0.0
        stop = 5.0
        npoints = 100
        rng = stop - start
        step = rng / npoints
        lst = gen_x_line_wav_strs(start, stop, step, npoints, dwell, do_clear=True, tbl_id=x_tbl_id)
        # WAV 1 X LIN 6400 8 -1.5 6400 0 1200
        # WAV 1 & LIN 1200 -8 6.5 1200 0 400
        for l in lst:
            sock_send(sock, l, do_rcv=False)
            check_for_error(sock)
        start = 5.0
        stop = 10.0
        npoints = 2
        rng = stop - start
        step = rng / npoints
        # ylst = gen_y_step_wav_strs(start, stop, step, npoints, dwell, do_clear=True, tbl_id=y_tbl_id)
        ylst = []
        ylst.append(define_seg_by_time(0.05, 0.005, 0.05, 0.0, _new=True, tblid=4))
        ylst.append(define_seg_by_time(0.32, 0.005, 0.00, 0.05, _new=False, tblid=4))
        for l in ylst:
            sock_send(sock, l, do_rcv=False)
            check_for_error(sock)
        # trig_lst = gen_pxp_line_trig_str(dwell, npoints)
        linetime = line_time(rng, dwell, npoints)
        scanvelo = scan_velo(rng, linetime)
        trig_lst = gen_pxp_line_trig_str(dwell, 1, accRange, scanvelo)
        for l in trig_lst:
            sock_send(sock, l, do_rcv=False)
            check_for_error(sock)
        tbl_data = get_wav_datatbl(sock, x_tbl_id, 8400)
        plot_data(0, tbl_data)
    # s = gen_X_waveform_strs(start, stop, accRange)
    #         for l in s:
    #             print l
    #             sock_send(sock, l, do_rcv=False)
    #
    finally:
        print('closing socket', file=sys.stderr)
        sock.close()
    app.exec_()

 