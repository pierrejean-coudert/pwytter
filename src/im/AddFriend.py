# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'addfriend.ui'
#
# Created: Sun Aug  9 18:54:13 2009
#      by: PyQt4 UI code generator 4.5.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_AddDialog(object):
    def setupUi(self, AddDialog):
        AddDialog.setObjectName("AddDialog")
        AddDialog.setWindowModality(QtCore.Qt.NonModal)
        AddDialog.resize(493, 218)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/pwytter"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        AddDialog.setWindowIcon(icon)
        self.frame = QtGui.QFrame(AddDialog)
        self.frame.setGeometry(QtCore.QRect(20, 20, 451, 181))
        self.frame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtGui.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.btnAdd = QtGui.QPushButton(self.frame)
        self.btnAdd.setGeometry(QtCore.QRect(140, 120, 80, 28))
        font = QtGui.QFont()
        font.setPointSize(11)
        self.btnAdd.setFont(font)
        self.btnAdd.setObjectName("btnAdd")
        self.btnCancel = QtGui.QPushButton(self.frame)
        self.btnCancel.setGeometry(QtCore.QRect(260, 120, 80, 28))
        font = QtGui.QFont()
        font.setPointSize(11)
        self.btnCancel.setFont(font)
        self.btnCancel.setObjectName("btnCancel")
        self.lblAddFrnd = QtGui.QLabel(self.frame)
        self.lblAddFrnd.setGeometry(QtCore.QRect(20, 40, 171, 31))
        font = QtGui.QFont()
        font.setPointSize(11)
        font.setWeight(50)
        font.setBold(False)
        self.lblAddFrnd.setFont(font)
        self.lblAddFrnd.setObjectName("lblAddFrnd")
        self.txtAddFrnd = QtGui.QLineEdit(self.frame)
        self.txtAddFrnd.setGeometry(QtCore.QRect(220, 40, 211, 28))
        self.txtAddFrnd.setObjectName("txtAddFrnd")

        self.retranslateUi(AddDialog)
        QtCore.QMetaObject.connectSlotsByName(AddDialog)

    def retranslateUi(self, AddDialog):
        AddDialog.setWindowTitle(QtGui.QApplication.translate("AddDialog", "Add Friend", None, QtGui.QApplication.UnicodeUTF8))
        self.btnAdd.setText(QtGui.QApplication.translate("AddDialog", "Add", None, QtGui.QApplication.UnicodeUTF8))
        self.btnCancel.setText(QtGui.QApplication.translate("AddDialog", "Cancel", None, QtGui.QApplication.UnicodeUTF8))
        self.lblAddFrnd.setText(QtGui.QApplication.translate("AddDialog", "Enter Email Id of Friend", None, QtGui.QApplication.UnicodeUTF8))

import ImIcon_rc
