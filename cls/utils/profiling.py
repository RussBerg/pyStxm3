
import profile
import pstats


def determine_profile_bias_val():
    """
        determine_profile_bias_val(): description

        :param determine_profile_bias_val(: determine_profile_bias_val( description
        :type determine_profile_bias_val(: determine_profile_bias_val( type

        :returns: None
    """
    pr = profile.Profile()
    v = 0
    v_t = 0
    for i in range(5):
        v_t = pr.calibrate(100000)
        v += v_t
        print(v_t)

    bval = v / 5.0
    print('bias val = ', bval)
    profile.Profile.bias = bval
    return bval

def profile_it(func_name, bias_val=None):
    """
        profile_it(): description

        :param profile_it(: profile_it( description
        :type profile_it(: profile_it( type

        :returns: None
    """

    # determine_profile_bias_val()

    if(bias_val is None):
        profile.Profile.bias = determine_profile_bias_val()
    else:
        profile.Profile.bias = 6.76801200295e-07

    profile.run('%s()' % func_name, 'testprof.dat')

    p = pstats.Stats('testprof.dat')
    p.sort_stats('cumulative').print_stats(100)


def go():
    import time

    for i in range(1,200):
        x = (5*999/i+50)*0.00001233
        time.sleep(0.01)


if __name__ == '__main__':

    profile_it('go', bias_val=7.40181638985e-07)