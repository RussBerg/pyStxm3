from cls.utils.enum_utils import Enum
#E712_START_MODES = Enum('DO_NOT_START','IMEDDIATELY',"EXTERNAL_TRIG')
E712_WVGEN_START_MODES = Enum(DO_NOT_START=0, IMEDDIATELY=1, EXTERNAL_TRIG=2)
E712_WVGEN_FLAGS = Enum(USE_AND_REINIT=64, USE=128, START_AT_ENDPOS=256)
E712_TRIG_MODES = Enum(POS_DISTANCE=0, ON_TARGET=2,MINMAX_THRESHOLD=3,GENERATOR=4)

def gen_set_calc_ddl_processing_params_cmnd_lst(tblid):
    lst = []
    lst.append('CCL 1 advanced')
    lst.append('DPO %d' % tblid)
    lst.append('CCL 0 advanced')
    return(lst)

def gen_set_wav_gen_start_stop_mode_cmnd(tblid, flags, _new=True):
    '''
    as per page 95,
    PZ233E Commands Manual E-711/E-712 Modular Digital
    Multi-Channel Piezo COntroller System
    Release: 1.0.1 Date 27 July 2011
    :param tblid:
    :param flags:
    :param _new:
    :return:
    '''
    s = ''
    if(_new):
        s += 'WGO'
    #set table id
    s += ' %d' % tblid
    #add up startmode and flags
    s += ' %d' % flags
    return(s)
def gen_get_wav_gen_start_stop_mode_cmnd(wavegen_id):
    '''
    :param wavegen_id:
    :return:
    '''
    s = 'WGO? %d' % wavegen_id
    return(s)

def gen_clear_wav_table_cmnd(tbl_id):
    '''
    :param tbl_id:
    :return:
    '''
    s = 'WCL %d' % (tbl_id)
    return(s)

def gen_set_wav_gen_cycles_cmnd(wavegen_id, cycles):
    '''
    :param wavegen_id:
    :param cycles:
    :return:
    '''
    s = 'WGC %d %d' % (wavegen_id, cycles)
    return(s)
def gen_get_wav_gen_cycles_cmnd(wavegen_id, cycles):
    '''
    :param wavegen_id:
    :param cycles:
    :return:
    '''
    s = 'WGC? %d' % (wavegen_id)
    return(s)

def gen_set_wavetable_offset_cmnd(wavegen_id, offset):
    '''
    :param wavegen_id:
    :param offset:
    :return:
    '''
    return('WOS %d %f' % (wavegen_id, offset))
def gen_get_wavetable_offset_cmnd(wavegen_id):
    '''
    :param wavegen_id:
    :return:
    '''
    return('WOS? %d' % (wavegen_id))

def gen_set_wav_table_to_gen_con_cmnd(wavegen_id, tbl_id):
    '''
    :param wavegen_id:
    :param tbl_id:
    :return:
    '''
    s = 'WSL %d %d' % (wavegen_id, tbl_id)
    return(s)

def gen_get_wav_table_to_gen_con_cmnd(wavegen_id):
    '''
    :param wavegen_id:
    :return:
    '''
    s = 'WSL? %d' % (wavegen_id)
    return(s)

def gen_set_wav_table_rate_cmnd(wavegen_id, tbl_rate, interpolation_type=1):
    '''
    interpolation type is either:
     0 = no interpoolation
     1 = Straightline (default)
    :param wavegen_id:
    :param tbl_rate:
    :param interpolation_type:
    :return:
    '''
    s = 'WTR %d %d %d' % (wavegen_id, tbl_rate, interpolation_type)
    return(s)
def gen_get_wav_table_rate_cmnd(wavegen_id):
    '''
    :param wavegen_id:
    :return:
    '''
    s = 'WTR? %d' % (wavegen_id)
    return(s)

if __name__ == '__main__':
    #ss = get_WGO_cmnd(4, E712_WVGEN_START_MODES.IMEDDIATELY + E712_WVGEN_FLAGS.USE_AND_REINIT + E712_WVGEN_FLAGS.START_AT_ENDPOS, _new=True)
    #ex: 1 page 95
    #ss = gen_set_wav_gen_start_stop_mode_cmnd(1, E712_WVGEN_START_MODES.EXTERNAL_TRIG + E712_WVGEN_FLAGS.USE , _new=True)
    #print ss
    #ex: 2 page 95
    #ss = gen_set_wav_gen_start_stop_mode_cmnd(1, E712_WVGEN_START_MODES.IMEDDIATELY + E712_WVGEN_FLAGS.USE_AND_REINIT + E712_WVGEN_FLAGS.START_AT_ENDPOS, _new=True)
    #ss += gen_set_wav_gen_start_stop_mode_cmnd(2, E712_WVGEN_START_MODES.IMEDDIATELY + E712_WVGEN_FLAGS.USE, _new=False)
    #print ss
    ss = gen_set_wav_gen_start_stop_mode_cmnd(3, E712_WVGEN_START_MODES.IMEDDIATELY + E712_WVGEN_FLAGS.USE, _new=True)
    ss += gen_set_wav_gen_start_stop_mode_cmnd(4, E712_WVGEN_START_MODES.IMEDDIATELY + E712_WVGEN_FLAGS.USE + E712_WVGEN_FLAGS.START_AT_ENDPOS, _new=False)
    print(ss)

 