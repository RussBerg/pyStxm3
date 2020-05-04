# Suitcase subpackages should follow strict naming and interface conventions.
# The public API must include Serializer and should include export if it is
# intended to be user-facing. They should accept the parameters sketched here,
# but may also accpet additional required or optional keyword arguments, as
# needed.
import os
import event_model
import pandas
from pathlib import Path
import suitcase.utils
import h5py
import nexpy
import hdfdict
import numpy as np
import time
from time import mktime, strftime, strptime, localtime
import simplejson as json
from cls.utils.time_utils import make_timestamp_now
from cls.utils.json_threadsave import dict_to_json_string
from cls.utils.log import get_module_logger
from cls.types.stxmTypes import scan_types, single_entry_scans, multi_entry_scans, two_posner_scans, three_posner_scans
from bcm.devices.device_names import *
from suitcase.nxstxm.nxstxm_utils import (make_signal, _dataset, _string_attr, _group, make_1d_array, \
                                          get_nx_standard_epu_mode, get_nx_standard_epu_harmonic_new, translate_pol_id_to_stokes_vector, \
                                          readin_base_classes, make_NXclass, remove_unused_NXsensor_fields)

import suitcase.nxstxm.nx_key_defs as nxkd
#from suitcase.nxstxm.sim_img_idx_map import img_idx_map
from suitcase.nxstxm.generic_scan_utils import modify_generic_scan_nxdata_group, modify_generic_scan_ctrl_data_grps, \
                                                modify_generic_scan_instrument_group
from suitcase.nxstxm.single_2d_image_utils import modify_base_2d_nxdata_group, modify_2posner_ctrl_data_grps, \
                                                modify_base_2d_instrument_group
from suitcase.nxstxm.focus_image_utils import modify_focus_nxdata_group, modify_focus_ctrl_data_grps, \
                                                modify_focus_instrument_group
from suitcase.nxstxm.single_image_utils import modify_single_image_nxdata_group, modify_single_image_ctrl_data_grps, \
                                                modify_single_image_instrument_group

from suitcase.nxstxm.stack_image_utils import modify_stack_nxdata_group, modify_stack_ctrl_data_grps

from ._version import get_versions

_logger = get_module_logger(__name__)

MARK_DATA = False

__version__ = get_versions()['version']
del get_versions


def finish_export(data_dir, file_prefix):
    '''
    This was moved into its own function so that if multiple entrys had been created in the same file they
    would have been done so in a tmp file, were done now so rename it to the final filename
    :param file_prefix:
    :return:
    '''
    tmp_fname = os.path.join(data_dir, '%s.hdf5.tmp' % file_prefix)
    final_fname = tmp_fname.replace('.tmp', '')
    os.rename(tmp_fname, final_fname)
    _logger.info('nxstxm_primary: finished exporting [%s]' % final_fname)
    print('nxstxm_primary: finished exporting [%s]' % final_fname)

def test_can_do_tmp_file(data_dir, file_prefix):
    '''
    see if we are going to have trouble creating this file later when scan is done
    :param data_dir:
    :param file_prefix:
    :return:
    '''
    fname = os.path.join(data_dir, '%s.hdf5.tmp' % file_prefix)
    nf = None
    try:
        nf = h5py.File(fname, 'a')
        nf.close()
        os.remove(fname)
        return (True)
    except:
        _logger.info('Looks like there already was a file[%s]' % fname)
        if (nf is not None):
            nf.close()
        if(os.path.exists(fname + '.err')):
            #removing previous failed file
            os.remove(fname + '.err')
        os.rename(fname, fname + '.err')
        return (False)



def export(gen, directory, file_prefix='{uid}-', **kwargs):
    """
    Export a stream of documents to nxstxm_baseline.

    .. note::

        This can alternatively be used to write data to generic buffers rather
        than creating files on disk. See the documentation for the
        ``directory`` parameter below.

    Parameters
    ----------
    gen : generator
        expected to yield ``(name, document)`` pairs

    directory : string, Path or Manager.
        For basic uses, this should be the path to the output directory given
        as a string or Path object. Use an empty string ``''`` to place files
        in the current working directory.

        In advanced applications, this may direct the serialized output to a
        memory buffer, network socket, or other writable buffer. It should be
        an instance of ``suitcase.utils.MemoryBufferManager`` and
        ``suitcase.utils.MultiFileManager`` or any object implementing that
        inferface. See the suitcase documentation at
        https://nsls-ii.github.io/suitcase for details.

    file_prefix : str, optional
        The first part of the filename of the generated output files. This
        string may include templates as in ``{proposal_id}-{sample_name}-``,
        which are populated from the RunStart document. The default value is
        ``{uid}-`` which is guaranteed to be present and unique. A more
        descriptive value depends on the application and is therefore left to
        the user.

    **kwargs : kwargs
        Keyword arugments to be passed through to the underlying I/O library.

    Returns
    -------
    artifacts : dict
        dict mapping the 'labels' to lists of file names (or, in general,
        whatever resources are produced by the Manager)

    Examples
    --------

    Generate files with unique-identifer names in the current directory.

    >>> export(gen, '')

    Generate files with more readable metadata in the file names.

    >>> export(gen, '', '{plan_name}-{motors}-')

    Include the experiment's start time formatted as YY-MM-DD_HH-MM.

    >>> export(gen, '', '{time:%%Y-%%m-%%d_%%H:%%M}-')

    Place the files in a different directory, such as on a mounted USB stick.

    >>> export(gen, '/path/to/my_usb_stick')
    """
    with Serializer(directory, file_prefix, **kwargs) as serializer:
        for item in gen:
            serializer(*item)

    return serializer.artifacts


class Serializer(event_model.DocumentRouter):
    """
    Serialize a stream of documents to nxstxm_baseline.

    .. note::

        This can alternatively be used to write data to generic buffers rather
        than creating files on disk. See the documentation for the
        ``directory`` parameter below.

    Parameters
    ----------
    directory : string, Path, or Manager
        For basic uses, this should be the path to the output directory given
        as a string or Path object. Use an empty string ``''`` to place files
        in the current working directory.

        In advanced applications, this may direct the serialized output to a
        memory buffer, network socket, or other writable buffer. It should be
        an instance of ``suitcase.utils.MemoryBufferManager`` and
        ``suitcase.utils.MultiFileManager`` or any object implementing that
        inferface. See the suitcase documentation at
        https://nsls-ii.github.io/suitcase for details.

    file_prefix : str, optional
        The first part of the filename of the generated output files. This
        string may include templates as in ``{proposal_id}-{sample_name}-``,
        which are populated from the RunStart document. The default value is
        ``{uid}-`` which is guaranteed to be present and unique. A more
        descriptive value depends on the application and is therefore left to
        the user.

    **kwargs : kwargs
        Keyword arugments to be passed through to the underlying I/O library.

    Attributes
    ----------
    artifacts
        dict mapping the 'labels' to lists of file names (or, in general,
        whatever resources are produced by the Manager)
    """
    def __init__(self, directory, file_prefix='{uid}-',  **kwargs):

        self._file_prefix = file_prefix
        self._kwargs = kwargs
        self._directory = directory
        self._templated_file_prefix = file_prefix  # set when we get a 'start' document
        self._tmp_fname = os.path.join(self._directory, '%s.hdf5.tmp' % file_prefix)
        self._streamnames = {}  # maps descriptor uids to stream_names
        self._entries = {}
        self._img_idx_map_dct = {}

        self._start_uids = {}
        self._descriptor_uids = {}
        self._event_page_uids = {}
        self._stop_uids = {}
        self._primary_det_nm = None
        self._primary_det_prefix = None

        self._file_time_str = make_timestamp_now()
        self._cur_scan_md = {}
        self._processed_sp_ids = []

        self._data = {}

        if('index' in kwargs.keys()):
            self._index = kwargs['index']
        else:
            self._index = 0

        self._start_found = False
        self._nf = None

        #if (os.path.exists(self._tmp_fname)):
        #    os.remove(self._tmp_fname)

        if isinstance(directory, (str, Path)):
            # The user has given us a filepath; they want files.
            # Set up a MultiFileManager for them.
            self._manager = suitcase.utils.MultiFileManager(directory)
        else:
            # The user has given us their own Manager instance. Use that.
            self._manager = directory

        # Finally, we usually need some state related to stashing file
        # handles/buffers. For a Serializer that only needs *one* file
        # this may be:
        #
        # self._output_file = None
        #
        # For a Serializer that writes a separate file per stream:
        #
        # self._files = {}

    @property
    def artifacts(self):
        # The 'artifacts' are the manager's way to exposing to the user a
        # way to get at the resources that were created. For
        # `MultiFileManager`, the artifacts are filenames.  For
        # `MemoryBuffersManager`, the artifacts are the buffer objects
        # themselves. The Serializer, in turn, exposes that to the user here.
        #
        # This must be a property, not a plain attribute, because the
        # manager's `artifacts` attribute is also a property, and we must
        # access it anew each time to be sure to get the latest contents.
        return self._manager.artifacts

    def close(self):
        """
        Close all of the resources (e.g. files) allocated.
        """
        self._manager.close()

    # These methods enable the Serializer to be used as a context manager:
    #
    # with Serializer(...) as serializer:
    #     ...
    #
    # which always calls close() on exit from the with block.

    def __enter__(self):
        return self

    def __exit__(self, *exception_details):
        self.close()

    # Each of the methods below corresponds to a document type. As
    # documents flow in through Serializer.__call__, the DocumentRouter base
    # class will forward them to the method with the name corresponding to
    # the document's type: RunStart documents go to the 'start' method,
    # etc.
    #
    # In each of these methods:
    #
    # - If needed, obtain a new file/buffer from the manager and stash it
    #   on instance state (self._files, etc.) if you will need it again
    #   later. Example:
    #
    #   filename = f'{self._templated_file_prefix}-primary.csv'
    #   file = self._manager.open('stream_data', filename, 'xt')
    #   self._files['primary'] = file
    #
    #   See the manager documentation below for more about the arguments to open().
    #
    # - Write data into the file, usually something like:
    #
    #   content = my_function(doc)
    #   file.write(content)
    #
    #   or
    #
    #   my_function(doc, file)

    def start(self, doc):
        '''Extracts `start` document information for formatting file_prefix.

                This method checks that only one `start` document is seen and formats
                `file_prefix` based on the contents of the `start` document.
                    START: [entry1]

                    Run Start
                    =========
                    host            : myNotebook
                    plan_name       : exec_e712_wavgen
                    plan_type       : generator
                    scan_id         : 1
                    scan_title      : entry1
                    time            : 1552057991.7095182
                    uid             : f66a3e61-dcbb-4975-9fc8-c38a0255fb1b
                    user            : bergr

                Parameters:
                -----------
                doc : dict
                    RunStart document
                '''

        # raise an error if this is the second `start` document seen.
        # 'a' Read/write if exists, create otherwise (default)
        self._start_uids['uid'] = doc['uid']

        start_time = localtime(doc['time'])
        self._start_time_str = time.strftime("%Y-%m-%dT%H:%M:%S", start_time)

        #grab the meta data that was entered into the md var in the scan plan
        _metadata_dct = json.loads(doc['metadata'])
        self._cur_scan_md[doc['uid']] = {}
        for k in _metadata_dct.keys():
            self._cur_scan_md[doc['uid']][k] = _metadata_dct[k]

        #_img_idx_map_dct = json.loads(_metadata_dct['img_idx_map'])
        self._img_idx_map_dct = self._kwargs['img_idx_map']
        self._primary_det_prefix = _metadata_dct['primary_det']
        self._entries[doc['uid']] = _metadata_dct['entry_name']

        self._cur_uid = doc['uid']
        # self.e_idx = self._kwargs['img_idx_map'][doc['uid']]['e_idx']
        # self.entry_nm = self._kwargs['img_idx_map'][doc['uid']]['entry']
        # self.pol_idx = self._kwargs['img_idx_map'][doc['uid']]['pol_idx']
        # self.sp_id = self._kwargs['img_idx_map'][doc['uid']]['sp_id']
        # self.sp_idx = self._kwargs['img_idx_map'][doc['uid']]['sp_idx']
        self.e_idx = self._kwargs['img_idx_map']['e_idx']
        self.entry_nm = self._kwargs['img_idx_map']['entry']
        self.pol_idx = self._kwargs['img_idx_map']['pol_idx']
        self.sp_id = self._kwargs['img_idx_map']['sp_id']
        self.sp_idx = self._kwargs['img_idx_map']['sp_idx']

        js_str = self._cur_scan_md[doc['uid']]['wdg_com']
        self._wdg_com = json.loads(js_str)

        if self._start_found:
            raise RuntimeError(
                "The serializer in suitcase.csv expects documents from one "
                "run only. Two `start` documents where sent to it")
        else:
            self._start_found = True

        # format self._file_prefix
        self._templated_file_prefix = self._file_prefix.format(**doc)



    def descriptor(self, doc):
        '''Use `descriptor` doc to map stream_names to descriptor uid's.

        This method usess the descriptor document information to map the
        stream_names to descriptor uid's.

            DESCRIPTOR: for stream [oranges]
            Event Descriptor
            ================
            +-----------------------+-------+------------------+-------+-------------------------------+-------+------------------+
            | data keys             | dtype | lower_ctrl_limit | shape |             source            | units | upper_ctrl_limit |
            +-----------------------+-------+------------------+-------+-------------------------------+-------+------------------+
            | line_det_waveform_rbv | array |       None       | [104] | PV:uhvCI:counter:Waveform_RBV |  None |       None       |
            +-----------------------+-------+------------------+-------+-------------------------------+-------+------------------+
            hints           :
                fields          : ['line_det_waveform_rbv']
            name            : oranges
            object_keys     :
              line_det        : ['line_det_waveform_rbv']
            run_start       : f66a3e61-dcbb-4975-9fc8-c38a0255fb1b
            time            : 1552058010.8317492
            uid             : bb5b81e5-d8be-45d6-939a-b8d0d4b4365f

        Parameters:
        -----------
        doc : dict
            EventDescriptor document
        '''
        # extract some useful info from the doc
        self._descriptor_uids['runstart'] = doc['run_start']
        #here create a link from the descriptor[uid] to descriptor[run_start] so that the event_page can retrieve the entry name
        self._descriptor_uids['uid'] = {doc['uid']: doc['run_start']}
        strm_name = doc['name']
        #uid = doc['run_start']
        # e_idx = img_idx_map[uid]['e_idx']
        # pol_idx = img_idx_map[uid]['pol_idx']
        # sp_idx = img_idx_map[uid]['sp_idx']
        # entry = img_idx_map[uid]['entry']
        self._data[strm_name] = {}
        for k, v in doc['data_keys'].items():
            self._data[strm_name][k] = {}
            self._data[strm_name][k][self._cur_uid] = {}
            self._data[strm_name][k][self._cur_uid]['data'] = []
            self._data[strm_name][k][self._cur_uid]['info'] = v

        streamname = doc['name']
        self._streamnames[doc['uid']] = streamname
        #print('\nDESCRIPTOR: for stream [%s]' % streamname)
        #print(doc)
        #fname = os.path.join(self._directory, '%s.tmp.hdf5' % doc['run_start'])
        # nf = h5py.File(self._tmp_fname, "a")
        # entry_nxgrp = nf[self._entries[doc['run_start']]]
        # col_grp = _group(entry_nxgrp, nxkd.NXD_COLLECTION, 'NXcollection')
        #
        # for field in doc['data_keys']:
        #     obj_nm = doc['data_keys'][field]['object_name']
        #     src = doc['data_keys'][field]['source']
        #     units = doc['data_keys'][field]['units']
        #     val = -99.99
        #     make_NXsensor(col_grp, obj_nm, src, val, units, modify=False)
        #
        # nf.close()


    def event_page(self, doc):
        # There are other representations of Event data -- 'event' and
        # 'bulk_events' (deprecated). But that does not concern us because
        # DocumentRouter will convert this representations to 'event_page'
        # then route them through here.
        '''Add event page document information to a ".csv" file.

                This method adds event_page document information to a ".csv" file,
                creating it if nesecary.

                .. warning::

                    All non 1D 'tabular' data is explicitly ignored.

                .. note::

                    The data in Events might be structured as an Event, an EventPage,
                    or a "bulk event" (deprecated). The DocumentRouter base class takes
                    care of first transforming the other repsentations into an
                    EventPage and then routing them through here, so no further action
                    is required in this class. We can assume we will always receive an
                    EventPage.

                    EVENT_PAGE: for stream [oranges]
                        {'time': [1552057991.7633746],
                            'uid': ['e368a918-3f0f-4855-8898-6b444f45457c'],
                            'seq_num': [101],
                            'descriptor': 'bb5b81e5-d8be-45d6-939a-b8d0d4b4365f', 'filled': {},
                            'data': {'line_det_waveform_rbv': [array([0., 1., 1., 0., 1., 1., 0., 1., 1., 0., 1., 1., 1., 1., 1., 1., 1.,
                               1., 1., 0., 1., 1., 1., 1., 0., 1., 1., 0., 1., 1., 0., 1., 1., 0.,
                               1., 1., 1., 0., 1., 1., 1., 1., 1., 0., 1., 0., 1., 0., 1., 0., 1.,
                               1., 1., 0., 1., 1., 0., 1., 1., 1., 0., 1., 0., 1., 0., 1., 1., 1.,
                               0., 1., 1., 1., 0., 1., 1., 0., 1., 1., 0., 1., 0., 1., 1., 0., 2.,
                               0., 1., 0., 1., 0., 1., 1., 1., 1., 0., 1., 0., 1., 1., 1.])]},
                            'timestamps': {'line_det_waveform_rbv': [[1552057941.473328, 1552057989.462274, ...]]}}

                Parameters:
                -----------
                doc : dict
                    EventPage document
                '''
        #self._event_page_uids['uid'].append(doc['uid'])
        strm_name = self._streamnames[doc['descriptor']]
        for k in doc['data'].keys():
            if(k in self._data[strm_name].keys()):
                #self._data[strm_name][k]['data'].append((doc['seq_num'][0], doc['data'][k][0]))
                self._data[strm_name][k][self._cur_uid]['data'].append(doc['data'][k][0])


        self._event_page_uids['descriptor'] = doc['descriptor']

        event_model.verify_filled(doc)
        streamname = self._streamnames[doc['descriptor']]
        #print('\nEVENT_PAGE: for stream [%s]' % streamname)
        #print(doc)

        #rs_uid = self._descriptor_uids['uid'][doc['descriptor']]
        #valid_data = {}
        # for field in doc['data']:
        #     # check that the data is 1D, if not ignore it
        #     if doc['data'][field][0].ndim == 1:
        #         # create a file for this stream and field if required
        #         # if streamname not in self._files.keys():
        #         #     filename = (f'{self._templated_file_prefix}{streamname}.csv')
        #         #     f = self._manager.open('stream_data', filename, 'xt')
        #         #     self._files[streamname] = f
        #         # add the valid data to the valid_data dict
        #         valid_data[field] = doc['data'][field]
        #         self._data[doc['seq_num']] = doc['data'][field][0]
        #
        # if valid_data:
        #     event_data = pandas.DataFrame(valid_data, index=doc[self._kwargs['index_label']])
        #     event_data['seq_num'] = doc['seq_num']
        #
        #     if self._initial_header_kwarg:
        #         self._kwargs['header'] = streamname not in self._has_header
        #
        #     event_data.to_csv(self._files[streamname], **self._kwargs)
        #     self._has_header.add(streamname)



    def _skip(self, mainstr, skip_list):
        '''
        run through list of strings looking to see if the mainstr contains anything in the skip list
        if we find an occurance then return True
        :param mainstr:
        :param skip_list:
        :return:
        '''
        ret = False
        for sl in skip_list:
            if(mainstr.find(sl) > -1):
                return(True)

    def create_entry_structure(self, doc, scan_type):
        '''
         Enum('detector_image', \
				'osa_image', \
				'osa_focus', \
				'sample_focus', \
				'sample_point_spectra', \
				'sample_line_spectra', \
				'sample_image', \
				'sample_image_stack', \
				'generic_scan', \
				'coarse_image', \
				'coarse_goni', \
				'tomography')
        :param doc:
        :param scan_type:
        :return:
        '''

        if(scan_type in single_entry_scans):
            self.save_single_entry_scan(doc, scan_type)
        else:
            self.save_multi_entry_scan(doc, scan_type)

    def create_file_attrs(self):
        nf = None
        try:
            nf = h5py.File(self._tmp_fname, 'a')
            # set attrs foe the file
            _string_attr(nf, nxkd.NXD_HDF_VER, nxkd.HDF5_VER)
            _string_attr(nf, nxkd.NXD_H5PY_VER, h5py.__version__)
            _string_attr(nf, nxkd.NXD_NXPY_VER, nexpy.__version__)
            _string_attr(nf, nxkd.NXD_NX_VER, nxkd.NEXUS_VER)
            _string_attr(nf, nxkd.NXD_FILE_NAME, self._tmp_fname)
            _string_attr(nf, nxkd.NXD_FILE_TIME, self._file_time_str)
            nf.close()

        except:
            _logger.error('create_file_attrs: problem creating file [%s]' % self._tmp_fname)


    def save_single_entry_scan(self, doc, scan_type):
        '''

        :param doc:
        :param scan_type:
        :return:
        '''
        nf = None
        try:
            nf = self._nf = h5py.File(self._tmp_fname, 'a')

            #this entry name comes from metadata setup by scan plan
            #entry_nm = self._cur_scan_md[doc['run_start']]['entry_name']
            entry_nxgrp = _group(nf, self.entry_nm, 'NXentry')

            # # set attrs foe the file
            # _string_attr(nf, nxkd.NXD_HDF_VER, nxkd.HDF5_VER)
            # _string_attr(nf, nxkd.NXD_H5PY_VER, h5py.__version__)
            # _string_attr(nf, nxkd.NXD_NXPY_VER, nexpy.__version__)
            # _string_attr(nf, nxkd.NXD_NX_VER, nxkd.NEXUS_VER)
            # _string_attr(nf, nxkd.NXD_FILE_NAME, self._tmp_fname)
            # _string_attr(nf, nxkd.NXD_FILE_TIME, self._file_time_str)

            # set datasets that must exist in tmp file
            # hdfdict.dump({'img_idx_map':img_idx_map}, nf)
            #_dataset(nf, 'img_idx_map', img_idx_map, 'NX_CHAR')
            _dataset(entry_nxgrp, 'title', 'NeXus sample', 'NX_CHAR')
            _dataset(entry_nxgrp, 'start_time', self._start_time_str, 'NX_DATE_TIME')
            _dataset(entry_nxgrp, 'end_time', self._stop_time_str, 'NX_DATE_TIME')
            _dataset(entry_nxgrp, 'definition', 'NXstxm', 'NX_CHAR')
            _dataset(entry_nxgrp, 'version', '1.0', 'NX_CHAR')

            self.specific_scan_funcs = self.get_scan_specific_funcs(scan_type)

            #create entry groups
            self.create_collection_group(entry_nxgrp, doc, scan_type)

            ctrl_nxgrp = self.create_base_control_group(entry_nxgrp, doc, scan_type)
            self.specific_scan_funcs['mod_nxctrl'](self, ctrl_nxgrp, doc,scan_type)

            data_nxgrp = self.create_base_nxdata_group(entry_nxgrp, self._primary_det_prefix, doc, scan_type)
            self.specific_scan_funcs['mod_nxdata'](self, data_nxgrp, doc, scan_type)

            # self.create_scan_specific_nxdata_group(entry_nxgrp, self._primary_det_prefix, doc, scan_type)
            #inst_nxgrp = self.create_instrument_group(entry_nxgrp, doc, scan_type)

            inst_nxgrp = self.create_base_instrument_group(entry_nxgrp, doc, scan_type)
            self.specific_scan_funcs['mod_nxinst'](self, inst_nxgrp, doc, scan_type)
            #
            self.create_base_sample_group(entry_nxgrp, doc, scan_type)

            nf.close()
        except:
            _logger.error('Problem saving file[%s]' % self._tmp_fname)
            if (nf is not None):
                nf.close()
            os.rename(self._tmp_fname, self._tmp_fname + '.err')

    def save_multi_entry_scan(self, doc, scan_type):
        '''

        :param doc:
        :param scan_type:
        :return:
        '''
        nf = None
        try:
            nf = self._nf = h5py.File(self._tmp_fname, 'a')

            #this entry name comes from metadata setup by scan plan
            #entry_nm = self._cur_scan_md[doc['run_start']]['entry_name']
            entry_nxgrp = _group(nf, self.entry_nm, 'NXentry')

            # set attrs foe the file
            # _string_attr(nf, nxkd.NXD_HDF_VER, nxkd.HDF5_VER)
            # _string_attr(nf, nxkd.NXD_H5PY_VER, h5py.__version__)
            # _string_attr(nf, nxkd.NXD_NXPY_VER, nexpy.__version__)
            # _string_attr(nf, nxkd.NXD_NX_VER, nxkd.NEXUS_VER)
            # _string_attr(nf, nxkd.NXD_FILE_NAME, self._tmp_fname)
            # _string_attr(nf, nxkd.NXD_FILE_TIME, self._file_time_str)

            # set datasets that must exist in tmp file
            # hdfdict.dump({'img_idx_map':img_idx_map}, nf)
            #_dataset(nf, 'img_idx_map', img_idx_map, 'NX_CHAR')
            _dataset(entry_nxgrp, 'title', 'NeXus sample', 'NX_CHAR')
            _dataset(entry_nxgrp, 'start_time', self._start_time_str, 'NX_DATE_TIME')
            _dataset(entry_nxgrp, 'end_time', self._stop_time_str, 'NX_DATE_TIME')
            _dataset(entry_nxgrp, 'definition', 'NXstxm', 'NX_CHAR')
            _dataset(entry_nxgrp, 'version', '1.0', 'NX_CHAR')

            self.specific_scan_funcs = self.get_scan_specific_funcs(scan_type)

            #create entry groups
            self.create_collection_group(entry_nxgrp, doc, scan_type)

            ctrl_nxgrp = self.create_stack_control_group(entry_nxgrp, doc, scan_type)
            self.specific_scan_funcs['mod_nxctrl'](self, ctrl_nxgrp, doc,scan_type)

            data_nxgrp = self.create_stack_nxdata_group(entry_nxgrp, self._primary_det_prefix, doc, scan_type)
            self.specific_scan_funcs['mod_nxdata'](self, data_nxgrp, doc, scan_type)

            # self.create_scan_specific_nxdata_group(entry_nxgrp, self._primary_det_prefix, doc, scan_type)
            #inst_nxgrp = self.create_instrument_group(entry_nxgrp, doc, scan_type)

            inst_nxgrp = self.create_base_instrument_group(entry_nxgrp, doc, scan_type)
            self.specific_scan_funcs['mod_nxinst'](self, inst_nxgrp, doc, scan_type)
            #
            self.create_base_sample_group(entry_nxgrp, doc, scan_type)

            nf.close()
        except:
            _logger.error('Problem saving file[%s]' % self._tmp_fname)
            if(nf is not None):
                nf.close()
            os.rename(self._tmp_fname, self._tmp_fname + '.err')


    def get_scan_specific_funcs(self, scan_type):
        '''
        using the scan-type that is specified, return a dict of functions that will be used be the data saving
        main routine

                'detector_image', \
				'osa_image', \
				'osa_focus', \
				'sample_focus', \
				'sample_point_spectra', \
				'sample_line_spectra', \
				'sample_image', \
				'sample_image_stack', \
				'generic_scan', \
				'coarse_image', \
				'coarse_goni', \
				'tomography'

        :param scan_type:
        :return:
        '''
        single_2d_scans = [scan_types.DETECTOR_IMAGE, scan_types.OSA_IMAGE, scan_types.COARSE_IMAGE, \
                           scan_types.COARSE_GONI]
        focus_scans = [ scan_types.SAMPLE_FOCUS, scan_types.OSA_FOCUS]

        single_image_scans = [scan_types.SAMPLE_IMAGE]
        stack_type_scans = [scan_types.SAMPLE_IMAGE_STACK, scan_types.TOMOGRAPHY]

        dct = {}
        if(scan_type is scan_types.GENERIC_SCAN):
            dct['mod_nxctrl'] = modify_generic_scan_ctrl_data_grps
            dct['mod_nxdata'] = modify_generic_scan_nxdata_group
            dct['mod_nxinst'] = modify_generic_scan_instrument_group

        elif(scan_type in single_2d_scans):
            dct['mod_nxctrl'] = modify_2posner_ctrl_data_grps
            dct['mod_nxdata'] = modify_base_2d_nxdata_group
            dct['mod_nxinst'] = modify_base_2d_instrument_group

        elif (scan_type in focus_scans):
            dct['mod_nxctrl'] = modify_focus_ctrl_data_grps
            dct['mod_nxdata'] = modify_focus_nxdata_group
            dct['mod_nxinst'] = modify_focus_instrument_group

        elif(scan_type in single_image_scans):
            dct['mod_nxctrl'] = modify_single_image_ctrl_data_grps
            dct['mod_nxdata'] = modify_single_image_nxdata_group
            dct['mod_nxinst'] = modify_single_image_instrument_group

        elif (scan_type in stack_type_scans):
            dct['mod_nxctrl'] = modify_stack_ctrl_data_grps
            dct['mod_nxdata'] = modify_stack_nxdata_group
            dct['mod_nxinst'] = modify_single_image_instrument_group



        return(dct)

    def create_scan_specific_nxdata_group(self, entry_nxgrp, cntr_nm, doc, scan_type):
        '''
        a function that determmines the scan type and calls the proper function to create the NXdata group
        :param entry_nxgrp:
        :param cntr_nm:
        :param doc:
        :param scan_type:
        :return:
        '''
        single_2d_scans = [scan_types.DETECTOR_IMAGE, scan_types.OSA_IMAGE, scan_types.COARSE_IMAGE, \
                           scan_types.COARSE_GONI]

        three_d_scans = [scan_types.DETECTOR_IMAGE, scan_types.OSA_IMAGE, scan_types.OSA_FOCUS, scan_types.SAMPLE_FOCUS,
                         scan_types.SAMPLE_IMAGE_STACK, scan_types.COARSE_IMAGE, scan_types.COARSE_GONI, \
                         scan_types.TOMOGRAPHY]

        if(scan_type is scan_types.GENERIC_SCAN):
            create_generic_scan_nxdata_group(entry_nxgrp, cntr_nm, doc)
        elif(scan_type in single_2d_scans):
            create_base_2d_nxdata_group(entry_nxgrp, cntr_nm, doc, scan_type)


    def get_current_uid(self):
        return(self._cur_uid)

    def create_collection_group(self, nxgrp, doc, scan_type):
        '''

        :param nxgrp:
        :param doc:
        :param scan_type:
        :return:
        '''
        coll_nxgrp = _group(nxgrp, 'collection', 'NXcollection')

        #js_str = dict_to_json_string(self._cur_scan_md[doc['run_start']]['wdg_com'], to_unicode=True)
        scan_grp = _group(coll_nxgrp, 'scan_request', 'NXscanDefinition')
        js_str = self._cur_scan_md[doc['run_start']]['wdg_com']
        _dataset(scan_grp, 'scan_request', js_str, 'NXchar')
        #walk all of the baseline devices and create a signal entry in collection group
        for k, dct in self._data['baseline'].items():
            k = k.replace('_val','')
            self.make_signal(coll_nxgrp, k, dct[self._cur_uid])



    def make_signal(self, nxgrp, name, dct, modify=False):
        # try:
        if (not modify):
            nx_dct = readin_base_classes('NXsensor')

        if (not modify):
            tmgrp = make_NXclass(nxgrp, name, 'NXsensor', nx_dct['NXsensor'], nxgrp)
        else:
            tmgrp = nxgrp[name]

        #use the value of the signal at end of scan [1], [0] is the start of the scan
        tmgrp['value'][()] = dct['data'][1]
        #strip the 'PV:' off of the source name
        tmgrp['name'][()] = dct['info']['source'].replace('PV:','')
        # tmgrp['measurement'][()] = measurement
        tmgrp['short_name'][()] = dct['info']['object_name']
        tmgrp['type'][()] = dct['info']['units']
        tmgrp['run_control'][()] = 1  # Is data collection controlled or synchronised to this quantity: 1=no

        remove_unused_NXsensor_fields(tmgrp)

    def create_base_instrument_group(self, nxgrp, doc, scan_type):
        '''

        :param nxgrp:
        :param doc:
        :param scan_type:
        :return:
        '''
        inst_nxgrp = _group(nxgrp, 'instrument', 'NXinstrument')
        self.make_source(inst_nxgrp, doc)
        self.make_monochromator(inst_nxgrp, doc)
        self.make_epu(inst_nxgrp, doc)
        self.make_zoneplate(inst_nxgrp, doc)

        return(inst_nxgrp)

    def make_detector(self, nxgrp, name, data, dwell, npoints, units='counts'):
        '''

        :param nxgrp:
        :param name:
        :param data:
        :param dwell:
        :param npoints:
        :return:
        '''
        grp = _group(nxgrp, name, 'NXdetector')
        if (data is None):
            _dataset(grp, nxkd.NXD_DATA, np.zeros(npoints, dtype=np.float32), 'NX_FLOAT')
        else:
            _dataset(grp, nxkd.NXD_DATA, data, 'NX_FLOAT')
        _dataset(grp, 'count_time', make_1d_array(npoints, dwell), 'NX_FLOAT')
        _dataset(grp, 'unit', units, 'NX_CHAR')


    def make_monochromator(self, nxgrp, doc, modify=False):
        '''

        :param data_dct:
        :param modify:
        :return:
        '''
        rois = self.get_rois_from_current_md(doc['run_start'])
        xnpoints = rois['X']['NPOINTS']
        ynpoints = rois['Y']['NPOINTS']

        #epnts = dct_get(data_dct, 'NUM_P.EV')
        epnts = self.get_baseline_all_data(self.get_devname(DNM_MONO_EV_FBK) + '_val')
        #just use the value of energy at start
        epnt = epnts[0]
        e_arr = make_1d_array(xnpoints * ynpoints, epnt)

        if (modify):
            del nxgrp['monochromator']['energy']
            grp = nxgrp['monochromator']
        else:
            grp = _group(nxgrp, 'monochromator', 'NXmonochromator')

        _dataset(grp, 'energy', e_arr, 'NX_FLOAT')

    def make_epu(self, nxgrp, doc, modify=False, pol_pnt=0):
        """
        The epu polaraization is a confusing situation, the implementation of the polarization number
        """
        rois = self.get_rois_from_current_md(doc['run_start'])
        xnpoints = rois['X']['NPOINTS']
        ynpoints = rois['Y']['NPOINTS']



        ang = self.get_baseline_all_data(self.get_devname(DNM_EPU_POL_ANGLE) + '_val')[0]
        ang_arr = make_1d_array(xnpoints * ynpoints, ang)
        epu_gap_offset = self.get_baseline_all_data(self.get_devname(DNM_EPU_GAP_OFFSET) + '_val')[0]
        epu_gap_offset_arr = make_1d_array(xnpoints * ynpoints, epu_gap_offset)
        epu_gap_fbk = self.get_baseline_all_data(self.get_devname(DNM_EPU_GAP_FBK) + '_val')[0]
        epu_gap_fbk_arr = make_1d_array(xnpoints * ynpoints, epu_gap_fbk)
        epu_harm = int(self.get_baseline_all_data(self.get_devname(DNM_EPU_HARMONIC_PV) + '_val')[0])
        epu_harm_arr = make_1d_array(xnpoints * ynpoints, epu_harm)

        #stokes = dct_get(data_dct, 'NUM_P.STOKES')
        # harfd code these for now
        stokes = translate_pol_id_to_stokes_vector(pol_pnt)


        # (use_pol_angle, mode_str) = get_nx_standard_epu_mode(pvs['Epu_pol_fbk'][RBV])
        (use_pol_angle, mode_str) = get_nx_standard_epu_mode(pol_pnt)
        if (use_pol_angle):
            pol_angle_arr = ang_arr
        else:
            pol_angle_arr = ang_arr
            #pol_angle.fill(0.0)

        epu_harmonic = get_nx_standard_epu_harmonic_new(epu_harm)

        if (not modify):
            grp = _group(nxgrp, 'epu', 'NXinsertion_device')
            _dataset(grp, 'type', 'elliptically polarizing undulator', 'NX_CHAR')
            _dataset(grp, 'mode', mode_str, 'NX_CHAR')
            _dataset(grp, 'linear_inclined_angle', pol_angle_arr, 'NX_ANGLE')
            _dataset(grp, 'gap', epu_gap_fbk_arr, 'NX_FLOAT', nx_units='NX_LENGTH')
            _dataset(grp, 'gap_offset', epu_gap_offset_arr, 'NX_FLOAT', nx_units='NX_LENGTH')
            _dataset(grp, 'harmonic', epu_harm_arr, 'NX_INT', nx_units='NX_UNITLESS')

            _dataset(grp, 'stokes', np.tile(stokes, (1, 1)), 'NX_FLOAT', nx_units='NX_UNITLESS')

    def make_zoneplate(self, nxgrp, doc, modify=False):
        """
        The fresnel zoneplate definition, only a subset of standard used because
        I don't not have all the info to populate all fields

        fields:
        central_stop_diameter:NX_FLOAT
                    central_stop_material:NX_CHAR
                  central_stop_thickness:NX_FLOAT
        fabrication:NX_CHAR
                  focus_parameters:NX_FLOAT[]
                  mask_material:NX_CHAR
                  mask_thickness:NX_FLOAT
        outer_diameter:NX_FLOAT
        outermost_zone_width:NX_FLOAT
                  support_membrane_material:NX_CHAR
                  support_membrane_thickness:NX_FLOAT
                  zone_height:NX_FLOAT
                  zone_material:NX_CHAR
                  zone_support_material:NX_CHAR
        """
        zp_def = self.get_stxm_zp_def(doc['run_start'])
        if (not modify):
            grp = _group(nxgrp, 'zoneplate', 'NXfresnel_zone_plate')
            _dataset(grp, 'name', 'zone plate #%d' % zp_def['zp_idx'], 'NX_CHAR')
            _dataset(grp, 'outer_diameter', zp_def['zpD'], 'NX_FLOAT', nx_units='NX_LENGTH')
            _dataset(grp, 'central_stop_diameter', zp_def['zpCStop'], 'NX_FLOAT', nx_units='NX_LENGTH')
            _dataset(grp, 'outermost_zone_width', zp_def['zpOZone'], 'NX_FLOAT', nx_units='NX_LENGTH')
            _dataset(grp, 'fabrication', 'etched', 'NX_CHAR')



    def make_source(self, nxgrp, doc, modify=False):
        '''

        :param nxgrp:
        :param data_dct:
        :param modify:
        :return:
        '''
        if (not modify):
            ring_cur_signame = self.get_devname(DNM_RING_CURRENT) + '_val'
            if (ring_cur_signame in self._data['baseline'].keys()):
                rois = self.get_rois_from_current_md(doc['run_start'])
                # use the baseline start/stop values and create a sequence from start to stop
                #strt, stp = self._data['baseline'][ring_cur_signame][uid]['data']
                strt, stp = self.get_baseline_all_data(ring_cur_signame)
                sr_data = np.linspace(strt, stp, rois['X']['NPOINTS'], dtype=np.float32)
            else:
                sr_data = np.array(self._data['primary'][ring_cur_signame]['data'], dtype=np.float32)

            src_grp = _group(nxgrp, 'source', 'NXsource')
            _dataset(src_grp, 'type', 'Synchrotron X-ray Source', 'NX_CHAR')
            _dataset(src_grp, 'name', 'Canadian Lightsource Inc.', 'NX_CHAR')
            _dataset(src_grp, 'probe', 'x-ray', 'NX_CHAR')
            _dataset(src_grp, 'current', sr_data, 'NX_FLOAT', 'NX_CURRENT')

        else:
            # nothing to modify
            pass

    def get_devname(self, lu_nm):
        '''

        :param lu_nm:
        :return:
        '''
        if(lu_nm in self._kwargs['rev_lu_dct'].keys()):
            return(self._kwargs['rev_lu_dct'][lu_nm])
        else:
            print('nxstxm_primary: get_devname: Oh Oh ')
            return(None)


    def get_baseline_start_data(self, src_devnm):
        '''

        :param src_devnm:
        :return:
        '''
        return(self._data['baseline'][src_devnm][self._cur_uid]['data'][0])

    def get_baseline_stop_data(self, src_devnm):
        '''

        :param src_devnm:
        :return:
        '''
        return(self._data['baseline'][src_devnm][self._cur_uid]['data'][1])

    def get_baseline_all_data(self, src_devnm):
        '''

        :param src_devnm:
        :return:
        '''
        return(self._data['baseline'][src_devnm][self._cur_uid]['data'])

    def get_sample_x_data(self, _type='all'):
        '''
        gets data from baseline stream
        _type can be 'all, or 'start', or 'stop'
        :param _type:
        :return:
        '''
        x_src = self.get_devname(DNM_SAMPLE_X)
        if(_type is 'all'):
            return(self.get_baseline_all_data(x_src))
        elif(_type is 'start'):
            return(self.get_baseline_start_data(x_src))
        elif (_type is 'stop'):
            return (self.get_baseline_stop_data(x_src))
        else:
            return(None)

    def get_sample_y_data(self, _type='all'):
        '''
        gets data from baseline stream
        _type can be 'all, or 'start', or 'stop'
        :param _type:
        :return:
        '''
        y_src = self.get_devname(DNM_SAMPLE_Y)
        if(_type is 'all'):
            return(self.get_baseline_all_data(y_src))
        elif(_type is 'start'):
            return(self.get_baseline_start_data(y_src))
        elif (_type is 'stop'):
            return (self.get_baseline_stop_data(y_src))
        else:
            return(None)


    def create_base_control_group(self, entry_nxgrp, doc, scan_type):
        '''

        :param entry_nxgrp:
        :param doc:
        :param scan_type:
        :return:
        '''
        cntrl_nxgrp = _group(entry_nxgrp, 'control', 'NXmonitor')
        #_dataset(cntrl_nxgrp, nxkd.NXD_DATA, oneD_srdata, 'NX_NUMBER')
        ev_src = self.get_devname(DNM_ENERGY)
        _dataset(cntrl_nxgrp, 'energy', [self.get_baseline_start_data(ev_src)], 'NX_FLOAT')
        _dataset(cntrl_nxgrp, 'sample_x', self.get_sample_x_data('start'), 'NX_FLOAT')
        _dataset(cntrl_nxgrp, 'sample_y', self.get_sample_y_data('start'), 'NX_FLOAT')

        # this should be an array the same shape as the 'data' group in NXdata filled with the storagering current
        #sr_data = np.array(self._data['primary'][self.get_devname(DNM_RING_CURRENT) + '_val']['data'],
        #                   dtype=np.float32)

        # if(scan_type in single_entry_scans):
        #     self.create_2posner_ctrl_str_attrs(cntrl_nxgrp, doc)
        #     self.create_2posner_ctrl_data_grps(cntrl_nxgrp, doc)
        _string_attr(cntrl_nxgrp, 'signal', 'data')
        return(cntrl_nxgrp)

    def create_stack_control_group(self, entry_nxgrp, doc, scan_type):
        '''

        :param entry_nxgrp:
        :param doc:
        :param scan_type:
        :return:
        '''
        cntrl_nxgrp = _group(entry_nxgrp, 'control', 'NXmonitor')

        ev_setpoints = self._wdg_com['SINGLE_LST']['EV_ROIS']
        _dataset(cntrl_nxgrp, 'energy', ev_setpoints, 'NX_FLOAT')
        _dataset(cntrl_nxgrp, 'sample_x', self.get_sample_x_data('start'), 'NX_FLOAT')
        _dataset(cntrl_nxgrp, 'sample_y', self.get_sample_y_data('start'), 'NX_FLOAT')

        _string_attr(cntrl_nxgrp, 'signal', 'data')
        return(cntrl_nxgrp)


    def fix_aborted_data(self, data_lst, npoints):
        '''
        if the scabn was aborted then we have fewer data points than we expected, create a square array the size
        of that we were expecting and copy the datapoints we did get into it
        :param data_lst:
        :param npoints:
        :return:
        '''
        zarr = np.zeros(npoints, dtype=np.int32)
        darr = np.array(data_lst, dtype=np.int32)
        if len(darr) < len(zarr):
            c = zarr.copy()
            c[:len(darr)] += darr
        else:
            c = darr.copy()
            c[:len(zarr)] += zarr
        return(c)


    def fix_posner_nm(self, nm_str):
        '''

        :param nm_str:
        :return:
        '''
        l = nm_str.lower()
        l = l.replace('.','_')
        return(l)

    def get_rois_from_current_md(self, uid):
        '''
        convienience function, assumes self._cur_sp_id has been set
        :param uid:
        :return:
        '''
        rois = self._cur_scan_md[uid]['rois'][self._cur_sp_id]
        return(rois)



    def create_base_nxdata_group(self, entry_nxgrp, cntr_nm, doc, scan_type):
        '''

        :param entry_nxgrp:
        :param cntr_nm:
        :param doc:
        :param scan_type:
        :return:
        '''
        resize_data = False
        data_nxgrp = _group(entry_nxgrp, cntr_nm, 'NXdata')

        #make sure dwell is in seconds
        dwell = np.float32(self._cur_scan_md[doc['run_start']]['dwell']) * 0.001
        _dataset(data_nxgrp, 'count_time', np.array([dwell], dtype=np.float32), 'NX_FLOAT')

        ev_src = self.get_devname(DNM_ENERGY)
        _dataset(data_nxgrp, 'energy', [self.get_baseline_start_data(ev_src)], 'NX_FLOAT')
        _dataset(data_nxgrp, 'sample_x', self.get_sample_x_data('start'), 'NX_FLOAT')
        _dataset(data_nxgrp, 'sample_y', self.get_sample_y_data('start'), 'NX_FLOAT')

        pol_src = self.get_devname(DNM_EPU_POLARIZATION)
        _dataset(data_nxgrp, 'epu_polarization', self.get_baseline_start_data(pol_src), 'NX_FLOAT')

        scan_type_str = self.get_stxm_scan_type_str(doc['run_start'])
        _dataset(data_nxgrp, 'stxm_scan_type', scan_type_str, 'NX_CHAR')

        return(data_nxgrp)


    def create_stack_nxdata_group(self, entry_nxgrp, cntr_nm, doc, scan_type):
        '''

        :param entry_nxgrp:
        :param cntr_nm:
        :param doc:
        :param scan_type:
        :return:
        '''
        resize_data = False
        data_nxgrp = _group(entry_nxgrp, cntr_nm, 'NXdata')

        #make sure dwell is in seconds
        dwell = np.float32(self._cur_scan_md[doc['run_start']]['dwell']) * 0.001
        _dataset(data_nxgrp, 'count_time', np.array([dwell], dtype=np.float32), 'NX_FLOAT')

        #ev_src = self.get_devname(DNM_ENERGY)
        ev_setpoints = self._wdg_com['SINGLE_LST']['EV_ROIS']
        #_dataset(data_nxgrp, 'energy', [self.get_baseline_start_data(ev_src)], 'NX_FLOAT')
        _dataset(data_nxgrp, 'energy', ev_setpoints, 'NX_FLOAT')
        _dataset(data_nxgrp, 'sample_x', self.get_sample_x_data('start'), 'NX_FLOAT')
        _dataset(data_nxgrp, 'sample_y', self.get_sample_y_data('start'), 'NX_FLOAT')

        pol_src = self.get_devname(DNM_EPU_POLARIZATION)
        _dataset(data_nxgrp, 'epu_polarization', self.get_baseline_start_data(pol_src), 'NX_FLOAT')

        scan_type_str = self.get_stxm_scan_type_str(doc['run_start'])
        _dataset(data_nxgrp, 'stxm_scan_type', scan_type_str, 'NX_CHAR')

        return(data_nxgrp)

    def get_stxm_scan_type_str(self, uid):
        scan_type = self._cur_scan_md[uid]['scan_type']
        s = scan_types[scan_type].replace('_',' ')
        return(s)

    def get_stxm_scan_type(self, uid):
        scan_type = self._cur_scan_md[uid]['scan_type']
        return(scan_type)

    def get_stxm_zp_def(self, uid):
        zp_def = self._cur_scan_md[uid]['zp_def']
        return (zp_def)

    def create_base_sample_group(self, entry_nxgrp, doc, scan_type):
        '''

        :param entry_nxgrp:
        :param doc:
        :param scan_type:
        :return:
        '''
        angle = self.get_baseline_start_data(self.get_devname(DNM_GONI_THETA))
        smpl_nxgrp = _group(entry_nxgrp, 'sample', 'NXsample')
        _dataset(smpl_nxgrp, 'rotation_angle', angle, 'NX_FLOAT')

    def get_primary_det_nm(self, uid):
        '''
        :return:
        '''
        if('primary_det' not in self._cur_scan_md[uid].keys()):
            print(
                'get_primary_det_nm: looks like a prefix for the primary detector was not specified in the plan metadata')
            return (None)

        primary_det_prefix = self._cur_scan_md[uid]['primary_det']
        for k in self._data['primary'].keys():
            if(k.find(primary_det_prefix) > -1):
                return(k)


    def get_primary_det_prefix(self, uid):
        return(self._cur_scan_md[uid]['primary_det'])

    def make_devs(self, nf, dev_dct):
        for dev_nm, data in dev_dct.items():
            #info = dev['info']
            _grp = _group(nf, dev_nm, 'none')
            _string_attr(_grp, 'PVNAME', dev_nm)
            if(dev_nm.find('description') is -1):
                _dataset(_grp, 'data', data, 'number')


    def return_dct_of_this_field_and_val(self, dct, field, val):
        '''
        search through dict looking for the keys that has this field and value
        then return key'''
        res = {}
        for k in list(dct.keys()):
            f_keys = list(dct[k]['info'].keys())
            if field in f_keys:
                if (val == dct[k]['info'][field]):
                    res[k] = dct[k]
        return (res)


    def stop(self, doc):
        '''Add `stop` document information to the metadata dictionary.
                This method adds the stop document information to the metadata
                dictionary. In addition it also creates the metadata '.json' file and
                exports the metadata dictionary to it.
                Parameters:
                -----------
                doc : dict
                    RunStop document

                    {'run_start': 'f66a3e61-dcbb-4975-9fc8-c38a0255fb1b',
                     'time': 1552058010.90581,
                     'uid': '9aa11d7a-4edd-4c8d-9a7d-b82fcf92fdfb',
                     'exit_status': 'success',
                     'num_events': {'oranges': 101}}

                     scan_types = 'detector_image', \
                'osa_image', \
                'osa_focus', \
                'sample_focus', \
                'sample_point_spectra', \
                'sample_line_spectra', \
                'sample_image', \
                'sample_image_stack', \
                'generic_scan', \
                'coarse_image', \
                'coarse_goni', \
                'tomography'


                '''
        # add the stop doc to self._meta.
        stop_time = localtime(doc['time'])
        self._stop_time_str = time.strftime("%Y-%m-%dT%H:%M:%S", stop_time)
        scan_type = self._cur_scan_md[doc['run_start']]['scan_type']

        if (scan_type is scan_types.DETECTOR_IMAGE):
            # print('processing a detector scan')
            pass
        elif (scan_type is scan_types.COARSE_GONI):
            # print('processing a Coarse Goniometer scan')
            pass

        dets = {}
        skip_list = ['_units']
        for k, v in self._data['primary'].items():
            if (not self._skip(k, skip_list)):
                dlst = self._data['primary'][k][self._cur_uid]['data']
                arr = np.array(dlst)
                # dets[k] = arr[:,1]
                dets[k] = arr

        self._stop_uids['uid'] = doc['uid']
        self._stop_uids['run_start'] = doc['run_start']

        if (doc['uid'] in self._streamnames.keys()):
            streamname = self._streamnames[doc['uid']]
            # print('\nSTOP: for stream [%s]' % streamname)
        else:
            # print('\nSTOP: for doc[run_start]= %s' % doc['run_start'])
            pass
        has_baseline = False
        for k, v in self._streamnames.items():
            if(v.find('baseline') > -1):
                has_baseline = True

        if(not os.path.exists(self._tmp_fname)):
            self.create_file_attrs()

        #if((self._kwargs['first_uid'].find(self._cur_uid) > -1) and has_baseline):
        if (has_baseline):

        #if(self.sp_id not in self._processed_sp_ids):
            self.create_entry_structure(doc, scan_type=scan_type)
            self._processed_sp_ids.append(self.sp_id)
        else:
            # this is an ev only run so just update the data
            print('modifying data to an existing entry')
            uid = self.get_current_uid()
            det_nm = self.get_primary_det_nm(uid)
            det_prfx = self.get_primary_det_prefix(uid)
            dat_arr = np.array(self._data['primary'][det_nm][uid]['data'])

            #now place it in correct entry/counter
            self.modify_entry_data(self.entry_nm, det_prfx, dat_arr)


        # final_fname = self._tmp_fname.replace('.tmp','')
        # os.rename(self._tmp_fname, final_fname)
        # _logger.info('nxstxm_primary: finished exporting [%s]' % final_fname)
        # print('nxstxm_primary: finished exporting [%s]' % final_fname)

        # reset scan_type
        self._scan_type = None


    def modify_entry_data(self, entry_nm, det_prfx, data):
        nf = None
        try:
            nf = h5py.File(self._tmp_fname, 'a')

            if(entry_nm in nf.keys()):
                #the entry exists
                egrp = nf[entry_nm]

                if(det_prfx in egrp.keys()):
                    #the NXdata counter exists
                    cntr_data = egrp[det_prfx]

                    #add the data
                    print('add the data here for e_idx=%d' % self.e_idx)
                    cntr_data['data'][self.e_idx] = data

                else:
                    _logger.error('[%s] NXdata group doesnt exist in [%s]' % (det_prfx, entry_nm))

            else:
                _logger.error('[%s] NXentry group doesnt exist in file [%s]' % (entry_nm, self._tmp_fname))

            nf.close()

        except:
            _logger.error('Problem modifying data in [%s]' % self._tmp_fname)
            if (nf is not None):
                nf.close()
            os.rename(self._tmp_fname, self._tmp_fname + '.err')
