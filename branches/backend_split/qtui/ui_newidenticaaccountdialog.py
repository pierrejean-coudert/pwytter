# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'newidenticaaccountdialog.ui'
#
# Created: Sun Jul 19 12:40:50 2009
#      by: PyQt4 UI code generator 4.4.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_NewIdenticaAccountDialog(object):
    def setupUi(self, NewIdenticaAccountDialog):
        NewIdenticaAccountDialog.setObjectName("NewIdenticaAccountDialog")
        NewIdenticaAccountDialog.resize(352, 225)
        NewIdenticaAccountDialog.setMinimumSize(QtCore.QSize(296, 225))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/icons/services/Identi.ca.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        NewIdenticaAccountDialog.setWindowIcon(icon)
        NewIdenticaAccountDialog.setModal(True)
        self.verticalLayout_2 = QtGui.QVBoxLayout(NewIdenticaAccountDialog)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.label = QtGui.QLabel(NewIdenticaAccountDialog)
        self.label.setTextFormat(QtCore.Qt.PlainText)
        self.label.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.label.setWordWrap(True)
        self.label.setObjectName("label")
        self.verticalLayout_2.addWidget(self.label)
        self.groupBox = QtGui.QGroupBox(NewIdenticaAccountDialog)
        self.groupBox.setObjectName("groupBox")
        self.verticalLayout = QtGui.QVBoxLayout(self.groupBox)
        self.verticalLayout.setObjectName("verticalLayout")
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.label_2 = QtGui.QLabel(self.groupBox)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 0, 0, 1, 1)
        self.UsernameEdit = QtGui.QLineEdit(self.groupBox)
        self.UsernameEdit.setObjectName("UsernameEdit")
        self.gridLayout.addWidget(self.UsernameEdit, 0, 1, 1, 1)
        self.label_3 = QtGui.QLabel(self.groupBox)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 1, 0, 1, 1)
        self.PasswordEdit = QtGui.QLineEdit(self.groupBox)
        self.PasswordEdit.setEchoMode(QtGui.QLineEdit.Password)
        self.PasswordEdit.setObjectName("PasswordEdit")
        self.gridLayout.addWidget(self.PasswordEdit, 1, 1, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)
        spacerItem = QtGui.QSpacerItem(20, 15, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.verticalLayout_2.addWidget(self.groupBox)
        self.buttonBox = QtGui.QDialogButtonBox(NewIdenticaAccountDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout_2.addWidget(self.buttonBox)

        self.retranslateUi(NewIdenticaAccountDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), NewIdenticaAccountDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), NewIdenticaAccountDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(NewIdenticaAccountDialog)

    def retranslateUi(self, NewIdenticaAccountDialog):
        NewIdenticaAccountDialog.setWindowTitle(QtGui.QApplication.translate("NewIdenticaAccountDialog", "Connect to Identi.ca", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("NewIdenticaAccountDialog", "Connect to an existing Identi.ca. You will be able to synchronize and post updates using this account in pwytter.", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox.setTitle(QtGui.QApplication.translate("NewIdenticaAccountDialog", "Identi.ca login", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("NewIdenticaAccountDialog", "Username:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("NewIdenticaAccountDialog", "Password:", None, QtGui.QApplication.UnicodeUTF8))

import ressources_rc
