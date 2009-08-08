# -*- coding: utf-8 -*-

import locale
from functools import partial
from Queue import Queue
from time import strftime, localtime, strptime
import os

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtNetwork import *

from ui.ui_mainwindow import Ui_MainWindow
from tweetstore import TweetStore, Message, User
from tweetstore.twitter import TwitterAccount
from tweetstore.identica import IdenticaAccount
from tweetstore import event

from newtwitteraccountdialog import NewTwitterAccountDialog
from newidenticaaccountdialog import NewIdenticaAccountDialog
from preferencesdialog import PreferencesDialog
from theme import Theme

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
        
        #Find place to save user settings, e.g. the database
        #Comply with XDG Base Directory Specification v0.6
        configdir = os.environ.get("XDG_CONFIG_HOME")
        if not configdir:
            configdir = os.path.join(os.path.expanduser("~"), ".config")
        if not os.path.isdir(configdir):
            os.makedirs(configdir)
        self._store = TweetStore(os.path.join(configdir, "pwytter.db"))
        
        #Connect aboutToQuit to save settings
        self.connect(QCoreApplication.instance(), SIGNAL("aboutToQuit()"), self.saveSettings)
        
        #Hide mainwindow if settings dictates that it should be hidden at startup
        if not self._store.settings.get("MainWindow/ShowMainWindowOnStartUp", True):
            self.on_HideWindowAction_triggered()
        
        #Provide store for TweetView
        self.tweetView.setStore(self._store)
        
        #Save default style
        self.__defaultStyle = QApplication.style().objectName()
        #Load settings
        self.loadSettings()
        
        self._statusIconLinks = {"unconfigured":QPixmap(":/icons/icons/tango/22x22/categories/preferences-system.png"), 
                        "idle":                 QPixmap(":/icons/icons/tango/22x22/status/network-idle.png"),
                        "offline":              QPixmap(":/icons/icons/tango/22x22/status/network-offline.png"),
                        "updating":             QPixmap(":/icons/icons/tango/22x22/actions/view-refresh.png"),
                        "bad authendication":   QPixmap(":/icons/icons/tango/22x22/status/dialog-error.png")}
        
        #Add combobox to select view, cannot be done in QtDesigner
        self.ViewComboBox = QComboBox(self.ViewToolBar)
        self.ViewComboBox.setObjectName("ViewComboBox")
        self.ViewToolBar.addWidget(self.ViewComboBox)
        self.ViewComboBox.addItems(["Timeline", "Replies", "Direct messages", "Outbox", "Friends", "Followers"])    #TODO: Add icons for these
        self.ViewComboBox.setCurrentIndex(0)
        self.connect(self.ViewComboBox, SIGNAL("currentIndexChanged(int)"), self.showMessages)
        
        #Add ToolButton for toggling MessageEdit collapsation
        collapseToolbutton = QToolButton(self)
        collapseToolbutton.setDefaultAction(self.CollapseMessageEditAction)
        self.statusbar.addWidget(collapseToolbutton)
        #Add statusbar label, to display messages and fill the void.
        self.statusbarMessageLabel = QLabel("", self)
        self.statusbar.addWidget(self.statusbarMessageLabel, 1)
        
        #Update account list
        self.updateAccountList()
        
        #Setup tray icon
        self.setupTrayIcon()
        
        #Subscribe to events by tweetstore
        self._store.onStatusChange += self.statusChanged
        self._store.notification.onNotification += self.displayNotification
        
        #Setup splitter index 0 to not be collapsable, e.g. TweetView cannot be collapsed
        self.splitter.setCollapsible(0, False)
        #Collapse message edit
        self.on_CollapseMessageEditAction_triggered()
        
        #Hide the writing reply to... label initially
        self.replyLabel.hide()
        self.clearReplyButton.hide()

    def loadSettings(self):
        """Loads settings, to be invoked during initialization and when settings have been altered."""
        #Load settings for TweetView
        self.tweetView.setTweetPageSize(self._store.settings.get("MainWindow/TweetsPerPage", 10))
        self.tweetView.setUserPageSize(self._store.settings.get("MainWindow/UsersPerPage", 15))
        try: #Load theme from settings
            self.theme = Theme(self._store.settings["MainWindow/Theme"])
        except: #If cannot load from settings load default theme
            self.theme = Theme()
        #Set the theme on TweetView
        self.tweetView.setTheme(self.theme)
        #Set QStyle
        styleSet = False
        print self.theme.getQStyles()
        for identifier in self.theme.getQStyles():
            if QApplication.setStyle(identifier):
                styleSet = True
                break
        if not styleSet:
            #Note: This we find default style using objectName(), this is undocumented and may not work in the future.
            assert QApplication.setStyle(self.__defaultStyle) != None, "Couldn't set default QStyle."
        #Load Qt stylesheet
        QCoreApplication.instance().setStyleSheet(self.theme.getQtStylesheet())
        #TODO: Load settings for synchronizations timer, interval is self._store.settings.get("MainWindow/SynchronizationInterval", 180)
        #TODO: Load form size, position etc. if we want to... 

    def saveSettings(self):
        """Save various settings, before closing"""
        self._store.save()
        #TODO: Save form size, position etc. if we want to... 

    def closeEvent(self, event):
        """Hide mainWindow when it's suppose to close
            e.g. <alt> + F4 or if user clicks on the close button.
        """
        self.on_HideWindowAction_triggered()
        event.ignore()

    @pyqtSignature("")
    def on_CollapseMessageEditAction_triggered(self):
        """Change collapsation of MessageEdit"""
        min, max = self.splitter.getRange(1)
        if self.splitter.widget(1).size().height() == 0:
            height = self.splitter.widget(1).sizeHint().height()
            self.splitter.moveSplitter(max - height, 1)
        else:
            self.splitter.moveSplitter(max, 1)

    def displayMessageEditPane(self):
        """Ensure that MessageEdit is not collapsed"""
        min, max = self.splitter.getRange(1)
        if self.splitter.widget(1).size().height() == 0:
            height = self.splitter.widget(1).sizeHint().height()
            self.splitter.moveSplitter(max - height, 1)

    @pyqtSignature("int, int")
    def on_splitter_splitterMoved(self, x, y):
        """Update the checked state of the CollapseMessageEditAction"""
        min, max = self.splitter.getRange(1)
        self.CollapseMessageEditAction.setChecked(x != max)

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

    def getClosetsRelatedAccount(self, user, accounts = None):
        """Gets the account that is closet related to a user from the list of accounts.
        
            user:       User to whom a related account is wanted
            accounts:   List of accounts to select amongs, None for all accounts from TweetStore
        
            If multiple accounts for the service exists, an account that is friend of the user is
            preferred, if there's multiple if these an account that the user is a follower of is preferred.
            If there's more than one of these, the first of the account return from TweetStore is returned.
        """
        assert isinstance(user, User), "user must be an instance of User"
        if accounts:
            candidates = ()
            for account in accounts:
                if account.getService() == user.getService():
                    candidates += (account,)
        else:
            candidates = self._store.getAccounts(user.getService())
        #If we can't find an account return None
        if len(candidates) == 0:
            raise Exception, "No related account was found"
        if len(candidates) == 1:
            return candidates[0]
        #Find accounts that are friends of the user
        befriended_accounts = ()
        for candidate in candidates:
            if self._store.isFriend(user, candidate):
                befriended_accounts += (candidate,)
        #If there's only one let's use that one
        if len(befriended_accounts) == 1:
            return befriended_accounts[0]
        #If there's more than one, use them as candidates
        if len(befriended_accounts) != 0:
            candidates = befriended_accounts
        #Find accounts that the given user followers
        followed_accounts = ()
        for candidate in candidates:
            if self._store.isFollower(user, candidate):
                followed_accounts += (candidate,)
        #If there's any followed accounts return the first of them
        if len(followed_accounts) > 0:
            return followed_accounts[0]
        #Otherwise return the first candidate
        return candidates[0]

    @pyqtSignature("QVariant, QVariant")
    def on_tweetView_reply(self, user, msg):
        """Prepare to send a reply at user in response to msg, if provided"""
        user = user.toPyObject()
        msg = msg.toPyObject()
        #Get the most related account that can reply
        canReplyAccounts = ()
        for account in self._store.getAccounts():
            if account.getCapabilities().canReply(user):
                canReplyAccounts += (account,)
        account = self.getClosetsRelatedAccount(user, canReplyAccounts)
        #Get a possible prefix and put it into MessageTextEdit
        prefix = account.getCapabilities().replyPrefix(user)
        #Set prefix, do it here to avoid updating UI when state is not set correctly
        self.MessageTextEdit.document().setPlainText(prefix)
        #Update PostFromComboBox
        self.PostFromComboBox.clear()
        self.PostFromComboBox.addItem(QIcon(":/icons/icons/tango/32x32/apps/internet-group-chat.png"), "All")
        index = 1
        for replyAccount in canReplyAccounts:
            self.PostFromComboBox.addItem(QIcon(":/icons/icons/services/" + replyAccount.getService() + ".png"), str(replyAccount))
            if str(account) == str(replyAccount):
                self.PostFromComboBox.setCurrentIndex(index)
            index += 1
        #Set state depending on whether or not there is a prefix
        if prefix == u'':
            self._newMessageState = "reply"
        else:
            self._newMessageState = "prefixed_reply"
        self._newMessageToUser = user
        self._newMessageInReplyTo = msg
        #Force update UI
        self.displayMessageEditPane()
        self.on_MessageTextEdit_textChanged()   #Consider removing this if not needed
        
    @pyqtSignature("QVariant, QVariant")
    def on_tweetView_direct(self, user, msg):
        """Prepare to send a direct message at user"""
        user = user.toPyObject()
        msg = msg.toPyObject()
        #Get the most related account that can send direct messages
        canDirectAccounts = ()
        for account in self._store.getAccounts(user.getService()):
            if account.getCapabilities().canDirect(user):
                canDirectAccounts += (account,)
        account = self.getClosetsRelatedAccount(user, canDirectAccounts)
        #Get a possible prefix
        prefix = account.getCapabilities().directPrefix(user)
        #Set prefix, do it here to avoid updating UI when state is not set correctly
        self.MessageTextEdit.document().setPlainText(prefix)
        #Update PostFromComboBox
        self.PostFromComboBox.clear()
        self.PostFromComboBox.addItem(QIcon(":/icons/icons/tango/32x32/apps/internet-group-chat.png"), "All")
        index = 1
        for directAccount in canDirectAccounts:
            self.PostFromComboBox.addItem(QIcon(":/icons/icons/services/" + directAccount.getService() + ".png"), str(directAccount))
            if str(account) == str(directAccount):
                self.PostFromComboBox.setCurrentIndex(index)
            index += 1
        #Set state depending on whether or not there is a prefix
        if prefix == u'':
            self._newMessageState = "direct"
        else:
            self._newMessageState = "prefixed_direct"
        self._newMessageToUser = user
        self._newMessageInReplyTo = msg
        #Force update UI
        self.displayMessageEditPane()
        self.on_MessageTextEdit_textChanged()   #Consider removing this if not needed
    
    _newMessageState = None
    """State variable that indicates if we're programmatically writing a reply or direct message
        Possible values: "reply", "direct", "prefixed_reply", "prefixed_direct", None
    """
    _newMessageToUser = None
    """The user a programmatic reply or direct message is to"""
    
    _newMessageInReplyTo = None
    """The message a programmatic reply or direct message is in-reply-to"""
    
    @pyqtSignature("")
    def on_MessageTextEdit_textChanged(self):
        """Update the message edit UI"""
        #Get accounts that is selected
        accounts = (self._currentPostToAccount,)
        if accounts == (None,):
            accounts = ()
            #Only keep accounts that are present in PostFromComboBox
            for account in self._store.getAccounts():
                if self.PostFromComboBox.findText(str(account)) != -1:
                    accounts += (account,)
        #Search for prefixes if we need to do so by state
        reply_to_users = {}
        direct_to_users = {}
        limit = 2**16
        #If not in any state or state is prefixed, search for possible prefix
        if self._newMessageState == None or self._newMessageState.startswith("prefixed"):
            #Get the text
            text = unicode(self.MessageTextEdit.document().toPlainText())
            #Check accounts for prefixes
            for account in accounts:
                capabilities = account.getCapabilities()
                reply = capabilities.isReplyPrefix(text)
                if reply:
                    reply_to_users[account] = reply
                    limit = min(limit, capabilities.replyMessageSize())
                direct = capabilities.isDirectPrefix(text)
                if direct:
                    direct_to_users[account] = direct
                    limit = min(limit, capabilities.directMessageSize())
                if not direct and not reply:
                    limit = min(limit, capabilities.updateMessageSize())
            #if there's a prefix byPrefix is True
            byPrefix = len(reply_to_users) > 0 or len(direct_to_users) > 0
            
        #Handle possible programmatic states
        if self._newMessageState:
            #Find limit if needed
            if not self._newMessageState.startswith("prefixed"):
                for account in accounts:
                    if self._newMessageState.endswith("reply"):
                        limit = min(limit, account.getCapabilities().replyMessageSize())
                    else:
                        limit = min(limit, account.getCapabilities().directMessageSize())
            #If the message supposed to be prefixed, but isn't prefixed to the same user, or user is None, clear state
            if self._newMessageState.startswith("prefixed") and ( not byPrefix or
            (type == "reply"  and not self._newMessageToUser in reply_to_users.values()) or
            (type == "direct"  and not self._newMessageToUser in direct_to_users.values())):
                self.on_clearReplyButton_clicked()
                return None 
            if self._newMessageState.endswith("reply"):
                text = "Reply to <b>" + self._newMessageToUser.getUsername() + "</b>"
            if self._newMessageState.endswith("direct"):
                text = "Direct message to <b>" + self._newMessageToUser.getUsername() + "</b>"
            if self._newMessageInReplyTo:
                text += " in reply to: <i>" + self._newMessageInReplyTo.getMessage() + "</i>"
            self.replyLabel.setText(text)
            self.replyLabel.show()
            self.clearReplyButton.show()
            self.postButton.setDisabled(False)
            self.updateCharCount(limit)
        if self._newMessageState == None:
            #Handle non programmatic reply/direct message by prefix
            if byPrefix:
                #Set these to True if there's something we can't reply/direct to
                cantReply, cantDirect = None, None
                #Check if canReply and canDirect
                for account, user in reply_to_users.items():
                    if not account.getCapabilities().canReply(user):
                        cantReply = (account, user)
                for account, user in direct_to_users.items():
                    if not account.getCapabilities().canDirect(user):
                        cantDirect = (account, user)
                #If we cannot write direct or can't reply
                if cantReply or cantDirect:
                    if cantReply:
                        self.replyLabel.setText("<b style='color: red;'>Can't reply to " + user.getUsername() + " using " + str(account) + "!</b>")
                    if cantDirect:
                        self.replyLabel.setText("<b style='color: red;'>Can't send direct messages to " + user.getUsername() + " using " + str(account) + "!</b>")
                    self.replyLabel.show()
                    self.updateCharCount()
                    self.postButton.setDisabled(True)
                    self.clearReplyButton.hide()
                else:
                    #Update UI
                    text = ""
                    #If this message is replying to somebody indicate it
                    if len(reply_to_users) > 0:
                        text += "Reply to " + reply_to_users.values()[0].getUsername() + " on "
                        self.postButton.setText("Reply")
                        for account, user in reply_to_users.items():
                            text += account.getService() + ", "
                        text = text[:-2] + " " #Remove last comma and space
                    #In case prefix for a reply and a direct message is the same, let's allow the UI to handle it
                    if len(direct_to_users) > 0 and len(reply_to_users) > 0:
                        text += " and direct message to " + direct_to_users.values()[0].getUsername() + " on "
                        self.postButton.setText("Send and reply")
                    elif len(direct_to_users) > 0:
                        text += "Direct message to " + direct_to_users.values()[0].getUsername() + " on "
                        self.postButton.setText("Send")
                    for account, user in direct_to_users.items():
                        text += account.getService() + ", "
                    if len(direct_to_users) > 0:
                        text = text[:-2] + " " #Remove last comma and space
                    self.replyLabel.setText(text)
                    self.replyLabel.show()
                    self.clearReplyButton.hide()
                    self.postButton.setDisabled(False)
                    self.updateCharCount(limit)
            if not byPrefix:
                #If not prefixed we are writing an update, so hide labels and clear icon
                self.postButton.setText("Update")
                self.postButton.setDisabled(False)
                self.replyLabel.hide()
                self.clearReplyButton.hide()
                self.updateCharCount(limit)
        
    def updateCharCount(self, limit = None):
        """Update char count label and disable postbutton if it is above limit"""
        #If no limit provided don't show any text
        if not limit:
            self.counterLabel.setText("")
            
        left = limit - len(self.MessageTextEdit.document().toPlainText())
        #Disabled post button
        self.postButton.setDisabled(left < 0)
        #Update the label
        if left < 10:   #Red text
            self.counterLabel.setText("<b style='color: red;'>" + str(left) + "</b>")
        elif left < 20: #Bold black text
            self.counterLabel.setText("<b>" + str(left) + "</b>")
        else:   #Black text
            self.counterLabel.setText(str(left))

    _currentPostToAccount = None
    """Currently selected account in PostFromComboBox"""
            
    @pyqtSignature("QString")
    def on_PostFromComboBox_currentIndexChanged(self, text):
        """"Updates _currentPostToAccount, so it's always up to date"""
        #Update _currentPostToAccount
        self._currentPostToAccount = None
        for account in self._store.getAccounts():
            if str(account) == text:
                self._currentPostToAccount = account
        #Update view, postButton might be disabled if canReply == False
        self.on_MessageTextEdit_textChanged()

    @pyqtSignature("")
    def on_clearReplyButton_clicked(self):
        #Reset state
        self._newMessageState = None
        self._newMessageToUser = None
        self._newMessageInReplyTo = None
        #Add all items to PostFromComboBox
        current_account = self._currentPostToAccount
        self.PostFromComboBox.clear()
        self.PostFromComboBox.addItem(QIcon(":/icons/icons/tango/32x32/apps/internet-group-chat.png"), "All")
        index = 1
        for account in self._store.getAccounts():
            self.PostFromComboBox.addItem(QIcon(":/icons/icons/services/" + account.getService() + ".png"), str(account))
            if str(account) == str(current_account):
                self.PostFromComboBox.setCurrentIndex(index)
            index += 1
        if current_account == None:
            self.PostFromComboBox.setCurrentIndex(0)
        #Force update UI
        self.on_MessageTextEdit_textChanged()
        
    @pyqtSignature("")
    def on_postButton_clicked(self):
        """Post message"""
        #get the message text
        text = unicode(self.MessageTextEdit.document().toPlainText())
        #Get accounts that is selected
        accounts = (self._currentPostToAccount,)
        if accounts == (None,):
            accounts = ()
            #Only keep accounts that are present in PostFromComboBox
            for account in self._store.getAccounts():
                if self.PostFromComboBox.findText(str(account)) != -1:
                    accounts += (account,)
        print accounts
        #If we're writing a programmatic reply
        if self._newMessageState:
            for account in accounts:
                #If we're writing a reply
                if self._newMessageState.endswith("reply"):
                    if self._newMessageInReplyTo:
                        msg = Message(self._store, text, account.getUser(), reply_at = self._newMessageToUser, reply_to = self._newMessageInReplyTo)
                    else:
                        msg = Message(self._store, text, account.getUser(), reply_at = self._newMessageToUser)
                else: #If we're writing a direct message
                    if self._newMessageInReplyTo:
                        msg = Message(self._store, text, account.getUser(), direct_at = self._newMessageToUser, direct_to = self._newMessageInReplyTo)
                    else:
                        msg = Message(self._store, text, account.getUser(), direct_at = self._newMessageToUser)
                #Post whatever message
                self._store.postMessage(msg)
        #If we might be writing a reply, direct or an update
        if not self._newMessageState:
            for account in accounts:
                capabilities = account.getCapabilities()
                direct = capabilities.isDirectPrefix(text)
                if direct: #Write a direct message
                    msg = Message(self._store, text, account.getUser(), direct_at = direct)
                    continue #Continue to next account, don't also make a reply, if possible
                reply = capabilities.isReplyPrefix(text)
                if reply:
                    #Write a reply
                    msg = Message(self._store, text, account.getUser(), reply_at = reply)
                else:
                    #Write an update
                    msg = Message(self._store, text, account.getUser())
                #Post whatever message
                self._store.postMessage(msg)
        #Clear once message has been sent
        self.on_clearReplyButton_clicked()
        self.MessageTextEdit.document().clear()
        
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
        groupIcon = QIcon(":/icons/icons/tango/32x32/apps/internet-group-chat.png")
        self.PostFromComboBox.addItem(groupIcon, "All")
        self.ViewAccountComboBox.addItem(groupIcon, "All")
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
        #TODO:  Figure out how to make the comboboxes adjust their size.
        #       This is only relevat for first time runs, as it will be auto size at startup
        #       Note: self.PostFromComboBox.adjustSize() does not work.
    
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
        self._statusbarLabels[account].setToolTip(str(account) + "\n" + status)
        #TODO: Attempt reauthendicate if status is "bad authendication"
        
        
    @pyqtSignature("")
    def on_PreferencesAction_triggered(self):
        dlg = PreferencesDialog(self._store, self)
        #Update settings if they are changed
        if dlg.exec_() == QDialog.Accepted:
            self.loadSettings()
    
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

    def displayNotification(self, title, text, image = None):
        """Displays a message"""
        self.TrayIcon.showMessage(title, text)
        #TODO: Change this to use bindings for growl and libnotify
        #Please do ensure that the bubbles are associated with the tray icon.
        #Otherwise it will look ugly on desktops that uses this association to draw speech bubbles.
        #Example of this association: https://wiki.ubuntu.com/NotifyOSD?action=AttachFile&do=get&target=3g-finished.png
