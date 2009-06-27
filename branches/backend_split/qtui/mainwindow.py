# -*- coding: utf-8 -*-

import locale

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtNetwork import *
from ui_mainwindow import Ui_MainWindow
from functools import partial
from tweetstore import TweetStore, Message
from twitteraccount import TwitterAccount
from identicaaccount import IdenticaAccount
from Queue import Queue
from time import strftime, localtime, strptime
import event
from newtwitteraccountdialog import NewTwitterAccountDialog
from newidenticaaccountdialog import NewIdenticaAccountDialog

#switch back to old locale, this fixes local bug in time.strptime()
#see: http://www.mail-archive.com/python-bugs-list@python.org/msg11325.html
locale.setlocale(locale.LC_TIME, (None, None))

class EventSynchronizer(QObject):
	def __init__(self, parent):
		QObject.__init__(self, parent)
		self._EventQueue = Queue()
		parent.connect(self, SIGNAL("execute()"), self.executeEvent)
		
	def executeEvent(self):
		event, params = self._EventQueue.get()
		event.executeEvent(*params)
		
	def __call__(self, event, *params):
		self._EventQueue.put((event, params))
		self.emit(SIGNAL("execute()"))

class MainWindow(QMainWindow, Ui_MainWindow):
	def __init__(self, parent = None):
		#Initialize main window
		QMainWindow.__init__(self, parent)
		#Setup UI from QtDesigner, this also autoconnects signals to slots on self, marked with pyqtSignature decorator
		self.setupUi(self)
		
		#Setup event synchronization
		event.synchronizeEvent = EventSynchronizer(self)
		
		#TODO: Find a good place to save this, follow freedesktop specs on Linux, and whatever on Windows and OS X
		self._store = TweetStore("tweets.db")
		
		#Provide store for TweetView
		self.tweetView.setStore(self._store)
		
		self._statusIconLinks = {"unconfigured" :		QPixmap(":/icons/icons/tango/22x22/categories/preferences-system.png"), 
						"idle" :				QPixmap(":/icons/icons/tango/22x22/status/network-idle.png"),
						"offline" :				QPixmap(":/icons/icons/tango/22x22/status/network-offline.png"),
						"updating" :			QPixmap(":/icons/icons/tango/22x22/actions/view-refresh.png"),
						"bad authendication" :	QPixmap(":/icons/icons/tango/22x22/status/dialog-error.png")}
		
		#Add combobox to select view, cannot be done in QtDesigner
		self.ViewComboBox = QComboBox(self.ViewToolBar)
		self.ViewToolBar.addWidget(self.ViewComboBox)
		self.ViewComboBox.addItems(["Timeline", "Replies", "Direct messages", "Friends", "Followers"])	#TODO: Add icons for these
		self.connect(self.ViewComboBox, SIGNAL("currentIndexChanged(int)"), self.showMessages)
		self.ViewComboBox.setCurrentIndex(0)
		
		#Update account list
		self.updateAccountList()
		
		#Setup tray icon
		self.setupTrayIcon()
		
		#Subscribe to events by tweetstore
		self._store.onStatusChange += self.statusChanged
		self._store.onNewDirectMessages += self.newDirectMessages
		self._store.onNewTweets += self.newTweets
		self._store.onNewReplies += self.newReplies
		self._store.onNewFollowers += self.newFollowers
		
		#Setup splitter index 0 to not be collapsable, e.g. TweetView cannot be collapsed
		self.splitter.setCollapsible(0, False)

	@pyqtSignature("")
	def on_SynchronizeAccountsAction_triggered(self):
		#Get the account
		account = None
		actext = self.ViewAccountComboBox.currentText()
		for ac in self._store.getAccounts():
			if str(ac) == actext:
				account = ac
		#Sync the account, None for syncing all accounts
		self._store.sync(account)
		
	
	def showMessages(self, *whatever):
		"""Shows messages depending on comboboxes"""
		
		#Get the account
		account = "all"
		actext = self.ViewAccountComboBox.currentText()
		for ac in self._store.getAccounts():
			if str(ac) == actext:
				account = ac
		
		#Get the view
		view = str(self.ViewComboBox.currentText())
		self.tweetView.load(QUrl("pwytter://view/" + view.lower() + "/" + str(account) + "/0"))
		
	@pyqtSignature("")
	def on_postButton_clicked(self):
		""""Post message"""
		#Get account
		account = None
		actext = self.PostFromComboBox.currentText()
		for ac in self._store.getAccounts():
			if str(ac) == actext:
				account = ac
		#Get text
		text = unicode(self.MessageTextEdit.document().toPlainText())
		self.MessageTextEdit.document().clear()
				
		#post message
		if account:
			msg = Message(self._store, text, account.getUser())
			self._store.postMessage(msg)
		else:
			for account in self._store.getAccounts():
				msg = Message(self._store, text, account.getUser())
				self._store.postMessage(msg)
		
	@pyqtSignature("")
	def on_NewTwitterAccountAction_triggered(self):
		"""Launch dialog, ask for twitter username and password"""
		dlg = NewTwitterAccountDialog(self)
		#If dialog is accepted, create new twitter account
		if dlg.exec_() == QDialog.Accepted:
			TwitterAccount(str(dlg.UsernameEdit.text()), str(dlg.PasswordEdit.text()), self._store, self.accountLoginCallback)
	
	@pyqtSignature("")
	def on_NewIdenticaAccountAction_triggered(self):
		"""Launch dialog, ask for twitter username and password"""
		dlg = NewIdenticaAccountDialog(self)
		#If dialog is accepted, create new twitter account
		if dlg.exec_() == QDialog.Accepted:
			IdenticaAccount(str(dlg.UsernameEdit.text()), str(dlg.PasswordEdit.text()), self._store, self.accountLoginCallback)
	
	def accountLoginCallback(self, account, success, message):
		"""Handles callback from account creation, e.g. attempted login."""
		if success:
			self.updateAccountList()
			self.showMessages()
		else:
			QMessageBox.warning(self, "Failed to connect to " + account.getService(), message)
	
	def updateAccountList(self, *whatever):
		"""Update the widgets that uses a list of accounts"""
		#Clear both comboboxes and create if needed
		self.PostFromComboBox.clear()
		if hasattr(self, "ViewAccountComboBox"):
			self.ViewAccountComboBox.clear()
		else:
			self.ViewAccountComboBox = QComboBox(self.ViewToolBar)
			self.ViewToolBar.addWidget(self.ViewAccountComboBox)
			self.connect(self.ViewAccountComboBox, SIGNAL("currentIndexChanged(int)"), self.showMessages)
			
		#Clear the menu
		self.RemoveAccountMenu.clear()
		
		#Clear the statusbar
		if hasattr(self, "_statusbarLabels"):
			for label in self._statusbarLabels.values():
				self.statusbar.removeWidget(label)
		self._statusbarLabels = {}
		
		#Update comboboxes and menues
		self.PostFromComboBox.addItem("All")
		self.ViewAccountComboBox.addItem("All")
		for account in self._store.getAccounts():
			#TODO: Add icons for the accounts, extend tweetstore.Account to support this
			account_string = str(account)
			service_icon = QIcon(":/icons/icons/services/" + account.getService() + ".png")
			#Add account to comboboxes
			self.PostFromComboBox.addItem(service_icon, account_string)
			self.ViewAccountComboBox.addItem(service_icon, account_string)
			#Add account to removal menu
			action = QAction(service_icon, account_string, self.RemoveAccountMenu)
			self.RemoveAccountMenu.addAction(action)
			self.connect(action, SIGNAL("triggered()"), partial(self.removeAccount, account))
			#Add a statusbar label
			self._statusbarLabels[account] =  QLabel()
			self._statusbarLabels[account].setPixmap(self._statusIconLinks[account.getStatus()])
			self._statusbarLabels[account].setToolTip(str(account) + "\n" + account.getStatus())
			self.statusbar.addWidget(self._statusbarLabels[account])
	
	def removeAccount(self, account):
		"""Remove an account, triggered by remove account menu"""
		q = QMessageBox.question(self, 
								"Remove account",
								"Do you really want to remove the connection to " + str(account) + " ?",
								QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
		if q == QMessageBox.Yes:
			self._store.removeAccount(account)
			self.updateAccountList()
	
	def statusChanged(self, account, status):
		self._statusbarLabels[account].setPixmap(self._statusIconLinks[status])
		#self._statusbarLabels[account].setText("<img src=':/icons/icons/tango/22x22/" + self._statusIconLinks[status]+ ".png'>")
		self._statusbarLabels[account].setToolTip(str(account) + "\n" + status)
		#TODO: Attempt reauthendicate if status is "bad authendication"
		
	@pyqtSignature("")
	def on_HelpAction_triggered(self):
		print "TODO: Open help pages in a browser"
	
	@pyqtSignature("")
	def on_AboutAction_triggered(self):
		#TODO: Improve about box
		QMessageBox.about(self, "About Pwytter", "Pwytter is an open source\n microblog client for Windows, OS X and Linux.")
	
	@pyqtSignature("")
	def on_QuitAction_triggered(self):
		QCoreApplication.quit()

	def setupTrayIcon(self):
		"""Setup the tray icon"""
		self.TrayIcon = QSystemTrayIcon(QIcon(":/icons/icons/pwytter.png"), self)
		#TODO: Add menu to the tray icon
		self.connect(self.TrayIcon, SIGNAL("activated(QSystemTrayIcon::ActivationReason)"), self.ViewOrHide)
		self.TrayIcon.show()

	def ViewOrHide(self, reason):
		"""Handle clicks on the tray icon"""
		if reason == QSystemTrayIcon.Trigger:
			self.setVisible(not self.isVisible())

	@pyqtSignature("")
	def on_HideWindowAction_triggered(self):
		"""Hide window"""
		self.setVisible(False)

	def newDirectMessages(self, account, new_msgs):
		"""Handle new direct message event"""
		if len(new_msgs) == 1:
			self.TrayIcon.showMessage("New direct message", "You have a new direct message from " + new_msgs[0].getUser().getName() + " on " + account.getService() + ".")
		else:
			self.TrayIcon.showMessage("New direct messages", "You have " + str(len(new_msgs)) + " new direct messages on " + account.getService() + ".")
		
	def newTweets(self, account, new_msgs):
		"""Handle new tweets event"""
		if len(new_msgs) == 1:
			self.TrayIcon.showMessage("New tweet", "You have a new tweet in your timeline from " + new_msgs[0].getUser().getName() + " on " + account.getService() + ".")
		else:
			self.TrayIcon.showMessage("New tweets", "You have " + str(len(new_msgs)) + " new tweets in your timeline on " + account.getService() + ".")
		
	def newReplies(self, account, new_msgs):
		"""Handle new replies event"""
		if len(new_msgs) == 1:
			self.TrayIcon.showMessage("New reply", "You have a new reply from " + new_msgs[0].getUser().getName() + " on " + account.getService() + ".")
		else:
			self.TrayIcon.showMessage("New replies", "You have " + str(len(new_msgs)) + " new replies via " + account.getService() + ".")
		
	def newFollowers(self, account, new_followers):
		"""Handle new followers event"""
		if len(new_followers) == 1:
			self.TrayIcon.showMessage("New follower",  new_followers[0].getName() + " is now following you on " + account.getService() + ".")
		else:
			self.TrayIcon.showMessage("New followers", "You have " + str(len(new_followers)) + " new followers on " + account.getService() + ".")
