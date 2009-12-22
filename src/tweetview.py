# -*- coding: utf-8 -*-

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtNetwork import *
from PyQt4.QtWebKit import *
import tinpy
from theme import Theme

from time import strftime, localtime
import webbrowser
import tweetstore
from os import path
import traceback

""" Add a pwytter:// protocol to a QtWebView see:
    http://diotavelli.net/PyQtWiki/Using%20a%20Custom%20Protocol%20with%20QtWebKit
"""

class TweetView(QWebView):
    """Custom widget to display tweets and users in pwytter
    
        This is a QWebView extended to support a new procotol called pwytter://
        when displaying a pwytter:// page, external links, ALL external links are
        open in an external browser.
        Pwytter protocol renders tweets and users and supports following addresses:
        pwytter://view/timeline/<account>/<page>
        pwytter://view/replies/<account>/<page>
        pwytter://view/direct messages/<account>/<page>
        pwytter://view/outbox/<account>/<page>
        pwytter://view/followers/<account>/<page>
        pwytter://view/friends/<account>/<page>
        
        <account> can be the string representation of an account or the string 'all'
        <page> is a number, can be omitted
        
        Display a single user using:
        pwytter://view/user/<service>/<username>
        
        pwytter://image/cache/<image-id>
        pwytter://theme/<path-relative-theme-dir>
        
        In the future we might add:
        pwytter://search/<account>/<query>
        pwytter://view/timeline/<account>/<page>/by/<index>
    """
    __pyqtSignals__ = ("reply(QVariant, QVariant)", "direct(QVariant, QVariant)", "retweet(QVariant)")
    
    def __init__(self, parent = None):
        #Initialize the underlying widget
        QWebView.__init__(self, parent)
        
        #Currently displayed content
        self._content = ()
        
        #Delgate all links, then we'll manually load those we want :)
        self.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        self.connect(self.page(), SIGNAL("linkClicked(QUrl)"), self.linkClicked)
        self._jsAPI = JavascriptAPI(self, self)
        self.connect(self.page().mainFrame(), SIGNAL("javaScriptWindowObjectCleared()"), self.provideJavascriptAPI)

    def provideJavascriptAPI(self):
        self.page().mainFrame().addToJavaScriptWindowObject("pwytter", self._jsAPI)

    def setStore(self, store):
        self._store = store
        #Use NetworkAccessManager that implements pwytter://
        oldManager = self.page().networkAccessManager()
        self.manager = NetworkAccessManager(oldManager, self)
        self.page().setNetworkAccessManager(self.manager)

    _tweetPageSize = 10
    def setTweetPageSize(self, tweetPageSize):
        """Set tweet page size"""
        self._tweetPageSize = tweetPageSize

    _userPageSize = 15
    def setUserPageSize(self, userPageSize):
        """Set user page size"""
        self._userPageSize = userPageSize

    __theme = None
    def setTheme(self, theme):
        assert isinstance(theme, Theme), "theme must be an instance of Theme"
        self.__theme = theme
        self.reload()

    def linkClicked(self, url):
        #Load the url if it is the pwytter protocol
        if url.scheme() == "pwytter" or self.url().scheme() != "pwytter":
            self.page().mainFrame().load(url)
        else:
            #If it's an external link, for whatever I don't care! open it in a webbrowser :)
            webbrowser.open(url.toString(), 1)

    def _setReplyContent(self, reply):
        """Put some content into a reply, note reply need not be filled when this method returns"""
        try:
            assert self.__theme != None, "Theme must be provided before content can be viewed."
            urlparts = str(reply.url().toString()).split("/")
            if urlparts[2] == "view":
                self.__setReplyContentView(reply)
            elif urlparts[2] == "image":
                if urlparts[3] == "cache":
                    img_id = int(urlparts[4])
                    data = self._store._getImage(img_id)
                    reply.setContent(str(data))
            elif urlparts[2] == "theme":
                ressource = path.join(self.__theme.getPath(), *urlparts[3:])
                reply.setContent(open(ressource, "rb").read())
            else:
                print "Invalid url: " + url.toString()
                reply.setContent("<h1>404</h1><br>File not found!", "text/html; charset=UTF-8")
        except:
            reply.setContent("<h1>500</h1><br>Internal Server Error!<br><br><pre>" + traceback.format_exc() + "</pre>", "text/html; charset=UTF-8")

    def __setReplyContentView(self, reply):
        """Set a pwytterReply to a view, assume it is a view"""
        urlparts = str(reply.url().toString()).split("/")
        
        #If we're asked to view a specific user
        if urlparts[3] == "user":
            #Get the user to display
            user = self._store.getUser(urlparts[5], urlparts[4])
            if user == None:
                reply.setContent(u"<h1>User not found</h1>Username " + urlparts[5] + " on " + urlparts[4] + " was not found in the database.", "text/html; charset=UTF-8")
            else:
                self._content = (user,)
                vars = {"User" : UserWrapper(user, self._store, 0)}
                vars["Text"] = self.__GetTranslatedText()
                html = tinpy.build(self.__theme.getDetailedUserTemplate(), vars, strict = __debug__)
                reply.setContent(unicode(html).encode('utf-8'), "text/html; charset=UTF-8")
            return None

        #Get the account
        account = None
        for ac in self._store.getAccounts():
            if urlparts[4] == str(ac):
                account = ac
        #Get the account user if we need it
        user = None
        if account and urlparts[3] in ("replies", "direct messages"):
            user = account.getUser()
        #Get page
        try:
            page = int(urlparts[5])
        except:
            page = 0
        #Get data
        isOutbox = False    #If the messages can be deleted, ONLY true for outbox
        if urlparts[3] == "timeline":   
            self._content = tuple(self._store.getTimeline(account, page = page, page_size = self._tweetPageSize))
        elif urlparts[3] == "replies":
            self._content = tuple(self._store.getReplies(user, page = page, page_size = self._tweetPageSize))
        elif urlparts[3] == "direct messages":
            self._content = tuple(self._store.getDirectMessages(user, page = page, page_size = self._tweetPageSize))
        elif urlparts[3] == "outbox":
            self._content = tuple(self._store.getOutbox(account, page = page, page_size = self._tweetPageSize))
            isOutbox = True
        elif urlparts[3] == "followers":
            self._content = tuple(self._store.getFollowers(account, page = page, page_size = self._userPageSize))
        elif urlparts[3] == "friends":
            self._content = tuple(self._store.getFriends(account, page = page, page_size = self._userPageSize))
        #Parse template
        if urlparts[3] in ("followers", "friends"):
            vars = {}
            vars["Text"] = self.__GetTranslatedText()
            vars["Users"] = ()
            pageUniqueId = 0
            for user in self._content:
                vars["Users"] += (UserWrapper(user, self._store, pageUniqueId),)
                pageUniqueId += 1
            vars["HasNextPage"] = True
            vars["HasPrevPage"] = page != 0
            vars["NextPage"] = "/".join(urlparts[0:5]) + "/" + str(page+1)
            vars["PrevPage"] = "/".join(urlparts[0:5]) + "/" + str(page-1)
            #Parse users template
            html = tinpy.build(self.__theme.getUsersTemplate(), vars, strict = __debug__)
            reply.setContent(unicode(html).encode('utf-8'), "text/html; charset=UTF-8")
        else:
            vars = {}
            vars["Text"] = self.__GetTranslatedText()
            vars["Messages"] = ()
            pageUniqueId = 0
            for message in self._content:
                vars["Messages"] += (MessageWrapper(message, self._store, pageUniqueId, isOutbox),)
                pageUniqueId += 1
            vars["HasNextPage"] = True
            vars["HasPrevPage"] = page != 0
            vars["NextPage"] = "/".join(urlparts[0:5]) + "/" + str(page+1)
            vars["PrevPage"] = "/".join(urlparts[0:5]) + "/" + str(page-1)
            #Parse template
            html = tinpy.build(self.__theme.getMessagesTemplate(), vars, strict = __debug__)
            reply.setContent(unicode(html).encode('utf-8'), "text/html; charset=UTF-8")
    
    def _reply(self, id):
        """Handle javascript callback to create a reply for message or user with id"""
        if id == -1:
            return "Cannot use item in current view, there's likely a bug in the template!"
        try:
            #Get message and user we wish to reply to
            item = self._content[id]
            if isinstance(item, tweetstore.Message):
                msg = item
                user = item.getUser()
            else:
                msg = None
                user = item
            #Emit signal for the mainWindow to handle
            self.emit(SIGNAL("reply(QVariant, QVariant)"), QVariant(user), QVariant(msg))
        except IndexError:
            return "Item does not exist, there's likely a bug in the template!"
        except:
            return "Exception occured: \n" + traceback.format_exc()
    
    def _retweet(self, id):
        """Handle javascript callback to create a retweet for message with id"""
        if id == -1:
            return "Cannot use item in current view, there's likely a bug in the template!"
        try:
            #Get message and user we wish to reply to
            msg = self._content[id]
            if not isinstance(msg, tweetstore.Message):
                return "Cannot retweet to a user, this is likely a template bug!"
            #Emit signal for the mainWindow to handle
            self.emit(SIGNAL("retweet(QVariant)"), QVariant(msg))
        except IndexError:
            return "Item does not exist, there's likely a bug in the template!"
        except:
            return "Exception occured: \n" + traceback.format_exc()
            
    def _direct(self, id):
        """Handle javascript callback to create a direct for message or user with id"""
        if id == -1:
            return "Cannot use item in current view, there's likely a bug in the template!"
        try:
            #Get message and user we wish send a direct message to
            item = self._content[id]
            if isinstance(item, tweetstore.Message):
                msg = item
                user = item.getUser()
            else:
                msg = None
                user = item
            #Emit signal for the mainWindow to handle
            self.emit(SIGNAL("direct(QVariant, QVariant)"), QVariant(user), QVariant(msg))
        except IndexError:
            return "Item does not exist, there's likely a bug in the template!"
        except:
            return "Exception occured: \n" + traceback.format_exc()

    def _delete(self, id):
        """Handle javascript callback to delete a message, MUST be a message in outbox"""
        if id == -1:
            return "Cannot use item in current view, there's likely a bug in the template!"
        try:
            if not self._store.removeFromOutbox(self._content[id]):
                return "Message was not deleted, ensure that it could be deleted."
        except IndexError:
            return "Item does not exist, there's likely a bug in the template!"
        except:
            return "Exception occured: \n" + traceback.format_exc()
    
    __lazyLoadedTranslatedText = None
    def __GetTranslatedText(self):
        """Lazy loads and returns a dictionary of translated strings for use in templates"""
        #Load if not already loaded
        if self.__lazyLoadedTranslatedText == None:
            text = {}
            text["Reply"] = unicode(self.tr("Reply"))
            text["Retweet"] = unicode(self.tr("Retweet"))
            text["Direct_message"] = unicode(self.tr("Direct message"))
            text["Delete_message"] = unicode(self.tr("Delete message"))
            text["Prev_page"] = unicode(self.tr("Prev page"))
            text["Next_page"] = unicode(self.tr("Next page"))
            text["Go_to_previous_page"] = unicode(self.tr("Go to previous page"))
            text["Go_to_next_page"] = unicode(self.tr("Go to next page"))
            text["<user>_on_<service>"] = unicode(self.tr("on", "'on' as in: Jopsen on twitter"))
            text["Description"] = unicode(self.tr("Description"))
            text["On_<date>"] = unicode(self.tr("On", "'On' as in: On the 21 of 12, 2009."))
            self.__lazyLoadedTranslatedText = text
        #Return the dictionary
        return self.__lazyLoadedTranslatedText

class PwytterReply(QNetworkReply):
    """A reply for a pwytter:// request, does nothing but waits for someone to set it's content"""
    def __init__(self, parent, url, operation):
        QNetworkReply.__init__(self, parent)
        self.setUrl(url)
        self.ready = False
        
    def setContent(self, content, type = None):
        """Set content and mimetype, if provided."""
        self.content = content
        if type:
            self.setHeader(QNetworkRequest.ContentTypeHeader, QVariant(type))
        
        self.offset = 0
        self.ready = True
        self.setHeader(QNetworkRequest.ContentLengthHeader, QVariant(len(self.content)))
        QTimer.singleShot(0, self, SIGNAL("readyRead()"))
        QTimer.singleShot(0, self, SIGNAL("finished()"))
        self.open(self.ReadOnly | self.Unbuffered)
    
    def abort(self):
        pass
    
    def bytesAvailable(self):
        if self.ready:
            return len(self.content) - self.offset
        else:
            return 0
    
    def isSequential(self):
        return True
    
    def readData(self, maxSize):
        if self.bytesAvailable > 0:
            end = min(self.offset + maxSize, len(self.content))
            data = self.content[self.offset:end]
            self.offset = end
            return data

class NetworkAccessManager(QNetworkAccessManager):
    """Special NetworkAccessManager that handles pwytter:// requests and passes them on to tweetview"""
    def __init__(self, oldManager, view):
        QNetworkAccessManager.__init__(self)
        self.view = view
        self.oldManager = oldManager
        #Consider enabling when switching to Qt 4.5
        #self.setCache(oldManager.cache())
        self.setCookieJar(oldManager.cookieJar())
        self.setProxy(oldManager.proxy())
        #Consider enabling when switching to Qt 4.5
        #self.setProxyFactory(oldManager.proxyFactory())
    
    def createRequest(self, operation, request, data):
        if request.url().scheme() == "pwytter": #and operation == self.GetOperation, not need since we shouldn't perform other requests
            assert operation == self.GetOperation, "the pwytter:// protocol does only support GET requests!"
            reply = PwytterReply(self, request.url(), self.GetOperation)
            self.view._setReplyContent(reply)
            return reply
        return QNetworkAccessManager.createRequest(self, operation, request, data)

class UserWrapper:
    def __init__(self, user, store, id = -1):
        """Wraps a user as if it was a dictionary
            For use in template system, as we don't want template designers to deal with pwytter backend internals
            
            user:   instance of User
            store:  instance of tweetstore, used later to add stuff like isFriend
            id:     Page specific id, note ONLY page unique!
                    Used for getting hold of this user on the serverside.
                    Use -1 if no identifier is assigned.
        """
        self.__user = user
        self.__store = store
        self.__id = id
    
    def get(self, key, default = ""):
        try:
            return self.__getitem__(key)
        except KeyError:
            return default
    
    def __getitem__(self, key):
        if key == "Name":
            return self.__user.getName()
        if key == "Service":
            return self.__user.getService()
        if key == "Image":
            return "pwytter://image/cache/" + str(self.__user._getImageID())
        if key == "Description":
            return self.__user.getDescription()
        if key == "Location":
            return self.__user.getLocation()
        if key == "Url":
            return self.__user.getUrl()
        if key == "Username":
            return self.__user.getUsername()
        if key == "IsFriend":
            return self.__store.isFriend(self.__user)
        if key == "IsFollower":
            return self.__store.isFollower(self.__user)
        if key == "CanReply":
            if self.__id == -1: return False
            #Determine if we can reply to this user
            accounts = self.__store.getAccounts(self.__user.getService())
            for account in accounts:
                if account.getCapabilities().canReply(self.__user):
                    return True
            return False
        if key == "CanSendDirectMessage":
            if self.__id == -1: return False
            #Determine if we send direct messages to this user
            accounts = self.__store.getAccounts(self.__user.getService())
            for account in accounts:
                if account.getCapabilities().canDirect(self.__user):
                    return True
            return False
        if key == "Id":
            return self.__id
        #Key wasn't found if we got here:
        raise KeyError, "Key not found"
    
    def __repr__(self):
        return str(self.__user)

class MessageWrapper:
    def __init__(self, message, store, id = -1, isOutbox = False):
        """Wraps a message as if it was a dictionary
            For use in template system, as we don't want template designers to deal with pwytter backend internals
            
            message:    instance of Message
            store:      instance of tweetstore, used later to add stuff like isFriend
            id:         Page specific id, note ONLY page unique!
                        Used for getting hold of this user on the serverside.
                        Use -1 if no identifier is assigned.
            isOutbox:   Boolean indicates if a message is an outbox message and thus can be deleted.
        """
        self.__message = message
        self.__store = store
        self.__id = id
        self.__isOutbox = isOutbox
    
    def get(self, key, default = ""):
        try:
            return self.__getitem__(key)
        except KeyError:
            return default
    
    def __getitem__(self, key):
        if key == "Text":
            return self.__message.getMessage()
        if key == "User":
            return UserWrapper(self.__message.getUser(), self.__store, -1)
        if key == "Service":
            return self.__message.getService()
        if key == "Created":
            #TODO: Use a suitable date format
            return strftime("the %d of %m, %Y", localtime(self.__message.getCreated()))
        if key == "InReplyTo":
            return MessageWrapper(self.__message.getReplyTo(), self.__store, -1)
        if key == "ReplyAt":
            return UserWrapper(self.__message.getReplyAt(), self.__store, -1)
        if key == "IsReply":
            return self.__message.isReply()
        if key == "IsInReplyTo":
            return self.__message.getReplyTo() != None
        if key == "IsDirectMessage":
            return self.__message.isDirectMessage()
        if key == "DirectMessageAt":
            return UserWrapper(self.__message.getDirectAt(), self.__store, -1)
        if key == "CanReply":
            if self.__id == -1: return False
            #Cannot ever reply to an outbox message!
            if self.__isOutbox: return False
            #Determine if we can reply to this message
            accounts = self.__store.getAccounts(self.__message.getService())
            for account in accounts:
                if account.getCapabilities().canReply(self.__message.getUser(), self.__message):
                    return True
            return False
        if key == "CanRetweet":
            if self.__id == -1: return False
            #Cannot ever reply to an outbox message!
            if self.__isOutbox: return False
            #Determine if we can reply to this message
            accounts = self.__store.getAccounts(self.__message.getService())
            for account in accounts:
                if account.getCapabilities().canRetweet(self.__message):
                    return True
            return False
        if key == "CanSendDirectMessage":
            if self.__id == -1: return False
            #Cannot ever send direct to an outbox message!
            if self.__isOutbox: return False
            #Determine if we send direct messages as reply to this message
            accounts = self.__store.getAccounts(self.__message.getService())
            for account in accounts:
                if account.getCapabilities().canDirect(self.__message.getUser(), self.__message):
                    return True
            return False
        if key == "CanDelete":
            if self.__id == -1: return False
            #Can delete messages in outbox
            return self.__isOutbox
        if key == "Id":
            return self.__id
        #Key wasn't found if we got here:
        raise KeyError, "Key not found"

class JavascriptAPI(QObject):
    """Simple object that exposes the javascript API of tweetview"""
    def __init__(self, parent, view):
        QObject.__init__(self, parent)
        self._view = view

    @pyqtSignature("int")
    def reply(self, id):
        return self._view._reply(id)
    
    @pyqtSignature("int")   
    def direct(self, id):
        return self._view._direct(id)
        
    @pyqtSignature("int")   
    def delete(self, id):
        return self._view._delete(id)
        
    @pyqtSignature("int")   
    def retweet(self, id):
        return self._view._retweet(id)
