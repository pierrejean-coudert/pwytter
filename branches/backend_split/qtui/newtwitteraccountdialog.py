# -*- coding: utf-8 -*-

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from ui_newtwitteraccountdialog import Ui_NewTwitterAccountDialog

class NewTwitterAccountDialog(QDialog, Ui_NewTwitterAccountDialog):
	def __init__(self, parent = None):
		#Initialize dialog
		QDialog.__init__(self, parent)
		#Setup UI from QtDesigner
		self.setupUi(self)
