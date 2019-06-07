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
from cls.utils.json_threadsave import dict_to_json_string
from cls.appWidgets.splashScreen import get_splash, del_splash
from cls.scanning.nexus.cls_nx_api import _group, _dataset, nx_close, nx_open, nx_get, nx_put, nx_put_dict
from cls.utils.log import get_module_logger, log_to_console
from cls.zeromq.epics.epics_api import *
from cls.scanning.nexus.tmpfile_to_nxstxm import export_tmp_to_nxstxm


from cls.data_utils.jsonEncoder import NumpyAwareJSONEncoder

_logger = get_module_logger(__name__)
log_to_console()

#################################################
def start_server(host, port, base_dir, compression_type=compression_types.PICKLE):

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

    print('zmq_epics_server: waiting for messages from the client(s)')
    print('zmq_epics_server: base_dir given is [%s]' % base_dir)
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
            if (_dct['cmd'].find(CMD_SAVE_DICT_TO_TMPFILE) > -1):
                print('CMD_SAVE_DICT_TO_TMPFILE to %s' % tmp_fname)
                nx_f = nx_open(tmp_fname)
                print(list(_dct['dct'].keys()))
                nx_put_dict(nx_f, _dct['dct'])
                nx_close(nx_f)

            elif (_dct['cmd'].find(CMD_SAVE_JSON_TO_TMPFILE) > -1):
                print('CMD_SAVE_JSON_TO_TMPFILE to %s' % tmp_fname)
                nx_f = nx_open(tmp_fname)
                nx_put_dict(nx_f, _dct['json'])
                nx_close(nx_f)

            elif (_dct['cmd'].find(CMD_RNAME_TMP_TO_FINAL) > -1):
                print('[CMD_RNAME_TMP_TO_FINAL]: renamed [%s] to [%s]' % (tmp_fname, nxstxm_fname))
                nxstxm_fname = tmp_fname.replace('.tmp', '')
                os.rename(tmp_fname, nxstxm_fname )


            elif (_dct['cmd'].find(CMD_SET_FILE_NAME) > -1):
                tmp_fname = os.path.join(save_dir, _dct['subdir'], _dct['fname'])
                nxstxm_fname = tmp_fname.replace('.tmp', '')
                print('CMD_SET_FILE_NAME to %s' % tmp_fname)
                try:
                    if(os.path.exists(tmp_fname)):
                        os.remove(tmp_fname)
                    if (os.path.exists(tmp_fname)):
                        print('SOMETHING IS WRONG THE TMP FILE [%s] IS LOCKED SO IT CANT BE REMOVED' % tmp_fname)
                        break
                    print('CMD_SET_FILE_NAME: saving data to [%s]' % tmp_fname)
                    nx_open(tmp_fname, force_new=True)
                except WindowsError:
                    print('\tERROR:There was a problem removing the temporary file [%s]' % tmp_fname)
                    continue

            elif (_dct['cmd'].find(CMD_EXPORT_TMP_TO_NXSTXMFILE) > -1):
                print('CMD_EXPORT_TMP_TO_NXSTXMFILE: exportimg temp file [%s] to nxstxm_baseline data [%s]' % (tmp_fname, nxstxm_fname))
                export_tmp_to_nxstxm(tmp_fname, nxstxm_fname)

            else:
                print('Section [%s] not supported' % _dct['SECTION'])
                # save_data_to_tmp_file_idx(tmp_fname, _dct['idx'], _dct['devname'], _dct['data'], modify=False)

        elif (message.find(CMD_CREATE_NEW_FILE) > -1):
            nxf = nx_open(tmp_fname, force_new=True)
            nx_close(nxf)

        elif (message.find(CMD_ABORT) > -1):
            abort = True
            snd(socket, b"ABORTING")

    print('zmq_epics_server exited!')


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


    #start_server(_host, _port, _save_dir, compression_type=compression_types.MSGPACK)
    start_server(_host, _port, _save_dir, compression_type=compression_types.PICKLE)
