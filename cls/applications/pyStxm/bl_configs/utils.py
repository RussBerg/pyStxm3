
import os
from bcm.devices import BaseDevice


def make_basedevice(cat, nm, desc='', units='', rd_only=False, devcfg=None):
    devcfg.msg_splash("connecting to %s: [%s]" % (cat, nm))
    dev = BaseDevice(nm, desc=desc, units=units, rd_only=rd_only)
    return (dev)

def get_config_name(fname):
    nm = fname.split(os.path.sep)[-1].replace('.py', '')
    return(nm)