'''
Created on Oct 10, 2019

@author: bergr
'''

from guiqwt.plot import CurveDialog
from guiqwt.builder import make

from guiqwt.styles import COLORS

from cls_bsky.plotters.curve_object import curve_Obj

color_list = {}
clr_keys = list(COLORS.keys())
# move red to the last color from being the first
del (clr_keys[0])
clr_keys.append("r")
for k in clr_keys:
    color_list[k] = {}
    color_list[k]['clr'] = COLORS[k]
    color_list[k]['used'] = False
# don't use black
color_list['k']['used'] = True


def get_next_color(use_dflt=True):
    global color_list
    #    clr_keys = color_list.keys()
    # clr_str='blue'
    clr_str = '#6063ff'
    if (use_dflt):
        # clr_str='blue'
        clr_str = '#6063ff'
    else:
        # print 'get_next_color: clr_idx = %d' % color_idx
        for k in list(color_list.keys()):
            if (color_list[k]['used'] == False):
                clr_str = color_list[k]['clr']
                color_list[k]['used'] = True
                break
    return (clr_str)

def reset_color_idx():
    global color_list
    for k in list(color_list.keys()):
        color_list[k]['used'] = False
    #don't use black
    color_list['k']['used'] = True


def get_basic_line_style(color, marker='NoSymbol', width=1.0, alpha=0.0):
    dct = {}

    #   refer to CurveParam in guiqwt.styles
    dct['line'] = {}
    dct['line']['style'] = 'SolidLine'
    dct['line']['color'] = color
    dct['line']['width'] = width

    dct['symbol'] = {}
    dct['symbol']['size'] = 7
    dct['symbol']['alpha'] = alpha
    dct['symbol']['edgecolor'] = color
    dct['symbol']['facecolor'] = color
    # dct['symbol']['marker'] = 'Diamond'
    # dct['symbol']['marker'] = 'NoSymbol'
    # dct['symbol']['marker'] = 'Star1'
    dct['symbol']['marker'] = marker

    dct['curvestyle'] = 'Lines'
    dct['curvetype'] = 'Yfx'

    dct['shade'] = 0.00
    dct['fitted'] = False
    dct['baseline'] = 0.0

    return (dct)


class ZMQCurveViewerWidget(CurveDialog):
    # save_file = QtCore.pyqtSignal(object)
    # right_mouse_click = QtCore.pyqtSignal(object)
    # dropped = QtCore.pyqtSignal(QtCore.QMimeData)

    def __init__(self, winTitleStr="Plot Viewer",
                 toolbar=False,
                 type='basic',
                 filtStr="*.hdf5",
                 options={},
                 parent=None):
        if ('gridparam' not in list(options.keys())):
            # then use a default one
            options['gridparam'] = gridparam = make.gridparam(background="#afafaf",
                                                              minor_enabled=(False, False),
                                                              major_enabled=(True, True))
            options['gridparam']._min_line.width = 0.35
            options['gridparam']._maj_line.width = 0.35
            options['gridparam']._min_line.color = '#414141'
            options['gridparam']._maj_line.color = '#414141'

        self.parent = parent
        CurveDialog.__init__(self, edit=False, toolbar=toolbar, wintitle=winTitleStr,
                             # options=dict(title="", xlabel="xlabel", ylabel="ylabel"))
                             options=options, parent=parent)

        self.curve_objs = {}
        self._plot_items = []
        self.autoscale_enabled = True

    def add_legend(self, location="TL"):
        """
        options for location are (from guiqwt/styles.py):
            "TL"  = Top left
            "TR" = Top right
            "BL" = Bottom left
            "BR" = Bottom right
            "L" = Left
            "R" = Right
            "T" = Top
            "B" = Bottom
            "C" = Center

        """
        options = ['TL', 'TR', 'BL', 'BR', 'L', 'R', 'T', 'B', 'C']
        if (location not in options):
            #_logger.error('location [%s] is not valid' % location)
            return
        legend = make.legend(location)
        self._addItems(legend)

    def _addItems(self, *items):
        plot = self.get_plot()
        for item in items:
            plot.add_item(item)
            self._plot_items.append(item)

    def clear_plot(self):
        reset_color_idx()
        for item in self._plot_items:
            self.delPlotItem(item, replot=True)

        self.set_autoscale()

    def addXYPoint(self,curve_name, xpoint, point, update=False):
        #print 'cureviewer: addXYPoint: %s, x=%d, point=%d' % (curve_name, xpoint, point)
        self.curve_objs[curve_name].add_xy_point(xpoint, point, update)
        if(update):
            self.set_autoscale()

    def setXYData(self, curve_name, x, y, update=False):
        self.curve_objs[curve_name].setXYData(x, y)
        if(update):
            self.set_autoscale()

    def set_autoscale(self):
        plot = self.get_plot()
        if(self.autoscale_enabled):
            plot.do_autoscale(replot=True)
        #else:
        #    plot.do_autoscale(replot=False)

    def create_curve(self, curve_name, x=None, y=None, curve_style=None):
        if (y is None):
            num_points = 0
        else:
            num_points = len(y)

        if (curve_style is None):
            curve_style = get_basic_line_style(get_next_color(use_dflt=False))

        self.curve_objs[curve_name] = curve_Obj(curve_name, x, y, num_points=num_points, curve_style=curve_style)
        self.curve_objs[curve_name].changed.connect(self.update_curve)
        self._addItems(self.curve_objs[curve_name].curve_item)

    def delPlotItem(self, item, replot=True):
        #Don't delete the legend
        plot = self.get_plot()
        try:
            #print 'item: %s'  % item.title().text()
            if(item.title().text() != 'Legend'):
                #print 'deleting %s'  % item.title().text()
                plot.del_item(item)
                if(replot):
                    plot.replot()
        except:
            pass

    def update_curve(self):
        plot = self.get_plot()
        plot.replot()

if __name__ == "__main__":
    import guidata

    _app = guidata.qapplication()
    win = ZMQCurveViewerWidget()
    win.show()
    win.exec_()

