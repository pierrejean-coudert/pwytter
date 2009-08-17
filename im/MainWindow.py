# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'main.ui'
#
# Created: Tue Aug 11 17:02:32 2009
#      by: PyQt4 UI code generator 4.5.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_BuddyList(object):
    def setupUi(self, BuddyList):
        BuddyList.setObjectName("BuddyList")
        BuddyList.resize(297, 540)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/pwytter"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        BuddyList.setWindowIcon(icon)
        self.centralwidget = QtGui.QWidget(BuddyList)
        self.centralwidget.setObjectName("centralwidget")
        self.lstFrndList = QtGui.QListWidget(self.centralwidget)
        self.lstFrndList.setGeometry(QtCore.QRect(0, 50, 291, 391))
        self.lstFrndList.setMovement(QtGui.QListView.Free)
        self.lstFrndList.setObjectName("lstFrndList")
        self.cmdSetStatus = QtGui.QComboBox(self.centralwidget)
        self.cmdSetStatus.setGeometry(QtCore.QRect(10, 10, 161, 27))
        self.cmdSetStatus.setObjectName("cmdSetStatus")
        self.lblPhoto = QtGui.QLabel(self.centralwidget)
        self.lblPhoto.setGeometry(QtCore.QRect(220, 0, 71, 51))
        self.lblPhoto.setObjectName("lblPhoto")
        self.lEditStatusUpdate = QtGui.QTextEdit(self.centralwidget)
        self.lEditStatusUpdate.setGeometry(QtCore.QRect(10, 450, 271, 31))
        self.lEditStatusUpdate.setObjectName("lEditStatusUpdate")
        BuddyList.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(BuddyList)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 297, 26))
        self.menubar.setObjectName("menubar")
        self.menu_Buddies = QtGui.QMenu(self.menubar)
        self.menu_Buddies.setObjectName("menu_Buddies")
        self.menuAccounts = QtGui.QMenu(self.menubar)
        self.menuAccounts.setObjectName("menuAccounts")
        self.menu_Help = QtGui.QMenu(self.menubar)
        self.menu_Help.setObjectName("menu_Help")
        BuddyList.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(BuddyList)
        self.statusbar.setObjectName("statusbar")
        BuddyList.setStatusBar(self.statusbar)
        self.action_Add_Contact = QtGui.QAction(BuddyList)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/add"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.action_Add_Contact.setIcon(icon1)
        self.action_Add_Contact.setObjectName("action_Add_Contact")
        self.action_Change_Photo = QtGui.QAction(BuddyList)
        self.action_Change_Photo.setObjectName("action_Change_Photo")
        self.action_Quit = QtGui.QAction(BuddyList)
        self.action_Quit.setObjectName("action_Quit")
        self.actionTwitter = QtGui.QAction(BuddyList)
        self.actionTwitter.setObjectName("actionTwitter")
        self.actionIdentica = QtGui.QAction(BuddyList)
        self.actionIdentica.setObjectName("actionIdentica")
        self.menu_Buddies.addAction(self.action_Add_Contact)
        self.menu_Buddies.addAction(self.action_Quit)
        self.menuAccounts.addAction(self.actionTwitter)
        self.menuAccounts.addAction(self.actionIdentica)
        self.menubar.addAction(self.menu_Buddies.menuAction())
        self.menubar.addAction(self.menuAccounts.menuAction())
        self.menubar.addAction(self.menu_Help.menuAction())

        self.retranslateUi(BuddyList)
        QtCore.QMetaObject.connectSlotsByName(BuddyList)

    def retranslateUi(self, BuddyList):
        BuddyList.setWindowTitle(QtGui.QApplication.translate("BuddyList", "BuddyList", None, QtGui.QApplication.UnicodeUTF8))
        self.menu_Buddies.setTitle(QtGui.QApplication.translate("BuddyList", "&Buddies", None, QtGui.QApplication.UnicodeUTF8))
        self.menuAccounts.setTitle(QtGui.QApplication.translate("BuddyList", "Accounts", None, QtGui.QApplication.UnicodeUTF8))
        self.menu_Help.setTitle(QtGui.QApplication.translate("BuddyList", "&Help", None, QtGui.QApplication.UnicodeUTF8))
        self.action_Add_Contact.setText(QtGui.QApplication.translate("BuddyList", "&Add Contact", None, QtGui.QApplication.UnicodeUTF8))
        self.action_Change_Photo.setText(QtGui.QApplication.translate("BuddyList", "&Change Photo", None, QtGui.QApplication.UnicodeUTF8))
        self.action_Quit.setText(QtGui.QApplication.translate("BuddyList", "&Quit", None, QtGui.QApplication.UnicodeUTF8))
        self.actionTwitter.setText(QtGui.QApplication.translate("BuddyList", "Twitter", None, QtGui.QApplication.UnicodeUTF8))
        self.actionIdentica.setText(QtGui.QApplication.translate("BuddyList", "Identica", None, QtGui.QApplication.UnicodeUTF8))

import ImIcon_rc
