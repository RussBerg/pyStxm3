
import numpy as np
from math import fabs, sqrt, sin, cos, pi

from guidata.qt.QtGui import QPen, QBrush, QPolygonF, QTransform, QPainter
from guidata.qt.QtCore import Qt, QRectF, QPointF, QLineF

from guidata.utils import assert_interfaces_valid, update_dataset
from guidata.py3compat import maxsize

# Local imports
from guiqwt.transitional import QwtPlotItem, QwtSymbol, QwtPlotMarker
from guiqwt.config import CONF
from cls.plotWidgets.guiqwt_config import _

from guiqwt.interfaces import IBasePlotItem, IShapeItemType, ISerializableType
from guiqwt.styles import (MarkerParam, ShapeParam, RangeShapeParam,
                           AxesShapeParam, MARKERSTYLES)
from guiqwt.geometry import (vector_norm, vector_projection, vector_rotation,
                             compute_center)
from guiqwt.baseplot import canvas_to_axes
from guiqwt.shapes import PolygonShape, AbstractShape


class BeamSpotShape(PolygonShape):
    CLOSED = True

    def __init__(self, x1=0, y1=0, shapeparam=None):
        super(BeamSpotShape, self).__init__(shapeparam=shapeparam)
        self.is_ellipse = False
        self.set_xdiameter(x1, y1, x1+1, y1+1)
        self.dist_from_center = 5.0
        self.width_of_side = 2.5
        self.len_long_side = 25.0
        self.len_short_side = 20.0


        clr = 'yellow'

        self.set_resizable(False)
        self.shapeparam.label = 'beam_spot'
        self.shapeparam._title = 'beam_spot'
        self.shapeparam.symbol.alpha = 0.6
        self.shapeparam.sel_symbol.alpha = 0.6
        self.shapeparam.symbol.marker = 'NoSymbol'
        self.shapeparam.sel_symbol.marker = 'NoSymbol'
        self.shapeparam.sel_symbol.color = clr
        self.shapeparam.symbol.color = clr
        self.shapeparam.fill.color = clr
        self.shapeparam.sel_fill.color = clr

        self.shapeparam.update_shape(self)

    def get_xdiameter(self):
        """Return the coordinates of the ellipse's X-axis diameter"""

        return tuple(self.points[0]) + tuple(self.points[1])

    def get_ydiameter(self):
        """Return the coordinates of the ellipse's Y-axis diameter"""
        return tuple(self.points[2]) + tuple(self.points[3])

    def get_stars_rect(self, cx, cy):

        left = cx - self.len_long_side - self.dist_from_center
        top = cy - self.len_long_side - self.dist_from_center
        right = cx + self.len_long_side + self.dist_from_center
        btm = cy + self.len_long_side + self.dist_from_center

        rect = QRectF()
        rect.setTop(top)
        rect.setLeft(left)
        rect.setBottom(btm)
        rect.setRight(right)

        return(rect)

    def get_stars_width(self, cx, cy):
        wdth = (cx + self.len_long_side + self.dist_from_center)
        return(wdth)

    def get_stars_ht(self, cx, cy):
        ht = (cy + self.len_long_side + self.dist_from_center)
        return(ht)

    def _stars_points(self, cx, cy):

        st1_poly = QPolygonF()
        st1_poly.append(QPointF(cx, cy + self.dist_from_center))
        st1_poly.append(QPointF(cx + self.width_of_side, cy + self.len_short_side))
        st1_poly.append(QPointF(cx, cy + self.len_long_side))
        st1_poly.append(QPointF(cx - self.width_of_side, cy + self.len_short_side))

        st2_poly = QPolygonF()
        st2_poly.append(QPointF(cx - self.dist_from_center, cy))
        st2_poly.append(QPointF(cx - self.len_short_side, cy + self.width_of_side))
        st2_poly.append(QPointF(cx - self.len_long_side, cy))
        st2_poly.append(QPointF(cx - self.len_short_side, cy - self.width_of_side))

        st3_poly = QPolygonF()
        st3_poly.append(QPointF(cx, cy - self.dist_from_center))
        st3_poly.append(QPointF(cx - self.width_of_side, cy - self.len_short_side))
        st3_poly.append(QPointF(cx, cy - self.len_long_side))
        st3_poly.append(QPointF(cx + self.width_of_side, cy - self.len_short_side))

        st4_poly = QPolygonF()
        st4_poly.append(QPointF(cx + self.dist_from_center, cy))
        st4_poly.append(QPointF(cx + self.len_short_side, cy - self.width_of_side))
        st4_poly.append(QPointF(cx + self.len_long_side, cy))
        st4_poly.append(QPointF(cx + self.len_short_side, cy + self.width_of_side))

        return([st1_poly, st2_poly, st3_poly, st4_poly])

    def set_xdiameter(self, x0, y0, x1, y1):
        """Set the coordinates of the ellipse's X-axis diameter"""
        xline = QLineF(x0, y0, x1, y1)
        yline = xline.normalVector()
        yline.translate(xline.pointAt(.5) - xline.p1())
        if self.is_ellipse:
            yline.setLength(self.get_yline().length())
        else:
            yline.setLength(xline.length())
        yline.translate(yline.pointAt(.5) - yline.p2())
        self.set_points([(x0, y0), (x1, y1),
                         (yline.x1(), yline.y1()), (yline.x2(), yline.y2())])

    # def get_xdiameter(self):
    #     """Return the coordinates of the ellipse's X-axis diameter"""
    #     return tuple(self.points[0]) + tuple(self.points[1])
    #
    # def set_ydiameter(self, x2, y2, x3, y3):
    #     """Set the coordinates of the ellipse's Y-axis diameter"""
    #     yline = QLineF(x2, y2, x3, y3)
    #     xline = yline.normalVector()
    #     xline.translate(yline.pointAt(.5) - yline.p1())
    #     if self.is_ellipse:
    #         xline.setLength(self.get_xline().length())
    #     xline.translate(xline.pointAt(.5) - xline.p2())
    #     self.set_points([(xline.x1(), xline.y1()), (xline.x2(), xline.y2()),
    #                      (x2, y2), (x3, y3)])

    def get_ydiameter(self):
        """Return the coordinates of the ellipse's Y-axis diameter"""
        return tuple(self.points[2]) + tuple(self.points[3])

    # def get_rect(self):
    #     """Circle only!"""
    #     (x0, y0), (x1, y1) = self.points[0], self.points[1]
    #     xc, yc = .5 * (x0 + x1), .5 * (y0 + y1)
    #     radius = .5 * np.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2)
    #     return xc - radius, yc - radius, xc + radius, yc + radius

    def get_center(self):
        """Return center coordinates: (xc, yc)"""
        return compute_center(*self.get_xdiameter())

    def set_rect(self, x0, y0, x1, y1):
        """Circle only!"""
        self.set_xdiameter(x0, .5 * (y0 + y1), x1, .5 * (y0 + y1))

    def transform_points(self, xMap, yMap):
        points = QPolygonF()
        for i in range(self.points.shape[0]):
            points.append(QPointF(xMap.transform(self.points[i, 0]),
                                  yMap.transform(self.points[i, 1])))
        return points


    def compute_elements(self, xMap, yMap):
        """Return points, lines and ellipse rect"""
        points = self.transform_points(xMap, yMap)

        line0 = QLineF(points[0], points[1])
        line1 = QLineF(points[2], points[3])
        #print points[0]

        #rect is used to determine a hit test so make sure it encompasses all items
        rect = QRectF()
        rect.setWidth(line0.length())
        rect.setHeight(line1.length())
        rect.moveCenter(line0.pointAt(.5))

        c = rect.center()
        rect.setWidth(self.dist_from_center)
        rect.setHeight(self.dist_from_center)

        # rect.moveCenter(line0.pointAt(.5))
        st1, st2, st3, st4 = self._stars_points(c.x(), c.y())

        #rect = self.get_stars_rect(line0.pointAt(.5), line1.pointAt(.5))
        #rect.setWidth(line0.length())
        #rect.setHeight(line1.length())
        #rect.moveCenter(line0.pointAt(.5))

        return points, line0, line1, rect, st1, st2, st3, st4
        #return points, line0, line1, rect

    def hit_test(self, pos):
        """return (dist, handle, inside)"""
        if not self.plot():
            return maxsize, 0, False, None
        dist, handle, inside, other = self.poly_hit_test(self.plot(),
                                                         self.xAxis(), self.yAxis(), pos)
        if not inside:
            xMap = self.plot().canvasMap(self.xAxis())
            yMap = self.plot().canvasMap(self.yAxis())
            #_points, _line0, _line1, rect = self.compute_elements(xMap, yMap)
            _points, _line0, _line1, rect, _st1, _st2, _st3, _st4 = self.compute_elements(xMap, yMap)
            inside = rect.contains(QPointF(pos))
        return dist, handle, inside, other

    def draw(self, painter, xMap, yMap, canvasRect):
        points, line0, line1, rect, st1, st2, st3, st4 = self.compute_elements(xMap, yMap)
        #points, line0, line1, rect = self.compute_elements(xMap, yMap)
        pen, brush, symbol = self.get_pen_brush(xMap, yMap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(pen)
        painter.setBrush(brush)
        #painter.drawLine(line0)
        #painter.drawLine(line1)

        painter.drawPolygon(st1)
        painter.drawPolygon(st2)
        painter.drawPolygon(st3)
        painter.drawPolygon(st4)

        painter.save()
        painter.translate(rect.center())
        painter.rotate(-line0.angle())
        painter.translate(-rect.center())
        #painter.drawEllipse(rect.toRect())
        painter.restore()
        if symbol != QwtSymbol.NoSymbol:
            for i in range(points.size()):
                symbol.drawSymbol(painter, points[i].toPoint())

    def get_xline(self):
        return QLineF(*(tuple(self.points[0]) + tuple(self.points[1])))

    def get_yline(self):
        return QLineF(*(tuple(self.points[2]) + tuple(self.points[3])))

    def __reduce__(self):
        state = (self.shapeparam, self.points, self.z())
        return (self.__class__, (), state)

    def __setstate__(self, state):
        self.shapeparam, self.points, z = state
        self.setZ(z)
        self.shapeparam.update_shape(self)



assert_interfaces_valid(BeamSpotShape)

