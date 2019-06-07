'''
Created on Nov 19, 2015

@author: bergr
'''
'''
Created on Nov 17, 2015

@author: bergr
'''

import os, sys
import string

import tempfile
import copy
import time
import zmq
import simplejson as json
from  multiprocessing import Process


from cls.utils.json_threadsave import dict_to_json_string
from cls.appWidgets.splashScreen import get_splash, del_splash
from cls.scanning.nexus.cls_nx_api import _group, _dataset, nx_close, nx_open, nx_get, nx_put, nx_put_dict
from cls.utils.log import get_module_logger, log_to_console
from cls.zeromq.epics.epics_api import *
from cls.scanning.nexus.tmpfile_to_nxstxm import export_tmp_to_nxstxm
from epics import caget, caput
from cls.utils.dict_utils import dct_merge
from cls.data_utils.jsonEncoder import NumpyAwareJSONEncoder
from cls.zeromq.forwarder.device_map import motors, ais, get_epics_name
from cls.zeromq.ports import *
_logger = get_module_logger(__name__)
log_to_console()


def fowarder_server(port="5559"):
    '''
    infinite loop where it pulls pv's from a list gets their current value and sends out as a zmq msg
    :param port:
    :param ext_name:
    :return:
    '''

    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.connect("tcp://localhost:%s" % port)
    print("epics publisher to zmq client: tcp://localhost:%s" % port)
    all_dct = dct_merge(motors, ais)
    while True:

        for ext_name in all_dct:
            #get fbk value
            pvname = get_epics_name(all_dct, ext_name)
            val = caget(pvname)
            pvname = all_dct[ext_name]['RBV']
            topic = 'FBK'
            messagedata = "%s#%.3f" % (ext_name, val)
            #print "[%s] %s %s" % (port, topic, messagedata)
            socket.send("%s %s" % (topic, messagedata))
            time.sleep(0.005)


#################################################
def zeromq_put_server(host, port, base_dir, compression_type=compression_types.PICKLE):

    if(compression_type is compression_types.PICKLE):
        print('Using PICKLE compression')
        msg_to_dict = proc_zipped_pickle
    elif(compression_type is compression_types.MSGPACK):
        print('Using MSGPACK compression')
        msg_to_dict = proc_msgpack
    else:
        _logger.error('Error: no compression_type specified, using PICKLE')
        print('Using PICKLE compression')
        msg_to_dict = proc_zipped_pickle

    context = zmq.Context()
    # the zmq.REPly socket type
    # It will block on recv() to get a request before it can send a reply.
    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.SUBSCRIBE, '')
    host_str = "tcp://%s:%s" % (host, port)
    print('Subscribing to server: %s' % host_str)
    socket.connect(host_str)

    #tempfile.tempdir = save_dir
    #tmp_fname = tempfile.mktemp('.tmp')
    #cur_date = time.strftime('%m%d')
    tmp_fname = None
    nxstxm_fname = None
    #print 'saving data to [%s]' % tmp_fname
    #nx_open(tmp_fname, force_new=True)

    print('zeromq_caput_server: waiting for messages from the client(s)')
    print('zeromq_caput_server: base_dir given is [%s]' % base_dir)
    abort = False
    while not abort:
        #  Wait for next request from client
        message = socket.recv()
        #print("Received request: %s" % message[0:10])

        #update savedir to current date
        cur_date = time.strftime('%m%d')
        save_dir = os.path.join(base_dir, cur_date)

        get = False
        put = False

        if (not all(c in string.printable for c in message)):
            # snd(socket, b"Receiving Zipped Pickle")
            #_dct = proc_zipped_pickle(message)
            _dct = msg_to_dict(message)

            # print 'rcvd: zipped pickled dict', _dct
            if (_dct['cmd'].find(CMD_PUT_PV_ATTR) > -1):
                print('CMD_PUT_PV_ATTR [%s = %.3f]' % (_dct['EPICS_NAME'], _dct['VAL']))
                pvname = _dct['EPICS_NAME']
                val = _dct['VAL']
                caput(pvname, val)

            else:
                print('Section [%s] not supported' % _dct['SECTION'])
                # save_data_to_tmp_file_idx(tmp_fname, _dct['idx'], _dct['devname'], _dct['data'], modify=False)

        if (message.find(CMD_SENDING_DICT) > -1):
            _dct = process_str_to_dict(message, strip_cmd=True)
            if(_dct['CMD'] == 'PUT'):
                print('CMD_PUT [%s = %.3f]' % (_dct['EPICS_NAME'], _dct['PUT_VAL']))
                pvname = _dct['VAL']
                val = _dct['PUT_VAL']
                caput(pvname, val)

        elif (message.find(CMD_ABORT) > -1):
            abort = True
            snd(socket, b"ABORTING")

    print('zeromq_caput_server exited!')


if __name__ == '__main__':
    import sys
    import time

    if len(sys.argv) > 1:
        _host = sys.argv[1]
        _port = sys.argv[2]
        _save_dir = sys.argv[3]

    else:
        _host = 'localhost'
        _port = '5555'
        _save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
        _save_dir = r'S:\STXM-data\Cryo-STXM\2018\guest'

    #Process(target=fowarder_server, args=(pub_port,)).start()

    #zeromq_put_server(_host, _port, _save_dir, compression_type=compression_types.MSGPACK)
    #zeromq_put_server(_host, _port, _save_dir, compression_type=compression_types.PICKLE)
    Process(target=zeromq_put_server, args=(_host, put_port, _save_dir, compression_types.PICKLE,)).start()
