import os, sys

from PyQt5 import QtGui, QtCore, QtWidgets, uic
from cls.appWidgets.dialogs import getOpenFileName


import re
	

re1='.*?'	# Non-greedy match on filler
re2='(\\(self\\))'	# Round Braces 1
		
rg = re.compile(re1+re2,re.IGNORECASE|re.DOTALL)
# m = rg.search(txt)
# if m:
#     rbraces1=m.group(1)
#     print "("+rbraces1+")"+"\n"


class Window(QtWidgets.QWidget):
	"""
	classdocs
	"""
	
	def __init__(self):
		QtWidgets.QWidget.__init__(self)
		uic.loadUi('autodoc.ui', self)
		self.setWindowTitle('AutoDocument a python file')
		self.setGeometry(550,550,500,500)
		self.loadBtn.clicked.connect(self.on_clicked)
		self.saveBtn.clicked.connect(self.on_save)
		self.fnameLbl.setText('')
		self.fileLines = []
		self.newlines = []
		self.fname = None
		
	def on_clicked(self):
		self.fname = str(getOpenFileName("Get Filename", filter_str="py Files (*.py)", search_path=r'.'))
		
		if(os.path.exists(self.fname)):
			self.originalTextEdit.clear()
			self.cmntdTextEdit.clear()
			
			
			self.fnameLbl.setText(self.fname)
			lines = self.load_file(self.fname)
			self.newlines = self.comment_lines(lines)
			for l in lines:
				self.originalTextEdit.append(l)
			
			for l in self.newlines:	
				self.cmntdTextEdit.append(l)
			#for line in newlines:
			#	print line
			
			#self.save_file(fname + '.cmntd.py', newlines)
	
	def on_save(self):
		self.save_file(self.fname + '.cmntd.py', self.newlines)
		
	def comment_lines(self, lines):
		newlines = []
		for l in lines:
			l2 = l.strip('\n')
			if(self.is_func_def(l2)):
				newlines.append(l2)
				func_name, parmstr = self.get_func_args(l2)
				newlines.append('\t\t"""')
				newlines.append(self.add_func_desc(func_name))
				newlines.append(parmstr)
				newlines.append('\t\t"""')
			else:
				newlines.append(l2)
		return(newlines)
	
	def is_func_def(self, line):
		if(line.find('def ') > -1):
			return(True)
		else:
			return(False)
	
	def add_func_desc(self, func_name):
		s = '\t\t%s(): description' % func_name
		return(s)
	
	
	
	def get_func_args(self, line):
		funcname_idx1 = line.find('def ') + 4
		funcname_idx2 = line.find('(')
		func_name = line[funcname_idx1 : funcname_idx2]
		if(rg.search(line)):
			return(func_name, '\n\t\t:returns: None')
		self_idx = line.find('self,') + 5
		endp_idx = line.find('):')
		def_line = line[self_idx : endp_idx].replace(' ','')
		
		
		args = def_line.split(',')
		parm_str = ''
		for arg in args:
			parm_str += self.add_param_stub(arg)
		
		parm_str += '\n\t\t:returns: None'
		
		return(func_name, parm_str)
	
	def add_param_stub(self, arg):
		s = '\n\t\t:param %s: %s description\n' % (arg, arg) 
		s += '\t\t:type %s: %s type\n' % (arg, arg)
		return(s)
		
	def add_stub(self, s):
		s += """
		 <description here>
		
		:param wdgcom: <parm1 description>
		:type wdgcom: <parm1 type>

		:param do_recalc: selectively the STEPSIZE of the ROI's for X and Y can be recalculated if the number of points or range have changed
		:type do_recalc: flag.
	
		:returns: None
	  
		"""
		return(s)
		
		
	def load_file(self, fname):
		"""
		Convert a STXM .hdr file (fname) and return it as a json object, 
		"""
		if os.path.exists(fname):	
			inFile = open(fname, 'r')
			#turf the list and rebuild with new file contents	
			del self.fileLines[:]
			for l in inFile:
				self.fileLines.append(l)
			inFile.close()
			return self.fileLines
		else:
			pass
	
	def save_file(self, fname, lines):

		#write my translated lines out to imtermediate json file
		#for some reason the lines are full of new line chars 
		outFile = open(fname, 'w')
		for l in lines:
			print(l)
			outFile.write(l + '\n')
		outFile.close()
		

if __name__ == '__main__':
	app = QtWidgets.QApplication(sys.argv)

	window = Window()
	window.show()
	sys.exit(app.exec_())