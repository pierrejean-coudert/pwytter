# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/passworddialog.ui'
#
# Created: Tue Dec 22 13:07:41 2009
#      by: PyQt4 UI code generator 4.6
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_PasswordDialog(object):
    def setupUi(self, PasswordDialog):
        PasswordDialog.setObjectName("PasswordDialog")
        PasswordDialog.resize(393, 151)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/icons/tango/32x32/apps/help-browser.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        PasswordDialog.setWindowIcon(icon)
        PasswordDialog.setModal(True)
        self.verticalLayout = QtGui.QVBoxLayout(PasswordDialog)
        self.verticalLayout.setSizeConstraint(QtGui.QLayout.SetFixedSize)
        self.verticalLayout.setObjectName("verticalLayout")
        self.ExplainationLabel = QtGui.QLabel(PasswordDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.ExplainationLabel.sizePolicy().hasHeightForWidth())
        self.ExplainationLabel.setSizePolicy(sizePolicy)
        self.ExplainationLabel.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.ExplainationLabel.setWordWrap(True)
        self.ExplainationLabel.setObjectName("ExplainationLabel")
        self.verticalLayout.addWidget(self.ExplainationLabel)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setSizeConstraint(QtGui.QLayout.SetDefaultConstraint)
        self.horizontalLayout.setContentsMargins(-1, -1, -1, 12)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label_2 = QtGui.QLabel(PasswordDialog)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout.addWidget(self.label_2)
        self.AccountPasswordEdit = QtGui.QLineEdit(PasswordDialog)
        self.AccountPasswordEdit.setEchoMode(QtGui.QLineEdit.Password)
        self.AccountPasswordEdit.setObjectName("AccountPasswordEdit")
        self.horizontalLayout.addWidget(self.AccountPasswordEdit)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.buttonBox = QtGui.QDialogButtonBox(PasswordDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(PasswordDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), PasswordDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), PasswordDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(PasswordDialog)

    def retranslateUi(self, PasswordDialog):
        PasswordDialog.setWindowTitle(QtGui.QApplication.translate("PasswordDialog", "Bad authendication", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("PasswordDialog", "Password:", None, QtGui.QApplication.UnicodeUTF8))

import ressources_rc
