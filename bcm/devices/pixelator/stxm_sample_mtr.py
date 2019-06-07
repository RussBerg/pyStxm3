'''
Created on 2014-07-03

@author: bergr
'''
#!/usr/bin/env python

from bcm.devices.motor_qt import Motor_Qt

class sample_abstract_motor(Motor_Qt):
    """
    Represents an abstract motor that connects to a defined set of PV's of an Abstract positioner (Coarse Stepper Motor and Fine piezo motor combined) 
    """

    def __init__(self, prefix, **kwargs):
        """
                	Initialize the scan.

                	name: The name of the scan record.
                	"""
        pass

class sample_motor(Motor_Qt):
    """
    Represents an motor that is typically a piezo motor, either a sample fine stage or a zoneplate X/Y stage 
    """

    def __init__(self, prefix, **kwargs):
        """
                	Initialize the scan.

                	name: The name of the scan record.
                	"""
        pass

class e712_sample_motor(Motor_Qt):
    """
    Represents an motor that is typically a piezo motor, either a sample fine stage or a zoneplate X/Y stage 
    """

    def __init__(self, prefix, **kwargs):
        """
                	Initialize the scan.

                	name: The name of the scan record.
                	"""
        pass
    def get_stage_params(self):
        """
                	Initialize the scan.

                	name: The name of the scan record.
                	"""
        pass
        # dct = {}
        # dct['DigFltBWidth'] = self.get('DigFltBWidth_RBV')
        # dct['DigFltParm1'] = self.get('DigFltParm1_RBV')
        # dct['DigFltParm2'] = self.get('DigFltParm2_RBV')
        # dct['DigFltParm3'] = self.get('DigFltParm3_RBV')
        # dct['DigFltParm4'] = self.get('DigFltParm4_RBV')
        # dct['DigFltParm5'] = self.get('DigFltParm5_RBV')
        # dct['CapSensBParm'] = self.get('CapSensBParm_RBV')
        # dct['CapSensMParm'] = self.get('CapSensMParm_RBV')
        # dct['PTerm'] = self.get('PTerm_RBV')
        # dct['ITerm'] = self.get('ITerm_RBV')
        # dct['DTerm'] = self.get('DTerm_RBV')
        # #dct['SlewRate'] = self.get('SlewRate_RBV')
        # dct['SlewRate'] = self.get('VELO')
        # dct['NotchFreq1'] = self.get('NotchFreq1_RBV')
        # dct['NotchFreq2'] = self.get('NotchFreq2_RBV')
        # dct['NotchReject1'] = self.get('NotchReject1_RBV')
        # dct['NotchReject2'] = self.get('NotchReject2_RBV')
        # dct['NotchBW1'] = self.get('NotchBW1_RBV')
        # dct['NotchBW2'] = self.get('NotchBW2_RBV')
        #
        # return(dct)
            
