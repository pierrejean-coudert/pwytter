# -*- coding: utf-8 -*-

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from ui.ui_passworddialog import Ui_PasswordDialog

class PasswordDialog(QDialog, Ui_PasswordDialog):
    def __init__(self, parent = None):
        #Initialize dialog
        QDialog.__init__(self, parent)
        #Setup UI from QtDesigner
        self.setupUi(self)
