"""This module implements utility classes and functions for logging."""

from PyQt5 import QtCore, QtGui, QtWidgets
import logging
from . import termcolor
import types

LOG_LEVEL = logging.DEBUG

class NullHandler(logging.Handler):

    """A do-nothing log handler."""
    
    def emit(self, record):
        pass

class ColoredConsoleHandler(logging.StreamHandler):
    def emit(self, record):
        try:
            msg = self.format(record)
            if record.levelno == logging.WARNING:
                msg = termcolor.colored(msg, "yellow")
            elif record.levelno > logging.WARNING:
                msg = termcolor.colored(msg, "red")
            elif record.levelno == logging.DEBUG:
                msg = termcolor.colored(msg, "cyan")
            if not hasattr(types, "UnicodeType"): #if no unicode support...
                self.stream.write("%s\n" % msg)
            else:
                self.stream.write("%s\n" % msg)
            self.flush()
        except:
            self.handleError(record)


class BaseQtLogHandler(QtCore.QObject, logging.StreamHandler):
    
    def __init__(self):
        QtCore.QObject.__init__(self)
        logging.StreamHandler.__init__(self)

class QtLogHandler(BaseQtLogHandler):
    new_msg = QtCore.pyqtSignal(QtGui.QColor, object)
    def emit(self, record):
        msg = self.format(record)
        logstr = msg
        if record.levelno == logging.INFO:
            logstr = '%s' % msg
            #log.msg(logstr)
            #black
            self.new_msg.emit(QtGui.QColor(0, 0, 0, 255), logstr)
        elif record.levelno == logging.WARNING:
            logstr = 'WARNING: %s' % msg
            #log.msg(logstr)
            #orange
            self.new_msg.emit(QtGui.QColor(253, 14, 2, 255), logstr)
        elif record.levelno == logging.ERROR:
            logstr = 'ERROR: %s' % msg
            #log.err(logstr)
            #red
            self.new_msg.emit(QtGui.QColor(255, 0, 0, 255), logstr)
        elif record.levelno == logging.CRITICAL:
            logstr = '%s' % msg
            self.new_msg.emit(QtGui.QColor(0, 0, 255, 255), logstr)
        elif record.levelno == logging.DEBUG:
            logstr = 'DEBUG: %s' % (msg)
            self.new_msg.emit(QtGui.QColor(0, 0, 0, 255), logstr)
        else:
            logstr = '[lvl=%d] %s' % (record.levelno, msg)
            #log.msg(logstr)
            #black
            self.new_msg.emit(QtGui.QColor(0, 255, 0, 255), logstr)
            
        #print logstr
        self.flush()

def get_module_logger(name, filename=None):
    """A factory which creates loggers with the given name and returns it."""
    
    _logger = logging.getLogger(name)
    _logger.setLevel(LOG_LEVEL)
    _logger.addHandler( NullHandler() )
    return _logger

def log_to_qt(level=LOG_LEVEL):
    """Add a log handler which logs to a signal."""
    qt = QtLogHandler()
    qt.setLevel(level)
    formatter = logging.Formatter('%(asctime)s [%(name)s] %(message)s', '%b/%d %H:%M:%S')
    qt.setFormatter(formatter)
    logging.getLogger('').addHandler(qt)
    return(qt)

def log_to_console(level=LOG_LEVEL):
    """Add a log handler which logs to the console."""
    
    console = ColoredConsoleHandler()
    console.setLevel(level)
    formatter = logging.Formatter('%(asctime)s [%(name)s] %(message)s', '%b/%d %H:%M:%S')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

def log_to_file(filename, level=logging.DEBUG):
    """Add a log handler which logs to the console."""    
    logfile = logging.FileHandler(filename)
    logfile.setLevel(level)
    formatter = logging.Formatter('%(asctime)s [%(name)s] %(message)s', '%b/%d %H:%M:%S')
    logfile.setFormatter(formatter)
    logging.getLogger('').addHandler(logfile)
      
def log_to_qt_and_to_file_orig(filename, level=LOG_LEVEL):
    """Add a log handler which logs to a signal."""
    qt = QtLogHandler()
    qt.setLevel(level)
    formatter = logging.Formatter('%(asctime)s [%(name)s] %(message)s', '%b/%d %H:%M:%S')
    qt.setFormatter(formatter)
    logging.getLogger('').addHandler(qt)
    
    logfile = logging.FileHandler(filename)
    logfile.setLevel(level)
    formatter = logging.Formatter('%(asctime)s [%(name)s] %(message)s', '%b/%d %H:%M:%S')
    logfile.setFormatter(formatter)
    logging.getLogger('').addHandler(logfile)
    
    return(qt)


def log_to_qt_and_to_file(filename, level=LOG_LEVEL):
    """Add a log handler which logs to a signal.
    the level passed in is to filter what will be sent to the file, typically I want the console to
    see all messages EXCEPT debug messages, but I want the logfile to see ALL messages including debug
    messages

    This currently is hard coded to send all messages except debug messages to the console and
    all messages including debug to the file
    level values
        logging.DEBUG       10
        logging.INFO        20
        logging.ERROR       40
        logging.WARNING     30
        logging.CRITICAL    50

    when the level is set on a logger it will see messages of THAT level and HIGHER
    """
    qt = QtLogHandler()
    # set console to see INFO level and higher (skipping DEBUG)
    qt.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s [%(name)s] %(message)s', '%b/%d %H:%M:%S')
    qt.setFormatter(formatter)
    logging.getLogger('').addHandler(qt)

    logfile = logging.FileHandler(filename)
    # set file to see all messages DEBUG and higher
    logfile.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s [%(name)s] %(message)s', '%b/%d %H:%M:%S')
    logfile.setFormatter(formatter)
    logging.getLogger('').addHandler(logfile)

    return (qt)



