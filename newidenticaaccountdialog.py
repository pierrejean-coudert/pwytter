# -*- coding: utf-8 -*-

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from ui.ui_newidenticaaccountdialog import Ui_NewIdenticaAccountDialog

class NewIdenticaAccountDialog(QDialog, Ui_NewIdenticaAccountDialog):
    def __init__(self, parent = None):
        #Initialize dialog
        QDialog.__init__(self, parent)
        #Setup UI from QtDesigner
        self.setupUi(self)
