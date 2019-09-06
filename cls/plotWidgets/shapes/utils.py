
from PyQt5 import QtWidgets
from cls.plotWidgets.CLSPlotItemBuilder import clsPlotItemBuilder
from cls.utils.save_settings import SaveSettings
from cls.app_data.defaults import rgb_as_hex, master_colors, get_style
from cls.plotWidgets.stxm_osa_dflt_settings import make_dflt_stxm_osa_smplholder_settings_dct

make = clsPlotItemBuilder()

import os
from cls.utils.dict_utils import dct_put
curDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '/')

MIN_SHAPE_Z = 1001

shape_cntr = MIN_SHAPE_Z
# def make_dflt_stxm_osa_smplholder_settings_dct(fpath):
# 	dct = {}
# 	dct_put(dct, "OSA.CENTER", (0,0))
# 	dct_put(dct, "OSA.RECT", (-1250,500,1250,-5500))
# 	dct_put(dct, "OSA_AMBIENT.CENTER", ( -1247.7022682879685, -1595.9402372900463))
# 	dct_put(dct, "OSA_AMBIENT.RECT", (-2497.7022682879715, 1404.0597627099448, 2.2977317120344196, -4595.9402372900377))
# 	dct_put(dct, "OSA_CRYO.CENTER", ( -1187.5421670895232, -1000.5925262721269 ))
# 	dct_put(dct, "OSA_CRYO.RECT", ( -4187.5421670895175, 249.5951432086572, 1812.457832910471, -2250.780195752911))
# 	dct_put(dct, "SAMPLE_GONI.CENTER", (320.4466858789624, -651.6853932584269 ))
# 	dct_put(dct, "SAMPLE_GONI.RADIUS", 1000)
# 	dct_put(dct, "SAMPLE_GONI.RECT",( -494.5533141210376, -511.68539325842687, 1135.4466858789624, -791.6853932584269))
# 	dct_put(dct, "SAMPLE_STANDARD.CENTER",(-2550.3974645796065, 2707.6956184038504))
# 	dct_put(dct, "SAMPLE_STANDARD.RADIUS", 1000)
# 	dct_put(dct, "SAMPLE_STANDARD.RECT", ( -3365.3974645796065, 2847.6956184038504, -1735.3974645796065, 2567.6956184038504 ))
# 	dct_put(dct, "SMPL_HLDR.CENTER", ( 0, 2500.0 ))
# 	dct_put(dct, "SMPL_HLDR.RADIUS", 1000)
# 	dct_put(dct, "SMPL_HLDR.RECT", (  -7000, 7000, 7000, -2000 ))
# 	dct_put(dct, "fpath", fpath)
# 	return(dct)


# class ShapeUtilsClass(QtWidgets.QObject):
#     """Simple canvas with a sine plot."""
#     def __init__(self, xdata, ydatas, width=5, height=4, dpi=100, axes_bgrnd_color=AXES_BACKGROUND_COLOR):
#         super(ShapeUtilsClass, self).__init__(width=width, height=height, dpi=dpi)


def create_segment(rect, title='None', plot=None, annotated=False, alpha=0.05, l_style='SolidLine', l_clr='#ffff00'):
    '''

    :param rect:
    :param xc:
    :param yc:
    :param title:
    :param plot:
    :return:
    '''
    global shape_cntr
    #def segment(self, x0, y0, x1, y1, title=None):
    if (annotated):
        # annotated_segment(self, x0, y0, x1, y1, title=None, subtitle=None
        r = make.annotated_segment(rect[0], rect[1], rect[2], rect[3], title=title, subtitle=None)
        sh = r.shape.shapeparam
    else:
        r = make.segment(rect[0], rect[1], rect[2], rect[3], title=title)
        sh = r.shapeparam

    r.set_resizable(False)
    sh._title = title
    sh.fill.alpha = alpha
    sh.sel_fill.alpha = alpha
    sh.symbol.alpha = alpha
    sh.sel_symbol.alpha = alpha
    sh.line._style = l_style
    sh.line._color = l_clr

    sh.symbol.marker = 'NoSymbol'
    sh.sel_symbol.marker = 'NoSymbol'

    r.set_item_parameters({"ShapeParam": sh})

    # self.plot.add_item(r, z=999999999)
    #z = 999999999
    shape_cntr += 1
    z = shape_cntr
    if (plot):
        plot.add_item(r, z)
    return (r, z)

def create_rect_centerd_at(rect, xc, yc, title, plot=None):
    '''
    self explanatory
    :param rect:
    :param xc:
    :param yc:
    :param title:
    :return:
    '''

    dx = (rect[2] - rect[0]) * 0.5
    dy = (rect[1] - rect[3]) * 0.5
    r, z = create_rectangle((xc - dx, yc + dy , xc + dx, yc - dy), title=title)
    #z = 999999999

    if(plot):
        plot.add_item(r, z)

    return(r, z)


def create_rectangle(rect, title='None', plot=None, annotated=False, alpha=0.2, l_style='SolidLine', l_clr='#55ff7f'):
    '''
    self explanatory
    :param rect:
    :param title:
    :return:
    '''
    global shape_cntr
    if(annotated):
        r = make.annotated_rectangle(rect[0], rect[1], rect[2], rect[3], title=title)
        sh = r.shape.shapeparam
    else:
        r = make.rectangle(rect[0], rect[1], rect[2], rect[3], title=title)
        sh = r.shapeparam

    r.set_resizable(False)
    sh._title = title
    #sh.fill.alpha = alpha
    sh.fill.alpha = 0.2
    sh.fill.color = l_clr
    sh.sel_fill.alpha = alpha
    sh.sel_fill.color = l_clr
    sh.symbol.alpha = alpha
    sh.sel_symbol.alpha = alpha
    sh.line._style = l_style
    sh.line._color = l_clr

    sh.symbol.marker = 'NoSymbol'
    sh.sel_symbol.marker = 'NoSymbol'

    r.set_item_parameters({"ShapeParam": sh})
    #z = None
    shape_cntr += 1
    z = shape_cntr
    if (plot):
        plot.add_item(r, z)
    return (r, z)

def create_simple_circle(xc, yc, rad, title='None', clr=None, fill_alpha=0.05, plot=None):
    """
    create_simple_circle(): description

    :param xc: xc description
    :type xc: xc type

    :param yc: yc description
    :type yc: yc type

    :param rad: rad description
    :type rad: rad type

    :returns: None
    """
    global shape_cntr
    from guiqwt.styles import ShapeParam
    #circ = make.annotated_circle(x0, y0, x1, y1, ratio, title, subtitle)
    #rad = val/2.0
    circ = make.circle(xc, yc + rad, xc, yc - rad, title=title)
    circ.set_resizable(False)
    sh = circ.shapeparam
    sh._title = title
    if(clr is not None):
        sh.sel_fill.color = clr
        sh.fill.color = clr

    sh.fill.alpha = fill_alpha
    sh.sel_fill.alpha = fill_alpha
    sh.symbol.alpha = fill_alpha
    sh.sel_symbol.alpha = fill_alpha
    sh.symbol.marker = 'NoSymbol'
    sh.sel_symbol.marker = 'NoSymbol'

#         shape.shapeparam
#         Shape:
#             _styles:
#               _ShapeParam___line:
#                 LineStyleParam:
#                   Style: Solid line
#                   Color: black
#                   Width: 1.0
#                 LineStyleParam:
#                   Style: Solid line
#                   Color: black
#                   Width: 1.0
#               _ShapeParam___sym:
#                 SymbolParam:
#                   Style: No symbol
#                   Size: 9
#                   Border: gray
#                   Background color: yellow
#                   Background alpha: 1.0
#                 SymbolParam:
#                   Style: No symbol
#                   Size: 9
#                   Border: gray
#                   Background color: yellow
#                   Background alpha: 1.0
#               _ShapeParam___fill:
#                 BrushStyleParam:
#                   Style: Uniform color
#                   Color: black
#                   Alpha: 1.0
#                   Angle: 0.0
#                   sx: 1.0
#                   sy: 1.0
#                 BrushStyleParam:
#                   Style: Uniform color
#                   Color: black
#                   Alpha: 1.0
#                   Angle: 0.0
#                   sx: 1.0
#                   sy: 1.0
#             : False
#             : False

    # circ.set_resizable(False)
    # offset teh annotation so that it is not on the center
    #circ.shape.shapeparam.fill = circ.shape.shapeparam.sel_fill
    #circ.shape.shapeparam.line = circ.shape.shapeparam.sel_line
    #circ.label.C = (50,50)
    # circ.set_label_visible(False)
    # print circ.curve_item.curveparam
    # circ.set_style(, option)
    circ.set_item_parameters({"ShapeParam": sh})
    #z = 999999999
    shape_cntr += 1
    z = shape_cntr
    if (plot):
        plot.add_item(circ, z)

    return (circ, z)