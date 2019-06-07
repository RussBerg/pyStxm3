'''
Created on Jan 15, 2010

@author: michel
'''
from PyQt5.QtCore import QThread
import threading
# from bcm.protocol.ca import threads_init
import time


# def async(f):
#     """ Run the specified function asynchronously in a thread. Return values will not be available"""
#
#     def new_f(*args, **kwargs):
#         # threads_init() # enable epics environment to be active within thread
#         return f(*args, **kwargs)
#
#     def _f(*args, **kwargs):
#         threading.Thread(target=new_f, args=args, kwargs=kwargs).start()
#         # pass
#
#     _f.__name__ = f.__name__
#     return _f


def ca_thread_enable(f):
    """ Make sure an active EPICS CA context is available or join one before running"""

    def _f(*args, **kwargs):
        threads_init()
        return f(*args, **kwargs)
        _f.__name__ = f.__name__

    return _f


def QTasync(f):
    """ Run the specified function asynchronously in a thread. Return values will not be available"""

    def new_f(*args, **kwargs):
        # print args
        # print kwargs
        # threads_init() # enable epics environment to be active within thread
        return f(*args, **kwargs)

    def new_f_1arg(*args):
        # threads_init() # enable epics environment to be active within thread
        return f(*args)

    #    def done(*args):
    #        print 'thread finished'

    def _f(*args, **kwargs):
        # print args
        # print kwargs
        thread = QThread()
        # override the run() function for teh trhead to point to our passed in func
        # thread.run = lambda self=thread : new_f(kwargs, args)
        thread.run = lambda self=thread: new_f(args, kwargs)
        # if len(kwargs.keys()) > 0:
        # thread.run = lambda self=thread : new_f(args, kwargs)
        # else:
        #    thread.run = lambda self=thread : new_f_1arg(args)
        # thread.finished.connect(done)
        thread.start()

    _f.__name__ = f.__name__
    return _f


def QTasync_new(f):
    """ Run the specified function asynchronously in a thread. Return values will not be available"""

    def new_f(*args, **kwargs):
        return f(*args, **kwargs)

    def _f(*args, **kwargs):
        thread = QThread()

        # thread.run = lambda self=thread : new_f(args, kwargs)
        thread.run = lambda self=thread: new_f(args, kwargs)
        thread.start()

    _f.__name__ = f.__name__
    return _f


def timeit(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()

        print('%r (%r, %r) %2.2f sec' % \
              (method.__name__, args, kw, te - ts))
        # return result
        return ('%2.2f sec' % (te - ts))

    return timed


def timeit_withResult(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()

        # print '%r (%r, %r) %2.2f sec' % (method.__name__, args, kw, te-ts)
        # return result
        return ('%2.2f' % (te - ts), result)

    return (timed)


if __name__ == "__main__":

    import sys
    from PyQt5 import QtCore

    app = QtCore.QCoreApplication(sys.argv)


    class foo(object):

        @timeit_withResult
        def testTime(self, args):
            print(args, end=' ')

            for i in range(0, args):
                print('testTime:[%d]' % i)
            return ('SUCCESS')

        @QTasync
        def testFunction(self, dud):
            print('testFunction: self == ', self)
            print(self)
            print(self[0])
            print(self[1])
            print(self[2])

            # for i in range(0, args[0]):
            #    print 'foo:testFunction:[%d]' % i

        @QTasync
        def test2argFunction(self, args):
            print(args, end=' ')

            for i in range(args[0], args[1]):
                print('foo:test2argFunction:[%d]' % i)


    @QTasync
    def testFunction(args):
        print(args, end=' ')

        for i in range(0, args[0]):
            print('testFunction:[%d]' % i)


    @QTasync
    def test2argFunction(args):
        print(args, end=' ')

        for i in range(args[0], args[1]):
            print('test2argFunction:[%d]' % i)
            # testFunction((100,))


    # test2argFunction((45,78))
    f = foo()
    # res = f.testTime(10)
    # print 'result of calling f.testTime(10): ' , res
    f.testFunction(100, 12)
    # f.test2argFunction((45,78))

    sys.exit(app.exec_())
