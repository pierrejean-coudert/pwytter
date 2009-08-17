# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Mapping.ui'
#
# Created: Wed Aug 12 10:53:01 2009
#      by: PyQt4 UI code generator 4.5.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_Map(object):
    def setupUi(self, Map):
        Map.setObjectName("Map")
        Map.resize(504, 304)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/pwytter"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        Map.setWindowIcon(icon)
        self.frame = QtGui.QFrame(Map)
        self.frame.setGeometry(QtCore.QRect(20, 20, 461, 261))
        self.frame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtGui.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.lblGList = QtGui.QLabel(self.frame)
        self.lblGList.setGeometry(QtCore.QRect(40, 10, 101, 31))
        self.lblGList.setObjectName("lblGList")
        self.lstGmail = QtGui.QListWidget(self.frame)
        self.lstGmail.setGeometry(QtCore.QRect(20, 40, 161, 192))
        self.lstGmail.setObjectName("lstGmail")
        self.lblTList = QtGui.QLabel(self.frame)
        self.lblTList.setGeometry(QtCore.QRect(300, 20, 121, 18))
        self.lblTList.setObjectName("lblTList")
        self.lstTwitter = QtGui.QListWidget(self.frame)
        self.lstTwitter.setGeometry(QtCore.QRect(280, 40, 161, 192))
        self.lstTwitter.setObjectName("lstTwitter")
        self.buttonMap = QtGui.QPushButton(self.frame)
        self.buttonMap.setGeometry(QtCore.QRect(190, 80, 80, 28))
        self.buttonMap.setObjectName("buttonMap")
        self.buttoncancel = QtGui.QPushButton(self.frame)
        self.buttoncancel.setGeometry(QtCore.QRect(190, 130, 80, 28))
        self.buttoncancel.setObjectName("buttoncancel")

        self.retranslateUi(Map)
        QtCore.QMetaObject.connectSlotsByName(Map)

    def retranslateUi(self, Map):
        Map.setWindowTitle(QtGui.QApplication.translate("Map", "Map Accounts", None, QtGui.QApplication.UnicodeUTF8))
        self.lblGList.setText(QtGui.QApplication.translate("Map", "Gmail Friend List :", None, QtGui.QApplication.UnicodeUTF8))
        self.lblTList.setText(QtGui.QApplication.translate("Map", "Twitter Friends List :", None, QtGui.QApplication.UnicodeUTF8))
        self.buttonMap.setText(QtGui.QApplication.translate("Map", "Map", None, QtGui.QApplication.UnicodeUTF8))
        self.buttoncancel.setText(QtGui.QApplication.translate("Map", "Cancel", None, QtGui.QApplication.UnicodeUTF8))

import ImIcon_rc
