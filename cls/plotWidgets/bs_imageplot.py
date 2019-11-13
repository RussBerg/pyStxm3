#!/home/bergr/.conda/envs/cls_bsky/bin/python

from PyQt5 import QtWidgets

import numpy as np

from guiqwt.builder import make

from cls.plotWidgets.zmq_imageWidget import ZMQImageWidget
from cls.utils.doc_utils import dump_args, get_detectors, get_positioners, get_num_points, get_datakeys, get_det_shape_from_md, \
                                     get_positioner_setpoints

class ImgPlotWindow(QtWidgets.QWidget):

    def __init__(self, isolate_curve_nm=None, lines_as_horiz=True):
        super(ImgPlotWindow, self).__init__()
        self.setMinimumWidth(100)
        self.setMinimumHeight(100)
        self.md = {}
        self._xdata = None

        #a flag to say if we want lines plotted horizontally or vertically
        self.lines_as_horiz = lines_as_horiz
        self.isolate_curve_nm = isolate_curve_nm
        #if (len(self.isolate_curve_nm) > -1):
        if (self.isolate_curve_nm is not None):
            self.isolate_curve = True
        else:
            self.isolate_curve = False

        self.image_names = []

        gridparam = make.gridparam(background="#727272",
                                   minor_enabled=(False, False),
                                   major_enabled=(True, True),
                                   major_style=('DotLine', '#6b6b6b', 0.5),
                                   minor_style=('DotLine', '#6b6b6b', 0.5))
        options = dict(
            show_xsection=False,
            show_ysection=False,
            xlabel=("um", ""),
            ylabel=("um", ""),
            zlabel=None,
            show_contrast=True,
            xsection_pos="top",
            ysection_pos="right",
            lock_aspect_ratio=False,
            gridparam=gridparam,
            colormap="gist_gray")

        self.plot = ZMQImageWidget(options=options)
        #self.plot.add_legend("TL")
        # self.plot.plot_widget.itemlist.setVisible(True)
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.plot)
        self.setLayout(vbox)
        self._data_valid = True

    def is_valid_image_det(self, det_name):
        data_dim = len(get_det_shape_from_md(self.md, det_name))
        if (data_dim in [1, 2]):
            return (True)
        else:
            return (False)

    def get_data_points(self, doc, datakeys=[]):
        data = {}
        seq_num = doc['seq_num']
        data[seq_num] = []
        if (self.isolate_curve and (self.isolate_curve_nm in datakeys)):
            k = self.isolate_curve_nm
            data[seq_num].append(
                {'det_name': k.replace('_val', ''), 'value': np.array(doc['data'][k]), 'timestamp': doc['timestamps'][k]})
            return (data)
        else:
            for det in datakeys:
                # print('get_data_points: [%s]' % k)
                if (self.is_valid_image_det(det)):
                    data[seq_num].append({'det_name': det.replace('_val', ''), 'value': np.array(doc['data'][det]),
                                          'timestamp': doc['timestamps'][det]})
            return (data)

    def closeEvent(self, ao):
        exit()

    # def init_image(self, doc):
    #     remove_lst = []
    #     self.image_names = doc['detectors']
    #     if (self.isolate_curve and (self.isolate_curve_nm in self.image_names)):
    #         self.image_names = [self.isolate_curve_nm]
    #         self.setWindowTitle(self.isolate_curve_nm)
    #
    #     self.plot.delImagePlotItems()
    #     for det in self.image_names:
    #         if (self.is_valid_image_det(det)):
    #             # print('init_image: creating curve [%s]' % det)
    #             #self.plot.create_curve('%s' % det, curve_style=style)
    #             shape = get_det_shape_from_md(doc['md'], det)
    #             self.setWindowTitle(det)
    #
    #             if(len(shape) == 1):
    #                 stpts = self.setpoints[0]
    #                 #stpts = self.setpoints
    #                 parms = {'RECT': (stpts[0], stpts[-1], stpts[-1], stpts[0])}
    #                 centers = ((stpts[0] + stpts[-1]) * 0.5, (stpts[0] + stpts[-1]) * 0.5)
    #                 rng = abs(stpts[0] - stpts[-1])
    #                 rng = rng + (rng * 0.25)
    #
    #                 if(self.lines_as_horiz):
    #                     self.plot.initData(self.npts, shape[0])
    #                     # set_image_parameters(x1, y1, x2, y2)
    #                     self.plot.set_image_parameters(stpts[0], stpts[-1], stpts[-1], stpts[0])
    #                     #centers = (self.npts*0.5, shape[0]*0.5)
    #                     #self.plot.set_center_at_XY(centers, (rng, rng))
    #                     #set_plot_limits(x0, x1, y0, y1)
    #
    #                     #self.plot.plot.set_plot_limits(stpts[0], stpts[-1], stpts[0], stpts[-1])
    #                 else:
    #                     #centers = (shape[0] *0.5, self.npts *0.5)
    #                     self.plot.initData(shape[0], self.npts)
    #                     # set_image_parameters(x1, y1, x2, y2)
    #                     self.plot.set_image_parameters(stpts[0],  stpts[-1], stpts[-1], stpts[0])
    #                     #self.plot.set_center_at_XY(centers, (500, 500))
    #                     #self.plot.plot.set_plot_limits(stpts[0], stpts[-1], stpts[0], stpts[-1])
    #             else:
    #                 stpts = self.setpoints
    #                 self.plot.initData(shape[0], shape[1])
    #                 #set_image_parameters(x1, y1, x2, y2)
    #                 self.plot.set_image_parameters(stpts[0], stpts[-1], stpts[-1], stpts[0])
    #                 #self.plot.set_center_at_XY(centers, (500, 500))
    #                 #self.plot.plot.set_plot_limits(stpts[0], stpts[-1], stpts[0], stpts[-1])
    #
    #             self.plot.set_center_at_XY(centers, (rng, rng))
    #
    #         else:
    #             remove_lst.append(det)
    #     # remove detectors that are delivering invalid data
    #     for rem_det in remove_lst:
    #         self.image_names.remove(rem_det)

    def init_image(self, doc):
        '''
        initialize an image or images depending
        :param doc:
        :return:
        '''
        remove_lst = []
        self.image_names = doc['detectors']
        if (self.isolate_curve and (self.isolate_curve_nm in self.image_names)):
            self.image_names = [self.isolate_curve_nm]
            self.setWindowTitle(self.isolate_curve_nm)

        self.plot.delImagePlotItems()
        minplot = None
        maxplot = None
        for det in self.image_names:
            if (self.is_valid_image_det(det)):
                shape = get_det_shape_from_md(doc['md'], det)
                self.setWindowTitle(det)
                if(len(shape) == 1):
                    num_line_pts = shape[0]
                    stpts = self.setpoints
                    #init if not already
                    if(minplot is None):
                        minplot = stpts[0]
                    if (maxplot is None):
                        maxplot = stpts[-1]
                    #set to find min and max
                    if (stpts[0] < minplot):
                        minplot = stpts[0]
                    if (stpts[-1] > maxplot):
                        maxplot = stpts[-1]

                    if(self.lines_as_horiz):
                        for i in range(self.image_dct['num_images']):
                            npts = self.image_dct['img_to_idx_counts'][i][1]
                            self.plot.initData(i, npts, shape[0])
                            stpts = self.image_dct['srtstop'][i]
                            #img_idx, x1, y1, x2, y2
                            #self.plot.set_image_parameters(i, stpts[0], 0, stpts[-1], num_line_pts)
                            self.plot.set_image_parameters(i, 0, stpts[0], num_line_pts, stpts[-1])

                    else:
                        for i in range(self.image_dct['num_images']):
                            npts = self.image_dct['img_to_idx_counts'][i][1]
                            self.plot.initData(i, shape[0], npts)
                            stpts = self.image_dct['srtstop'][i]
                            self.plot.set_image_parameters(i, stpts[0], 0, stpts[-1], num_line_pts)

                else:
                    stpts = self.setpoints
                    self.plot.initData(0, shape[0], shape[1])
                    self.plot.set_image_parameters(0, stpts[0], stpts[-1], stpts[-1], stpts[0])

                #self.plot.set_center_at_XY(centers, (rng, rng))
                if (self.lines_as_horiz):
                    if (num_line_pts):
                        rng = maxplot - minplot
                        yc = (minplot + maxplot) * 0.5
                        xc = (0 + num_line_pts) * 0.5
                        self.plot.set_center_at_XY((xc, yc), (rng * 0.15, rng * 0.6))

                else:
                    if(num_line_pts):
                        rng = maxplot - minplot
                        xc = (minplot + maxplot) * 0.5
                        yc = (0 + num_line_pts) * 0.5
                        self.plot.set_center_at_XY((xc, yc), (rng , rng * 0.15))


            else:
                remove_lst.append(det)
        # remove detectors that are delivering invalid data
        for rem_det in remove_lst:
            self.image_names.remove(rem_det)

    def add_data(self, data_dct):
        '''
        data_dct =
            {1: [{'noisy_det': 0.9855252608504612, 'timestamp': 1569433874.0520704}, {'m902': 125.0, 'timestamp': 1569433919.689106}, {'m902_user_setpoint': 125.0, 'timestamp': 1569433919.689106}]}
            ...
        :param data_dct:
        :return:

        '''

        bs_seq_num = list(data_dct.keys())[0]
        _seqnum = bs_seq_num - 1
        img_idx = self.image_dct['map'][_seqnum]

        for _dct in data_dct[bs_seq_num]:
            if (_dct['det_name'] in self.image_names):
                if(_dct['value'].ndim > 1):
                    self.plot.set_data(_dct['value'])
                else:
                    stpts = self.setpoints[0]
                    #if plot seq num is rows
                    if(self.lines_as_horiz ):
                        row = self.image_dct['col_idxs'][_seqnum]
                        #self.plot.addLine(img_idx, self.npts - (row), _dct['value'], show=True)
                        self.plot.addLine(img_idx, row, _dct['value'], show=True)

                    else:
                        #else add vertical line
                        # addVerticalLine(self, img_idx, col, line, show=False):
                        col = self.image_dct['col_idxs'][_seqnum]
                        self.plot.addVerticalLine(img_idx, col, _dct['value'], show=True)


    def create_xdata(self, doc):
        if ('num' in doc['plan_pattern_args'].keys()):
            npoints = doc['plan_pattern_args']['num']
            start = doc['plan_pattern_args']['args'][1]
            stop = doc['plan_pattern_args']['args'][2]
        else:
            npoints = len(doc['plan_pattern_args']['object'])
            start = doc['plan_pattern_args']['object'][1]
            stop = doc['plan_pattern_args']['object'][-1]
        self._xdata = np.linspace(start, stop, npoints)

    def is_valid_data(self, doc):
        res = False
        valid_plan_types_list = ['list_scan', 'scan', 'scan_nd']
        if(doc['plan_name'] in valid_plan_types_list):
            return (True)
        else:
            return (False)

    def determine_num_images(self, setpoints):
        '''
        looking at the setpoints, determine how many images will be required dividing between the delta boundaries
        between the setpoints.
        ex: 3 images for the setpoints
            [1,2,3,4,5,10,15,20,25,30,31,32,33]
            [  first  |   second     |  third ]
        :return:
        '''
        dct = {}
        deltas = np.diff(np.array(setpoints))
        deltas = deltas[deltas > 0.0]
        #add an extra delta at teh end so that the number of deltas is correct
        l = list(deltas)
        l.append(l[-1])
        deltas = np.array(l)
        #ok now move on
        u, indices = np.unique(deltas.round(decimals=4), return_index=True)
        u, counts = np.unique(deltas.round(decimals=4), return_counts=True)

        #indices.sort()
        num_images = len(u)
        z = list(zip(indices, counts))
        ind_cnts_sorted_lst = sorted(z, key=lambda t: t[0])

        dct['img_to_idx_map'] = indices
        dct['img_to_idx_counts'] = ind_cnts_sorted_lst
        dct['num_images'] = num_images
        dct['map'] = {}
        dct['srtstop'] = {}
        seq = np.array(list(range(0, len(setpoints) )))
        img_idx = 0
        l = []
        indiv_col_idx = []
        for strt, num in ind_cnts_sorted_lst:
            #dct['map'].append((setpoints[strt], setpoints[num], np.linspace(setpoints[strt], setpoints[num], num)))
            #arr = np.array(list(range(ind_cnts_sorted_lst[img_idx][0], ind_cnts_sorted_lst[img_idx][1])))
            arr = np.ones(ind_cnts_sorted_lst[img_idx][1], dtype=int)
            arr *= img_idx
            l = l + list(arr)
            if(strt > 0):
                indiv_setpoints = setpoints[strt - 1: strt+num]

            else:
                indiv_setpoints = setpoints[strt: strt + num]

            indiv_col_idx = indiv_col_idx + list(range(0, num))
            dct['srtstop'][img_idx] = (indiv_setpoints[0], indiv_setpoints[-1])
            img_idx += 1

        #dct['col_idxs'] = list(zip(seq, indiv_col_idx))
        dct['col_idxs'] = indiv_col_idx
        map_tpl = list(zip(seq, l))
        for i, img_idx in map_tpl:
            dct['map'][i] = img_idx

        return(dct)



    def doc_callback(self, *args, **dud):
        '''
        :param args:
        :param kwargs:
        :return:
        '''
        name, doc = args
        # print(doc)

        if (name.find('start') > -1):
            #self.md = doc['md']
            self._data_valid = True
            if (self.is_valid_data(doc)):
                self.posners = get_positioners(doc)
                self.setpoints = get_positioner_setpoints(doc, len(self.posners))
                self.image_dct = self.determine_num_images(self.setpoints)
                self.npts = get_num_points(doc)
                self.create_xdata(doc)
                self.init_image(doc)

            else:
                self._data_valid = False

        # elif (name.find('descriptor') > -1):
        #
        #
        elif (name.find('event') > -1):
            if (self._data_valid):
                datakeys = get_datakeys(doc)
                data = self.get_data_points(doc, datakeys)
                # print(data)
                self.add_data(data)
            else:
                # ignore invalid data
                pass



if __name__ == "__main__":

    import argparse
    from PyQt5 import QtWidgets
    from bluesky.utils import install_qt_kicker
    from bluesky.callbacks.zmq import RemoteDispatcher
    from cls_bsky.utils.args_utils import str2bool

    parser = argparse.ArgumentParser(description='Start a 2D plotter.')

    parser.add_argument('-l', '--lines_as_horiz', metavar='False', type=str2bool,
                        default=False,
                        help='if signal is a line plot it horizontally or vertically')
    parser.add_argument('-c', '--curve_name', metavar='signal_name', type=str,
                        help='the name of a detector signal in data stream')
    args = parser.parse_args()

    app = QtWidgets.QApplication([])

    win = ImgPlotWindow(isolate_curve_nm=args.curve_name, lines_as_horiz=args.lines_as_horiz)

    d = RemoteDispatcher('localhost:5578')
    d.subscribe(win.doc_callback)
    install_qt_kicker(loop=d.loop)

    win.show()
    #starts the event loop for asnycio as well as it will call processEvents() for Qt
    d.start()



