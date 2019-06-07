'''
Created on 2014-05-26

@author: bergr
'''
#!/usr/bin/env python
"""Epics analog input record"""
import epics

class digitalIO(epics.Device):
	"Simple interface to DAQmx Epics digital IO task"

	attrs = ('Run','ClockSrcSelect_RBV','LineSelect_RBV','PortSelect_RBV','PulseWidth_RBV',
			'SamplesPerChan_RBV','SamplingRate_RBV','TimeOut_RBV','PulseWidth','SamplesPerChan','SamplingRate',
			'TimeOut','ClockSrcSelect','DeviceSelect','EdgeSelect','GenMode','LineSelect','PortSelect','TaskType','TrigSrcSelect',
			'TrigStartEdgeSel','TriggerType','AutoStart_RBV','InvertLines_RBV','Retriggerable_RBV','Run_RBV','AutoStart','InvertLines','Retriggerable',
			'ReadLine','ReadPort','ReadLine_B0','ReadLine_B1','ReadLine_B2','ReadLine_B3','ReadLine_B4','ReadLine_B5','ReadLine_B6',
			'ReadLine_B7','ReadLine_B8','ReadLine_B9','ReadLine_BA','ReadLine_BB','ReadLine_BC','ReadLine_BD',
			'ReadLine_BE','ReadLine_BF','ReadPort_B0','ReadPort_B1','ReadPort_B2','ReadPort_B3','ReadPort_B4',
			'ReadPort_B5','ReadPort_B6','ReadPort_B7','ReadPort_B8','ReadPort_B9','ReadPort_BA','ReadPort_BB',
			'ReadPort_BC','ReadPort_BD','ReadPort_BE','ReadPort_BF',
			'WriteLine','WritePort','WriteLine_B0','WriteLine_B1','WriteLine_B2','WriteLine_B3','WriteLine_B4','WriteLine_B5',
			'WriteLine_B6','WriteLine_B7','WriteLine_B8','WriteLine_B9','WriteLine_BA','WriteLine_BB','WriteLine_BC',
			'WriteLine_BD','WriteLine_BE','WriteLine_BF','WritePort_B0','WritePort_B1','WritePort_B2','WritePort_B3',
			'WritePort_B4','WritePort_B5','WritePort_B6','WritePort_B7','WritePort_B8','WritePort_B9','WritePort_BA',
			'WritePort_BB','WritePort_BC','WritePort_BD','WritePort_BE','WritePort_BF','ReadLine_bits','ReadPort_bits',
			'WriteLine_bits','WritePort_bits')

	def __init__(self, prefix, **kwargs):
		if prefix.endswith('.'):
			prefix = prefix[:-1]
		epics.Device.__init__(self, prefix, delim=':', attrs=self.attrs, **kwargs)
		self.configure()
	
	def configure(self):
		""" to be implemented by inheriting class """
		pass
	
	def set_bit(self, bit, val):
		hx = hex(bit).split('x')[1]
		attr = 'WriteLine_B%s' % hx.upper()
		print('set_bit: [%s]=%x' % (attr, val))
		self.put(attr, val)
		
	def set_port(self, port, val):
		hx = hex(port).split('x')[1]
		attr = 'WritePort_B%s' % hx.upper()
		print('set_port: [%s]=%x' % (attr, val))
		self.put(attr, val)
		
	def get_bit(self, bit):
		hx = hex(bit).split('x')[1]
		attr = 'ReadLine_B%s' % hx.upper()
		val = self.get(attr)
		print('get_bit: [%s]=%x' % (attr, val))
		
		
	def get_port(self, port):
		hx = hex(port).split('x')[1]
		attr = 'ReadPort_B%s' % hx.upper()
		val = self.get(attr)
		print('get_port: [%s]=%x' % (attr, val))
		



class BaseTrigger(digitalIO):	
	""" test trigger """
	
	def __init__(self, prefix, **kwargs):
		if prefix.endswith('.'):
			prefix = prefix[:-1]
		epics.Device.__init__(self, prefix, delim=':', attrs=self.attrs, **kwargs)	
		
		
	def configure(self):
		self.put('Run', 0)
		self.put('DeviceSelect', 3)		#/Dev4
		self.put('PortSelect', 1)		#port1
		self.put('LineSelect', 3)		#DIGITAL_OUTPUT_LINE
		self.put('TaskType', 2)		#line3
		self.put('GenMode', 0)			#finite_Samps
		self.put('SampleMode', 0)		#DAQmx_Val_FiniteSamps
		self.put('SamplesPerChan', 2)	#
		self.put('SamplingRate', 10.0)	#10.0 Hz
		self.put('TriggerType', 3)		#DAQmx_Digital_Edge	
		self.put('TrigSrcSelect', 3)	#/PFI3
		self.put('TriggerDelay', 0.0)		

if __name__ == '__main__':
	shttr = BaseTrigger('testDIO:shutter')
	shttr.set_bit(0, 1)
	shttr.set_port(0, 5)
	
	shttr.get_bit(0)
	shttr.get_port(0)
	
	
	
	
			
		
		
		
		
