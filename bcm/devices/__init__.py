#the device files list in this directory show what the interface for each device
# must support, these are not for inheriting

USE_EPICS = False
USE_TANGO = False
USE_PIXELATOR = False
USE_OPHYD_EPICS = True
USE_OPHYD_SIM = False



if(USE_EPICS):
    from .epics.base import BaseDevice
    from .epics.aio import basedevice as basedevice
    from .epics.camera import camera
    from .epics.counter import BaseGate, BaseCounter
    from .epics.shutter import PvShutter
    from .epics.dio import digitalIO
    from .epics.mbbi import Mbbi
    from .epics.mbbo import Mbbo
    from .epics.mca import Mca
    from .epics.motor_qt import Motor_Qt
    from .epics.scan import Scan
    from .epics.stringin import Stringin
    from .epics.stxm_sample_mtr import sample_abstract_motor, sample_motor, e712_sample_motor
    from .epics.transform import Transform
    from .epics.waveform import Waveform

elif(USE_OPHYD_EPICS):

    from .ophyd.base_device import BaseDevice
    from .ophyd.base_object import BaseObject
    #from .ophyd.base_sig_io import BaseSignalIO as aio

    from .ophyd.camera import camera
    from .ophyd.mbbi import Mbbi
    from .ophyd.mbbo import Mbbo
    from .ophyd.bo import Bo
    from .ophyd.shutter import PvShutter
    from .ophyd.scan import Scan
    from .ophyd.transform import Transform
    from .ophyd.dio import digitalIO
    from .ophyd.counter import BaseGate, BaseCounter
    from .ophyd.stringin import Stringin
    from .ophyd.waveform import Waveform
    from .ophyd.motor import Motor_Qt
    from .ophyd.stxm_sample_mtr import sample_abstract_motor, sample_motor, e712_sample_motor
    from .ophyd.pi_e712 import E712WGDevice

elif(USE_OPHYD_SIM):

    from .ophyd_sim.base_device import BaseDevice
    from .ophyd_sim.base_object import BaseObject
    #from .ophyd.base_sig_io import BaseSignalIO as aio

    from .ophyd_sim.camera import camera
    from .ophyd_sim.mbbi import Mbbi
    from .ophyd_sim.mbbo import Mbbo
    from .ophyd_sim.shutter import PvShutter
    from .ophyd_sim.scan import Scan
    from .ophyd_sim.transform import Transform
    from .ophyd_sim.dio import digitalIO
    from .ophyd_sim.counter import BaseGate, BaseCounter
    from .ophyd_sim.stringin import Stringin
    from .ophyd_sim.waveform import Waveform
    from .ophyd_sim.motor import Motor_Qt
    from .ophyd_sim.stxm_sample_mtr import sample_abstract_motor, sample_motor, e712_sample_motor
    from .ophyd_sim.pi_e712 import E712WGDevice
    
elif(USE_TANGO):
    pass
elif(USE_PIXELATOR):
    pass
else:
    print('ERROR: No DCS configured')




