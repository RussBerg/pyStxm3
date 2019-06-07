"""
guiLoop lets you use while and for loops with GUIs.
Usually using loops in GUIs makes them block.

This module uses the yield statement in loops to let the GUI update while the loop is still running.
See the example.py or start_and_stop.py for examples.
The code is available here: https://gist.github.com/niccokunzmann/8673951#file-guiloop-py

Currently only tkinter is supported but with a little help this can be adapted to other GUI frameworks, too.

Change the function _start_in_gui for different GUI frameworks.

If you use this code for an other GUI than tkinter send me your code or
leave a comment so that some day this can become a module on pypi.python.org
useful for others, too.

This was created because of an stackoverflow question:
    http://stackoverflow.com/questions/21411748/python-how-do-i-continuously-repeat-a-sequence-without-a-while-loop-and-still
    
"""
from PyQt5 import QtGui
import time
from PyQt5 import QtWidgets

def use_tkinter_after(gui_element, wait_time, call_this):
    # the following line needs replacement depending on the GUI
    # it calls 'call_this' after a period of time 'wait_time' in ms
    # for Tkinter
    gui_element.after(wait_time, call_this)

def use_PyQT4_QTimer(gui_element, wait_time, call_this):
    from PyQt5.QtCore import QTimer
    QTimer.singleShot(wait_time, call_this)

def use_any_timer(gui_element, wait_time, call_this):
    if hasattr(gui_element, 'after'):
        use_tkinter_after(gui_element, wait_time, call_this)
    elif hasattr(gui_element, 'pyqtConfigure'):
        use_PyQT4_QTimer(gui_element, wait_time, call_this)
    else:
        raise TypeError("Can not automatically detect which GUI this is.")

def _loop_in_the_gui(gui_element, generator, _start_in_gui):
    try:
        # generator yields the time to wait
        wait_time = next(generator)
    except StopIteration:
        pass
    else:
        if wait_time is None:
            # yield
            wait_time = 0
        else:
            # yield seconds
            wait_time = int(wait_time * 1000) # Tkinter works with milli seconds
        call_this_again = lambda: _loop_in_the_gui(gui_element, generator,
                                                   _start_in_gui)
        _start_in_gui(gui_element, wait_time, call_this_again)

class guiLoop(object):
    
    def __init__(self, function, start_in_gui = use_any_timer):
        """make a function to a guiLoop function
        The resulting function needs a gui element as first argument."""
        self.function = function
        self.__doc__ = function.__doc__
        self.__name__ = function.__name__
        self.start_in_gui = start_in_gui

    def __call__(self, gui_element, *args, **kw):
        generator = self.function(*args, **kw)
        _loop_in_the_gui(gui_element, generator, self.start_in_gui)
        return generator

    def __get__(self, gui_element, cls):
        if gui_element is None:
            return self
        return lambda *args, **kw: self(gui_element, gui_element, *args, **kw)
        

#@guiLoop
#def gui_sleep(dly):
#    #print 'gui_sleep: starting to sleep'
#    yield dly # time to wait
#    #print 'gui_sleep: DONE!'
        
def gui_sleep(dly):
    iters = int(dly/0.001)
    idx = 0
    for i in range(iters):
        time.sleep(0.001)
        if(idx > 50):
            QtWidgets.QApplication.processEvents()
            idx = 0
        idx += 1
    QtWidgets.QApplication.processEvents()

def tkLoop(function):
    """a guiLoop for tkinter"""
    return guiLoop(function, use_tkinter_after)

def qt4Loop(function):
    """a guiLoop for PyQT4"""
    return guiLoop(function, use_PyQT4_QTimer)

class StopLoopException(Exception):
    """This is raised if the loop shall stop"""
    pass

def stopLoop(generator):
    """stop the loop
    Generator is the return value of guiLoop."""
    try: generator.throw(StopLoopException())
    except StopLoopException: pass

__all__ = ['guiLoop', 'stopLoop', 'StopLoopException', 'tkLoop', 'qt4Loop']
