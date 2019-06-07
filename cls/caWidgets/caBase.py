# -*- coding:utf-8 -*-
"""
Created on 2011-03-07

@author: bergr
"""


class caBase():
    def __init__(self, pvName, widgetType):
        self.pvName = pvName
        self.widgetType = widgetType
        self.chId = None
        