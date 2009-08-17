# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'chatwindow.ui'
#
# Created: Tue Aug 11 15:07:30 2009
#      by: PyQt4 UI code generator 4.5.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_ChatWindow(object):
    def setupUi(self, ChatWindow):
        ChatWindow.setObjectName("ChatWindow")
        ChatWindow.resize(443, 371)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/pwytter"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        ChatWindow.setWindowIcon(icon)
        self.centralwidget = QtGui.QWidget(ChatWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.lblName = QtGui.QLabel(self.centralwidget)
        self.lblName.setGeometry(QtCore.QRect(40, 10, 271, 21))
        font = QtGui.QFont()
        font.setPointSize(15)
        font.setWeight(75)
        font.setBold(True)
        self.lblName.setFont(font)
        self.lblName.setObjectName("lblName")
        self.lblPic = QtGui.QLabel(self.centralwidget)
        self.lblPic.setGeometry(QtCore.QRect(350, 10, 54, 31))
        self.lblPic.setObjectName("lblPic")
        self.txtMsgSend = QtGui.QTextEdit(self.centralwidget)
        self.txtMsgSend.setGeometry(QtCore.QRect(30, 260, 391, 41))
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.txtMsgSend.sizePolicy().hasHeightForWidth())
        self.txtMsgSend.setSizePolicy(sizePolicy)
        self.txtMsgSend.setObjectName("txtMsgSend")
        self.ShowChat = QtGui.QTextEdit(self.centralwidget)
        self.ShowChat.setEnabled(True)
        self.ShowChat.setGeometry(QtCore.QRect(30, 50, 391, 191))
        self.ShowChat.setLineWrapMode(QtGui.QTextEdit.WidgetWidth)
        self.ShowChat.setReadOnly(True)
        self.ShowChat.setObjectName("ShowChat")
        ChatWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(ChatWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 443, 26))
        self.menubar.setObjectName("menubar")
        ChatWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(ChatWindow)
        self.statusbar.setObjectName("statusbar")
        ChatWindow.setStatusBar(self.statusbar)

        self.retranslateUi(ChatWindow)
        QtCore.QMetaObject.connectSlotsByName(ChatWindow)

    def retranslateUi(self, ChatWindow):
        ChatWindow.setWindowTitle(QtGui.QApplication.translate("ChatWindow", "MainWindow", None, QtGui.QApplication.UnicodeUTF8))

import ImIcon_rc
