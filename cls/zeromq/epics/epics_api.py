'''
Created on Nov 17, 2015

@author: bergr
'''
import simplejson as json
import zmq
import numpy as np
import zlib, pickle as pickle
import msgpack
import msgpack_numpy as m
from cls.utils.enum_utils import Enum

# a set of defined messages to be passed back and forth between zmq_epics client and severs
compression_types = Enum('pickle', 'msgpack')

CMD_UPDATE_POSNER_SNAPSHOT = 'UPDATE_POSNER_SNAPSHOT>'
CMD_GET_POSNER_SNAPSHOT = 'GET_POSNER_SNAPSHOT>'

CMD_UPDATE_DETECTOR_SNAPSHOT = 'UPDATE_DETECTOR_SNAPSHOT>'
CMD_GET_DETECTOR_SNAPSHOT = 'GET_DETECTOR_SNAPSHOT>'

CMD_UPDATE_PV_SNAPSHOT = 'UPDATE_PV_SNAPSHOT>'
CMD_GET_PV_SNAPSHOT = 'GET_PV_SNAPSHOT>'

CMD_UPDATE_PRESSURES_SNAPSHOT = 'UPDATE_PRESSURES_SNAPSHOT>'
CMD_UPDATE_TEMPERATURES_SNAPSHOT = 'UPDATE_TEMPERATURES_SNAPSHOT>'


CMD_UPDATE_SSCAN_SNAPSHOT = 'UPDATE_SSCAN_SNAPSHOT>'
CMD_GET_SSCAN_SNAPSHOT = 'GET_SSCAN_SNAPSHOT>'

CMD_DISC_POSNER_LIST = 'DISCOVER_POSNER_LIST>'
CMD_SENDING_DICT = 'SENDING_DICT>'

CMD_ABORT = 'CMD_ABORT>'
CMD_CHECK_IF_RUNNING = 'CHECK_IF_RUNNING>'

CMD_REGISTER_UPD_LIST = 'REGISTER_UPD_LIST>'
CMD_UPDATE_UPD_SNAPSHOT = 'UPDATE_UPD_SNAPSHOT>'

CMD_REGISTER_IMG_IDX_MAP = 'REGISTER_IMG_IDX_MAP>'

CMD_CREATE_NEW_FILE = 'CREATE_NEW_FILE>'

CMD_SET_FILE_NAME = 'SET_FILE_NAME>'
CMD_SAVE_DATA_TO_IDX = 'SAVE_DATA_TO_IDX>'
CMD_SAVE_DICT_TO_TMPFILE = 'SAVE_DICT_TO_TMPFILE>'
CMD_SAVE_JSON_TO_TMPFILE = 'SAVE_JSON_TO_TMPFILE>'
CMD_EXPORT_TMP_TO_NXSTXMFILE = 'EXPORT_TMP_TO_NXSTXMFILE>'
CMD_RNAME_TMP_TO_FINAL = 'RNAME_TMP_TO_FINAL>'

# "PUT>%s#%s=%d" % (nm, attr, val)
CMD_PUT_PV_ATTR = b"PUT>%s#%s=%d"

# b"GET>%s#%s" % (nm, attr)
CMD_GET_PV_ATTR = b"GET>%s#%s"

CMD_GET = b"GET>%s#%s"
CMD_PUT_PV_INT = b"PUT_INT>%s#%d"
CMD_PUT_PV_DBL = b"PUT_DBL>%s#%f"
CMD_PUT_PV_STR = b"PUT_STR>%s#%s"
CMD_PUT_PV_ARR = b"PUT_ARR>%s#%s"


def list_to_string(lst):
    s = ','.join(map(str, lst))
    ss = '[' + s + ']'
    return (ss)


def dict_to_str(dct):
    s = json.dumps(dct)
    return (s)


def process_str_to_list(str, as_int_array=False):
    s2 = str.replace('[', '')
    s2 = s2.replace(']', '')
    s2 = s2.replace('"', '')
    s2 = s2.replace(' ', '')
    s2 = s2.replace('\n', '')
    s2 = s2.strip()
    s2 = s2.rstrip()
    l = s2.split(',')
    if (as_int_array):
        l = list(map(int, l))
    return (l)


def process_str_to_dict(msg, strip_cmd=False):
    if (strip_cmd):
        s = msg.split('>')
        dct = json.loads(s[1])
    else:
        dct = json.loads(msg)
    return (dct)


def snd(sock, request, verbose=True):
    if(verbose):
        print('zmq:epics_api:snd: sending [%s]' % request)
    else:
        print('zmq:epics_api:snd: sending something')
    sock.send_string(request)
    #print('SND: [%s]' % request)




def snd_rcv(sock, request, verbose=True):
    if(verbose):
        print('zmq:epics_api:snd_rcv: sending [%s]' % request)
    else:
        print('zmq:epics_api:snd_rcv: sending a msg')
    sock.send(request)
    # time.sleep(0.001)
    _message = sock.recv()

    print('zmq:epics_api:snd_rcv: got response [%s]' % _message)
    ####### CRITICAL
    # without the following call the Qt event loop does something strange with the zmq context/socket
    # and it will stop working, with this call it continues to work, must be because of a poll that gets called
    # as a result
    sock.getsockopt(zmq.EVENTS)
    ###
    return (_message)


def send_put_msg(sock, nm, attr, val):
    request = CMD_PUT_PV_ATTR % (nm, attr, val)
    message = snd_rcv(sock, request)
    #print("Received reply %s [ %s ]" % (request, message))


def send_get_msg(sock, nm, attr):
    request = CMD_GET_PV_ATTR % (nm, attr)
    message = snd_rcv(sock, request)
    # print("Received reply %s [ %s ]" % (request, message))
    return (message)


def get_put_args(msg):
    ''' PUT>DNM_DETECTOR_Z#VAL=2500

    returns: pvname, attr, val

    '''
    m1 = msg.split('>')
    m2 = m1[1].split('#')
    m3 = m2[1].split('=')
    return (m2[0], m3[0], m3[1])


def get_get_args(msg):
    ''' GET>DNM_DETECTOR_Z#RBV

    returns: pv, attr

    '''
    m1 = msg.split('>')
    m2 = m1[1].split('#')
    return (m2[0], m2[1])


def send_update_list_msg(sock, cmd, lst, do_rcv=True):
    ''' %cmd%>[list of items]
    ex:
        'UPDATE_SSCAN>[uhvstxm:det:scan1,uhvstxm:det:scan2]'
    returns:

    '''
    request = '%s%s' % (cmd, list_to_string(lst))
    if(do_rcv):
        message = snd_rcv(sock, request)
        print(("Received reply %s [ %s ]" % (request, message)))
    else:
        snd(sock, request)



def send_register_update_list_msg(sock, cmd, lst, do_rcv=True):
    ''' %cmd%>[list of items]
    ex:
        'CMD_REGISTER_UPD_LIST>[ENERGY, EPU_GAP, EPU_OFFSET]'
    returns:

    '''
    request = '%s%s' % (cmd, list_to_string(lst))
    if(do_rcv):
        message = snd_rcv(sock, request, verbose=False)
    else:
        snd(sock, request, verbose=False)
    #print("Received reply %s [ %s ]" % (request, message))


def send_register_img_idx_map_msg(sock, cmd, dct, do_rcv=True):
    request = '%s%s' % (cmd, dict_to_str(dct))
    if (do_rcv):
        message = snd_rcv(sock, request, verbose=False)
    else:
        snd(sock, request, verbose=False)
    #print("Received reply %s [ %s ]" % (request, message))


def send_do_update_msg(sock, cmd, idx, do_rcv=True):
    ''' %cmd%>[list of items]
    ex:
        'CMD_REGISTER_UPD_LIST>13'
    returns:

    '''
    request = '%s%d' % (cmd, idx)
    if(do_rcv):
        message = snd_rcv(sock, request)
    else:
        snd(sock, request)
    #print("Received reply %s [ %s ]" % (request, message))


def send_get_sscan_msg(sock, cmd, lst, do_rcv=True):
    ''' %cmd%>[list of items]
    ex:
        'UPDATE_SSCAN>[uhvstxm:det:scan1,uhvstxm:det:scan2]'
    returns:

    '''
    request = '%s%s' % (cmd, list_to_string(lst))
    message = snd_rcv(sock, request)
    dct = process_str_to_dict(message)
    # print "Received reply %s [ %s ]" % (request, message)
    return (dct)


def zmq_send_dct(sock, dct, do_rcv=True):
    ''' take a dict turn it into a string and send it

    ex:
        'INPUT_DICT>{ dict as a string}'
    returns:

    '''
    request = '%s%s' % (CMD_SENDING_DICT, dict_to_str(dct))
    if (do_rcv):
        message = snd_rcv(sock, request)
    else:
        snd(sock, request)
    # dct = process_str_to_dict(message)
    #print "Received reply [ %s ]" % (message)


# return(dct)

def send_array(sock, A, flags=0, copy=True, track=False):
    """send a numpy array with metadata"""
    md = dict(
        dtype=str(A.dtype),
        shape=A.shape,
    )
    sock.send_json(md, flags | zmq.SNDMORE)
    return sock.send(A, flags, copy=copy, track=track)


def rcv_array(sock, flags=0, copy=True, track=False):
    """recv a numpy array"""
    md = sock.recv_json(flags=flags)
    msg = sock.recv(flags=flags, copy=copy, track=track)
    buf = buffer(msg)
    A = np.frombuffer(buf, dtype=md['dtype'])
    return A.reshape(md['shape'])


def send_zipped_pickle(socket, obj, flags=0, protocol=-1, do_rcv=True):
    """pickle an object, and zip the pickle before sending it"""
    #print 'send_zipped_pickle: sending a pickled object'
    p = pickle.dumps(obj, protocol)
    z = zlib.compress(p)
    socket.send(z, flags=flags)
    #snd_rcv(socket, z, verbose=False)
    #print 'send_zipped_pickle: sending a pickle'
    if(do_rcv):
        rcv_msg = socket.recv()
    return

def send_msgpack_msg(socket, msg, flags=0, do_rcv=True):
    """pickle an object, and zip the pickle before sending it"""
    #print 'send_zipped_pickle: sending a pickled object'
    msg_enc = msgpack.packb(msg, default=m.encode)
    socket.send(msg_enc, flags=flags)
    if(do_rcv):
        rcv_msg = socket.recv()
    return


def recv_zipped_pickle(socket, flags=0, protocol=-1):
    """inverse of send_zipped_pickle"""
    z = socket.recv(flags)
    p = zlib.decompress(z)
    return pickle.loads(p)


def proc_zipped_pickle(msg):
    p = zlib.decompress(msg)
    return pickle.loads(p)

def proc_msgpack(msg):
    dct = msgpack.unpackb(msg, object_hook=m.decode)
    return(dct)

def parse_update_list_msg(msg):
    ''' %cmd%>[list of items]
    ex:
        'UPDATE_SSCAN>[uhvstxm:det:scan1,uhvstxm:det:scan2]'
    returns: cmd, list

    '''
    m1 = msg.split('>')
    l = process_str_to_list(m1[1])

    return (m1[0], l)


def parse_get_list_msg(msg):
    ''' %cmd%>[list of items]
    ex:
        'GET_SSCAN>[uhvstxm:det:scan1,uhvstxm:det:scan2]'
    returns: cmd, list

    '''
    m1 = msg.split('>')
    l = process_str_to_list(m1[1])

    return (m1[0], l)


def parse_get_idx_from_update_dev_msg(msg):
    ''' %cmd%>integer
    ex:
        'UPDATE_UPD_SNAPSHOT>13'
    returns: int(13)

    '''
    m1 = msg.split('>')
    val = int(m1[1])

    return (val)


def parse_get_idx_from_save_data_msg(msg):
    ''' %cmd%>idx integer#rows#columns#1D array
    ex:
        'SAVE_DATA_TO_IDX>counter0#13#3#3#[1,2,3,4,5,6,7,8,9]'
    returns: int(13), data array

    '''
    m1 = msg.split('>')
    devname, idx, rows, cols, a_str = m1[1].split('#')
    idx = int(idx)
    rows = int(rows)
    cols = int(cols)
    arr = process_str_to_list(a_str, as_int_array=True)
    arr = np.reshape(arr, (rows, cols))
    return (devname, idx, arr)


def strip_command_from_msg(msg):
    ''' %cmd%>integer
    ex:
        'UPDATE_UPD_SNAPSHOT>HERE I AM'
    returns: 'HERE I AM'

    '''
    m1 = msg.split('>')
    s = m1[1]

    return (s)
