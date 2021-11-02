
#import logging
# from ..utils import enum
import os

from ophyd import EpicsSignalRO, Device, EpicsSignal

from ophyd.areadetector.base import (ADBase, ADComponent as C, ad_group, EpicsSignalWithRBV as SignalWithRBV)
# from ophyd.signal import (EpicsSignalRO, EpicsSignal)
# from ophyd.device import DynamicDeviceComponent as DDC
import ophyd
from ophyd.areadetector.plugins import HDF5Plugin, TIFFPlugin
from ophyd.areadetector.trigger_mixins import SingleTrigger
from ophyd.areadetector.filestore_mixins import (FileStoreHDF5IterativeWrite  )
from ophyd.areadetector import (GreatEyesDetector, GreatEyesDetectorCam,
                                ImagePlugin, TIFFPlugin, StatsPlugin,
                                ProcessPlugin, ROIPlugin, TransformPlugin)
from ophyd.areadetector.filestore_mixins import FileStoreTIFFIterativeWrite, FileStoreHDF5SingleIterativeWrite

from ophyd.areadetector.cam import SimDetectorCam

class GreateyesTransform(TransformPlugin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    type = C(EpicsSignal,'Type')

class TIFFPluginWithFileStore(TIFFPlugin, FileStoreTIFFIterativeWrite):
    """Add this as a component to detectors that write TIFFs."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

# class GE_HDF5_Plugin(HDF5Plugin, FileStoreHDF5IterativeWrite  ):
#      pass

class GE_HDF5_Plugin(HDF5Plugin, FileStoreHDF5SingleIterativeWrite  ):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


dest = '/home/bergr/SM/test_data'
# = '/opt/test_data'

class SimGreatEyesCCDTiff( SingleTrigger, GreatEyesDetector):
    _html_docs = ['GreatEyesDoc.html']
    file_plugin = C(TIFFPluginWithFileStore, 'TIFF1:',
             write_path_template=dest,
             read_path_template=dest,
             read_attrs=[],
             root='/home/bergr/SM/')

    cam = C(GreatEyesDetectorCam, 'cam1:')
    image = C(ImagePlugin, 'image1:')
    stats1 = C(StatsPlugin, 'Stats1:')
    stats2 = C(StatsPlugin, 'Stats2:')
    stats3 = C(StatsPlugin, 'Stats3:')
    stats4 = C(StatsPlugin, 'Stats4:')
    stats5 = C(StatsPlugin, 'Stats5:')
    trans1 = C(GreateyesTransform, 'Trans1:')
    roi1 = C(ROIPlugin, 'ROI1:')
    roi2 = C(ROIPlugin, 'ROI2:')
    roi3 = C(ROIPlugin, 'ROI3:')
    roi4 = C(ROIPlugin, 'ROI4:')
    proc1 = C(ProcessPlugin, 'Proc1:')

    def __init__(self, prefix, name):
        super(SimGreatEyesCCD, self).__init__(prefix=prefix, name=name)
        self.stage_sigs['cam.image_mode'] = 0
        #self.file_plugin.warmup()
        #print(self.trigger)

    def stage(self, *args, **kwargs):
        # init some settings
        self.file_plugin.array_counter.put(0)


        return (super().stage(*args, **kwargs))

    def get_name(self):
        return(self.name)

    def get_position(self):
        return(0.0)

    def describe(self):
        '''Describe details for the flyer collect() method'''
        desc = dict()
        d = {self.name: desc}
        #print('describe_collect: ', d)
        return d

class SimGreatEyesCCD( SingleTrigger, GreatEyesDetector):
    _html_docs = ['GreatEyesDoc.html']
    file_plugin = C(GE_HDF5_Plugin, suffix='HDF1:',
                    write_path_template=dest,
                    read_path_template='C:\\tmp',
                    root='C:\\'
                    )

    cam = C(GreatEyesDetectorCam, 'cam1:')
    image = C(ImagePlugin, 'image1:')
    stats1 = C(StatsPlugin, 'Stats1:')
    stats2 = C(StatsPlugin, 'Stats2:')
    stats3 = C(StatsPlugin, 'Stats3:')
    stats4 = C(StatsPlugin, 'Stats4:')
    stats5 = C(StatsPlugin, 'Stats5:')
    trans1 = C(GreateyesTransform, 'Trans1:')
    roi1 = C(ROIPlugin, 'ROI1:')
    roi2 = C(ROIPlugin, 'ROI2:')
    roi3 = C(ROIPlugin, 'ROI3:')
    roi4 = C(ROIPlugin, 'ROI4:')
    proc1 = C(ProcessPlugin, 'Proc1:')

    def __init__(self, prefix, name):
        super(SimGreatEyesCCD, self).__init__(prefix=prefix, name=name)
        self.stage_sigs['cam.image_mode'] = 0
        self.file_plugin.warmup()
        #print(self.trigger)

    def stage(self, *args, **kwargs):

        #init some settings
        self.file_plugin.array_counter.put(0)
        #self.file_plugin.compression.put(6) # set to LZ4

        return(super().stage(*args, **kwargs))

    def get_name(self):
        return(self.name)

    def get_position(self):
        return(0.0)

    def describe(self):
        '''Describe details for the flyer collect() method'''
        desc = dict()
        d = {self.name: desc}
        #print('describe_collect: ', d)
        return d

class GreatEyesCCD(SingleTrigger, GreatEyesDetector):
    _html_docs = ['GreatEyesDoc.html']
    # file_plugin = C(GE_HDF5_Plugin, suffix='HDF1:',
    #                 write_path_template=dest,
    #                 read_path_template=dest,
    #                 root=dest)
    # file_plugin = C(GE_HDF5_Plugin, suffix='HDF1:',
    #                 write_path_template='/home/bergr/SM/test_data')
    file_plugin = C(GE_HDF5_Plugin, suffix='HDF1:',
                    read_path_template='S:\\SM\\test_data',
                    write_path_template='/nas/sm-user/SM/test_data',
                    root='S:\\')
    cam = C(GreatEyesDetectorCam, 'cam1:')
    image = C(ImagePlugin, 'image1:')
    stats1 = C(StatsPlugin, 'Stats1:')
    stats2 = C(StatsPlugin, 'Stats2:')
    stats3 = C(StatsPlugin, 'Stats3:')
    stats4 = C(StatsPlugin, 'Stats4:')
    stats5 = C(StatsPlugin, 'Stats5:')
    trans1 = C(GreateyesTransform, 'Trans1:')
    roi1 = C(ROIPlugin, 'ROI1:')
    roi2 = C(ROIPlugin, 'ROI2:')
    roi3 = C(ROIPlugin, 'ROI3:')
    roi4 = C(ROIPlugin, 'ROI4:')
    proc1 = C(ProcessPlugin, 'Proc1:')

    def __init__(self, prefix, name):
        super(GreatEyesCCD, self).__init__(prefix=prefix, name=name)
        #these will appear in databroker documents
        #self.read_attrs = ['file_plugin', 'stats1.total']
        self.read_attrs = ['file_plugin']


    def stage(self, *args, **kwargs):
        # init some settings
        self.file_plugin.array_counter.put(0)

        return (super().stage(*args, **kwargs))

    def get_name(self):
        return(self.name)

    def get_position(self):
        return(0.0)

    def get_temperature(self):
        val = self.cam.temperature_actual.get()
        return(val)

    # def describe(self):
    #     '''Describe details for the flyer collect() method'''
    #     desc = dict()
    #     d = {self.name: desc}
    #     #print('describe_collect: ', d)
    #     return d


def go():
    ccd = SimGreatEyesCCD('SIM_CCD1610-I10-02:', name='SIM_GE_CCD')
    # ccd = GreatEyesDetector('SIMCCD1610-I10-02:', name='SIM_GE_CCD')
    # ccd.cam.stage()
    # ccd.cam.trigger()
    print('areaDetector main done')
    # RE = RunEngine({})
    # RE(bp.count([ccd]))
    ccd.stage()
    ccd.trigger()
    ccd.unstage()

if __name__ == '__main__':


    from bluesky import RunEngine
    import bluesky.plans as bp
    from databroker import Broker

    db = Broker.named('mongo_databroker')
    RE = RunEngine({})
    RE.subscribe(db.insert)
    #ccd = SimGreatEyesCCD('SIM_CCD1610-I10-02:', name='SIM_GE_CCD')
    ccd = GreatEyesCCD('CCD1610-01:', name='GE_CCD')
    print(ccd.summary())
    #ccd.read_attrs = ['file_plugin']
    uid, = RE(bp.count([ccd]))
    hdr = db[uid]
    docs = hdr.documents()
    #next(docs)  # repeat it until the end of iterator
    #hdr = db['<your uid>']
    docs = hdr.documents()
    for name, doc in docs:
        if name in ['resource', 'datum']:
            print(name, doc)
    #

    #print(ccd.describe())
    # ccd.stage()
    # # ccd.trigger()
    # # ccd.read()
    # ccd.unstage()
