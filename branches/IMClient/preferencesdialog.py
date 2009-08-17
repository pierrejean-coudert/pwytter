# -*- coding: utf-8 -*-

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from ui.ui_preferencesdialog import Ui_PreferencesDialog
from tweetstore import TweetStore
from theme import getThemes
import webbrowser

class PreferencesDialog(QDialog, Ui_PreferencesDialog):
    def __init__(self, store, parent = None):
        assert isinstance(store, TweetStore), "store must be an instance of TweetStore"
        self.__store = store
        #Initialize dialog
        QDialog.__init__(self, parent)
        #Setup UI from QtDesigner
        self.setupUi(self)
        #Load settings
        self.loadSettings()
        #Add delete shortcuts for black/whitelist tags
        self.s1 = QShortcut(QKeySequence.Delete, self.BlacklistTagListWidget, self.deleteSelectedBlacklistString).setContext(Qt.WidgetShortcut)
        self.s1 = QShortcut(QKeySequence.Delete, self.WhitelistTagListWidget, self.deleteSelectedWhitelistString).setContext(Qt.WidgetShortcut)

    def loadSettings(self):
        """Loads settings from store.settings to the widgets.
        
            This method may be used to reset the content in the form, if a reset button should be desired.
        """
        #Load general settings
        self.SynchronizationIntervalSpinBox.setValue(self.__store.settings.get("MainWindow/SynchronizationInterval", 180))
        self.TweetsPerPageSpinBox.setValue(self.__store.settings.get("MainWindow/TweetsPerPage", 10))
        self.UsersPerPageSpinBox.setValue(self.__store.settings.get("MainWindow/UsersPerPage", 15))
        self.ShowMainWindowOnStartupCheckBox.setChecked(self.__store.settings.get("MainWindow/ShowMainWindowOnStartUp", True))
        #Load user black/whitelist
        for user in self.__store.getCachedUsers():
            if self.__store.notification.isBlacklisted(user):
                QListWidgetItem(str(user), self.BlacklistUserListWidget, QListWidgetItem.Type).setData(Qt.UserRole, QVariant(user))
            else:
                QListWidgetItem(str(user), self.WhitelistedUserListWidget, QListWidgetItem.Type).setData(Qt.UserRole, QVariant(user))
        #Load notification checkboxes
        self.NotifyOnNewTweetCheckBox.setChecked(self.__store.notification.notifyOnNewTweets)
        self.NotifyOnNewReplyCheckBox.setChecked(self.__store.notification.notifyOnNewReplies)
        self.NotifyOnNewDirectMessageCheckBox.setChecked(self.__store.notification.notifyOnNewDirectMessages)
        self.NotifyOnNewFollowerCheckBox.setChecked(self.__store.notification.notifyOnNewFollowers)
        self.NotifyOnNewFriendCheckBox.setChecked(self.__store.notification.notifyOnNewFriends)
        self.NotifyOnSyncCompletedCheckBox.setChecked(self.__store.notification.notifyOnSynchronized)
        #Load blacklist tags
        for tag in self.__store.notification.blacklistStrings:
            self.BlacklistTagListWidget.addItem(tag)
        #Load whitelist tags
        for tag in self.__store.notification.whitelistStrings:
            self.WhitelistTagListWidget.addItem(tag)
        #Load theme settings
        currentTheme = self.__store.settings.get("MainWindow/Theme", "default")
        themeItem = None
        for theme in getThemes():
            item = QListWidgetItem(str(theme), self.ThemeListWidget, QListWidgetItem.Type)
            item.setData(Qt.UserRole, QVariant(theme))
            if theme.getName() == currentTheme:
                themeItem = item
        if themeItem:
            self.ThemeListWidget.setCurrentItem(themeItem)

    @pyqtSignature("")
    def on_buttonBox_accepted(self):
        """Handle accept button click, saves settings."""
        #Save general settings
        self.__store.settings["MainWindow/SynchronizationInterval"] = self.SynchronizationIntervalSpinBox.value()
        self.__store.settings["MainWindow/TweetsPerPage"] = self.TweetsPerPageSpinBox.value()
        self.__store.settings["MainWindow/UsersPerPage"] = self.UsersPerPageSpinBox.value()
        self.__store.settings["MainWindow/ShowMainWindowOnStartUp"] = self.ShowMainWindowOnStartupCheckBox.isChecked()
        #Save user blacklist
        for row in range(0, self.BlacklistUserListWidget.count()):
            user = self.BlacklistUserListWidget.item(row).data(Qt.UserRole).toPyObject()
            self.__store.notification.blacklist(user)
        #Save user whitelist
        for row in range(0, self.WhitelistedUserListWidget.count()):
            user = self.WhitelistedUserListWidget.item(row).data(Qt.UserRole).toPyObject()
            self.__store.notification.whitelist(user)
        #Save notification checkboxes
        self.__store.notification.notifyOnNewTweets         = self.NotifyOnNewTweetCheckBox.isChecked()
        self.__store.notification.notifyOnNewReplies        = self.NotifyOnNewReplyCheckBox.isChecked()
        self.__store.notification.notifyOnNewDirectMessages = self.NotifyOnNewDirectMessageCheckBox.isChecked()
        self.__store.notification.notifyOnNewFollowers      = self.NotifyOnNewFollowerCheckBox.isChecked()
        self.__store.notification.notifyOnNewFriends        = self.NotifyOnNewFriendCheckBox.isChecked()
        self.__store.notification.notifyOnSynchronized      = self.NotifyOnSyncCompletedCheckBox.isChecked()
        #Save tag blacklist
        self.__store.notification.blacklistStrings = ()
        for row in range(0, self.BlacklistTagListWidget.count()):
            tag = unicode(self.BlacklistTagListWidget.item(row).text())
            self.__store.notification.blacklistStrings += (tag,)
        #Save tag whitelist
        self.__store.notification.whitelistStrings = ()
        for row in range(0, self.WhitelistTagListWidget.count()):
            tag = unicode(self.WhitelistTagListWidget.item(row).text())
            self.__store.notification.whitelistStrings += (tag,)
        #Save theme selection
        self.__store.settings["MainWindow/Theme"] = self.ThemeListWidget.currentItem().data(Qt.UserRole).toPyObject().getName()
        #Return the dialog
        self.accept()
    
    @pyqtSignature("")
    def on_buttonBox_rejected(self):
        """Handle reject button click, discards changes."""
        pass #Nothing to do so far...
        #Return the form
        self.reject()

    @pyqtSignature("")
    def on_WhiteListUserToolButton_clicked(self):
        """Move selected item in blacklisted user to whitelisted users"""
        #Take the item from blacklisted users
        item = self.BlacklistUserListWidget.takeItem(self.BlacklistUserListWidget.currentRow())
        #Add it to whitelisted users
        self.WhitelistedUserListWidget.addItem(item)
    
    @pyqtSignature("")
    def on_BlackListUserToolButton_clicked(self):
        """Move selected item in whitelisted user to blacklisted users"""
        #Take the item from whitelisted users
        item = self.WhitelistedUserListWidget.takeItem(self.WhitelistedUserListWidget.currentRow())
        #Add it to blacklisted users
        self.BlacklistUserListWidget.addItem(item)

    def deleteSelectedBlacklistString(self):
        """Remove selected blacklist string"""
        item = self.BlacklistTagListWidget.takeItem(self.BlacklistTagListWidget.currentRow())
        del item
    
    def deleteSelectedWhitelistString(self):
        """Remove selected whitelist string"""
        item = self.WhitelistTagListWidget.takeItem(self.WhitelistTagListWidget.currentRow())
        del item
    
    @pyqtSignature("")
    def on_AddBlackListTagButton_clicked(self):
        """Add new item to blacklist tag"""
        text = self.BlacklistTagLineEdit.text()
        self.BlacklistTagListWidget.addItem(text)
        self.BlacklistTagLineEdit.clear()
    
    @pyqtSignature("")
    def on_AddWhiteListTagButton_clicked(self):
        """Add new item to whitelist tag"""
        text = self.WhitelistTagLineEdit.text()
        self.WhitelistTagListWidget.addItem(text)
        self.WhitelistTagLineEdit.clear()

    @pyqtSignature("")
    def on_ThemeListWidget_itemSelectionChanged(self):
        #TODO: Make this work...
        theme = self.ThemeListWidget.currentItem().data(Qt.UserRole).toPyObject()
        #Display description
        #TODO: Insert author etc.
        self.ThemeDescriptionTextBrowser.setHtml("<h3>" + theme.getTitle() + "</h3>" + theme.getDescription())
        #Display preview
        pix = QPixmap()
        pix.loadFromData(theme.getPreview())
        self.PreviewLabel.setPixmap(pix)

    @pyqtSignature("QUrl")
    def on_ThemeDescriptionTextBrowser_anchorClicked(self, url):
        #Open all links in external browser, regardless of what it is
        webbrowser.open(url.toString(), 1)
