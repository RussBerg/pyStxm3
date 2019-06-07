'''
Created on Sep 26, 2016

@author: bergr
'''

from cls.scanning.BaseScanSignals import BaseScanSignals

from bcm.devices import BaseDevice

from cls.utils.log import get_module_logger
from cls.utils.dict_utils import dct_get, dct_put

_logger = get_module_logger(__name__)

class SScanClass(BaseScanSignals):
    """
    This class wraps a Scan device and attaches the signals used to define the API 
    I am using to run scans. This way each individual scan (<prefix>:scan1, <prefix>:scan2 etc) will 
    provide the same signals as an abstract scan made up of individual scans
    
    :param scan_name: The name of an sscan record
    :type scan_name: A python string ex: ambstxm:focus:scan1.

    :param section_name: A name for this scan that will be used to locate the sscan contents in the CFG dict under [SSCAN][section_name]
    :type section_name: A python string ex: X
    
    :param mtr: An instance of Motor() that is used in this sscan
    :type mtr: An instance of the Motor class that was initialized in the BL1610.py file and stored in the MAIN_OBJ[DEVICES] dict 

    :returns: None
     
    """
    
    
    def __init__(self, scan_name, section_name, posner=None, main_obj=None):
        """
        __init__(): description

        :param scan_name: scan_name description
        :type scan_name: scan_name type

        :param section_name: section_name description
        :type section_name: section_name type

        :param posner=None: posner=None description
        :type posner=None: posner=None type

        :returns: None
        """
        super(SScanClass, self).__init__()
        self.scan_name = scan_name
        self.section_name = section_name
        if(main_obj is None):
            _logger.error('main_obj must be an instance if MAIN_OBJ, cannot be None')
            exit()
        self.main_obj = main_obj
        #self.sscan = Scan(scan_name)
        self.sscan = self.main_obj.device(scan_name)
        
        self.is_data_level = False
        self.is_top_level = False
        
        idx = scan_name.find(':scan')
        num_idx = scan_name.find(':scan') + 5
        scan_num =  int(scan_name[num_idx:]) 
        
        self.pvs = BaseDevice()
        #self.mtr = mtr
        self.positioners = {}
        self.P1 = None
        self.P2 = None
        self.P3 = None
        self.P4 = None

        self._rprt_dct = {'scan_name': scan_name, 'section_name': section_name,
                          'scan_num': scan_num,
                          'P1': self.P1, 'P2': self.P2, 'P3': self.P3, 'P4': self.P4}

        self.num_detectors = 0
        if(posner != None):
            #assume only a single positioner will be used
            self.set_positioner(1, posner)
        
        self.trace_faze_fld = False
        
        #self.AbortScans_PROC = self.pvs.add_pv(scan_name[0:idx] + ':AbortScans.PROC')
        self.AbortScans_PROC = self.pvs.add_pv(scan_name[0:idx] + ':abort_all.PROC')
        self.scanPause = self.pvs.add_pv(scan_name[0:idx] + ':scanPause')
        self.clearAll = self.pvs.add_pv(scan_name[0:idx] + ':clear_all.PROC')
        self.reload = self.pvs.add_pv(scan_name[0:idx] + ':reload_cmd.PROC')
        self.ttl_progress = self.pvs.add_pv(scan_name[0:idx] + ':ttl_progress_%d' % scan_num)
        self.reset_ttl_progress = self.pvs.add_pv(scan_name[0:idx] + ':ttl_progress:reset.PROC')

        # support for toggling bidirectionality, these pvs are placeholders for the values that will
        # be toggled at the end of each scan (because <scan prefix>:toggle:x.VAL will be written to by the ASPV field each time through
        # then the set of records used for toggling will alternate the start and end values so that each execution of the scan will
        # result in the start and end values swapping
        #self.tgl_x_start = self.pvs.add_pv(scan_name[0:idx] + ':toggle:x:start')
        #self.tgl_x_end = self.pvs.add_pv(scan_name[0:idx] + ':toggle:x:end')

        self.cb_idxs = []
        self.scan_done = True
        self.scan_started = False
        self.scan_pending = True
        self.scan_paused = False
    
        self.num_points = None
        self.scan_data = None

        self.faze = 0

        self.det_data = {}
        #self.sscan.add_callback('D01DA', self.on_detector_monitor)
        #self.sscan.add_callback('D02DA', self.on_detector_monitor)
        #self.ttl_progress.changed.connect(self.on_progress)

        self.callback_dct = {'SMSG':None, 'FAZE':None, 'CPT':None, 'DATA':None, 'BUSY':None }

    def __repr__(self):
        state_txts = []
        for k,v in list(self._rprt_dct.items()):
            state_txts.append(' %12s: %s' % (k, str(v)))
        state_txts.append(self.sscan_faze_cb_report())
        state_txts.sort()
        txt = "<%s: %s\n%s\n>" % (self.__class__.__name__, self.scan_name, '\n'.join(state_txts))
        return txt

    def sscan_faze_cb_report(self):
        '''
        a convienience function to get the current state of all scan callbacks for FAZE field of SSCAN record
        :param sscans:
        :return:
        '''
        cbs = self.sscan._pvs['FAZE'].callbacks
        num_cbs = len(list(cbs.keys()))
        cb_ids = list(cbs.keys())
        id_str = ''
        for _id in cb_ids:
            id_str += '%d ' % _id

        return('[%d] cbs for FAZE with Ids [%s]' % (num_cbs, id_str))




    def connect_callbacks(self):
        '''
        add a callback for the few fields that we care about monitoring
        :return:
        '''
        self.callback_dct['SMSG'] = self.sscan.add_callback('SMSG', self.on_scan_status)
        self.callback_dct['FAZE'] = self.sscan.add_callback('FAZE', self.on_faze)
        self.callback_dct['CPT'] = self.sscan.add_callback('CPT', self.on_cpt)
        self.callback_dct['DATA'] = self.sscan.add_callback('DATA', self.on_data)
        self.callback_dct['BUSY'] = self.sscan.add_callback('BUSY', self.on_busy)
        #self.callback_dct['BUSY'] = self.sscan.add_callback('BUSY', self.on_busy, sscan=self)

        print('[%s] using id [%d] for FAZE' % (self.get_name(), self.callback_dct['FAZE']))

    def disconnect_callbaks(self):
        '''
        remove a callback for the few fields that we care about monitoring
        :return:
        '''
        self.sscan.remove_callbacks('SMSG', self.callback_dct['SMSG'])
        self.sscan.remove_callbacks('FAZE', self.callback_dct['FAZE'])
        self.sscan.remove_callbacks('CPT', self.callback_dct['CPT'])
        self.sscan.remove_callbacks('DATA',self.callback_dct['DATA'])
        self.sscan.remove_callbacks('BUSY', self.callback_dct['BUSY'])

        self.callback_dct = {'SMSG': None, 'FAZE': None, 'CPT': None, 'DATA': None, 'BUSY': None}

    def on_progress(self, val):
        """
        on_progress(, val): description

        :returns: None
        """        
        self.progress.emit(val)
    
    # def reload_base_scan_config(self):
    #     """
    #     reload_base_scan_config(): description
    #
    #     :returns: None
    #     """
    #     from cls.appWidgets.guiWaitLoop import gui_sleep # https://gist.github.com/niccokunzmann/8673951
    #
    #     self.cmd_file_pv.put(self.cmd_file)
    #     self.clear_all()
    #     self.reload.put(1)
    #
    #     #time.sleep(2.0)
    #     gui_sleep(1.0)
    #     print 'done reloading'
        
    

        
    def start(self):
        """
        start(): description

        :returns: None
        """
        #self.reset_ttl_progress.put(1)
        self.num_points = self.sscan.get('NPTS') 
        self.scan_started = False
        self.sscan.put('EXSC',1)
        
    def stop(self):
        """
        stop(): description

        :returns: None
        """
        #when an abort is called push it 3 times to ensure that the sscan record is not going to 
        # get stuck "waiting for callbacks" 
        for i in range(3):
            self.AbortScans_PROC.put(1)
            
        self.abort_scan.emit()
    
    def pause(self, do_pause):
        """
        pause(): description

        :param do_pause: do_pause description
        :type do_pause: do_pause type

        :returns: None
        """
        if(not do_pause):
            self.scan_paused = False
            self.scanPause.put(0)
        else:
            self.scan_paused = True
            self.scanPause.put(1)    
    
    def clear_all(self):
        """
        clear_all(): description

        :returns: None
        """
        self.clearAll.put(1)
        
    def set_scan_pending(self):
        """
        set_scan_pending(): description

        :returns: None
        """
        self.scan_pending = True
    
    def set_section_name(self, name):
        """
        set_section_name(): description

        :param name: name description
        :type name: name type

        :returns: None
        """
        self.section_name = name
    
    def set_num_points(self, npts):
        """
        set_num_points(): description

        :param npts: npts description
        :type npts: npts type

        :returns: None
        """
        self.num_points = npts
    
    def set_is_data_level(self, data_lvl=False):
        """
        set_is_data_level(): description

        :param data_lvl=False: data_lvl=False description
        :type data_lvl=False: data_lvl=False type

        :returns: None
        """
        self.is_data_level = data_lvl

    def set_is_top_level(self, top_lvl=False):
        """
        set_is_top_level(): description

        :param top_lvl=False: top_lvl=False description
        :type top_lvl=False: top_lvl=False type

        :returns: None
        """
        self.is_top_level = top_lvl
    
    def set_positioner(self, posnum, positioner):
        """
        set_positioner(): description

        :param posnum: posnum description
        :type posnum: posnum type

        :param positioner: positioner description
        :type positioner: positioner type

        :returns: None
        """
        if((posnum >0) and (posnum < 5)):
            self.positioners[posnum] = self.gen_posner_dict(posnum, positioner)
            if(posnum == 1):
                self.P1 = positioner
            elif(posnum == 2):
                self.P2 = positioner    
            elif(posnum == 3):
                self.P3 = positioner
            elif(posnum == 4):
                self.P4 = positioner    
                    
    def get_name(self):
        """
        get_name(): description

        :returns: None
        """
        return(self.sscan._prefix[0:-1])
    
    def put(self, attr, val):
        """
        put(): description

        :param attr: attr description
        :type attr: attr type

        :param val: val description
        :type val: val type

        :returns: None
        """
        self.sscan.put(attr,val)
    
    def get(self, attr):
        """
        get(): description

        :param attr: attr description
        :type attr: attr type

        :returns: None
        """
        return(self.sscan.get(attr))

    def reset_triggers(self):
        """
        reset_triggers(): description

        :returns: None
        """
        self.sscan.reset_triggers()
        
    def add_callback(self, attrib, slot):
        """
        add_callback(): description

        :param attrib: attrib description
        :type attrib: attrib type

        :param slot: slot description
        :type slot: slot type

        :returns: None
        """
        self.cb_idxs.append((attrib, self.sscan.add_callback(attrib, slot)))
    
    def on_exit(self):
        """
        on_exit(): description

        :returns: None
        """
        for (attr, cbidx) in self.cb_idxs:
            self.remove_callbacks(attr, cbidx)
    
    def gen_posner_dict(self, pos_num, posner):
        """
        gen_posner_dict(): description

        :param pos_num: pos_num description
        :type pos_num: pos_num type

        :param posner: posner description
        :type posner: posner type

        :returns: None
        """
        dct = {}
        dct_put(dct, 'P%dSM' % pos_num, 0) # linear
        dct_put(dct, 'R%dPV' % pos_num, '') # readback
        dct_put(dct, 'P%dPV' % pos_num, '') # setter
        dct_put(dct, 'P%dEU' % pos_num, 'um') # setter
        
        dct_put(dct, 'P%dSP' % pos_num, '0') # start
        dct_put(dct, 'P%dCP' % pos_num, '0') # center
        dct_put(dct, 'P%dEP' % pos_num, '0') # end
        dct_put(dct, 'P%dSI' % pos_num, '0') # step
        dct_put(dct, 'P%dWD' % pos_num, '0') # width
        dct_put(dct, 'P%dAR' % pos_num, 'um') # absolute
        dct_put(dct, 'P%dPA' % pos_num, 'um') # table of setpoints
        
        dct_put(dct, 'P%d' % pos_num, posner) # table of setpoints
        
        return(dct)
    
    def get_det_data(self):
        return(self.det_data)
    
    def on_detector_monitor(self, **kw):
        #print kw['value']
        if('pvname' not in list(self.det_data.keys())):
            self.det_data['%s' % kw['pvname']] = []
        
        self.det_data['%s' % kw['pvname']].append(kw['value'])
        
    
        
    def on_cpt(self, **kw):
        """
        on_cpt(): description

        :param **kw: **kw description
        :type **kw: **kw type

        :returns: None
        """
        pass
#         val = float(kw['value'])
#         
#         if(self.num_points > 0.0):
#             #self.num_points = 1.0
#             percent = (val / self.num_points) * 100.0
#             #print '[%s] on_cpt: emitting %.2f' % (self.scan_name, percent)
#             self.progress.emit(percent)
    
    def on_data(self, **kw):
        """
        on_data(): description

        :param **kw: **kw description
        :type **kw: **kw type

        :returns: None
        """
        #print '[%s]: DATA:  ' % (self.scan_name)
        pass
        
        
    def on_busy(self, **kw):
        """
        on_busy(): description

        :param **kw: **kw description
        :type **kw: **kw type

        :returns: None
        """
        #print '[%s]: BUSY:  %s' % (self.scan_name, kw['value'])
        val = int(kw['value'])
        if((val == 0) and self.scan_started):
            self.stopped.emit(True)

        if (val == 0):
            #print 'on_busy: scan_name = %s' % self.scan_name
            if(self.is_top_level):
                print('[%s] TOP LEVEL IS DONE' % (self.scan_name))
                self.done.emit()

            #if (self.scan_name.find('uhvstxm:scan1') > -1):
            #    print '[%s] BUSY is 0[done]' % (self.scan_name)

            if (self.is_data_level):
                self.data_ready.emit()
                #if (self.scan_name.find('uhvstxm:scan1') > -1):
                print('[%s] DATA_READY is 1' % (self.scan_name))



            #print ''

    # def on_busy(self, **kw):
    #     """
    #     on_busy(): description
    #
    #     :param **kw: **kw description
    #     :type **kw: **kw type
    #
    #     :returns: None
    #     """
    #     #print '[%s]: BUSY:  %s' % (self.scan_name, kw['value'])
    #     val = int(kw['value'])
    #     passed_self = kw['sscan']
    #     if((val == 0) and passed_self.scan_started):
    #         passed_self.stopped.emit(True)
    #
    #     if (val == 0):
    #         #print 'on_busy: scan_name = %s' % self.scan_name
    #         if(passed_self.is_top_level):
    #             print '[%s] TOP LEVEL IS DONE' % (passed_self.scan_name)
    #             passed_self.done.emit()
    #
    #         #if (self.scan_name.find('uhvstxm:scan1') > -1):
    #         #    print '[%s] BUSY is 0[done]' % (self.scan_name)
    #
    #         if (passed_self.is_data_level):
    #             passed_self.data_ready.emit()
    #             #if (self.scan_name.find('uhvstxm:scan1') > -1):
    #             print '[%s] DATA_READY is 1' % (passed_self.scan_name)

    
    def trace_FAZE(self, do):
        self.trace_faze_fld = do
    
    def on_faze(self,  **kw):
        """
        on_faze(): description

        :param **kw: **kw description
        :type **kw: **kw type

        :returns: None
        """
        """
        phase    message    meaning
        0    IDLE    Nothing is going on.
        1    INIT_SCAN    A scan is starting
        2    DO:BEFORE_SCAN    The next thing to do is trigger the before-scan link.
        3    WAIT:BEFORE_SCAN    The before-scan link has been triggered. We're waiting for its callback to come in.
        4    MOVE_MOTORS    The next thing to do is to write to positioners.
        5    WAIT:MOTORS    We've told motors to move. Now we're waiting for their callbacks to come in.
        6    TRIG_DETECTORS    The next thing to do is to trigger detectors.
        7    WAIT:DETECTORS    We've triggered detectors. Now we're waiting for their callbacks to come in.
        8    RETRACE_MOVE    The next thing to do it send positioners to their post-scan positions.
        9    WAIT:RETRACE    We've told positioners to go to their post-scan positions. Now we're waiting for their callbacks to come in.
        10    DO:AFTER_SCAN    The next thing to do is trigger the after-scan link.
        11    WAIT:AFTER_SCAN    The after-scan link has been triggered. We're waiting for its callback to come in.
        12    SCAN_DONE    The scan is finished.
        13    SCAN_PENDING    A scan has been commanded, but has not yet started
        14    PREVIEW    We're doing a preview of the scan.
        15    RECORD SCALAR DATA    Record scalar data.
        
        """

        started_states = [1]
        done_states = [12]
        data_ready_states = [10]
        
        val = int(kw['value'])
        ch_val = kw['char_value']

        if(self.faze == val):
            #make sure we arent processing repeats of same faze
            return

        self.faze = val

        #if(self.get_name().find('uhvstxm:scan2') > -1):
        #    print '[%s] FAZE = %s' % (self.get_name(), ch_val)

        if(self.trace_faze_fld):
            print('[%s]: FAZE:  %s' % (self.scan_name, kw['value']))
        #if(val == 1):
        if(val in started_states):
            if(self.scan_started == False):
                #print '[%s] SCAN STARTED [%d]' % (self.scan_name, val)
                self.scan_done = False
                self.scan_started = True
                self.scan_pending = False
                self.started.emit(True)

        if(val in data_ready_states):
            pass
            #self.data_ready.emit()
            #print '[%s] DATA_READY [%d] emitted' % (self.scan_name, val)
        elif(val == 2):
            #print '[%s] DO:BEFORE_SCAN' % (self.scan_name)
            pass
            
        elif(val == 3):
            pass

        elif(val in done_states):
            if((self.scan_done == False) and (self.scan_pending == False)):
                self.scan_done = True
                self.scan_started = False
                #if (self.scan_name.find('uhvstxm:scan1') > -1):
                #    print '[%s] emitting [done] SCAN_DONE val == %d' % (self.scan_name, val)
                #self.done.emit()

            if(self.is_data_level):
                #if(self.scan_name.find('uhvstxm:scan1') > -1):
                #    print '[%s] on_faze: if(self.is_data_level): val == %d emitting [data_ready]' % (self.scan_name, val)
                #self.data_ready.emit()
                pass

        elif(val == 13):
            self.scan_pending = True

        elif(val == 15):
            pass

    def on_scan_status(self, **kw):
        """
        on_scan_status(): description

        :param **kw: **kw description
        :type **kw: **kw type

        :returns: None
        """
        s = kw['char_value']
        self.status.emit(s)
        #_logger.info('[%s]: SMSG:  %s' % (self.scan_name, kw['value']))
    
    def get_all_detector_data(self):
        """
        get_all_detector_data(): description

        :returns: None
        """
        all_data = []
        
        #for i in range(1,70):
        for i in range(1, self.num_detectors):
            pv_attr = 'D%02dPV' % i
            pvname = self.sscan.get(pv_attr)
            if(pvname != None):
                if(len(pvname) > 0):
                    dct = self.get_detector_data(i, int(self.num_points))
                    all_data.append(dct)
        return(all_data)
            
    def get_detector_data(self, det_num, npts=None):
        """
        get_detector_data(): description

        :param det_num: det_num description
        :type det_num: det_num type

        :param npts=None: npts=None description
        :type npts=None: npts=None type

        :returns: None
        """
        """
        Data and related PV's:
        Field    Summary    Type    DCT    Initial/Default    Read    Modify    Posted    PP
        For nn in [01..70] (e.g., "D01PV", "D02PV", ... "D70PV") :
        DnnPV    data nn Process Variable name    STRING [40]    Yes    Null    Yes    Yes    No    No
        DnnNV    data nn Name Valid    LONG    No    0    Yes    Yes    Yes    No
        DnnDA    Detector nn End-Of-Scan Data Array    FLOAT[ ]    No    Null    Yes    No    Yes    No
        DnnCA    Detector nn Current-Data Array    FLOAT[ ]    No    Null    Yes    No    Yes    No
        DnnEU    Detector nn Eng. Units    STRING [16]    Yes    16    Yes    Yes    No    No
        DnnHR    Det. nn High Range    DOUBLE    Yes    0    Yes    Yes    No    No
        DnnLR    Det. nn Low Range    DOUBLE    Yes    0    Yes    Yes    No    No
        DnnPR    Det. nn Precision    SHORT    Yes    0    Yes    Yes    No    No
        DnnCV    Detector nn Current Value    FLOAT    No    0    Yes    No    Yes    No
        DnnLV    Detector nn Last Value    FLOAT    No    0    Yes    No    No    No

        """

        dat_attr = 'D%02dDA' % det_num
        pv_attr = 'D%02dPV' % det_num
        hval_attr = 'D%02dHR' % det_num
        lval_attr = 'D%02dLR' % det_num
        #print 'get_detector_data: [%s] getting [%s] ' % (self.positioner, dat_attr)
        if(npts is None):
            #get all points
            #dat = self.scn.get(dat_attr)
            dat = self.scan_data[dat_attr]
        else:
            dat = self.scan_data[dat_attr][0:npts]
        pvname = self.scan_data[pv_attr]
        hval = self.scan_data[hval_attr]
        lval = self.scan_data[lval_attr]
        dct = {}
        dct['pvname'] = pvname
        dct['lval'] = lval
        dct['hval'] = hval
        dct['data'] = dat
        dct['npts'] = npts
        return(dct)
    
    def get_positioner_points(self, pnum, npts=None):
        """
        get_positioner_points(): description

        :param pnum: pnum description
        :type pnum: pnum type

        :param npts=None: npts=None description
        :type npts=None: npts=None type

        :returns: None
        """
        dat_attr = 'P%dRA' % pnum
        try:
            #print 'get_positioner_points: [%s] getting [%s] ' % (self.positioner, dat_attr)
            if(npts is None):
                #get all points
                pts = self.sscan.get(dat_attr)
            else:
                if(npts == 1):
                    start = self.sscan.get('P1SP')
                    end = self.sscan.get('P1EP')
                    pts = [start, end]
                else:
                    pts = self.sscan.get(dat_attr)[0:npts]
            return(pts)
        
        except KeyError as e:
            _logger.error('get_positioner_points: Error: [%s]' % str(e))
            print('get_positioner_points: Error: [%s]' % str(e))
    
    def get_all_positioner_points(self):
        """
        get_all_positioner_points(): description

        :returns: None
        """
        npts = self.sscan.get('NPTS')
        all_data = {}
        for i in range(1,4):
            pv_attr = 'P%dPV' % i
            pra_attr = 'P%dRA' % i
            pvname = self.sscan.get(pv_attr)
            if(len(pvname) > 0):
                pts = self.get_positioner_points(i, int(npts))
                all_data[pra_attr] = pts
                        
        return(all_data)
    
    def get_all(self):
        """
        get_all(): description

        :returns: None
        """
        #print '[%s] get_all() called' % self.positioner
        try:
            self.scan_data = self.sscan.get_all()
        except KeyError as e:
            _logger.error('no key in scan data for [%s]' % str(e))
            print('no key in scan data for [%s]' % str(e))
            
    def get_all_data(self):
        """
        get_all_data(): description

        :returns: None
        """
        #print '[%s] get_all() called' % self.positioner
        try:
            #self.scan_data = self.sscan.get_all()
            self.scan_data = self.get_all_positioner_points()
            self.scan_data['CPT'] = self.sscan.get('CPT')
            self.scan_data['NPTS'] = self.sscan.get('NPTS')
            return(self.scan_data)
        except KeyError as e:
            _logger.error('no key in scan data for [%s]' % str(e))
            print('no key in scan data for [%s]' % str(e))
            return({})         
    
    def clear_all_detectors(self):
        """
        clear_all_detectors(): description

        :returns: None
        """
        """ clear all of the detector fields in the scan record """
        for i in range(1,70):
            pv_attr = 'D%02dPV' % i
            self.sscan.put(pv_attr, '')
        
        #print '%s: all detector fields cleared'
        
    def set_det_trigger(self, trig_num, pv, val):
        """
        set_det_trigger(): description

        :param trig_num: trig_num description
        :type trig_num: trig_num type

        :param pv: pv description
        :type pv: pv type

        :param val: val description
        :type val: val type

        :returns: None
        """
        if trig_num in range(1,4):
            self.sscan.put('T%dPV' % trig_num, pv)
            self.sscan.put('T%dCD' % trig_num, val)
            
    def set_scan_to_execute(self, scan_prefix, scan_name):
        """
        set_scan_to_execute(): description

        :param scan_prefix: scan_prefix description
        :type scan_prefix: scan_prefix type

        :param scan_name: scan_name description
        :type scan_name: scan_name type

        :returns: None
        """
        
        self.sscan.put('T4PV', scan_prefix + ':'+ scan_name + '.EXSC')
        self.sscan.put('T4CD', 1)



if __name__ == '__main__':
    pass
