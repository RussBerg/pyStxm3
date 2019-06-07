# -*- coding:utf-8 -*-
"""
Created on 2011-08-05

@author: bergr
"""
import numpy
from PyQt5.QtCore import QRect, QPoint

def line(m, x, b):
    return(m*x+b)

def yintercept(y,m,x):
    b = y - m*x
    return(b)

def x_intersection_point(m1,m2,b1,b2):
    x = (b2-b1)/(m1-m2)
    return(x)

def get_angle_from_points(p1,p2):
    
    a = p2[0] - p1[0]
    o = p2[1] - p1[1]
    theta = numpy.arctan(o/a)
    return(theta)

def get_slope_from_angle(theta):
    m = numpy.tan(theta)
    return(m)

def get_angle_from_slope(slope):
    theta = numpy.arctan(slope)
    return(theta)



def distance(p1,p2):
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    d = numpy.sqrt((dx*dx)+(dy*dy))
    return(d)

def slope(p1,p2):
    rise = p2[1] - p1[1]
    run = p2[0] - p1[0]
    return(rise/run)

def rad(deg):
    return numpy.deg2rad(deg)

def deg(rad):
    return numpy.rad2deg(rad)
    
def opp(theta, hyp=None, adj=None):
    #th = numpy.deg2rad(theta)
    th = theta

    if((hyp is None) and (adj is None)):
        res = 0.0
        print('need to supply hyp or adj: opp(theta, hyp, adj)')
    if(hyp is None):
        res = numpy.tan(th)*float(adj)
    elif(adj is None):    
        res = numpy.sin(th)*float(hyp)
    else:
        res = 0.0    
    #print 'opp = %f' % res
    return(res)

def adj(theta, hyp=None, opp=None):
    #th = numpy.deg2rad(theta)
    th = theta
    
    if(opp is None):
        res = numpy.cos(th)*float(hyp)
    elif(hyp is None):
        res = float(opp) / numpy.tan(th)    
    else:
        res=0.0    
    #print 'adj = %f' % res
    return(res)

def hypot(theta, adj=None, opp = None):
    #th = numpy.deg2rad(theta)
    th = theta
    
    if(opp is None):
        res = float(adj) / numpy.cos(th)
    elif(adj is None):
        res = float(opp) / numpy.sin(th)
    else:
        #print 'hypot: ERROR: cannot calc Hypotenuse, need to spec opp or adjacent'
        res = 0.0
    
    #print 'hypot = %f' % res
    return(res)

def pathag(a,b):
    res = numpy.sqrt(numpy.square(a) + numpy.square(b))
    #print 'pathag = %f' % res
    return(res)

def calcRectPoints(center, size, angle):
    height = size[1] *2
    width = size[0] *2
    #first construct a double sized rect (top, left, width*2, height*2)
    rect = QRect(center[0] - size[0], center[1] + size[1], width, height)
    
    #then move the center to center+width and center + height
    newCenter = QPoint(center[0] , center[1])
    #print 'newCenter =   (%f, %f)' % (newCenter.x(), newCenter.y())
    rect.moveCenter(newCenter)
    
    #rect.getCoords()
    a = QPoint(rect.center())
    b = QPoint(rect.right(), newCenter.y())
    c = QPoint(rect.topRight())
    e = QPoint(rect.topLeft())
    f = QPoint(rect.left(), newCenter.y())
    g = QPoint(rect.bottomLeft())
    i = QPoint(rect.bottomRight())
    d = QPoint(newCenter.x(), rect.top())
    h = QPoint(newCenter.x(), rect.bottom())
    angleR = numpy.deg2rad(angle)
    B = rotate_about('B', newCenter, b, angleR)
    C = rotate_about('C', newCenter, c, angleR)
    E = rotate_about('E', newCenter, e, angleR)
    F = rotate_about('F', newCenter, f, angleR)
    G = rotate_about('G', newCenter, g, angleR)
    I = rotate_about('I', newCenter, i, angleR)
    D = rotate_about('D', newCenter, d, angleR)
    H = rotate_about('H', newCenter, h, angleR)    
    return(a,B,C,E,F,G,I,D,H)

def slide( p, deltaP):
    '''Move to new (x+dx,y+dy).
    Can anyone think up a better name for this function?
    slide? shift? delta? move_by?
    '''
    x = p.x() + deltaP.x()
    y = p.y() + deltaP.y()
    return(QPoint(x,y))

def rotate_about(name, center,  p, theta):
    """Rotate counter-clockwise around a point, by theta degrees.
    Positive y goes *up,* as in traditional mathematics.
    The new position is returned as a new Point.
    """
    centerOffset = QPoint(-center.x(), -center.y())
    p = slide(p, centerOffset)
    p = rotate(p, theta)
    result = slide(p, center)
    return result

def rotate(point, rad):
    """Rotate counter-clockwise by rad radians.
    Positive y goes *up,* as in traditional mathematics.
     Interestingly, you can use this in y-down computer graphics, if
    you just remember that it turns clockwise, rather than
    counter-clockwise.
    The new position is returned as a new Point.
    """

    px = point.x()
    py = point.y()
 
    s, c = [f(rad) for f in (numpy.sin, numpy.cos)]
    x, y = (c*px - s*py, s*px + c*py)
    
    #print 'rotate [%s]: was (%f, %f) is now (%f, %f)' % (name, point.x(), point.y(), x, y)
    #print 'rotate : was (%f, %f) is now (%f, %f)' % (point.x(), point.y(), x, y)
    
    return QPoint(x,y)



def slide_noqt( p, deltaP):
    '''Move to new (x+dx,y+dy).
    Can anyone think up a better name for this function?
    slide? shift? delta? move_by?
    '''
    x = p[0] + deltaP[0]
    y = p[1] + deltaP[1]
    return((x,y))

def rotate_about_noqt(name, center,  p, theta):
    """Rotate counter-clockwise around a point, by theta degrees.
    Positive y goes *up,* as in traditional mathematics.
    The new position is returned as a new Point.
    """
    centerOffset = (-center[0], -center[0])
    p = slide_noqt(p, centerOffset)
    p = rotate_noqt(p, theta)
    result = slide_noqt(p, center)
    return result

def rotate_noqt(point, rad):
    """Rotate counter-clockwise by rad radians.
    Positive y goes *up,* as in traditional mathematics.
     Interestingly, you can use this in y-down computer graphics, if
    you just remember that it turns clockwise, rather than
    counter-clockwise.
    The new position is returned as a new Point.
    """

    px = point[0]
    py = point[1]
 
    s, c = [f(rad) for f in (numpy.sin, numpy.cos)]
    x, y = (c*px - s*py, s*px + c*py)
    
    #print 'rotate [%s]: was (%f, %f) is now (%f, %f)' % (name, point.x(), point.y(), x, y)
    #print 'rotate : was (%f, %f) is now (%f, %f)' % (point.x(), point.y(), x, y)
    
    return((x,y))


def foci(major, minor):
    """ this returns the foci of the ellipse given the major and monir axis,
    the answer is the value +- on the major axis
    """
    return(numpy.sqrt(numpy.square(major) - numpy.square(minor)))

if __name__ == '__main__':
    import sys
    import random
    import cv, cv2
    from PyQt5.QtWidgets import QApplication
  
    app = QApplication(sys.argv)

    cv.NamedWindow("rect", 1)
    finale_img = cv.CreateImage((600,600), cv.IPL_DEPTH_8U, 3)
    cent = (int(300), int(300))
    size = (50,50)
    color2 = cv.CV_RGB(random.randrange(256),random.randrange(256),random.randrange(256))
    cv.Ellipse(finale_img, cent, size, 90, 0, 360, color2, 2, cv.CV_AA,0)
    for i in range(0, 360, 22.5):
       
    
        center,B,C,E,F,G,I,D,H = calcRectPoints(cent, size, float(i))
        Ex = int(E.x())
        Ey = int(E.y())
        Ix = int(I.x())
        Iy = int(I.y())
        color = cv.CV_RGB(random.randrange(256),random.randrange(256),random.randrange(256))
        #cv.Rectangle(finale_img, center,(r[0],r[1]), cv.CV_RGB(255,255, 255),1,cv.CV_AA, 0)
        cv.Rectangle(finale_img,(Ex, Ey),(Ix, Iy), color,1,cv.CV_AA, 0)
        cv.ShowImage( "rect", finale_img )
        
    sys.exit(app.exec_())
    
    
