'''
Created on 2014-07-03

@author: bergr
'''
#!/usr/bin/env python

from .motor_qt import Motor_Qt

# class sample_motor(epics.Device):
# 	"""
# 	Sample motor used for scanning in the stxm
# 	"""
# 
# 	attrs = ('SET', 'VAL', 'Mode', 'Mode_RBV', 'ScanStart', 'ScanStop', 'MarkerStart', 'MarkerStop', 'SetMarker', 'ServoPower', 'ServoPower_RBV')
# 
# 	def __init__(self, prefix, **kwargs):
# 		if prefix.endswith('.'):
# 			prefix = prefix[:-1]
# 		epics.Device.__init__(self, prefix, delim=':',
# 							  attrs=self.attrs,
# 							  **kwargs)
# 		

class sample_abstract_motor(Motor_Qt):
    """
    Represents an abstract motor that connects to a defined set of PV's of an Abstract positioner (Coarse Stepper Motor and Fine piezo motor combined) 
    """

    attrs = ('VAL')
    

    def __init__(self, prefix, **kwargs):
        if prefix.endswith('.'):
            prefix = prefix[:-1]
        Motor_Qt.__init__(self, prefix,
                              **kwargs)
        myattrs = (':Mode', ':Mode_RBV', ':ScanStart', ':ScanStop', ':MarkerStart', ':MarkerStop', ':SetMarker', ':AtzSetCoarsePos')
        
        for attr in myattrs:
            self.add_pv('%s%s' % (prefix, attr), attr=attr[1:])

class sample_motor(Motor_Qt):
    """
    Represents an motor that is typically a piezo motor, either a sample fine stage or a zoneplate X/Y stage 
    """

    attrs = ('VAL')
    

    def __init__(self, prefix, **kwargs):
        if prefix.endswith('.'):
            prefix = prefix[:-1]
        Motor_Qt.__init__(self, prefix,
                              **kwargs)
        myattrs = (':Mode', ':Mode_RBV', ':ScanStart', ':ScanStop', ':MarkerStart', ':MarkerStop', ':SetMarker', ':ServoPower', \
				':ServoPower_RBV', ':OutputVolt_RBV', ':AutoZero')
        
        for attr in myattrs:
            self.add_pv('%s%s' % (prefix, attr), attr=attr[1:])


class e712_sample_motor(Motor_Qt):
    """
    Represents an motor that is typically a piezo motor, either a sample fine stage or a zoneplate X/Y stage 
    """

    attrs = ('VAL')



    def __init__(self, prefix, **kwargs):
        if prefix.endswith('.'):
            prefix = prefix[:-1]
        Motor_Qt.__init__(self, prefix,
                          **kwargs)
        myattrs = (
        ':Mode', ':Mode_RBV', ':ScanStart', ':ScanStop', ':MarkerStart', ':MarkerStop', ':SetMarker', ':ServoPower', \
        ':ServoPower_RBV', ':OutputVolt_RBV', ':AutoZero', ':DigFltBWidth_RBV',':DigFltParm1_RBV',':DigFltParm2_RBV',':DigFltParm3_RBV' , \
        ':DigFltParm4_RBV' ,':DigFltParm5_RBV' ,':CapSensBParm_RBV',':CapSensMParm_RBV',':PTerm_RBV', ':ITerm_RBV', ':DTerm_RBV', ':SlewRate_RBV',':NotchFreq1_RBV', \
        ':NotchFreq2_RBV', ':NotchReject1_RBV',':NotchReject2_RBV', ':NotchBW1_RBV',':NotchBW2_RBV')

        for attr in myattrs:
            self.add_pv('%s%s' % (prefix, attr), attr=attr[1:])

    def get_stage_params(self):
        dct = {}
        dct['DigFltBWidth'] = self.get('DigFltBWidth_RBV')
        dct['DigFltParm1'] = self.get('DigFltParm1_RBV')
        dct['DigFltParm2'] = self.get('DigFltParm2_RBV')
        dct['DigFltParm3'] = self.get('DigFltParm3_RBV')
        dct['DigFltParm4'] = self.get('DigFltParm4_RBV')
        dct['DigFltParm5'] = self.get('DigFltParm5_RBV')
        dct['CapSensBParm'] = self.get('CapSensBParm_RBV')
        dct['CapSensMParm'] = self.get('CapSensMParm_RBV')
        dct['PTerm'] = self.get('PTerm_RBV')
        dct['ITerm'] = self.get('ITerm_RBV')
        dct['DTerm'] = self.get('DTerm_RBV')
        #dct['SlewRate'] = self.get('SlewRate_RBV')
        dct['SlewRate'] = self.get('velocity')
        dct['NotchFreq1'] = self.get('NotchFreq1_RBV')
        dct['NotchFreq2'] = self.get('NotchFreq2_RBV')
        dct['NotchReject1'] = self.get('NotchReject1_RBV')
        dct['NotchReject2'] = self.get('NotchReject2_RBV')
        dct['NotchBW1'] = self.get('NotchBW1_RBV')
        dct['NotchBW2'] = self.get('NotchBW2_RBV')

        return(dct)
            

if __name__ == "__main__":
    
    mtr = sample_motor('IOC:m100')
    print(mtr.get('RBV'))
    