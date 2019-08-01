
from PyQt5 import QtCore

from cls.utils.roi_utils import get_unique_roi_id
from cls.plotWidgets.shapes.utils import create_rectangle, create_segment
from cls.utils.roi_utils import get_base_roi

PAD_SIZE = 1.2 #um

def add_pattern_to_plot(parent, xc=0.0, yc=0.0):
    '''
    parent is the imageWidget that is requesting the patter.
    The pattern is 9 1 by 1 um squares in 3 rows.
    G H I
    D E F
    A B C

    :param parent:
    :return:
    '''


    # xcenters = [0.5, 2.5, 4.5]
    # ycenters = [0.5, 2.5, 4.5]
    pad_width = PAD_SIZE + PAD_SIZE
    xcenters = [xc-pad_width, xc, xc+pad_width]
    ycenters = [yc-pad_width, yc, yc+pad_width]

    item_idx = 0
    ltr_lst = ['A','B','C','D','E','F','G','H','I']
    ltr_lst.reverse()
    rois_dct = {}
    title = 'pattern'
    main_rect = None
    points = []
    for x_center in xcenters:
        for y_center in ycenters:
            letter = ltr_lst.pop()
            x_roi = get_base_roi('pattrn_%sx' % letter, '', x_center, PAD_SIZE, 20, enable=True, is_point=False, src=None)
            y_roi = get_base_roi('pattrn_%sy' % letter, '', y_center, PAD_SIZE, 20, enable=True, is_point=False, src=None)

            x1 = float(x_roi['START'])
            y1 = float(y_roi['START'])
            x2 = float(x_roi['STOP'])
            y2 = float(y_roi['STOP'])

            rect = (x1, y1, x2, y2)
            item, z = create_rectangle(rect, title=title+'_' + letter, plot=parent.plot, annotated=False)
            item.selection_name = title+'_' + letter
            #qrect = QtCore.QRectF(QtCore.QPointF(rect[0], rect[2]), QtCore.QPointF(rect[3], rect[1]))
            qrect = QtCore.QRectF(QtCore.QPointF(rect[0], rect[1]), QtCore.QPointF(rect[2], rect[3]))

            if (main_rect is None):
                main_rect = qrect
            else:
                main_rect = main_rect.united(qrect)
            item_idx += 1
            rois_dct[letter] = {'X': x_roi, 'Y': y_roi}

    #create 1 large rectangle that will be on top of all of them and used as the one to drag around which provides the center
    #and size of the pattern
    main_r = (main_rect.left(), main_rect.top(), main_rect.right(), main_rect.bottom())
    #because z =None in create_rectangle() that ensures that the lastly created rectaangle will be on th etop, so it will be selected before
    #others below it so that is why main_rect is created last
    item, z = create_rectangle(main_r, title=title+'_MAIN', plot=parent.plot, annotated=True, alpha=0.01, l_style='DashLine', l_clr='#645d03')
    item.unique_id = get_unique_roi_id()
    item.selection_name = 'pattern_MAIN'
    return(rois_dct)

def set_shapeparam(item, sh, title='None', plot=None, annotated=False, alpha=0.05, l_style='SolidLine', l_clr='#ffff00'):
    item.set_resizable(False)
    sh._title = title
    sh.fill.alpha = alpha
    sh.sel_fill.alpha = alpha
    sh.symbol.alpha = alpha
    sh.sel_symbol.alpha = alpha
    sh.line._style = l_style
    sh.line._color = l_clr

    sh.symbol.marker = 'NoSymbol'
    sh.sel_symbol.marker = 'NoSymbol'

    item.set_item_parameters({"ShapeParam": sh})