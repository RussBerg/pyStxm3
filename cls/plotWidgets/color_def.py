'''
Created on Sep 28, 2015

@author: bergr
'''
from PyQt5 import QtGui, QtCore

def get_alarm_clr(alpha):
	return(QtGui.QColor(255, 0, 0, alpha))

def get_warn_clr(alpha):
	return(QtGui.QColor(215, 225, 4, alpha))


def get_normal_clr(alpha):
	return(QtGui.QColor(20, 255, 0, alpha))


#BRUSHSTYLE_CHOICES = [
# 				    ("NoBrush", _("No brush pattern"), "nobrush.png"),
# 				    ("SolidPattern", _("Uniform color"), "solidpattern.png"),
# 				    ("Dense1Pattern", _("Extremely dense brush pattern"), "dense1pattern.png"),
# 				    ("Dense2Pattern", _("Very dense brush pattern"), "dense2pattern.png"),
# 				    ("Dense3Pattern", _("Somewhat dense brush pattern"), "dense3pattern.png"),
# 				    ("Dense4Pattern", _("Half dense brush pattern"), "dense4pattern.png"),
# 				    ("Dense5Pattern", _("Somewhat sparse brush pattern"), "dense5pattern.png"),
# 				    ("Dense6Pattern", _("Very sparse brush pattern"), "dense6pattern.png"),
# 				    ("Dense7Pattern", _("Extremely sparse brush pattern"), "dense7pattern.png"),
# 				    ("HorPattern", _("Horizontal lines"), "horpattern.png"),
# 				    ("VerPattern", _("Vertical lines"), "verpattern.png"),
# 				    ("CrossPattern", _("Crossing horizontal and vertical lines"),
# 				     "crosspattern.png"),
# 				    ("BDiagPattern", _("Backward diagonal lines"), "bdiagpattern.png"),
# 				    ("FDiagPattern", _("Forward diagonal lines"), "fdiagpattern.png"),
# 				    ("DiagCrossPattern", _("Crossing diagonal lines"), "diagcrosspattern.png"),
# 				    ("LinearGradientPattern", _("Linear gradient (set using a dedicated QBrush constructor)"), "none.png"),
# 				    ("ConicalGradientPattern", _("Conical gradient (set using a dedicated QBrush constructor)"), "none.png"),
# 				    ("RadialGradientPattern", _("Radial gradient (set using a dedicated QBrush constructor)"), "none.png"),
# 				    ("TexturePattern", _("Custom pattern (see QBrush::setTexture())"), "none.png"),
# 				]
def get_normal_fill_pattern():
	return(QtCore.Qt.SolidPattern)

def get_warn_fill_pattern():
	#It turns out that the Dense7Pattern added a ton of overhead in cycles so is mush slower UI updating than SOlid
	#so making it Solid instead for performance reasons
	#return(QtCore.Qt.Dense7Pattern)
	return(QtCore.Qt.SolidPattern)

def get_alarm_fill_pattern():
	return(QtCore.Qt.SolidPattern)

def get_coarse_mtr_fill_pattern():
	return(QtCore.Qt.DiagCrossPatter)

def get_fine_mtr_fill_pattern():
	return(QtCore.Qt.SolidPattern)

