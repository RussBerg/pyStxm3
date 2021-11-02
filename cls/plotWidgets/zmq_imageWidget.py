


import numpy as np

from guiqwt.interfaces import ICSImageItemType,IShapeItemType

from guidata.dataset.dataitems import StringItem
from guidata.dataset.datatypes import DataSet
from guiqwt.plot import ImageDialog
from guiqwt.builder import make
from guiqwt.image import ImageItem
from guiqwt.styles import ImageParam, ImageAxesParam


from cls.utils.log import get_module_logger
from cls.utils.roi_dict_defs import EV_SCAN_EDGE_RANGE

# from guiqwt.styles import (update_style_attr, CurveParam, ErrorBarParam,
#                            style_generator, LabelParam, LegendParam, ImageParam,
#                            TrImageParam, HistogramParam, Histogram2DParam,
#                            RGBImageParam, MaskedImageParam, XYImageParam,
#                            ImageFilterParam, MARKERS, COLORS, GridParam,
#                            LineStyleParam, AnnotationParam, QuadGridParam,
#                            LabelParamWithContents, MarkerParam)

from guiqwt.styles import LineStyleParam

_logger = get_module_logger(__name__)


class ZMQImageWidget(ImageDialog):

    def __init__(self, options=None):
        # gridparam = make.gridparam(background="#000000",
        #                                 minor_enabled=(False, False),
        #                                 major_enabled=(True, True),
        #                            major_style=('DotLine', '#6b6b6b', 0.5),
        #                             minor_style=('DotLine', '#6b6b6b', 0.5))
        if(options is None):
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
                gridparam=None,
                colormap="gist_gray")

        super(ZMQImageWidget, self).__init__(wintitle="", toolbar=True, edit=False,
                                             options=options)
        # item = make.image(data)
        self.plot = self.get_plot()
        #the key for data is an index value
        self.data = {}
        self.item = {}

        self.image_is_new = True
        self._auto_contrast = True
        self.plot.set_axis_direction('left', False)

    def replot(self):
        plot = self.get_plot()
        plot.replot()

    def show_data(self, img_idx, data, init=False, ):
        """
        show_data(): description

        :param data: data description
        :type data: data type

        :param init=False: init=False description
        :type init=False: init=False type

        :returns: None
        """

        if(data[img_idx].size is 0):
            return
        plot = self.get_plot()
        items = len(self.plot.get_items(item_type=ICSImageItemType))
        if(self.item[img_idx] is None):
            self.item[img_idx] = make.image(
                self.data[img_idx],
                interpolation='nearest',
                colormap='gist_gray')
            plot.add_item(self.item[img_idx], z=items+1)
            #plot.set_plot_limits(0.0, 740.0, 0.0, 800.0)
        else:
            if(self._auto_contrast):
                #self.item[img_idx].set_data(data[img_idx])
                #self.item[img_idx].set_data(data)
                self.item[img_idx].set_data(data[img_idx])
            else:
                lut_range = self.item.get_lut_range()
                self.item[img_idx].set_data(data[img_idx], lut_range)
        plot.replot()

    def initData(self, img_idx, rows, cols, parms={}):
        """
        initData(): description

        :param image_type: image_type description
        :type image_type: image_type type

        :param rows: rows description
        :type rows: rows type

        :param cols: cols description
        :type cols: cols type

        :param parms={}: parms={} description
        :type parms={}: parms={} type

        :returns: None
        """
        # clear title
        # print('ImageWidgetPlot: initData called, rows=%d, cols=%d' % (rows, cols))

        plot = self.get_plot()
        plot.set_title('')
        # clear any shapes
        self.delShapePlotItems()
        # scalars for non-square data
        self.htSc = 1
        self.widthSc = 1
        array = np.empty((int(rows), int(cols)))
        array[:] = np.NAN
        array[0][0] = 0
        self.data[img_idx] = array
        self.wPtr = 0
        self.hPtr = 0
        # self.item = make.image(self.data[img_idx], title='', interpolation='nearest', colormap='gist_gray')
        # plot.add_item(self.item, z=1)
        self.item[img_idx] = make.image(self.data[img_idx], title='', interpolation='nearest', colormap='jet')
        #plot.add_item(self.item[img_idx], z=1)
        plot.add_item(self.item[img_idx])
        # plot.set_plot_limits(0.0, 740.0, 0.0, 800.0)
        self.image_is_new = True
        return (self.data[img_idx].shape)

    def addPoint(self, img_idx, y, x, val, show=False):
        """
        addPoint(): description

        :param y: y description
        :type y: y type

        :param x: x description
        :type x: x type

        :param val: val description
        :type val: val type

        :param show=False: show=False description
        :type show=False: show=False type

        :returns: None
        """
        ''' this function adds a new point to the 2d array
        '''
        # if(not self.dataAtMax):
        if(self.data[img_idx] is not None):
            rows, cols = self.data[img_idx].shape
            if ((y < rows) and (x < cols)):
                # remember this is a 2d array array[row][column] so it is [array[y][x]
                # so that it will display the data from bottom/up left to right
                self.data[img_idx][y, x] = val

            if(show):
                self.show_data(img_idx, self.data)

    def addLine(self, img_idx, row, line, show=False):
        """
        addLine(): description

        :param row: row description
        :type row: row type

        :param line: line description
        :type line: line type

        :param show=False: show=False description
        :type show=False: show=False type

        :returns: None
        """
        ''' this function adds a new line to the 2d array
        '''
        # print 'addLine: row=%d' % row
        # print 'addLine: data length = %d vals' % len(line)
        if((self.image_is_new)):
            self.image_is_new = False
            #if(row != 0):
            #    return
        # this is a catch for a spurious previsou row being sent
        # at the start of a scan, fix this sometime

        # print 'row=%d' % row
        if(self.data[img_idx] is not None):
            rows, cols = self.data[img_idx].shape
            if(cols != len(line)):
                line = np.resize(line, (cols,))

            if(row >= rows):
                row = rows - 1

            #AUG16 self.data[row, :] = copy.deepcopy(line)
            self.data[img_idx][row, :] = line
            if(show):
                #self.show_data(img_idx, self.data)
                self.replot()
        else:
            _logger.error('stxmImageWidget: addLine: self.data is None')

    def addVerticalLine(self, img_idx, col, line, show=False):
        """
        addVerticalLine(): description

        :param col: column description
        :type col: col type

        :param line: line description
        :type line: line type

        :param show=False: show=False description
        :type show=False: show=False type

        :returns: None
        """
        ''' this function adds a new vertical line to the 2d array
        '''
        # print 'addLine: row=%d' % row
        # print 'addLine: data length = %d vals' % len(line)
        if((self.image_is_new)):
            self.image_is_new = False
            if(col != 0):
                return
        # this is a catch for a spurious previsou row being sent
        # at the start of a scan, fix this sometime

        # print 'row=%d' % row
        if(self.data[img_idx] is not None):
            rows, cols = self.data[img_idx].shape
            # if(cols != len(line)):
            #    line = np.resize(line, (cols,))

            if(col >= cols):
                col = cols - 1

            #self.data[:, col] = copy.deepcopy(line)
            self.data[img_idx][:, col] = line[0:rows]
            if(show):
            #     self.show_data(img_idx, self.data[img_idx])
                self.replot()
        else:
            _logger.error(
                'stxmImageWidget: addVerticalLine: self.data[%d] is None' % img_idx)

    def delImagePlotItems(self):
        """
        delImagePlotItems(): description

        :returns: None
        """
        i = 0
        items = self.plot.get_items(item_type=ICSImageItemType)
        for item in items:
            # Don't delete the base image
            # if(item.title().text() != 'Image #1'):
            # print 'deleting %s'  % item.title().text()
            self.plot.del_item(item)
            del item
            self.item[i] = None
            i += 1

        # self.item = None
        self.plot.replot()

    def delShapePlotItems(self):
        """
        delShapePlotItems(): description

        :returns: None
        """
        items = self.plot.get_items(item_type=IShapeItemType)
        for item in items:
            self.delShapePlotItem(item, replot=False)

        self.plot.replot()

    def delShapePlotItem(self, item, replot=True):
        """
        delShapePlotItem(): description

        :returns: None
        """
        dct = self.get_shape_item_types(item)

        if(not isinstance(item, ImageItem)):
            self.plot.del_item(item)
            del item

            if(replot):
                self.plot.replot()

    def set_data(self, img_idx, data):
        """
        set_data(): description

        :param data: data description
        :type data: data type

        :returns: None
        """
        if(data.size is 0):
            return
        self.data[img_idx] = data
        # self.show_data(self.data)
        self.show_data(img_idx, self.data)
        self.set_autoscale()

    def set_autoscale(self, fill_plot_window=False):
        """
        set_autoscale(): description

        :param fill_plot_window=False: fill_plot_window=False description
        :type fill_plot_window=False: fill_plot_window=False type

        :returns: None
        """
        plot = self.get_plot()
        if(fill_plot_window):
            # unlock so that an autoscale will work
            self.set_lock_aspect_ratio(False)
            plot.do_autoscale()
            # lock it again
            self.set_lock_aspect_ratio(True)
        else:
            self.set_lock_aspect_ratio(True)
            plot.do_autoscale()

    def set_lock_aspect_ratio(self, val):
        """
        set_lock_aspect_ratio(): description

        :param val: val description
        :type val: val type

        :returns: None
        """
        self.plot.lock_aspect_ratio = bool(val)

    def set_image_parameters(self, img_idx, x1, y1, x2, y2):
        """
        set_image_parameters(): description

        Use this function to adjust the image parameters such that the x and y axis are
        within the xmin,xmax and ymin,ymax bounds, this is an easy way to display the image
        in microns as per the scan parameters, as well as the fact that if you have a scan with
        a non-square aspect ratio you can still display the scan as a square because the image will
        repeat pixels as necessary in either direction so that the image is displayed in teh min/max
        bounds you set here

        :param imageItem: a image plot item as returned from make.image()
        :type imageItem: a image plot item as returned from make.image()

        :param x1: min x that the image will be displayed
        :type x1: int

        :param y1: max x that the image will be displayed
        :type y1: int

        :param x2: min y that the image will be displayed
        :type x2: int

        :param y2: max y that the image will be displayed
        :type y2: int

        :returns:  None

        .. todo::
        there are man other image params that could be set in teh future, for now only implemented min/max
        ImageParam:
            Image title: Image
            Alpha channel: False
            Global alpha: 1.0
            Colormap: gist_gray
            Interpolation: None (nearest pixel)
            _formats:
              X-Axis: %.1f
              Y-Axis: %.1f
              Z-Axis: %.1f
            Background color: #000000
            _xdata:
              x|min: -
              x|max: -
            _ydata:
              y|min: -
              y|max: -

        """
        if(self.item[0] is None):
            return
        iparam = ImageParam()
        iparam.colormap = self.item[img_idx].get_color_map_name()
        iparam.xmin = x1
        iparam.ymin = y1
        iparam.xmax = x2
        iparam.ymax = y2
        self.zoom_rngx = float(x2 - x1)
        self.zoom_rngy = float(y2 - y1)

        axparam = ImageAxesParam()
        axparam.xmin = x1
        axparam.ymin = y1
        axparam.xmax = x2
        axparam.ymax = y2

        self.item[img_idx].set_item_parameters({"ImageParam": iparam})
        self.item[img_idx].set_item_parameters({"ImageAxesParam": axparam})

    def set_center_at_XY(self, center, rng, zoomout=0.35):
        """
        set_center_at_XY(): description

        :param center: center description
        :type center: center type

        :param rng: rng description
        :type rng: rng type

        :returns: None
        """
        """ given the center and range tuples specified center the plot around center
        """
        (cx, cy) = center
        (rx, ry) = rng

        if(rx == 0.0):
            rx = 50
        if(ry == 0.0):
            ry = 50
        bufferx = zoomout * rx
        buffery = zoomout * ry

        xstart = cx - (0.5 * rx) - bufferx
        xstop = cx + (0.5 * rx) + bufferx

        ystart = cy - (0.5 * ry) - buffery
        ystop = cy + (0.5 * ry) + buffery

        dx = xstop - xstart
        dy = ystop - ystart

        x0, x1, y0, y1 = self.plot.get_plot_limits()

        pdx = x1 - x0
        pdy = y1 - y0

        if(pdx > pdy):
            #scale y
            dy = dy * (pdy/pdx)
            ystart = cy - (0.5 * dy)
            ystop = cy + (0.5 * dy)
        else:
            #scale x
            dx = dx * (pdx / pdy)
            xstart = cx - (0.5 * dx)
            xstop = cx + (0.5 * dx)

        self.plot.set_plot_limits(xstart, xstop, ystart, ystop)

    def determine_num_images(self, num_e_rois, setpoints):
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

        #do any of the deltas == EV_SCAN_EDGE_RANGE for only 1 value? if so this is an ev region boundary and
        # can be removed from the  deltas
        deltas = deltas[deltas > 0.0]
        #deltas = np.where(deltas == 0.2, 0.3, deltas)
        #add an extra delta at the end so that the number of deltas is correct
        l = list(deltas)
        l.append(l[-1])
        deltas = np.array(l)
        #ok now move on
        u, indices = np.unique(deltas.round(decimals=4), return_index=True)
        u, counts = np.unique(deltas.round(decimals=4), return_counts=True)

        #indices.sort()
        num_images = num_e_rois
        z = list(zip(indices, counts))

        i = 0
        for ind, cnt in z:
            if(cnt == (num_e_rois - 1)):
                #remove this pair because it belongs to the ev boundaries
                break
            i += 1
        del(z[i])

        #fix total counts
        i = 0
        l_z = []
        for ind, cnt in z:
            #z[i][1] += 1
            ind, cnt = z[i]
            if(len(l_z) == (num_e_rois - 1)):
                l_z.append((ind, cnt))
            else:
                l_z.append((ind, cnt + 1))
            i += 1

        ind_cnts_sorted_lst = sorted(l_z, key=lambda t: t[0])

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




if __name__ == "__main__":
    import guidata

    _app = guidata.qapplication()
    win = ZMQImageWidget()
    win.show()
    _app.exec_()
