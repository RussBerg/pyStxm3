#! \env\python
"""PLV_control.py

Record photographs from the optical microscope, getting position data also,
and writing the data to jpeg, STXM SDF and STXM NeXus formats.
"""

import twain
import wx
import ConfigParser

import traceback, sys
import os, os.path
import cStringIO
from PIL import Image
from PIL import ImageOps
import serial
import h5py, numpy

CONFIG_FILE = 'PLV_control.cfg'
ID_OPEN_SCANNER=103
ID_ACQUIRE_NATIVELY=104

class CannotWriteTransferFile(Exception):
    pass
    

class TwainBase:
    """Simple Base Class for twain functionality. This class should
    work with all the windows librarys, i.e. wxPython, pyGTK and Tk.
    """

    SM=None                        # Source Manager
    SD=None                        # Data Source
    ProductName='PLV Control'      # Name of this product
#    AcquirePending = False         # Flag to indicate that there is an acquire pending
    mainWindow = None              # Window handle for the application window


    def Initialise(self):
        """Set up the variables used by this class"""
        (self.SD, self.SM) = (None, None)
        self.ProductName='PLV Control'
#        self.AcquirePending = False
        self.mainWindow = None
        
    def Terminate(self):
        """Destroy the data source and source manager objects."""
        if self.SD: self.SD.destroy()
        if self.SM: self.SM.destroy()
        (self.SD, self.SM) = (None, None)

    def OpenScanner(self, mainWindow=None, ProductName=None):
        """Connect to the scanner"""
        if ProductName: self.ProductName = ProductName
        if mainWindow: self.mainWindow = mainWindow
        if not self.SM:
            self.SM = twain.SourceManager(self.mainWindow, ProductName=self.ProductName)
        if not self.SM:
            return
        if self.SD:
            self.SD.destroy()
            self.SD=None
        SourceList = self.SM.GetSourceList()
        if len(SourceList)==1:
            self.SD = self.SM.OpenSource(SourceList[0])
        else:
            self.SD = self.SM.OpenSource()
        if self.SD:
            self.SetFrameTitle(self.ProductName+': ' + self.SD.GetSourceName())
        self.SM.SetCallback(self.OnTwainEvent)
    
    def Acquire(self):
        """Begin the acquisition process. The actual acquisition will be notified by 
        either polling or a callback function."""
        if not self.SD:
            self.OpenScanner()
        if not self.SD: return
        try:
            self.SD.SetCapability(twain.ICAP_YRESOLUTION, twain.TWTY_FIX32, 100.0) 
        except:
            pass
        try:
            self.SD.RequestAcquire(1)#1, 1)  # 1,1 to show scanner user interface
        except:# twain.excTWCC_SEQERROR:
            pass
#        self.AcquirePending=True
#        self.SetFrameTitle(self.ProductName + ': ' + 'Waiting for Data')

    def ProcessXFer(self):
        """An image is ready at the scanner - fetch and display it"""
        more_to_come = False
        try:
            (handle, more_to_come) = self.SD.XferImageNatively()
            self.bmp_stream = twain.DIBToBMFile(handle)
            twain.GlobalHandleFree(handle)
#            if more_to_come: self.AcquirePending = True
#            else: self.SD = None
        except:
            # Display information about the exception
            import sys, traceback
            ei = sys.exc_info()
            traceback.print_exception(ei[0], ei[1], ei[2])

    def OnTwainEvent(self, event):
        """This is an event handler for the twain event. It is called 
        by the thread that set up the callback in the first place.

        It is only reliable on wxPython.
        
        """
        try:
            if event == twain.MSG_XFERREADY:
                self.SetFrameTitle(self.ProductName + ': ' + 'Waiting for Data')
#                self.AcquirePending = False
                self.ProcessXFer()
                self.GetImagePosition()
                self.GetMicroscopeParameters()
                self.TranslateMicroscopeParameters()
                self.GetImageParameters()
                self.DisplayImageParameters()
                self.DisplayImage()
                #self.SD.HideUI()
                self.SetFrameTitle(self.ProductName + ': ' + self.SD.GetSourceName())
            elif event == twain.MSG_CLOSEDSREQ:
                self.SD = None
            else:
                print "TWAIN event:", event
        except:
            # Display information about the exception
            import sys, traceback
            ei = sys.exc_info()
            traceback.print_exception(ei[0], ei[1], ei[2])

    def DisplayImageParameters(self):
	self.ModeObjectiveData.SetLabel(self.CurrentMicroscopeMode+"\n"+self.CurrentObjectiveLabel)
	self.LampBrightData.SetLabel(str(self.MicroscopeParameters[1])+"\n"+str(self.Brightness))
	self.GammaExposureData.SetLabel(str(self.Gamma)+"\n"+str(self.ExposureTime))
	self.XYData.SetLabel(str(self.ImagePosition[0])+"\n"+str(self.ImagePosition[1]))
	
    def GetImageParameters(self):
#	print self.GetCurrentTWAINCapabilityValue(self.SD,twain.ICAP_PIXELTYPE)
#	print self.GetCurrentTWAINCapabilityValue(self.SD,twain.ICAP_AUTOBRIGHT)
#	print self.GetCurrentTWAINCapabilityValue(self.SD,twain.ICAP_BRIGHTNESS)
#	print self.GetCurrentTWAINCapabilityValue(self.SD,twain.ICAP_GAMMA)
#	print self.GetCurrentTWAINCapabilityValue(self.SD,twain.ICAP_EXPOSURETIME)
#	#print self.GetCurrentTWAINCapabilityValue(self.SD,twain.ICAP_HIGHLIGHT)
#	#print self.GetCurrentTWAINCapabilityValue(self.SD,twain.ICAP_SHADOW)
#	#print self.GetCurrentTWAINCapabilityValue(self.SD,twain.ICAP_BITDEPTH)
#	#print self.GetCurrentTWAINCapabilityValue(self.SD,twain.ICAP_XRESOLUTION)
#	print self.GetCurrentTWAINCapabilityValue(self.SD,twain.ICAP_XSCALING)
#	#print self.GetCurrentTWAINCapabilityValue(self.SD,twain.ICAP_YRESOLUTION)
#	print self.GetCurrentTWAINCapabilityValue(self.SD,twain.ICAP_YSCALING)
#	#print self.GetCurrentTWAINCapabilityValue(self.SD,twain.ICAP_COMPRESSION)
        
	self.PixelType = self.GetCurrentTWAINCapabilityValue(self.SD,twain.ICAP_PIXELTYPE)
	self.AutoBright = self.GetCurrentTWAINCapabilityValue(self.SD,twain.ICAP_AUTOBRIGHT)
	self.Brightness = self.GetCurrentTWAINCapabilityValue(self.SD,twain.ICAP_BRIGHTNESS)
	self.Gamma = self.GetCurrentTWAINCapabilityValue(self.SD,twain.ICAP_GAMMA)
	self.ExposureTime = self.GetCurrentTWAINCapabilityValue(self.SD,twain.ICAP_EXPOSURETIME)
#	#self.Highlight = self.GetCurrentTWAINCapabilityValue(self.SD,twain.ICAP_HIGHLIGHT)
#	#self.Shadow = self.GetCurrentTWAINCapabilityValue(self.SD,twain.ICAP_SHADOW)
#	#self.BitDepth = self.GetCurrentTWAINCapabilityValue(self.SD,twain.ICAP_BITDEPTH)
#	#self.XResolution = self.GetCurrentTWAINCapabilityValue(self.SD,twain.ICAP_XRESOLUTION)
##	self.XScaling = self.GetCurrentTWAINCapabilityValue(self.SD,twain.ICAP_XSCALING)
#	#self.YResolution = self.GetCurrentTWAINCapabilityValue(self.SD,twain.ICAP_YRESOLUTION)
##	self.YScaling = self.GetCurrentTWAINCapabilityValue(self.SD,twain.ICAP_YSCALING)
#	#self.Compression = self.GetCurrentTWAINCapabilityValue(self.SD,twain.ICAP_COMPRESSION)
        
    
    def GetCurrentTWAINCapabilityValue(self,SD,CapCode):
        SpecialCapData = {twain.ICAP_PIXELTYPE:['TWPT_BW','TWPT_GRAY','TWPT_RGB','TWPT_PALETTE','TWPT_CMY','TWPT_CMYK','TWPT_YUV','TWPT_YUVK','TWPT_CIEXYZ','TWPT_LAB','TWPT_SRGB','TWPT_SCRGB','TWPT_INFRARED'], 
	 twain.ICAP_COMPRESSION:['TWCP_NONE','TWCP_PACKBITS','TWCP_GROUP31D','TWCP_GROUP31DEOL','TWCP_GROUP32D','TWCP_GROUP4','TWCP_JPEG','TWCP_LZW','TWCP_JBIG','TWCP_PNG','TWCP_RLE4','TWCP_RLE8','TWCP_BITFIELDS']}
        try:
            CapTuple = SD.GetCapabilityCurrent(CapCode)
        except twain.excTWCC_CAPUNSUPPORTED:
            CapTuple = (6,0)
        if CapCode in SpecialCapData.keys():
            CapValue = SpecialCapData[CapCode][CapTuple[1]]
        elif CapTuple[0] in [0,1,2,3,4,5]:
            CapValue = int(CapTuple[1])
        elif CapTuple[0]==6:
            CapValue = bool(CapTuple[1])
        elif CapTuple[0]==7:
            CapValue = float(CapTuple[1])
        else:
            CapValue = CapTuple[1]
        return CapValue 

    def GetImagePosition(self):
        Flag = True
        if self.config.has_section('Encoder_COM') and self.config.has_option('Encoder_COM','Port'):
            Encoder_port = int(self.config.getint('Encoder_COM', 'Port'))
        else:
            Encoder_port = 1
        while Flag:
         try:
            SP = serial.Serial(Encoder_port-1, 4800, timeout=1, stopbits=2, rtscts=0)
            SP.write("@P\n\r")
            R = SP.read(36)
            self.ImagePosition = (float(R[1:12])*-1000, float(R[19:30])*-1000)
            SP.close()
            Flag=False
         except ValueError:
            SP.close()
            print "Error, is Gage-Chek turned on?"
            Flag = self.ShowErrorDialog("Error reading position from Gage-Chek.\nPlease make sure Gage-Chek unit is switched on.\n Retry?")
            self.ImagePosition = (0,0)
         except serial.serialutil.SerialException:
            print "Error accessing COM port. Please unplug and reconnect the silver USB adapter."
            Flag = self.ShowErrorDialog("Error accessing COM port.\nPlease unplug and reconnect the silver USB adapter.\n Retry?")
            self.ImagePosition = (0,0)
        print self.ImagePosition
        
        
    def GetMicroscopeParameters(self):
        Flag = True
        if self.config.has_section('Microscope_COM') and self.config.has_option('Microscope_COM','Port'):
            Microscope_port = int(self.config.getint('Microscope_COM', 'Port'))
        else:
            Microscope_port = 1
        while Flag:
         try:
            Query = ['76023\n\r','77021\n\r','78023\n\r','81023\n\r','82023\n\r']#Objective, Lamp, Illumination Turret, Flapping Condensor, Condensor.
            Characters = [(6,7),(6,9),(6,7),(6,7),(6,7)]
            Response = ['','','','',''] #list for responses
            SP = serial.Serial(Microscope_port-1, 19200, timeout=1, stopbits=1, rtscts=0)
            #SP.write("70001\n\r");print SP.readline()#eol='\r') ##debug - identify microscope and list parts
            for i in range(len(Query)):
               SP.write(Query[i])
               R = SP.readline()#eol='\r')
               #print "R=",R
               if len(R)==0:
                   raise ValueError('zero length string')
               Response[i] = int(R[Characters[i][0]:Characters[i][1]])
            Flag=False
         except ValueError:
            SP.close()
            print "Error, is the microscope turned on?"
            Flag = self.ShowErrorDialog("Error reading configuration of the microscope.\nPlease make sure the microscope is switched on *also check that condensor is plugged in).\n Retry?")
        SP.close()
        self.MicroscopeParameters = Response
        
    def TranslateMicroscopeParameters(self):
        print self.MicroscopeParameters
        self.CurrentObjectiveLabel = None
        self.CurrentObjectiveMagnification = None
        self.CurrentIlluminationTurretObject = None
        self.CurrentCondensorObject = None
        self.CurrentMicroscopeMode = None
        self.CurrentFlappingCondensorPosition = None
        if self.config.has_section('Objective '+str(self.MicroscopeParameters[0])) and self.config.has_option('Objective '+str(self.MicroscopeParameters[0]),'Label'):
            self.CurrentObjectiveLabel = self.config.get('Objective '+str(self.MicroscopeParameters[0]), 'Label')
        if self.config.has_section('Objective '+str(self.MicroscopeParameters[0])) and self.config.has_option('Objective '+str(self.MicroscopeParameters[0]),'Label'):
            self.CurrentObjectiveMagnification = self.config.get('Objective '+str(self.MicroscopeParameters[0]), 'Magnification')
        if self.config.has_section('Illumination Turret') and self.config.has_option('Illumination Turret','Position'+str(self.MicroscopeParameters[2])):
            self.CurrentIlluminationTurretObject = self.config.get('Illumination Turret', 'Position'+str(self.MicroscopeParameters[2]))
        if self.config.has_section('Condensor') and self.config.has_option('Condensor','Position'+str(self.MicroscopeParameters[4])):
            self.CurrentCondensorObject = self.config.get('Condensor','Position'+str(self.MicroscopeParameters[4]))
        if self.config.has_section('Modes') and self.config.has_option('Modes',str(self.MicroscopeParameters[2])+'_'+str(self.MicroscopeParameters[4])):
            self.CurrentMicroscopeMode = self.config.get('Modes', str(self.MicroscopeParameters[2])+'_'+str(self.MicroscopeParameters[4]))
        if self.config.has_section('Flapping Condensor') and self.config.has_option('Flapping Condensor','Position'+str(self.MicroscopeParameters[3])):
            self.CurrentFlappingCondensorPosition = self.config.get('Flapping Condensor','Position'+str(self.MicroscopeParameters[3]))
        
        
        
    def ShowErrorDialog(self,message='Is everything switched on?'):
	dlg = wx.MessageDialog(self, message, 'Communication Error!', wx.YES_NO|wx.ICON_EXCLAMATION|wx.STAY_ON_TOP)
	resultID = dlg.ShowModal()
	dlg.Destroy()
	if resultID==wx.ID_YES:
	    result=True
	elif resultID==wx.ID_NO:
	    result=False
        return result
        
        
    def GetFileName(self):
        """Generate automatic filename."""
        import datetime
        N = datetime.datetime.now()
        DATESTR = N.strftime(self.config.get('General', 'SystemID')+'_%y%m%d')
        FILEPATH = os.path.join(self.config.get('General', 'BasePath'),DATESTR)
        if not os.path.isdir(FILEPATH):
            fileint = 1
        else:
            dirlist = os.listdir(FILEPATH)
            fileint = 0
            for fn in dirlist:
                if fn[0:10] == DATESTR and (fn[13:]=='.jpg' or fn[13:]=='.hdr' or fn[13:]=='_a.xim'):
                    if fn[10:13].isdigit() and int(fn[10:13]) > fileint:
                        fileint = int(fn[10:13])
            fileint = fileint + 1
        FILENAME = DATESTR + str(fileint).zfill(3)
        self.FileName = (FILEPATH,FILENAME)
    
    
    
    def SaveData(self):
        """Write the data to file as a jpg and also in SDF format (.hdr + .xim)."""
        filename = self.FileName
        if not os.path.isdir(filename[0]):
            os.makedirs(filename[0])
#        print filename[1], os.path.join(filename[0],filename[1])
        filepath = os.path.join(filename[0],filename[1])
        print self.CommentText.GetValue()
        
        im = Image.open(cStringIO.StringIO(self.bmp_stream))
        
        if self.config.has_section('General') and self.config.has_option('General','SDF_width') and self.config.has_option('General','SDF_height'):
            SDF_size = (self.config.getint('General', 'SDF_width'), self.config.getint('General', 'SDF_height'))
        else:
            SDF_size = (320,240)
        if self.config.has_section('General') and self.config.has_option('General','CameraScaleFactor'):
            ScaleFactor = self.config.getfloat('General', 'CameraScaleFactor')
        else:
            ScaleFactor = 1.0
        X_Factor = float(im.size[0])/float(SDF_size[0])/float(self.CurrentObjectiveMagnification)*ScaleFactor
        X_MinMax = ((0.5-SDF_size[0]*0.5)*X_Factor + self.ImagePosition[0],(-0.5+SDF_size[0]*0.5)*X_Factor + self.ImagePosition[0])
        PAxisPoints = '\t\t\t\tPoints = ( '+str(SDF_size[0])
        for i in range(SDF_size[0]):
            PAxisPoints = PAxisPoints+', '+str((i+0.5-SDF_size[0]*0.5)*X_Factor + self.ImagePosition[0])
        Y_Factor = float(im.size[1])/float(SDF_size[1])/float(self.CurrentObjectiveMagnification)*ScaleFactor
        Y_MinMax = ((0.5-SDF_size[1]*0.5)*Y_Factor + self.ImagePosition[1],(-0.5+SDF_size[1]*0.5)*Y_Factor + self.ImagePosition[1])
        QAxisPoints = '\t\t\t\tPoints = ( '+str(SDF_size[1])
        for i in range(SDF_size[1]):
            QAxisPoints = QAxisPoints+', '+str((i+0.5-SDF_size[1]*0.5)*Y_Factor + self.ImagePosition[1])
        
        
        im = ImageOps.mirror(im)
        # Write jpeg
        ImageOps.flip(im).save(filepath+'.jpg')
        # Write STXM SDF
        im = ImageOps.grayscale(im.resize(SDF_size))
        NXim = im.copy()
        imData = list(im.getdata())
        f = open(filepath+"_a.xim",'w')
        try:
            for i in range(im.size[1]):
                line = imData[i*im.size[0]:(i+1)*im.size[0]]
                for j in line:
                    f.write(repr(j)+'\t')
                f.write('\n')
        finally:
            f.close()
        
        comment = self.CommentText.GetValue()
        f = open(filepath+".hdr",'w')
        try:
            f.write('ScanDefinition = { Label = "'+filename[1]+'.hdr"; Type = "Image Scan"; Flags = "Image"; Dwell = 1;\n')
            f.write('\tRegions = (1,\n')
            f.write('{\n')
            f.write('\t\t\tPAxis = { Name = "Sample X"; Unit = "um"; Min = '+str(X_MinMax[0])+'; Max = '+str(X_MinMax[1])+'; Dir = 1;\n')
            f.write(PAxisPoints+');\n')
            f.write('};\n')
            f.write('\n')
            f.write('\t\t\tQAxis = { Name = "Sample Y"; Unit = "um"; Min = '+str(Y_MinMax[0])+'; Max = '+str(Y_MinMax[1])+'; Dir = 1;\n')
            f.write(QAxisPoints+');\n')
            f.write('};\n')
            f.write('});\n')
            f.write('\n')
            f.write('\tStackAxis = { Name = "Energy"; Unit = "eV"; Min = 1; Max = 1; Dir = -1;\n')
            f.write('\tPoints = (1, 1);\n')
            f.write('};\n')
            f.write('\n')
            f.write('\tChannels = (1, { Name = "counter0"; Unit = "Hz";});\n')
            f.write('};\n')
            f.write(' BeamFeedback = false; SampleXFeedback = false; SampleYFeedback = false; SampleZFeedback = false; ShutterAutomatic = false;\n')
            f.write('Channels = (1,\n')
            f.write('{ ID = 0; Type = 0; Name = "Counter0"; Controller = 0; DeviceNumber = 0; UnitName = "Hz"; LinearCoefficient = 1; ConstantCoefficient = 0; ProcessString = "I";});\n')
            f.write('CoarseZ = { Name = CoarseZ; LastPosition =  1000; Status = 0; Type = 0; ControllerID = 0; Vel = 0;};\n')
            f.write('ImageScan = { ScanType = "Image (Line - unidirection)"; Stage = "Automatic"; Shutter = "Automatic"; Interferometry = "On"; SingleEnergy = true;\n')
            f.write('\tEnergyRegions = (1,\n')
            f.write('{ StartEnergy = 1; EndEnergy = 1; Range = 0; Step = 0; Points = 1; DwellTime = 1;});\n')
            f.write(' PointDelay = 0.04; LineDelay = 0; AccelDist = 6.48058; MultipleRegions = true;\n')
            f.write('\tSpatialRegions = (1,\n')
            f.write('{ CentreXPos = '+str(self.ImagePosition[0])+'; CentreYPos = '+str(self.ImagePosition[1])+'; XRange = '+str(SDF_size[0]*X_Factor)+'; YRange = '+str(SDF_size[1]*Y_Factor)+'; XStep = '+str(X_Factor)+'; YStep = '+str(Y_Factor)+'; XPoints = '+str(SDF_size[0])+'; YPoints = '+str(SDF_size[1])+';});\n')
            f.write('};\n')
            f.write('MicroscopeParameters = { Objective = { Position = "'+str(self.MicroscopeParameters[0])+'"; Label = "'+self.CurrentObjectiveLabel+'"; Magnification = "'+self.CurrentObjectiveMagnification+'";}; IlluminationTurret = { Position = "'+str(self.MicroscopeParameters[2])+'"; Label = "'+self.CurrentIlluminationTurretObject+'";};\n')
            f.write('\tCondensor = { Position = "'+str(self.MicroscopeParameters[4])+'"; Label = "'+self.CurrentCondensorObject+'";}; FlappingCondensor = { Position = "'+str(self.MicroscopeParameters[3])+'"; Label = "'+self.CurrentFlappingCondensorPosition+'";};\n')
            f.write('\tMode = "'+self.CurrentMicroscopeMode+'"; Lamp = "'+str(self.MicroscopeParameters[1])+'"; Gamma = "'+str(self.Gamma)+'"; Brightness = "'+str(self.Brightness)+'"; ExposureTime = "'+str(self.ExposureTime)+'"; AutoBrightness = "'+str(self.AutoBright)+'"; PixelType = "'+str(self.PixelType)+'";};\n')
            if len(comment)>0:
                f.write('Comment = { Comment = "%s";};\n' % comment)
            f.write('\n')
        finally:
            f.close()
        
        
        
        #Write NeXus
        NXfile = h5py.File(filepath+".hdf5", 'w')
        NXfile.attrs['HDF5_Version'] = numpy.array([b'1.8.4'])
        NXfile.attrs['NeXus_version'] = numpy.array([b'4.3.0'])
        NXfile.attrs['file_name'] = numpy.array([b'/home/homersimpson/PLV_now.hdf5'])
        NXfile.attrs['file_time'] = numpy.array([b'2012-01-01T12:00:00+01:00'])
        NXfile.create_group('entry1')
        NXfile['entry1'].attrs['NX_class'] = numpy.array([b'NXentry'])
        NXfile['entry1'].create_dataset('definition',data=numpy.array([b'NXstxm ']))
        NXfile['entry1'].create_dataset('title',data=numpy.array([b'Sample ']))
        NXfile['entry1'].create_dataset('start_time',data=numpy.array([b'2012-01-01T12:00:00+100 ']))
        NXfile['entry1'].create_group('Camera')
        NXfile['entry1']['Camera'].attrs['NX_class'] = numpy.array([b'NXdata'])
        
# Old style        
#        NXfile['entry1']['Camera'].create_dataset('data',data=numpy.array(NXim,numpy.float64).reshape(NXim.size[1],NXim.size[0],1).transpose((2,0,1)))
#        NXfile['entry1']['Camera'].create_dataset('SampleX',data=numpy.linspace(X_MinMax[0],X_MinMax[1],num=NXim.size[0]))
#        NXfile['entry1']['Camera']['SampleX'].attrs['axis'] = 3
#        NXfile['entry1']['Camera'].create_dataset('SampleY',data=numpy.linspace(Y_MinMax[0],Y_MinMax[1],num=NXim.size[1]))
#        NXfile['entry1']['Camera']['SampleY'].attrs['axis'] = 2
#        NXfile['entry1']['Camera'].create_dataset('Energy',data=numpy.array([0.1]))
#        NXfile['entry1']['Camera']['Energy'].attrs['axis'] = 1
#        sc = NXfile['entry1']['Camera'].create_dataset('scan_type',data=numpy.array([b'Sample ']))

# New style
        NXfile['entry1']['Camera'].create_dataset('data',data=numpy.array(NXim,numpy.float64).reshape(NXim.size[1],NXim.size[0]))
        NXfile['entry1']['Camera'].create_dataset('sample_x',data=numpy.linspace(X_MinMax[0],X_MinMax[1],num=NXim.size[0]))
        NXfile['entry1']['Camera']['sample_x'].attrs['axis'] = 2
        NXfile['entry1']['Camera'].create_dataset('sample_y',data=numpy.linspace(Y_MinMax[0],Y_MinMax[1],num=NXim.size[1]))
        NXfile['entry1']['Camera']['sample_y'].attrs['axis'] = 1
        NXfile['entry1']['Camera'].create_dataset('energy',data=numpy.array([0.1]))
        sc = NXfile['entry1']['Camera'].create_dataset('stxm_scan_type',data=numpy.array([b'sample image ']))
        
        NXfile['entry1']['Camera'].create_dataset('count_time',data=numpy.array([self.ExposureTime]))
        NXfile.close()
#        print "done"

class DynamicImage(wx.Window):
    def __init__(self, parent):
        wx.Window.__init__(self, parent)
        self.image = wx.EmptyImage(int(parent.config.get('General', 'SDF_width')),int(parent.config.get('General', 'SDF_height')))
        (w, h) = self.image.GetSize()
        self.image_ar = float(w)/float(h)
        self.resize_space(1)
        self.Bind(wx.EVT_SIZE, self.resize_space)
        self.Bind(wx.EVT_PAINT, self.onpaint)

    def SetImage(self, image):
        self.image = image
        (w, h) = self.image.GetSize()
        self.image_ar = float(w)/float(h)
        self.bitmap = wx.BitmapFromImage(self.image)
        self.resize_space(1)

        
    def onpaint(self, evt):
        dc = wx.PaintDC(self)
        dc.DrawBitmap(self.bitmap, self.position[0], self.position[1], useMask=False)

    def resize_space(self, size):
        (w, h) = self.get_best_size()
        self.s_image = self.image.Scale(w, h)
        self.bitmap = wx.BitmapFromImage(self.s_image)
        self.Refresh()
        
    def get_best_size(self):
        (window_width, window_height) = self.GetClientSizeTuple()
        (w, h) = self.image.GetSize()
        if window_width>w and window_height>h:
            #if window bigger than image, don't resize, just center it
            new_size = (w, h)
	    self.position = ((window_width - new_size[0])/2,(window_height - new_size[1])/2) 
        elif self.image_ar>=float(window_width)/float(window_height):
	    new_size = (window_width, window_width / self.image_ar)
	    self.position = (0,(window_height - new_size[1])/2) 
        else:
	    new_size = (window_height * self.image_ar, window_height )
	    self.position = ((window_width - new_size[0])/2,0) 
        return new_size
    


        
class MainFrame(wx.Frame, TwainBase):
    """wxPython implementation"""
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, wx.DefaultPosition, wx.Size(600,600))
        self.CreateStatusBar()
        menu = wx.Menu()        
        menu.Append(ID_OPEN_SCANNER, "&Connect", "Connect to the Scanner")
        menu.Append(ID_ACQUIRE_NATIVELY, "Acquire &Natively", "Acquire an Image using Native Transfer Interface")
        menu.AppendSeparator()
        menu.Append(wx.ID_EXIT, "E&xit", "Terminate the program")
        menuBar = wx.MenuBar()
        menuBar.Append(menu, "&File")
        self.SetMenuBar(menuBar)

        wx.EVT_MENU(self, wx.ID_EXIT, self.MnuQuit)
        wx.EVT_MENU(self, ID_OPEN_SCANNER, self.MnuOpenScanner)
        wx.EVT_MENU(self, ID_ACQUIRE_NATIVELY, self.MnuAcquireNatively)
        wx.EVT_CLOSE(self, self.OnClose)
        
        
        self.config = ConfigParser.SafeConfigParser({'SDF_width':'320','SDF_height':'240','SystemID':'PLV','BasePath':os.path.dirname(__file__)})
        self.config.read(os.path.join(os.path.dirname(__file__),CONFIG_FILE))

        
        sizer1 = wx.BoxSizer(wx.VERTICAL)
        sizerTop = wx.BoxSizer(wx.HORIZONTAL)
        sizerBot = wx.BoxSizer(wx.HORIZONTAL)
        
        
        sizerTop.Add(wx.StaticText(self,-1,"Mode: \nObjective: ",style=wx.ALIGN_RIGHT), 2, wx.EXPAND)
        self.ModeObjectiveData = wx.StaticText(self,-1,"-\n-",style=wx.ALIGN_LEFT)
        sizerTop.Add(self.ModeObjectiveData, 4, wx.EXPAND)
        sizerTop.Add(wx.StaticText(self,-1,"Lamp: \nBrightness: ",style=wx.ALIGN_RIGHT), 2, wx.EXPAND)
        self.LampBrightData = wx.StaticText(self,-1,"-\n-",style=wx.ALIGN_LEFT)
        sizerTop.Add(self.LampBrightData, 1, wx.EXPAND)
        sizerTop.Add(wx.StaticText(self,-1,"Gamma: \nExposure: ",style=wx.ALIGN_RIGHT), 2, wx.EXPAND)
        self.GammaExposureData = wx.StaticText(self,-1,"-\n-",style=wx.ALIGN_LEFT)
        sizerTop.Add(self.GammaExposureData, 1, wx.EXPAND)
        sizerTop.Add(wx.StaticText(self,-1,"X: \nY: ",style=wx.ALIGN_RIGHT), 1, wx.EXPAND)
        self.XYData = wx.StaticText(self,-1,"-\n-",style=wx.ALIGN_LEFT)
        sizerTop.Add(self.XYData, 1, wx.EXPAND)
        
        
        sizer1.Add(sizerTop, 0, wx.EXPAND)
        
        self.ImageView = DynamicImage(self)
        sizer1.Add(self.ImageView, 1, wx.ALL|wx.GROW|wx.ALIGN_CENTER)
        
        CommentLabel = wx.StaticText(self, -1, "  Comment: ")
        sizerBot.Add(CommentLabel)
        self.CommentText = wx.TextCtrl(self, -1, "", style=wx.TE_MULTILINE)
        sizerBot.Add(self.CommentText, 10, wx.EXPAND)
        self.GetFileName()
        self.SaveButton = wx.Button(self, -1, 'Save as: \n'+self.FileName[1])
        self.SaveButton.Enable(False)
        self.Bind(wx.EVT_BUTTON, self.OnSaveButton, self.SaveButton)
        sizerBot.Add(self.SaveButton)
        self.CancelButton = wx.Button(self, -1, 'Cancel\n')
        self.CancelButton.Enable(False)
        self.Bind(wx.EVT_BUTTON, self.OnCancelButton, self.CancelButton)
        sizerBot.Add(self.CancelButton,flag=wx.ALIGN_CENTER_VERTICAL)
        sizer1.Add(sizerBot, 0, wx.EXPAND)
        
        self.SetAutoLayout(True)
        self.SetSizer(sizer1)               #add outer sizer to frame
#        self.Fit()

        # Print out the exception - requires that you run from the command prompt
        sys.excepthook = traceback.print_exception

        # Initialise the Twain Base Class
        self.Initialise()
        #Start connection
        self.OpenScanner(self.GetHandle(), ProductName=self.ProductName)
        self.Acquire()
        
    def OnSaveButton(self, evt):
        self.SaveData()
        self.SaveButton.SetLabel('Saved as\n'+self.FileName[1])
        self.SaveButton.Enable(False)
        self.CancelButton.Enable(False)
        self.Acquire()
        
    def OnCancelButton(self, evt):
        self.SaveButton.Enable(False)
        self.CancelButton.Enable(False)
        self.Acquire()
        
    def MnuQuit(self, event):
        self.Close(1)

    def OnClose(self, event):
        # Terminate the Twain Base Class
        self.Terminate()
        self.Destroy()

    def MnuOpenScanner(self, event):
        self.OpenScanner(self.GetHandle(), ProductName=self.ProductName)

    def MnuAcquireNatively(self, event):
        return self.Acquire()

    def DisplayImage(self):
        print "Reading image...",
#        sys.stdout.flush()
        self.ImageView.SetImage(wx.ImageFromStream(cStringIO.StringIO(self.bmp_stream)).Rotate90().Rotate90())
        print "done!"
        self.GetFileName()
        self.SaveButton.SetLabel('Save as\n'+self.FileName[1])
        self.SaveButton.Enable(True)
        self.CancelButton.Enable(True)
       
       
        


    def SetFrameTitle(self, message):
        # Set the title on the main window - used for tracing
        self.SetTitle(message)

class SimpleApp(wx.App):
    def OnInit(self):
        frame = MainFrame(None, -1, "PLV Control")
        frame.Show(True)
        self.SetTopWindow(frame)
        return True

SimpleApp(0).MainLoop()
 
