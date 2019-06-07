

from guiqwt.builder import PlotItemBuilder
from guiqwt.annotations import AnnotatedPoint

class clsPlotItemBuilder(PlotItemBuilder):
    '''
    subclass teh main builder and extend it to support annotated_point
    '''

    def annotated_point(self, x0, y0,title=None, subtitle=None):
        """
        Make an annotated point `plot item`
        (:py:class:`guiqwt.annotations.AnnotatedPoint` object)
           * x0, y0: point coordinates
           * title, subtitle: strings
        """
        #param = self.__get_annotationparam(title, subtitle)
        param = self._PlotItemBuilder__get_annotationparam(title, subtitle)

        shape = AnnotatedPoint(x0, y0, param)
        shape.set_style("plot", "shape/drag")
        return shape



