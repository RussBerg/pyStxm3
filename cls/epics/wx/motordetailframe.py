"""
wxFrame for Detailed Motor Settings, ala medm More (+Setup) screen
"""

import time
import wx
from wx.lib.scrolledpanel import ScrolledPanel

from epics.wx.wxlib import (PVText, PVFloatCtrl, PVTextCtrl,
                            PVEnumButtons, PVEnumChoice,
                            DelayedEpicsCallback, EpicsFunction)

from .utils import set_sizer, LCEN, RCEN, CEN

def xLabel(parent, label):
    "simple label"
    return wx.StaticText(parent, label=label, style=wx.ALIGN_BOTTOM)

def xTitle(parent, label, fontsize=13, color='Blue'):
    "simple title"
    wid = wx.StaticText(parent, label=label, style=wx.ALIGN_BOTTOM)
    font = wid.GetFont()
    font.PointSize = fontsize
    wid.SetFont(font)
    wid.SetForegroundColour(color)
    return wid

class MotorDetailFrame(wx.Frame):
    """ Detailed Motor Setup Frame"""
    __motor_fields = ('SET', 'LLM', 'HLM', 'LVIO', 'TWV', 'HLS', 'LLS')

    def __init__(self, parent=None, motor=None):
        wx.Frame.__init__(self, parent, wx.ID_ANY, size=(525, 650),
                          style=wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL)
        self.motor = motor
        prec = motor.PREC
        motor_pvname = self.motor._prefix
        devtype = motor.get('DTYP', as_string=True)
        if motor_pvname.endswith('.'):
            motor_pvname = motor_pvname[:-1]

        self.SetTitle("Motor Details: %s  | %s | (%s)" % (motor_pvname,
                                                          self.motor.DESC,
                                                          devtype))

        panel = ScrolledPanel(self, size=(500, 650), name='mpanel',
                              style=wx.GROW|wx.TAB_TRAVERSAL)
        sizer = wx.BoxSizer(wx.VERTICAL)

        spanel = wx.Panel(panel, -1, size=(500, 50))
        ssizer = wx.BoxSizer(wx.HORIZONTAL)
        ssizer.AddMany([(wx.StaticText(spanel, label=' Label ',
                                       size=(65, -1)), 0,  RCEN),
                        (self.MotorTextCtrl(spanel, 'DESC',
                                             size=(210, -1)), 1,  LCEN),
                        (wx.StaticText(spanel, label='  units ',
                                       size=(75, -1)), 0, RCEN),
                        (self.MotorTextCtrl(spanel, 'EGU',
                                             size=(95, -1)), 0,  LCEN)
                        ])

        set_sizer(spanel, ssizer)
        sizer.Add(spanel, 0, wx.EXPAND)
        sizer.Add(wx.StaticLine(panel, size=(100, 2)),  0, wx.EXPAND)

        ds = wx.GridBagSizer(6, 4)
        dp = wx.Panel(panel)
        nrow = 0

        nrow += 1
        ds.Add(xTitle(dp,"Drive"), (nrow, 0), (1, 1), LCEN, 5)
        ds.Add(xLabel(dp,"User" ), (nrow, 1), (1, 1), CEN)
        ds.Add(xLabel(dp,"Dial" ), (nrow, 2), (1, 1), CEN)
        ds.Add(xLabel(dp,"Raw"  ), (nrow, 3), (1, 1), CEN)

        ####
        nrow += 1
        self.info = wx.StaticText(dp, label='', size=(55, 20), style=CEN)
        self.info.SetForegroundColour("Red")

        ds.Add(xLabel(dp,"High Limit"),     (nrow, 0), (1, 1), LCEN, 5)
        ds.Add(self.MotorCtrl(dp,'HLM'),   (nrow, 1), (1, 1), CEN)
        ds.Add(self.MotorCtrl(dp,'DHLM'),  (nrow, 2), (1, 1), CEN)
        ds.Add(self.info,                   (nrow, 3), (1, 1), CEN)

        ####
        nrow += 1
        ostyle = RCEN|wx.EXPAND
        ds.Add(xLabel(dp,"Readback"),       (nrow, 0),  (1, 1), LCEN, 5)
        ds.Add(self.MotorText(dp, 'RBV'),  (nrow, 1),  (1, 1), ostyle, 5)
        ds.Add(self.MotorText(dp, 'DRBV'), (nrow, 2),  (1, 1), ostyle, 5)
        ds.Add(self.MotorText(dp, 'RRBV'), (nrow, 3),  (1, 1), ostyle, 5)

        ####
        nrow += 1
        self.drives  = [self.MotorCtrl(dp, 'VAL'),
                        self.MotorCtrl(dp, 'DVAL'),
                        self.MotorCtrl(dp, 'RVAL')]

        ds.Add(xLabel(dp,"Move"),  (nrow, 0), (1, 1), LCEN, 5)
        ds.Add(self.drives[0],     (nrow, 1), (1, 1), CEN)
        ds.Add(self.drives[1],     (nrow, 2), (1, 1), CEN)
        ds.Add(self.drives[2],     (nrow, 3), (1, 1), CEN)

        nrow += 1
        ds.Add(xLabel(dp,"Low Limit"),      (nrow, 0), (1, 1), LCEN, 5)
        ds.Add(self.MotorCtrl(dp, 'LLM'),  (nrow, 1), (1, 1), CEN)
        ds.Add(self.MotorCtrl(dp, 'DLLM'), (nrow, 2), (1, 1), CEN)

        ####

        twk_sizer = wx.BoxSizer(wx.HORIZONTAL)
        twk_panel = wx.Panel(dp)
        twk_val = PVFloatCtrl(twk_panel, size=(110, -1), precision=prec)
        twk_val.SetPV(self.motor.PV('TWV'))

        twk_left = wx.Button(twk_panel, label='<',  size=(30, 30))
        twk_right = wx.Button(twk_panel, label='>',  size=(30, 30))
        twk_left.Bind(wx.EVT_BUTTON,  self.OnLeftButton)
        twk_right.Bind(wx.EVT_BUTTON, self.OnRightButton)
        twk_sizer.AddMany([(twk_left,   0, CEN),
                           (twk_val,    0, CEN),
                           (twk_right,  0, CEN)])

        set_sizer(twk_panel, twk_sizer)

        nrow += 1
        ds.Add(xLabel(dp,"Tweak"),    (nrow, 0), (1, 1), LCEN, 5)
        ds.Add(twk_panel,             (nrow, 1), (1, 2), wx.ALIGN_LEFT)

        epv = self.motor.PV('disabled')

        able_btns = PVEnumButtons(dp, pv=epv, orientation = wx.VERTICAL,
                                  size=(110, -1))

        ds.Add(able_btns,   (nrow-1, 3), (2, 1), CEN)

        stop_btns = PVEnumButtons(dp, pv=self.motor.PV('SPMG'),
                                  orientation = wx.VERTICAL,
                                  size=(110,-1))

        ds.Add(stop_btns,     (2, 4), (4, 1), wx.ALIGN_RIGHT)

        for attr in ('LLM', 'HLM', 'DLLM', 'DHLM'):
            pv = self.motor.PV(attr)
            pv.add_callback(self.OnLimitChange, wid=self.GetId(), attr=attr)

        #
        set_sizer(dp, ds) # ,fit=True)
        sizer.Add(dp, 0)

        ####
        sizer.Add(wx.StaticLine(panel, size=(100, 2)),  0, wx.EXPAND)
        sizer.Add((5, 5), 0)
        sizer.Add(xTitle(panel, 'Calibration'), 0, LCEN, 5)

        ds = wx.GridBagSizer(6, 5)
        dp = wx.Panel(panel)

        ds.Add(xLabel(dp, 'Mode: '),  (0, 0), (1, 1), LCEN, 5)

        ds.Add(PVEnumButtons(dp, pv=self.motor.PV('SET'),
                             orientation = wx.HORIZONTAL,
                             size=(-1, -1)), (0, 1), (1, 2), wx.ALIGN_LEFT)

        ds.Add(xLabel(dp, 'Direction: '), (1, 0), (1, 1), LCEN, 5)
        ds.Add(PVEnumButtons(dp, pv=self.motor.PV('DIR'),
                             orientation=wx.HORIZONTAL,
                             size=(-1, -1)), (1, 1), (1, 2), wx.ALIGN_LEFT)

        ds.Add(xLabel(dp, 'Freeze Offset: '), (0, 4), (1, 1), LCEN, 5)
        ds.Add(PVEnumChoice(dp, pv=self.motor.PV('FOFF'),
                            size=(110, -1)),  (0, 5), (1, 1), CEN)

        ds.Add(xLabel(dp, 'Offset Value: '), (1, 4), (1, 1), LCEN, 5)
        ds.Add(self.MotorCtrl(dp,'OFF'),    (1, 5), (1, 1), CEN)

        set_sizer(dp, ds)
        sizer.Add(dp, 0)
        #####

        sizer.Add((5, 5), 0)
        sizer.Add(wx.StaticLine(panel, size=(100, 2)),  0, wx.EXPAND)
        sizer.Add((5, 5), 0)
        #
        ds = wx.GridBagSizer(6, 3)
        dp = wx.Panel(panel)
        nrow = 0

        ds.Add(xTitle(dp, "Dynamics"),  (nrow, 0), (1, 1), LCEN, 5)
        ds.Add(xLabel(dp, "Normal" ),   (nrow, 1), (1, 1), CEN)
        ds.Add(xLabel(dp, "Backlash" ), (nrow, 2), (1, 1), CEN)

        ####
        nrow += 1
        ds.Add(xLabel(dp, "Max Speed"),      (nrow, 0), (1, 1), LCEN, 5)
        ds.Add(self.MotorCtrl(dp, 'SMAX'),  (nrow, 1), (1, 1), CEN)

        nrow += 1
        ds.Add(xLabel(dp, "Speed"),           (nrow, 0), (1, 1), LCEN, 5)
        ds.Add(self.MotorCtrl(dp, 'VELO'),   (nrow, 1), (1, 1), CEN)
        ds.Add(self.MotorCtrl(dp, 'BVEL'),   (nrow, 2), (1, 1), CEN)

        nrow += 1
        ds.Add(xLabel(dp, "Base Speed"),     (nrow, 0), (1, 1), LCEN, 5)
        ds.Add(self.MotorCtrl(dp, 'VBAS'),  (nrow, 1), (1, 1), CEN)

        nrow += 1
        ds.Add(xLabel(dp, "Accel (s)"),      (nrow, 0), (1, 1), LCEN, 5)
        ds.Add(self.MotorCtrl(dp, 'ACCL'),  (nrow, 1), (1, 1), CEN)
        ds.Add(self.MotorCtrl(dp, 'BACC'),  (nrow, 2), (1, 1), CEN)

        nrow += 1
        ds.Add(xLabel(dp, "Backslash Distance"), (nrow, 0), (1, 2), LCEN, 5)
        ds.Add(self.MotorCtrl(dp, 'BDST'),     (nrow, 2), (1, 1), CEN)

        nrow += 1
        ds.Add(xLabel(dp, "Move Fraction"),  (nrow, 0), (1, 2), LCEN, 5)
        ds.Add(self.MotorCtrl(dp, 'FRAC'),  (nrow, 2), (1, 1), CEN)

        set_sizer(dp, ds) # ,fit=True)

        sizer.Add(dp, 0)
        sizer.Add(wx.StaticLine(panel, size=(100, 2)),  0, wx.EXPAND)

        sizer.Add((5, 5), 0)
        sizer.Add(xTitle(panel, 'Resolution'), 0, LCEN, 5)

        ds = wx.GridBagSizer(4, 4)
        dp = wx.Panel(panel)
        nrow = 0
        ds.Add(xLabel(dp, "Motor Res"),      (nrow, 0), (1, 1), LCEN, 5)
        ds.Add(self.MotorCtrl(dp, 'MRES'),  (nrow, 1), (1, 1), CEN)
        ds.Add(xLabel(dp, "Encoder Res"),    (nrow, 2), (1, 1), LCEN, 5)
        ds.Add(self.MotorCtrl(dp, 'ERES'),  (nrow, 3), (1, 1), CEN)

        nrow += 1
        ds.Add(xLabel(dp, "Steps / Rev"),    (nrow, 0), (1, 1), LCEN, 5)
        ds.Add(self.MotorCtrl(dp, 'SREV'),  (nrow, 1), (1, 1), CEN)
        ds.Add(xLabel(dp, "Units / Rev"),    (nrow, 2), (1, 1), LCEN, 5)
        ds.Add(self.MotorCtrl(dp, 'UREV'),  (nrow, 3), (1, 1), CEN)

        nrow += 1
        ds.Add(xLabel(dp, "Precision"),      (nrow, 0), (1, 1), LCEN, 5)
        ds.Add(self.MotorCtrl(dp, 'PREC'),  (nrow, 1), (1, 1), CEN)

        set_sizer(dp, ds)
        sizer.Add(dp, 0)
        sizer.Add(wx.StaticLine(panel, size=(100, 2)),  0, wx.EXPAND)


        for attr in self.__motor_fields:
            self.motor.PV(attr).add_callback(self.OnMotorEvent,
                                             wid=self.GetId(), field=attr)

        self.info.SetLabel('')
        for f in ('HLS', 'LLS', 'LVIO', 'SET'):
            if self.motor.get(f):
                wx.CallAfter(self.OnMotorEvent,
                             pvname=self.motor.PV(f).pvname, field=f)

        set_sizer(panel, sizer, fit=True)
        panel.SetupScrolling()
        self.Show()
        self.Raise()

    @DelayedEpicsCallback
    def OnMotorEvent(self, pvname=None, field=None, **kws):
        "Motor event handler"
        if pvname is None:
            return None

        field_val = self.motor.get(field)
        if field in ('LVIO', 'HLS', 'LLS'):
            s = ''
            if field_val != 0:
                s = 'Limit!'
            self.info.SetLabel(s)

        elif field == 'SET':
            color = 'Yellow'
            if field_val == 0:
                color = 'White'
            for d in self.drives:
                d.SetBackgroundColour(color)
                d.Refresh()

    def MotorCtrl(self, panel, attr):
        "PVFloatCtrl for a Motor attribute"
        return PVFloatCtrl(panel, size=(100, -1),
                           precision= self.motor.PREC,
                           pv=self.motor.PV(attr),
                           style = wx.TE_RIGHT)

    def MotorText(self, panel, attr):
        "PVText for a Motor attribute"
        pv = self.motor.PV(attr)
        return PVText(panel,  pv=pv, as_string=True,
                      size=(100, -1), style=wx.ALIGN_RIGHT|wx.CENTER)

    def MotorTextCtrl(self, panel, attr, size=(100, -1)):
        "PVTextCtrl for a Motor attribute"
        pv = self.motor.PV(attr)
        return PVTextCtrl(panel, pv=pv, size=size,
                          style=wx.ALIGN_LEFT|wx.TE_PROCESS_ENTER)

    @DelayedEpicsCallback
    def OnLimitChange(self, attr=None, value=None, **kws):
        "limit-change callback"
        funcs = {'low_limit':       self.drives[0].SetMin,
                 'high_limit':      self.drives[0].SetMax,
                 'dial_low_limit':  self.drives[1].SetMin,
                 'dial_high_limit': self.drives[1].SetMax}
        if attr in funcs:
            funcs[attr](value)

    @EpicsFunction
    def OnLeftButton(self, event=None):
        "left button event handler"
        if self.motor is not None:
            self.motor.tweak(direction='reverse')
        event.Skip()

    @EpicsFunction
    def OnRightButton(self, event=None):
        "right button event handler"
        if self.motor is not None:
            self.motor.tweak(direction='forward')
        event.Skip()
