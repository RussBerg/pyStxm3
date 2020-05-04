
#import logging
# from ..utils import enum
# from ophyd.areadetector.base import (ADBase, ADComponent as C, ad_group, EpicsSignalWithRBV as SignalWithRBV)
# from ophyd.signal import (EpicsSignalRO, EpicsSignal)
# from ophyd.device import DynamicDeviceComponent as DDC

from ophyd.areadetector.cam import GreatEyesDetectorCam, SimDetectorCam

class SimGreatEyesCCD(SimDetectorCam):
    _html_docs = ['GreatEyesDoc.html']

    def __init__(self, prefix, name):
        super(SimGreatEyesCCD, self).__init__(prefix=prefix, name=name)

    def get_name(self):
        return(self.name)

    def get_position(self):
        return(0.0)

class GreatEyesCCD(GreatEyesDetectorCam):
    _html_docs = ['GreatEyesDoc.html']

    # bandwidth = C(EpicsSignal, 'Bandwidth')
    # binning_mode = C(SignalWithRBV, 'BinningMode')
    # convert_pixel_format = C(SignalWithRBV, 'ConvertPixelFormat')
    # corrupt_frames = C(EpicsSignalRO, 'CorruptFrames_RBV')
    # driver_dropped = C(EpicsSignalRO, 'DriverDropped_RBV')
    # dropped_frames = C(EpicsSignalRO, 'DroppedFrames_RBV')
    # firmware_version = C(EpicsSignal, 'FirmwareVersion')
    # format7_mode = C(SignalWithRBV, 'Format7Mode')
    # frame_rate = C(SignalWithRBV, 'FrameRate')
    # max_packet_size = C(EpicsSignal, 'MaxPacketSize')
    # packet_delay_actual = C(EpicsSignal, 'PacketDelayActual')
    # packet_delay = C(SignalWithRBV, 'PacketDelay')
    # packet_size_actual = C(EpicsSignal, 'PacketSizeActual')
    # packet_size = C(SignalWithRBV, 'PacketSize')
    # pixel_format = C(SignalWithRBV, 'PixelFormat')
    # read_status = C(EpicsSignal, 'ReadStatus')
    # serial_number = C(EpicsSignal, 'SerialNumber')
    # skip_frames = C(SignalWithRBV, 'SkipFrames')
    # software_trigger = C(EpicsSignal, 'SoftwareTrigger')
    # software_version = C(EpicsSignal, 'SoftwareVersion')
    # strobe_delay = C(SignalWithRBV, 'StrobeDelay')
    # strobe_duration = C(SignalWithRBV, 'StrobeDuration')
    # strobe_enable = C(SignalWithRBV, 'StrobeEnable')
    # strobe_polarity = C(SignalWithRBV, 'StrobePolarity')
    # strobe_source = C(SignalWithRBV, 'StrobeSource')
    # time_stamp_mode = C(SignalWithRBV, 'TimeStampMode')
    # transmit_failed = C(EpicsSignalRO, 'TransmitFailed_RBV')
    # trigger_polarity = C(SignalWithRBV, 'TriggerPolarity')
    # trigger_source = C(SignalWithRBV, 'TriggerSource')
    # video_mode = C(SignalWithRBV, 'VideoMode')

    def __init__(self, prefix, name):
        super(GreatEyesCCD, self).__init__(prefix=prefix, name=name)

    def get_name(self):
        return(self.name)

    def get_position(self):
        return(0.0)