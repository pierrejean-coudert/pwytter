# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'newtwitteraccountdialog.ui'
#
# Created: Thu Jun 25 11:22:53 2009
#      by: PyQt4 UI code generator 4.4.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_NewTwitterAccountDialog(object):
    def setupUi(self, NewTwitterAccountDialog):
        NewTwitterAccountDialog.setObjectName("NewTwitterAccountDialog")
        NewTwitterAccountDialog.resize(352, 216)
        NewTwitterAccountDialog.setMinimumSize(QtCore.QSize(352, 208))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/icons/services/Twitter.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        NewTwitterAccountDialog.setWindowIcon(icon)
        NewTwitterAccountDialog.setModal(True)
        self.verticalLayout_2 = QtGui.QVBoxLayout(NewTwitterAccountDialog)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.label_3 = QtGui.QLabel(NewTwitterAccountDialog)
        self.label_3.setTextFormat(QtCore.Qt.PlainText)
        self.label_3.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.label_3.setWordWrap(True)
        self.label_3.setObjectName("label_3")
        self.verticalLayout_2.addWidget(self.label_3)
        self.groupBox = QtGui.QGroupBox(NewTwitterAccountDialog)
        self.groupBox.setObjectName("groupBox")
        self.verticalLayout = QtGui.QVBoxLayout(self.groupBox)
        self.verticalLayout.setObjectName("verticalLayout")
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.label = QtGui.QLabel(self.groupBox)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.UsernameEdit = QtGui.QLineEdit(self.groupBox)
        self.UsernameEdit.setObjectName("UsernameEdit")
        self.gridLayout.addWidget(self.UsernameEdit, 0, 1, 1, 1)
        self.label_2 = QtGui.QLabel(self.groupBox)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)
        self.PasswordEdit = QtGui.QLineEdit(self.groupBox)
        self.PasswordEdit.setEchoMode(QtGui.QLineEdit.Password)
        self.PasswordEdit.setObjectName("PasswordEdit")
        self.gridLayout.addWidget(self.PasswordEdit, 1, 1, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)
        spacerItem = QtGui.QSpacerItem(20, 6, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.verticalLayout_2.addWidget(self.groupBox)
        self.buttonBox = QtGui.QDialogButtonBox(NewTwitterAccountDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout_2.addWidget(self.buttonBox)

        self.retranslateUi(NewTwitterAccountDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), NewTwitterAccountDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), NewTwitterAccountDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(NewTwitterAccountDialog)

    def retranslateUi(self, NewTwitterAccountDialog):
        NewTwitterAccountDialog.setWindowTitle(QtGui.QApplication.translate("NewTwitterAccountDialog", "Connect to Twitter", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("NewTwitterAccountDialog", "Connect to an existing Twitter account. You will be able to synchronize and post updates using this account in pwytter.", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox.setTitle(QtGui.QApplication.translate("NewTwitterAccountDialog", "Twitter login", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("NewTwitterAccountDialog", "Username:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("NewTwitterAccountDialog", "Password", None, QtGui.QApplication.UnicodeUTF8))

import ressources_rc
