'''
Created on May 30, 2018

@author: bergr
'''
import os

from PyQt5 import QtWidgets
from PyQt5 import uic

from bcm.devices.device_names import *
from bcm.devices import Transform

from cls.applications.pyStxm.main_obj_init import MAIN_OBJ
from cls.devWidgets.ophydLabelWidget import assign_aiLabelWidget
from cls.types.stxmTypes import endstation_id_types
from cls.appWidgets.basePreference import BasePreference


widgetsUiDir = os.path.join( os.path.dirname(os.path.abspath(__file__)))

def angstrom_to_nanometer(ang):
	ang_to_nm = 0.1
	return(ang * ang_to_nm)

def nanometer_to_angstrom(nm):
	nm_to_ang = 10
	return(nm * nm_to_ang)


def A0Max(zpD, f, osaD):
	'''
	AoMax = (Do * f)/D
	where: 
		Do is OSA diameter
		D is ZP Diamter
		f is focal length
	
	todo:
	'''
	
	Do = osaD
	D = zpD 
	aomax = (Do * (-1.0 *f))/D
	Cz = aomax - 15 #ideally set Cz to about 15um less than A0 max
	return((aomax, Cz))


def waveLength(energy):
	''' 
	return the wavelength as a function of energy, returned in nanometers
	E(eV) = 12398.52/lambda
	lambda = 12398.52/E(eV)
	'''
	wvLen = float(12398.52/energy)
	return(wvLen)
	


def focal_length(energy, a1):
	'''
	f = A1 * E 
	'''
	f = a1 * energy 

	return(f)


def get_zp_dct():
	
	zp1 = {'a1':-4.840,'D':100.0, 'CsD':45.0, 'OZone': 60.0}
	zp2 = {'a1':-6.792,'D':240.0, 'CsD':90.0, 'OZone': 35.0}
	zp3 = {'a1':-7.767,'D':240.0, 'CsD':90.0, 'OZone': 40.0}
	zp4 = {'a1':-4.524,'D':140.0, 'CsD':60.0, 'OZone': 40.0}
	zp5 = {'a1':-4.859,'D':240.0, 'CsD':95.0, 'OZone': 25.0}
	zp6 = {'a1': -4.857, 'D': 240.0, 'CsD': 95.0, 'OZone': 25.0}
	zp7 = {'a1': -5.067, 'D': 250.0, 'CsD': 100.0, 'OZone': 25.0}
	zps = [zp1, zp2, zp3, zp4, zp5, zp6, zp7]
	return(zps)

def get_amb_osa_dct():
	osa1 = {'D':30.0}
	osa2 = {'D':50.0}
	osa3 = {'D':40.0}
	osas = [osa1, osa2, osa3]
	return(osas)

def get_uhv_osa_dct():
	osa1 = {'D':40.0}
	osa2 = {'D':50.0}
	osa3 = {'D':60.0}
	osa4 = {'D':70.0}
	osas = [osa1, osa2, osa3, osa4]
	return(osas)

def get_osa_dct():
	devices = MAIN_OBJ.get_device_obj()
	if(devices.es_id == endstation_id_types.UHV):
		osas = get_uhv_osa_dct()
	else:
		osas = get_amb_osa_dct()
	return(osas)


def calc_zpz(f, A0):
	zpz = f + A0
	return(zpz)


def focus_to_cursor_set_Cz(f, A0, Cz, new_zpz):
	calcd_zpz = calc_zpz(f, A0)
	delta_zpz = calcd_zpz - new_zpz
	new_Cz = Cz + delta_zpz
	#print 'focus_to_cursor_set_Cz:'
	#print 'new focus found at Zpz=%.2fum, deltaToFocus=%.2f ' % (new_zpz, delta_zpz)
	#print 'move Zpz to %.2f, move Cz from %.2f to %.2f' % (calcd_zpz, Cz, new_Cz)
	return((calcd_zpz, new_Cz))
	

def focus_to_cursor_set_A0(f, A0, Cz, new_zpz):
	calcd_zpz = calc_zpz(f, A0)
	delta_zpz = calcd_zpz - new_zpz
	X = new_zpz - calcd_zpz
	A0updated = X + A0
	#print 'focus_to_cursor_set_A0:'
	#print 'new focus found at Zpz=%.2fum, deltaToFocus=%.2f ' % (new_zpz, delta_zpz)
	#print 'change A0 from %.2f to %.2f' % (A0, A0updated)
	return((calcd_zpz, A0updated))


def init_zp_def_transform_rec(zp_def, blEnergy='BL1610-I10:ENERGY',stxm='uhv'):
	#currently these are defined here but these need to evenutally be written to disk and loaded
	return
	# def_idx = zp_def['zp_id']
	# trec = Transform('%s:%s:zp%d:def' % (blEnergy, stxm, def_idx))
	# trec.put('DESC', stxm + ' zp%d def' % def_idx)
	# trec.put('CMTA', 'zp%d A1' % def_idx)
	# trec.put('A', zp_def['a1'])
	# trec.put('OUTA', '%s:%s:zp:def.CLCA PP' % (blEnergy, stxm))
	#
	# trec.put('CMTB', 'zp%d Diameter' % def_idx)
	# trec.put('B', zp_def['D'])
	# trec.put('OUTB', '%s:%s:zp:def.CLCB PP' % (blEnergy, stxm))
	#
	# trec.put('CMTC', 'zp%d Central stop' % def_idx)
	# trec.put('C', zp_def['CsD'])
	# trec.put('OUTC', '%s:%s:zp:def.CLCC PP' % (blEnergy, stxm))
	#
	# trec.put('CMTD', 'zp%d Resolution' % def_idx)
	# trec.put('D', zp_def['OZone'])
	# trec.put('OUTD', '%s:%s:zp:def.CLCD PP' % (blEnergy, stxm))
	
def init_osa_def_transform_rec(osa_def, blEnergy='BL1610-I10:ENERGY',stxm='uhv'):
	#currently these are defined here but these need to evenutally be written to disk and loaded
	return
	# def_idx = osa_def['osa_id']
	# trec = Transform('%s:%s:zp%d:def' % (blEnergy, stxm, def_idx))
	# trec.put('DESC', stxm + ' osa%d def' % def_idx)
	# trec.put('CMTA', 'osa%d A1' % def_idx)
	# trec.put('A', osa_def['D'])
	
	

class FocusParams(BasePreference):

	def __init__(self, name='FocusParams', parent=None):
		super(FocusParams, self).__init__(name, parent)
		self._parent = parent
		uic.loadUi(	os.path.join(widgetsUiDir, 'focusAndZoneplateParms.ui'), self) 

		self.evFbkLbl = assign_aiLabelWidget(self.evFbkLbl, MAIN_OBJ.device(DNM_ENERGY_RBV), hdrText='Energy', egu='eV', title_color='white', var_clr='white')
		self.a1FbkLbl = assign_aiLabelWidget(self.a1FbkLbl, MAIN_OBJ.device(DNM_ZP_DEF_A), hdrText='A1', egu='', title_color='white', var_clr='white',format='%5.4f')
		self.a0MaxFbkLbl = assign_aiLabelWidget(self.a0MaxFbkLbl, MAIN_OBJ.device(DNM_A0MAX), hdrText='A0Max', egu='um', title_color='white', var_clr='white',format='%5.2f')
		self.flFbkLbl = assign_aiLabelWidget(self.flFbkLbl, MAIN_OBJ.device(DNM_FOCAL_LEN), hdrText='Fl', egu='um', title_color='white', var_clr='white',format='%5.2f')
		self.sampleZFbkLbl = assign_aiLabelWidget(self.sampleZFbkLbl, MAIN_OBJ.device(DNM_IDEAL_A0), hdrText='Cz', egu='um', title_color='white', var_clr='white',format='%5.2f')
		self.zpzFbkLbl = assign_aiLabelWidget(self.zpzFbkLbl, MAIN_OBJ.device(DNM_ZPZ_RBV), hdrText='Zpz', egu='um', title_color='white', var_clr='white',format='%5.2f')
		
		self.a0Fld.returnPressed.connect(self.on_a0_changed)
		
		self.zpToolBox = QtWidgets.QToolBox()
		self.osaToolBox = QtWidgets.QToolBox()
		
		self.zp_tbox_widgets = []
		self.osa_tbox_widgets = []

		self._cur_sel_zp_def = {}
		
		zp_dct = self.get_section('ZP_PARAMS')
		osa_dct = self.get_section('OSA_PARAMS')

		self.zp_panels = []
		pages = 0
		for zp_def in zp_dct:
			zpParms_ui = uic.loadUi( os.path.join(widgetsUiDir, 'zpFlds.ui') )

			init_zp_def_transform_rec(zp_def, stxm=MAIN_OBJ.get_endstation_prefix())
			
			#populate fields
			zpParms_ui.zpDFld.setText('%.2f' % zp_def['D'])
			zpParms_ui.zpCStopFld.setText('%.2f' % zp_def['CsD'])
			zpParms_ui.zpOZoneFld.setText('%.2f' % zp_def['OZone'])
			zpParms_ui.zpA1Fld.setText('%.3f' % zp_def['a1'])
			
			zpParms_ui.zpDFld.returnPressed.connect(self.update_zp_data)
			zpParms_ui.zpCStopFld.returnPressed.connect(self.update_zp_data)
			zpParms_ui.zpOZoneFld.returnPressed.connect(self.update_zp_data)
			zpParms_ui.zpA1Fld.returnPressed.connect(self.update_zp_data)
			
			self.zpToolBox.insertItem(pages, zpParms_ui, 'ZP %d'%(pages+1))
			self.zp_tbox_widgets.append(zpParms_ui)
			pages += 1
			
			self.zp_panels.append(zpParms_ui)
		
		self.zpGroupBox.layout().addWidget(self.zpToolBox)
		self.zpToolBox.setCurrentIndex(1)
		
		
		pages = 0
		for osa_def in osa_dct:
			osaParms_ui = uic.loadUi(os.path.join(widgetsUiDir, 'osaFlds.ui'))
			
			init_osa_def_transform_rec(osa_def)
			
			#populate fields
			osaParms_ui.osaDFld.setText('%.2f' % osa_def['D'])
			self.osaToolBox.insertItem(pages, osaParms_ui, 'OSA %d'%(pages+1))
			
			osaParms_ui.osaDFld.returnPressed.connect(self.update_osa_data)
			self.osa_tbox_widgets.append(osaParms_ui)
			pages += 1
		
		self.osaGroupBox.layout().addWidget(self.osaToolBox)
		self.osaToolBox.setCurrentIndex(1)

		self.zpToolBox.currentChanged.connect(self.update_zp_selection)
		self.osaToolBox.currentChanged.connect(self.update_osa_selection)
		
		#MAIN_OBJ.device(DNM_ZONEPLATE_SCAN_MODE).put('user_setpoint', 1)
		MAIN_OBJ.device(DNM_ZONEPLATE_SCAN_MODE).put(1)

		# init from saved
		self.reload()

		#configure the preference sections that will be saved in DEFAULTS, create if they dont already exist
		self.add_section('ZP_FOCUS_PARAMS.ZP_IDX')
		self.add_section('ZP_FOCUS_PARAMS.ZP_A1')
		self.add_section('ZP_FOCUS_PARAMS.OSA_IDX')
		self.add_section('ZP_FOCUS_PARAMS.OSA_A0')
		self.add_section('ZP_FOCUS_PARAMS.ZP_D')
		self.add_section('ZP_FOCUS_PARAMS.OSA_D')
		self.add_section('ZP_FOCUS_PARAMS.OSA_A0')
		self.add_section('ZP_FOCUS_PARAMS.OSA_A0MAX')
		self.add_section('ZP_PARAMS', {})
		self.add_section('OSA_PARAMS', {})



	def reload(self):
		'''
		load settings saved in the DEFAULTS module
		:return:
		'''
		zp_idx = self.get_section('ZP_FOCUS_PARAMS.ZP_IDX')
		zpA1 = self.get_section('ZP_FOCUS_PARAMS.ZP_A1')
		osa_idx = self.get_section('ZP_FOCUS_PARAMS.OSA_IDX')
		A0 = self.get_section('ZP_FOCUS_PARAMS.OSA_A0')

		# Jan16 2018 MAIN_OBJ.device('A0').put(A0)
		# force epics to update the record def fror ZP's
		MAIN_OBJ.device('Zp_select').put('user_setpoint', zp_idx)

		self.a0Fld.setText('%.3f' % A0)
		zp_pnl = self.zp_panels[zp_idx]
		zp_pnl.zpA1Fld.setText('%.3f' % zpA1)

		self.zpToolBox.setCurrentIndex(zp_idx)
		self.osaToolBox.setCurrentIndex(osa_idx)

	def on_energy_fbk_changed(self, val):
		self.update_zp_data(update_defaults=False)

	def on_a0_changed(self):
		A0 = float(str(self.a0Fld.text()))
		MAIN_OBJ.device('A0').put(A0)
		self.update_zp_data()

	def update_zp_selection(self):
		zp_idx = self.zpToolBox.currentIndex()
		MAIN_OBJ.device('Zp_select').put('user_setpoint', zp_idx)
		self.update_zp_data()
		
	def update_osa_selection(self):
		osa_idx = self.osaToolBox.currentIndex()
		MAIN_OBJ.device('OSA_select').put('user_setpoint', osa_idx)
		self.update_zp_data()
	
	def update_osa_data(self):
		osasel_pv = MAIN_OBJ.device('OSA_select')
		osadef_pv = MAIN_OBJ.device('OSA_def')
		idx = self.osaToolBox.currentIndex()
		_ui = self.osa_tbox_widgets[idx]
		osaD = float(str(_ui.osaDFld.text())) 

		#get list of zp defs
		#osas = DEFAULTS.get('PRESETS.OSA_PARAMS')
		osas = self.get_section('OSA_PARAMS')
		osas[idx]['D'] = osaD
		self.set_section('OSA_PARAMS', osas)
		
		self.update_zp_data()
		
		
	def update_zp_data(self, update_defaults=True):
		"""
		Write ZP select
		Write OSA Select
		Write A0
		Write
		Mode select
		Store presets
		
		"""
		zp_idstrs = ['A','B','C','D','E','F','G','H','I','J']
		energy = float(str(self.evFbkLbl.get_text()))
		aomax = float(str(self.a0MaxFbkLbl.get_text()))
		zp_idx = self.zpToolBox.currentIndex()

		zpParms_ui = self.zp_tbox_widgets[zp_idx]
		
		osa_idx = self.osaToolBox.currentIndex()
		osa_ui = self.osa_tbox_widgets[osa_idx]
		osaD = float(str(osa_ui.osaDFld.text())) 
		A0 = float(str(self.a0Fld.text()))

		self._cur_sel_zp_def = {}

		self._cur_sel_zp_def['fl'] = fl = float(str(self.flFbkLbl.get_text()))
		self._cur_sel_zp_def[DNM_ZPZ_POS] = Zpz_pos = float(str(self.zpzFbkLbl.get_text()))
		self._cur_sel_zp_def['Cz_pos'] = Cz_pos = float(str(self.sampleZFbkLbl.get_text()))
		self._cur_sel_zp_def['zpD'] = zpD = float(str(zpParms_ui.zpDFld.text()))
		self._cur_sel_zp_def['zpCStop'] = zpCStop = float(str(zpParms_ui.zpCStopFld.text()))
		self._cur_sel_zp_def['zpOZone'] = zpOZone = float(str(zpParms_ui.zpOZoneFld.text()))
		self._cur_sel_zp_def['zpA1'] = zpA1 = float(str(zpParms_ui.zpA1Fld.text()))
		self._cur_sel_zp_def['zp_idx'] = zp_idx + 1 # make base 1

		devices = MAIN_OBJ.get_devices()
		pv_keys = list(devices['PVS'].keys())
		z_str = 'Zp_def%d_A' % zp_idx
		if(z_str in pv_keys):
			devices['PVS'][z_str].put(zpA1)

		self.set_section('ZP_FOCUS_PARAMS.ZP_IDX', zp_idx)
		self.set_section('ZP_FOCUS_PARAMS.ZP_A1', zpA1)
		self.set_section('ZP_FOCUS_PARAMS.ZP_D', zpD)
		self.set_section('ZP_FOCUS_PARAMS.OSA_IDX', osa_idx)
		self.set_section('ZP_FOCUS_PARAMS.OSA_D', osaD)
		self.set_section('ZP_FOCUS_PARAMS.OSA_A0', A0)
		self.set_section('ZP_FOCUS_PARAMS.OSA_A0MAX', aomax)
		
		zps = self.get_section('ZP_PARAMS')
		#{'osa_id': 1, 'D':30.0}
		zps[zp_idx]['a1'] = zpA1
		#DEFAULTS.set('PRESETS.ZP_PARAMS', zps)
		self.set_section('ZP_PARAMS', zps)

	def get_cur_zp_def(self):
		self.update_zp_data()
		return(self._cur_sel_zp_def)


if __name__ == "__main__":
	import sys
	
	app = QtWidgets.QApplication(sys.argv)
	window = FocusParams()
	window.show()
	
	app.exec_()
	