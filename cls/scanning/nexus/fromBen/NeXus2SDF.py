#! /usr/bin/env python
# -*- coding: utf-8 -*-

'''
Read in files in the NeXus format and convert them to the ALS "SDF" STXM format for reading in aXis2000.
Mulitple region scans are broken up into separate SDF file sets (i.e. multiple .hdr files).
'''
#Python versions below 2.6 are not supported
import re, time, numpy, types, argparse, os.path
from os import listdir
from collections import OrderedDict
import h5py

ImplementedScanTypes = ['Sample','sample image stack','sample image','sample line spectrum','sample point spectrum']

class write_SDF:
  def __init__(self, FileName,OutputPath,overwrite='Yes',normalise=False):
	print(FileName,end=' ')#Python versions below 2.6 are not supported
	D = self.NeXusParser(FileName)
	Regions = list(D.keys())
	Detectors = list(D[Regions[0]].keys())
	SourcePath,SourceName = os.path.split(FileName)
	BaseName,ext = os.path.splitext(SourceName)
	print('-->',end=' ')
	if D[Regions[0]][Detectors[0]]['scan_type'] not in ImplementedScanTypes:
	  print('Skipping (conversion of scan type "'+D[Regions[0]][Detectors[0]]['scan_type']+'" not implemented)\n')
	  return
	for ri, r in enumerate(Regions):
	  if normalise:
		print('Point-by-point normalisation!')
		if hasattr(D[r],'full_monitor'):
		 print('Normalise')
		 self.normalise_PointByPoint(D[r])
		else:
		  print('Can\'t Normalise')
	  F = self.GenerateFields(D[r])
	  BaseNameRegion = BaseName+'_r'+str(ri+1)
	  if F['Type'] == 'NEXAFS Image Scan': #put image stack files in a new directory
		OutBaseName = os.path.join(OutputPath,BaseNameRegion,BaseNameRegion)
		if not os.path.isdir(os.path.join(OutputPath,BaseNameRegion)): #make the directory if it doesn't already exist
		  os.mkdir(os.path.join(OutputPath,BaseNameRegion))
		  exist_flag = False
		elif os.path.isfile(OutBaseName+'.hdr'):
		  exist_flag = True
		else:
		  exist_flag = False
	  else:
		OutBaseName = os.path.join(OutputPath,BaseNameRegion)
		if os.path.isfile(OutBaseName+'.hdr'):
		  exist_flag = True
		else:
		  exist_flag = False
	  if ri != 0:
		print('\n')
	  print(OutBaseName+'.hdr',end=' ')
	  if overwrite == 'Yes' or not exist_flag:
		permission = True
	  elif overwrite == 'Ask':
		choice = input(" exists!\nOverwrite?(y/N)").lower()
		if choice in ['y','ye','yes']:
		  permission = True
		else:
		  permission = False
	  else:
		permission = False
	  if permission:
		f = open(OutBaseName+'.hdr','w')
		try:
		  f.write('ScanDefinition = { Label = "'+SourceName+'"; Type = "'+F['Type']+'"; Flags = "'+F['Flags']+'"; Dwell = '+str(F['count_time'][0])+';\n')
		  f.write('\tRegions = (1,\n')
		  f.write('{\n\t\t\tPAxis = { Name = "'+F['PAxis']['Name']+'"; Unit = "um"; Min = '+str(F['PAxis']['Points'][0])+'; Max = '+str(F['PAxis']['Points'][-1])+'; Dir = 1;\n')
		  f.write('\t\t\t\tPoints = ( '+str(len(F['PAxis']['Points'])) )
		  for p in F['PAxis']['Points']:
			f.write(', %.3f'%p)
		  f.write(');\n};\n\n')
		  if F['QAxis'] is not None:
			f.write('\t\t\tQAxis = { Name = "'+F['QAxis']['Name']+'"; Unit = "um"; Min = '+str(F['QAxis']['Points'][0])+'; Max = '+str(F['QAxis']['Points'][-1])+'; Dir = 1;\n')
			f.write('\t\t\t\tPoints = ( '+str(len(F['QAxis']['Points'])) )
			for q in F['QAxis']['Points']:
			  f.write(', %.3f'%q)
			f.write(');\n};\n}')
		  
		  f.write(');\n\n')#Close "Regions"
		  if F['Type'] in ['NEXAFS Image Scan','Image Scan','NEXAFS Line Scan']:
			E = D[Regions[0]][Detectors[0]]['E']
			f.write('\tStackAxis = { Name = "Energy"; Unit = "eV"; Min = '+str(E[0])+'; Max = '+str(E[-1])+'; Dir = -1;\n')
			f.write('\tPoints = ('+str(len(E)))
			for e in E:
			  f.write(', %.3f'%e)
			f.write(');\n')
			f.write('};\n')
		  f.write('\n')
		  f.write('\tChannels = ('+str(len(Detectors))+',\n')
		  for d in Detectors:
			if d is not Detectors[0]:
			  f.write(',\n')
			f.write('{ Name = "'+d+'"; Unit = "counts";}')
		  f.write(');\n};\n')
		  
		  f.write('Time = "'+time.strftime("%Y %B %d %H:%M:%S", D.start_time)+'"; ')
		  f.write('BeamFeedback = false; SampleXFeedback = false; SampleYFeedback = false; SampleZFeedback = false; ShutterAutomatic = false;\n')
		  f.write('Channels = (1,\n')
		  f.write('{ ID = 0; Type = 0; Name = "Counter0"; Controller = 0; DeviceNumber = 0; UnitName = "Hz"; LinearCoefficient = 1; ConstantCoefficient = 0; ProcessString = "I";});\n')
		  f.write('CoarseZ = { Name = CoarseZ; LastPosition =  1000; Status = 0; Type = 0; ControllerID = 0; Vel = 0;};\n')
  
		  f.write('StorageRingCurrent = '+str(D[r].monitor.flatten()[0])+'; PMT_CounterDivider = 1;\n')
		  f.write('ImageScan = { ScanType = "Image (Line - unidirection)"; Stage = "Automatic"; Shutter = "Automatic"; Interferometry = "On"; SingleEnergy = false;\n')
		  f.write('\tEnergyRegions = ('+str(len(F['EnergyRegions'])))
		  for ER in F['EnergyRegions']:
			f.write(',\n{ StartEnergy = '+str(ER['StartEnergy'])+'; EndEnergy = '+str(ER['EndEnergy'])+'; Range = '+str(ER['Range'])+'; Step = '+str(ER['Step'])+'; Points = '+str(ER['Points'])+'; DwellTime = '+str(ER['DwellTime'])+';}')
		  f.write(');\n PointDelay = 0.04; LineDelay = 0; AccelDist = 6.48058; MultipleRegions = false;\n')
		  f.write('\tSpatialRegions = (1,\n'+F['SpatialRegions']+');\n')
		  f.write('};\n')
		  if 'Image' in list(F.keys()):
			f.write(F['Image'])
		  f.write('\n')
		finally:
		  f.close()
		self.write_asciidata(D[r],OutBaseName,F['Type'])
		print('\n')
	  else:
		print('Skipping (already exists).')
	
  def filter_zeros(self,data):
	filtered = data.copy()
	if args.filter_dark[1] is not 0:
	  ZeroPixels = data<=2
	  zpx,zpy = numpy.where(ZeroPixels)
	  for i in range(len(zpx)):
		SafeNeighbours = [numpy.repeat(numpy.arange(max(0,zpx[i]-1),min(data.shape[0],zpx[i]+2)),min(data.shape[1],zpy[i]+2)-max(0,zpy[i]-1)),numpy.tile(numpy.arange(max(0,zpy[i]-1),min(data.shape[1],zpy[i]+2)),min(data.shape[0],zpx[i]+2)-max(0,zpx[i]-1))]
		if numpy.count_nonzero(ZeroPixels[SafeNeighbours]) <= args.filter_dark[0]:
		  filtered[zpx[i],zpy[i]] = numpy.average(data[SafeNeighbours], weights=numpy.logical_not(ZeroPixels[SafeNeighbours]))
	return filtered
	
  def normalise_PointByPoint(self,Data,nominal=400):
	for Di,D in enumerate(Data.keys()):#for all detectors
	  Data[D]['data'] = Data[D]['data']*nominal/Data.full_monitor.astype('float')
	Data.monitor = numpy.tile(nominal,Data.monitor.shape)
	
	
	
  def write_asciidata(self,data,BaseName,flag):
	Alphabet = 'abcdefghijklmnopqrstuvwxyz'
	if flag == 'NEXAFS Image Scan':
	  for Di,D in enumerate(data.keys()):
		for Ei in range(data[D]['data'].shape[0]):
		  FileExt = '_'+Alphabet[Di]+str(Ei).zfill(3)+'.xim'
		  print(BaseName+FileExt,end=' ')
		  numpy.savetxt(BaseName+FileExt, self.filter_zeros(data[D]['data'][Ei,:,:]), fmt='%g', delimiter='\t', newline='\n')
	elif flag == 'Image Scan':
	  for Di,D in enumerate(data.keys()):
		FileExt = '_'+Alphabet[Di]+'.xim'
		print(BaseName+FileExt,end=' ')
		numpy.savetxt(BaseName+FileExt, self.filter_zeros(data[D]['data'][0,:,:]), fmt='%g', delimiter='\t', newline='\n')
	elif flag == 'NEXAFS Line Scan':
	  for Di,D in enumerate(data.keys()):
		FileExt = '_'+Alphabet[Di]+'.xim'
		print(BaseName+FileExt,end=' ')
		#print(data[D]['data'][:,0,:].shape,data[D]['data'][-1,0,:].shape)
		#print(numpy.hstack((data[D]['data'][:,0,:],data[D]['data'][-1,0,:])))
		numpy.savetxt(BaseName+FileExt, self.filter_zeros(data[D]['data'][:,0,:].T), fmt='%g', delimiter='\t', newline='\n')
	elif flag == 'NEXAFS Point Scan':
	  DataTable = data[list(data.keys())[0]]['E']
	  for Di,D in enumerate(data.keys()):
		DataTable = numpy.vstack((DataTable,data[D]['data'].flatten()))
	  numpy.savetxt(BaseName+'_0.xsp', DataTable.T, fmt='%g', delimiter='\t', newline='\t\n') #filtering not implemented for point scans
	else:
	  print('ERROR: unknown \"Type\" flag "'+flag+'". No .xim or .xsp files saved.')
	

  def GenerateFields(self, Data):
	'''Generate fields specific to the Berkeley SDF data format. It is probably not a good idea to reuse this code for anything else!'''
	Fields = {'PAxis':{},'QAxis':{}}
	Detectors = list(Data.keys())
	Fields['count_time'] = Data[Detectors[0]]['count_time']*1000
	if Data[Detectors[0]]['scan_type'] in ImplementedScanTypes:
	  E = Data[Detectors[0]]['E']
	  T = Data[Detectors[0]]['count_time']*1000
	  Estep = E[1-len(E)]-E[0]
	  EnergyRegions = [{'StartEnergy':E[0],'Step':Estep,'Points':1,'DwellTime':T[0]}]
	  for i in range(1,len(E)):
		if abs(E[i]-E[i-1] - Estep) > 0.00001 or (len(T)>1 and T[i-1] != T[i]):
		  EnergyRegions[-1]['EndEnergy'] = E[i-1]
		  EnergyRegions[-1]['Range'] = E[i-1] - EnergyRegions[-1]['StartEnergy']
		  Estep = E[min(i+1,len(E)-1)]-E[i]
		  EnergyRegions.append({'StartEnergy':E[i],'Step':Estep,'Points':1,'DwellTime':T[i]})
		else:
		  EnergyRegions[-1]['Points'] = EnergyRegions[-1]['Points']+1
	  EnergyRegions[-1]['EndEnergy'] = E[-1]
	  EnergyRegions[-1]['Range'] = E[-1] - EnergyRegions[-1]['StartEnergy']
	  Fields['EnergyRegions'] = EnergyRegions
	  X = Data[Detectors[0]]['X']
	  Y = Data[Detectors[0]]['Y']
	  if Data[Detectors[0]]['data'].shape[1] > 1: ### if image data (image or stack), because Y axis is not trivial
		Fields['PAxis']['Name'] = 'Sample X'
		Fields['PAxis']['Points'] = X
		Fields['QAxis']['Name'] = 'Sample Y'
		Fields['QAxis']['Points'] = Y
		Fields['SpatialRegions'] = '{ CentreXPos = '+str((X[-1]+X[0])*0.5)+'; CentreYPos = '+str((Y[-1]+Y[0])*0.5)+'; XRange = '+str(X[-1]-X[0])+'; YRange = '+str(Y[-1]-Y[0])+'; XStep = '+str(X[len(X)>1]-X[0])+'; YStep = '+str(Y[len(Y)>1]-Y[0])+'; XPoints = '+str(len(X))+'; YPoints = '+str(len(Y))+';}'
		Fields['Image'] = ''
		for ei,e in enumerate(E):
		  i = 0
		  while not numpy.isfinite(Data.monitor[ei+i]):
			print("Warning: non-finite value recorded in StorageRingCurrent!")
			i += 1
			if ei+i == len(Data.monitor):
			  Data.monitor[-1] = 400.
			  i = i-1
		  Fields['Image'] = Fields['Image']+'Image'+str(ei+1)+' = {StorageRingCurrent = '+str(Data.monitor[ei+i])+'; Energy = -5.00; Time = "2000 May 01 00:00:00";};\n'
		if Data[Detectors[0]]['data'].shape[0] > 1: # if stack, because E axis is not trivial
		  Fields['Flags'] = 'Image Stack'
		  Fields['Type'] = 'NEXAFS Image Scan'
		else: ######################################### if image
		  Fields['Flags'] = 'Image'
		  Fields['Type'] = 'Image Scan'
	  else: ########################################### if spectrum or linescan data
		Fields['PAxis']['Name'] = 'Energy'
		Fields['PAxis']['Points'] = E
		if Data[list(Data.keys())[0]]['data'].shape[2] > 1: # if linescan, because X axis is not trivial
		  Fields['Flags'] = 'Image'
		  Fields['Type'] = 'NEXAFS Line Scan'
		  Length = ((X[-1]-X[0])**2 + (Y[-1]-Y[0])**2 )**0.5
		  Theta = numpy.degrees(numpy.arctan2(Y[-1]-Y[0],X[-1]-X[0]))
		  Fields['QAxis']['Name'] = 'Sample'
		  Fields['QAxis']['Points'] = numpy.linspace(0,Length,len(X))
		  Fields['SpatialRegions'] = '{ CentreXPos = '+str((X[-1]+X[0])*0.5)+'; CentreYPos = '+str((Y[-1]+Y[0])*0.5)+'; Length = '+str(Length)+'; Theta = '+str(Theta)+'; Step = '+str(Length/len(X))+'; Points = '+str(len(X))+';}'
		  Fields['Image'] = 'Image0 = {StorageRingCurrent = '+str(Data.monitor.flatten()[0])+'; Energy = -5.00; Time = "2000 May 01 00:00:00";};\n'
		else: ######################################### if point spectrum
		  Fields['SpatialRegions'] = '{ CentreXPos = '+str(X[0])+'; CentreYPos = '+str(Y[0])+';}'
		  Fields['Flags'] = 'Spectra'
		  Fields['Type'] = 'NEXAFS Point Scan'
		  Fields['QAxis'] = None
	return Fields

  def NeXusParser(self, fileName):
	'''HDF is a bit painful to traverse. This  method puts the important bits into a convenient ordered dictionary.'''
	AXIS_LIST = ['E','Y','X']
	NXfile = h5py.File(fileName, 'r')
	ScanDefinition = OrderedDict()
	for NXentrygroup in list(NXfile):
	  if 'NX_class' in NXfile[NXentrygroup].attrs and NXfile[NXentrygroup].attrs['NX_class'] == 'NXentry':
		ScanDefinition[NXentrygroup] = OrderedDict()
		try:
		  ScanDefinition.start_time = time.strptime(NXfile[NXentrygroup]['start_time'][0], "%Y-%m-%dT%H:%M:%S")
		except ValueError:
		  ScanDefinition.start_time = time.strptime(NXfile[NXentrygroup]['start_time'][0][:-6], "%Y-%m-%dT%H:%M:%S")#Ignore timezone info if present
		for NXdatagroup in list(NXfile[NXentrygroup]):
		  if 'NX_class' in NXfile[NXentrygroup][NXdatagroup].attrs and NXfile[NXentrygroup][NXdatagroup].attrs['NX_class'] == 'NXdata':
			ScanDefinition[NXentrygroup][NXdatagroup] = OrderedDict()
			try:#try new format
			   ScanDefinition[NXentrygroup][NXdatagroup]['scan_type'] = NXfile[NXentrygroup][NXdatagroup]['stxm_scan_type'][0]
			   ScanDefinition[NXentrygroup][NXdatagroup]['scan_type_new'] = True
			except KeyError:
			   ScanDefinition[NXentrygroup][NXdatagroup]['scan_type'] = NXfile[NXentrygroup][NXdatagroup]['scan_type'][0]
			   ScanDefinition[NXentrygroup][NXdatagroup]['scan_type_new'] = False
			ScanDefinition[NXentrygroup][NXdatagroup]['count_time'] = numpy.array(NXfile[NXentrygroup][NXdatagroup]['count_time'])
			ScanDefinition[NXentrygroup][NXdatagroup]['data'] = numpy.array(NXfile[NXentrygroup][NXdatagroup]['data'])
			if 'X' in list(NXfile[NXentrygroup][NXdatagroup]): #Old axis labels, can be removed after some time
			  ScanDefinition[NXentrygroup][NXdatagroup]['X'] = numpy.array(NXfile[NXentrygroup][NXdatagroup]['X'])
			  ScanDefinition[NXentrygroup][NXdatagroup]['Y'] = numpy.array(NXfile[NXentrygroup][NXdatagroup]['Y'])
			  ScanDefinition[NXentrygroup][NXdatagroup]['E'] = numpy.array(NXfile[NXentrygroup][NXdatagroup]['E'])
			elif ScanDefinition[NXentrygroup][NXdatagroup]['scan_type_new']: #Newest axis labels follow stage names, use 'axis' attribute to know which to use
			  #Newest data arrays also have more variable dimensionality (not necessarily E.Y.X)
			  axis_ind = [None,None,None]
			  for NXaxisgroup in list(NXfile[NXentrygroup][NXdatagroup]):
				if 'axis' in NXfile[NXentrygroup][NXdatagroup][NXaxisgroup].attrs:
				  axis_num = int(NXfile[NXentrygroup][NXdatagroup][NXaxisgroup].attrs['axis']) - 1
				else:
				  axis_num = None
				if NXaxisgroup in ['sample_x']:
				  ScanDefinition[NXentrygroup][NXdatagroup]['X'] = numpy.array(NXfile[NXentrygroup][NXdatagroup][NXaxisgroup])
				  axis_ind[2] = axis_num
				elif NXaxisgroup in ['sample_y']:
				  ScanDefinition[NXentrygroup][NXdatagroup]['Y'] = numpy.array(NXfile[NXentrygroup][NXdatagroup][NXaxisgroup])
				  axis_ind[1] = axis_num
				elif NXaxisgroup in ['energy']:
				  ScanDefinition[NXentrygroup][NXdatagroup]['E'] = numpy.array(NXfile[NXentrygroup][NXdatagroup][NXaxisgroup])
				  axis_ind[0] = axis_num
			  if axis_ind[0] is None:
				ScanDefinition[NXentrygroup][NXdatagroup]['data'] = ScanDefinition[NXentrygroup][NXdatagroup]['data'][numpy.newaxis,:]
			  if axis_ind[1] == axis_ind[2]:
				ScanDefinition[NXentrygroup][NXdatagroup]['data'] = numpy.expand_dims(ScanDefinition[NXentrygroup][NXdatagroup]['data'],axis=1)
				if axis_ind[1] is None:
				  ScanDefinition[NXentrygroup][NXdatagroup]['data'] = ScanDefinition[NXentrygroup][NXdatagroup]['data'][:,numpy.newaxis]
			else: #New axis labels follow stage names, use 'axis' attribute to know which to use
			  axis_flag = 0
			  for NXaxisgroup in list(NXfile[NXentrygroup][NXdatagroup]):
				if 'axis' in NXfile[NXentrygroup][NXdatagroup][NXaxisgroup].attrs:
				  axis_num = int(NXfile[NXentrygroup][NXdatagroup][NXaxisgroup].attrs['axis']) - 1
				  if axis_num == 2:
					if axis_flag:
					  axis_num = 1
					else:
					  axis_flag = 1
				  ScanDefinition[NXentrygroup][NXdatagroup][AXIS_LIST[axis_num]] = numpy.array(NXfile[NXentrygroup][NXdatagroup][NXaxisgroup])
		  elif 'NX_class' in NXfile[NXentrygroup][NXdatagroup].attrs and NXfile[NXentrygroup][NXdatagroup].attrs['NX_class'] == 'NXinstrument':  #This should only be needed for old files.
			for NXcomponentgroup in list(NXfile[NXentrygroup][NXdatagroup]):
			  if 'NX_class' in NXfile[NXentrygroup][NXdatagroup][NXcomponentgroup].attrs and NXfile[NXentrygroup][NXdatagroup][NXcomponentgroup].attrs['NX_class'] == 'NXsource':
				ScanDefinition[NXentrygroup].backup_monitor = numpy.array(NXfile[NXentrygroup][NXdatagroup][NXcomponentgroup]['current'])[0]
		  elif 'NX_class' in NXfile[NXentrygroup][NXdatagroup].attrs and NXfile[NXentrygroup][NXdatagroup].attrs['NX_class'] == 'NXmonitor':
			if NXdatagroup in ['ring_current','Ring_Current']:
			  ScanDefinition[NXentrygroup].monitor = numpy.array(NXfile[NXentrygroup][NXdatagroup]['data'])
	  num_E = max(1,len(ScanDefinition[NXentrygroup][list(ScanDefinition[NXentrygroup])[0]]['E']))
	  if hasattr(ScanDefinition[NXentrygroup],'monitor'):
		ScanDefinition[NXentrygroup].full_monitor = ScanDefinition[NXentrygroup].monitor
		ScanDefinition[NXentrygroup].monitor = ScanDefinition[NXentrygroup].monitor.transpose().flatten()[:num_E]
	  else:
		if hasattr(ScanDefinition[NXentrygroup],'backup_monitor'):
		  ScanDefinition[NXentrygroup].monitor = numpy.tile(ScanDefinition[NXentrygroup].backup_monitor,num_E)
		else:
		  ScanDefinition[NXentrygroup].monitor = numpy.tile(400,num_E)
	ScanDefinition.type_flags = ["NEXAFS Image Scan","Image Stack"]
	return ScanDefinition
		




#-------------------------------------------------------------------------------
if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='convert NeXus .hdf5 STXM data files to the Berkeley SDF STXM format.',
  epilog='To avoid restrictions of the SDF format, each spatial region in the NeXus file (each "entry" group) is converted separately and a "_r#" suffix is added to the output file names.')
  parser.add_argument('NeXusFileName', nargs='*', default='.', help='List of NeXus file(s) and/or directories containing NeXus files to convert.')
  file_group = parser.add_mutually_exclusive_group()
  file_group.add_argument('-o', '--overwrite', action='store_true',help='Overwrite files (default if only one NeXus file name is given).')
  file_group.add_argument('-a', '--ask-write', action='store_true',help='Ask before overwriting.')
  file_group.add_argument('-s', '--skip', action='store_true', help='Skip existing files (don\'t overwrite) (default if converting a directory or list of NeXus files).')
  parser.add_argument('-d', '--directory', default='.', help='Path to output directory.')
  filter_group = parser.add_mutually_exclusive_group()
  filter_group.add_argument('-f', '--filter-zero', nargs='?', type=int, default=0, const=1, help='Remove isolated zero pixels. Pixels having a value of zero and having fewer zero pixels in the 3x3 neighbourhood than the isolation threshold (optional parameter; 0=no filtering (default if flag is not present), 1=isolated pixels (default if flag is present), 2=adjacent pairs also filtered, ..., 8=all dark pixels filtered) are set to the average of all neighbouring non-zero pixels. (Not implemented for point-spectra.)')
  filter_group.add_argument('-ff', '--filter-dark', nargs=2, type=float, default=[1.0,0], help='Remove isolated dark pixels. Pixels having values at or below the value threshold (first parameter; default is 0) and having fewer dark pixels in the 3x3 neighbourhood than the isolation threshold (second parameter; same effect as described for --filter-zero) are set to the average of all neighbouring pixels that do not meet the same conditions. (Not implemented for point-spectra.)')
  parser.add_argument('-n', '--normalise', action='store_true',help='Normalise the data by the ring current on a point-by-point basis.')
  args = parser.parse_args()
  
  ###Check inputs
  if not os.access(args.directory,os.W_OK):
	try:
	  os.mkdir(args.directory)
	except:
	  print('Unable to create output directory.\nExiting.')
	  exit()
  Overwrite = 'Yes' #default behaviour for single file conversion
  ###get list of inputs
  FullNeXusList = []
  for path in args.NeXusFileName:
	if os.path.isdir(path):
	  Overwrite = 'No' #default behaviour for lists of files
	  FullNeXusList.extend([os.path.join(path,f) for f in listdir(path) if f[-4:] in ['hdf5','.nxs']])
	elif os.path.isfile(path):
	  FullNeXusList.append(path)
  ### overwriting behaviour
  if args.ask_write:
	Overwrite = 'Ask'
  elif args.overwrite:
	Overwrite = 'Yes'
  elif args.skip:
	Overwrite = 'No'
  ### filtering dark pixels
  if args.filter_zero is not 0:
	args.filter_dark[1] = args.filter_zero
  else:
	args.filter_dark[1] = int(args.filter_dark[1])
  ###work on inputs
  if len(FullNeXusList) == 0:
	print('No files found.')
  else:
	for NeXus in FullNeXusList:
	  write_SDF(NeXus,args.directory,overwrite=Overwrite,normalise=args.normalise)
	print('\nFinished!')
  
 
