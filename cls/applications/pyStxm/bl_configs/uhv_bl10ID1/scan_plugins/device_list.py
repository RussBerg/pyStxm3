
from ophyd import EpicsMotor
from bcm.devices import Motor_Qt
from bcm.devices import BaseDevice
from bcm.devices.dev_categories import dev_categories
from bcm.devices.device_names import *
from test_detector import PointDetectorDevice
# ES = endstation temperatures

def devs_as_list():
    dlst = []
    for t in dev_dct[dev_categories.TEMPERATURES].keys():
        dlst.append(dev_dct[dev_categories.TEMPERATURES][t])

    for t in dev_dct[dev_categories.PRESSURES].keys():
        dlst.append(dev_dct[dev_categories.PRESSURES][t])

    for t in dev_dct[dev_categories.SIGNALS].keys():
        dlst.append(dev_dct[dev_categories.SIGNALS][t])

    for t in dev_dct[dev_categories.POSITIONERS].keys():
        dlst.append(dev_dct[dev_categories.POSITIONERS][t])

    for t in dev_dct[dev_categories.DETECTORS].keys():
        dlst.append(dev_dct[dev_categories.DETECTORS][t])

    return(dlst)

def categorize_devices(dev_dct, category, units):
    for k, dev in dev_dct.items():
        dev.set_dev_category(category)
        dev.set_dev_units(units)

def add_category_to_device(dev_dct, category):
    for k, dev in dev_dct.items():
        dev.category = lambda: None
        setattr(dev.category, 'category', category)
        #dev.set_dev_units(units)




dev_dct = {}
dev_dct[dev_categories.TEMPERATURES] = {}
dev_dct[dev_categories.PRESSURES] = {}
dev_dct[dev_categories.SIGNALS] = {}
dev_dct[dev_categories.POSITIONERS] = {}
dev_dct[dev_categories.DETECTORS] = {}

dev_dct[dev_categories.TEMPERATURES]['TM1610-3-I12-01'] = BaseDevice('TM1610-3-I12-01', name='Turbo_cooling_water', rd_only=True).get_ophyd_device()
dev_dct[dev_categories.TEMPERATURES]['TM1610-3-I12-30'] = BaseDevice('TM1610-3-I12-30', name='Sample_Coarse_Y', rd_only=True).get_ophyd_device()
dev_dct[dev_categories.TEMPERATURES]['TM1610-3-I12-32'] = BaseDevice('TM1610-3-I12-32', name='Detector_Y', rd_only=True).get_ophyd_device()
dev_dct[dev_categories.TEMPERATURES]['TM1610-3-I12-21'] = BaseDevice('TM1610-3-I12-21', name='Chamber_temp_1', rd_only=True).get_ophyd_device()
dev_dct[dev_categories.TEMPERATURES]['TM1610-3-I12-22'] = BaseDevice('TM1610-3-I12-22', name='Chamber_temp_2', rd_only=True).get_ophyd_device()
dev_dct[dev_categories.TEMPERATURES]['TM1610-3-I12-23'] = BaseDevice('TM1610-3-I12-23', name='Chamber_temp_3', rd_only=True).get_ophyd_device()
dev_dct[dev_categories.TEMPERATURES]['TM1610-3-I12-24'] = BaseDevice('TM1610-3-I12-24', name='Chamber_temp_4', rd_only=True).get_ophyd_device()

categorize_devices( dev_dct[dev_categories.TEMPERATURES], dev_categories.TEMPERATURES, 'degC')

dev_dct[dev_categories.PRESSURES]['FRG1610-3-I12-01:vac:p'] = BaseDevice('FRG1610-3-I12-01:vac:p', name='Chamber_pressure', rd_only=True).get_ophyd_device()
dev_dct[dev_categories.PRESSURES]['TCG1610-3-I12-03:vac:p'] = BaseDevice('TCG1610-3-I12-03:vac:p', name='Turbo_backing_pressure', rd_only=True).get_ophyd_device()
dev_dct[dev_categories.PRESSURES]['TCG1610-3-I12-04:vac:p'] = BaseDevice('TCG1610-3-I12-04:vac:p', name='Load_lock_pressure', rd_only=True).get_ophyd_device()
dev_dct[dev_categories.PRESSURES]['TCG1610-3-I12-05:vac:p'] = BaseDevice('TCG1610-3-I12-05:vac:p', name='Rough_line_pressure', rd_only=True).get_ophyd_device()

categorize_devices( dev_dct[dev_categories.PRESSURES], dev_categories.PRESSURES, 'torr')

dev_dct[dev_categories.SIGNALS]['SR_RING_CURRENT'] = BaseDevice('PCT1402-01:mA:fbk', name='SR_Current', rd_only=True).get_ophyd_device()

categorize_devices( dev_dct[dev_categories.SIGNALS], dev_categories.SIGNALS, 'mA')






# dev_dct[dev_categories.POSITIONERS][DNM_SAMPLE_FINE_X] = sample_motor('IOC:m100', name='m100', pos_set='ES')
# self.msg_splash("connecting to: [%s]" % DNM_SAMPLE_FINE_Y)
# # dev_dct[dev_categories.POSITIONERS][DNM_SAMPLE_FINE_Y] = sample_motor('IOC:m101', name='m101', pos_set='ES')
dev_dct[dev_categories.POSITIONERS][DNM_ZONEPLATE_X] = Motor_Qt( 'IOC:m103', name='m103', pos_set='ES')
dev_dct[dev_categories.POSITIONERS][DNM_ZONEPLATE_Y] = Motor_Qt( 'IOC:m104', name='m104', pos_set='ES')
dev_dct[dev_categories.POSITIONERS][DNM_OSA_X] = Motor_Qt('IOC:m904', name='m904', pos_set='ES')
# dev_dct[dev_categories.POSITIONERS][DNM_OSA_Y] = Motor_Qt('IOC:m905', name='m905', pos_set='ES')
# dev_dct[dev_categories.POSITIONERS][DNM_OSA_Z] = Motor_Qt('IOC:m906', name='m906', pos_set='ES', collision_support=True)
# dev_dct[dev_categories.POSITIONERS][DNM_OSA_Z_BASE] = Motor_Qt('IOC:m906', name='m906')
#

# dev_dct[dev_categories.POSITIONERS][DNM_ZONEPLATE_X] = EpicsMotor( 'IOC:m103', name='m103')
# dev_dct[dev_categories.POSITIONERS][DNM_ZONEPLATE_Y] = EpicsMotor( 'IOC:m104', name='m104')
# dev_dct[dev_categories.POSITIONERS][DNM_OSA_X] = EpicsMotor('IOC:m904', name='m904')
# dev_dct[dev_categories.POSITIONERS][DNM_OSA_Y] = EpicsMotor('IOC:m905', name='m905')
# dev_dct[dev_categories.POSITIONERS][DNM_OSA_Z] = EpicsMotor('IOC:m906', name='m906')

#add_category_to_device(dev_dct[dev_categories.POSITIONERS], dev_categories.POSITIONERS)


#categorize_devices( dev_dct[dev_categories.POSITIONERS], dev_categories.POSITIONERS, 'um')

dev_dct[dev_categories.DETECTORS]['point_det'] = PointDetectorDevice('uhvCI:counter:', name='point_det')


lst = devs_as_list()

