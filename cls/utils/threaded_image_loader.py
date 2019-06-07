

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import time
import traceback, sys
import timeit

from guiqwt.styles import AnnotationParam, ImageParam, ImageAxesParam, GridParam, CurveParam #, ItemParameters

from cls.utils.dict_utils import dct_get, dct_put
from cls.utils.roi_dict_defs import *

from cls.plotWidgets.CLSPlotItemBuilder import clsPlotItemBuilder
from cls.utils.fileUtils import get_file_path_as_parts
from cls.scanning.dataRecorder import DataIo
from cls.data_io.stxm_data_io import STXMDataIo
from cls.types.stxmTypes import scan_types
from cls.utils.roi_utils import get_first_sp_db_from_wdg_com

fnames = ['S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922000.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922001.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922002.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922003.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922004.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922005.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922006.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922007.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922008.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922009.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922010.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922011.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922012.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922013.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922014.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922015.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922016.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922017.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922018.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922019.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922020.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922021.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922022.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922023.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922024.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922025.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922026.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922027.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922028.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922029.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922030.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922031.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922032.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922033.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922034.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922035.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922036.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922037.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922038.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922039.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922040.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922041.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922045.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922046.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922047.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922048.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922051.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922054.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922055.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922056.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922057.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922058.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922059.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922060.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922061.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922062.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922063.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922064.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922065.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922066.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922067.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922068.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922069.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922070.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922071.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922072.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922075.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922076.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922077.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922078.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922079.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922081.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922082.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922083.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922084.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922085.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922086.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922093.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922094.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922095.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922096.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922097.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922098.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922099.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922100.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922101.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922102.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922103.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922104.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922105.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922106.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922107.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922108.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922109.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922110.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922111.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922112.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922113.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922114.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922115.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922116.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922117.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922118.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922119.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922120.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922121.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922122.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922123.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922124.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922125.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922126.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922127.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922128.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922129.hdf5',
     'S:/STXM-data/Cryo-STXM/2017/guest/0922/C170922130.hdf5']


make = clsPlotItemBuilder()

class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data

    error
        `tuple` (exctype, value, traceback.format_exc() )

    result
        `object` data returned from processing, anything

    progress
        `int` indicating % progress

    '''
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)


class Worker(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        self.fnames = self.args[0]

        # Add the callback to our kwargs
        kwargs['progress_callback'] = self.signals.progress

    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''

        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done



class ThreadpoolImageLoader(QWidget):


    def __init__(self, *args, **kwargs):
        super(ThreadpoolImageLoader, self).__init__(*args, **kwargs)

        self.counter = 0


        layout = QVBoxLayout()

        self.l = QLabel("Start")
        b = QPushButton("Load_images!")
        b.pressed.connect(self.load_image_items)

        layout.addWidget(self.l)
        layout.addWidget(b)

        #w = QWidget()
        #w.setLayout(layout)
        self.setLayout(layout)

        #self.setCentralWidget(w)

        #self.show()


        self.threadpool = QThreadPool()
        #print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.recurring_timer)
        self.timer.start()



    def get_image_data(self, fnames, addimages=True, counter='counter0', progress_callback=None):
        """
        openfile(): description

        :param fnames: a list of filenames
        :type fnames: list

        :param addimages=False: addimages=False description
        :type addimages=False: addimages=False type

        :returns: None
        """
        image_items = []
        num_files = len(fnames)
        idx = 0
        iidx = 0
        self.data_io = STXMDataIo
        #progbar = self.get_file_loading_progbar(num_files)

        for fname in fnames:
            fname = str(fname)
            data_dir, fprefix, fsuffix = get_file_path_as_parts(fname)
            if(data_dir is None):
                #_logger.error('Problem with file [%s]' % fname)
                return

            if (not isinstance(self.data_io, DataIo)):
                data_io = self.data_io(data_dir, fprefix)
            else:
                #we have been launched from a parent viewer
                self.data_io.update_data_dir(data_dir)
                self.data_io.update_file_prefix(fprefix)
                self.data_io.update_file_path(fname)
                data_io = self.data_io

            start_time = timeit.default_timer()

            entry_dct = data_io.load()
            ekey = list(entry_dct.keys())[0]
            wdg_com = entry_dct[ekey]['WDG_COM']
            nx_datas = data_io.get_NXdatas_from_entry(entry_dct, ekey)
            sp_db = get_first_sp_db_from_wdg_com(wdg_com)
            sp_id = list(entry_dct[ekey]['WDG_COM']['SPATIAL_ROIS'].keys())
            scan_type = entry_dct[ekey]['WDG_COM']['SPATIAL_ROIS'][sp_id[0]]['SCAN_PLUGIN']['SCAN_TYPE']
            rng_x = entry_dct[ekey]['WDG_COM']['SPATIAL_ROIS'][sp_id[0]]['X'][RANGE]
            rng_y = entry_dct[ekey]['WDG_COM']['SPATIAL_ROIS'][sp_id[0]]['Y'][RANGE]

            idx += 1
            iidx += 1
            #progbar.setValue(iidx)
            if(progress_callback is not None):
                progress_callback.emit((float(iidx)/float(num_files)) * 100.0)

            elapsed = timeit.default_timer() - start_time
            #print 'elapsed time = ', elapsed

            if(rng_x > rng_y):
                item_z = rng_x
            else:
                item_z = rng_y

            #if image is not a sample image then just skip it
            if(not (scan_type is scan_types.SAMPLE_IMAGE) and (num_files > 1)):
                continue

            if(counter not in list(nx_datas.keys())):
                #_logger.error('counter [%s] does not exist in the datafile' % counter)
                return
            data = data_io.get_signal_data_from_NXdata(nx_datas, counter)

            if((data.ndim is 3)):
                data = data[0]

            if((data.ndim is not 2)):
                #_logger.error('Data in file [%s] is of wrong dimension, is [%d] should be [2]' % (fname, data.ndim))
                print('Data in file [%s] is of wrong dimension, is [%d] should be [2]' % (fname, data.ndim))
            else:

                wdg_com = data_io.get_wdg_com_from_entry(entry_dct, ekey)
                #self.load_image_data(fname, wdg_com, data, addimages, flipud=False, name_lbl=False, item_z=item_z, show=False)
                item = make.image(data, interpolation='nearest', colormap='gist_gray', title=None)
                #item.set_selectable(True)
                (x1, y1, x2, y2) = dct_get(sp_db, SPDB_RECT)
                self.set_image_parameters(item, x1, y1, x2, y2, title=fprefix[-3:])


                image_items.append(item)

        return(image_items)

    def set_image_parameters(self, imgItem, x1, y1, x2, y2, title=None):
        """
        set_image_parameters(): description

        Use this function to adjust the image parameters such that the x and y axis are
        within the xmin,xmax and ymin,ymax bounds, this is an easy way to display the image
        in microns as per the scan parameters, as well as the fact that if you have a scan with
        a non-square aspect ratio you can still display the scan as a square because the image will
        repeat pixels as necessary in either direction so that the image is displayed in teh min/max
        bounds you set here

        :param imageItem: a image plot item as returned from make.image()
        :type imageItem: a image plot item as returned from make.image()

        :param x1: min x that the image will be displayed
        :type x1: int

        :param y1: max x that the image will be displayed
        :type y1: int

        :param x2: min y that the image will be displayed
        :type x2: int

        :param y2: max y that the image will be displayed
        :type y2: int

        :returns:  None

        .. todo::
        there are many other image params that could be set in teh future, for now only implemented min/max
        ImageParam:
            Image title: Image
            Alpha channel: False
            Global alpha: 1.0
            Colormap: gist_gray
            Interpolation: None (nearest pixel)
            _formats:
              X-Axis: %.1f
              Y-Axis: %.1f
              Z-Axis: %.1f
            Background color: #000000
            _xdata:
              x|min: -
              x|max: -
            _ydata:
              y|min: -
              y|max: -

        """
        iparam = ImageParam()
        iparam.label = title
        iparam.colormap = imgItem.get_color_map_name()
        iparam.xmin = x1
        iparam.ymin = y1
        iparam.xmax = x2
        iparam.ymax = y2
        self.zoom_rngx = float(x2 - x1)
        self.zoom_rngy = float(y2 - y1)

        axparam = ImageAxesParam()
        axparam.xmin = x1
        axparam.ymin = y1
        axparam.xmax = x2
        axparam.ymax = y2

        imgItem.set_item_parameters({"ImageParam": iparam})
        imgItem.set_item_parameters({"ImageAxesParam": axparam})

    def progress_fn(self, n):
        print(("%d%% done" % n))

    def generate_images(self, fnames, progress_callback):
        image_items = self.get_image_data(fnames, progress_callback=progress_callback)
        #print 'generate_images: all items generated'
        #print image_items
        return(image_items)

    # def make_image(self, progress_callback):
    #     item = make.image(self.data, interpolation='nearest', colormap='gist_gray', title=None)

    def thread_complete(self):
        print("THREAD COMPLETE!")

    def load_image_items(self, fnames, result_fn, progress_fn=None, thread_complete_fn=None):
        #assert isinstance(xdata, (tuple, list)) and len(xdata) == 2
        #assert isinstance(ydata, (tuple, list)) and len(ydata) == 2
        assert isinstance(fnames, (list))
        assert callable(result_fn)

        worker = Worker(self.generate_images, fnames) # Any other args, kwargs are passed to the run function
        worker.signals.result.connect(result_fn)

        if (progress_fn is None):
            worker.signals.progress.connect(self.progress_fn)
        else:
            worker.signals.progress.connect(progress_fn)

        if(thread_complete_fn is None):
            worker.signals.finished.connect(self.thread_complete)
        else:
            worker.signals.finished.connect(thread_complete_fn)

        # Execute
        self.threadpool.start(worker)


    def recurring_timer(self):
        self.counter +=1
        self.l.setText("Counter: %d" % self.counter)

def get_file_loading_progbar(max):
    progbar = QProgressBar()
    progbar.setFixedWidth(300)
    progbar.setWindowTitle("generating a composite image")
    progbar.setAutoFillBackground(True)
    progbar.setMinimum(0)
    progbar.setMaximum(max)
    ss = """QProgressBar 
          {        
                    border: 5px solid rgb(100,100,100);
                    border-radius: 1 px;
                    text-align: center;
          }
        QProgressBar::chunk
        {
                    background-color:  rgb(114, 148, 240);
                    width: 20 px;
        }"""

    progbar.setStyleSheet(ss)

    return(progbar)



def progress_fn(n):
    global progbar
    progbar.setValue(n)
    print(("EXTERNAL: progress: %d%% done" % n))

def result_output(image_items):
    print('EXTERNAL: result_output:', image_items)

def thread_complete():
    global progbar
    print("EXTERNAL: THREAD COMPLETE!")
    progbar.hide()



if __name__ == "__main__":
    app = QApplication([])
    progbar = get_file_loading_progbar(len(fnames))
    window = ThreadpoolImageLoader()
    window.load_image_items(fnames, progress_fn=progress_fn, result_fn=result_output, thread_complete_fn=thread_complete)
    progbar.show()
    app.exec_()
