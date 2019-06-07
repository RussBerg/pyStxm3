




POINT_TIME = 0.00005


def scan_velo(rng, linetime):
    if (rng is 0.0):
        velo = 10000
    else:
        velo = rng / linetime
    return (velo)


def calc_trig_start_time(scanvelo, acc_rng=1.0, line_updwn=0.005, line_delay=0.02):
    acc_time = float(scanvelo/acc_rng) + line_updwn + line_delay
    print('time to reach where trig should match %.2f um is %.5f sec' % (acc_rng, acc_time))
    return(acc_time)


def calc_acc_dist(amp, speedupdwn, seg_time):
    '''
        seg_time=180e-3
        speed_up_down=15e-3
        amplitude=32e-6
        acc_dist=amplitude*speed_up_down/(2*(seg_time-speed_up_down))
        print(acc_dist)
        1.4545454545454546e-06
        => the plot in the PI software showed 1.45um (which I guess is rounded)

        curve_lengts=150e-3
        speed_up_down=5e-3
        amplitude=32e-6
        acc_dist=amplitude*speed_up_down/(2*(curve_lengts-speed_up_down))
        print(acc_dist)
        5.517241379310345e-07

    :param amp:
    :param speedupdwn:
    :param seg_time:
    :return:
    '''
    #amp = amp + (2 * desired_acc_rng)
    acc_dist = amp*speedupdwn/(2*(seg_time-speedupdwn))
    return(acc_dist)



if __name__ == '__main__':
    #desired_acc_rng = 1.0
    rng = 30.0
    amplitude = rng
    num_pts = 150
    dwell = 0.001
    speedupdwn = 0.005
    seg_time = num_pts * dwell

    scanvelo = scan_velo(rng, seg_time)
    #trig_time = calc_trig_start_time(scanvelo)

    acc_dist = calc_acc_dist(rng, speedupdwn, seg_time)
    print('actual acc_distance is = %.4f' % (acc_dist))

    #acc_dist = amplitude * speedupdwn / (2 * (seg_time - speedupdwn))
    #print('%.4f um' % acc_dist)