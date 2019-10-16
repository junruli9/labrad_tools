import json
import time
import numpy as np
import os
import sys

from PyQt4 import QtGui, QtCore, Qt
from PyQt4.QtCore import pyqtSignal 
from twisted.internet.defer import inlineCallbacks

from gui_helpers import *

SEP = os.path.sep

class AnalogForm(QtGui.QWidget):
	def __init__(self, channels):
		super(AnalogForm, self).__init__()
		self.channels = channels
		self.populate()

	def populate(self):
		self.layout = QtGui.QVBoxLayout()
		self.boards = {}
		
		for board in sorted(self.channels.keys()):
			b = SequencerBoard(self.channels[board], 'analog')
			self.boards[board] = b
			self.layout.addWidget(b)

		self.setLayout(self.layout)

	def setValues(self, values):
		pass