'''
Created on Aug 9, 2016

@author: bergr
'''
import os
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import pyqtSignal
from guiqwt.tools import *
#from guiqwt.config import _
from guidata.qt.compat import getopenfilenames

from cls.plotWidgets.guiqwt_config import _

class clsOpenFileTool(CommandTool):
    
    #openfile = pyqtSignal(str)
    openfile = pyqtSignal(object)
    
    def __init__(self, manager, formats='*.*', toolbar_id=DefaultToolbarID):
        """
        __init__(): description

        :param manager: manager description
        :type manager: manager type

        :param formats='*.*': formats='*.*' description
        :type formats='*.*': formats='*.*' type

        :param toolbar_id=DefaultToolbarID: toolbar_id=DefaultToolbarID description
        :type toolbar_id=DefaultToolbarID: toolbar_id=DefaultToolbarID type

        :returns: None
        """
        CommandTool.__init__(self, manager, _("Open..."),
                             get_std_icon("DialogOpenButton", 16),
                             toolbar_id=toolbar_id)
        self.formats = formats
        self.directory = ""

    def set_enabled(self, en):
        self.action.setEnabled(en)

    def set_directory(self, dirname):
        """
        set_directory(): description

        :param dirname: dirname description
        :type dirname: dirname type

        :returns: None
        """
        self.directory = dirname

    # def get_filename(self, plot):
    #     """
    #     get_filename(): description
    #
    #     :param plot: plot description
    #     :type plot: plot type
    #
    #     :returns: None
    #     """
    #     saved_in, saved_out, saved_err = sys.stdin, sys.stdout, sys.stderr
    #     sys.stdout = None
    #     filename, _f = getopenfilename(plot, _("Open"),
    #                                    self.directory, self.formats)
    #     sys.stdin, sys.stdout, sys.stderr = saved_in, saved_out, saved_err
    #     filename = unicode(filename)
    #     if filename:
    #         self.directory = os.path.dirname(filename)
    #     return filename
    def get_filename(self, plot):
        """
        get_filename(): description

        :param plot: plot description
        :type plot: plot type

        :returns: None
        """
        saved_in, saved_out, saved_err = sys.stdin, sys.stdout, sys.stderr
        sys.stdout = None
        filenames, _f = getopenfilenames(plot, _("Open"),
                                       self.directory, self.formats)
        sys.stdin, sys.stdout, sys.stderr = saved_in, saved_out, saved_err
        filename = str(filenames)
        #if filename:
        #    self.directory = os.path.dirname(filename)
        return filenames

    def activate_command(self, plot, checked):
        """
        activate_command(): description

        :param plot: plot description
        :type plot: plot type

        :param checked: checked description
        :type checked: checked type

        :returns: None
        """
        """Activate tool"""
        filename = self.get_filename(plot)
        if filename:
            self.openfile.emit(filename)
            