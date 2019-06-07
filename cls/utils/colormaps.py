# -*- coding:utf-8 -*-
"""
Created on 2011-02-22

@author: bergr

Imports the colormaps from matplotlib (pylab) and assigns 11 common colormaps to 
the COLORMAPS dictionary:
_COLORNAMES = ['gist_yarg', 'gist_gray', 'hot', 'jet', 'hsv', 'Spectral', 'Paired', 'gist_heat', 'PiYG', 'Set1', 'gist_ncar']
COLORMAPS = {}

"""
from pylab import cm

_COLORNAMES = ['gist_yarg', 'gist_gray', 'hot', 'jet', 'hsv', 'Spectral', 'Paired', 'gist_heat', 'PiYG', 'Set1', 'gist_ncar']
COLORMAPS = {}

#note that these are not in the format that QImage.setColor needs them to be which is 
# ABGR
COLORMAPS['gist_yarg'] = cm.gist_yarg
COLORMAPS['gist_gray'] = cm.gist_gray
COLORMAPS['hot'] = cm.hot
COLORMAPS['jet'] = cm.jet
COLORMAPS['hsv'] = cm.hsv
COLORMAPS['Spectral'] = cm.Spectral
COLORMAPS['Paired'] = cm.Paired
COLORMAPS['gist_heat'] = cm.gist_heat
COLORMAPS['PiYG'] = cm.PiYG
COLORMAPS['Set1'] = cm.Set1
COLORMAPS['gist_ncar'] = cm.gist_ncar
    
        