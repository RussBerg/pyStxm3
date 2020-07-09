
import numpy as np
def generate_seq_image_map():
    '''
    create a map :
    <seq num> : <img num>, <row>, <column>
    :return:
    '''
    setpoints = []
    ev_npts_stpts_lst = []
    e_rois = [{'SETPOINTS': [1,2,3]},
               {'SETPOINTS': [4,5,6,7,8]},
               {'SETPOINTS': [9,11,22,33,44,55,66,77]}
               ]
    for i in range(len(e_rois)):
        num_e_rois = len(e_rois)
        e_roi = e_rois[i]
        #xpnts = self.x_roi[NPOINTS]
        xpnts = 10
        #enpts = int(e_roi[NPOINTS])
        enpts = int(len(e_roi['SETPOINTS']))
        stpts = e_roi['SETPOINTS']
        # create a list entry of (npts, start, stop)
        ev_npts_stpts_lst.append((enpts, stpts[0], stpts[-1]))
        setpoints += list(stpts)
        # self.lineByLineImageDataWidget.initData(i, image_types.LINE_PLOT, xpnts, enpts)
        # self.lineByLineImageDataWidget.set_image_parameters(i, stpts[0], 0, stpts[-1], xpnts)

    # self.lineByLineImageDataWidget.set_autoscale(fill_plot_window=True)
    # self.lineByLineImageDataWidget.set_fill_plot_window(True)
    # dct = self.lineByLineImageDataWidget.determine_num_images(ev_npts_stpts_lst, xpnts)
    dct = determine_num_images(ev_npts_stpts_lst, xpnts)
    # self.executingScan.linescan_seq_map_dct = dct
    linescan_seq_map_dct = dct
    return(dct)

def determine_num_images(ev_npts_stpts_lst, num_spatial_pnts):
    '''
    looking at the setpoints, determine how many images will be required dividing between the delta boundaries
    between the setpoints.
    ex: 3 images for the setpoints
        [1,2,3,4,5,10,15,20,25,30,31,32,33]
        [  first  |   second     |  third ]
    :return:
    '''
    dct = {}
    num_images = len(ev_npts_stpts_lst)
    img_idx = 0
    l = []
    indiv_col_idx = []
    dct['num_images'] = num_images
    dct['map'] = {}
    dct['srtstop'] = {}
    ttl_npts = 0
    for npts, strt, stp in ev_npts_stpts_lst:
        # ttl_npts += npts
        ttl_npts += npts * num_spatial_pnts
        # arr = np.ones(npts, dtype=int)
        arr = np.ones(npts * num_spatial_pnts, dtype=int)
        arr *= img_idx
        l = l + list(arr)
        # indiv_col_idx = indiv_col_idx + list(range(0, npts))
        indiv_col_idx = indiv_col_idx + list(range(0, npts))
        dct['srtstop'][img_idx] = (strt, stp)
        img_idx += 1

    seq = np.array(list(range(0, ttl_npts)))
    dct['col_idxs'] = indiv_col_idx
    map_tpl = list(zip(seq, l))
    for i, img_idx in map_tpl:
        dct['map'][i] = img_idx

    # print(dct)
    return(dct)



def get_sequence_nums(first_num, ttl_pnts):
    return(list(range(first_num, first_num + ttl_pnts)))

def get_rows(row_lst, npnts):
    return(np.tile(row_lst, npnts))

def get_columns(col_lst, npnts):
    lst = list(range(0, len(col_lst)))
    return(np.repeat(lst,  npnts))

def get_ttl_num_pnts(erois):
    ttl = 0
    for eroi in erois:
        ttl += len(eroi)
    return(ttl)


def do_gen(erois, nxpnts):
    dct = {}
    ev_idx = 0
    seq_num = 0
    for eroi in erois:
        # col_lst = [[0,1,2], [3,4,5,6,7,8], [11,22,33,44,55,66,77,88,99]]
        ev_lst = [eroi]
        row_lst = list(range(0, nxpnts))
        ttl_ev_npnts = get_ttl_num_pnts(ev_lst)

        seq = get_sequence_nums(seq_num, ttl_ev_npnts * nxpnts)
        seq_num = seq_num + seq[-1] + 1
        rows = get_rows(row_lst, len(ev_lst[0]))
        cols = get_columns(eroi, nxpnts)

        ev_idx_arr = np.ones(len(seq)) * ev_idx

        # print('Seq ', seq)
        # print('Rows', rows)
        # print('colm', cols)
        ttl = zip(seq, ev_idx_arr, rows, cols)
        for s, img_idx, r, c in ttl:
            #print('(%d, %d, %d, %d)' % (s, img_idx, r, c))
            dct[s] = {'img_num': img_idx, 'row': r, 'col': c}

        ev_idx += 1
    return(dct)

def generate_2d_seq_image_map(energies, nypnts, nxpnts, lxl=False):
    '''
        used primarily by Linespec scans that can have multiple images per scan where each image represents a
        different energy range and resolution
    :param energies: num energies
    :param nypnts: num rows
    :param nxpnts: num columns
    :param lxl: generate map for a line by line scan where each num in sequence is a row,
        if False then Point by Point scan where each num in sequence is a pixel
    :return:
    '''
    dct = {}
    seq_num = 0
    for ev_idx in list(range(0,energies)):
        row_lst = list(range(0, nypnts))
        col_lst = list(range(0, nxpnts))

        if(not lxl):
            seq = get_sequence_nums(seq_num, nypnts * nxpnts)
            seq_num = seq[-1] + 1
            rows = np.repeat(row_lst, nxpnts)
            cols = np.tile(col_lst, nypnts)
            ev_idx_arr = np.ones(len(seq)) * ev_idx
        else:
            seq = get_sequence_nums(seq_num, nypnts)
            seq_num = seq[-1] + 1
            rows = row_lst
            cols = np.zeros(nypnts)
            ev_idx_arr = np.ones(len(seq)) * ev_idx

        ttl = zip(seq, ev_idx_arr, rows, cols)
        for s, img_idx, r, c in ttl:
            # print('(%d, %d, %d, %d)' % (s, img_idx, r, c))
            dct[s] = {'img_num': int(img_idx), 'row': r, 'col': c}

        ev_idx += 1
    return (dct)

if __name__ == '__main__':
    import pprint
    #dct = generate_seq_image_map()
    #pprint.pprint(dct)

    # ev_idx = 0
    # npnts = 10
    # erois = [[50,451,342], [3,4,5,6,7,8], [11,22,33,44,55,66,77,88,99]]
    #
    # dct = do_gen(erois, npnts)
    # pprint.pprint(dct)

    dct = generate_2d_seq_image_map(3, 7, 5, lxl=False)
    pprint.pprint(dct)