# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/mainwindow.ui'
#
# Created: Sat Aug  8 14:03:11 2009
#      by: PyQt4 UI code generator 4.4.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(367, 823)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/icons/pwytter.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        MainWindow.setWindowIcon(icon)
        self.centralwidget = QtGui.QWidget(MainWindow)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(sizePolicy)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout_3 = QtGui.QHBoxLayout(self.centralwidget)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.splitter = QtGui.QSplitter(self.centralwidget)
        self.splitter.setOrientation(QtCore.Qt.Vertical)
        self.splitter.setObjectName("splitter")
        self.tweetView = TweetView(self.splitter)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.tweetView.sizePolicy().hasHeightForWidth())
        self.tweetView.setSizePolicy(sizePolicy)
        self.tweetView.setObjectName("tweetView")
        self.layoutWidget = QtGui.QWidget(self.splitter)
        self.layoutWidget.setObjectName("layoutWidget")
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.layoutWidget)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.replyLabel = QtGui.QLabel(self.layoutWidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.replyLabel.sizePolicy().hasHeightForWidth())
        self.replyLabel.setSizePolicy(sizePolicy)
        self.replyLabel.setScaledContents(False)
        self.replyLabel.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.replyLabel.setWordWrap(True)
        self.replyLabel.setObjectName("replyLabel")
        self.horizontalLayout_2.addWidget(self.replyLabel)
        self.clearReplyButton = QtGui.QToolButton(self.layoutWidget)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/icons/icons/tango/22x22/actions/edit-clear.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.clearReplyButton.setIcon(icon1)
        self.clearReplyButton.setPopupMode(QtGui.QToolButton.DelayedPopup)
        self.clearReplyButton.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        self.clearReplyButton.setAutoRaise(True)
        self.clearReplyButton.setObjectName("clearReplyButton")
        self.horizontalLayout_2.addWidget(self.clearReplyButton)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.MessageTextEdit = QtGui.QPlainTextEdit(self.layoutWidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.MessageTextEdit.sizePolicy().hasHeightForWidth())
        self.MessageTextEdit.setSizePolicy(sizePolicy)
        self.MessageTextEdit.setObjectName("MessageTextEdit")
        self.horizontalLayout.addWidget(self.MessageTextEdit)
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.postButton = QtGui.QPushButton(self.layoutWidget)
        self.postButton.setObjectName("postButton")
        self.verticalLayout.addWidget(self.postButton)
        self.PostFromComboBox = QtGui.QComboBox(self.layoutWidget)
        self.PostFromComboBox.setObjectName("PostFromComboBox")
        self.verticalLayout.addWidget(self.PostFromComboBox)
        self.counterLabel = QtGui.QLabel(self.layoutWidget)
        self.counterLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.counterLabel.setObjectName("counterLabel")
        self.verticalLayout.addWidget(self.counterLabel)
        spacerItem = QtGui.QSpacerItem(1, 1, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.horizontalLayout.addLayout(self.verticalLayout)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.horizontalLayout_3.addWidget(self.splitter)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 367, 26))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtGui.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuView = QtGui.QMenu(self.menubar)
        self.menuView.setObjectName("menuView")
        self.menuAccounts = QtGui.QMenu(self.menubar)
        self.menuAccounts.setObjectName("menuAccounts")
        self.menuConnect_to = QtGui.QMenu(self.menuAccounts)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/icons/icons/tango/32x32/actions/list-add.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.menuConnect_to.setIcon(icon2)
        self.menuConnect_to.setObjectName("menuConnect_to")
        self.RemoveAccountMenu = QtGui.QMenu(self.menuAccounts)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(":/icons/icons/tango/32x32/actions/list-remove.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.RemoveAccountMenu.setIcon(icon3)
        self.RemoveAccountMenu.setObjectName("RemoveAccountMenu")
        self.menu_Help = QtGui.QMenu(self.menubar)
        self.menu_Help.setObjectName("menu_Help")
        self.menu_Edit = QtGui.QMenu(self.menubar)
        self.menu_Edit.setObjectName("menu_Edit")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.ViewToolBar = QtGui.QToolBar(MainWindow)
        self.ViewToolBar.setMovable(False)
        self.ViewToolBar.setAllowedAreas(QtCore.Qt.NoToolBarArea)
        self.ViewToolBar.setFloatable(False)
        self.ViewToolBar.setObjectName("ViewToolBar")
        MainWindow.addToolBar(QtCore.Qt.TopToolBarArea, self.ViewToolBar)
        self.NewTwitterAccountAction = QtGui.QAction(MainWindow)
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap(":/icons/icons/services/Twitter.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.NewTwitterAccountAction.setIcon(icon4)
        self.NewTwitterAccountAction.setObjectName("NewTwitterAccountAction")
        self.QuitAction = QtGui.QAction(MainWindow)
        icon5 = QtGui.QIcon()
        icon5.addPixmap(QtGui.QPixmap(":/icons/icons/tango/32x32/actions/system-log-out.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.QuitAction.setIcon(icon5)
        self.QuitAction.setObjectName("QuitAction")
        self.AboutAction = QtGui.QAction(MainWindow)
        self.AboutAction.setObjectName("AboutAction")
        self.HelpAction = QtGui.QAction(MainWindow)
        icon6 = QtGui.QIcon()
        icon6.addPixmap(QtGui.QPixmap(":/icons/icons/tango/32x32/apps/help-browser.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.HelpAction.setIcon(icon6)
        self.HelpAction.setObjectName("HelpAction")
        self.SynchronizeAccountsAction = QtGui.QAction(MainWindow)
        icon7 = QtGui.QIcon()
        icon7.addPixmap(QtGui.QPixmap(":/icons/icons/tango/32x32/actions/view-refresh.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.SynchronizeAccountsAction.setIcon(icon7)
        self.SynchronizeAccountsAction.setObjectName("SynchronizeAccountsAction")
        self.NewIdenticaAccountAction = QtGui.QAction(MainWindow)
        icon8 = QtGui.QIcon()
        icon8.addPixmap(QtGui.QPixmap(":/icons/icons/services/Identi.ca.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.NewIdenticaAccountAction.setIcon(icon8)
        self.NewIdenticaAccountAction.setObjectName("NewIdenticaAccountAction")
        self.HideWindowAction = QtGui.QAction(MainWindow)
        self.HideWindowAction.setObjectName("HideWindowAction")
        self.CollapseMessageEditAction = QtGui.QAction(MainWindow)
        self.CollapseMessageEditAction.setCheckable(True)
        icon9 = QtGui.QIcon()
        icon9.addPixmap(QtGui.QPixmap(":/icons/icons/tango/22x22/apps/preferences-desktop-keyboard-shortcuts.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.CollapseMessageEditAction.setIcon(icon9)
        self.CollapseMessageEditAction.setObjectName("CollapseMessageEditAction")
        self.PreferencesAction = QtGui.QAction(MainWindow)
        icon10 = QtGui.QIcon()
        icon10.addPixmap(QtGui.QPixmap(":/icons/icons/tango/22x22/categories/preferences-system.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.PreferencesAction.setIcon(icon10)
        self.PreferencesAction.setObjectName("PreferencesAction")
        self.menuFile.addAction(self.QuitAction)
        self.menuView.addAction(self.HideWindowAction)
        self.menuConnect_to.addAction(self.NewTwitterAccountAction)
        self.menuConnect_to.addAction(self.NewIdenticaAccountAction)
        self.menuAccounts.addAction(self.SynchronizeAccountsAction)
        self.menuAccounts.addSeparator()
        self.menuAccounts.addAction(self.menuConnect_to.menuAction())
        self.menuAccounts.addAction(self.RemoveAccountMenu.menuAction())
        self.menu_Help.addAction(self.HelpAction)
        self.menu_Help.addSeparator()
        self.menu_Help.addAction(self.AboutAction)
        self.menu_Edit.addAction(self.PreferencesAction)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menu_Edit.menuAction())
        self.menubar.addAction(self.menuView.menuAction())
        self.menubar.addAction(self.menuAccounts.menuAction())
        self.menubar.addAction(self.menu_Help.menuAction())
        self.ViewToolBar.addAction(self.SynchronizeAccountsAction)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtGui.QApplication.translate("MainWindow", "Pwytter", None, QtGui.QApplication.UnicodeUTF8))
        self.replyLabel.setText(QtGui.QApplication.translate("MainWindow", "<b>Reply to</b>", None, QtGui.QApplication.UnicodeUTF8))
        self.clearReplyButton.setToolTip(QtGui.QApplication.translate("MainWindow", "Clear reply/direct message settings for this message.", None, QtGui.QApplication.UnicodeUTF8))
        self.clearReplyButton.setText(QtGui.QApplication.translate("MainWindow", "...", None, QtGui.QApplication.UnicodeUTF8))
        self.postButton.setText(QtGui.QApplication.translate("MainWindow", "Update", None, QtGui.QApplication.UnicodeUTF8))
        self.PostFromComboBox.setToolTip(QtGui.QApplication.translate("MainWindow", "Account to post status update to.", None, QtGui.QApplication.UnicodeUTF8))
        self.menuFile.setTitle(QtGui.QApplication.translate("MainWindow", "&File", None, QtGui.QApplication.UnicodeUTF8))
        self.menuView.setTitle(QtGui.QApplication.translate("MainWindow", "&View", None, QtGui.QApplication.UnicodeUTF8))
        self.menuAccounts.setTitle(QtGui.QApplication.translate("MainWindow", "&Accounts", None, QtGui.QApplication.UnicodeUTF8))
        self.menuConnect_to.setTitle(QtGui.QApplication.translate("MainWindow", "Add account", None, QtGui.QApplication.UnicodeUTF8))
        self.RemoveAccountMenu.setTitle(QtGui.QApplication.translate("MainWindow", "Remove account", None, QtGui.QApplication.UnicodeUTF8))
        self.menu_Help.setTitle(QtGui.QApplication.translate("MainWindow", "&Help", None, QtGui.QApplication.UnicodeUTF8))
        self.menu_Edit.setTitle(QtGui.QApplication.translate("MainWindow", "&Edit", None, QtGui.QApplication.UnicodeUTF8))
        self.ViewToolBar.setWindowTitle(QtGui.QApplication.translate("MainWindow", "Content toolbar", None, QtGui.QApplication.UnicodeUTF8))
        self.NewTwitterAccountAction.setText(QtGui.QApplication.translate("MainWindow", "&Twitter account", None, QtGui.QApplication.UnicodeUTF8))
        self.QuitAction.setText(QtGui.QApplication.translate("MainWindow", "&Quit", None, QtGui.QApplication.UnicodeUTF8))
        self.AboutAction.setText(QtGui.QApplication.translate("MainWindow", "&About", None, QtGui.QApplication.UnicodeUTF8))
        self.HelpAction.setText(QtGui.QApplication.translate("MainWindow", "&Help", None, QtGui.QApplication.UnicodeUTF8))
        self.SynchronizeAccountsAction.setText(QtGui.QApplication.translate("MainWindow", "&Synchronize accounts", None, QtGui.QApplication.UnicodeUTF8))
        self.NewIdenticaAccountAction.setText(QtGui.QApplication.translate("MainWindow", "&Identi.ca account", None, QtGui.QApplication.UnicodeUTF8))
        self.HideWindowAction.setText(QtGui.QApplication.translate("MainWindow", "&Hide window", None, QtGui.QApplication.UnicodeUTF8))
        self.CollapseMessageEditAction.setText(QtGui.QApplication.translate("MainWindow", "Toggle new message field.", None, QtGui.QApplication.UnicodeUTF8))
        self.PreferencesAction.setText(QtGui.QApplication.translate("MainWindow", "&Preferences", None, QtGui.QApplication.UnicodeUTF8))

from tweetview import TweetView
import ressources_rc