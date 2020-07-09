
import time
import numpy as np
import random
from epics import PV
pressures = {'SIM_CCG1410-01:vac:p': ('float', 'ai', 3.15773e-11),
'SIM_CCG1410-I00-01:vac:p': ('float', 'ai', .48551e-09),
'SIM_CCG1410-I00-02:vac:p': ('float', 'ai', 4.59066e-10),
'SIM_CCG1610-1-I00-02:vac:p': ('float', 'ai', 5.50333e-10),
'SIM_CCG1610-1-I00-03:vac:p': ('float', 'ai', 5.21795e-10),
'SIM_CCG1610-3-I12-01:vac:p': ('float', 'ai', 5.44816e-10),
'SIM_CCG1610-I10-01:vac:p': ('float', 'ai', 2.63027e-09),
'SIM_CCG1610-I10-02:vac:p': ('float', 'ai', 3.17139e-09),
'SIM_CCG1610-I10-03:vac:p': ('float', 'ai', .29942e-09),
'SIM_CCG1610-I10-04:vac:p': ('float', 'ai', 9.88553e-10),
'SIM_CCG1610-I12-01:vac:p': ('float', 'ai', .16815e-09),
'SIM_CCG1610-I12-02:vac:p': ('float', 'ai', 8.78517e-10),
'SIM_FRG1610-3-I12-01:vac:p': ('float', 'ai',  .00546939),
'SIM_HCG1610-1-I00-01:vac:p': ('float', 'ai', 5.25563e-10),
'SIM_TCG1610-3-I12-03:vac:p': ('float', 'ai', 5000),
'SIM_TCG1610-3-I12-04:vac:p': ('float', 'ai',  .0190631),
'SIM_TCG1610-3-I12-05:vac:p': ('float', 'ai', 5000)}

temps = {'SIM_TM1610-3-I12-01': ('float', 'ai', 25.125),
'SIM_TM1610-3-I12-21': ('float', 'ai', 10.1),
'SIM_TM1610-3-I12-22': ('float', 'ai', 24.6),
'SIM_TM1610-3-I12-23': ('float', 'ai', 98.5),
'SIM_TM1610-3-I12-24': ('float', 'ai', 24.2),
'SIM_TM1610-3-I12-30': ('float', 'ai', 23.8),
'SIM_TM1610-3-I12-32': ('float', 'ai', 23.5)}

#apd = PV('SIM_uhvPMT:ctr:SingleValue_RBV')
apd = PV('SIM_BL1610-I10-PMT:ctr:SingleValue_RBV')

def connect_pvs(pv_lst):
    dct = {}
    for p in pv_lst:
        dct[p] = PV(p)
    return(dct)

def do_sim(prs, tmps):
    arr = np.random.randint(0, 65535, 5000)
    i = 0
    while True:
        apd.put(arr[i])
   
        # for nm,pv in prs.items():
        #     fbk = pv.get()
        #     noise = (1.0 +(random.uniform(-1.0, 1.0) *0.15)) * fbk
        #     pv.put(noise)
        # for nm,pv in tmps.items():
        #     fbk = pv.get()
        #     noise = (1.0 +(random.uniform(-1.0, 1.0) *0.15)) * fbk
        #     pv.put(noise)
        time.sleep(0.3)
        i += 1
        if(i >= 5000):
            i = 0



if __name__ == '__main__':
    prs = connect_pvs(pressures)
    tmps = connect_pvs(temps)
    do_sim(prs, tmps)

