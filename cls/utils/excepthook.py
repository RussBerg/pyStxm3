
from PyQt5 import QtWidgets
import time
import io
import traceback
import functools
import logging
import sys


def excepthook(excType, excValue, tracebackobj):
    """
    Global function to catch unhandled exceptions.

    @param excType exception type
    @param excValue exception value
    @param tracebackobj traceback object
    """
    separator = '-' * 80
    logFile = "simple.log"
    notice = \
        """An unhandled exception occurred. Please report the problem\n""" \
        """using the error reporting dialog or via email to <%s>.\n""" \
        """A log has been written to "%s".\n\nError information:\n""" % \
        ("russ.berg@lightsource.ca", "")
    versionInfo = "0.0.1"
    timeString = time.strftime("%Y-%m-%d, %H:%M:%S")

    tbinfofile = io.StringIO()
    traceback.print_tb(tracebackobj, None, tbinfofile)
    tbinfofile.seek(0)
    tbinfo = tbinfofile.read()
    errmsg = '%s: \n%s' % (str(excType), str(excValue))
    sections = [separator, timeString, separator, errmsg, separator, tbinfo]
    msg = '\n'.join(sections)
    try:
        f = open(logFile, "w")
        f.write(msg)
        f.write(versionInfo)
        f.close()
    except IOError:
        pass
    errorbox = QtWidgets.QMessageBox()
    errorbox.setText(str(notice) + str(msg) + str(versionInfo))
    errorbox.exec_()

    #now force an exit of the application
    inst = QtWidgets.QApplication.instance()
    inst.exit()


# exception_decor.py



def create_logger():
    """
    Creates a logging object and returns it
    """
    logger = logging.getLogger("example_logger")
    logger.setLevel(logging.INFO)

    # create the logging file handler
    fh = logging.FileHandler("test.log")

    fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(fmt)
    fh.setFormatter(formatter)

    # add handler to logger object
    logger.addHandler(fh)
    return logger


def exception(function):
    """
    A decorator that wraps the passed in function and logs
    exceptions should one occur
    """

    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        logger = create_logger()
        try:
            return function(*args, **kwargs)
        except:
            # log the exception

            s = function.__name__
            err = "There was an exception in [%s]" % s
            err += traceback.format_exc()
            err += "\npySTXM will be stopped on close of this message box\n press <Enter> several times to exit"
            logger.exception(err)

            # re-raise the exception

            errorbox = QtWidgets.QMessageBox()
            errorbox.setText(str(err))
            errorbox.exec_()
            #now force the application to die
            inst = QtWidgets.QApplication.instance()
            inst.exit()
            #raise Exception(err)

    return wrapper


#from exception_decor import exception


@exception
def zero_divide():
    1 / 0


if __name__ == '__main__':
    zero_divide()

