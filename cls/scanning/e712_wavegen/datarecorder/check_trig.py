


import os, sys
import numpy as np
import matplotlib.pyplot as plt


DIGTAL_OUT_COLUMN = 5

def get_gcs_header(lines):
    '''
    # TYPE = 1
    # SEPARATOR = 9
    # DIM = 12
    # SAMPLE_TIME = 0.000200
    # NDATA = 699050
    # NAME0 = Current Position of axis3
    # NAME1 = Current Position of axis2
    # NAME2 = Current Position of axis3
    # NAME3 = Current Position of axis4
    # NAME4 = Value of Digital Output1
    # NAME5 = Current Position of axis6
    # NAME6 = Current Position of axis7
    # NAME7 = Current Position of axis8
    # NAME8 = Current Position of axis9
    # NAME9 = Current Position of axis10
    # NAME10 = Current Position of axis11
    # NAME11 = Current Position of axis12
    # END_HEADER

    read the lines putting the key value paris into a dict until I reach the end of the header

    :param lines:
    :return dict:
    '''
    dct = {}
    idx = 0
    for l in lines:
        idx += 1
        if(l.find('# END_HEADER') > -1):
            break
        l = l.replace('# ','')
        l = l.replace('#', '')
        l = l.replace(' ', '')
        l = l.replace('\n', '')
        if(len(l) > 0):
            l2 = l.split('=')
            dct[l2[0]] = return_value(l2[1])

    return(dct, idx)


def return_value(s):
    '''
    first try returning a float, if that fails try returning an integer, if that fails return it as a string
    :param s:
    :return:
    '''
    try:
        if(s.find('.') > -1):
            return float(s)
        else:
            return int(s)
    except ValueError:
        return(s)

def parse_gcs_datfile(fname):
    lines = get_file_as_lines(fname)
    hdr_dct, data_start_idx = get_gcs_header(lines)


    return(hdr_dct, lines, data_start_idx)



def get_file_as_lines(fname):
    lines = []
    if(os.path.exists(fname)):
        with open(fname) as f:
            ls = f.readlines()
            lines = ls[1:]
    else:
        print('ERROR: file [%s] does not exist' % fname)

    return (lines)


def get_data_columns(lines, num_cols, dat_len, strt_idx, sample_time):
    '''
    -25.084043	95.924285	-25.084043	24.999282	24.000000	0.000000	0.000000	0.000000	0.000000	0.000000	0.000000	0.000000

    :param lines:
    :param num_cols:
    :param dat_len:
    :param strt_idx:
    :return:
    '''
    dats = np.zeros((dat_len, num_cols + 1))

    time_idx = 0
    for l in lines[strt_idx:]:
        l = l.strip('<<')
        dat_cols = l.split()
        col_idx = 0
        for d in dat_cols:
            if(col_idx == DIGTAL_OUT_COLUMN):
                if(d.find('1') == -1):
                    d = 0
                else:
                    d = 5
            dats[time_idx, col_idx] = d
            col_idx += 1
        dats[time_idx, col_idx] = float(sample_time * time_idx)
        time_idx += 1

    col_data = []
    for i in range(col_idx+1):
        col_data.append(dats[:,i])
    return(dats, col_data)

def plot_data(p, x, y):
    p(x, y, label="n=%d" % (len(x),))


if __name__ == '__main__':
    fname = r'C:\controls\git_sandbox\pyStxm\cls\scanning\e712_wavegen\datarecorder\datarecorder-withaccrange.dat'
    hdr_dct, lines, data_start_idx = parse_gcs_datfile(fname)

    data, col_data = get_data_columns(lines, hdr_dct['DIM'], hdr_dct['NDATA'], data_start_idx, hdr_dct['SAMPLE_TIME'])
    for i in range(len(col_data)):
        print(col_data[i])

    x = col_data[DIGTAL_OUT_COLUMN+1]
    y = col_data[DIGTAL_OUT_COLUMN]
    plot_data(plt.plot, x, y)

    y = col_data[0]
    plot_data(plt.plot, x, y)
    y = col_data[1]
    plot_data(plt.plot, x, y)
    y = col_data[2]
    plot_data(plt.plot, x, y)
    y = col_data[3]
    plot_data(plt.plot, x, y)



    plt.show()

