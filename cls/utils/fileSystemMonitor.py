'''
Created on Apr 29, 2016

@author: bergr
'''

import os
import sys
import copy

from PyQt5 import QtCore, QtGui, QtWidgets

from cls.utils.dirlist import dirlist

class DirectoryMonitor(QtWidgets.QWidget):
	
	changed = QtCore.pyqtSignal()
	
	def __init__(self,queue=None, block_sigs_on_init=False, parent=None):
		"""
		__init__(): description

		:param parent=None: parent=None description
		:type parent=None: parent=None type

		:returns: None
		"""
		QtWidgets.QWidget.__init__(self)
		self.data_dir = None
		self.queue = queue
		self.file_extension = '.jpg'
		self.model = QtWidgets.QFileSystemModel()
		if(block_sigs_on_init):
			self.blockSignals(True)

		self.model.rowsInserted.connect(self.on_dir_changed)
		self.model.rowsRemoved.connect(self.on_dir_changed)
		self.view = QtWidgets.QTreeView()
		self.view.setModel(self.model)
		self.data = []
		
		self.added = []
		self.removed = []

		#####
		self.timer = None


	def set_data_dir(self, data_dir, do_block=True):
		"""
		set_data_dir(): description

		:param data_dir: data_dir description
		:type data_dir: data_dir type

		:returns: None
		"""
		if(len(data_dir) > 0):
			if(do_block):
				self.blockSignals(True)
				self.model.blockSignals(True)
			self.data_dir = data_dir
			self.model.setRootPath(self.data_dir)
			self.view.setRootIndex(self.model.index(self.data_dir))

			if(do_block):
				self.blockSignals(False)
				self.model.blockSignals(False)
			self.init_file_list()
	
	def set_file_extension_filter(self, ext='.jpg'):
		"""
		set_file_extension_filter(): description

		:param ext='.jpg': ext='.jpg' description
		:type ext='.jpg': ext='.jpg' type

		:returns: None
		"""
		self.file_extension = ext		
	
	def return_whats_different(self, lista, listb):
		"""
		return_whats_different(): description

		:param lista: lista description
		:type lista: lista type

		:param listb: listb description
		:type listb: listb type

		:returns: None
		"""
		result = [c for c in listb if c not in lista]
		return(result)
	
	def on_dir_changed(self, index, start, end):
		"""
		on_dir_changed(): description

		:param index: index description
		:type index: index type

		:param start: start description
		:type start: start type

		:param end: end description
		:type end: end type

		:returns: None
		"""
		#print 'fileSystemMonitor: on_dir_changed'
		added = []
		removed = []	
		new_data = dirlist(self.data_dir, self.file_extension, remove_suffix=False)
		if(len(new_data) < len(self.data)):
			#files have been deleted
			removed = self.return_whats_different(new_data, self.data)
		else:
			#files have been added	
			added = self.return_whats_different(self.data, new_data)
		self.data = copy.copy(new_data)
		self.added = added
		self.removed = removed
		if(self.queue is not None):
			_dct = {}
			send = False
			if(len(added) > 0):
				_dct['added'] = added
				send = True
			
			if(len(removed) > 0):
				_dct['removed'] = removed
				send = True
				
			if(send):
				self.queue.put_nowait(_dct)
				#adding a timer so that the file can finish writing, otherwise I get intermittant errors opening
				## file in ThumbnailViewer because its not ready yet
				self.timer = QtCore.QTimer()
				self.timer.setSingleShot(True)
				self.timer.timeout.connect(self.on_timer)
				self.timer.start(len(self.added) * 50)
				#print 'fileSystemMonitor: on_dir_changed: emitting CHANGED with len(self.added=%d)' % len(self.added)
				self.changed.emit()

	def on_timer(self):
		#now let everyone know were changed
		#print 'on_timer: len(added)=%d' % len(self.added)
		self.changed.emit()
	
	def init_file_list(self):
		"""
		init_file_list(): description

		:returns: None
		"""
		self.data = dirlist(self.data_dir, self.file_extension, remove_suffix=False)
	
	def get_file_list(self):
		"""
		get_file_list(): description

		:returns: None
		"""
		return(self.data)			
		


def on_dir_changed(xxx_todo_changeme):
	"""
	on_dir_changed(): description
	:param on_dir_changed((f_added: on_dir_changed((f_added description
	:type on_dir_changed((f_added: on_dir_changed((f_added type
	:param f_removed): f_removed) description
	:type f_removed): f_removed) type
	:returns: None
	"""
	(f_added, f_removed) = xxx_todo_changeme
	print('added: ' , f_added)
	print('removed: ' , f_removed)

def on_changed():
	global myview
	print('changed was fired: len(myview.added)=%d' % len(myview.added))


def update_file_list():
	global myview
	call_task_done = False
	f_added = []
	f_removed = []
	while not myview.queue.empty():
		resp = myview.queue.get()
		if ('added' in list(resp.keys())):
			f_added = resp['added']
			call_task_done = True

		if ('removed' in list(resp.keys())):
			f_removed = resp['removed']
			call_task_done = True

	if (call_task_done):
		on_dir_changed((f_added, f_removed))
		myview.queue.task_done()


if __name__ == '__main__':
	import queue

	app = QtWidgets.QApplication(sys.argv)
	queue = queue.Queue()
	myview = DirectoryMonitor(queue=queue)
	#myview.changed.connect(on_dir_changed)
	myview.changed.connect(update_file_list)
	#myview.set_file_extension_filter('.jpg')
	myview.set_file_extension_filter('.hdf5')
	#myview.show()
	myview.set_data_dir(r'S:\STXM-data\Cryo-STXM\2018\guest\test', do_block=False)
	myview.on_dir_changed(0,0,0)
	sys.exit(app.exec_())