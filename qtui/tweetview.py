# -*- coding: utf-8 -*-

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtNetwork import *
from PyQt4.QtWebKit import *
import tinpy

from time import strftime, localtime
import webbrowser
import tweetstore

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
		pwytter://view/followers/<account>/<page>
		pwytter://view/friends/<account>/<page>
		
		<account> can be the string representation of an account or the string 'all'
		<page> is a number, can be omitted
		
		pwytter://image/cache/<image-id>
		pwytter://image/theme/<image>
		
		In the future we might add:
		pwytter://search/<account>/<query>
		pwytter://view/timeline/<account>/<page>/by/<index>
	"""
	__pyqtSignals__ = ("reply(QVariant, QVariant)", "direct(QVariant, QVariant)")
	
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
		
		#Set the theme
		self.setTheme()

	_tweetPageSize = 5
	def setTweetPageSize(self, tweetPageSize):
		"""Set tweet page size"""
		self._tweetPageSize = tweetPageSize

	_userPageSize = 3
	def setUserPageSize(self, userPageSize):
		"""Set user page size"""
		self._userPageSize = userPageSize

	theme = {}
	def setTheme(self, theme = "default"):
		self.theme["messagesTemplate"] = open("themes/" + theme + "/Messages.tpl").read()
		self.theme["usersTemplate"] = tinpy.compile(open("themes/" + theme + "/Users.tpl").read())
		self.theme["userTemplate"] = open("themes/" + theme + "/DetailedUser.tpl").read()
		self.theme["name"] = theme
		self.reload()

	def linkClicked(self, url):
		#Load the url if it is the pwytter protocol
		if url.scheme() == "pwytter" or self.url().scheme() != "pwytter":
			self.page().mainFrame().load(url)
		else:
			#If it's an external link, for whatever I don't care! open it in a webbrowser :)
			webbrowser.open(url, 1)

	def _setReplyContent(self, reply):
		"""Put some content into a reply, note reply need not be filled when this method returns"""
		urlparts = str(reply.url().toString()).split("/")
		if urlparts[2] == "view":
			self.__setReplyContentView(reply)
		elif urlparts[2] == "image":
			if urlparts[3] == "cache":
				img_id = int(urlparts[4])
				data = self._store._getImage(img_id)
				reply.setContent(str(data))
			elif urlparts[3] == "theme":
				image = "themes/" + self.theme["name"] + "/Images/" + urlparts[4]
				reply.setContent(open(image).read())
		else:
			print "Invalid url: " + url.toString()
			reply.setContent("<h1>404</h1><br>File not found!", "text/html; charset=UTF-8")

	def __setReplyContentView(self, reply):
		"""Set a pwytterReply to a view, assume it is a view"""
		urlparts = str(reply.url().toString()).split("/")
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
		if urlparts[3] == "timeline":	
			self._content = tuple(self._store.getTimeline(account, page = page, page_size = self._tweetPageSize))
		elif urlparts[3] == "replies":
			self._content = tuple(self._store.getReplies(user, page = page, page_size = self._tweetPageSize))
		elif urlparts[3] == "direct messages":
			self._content = tuple(self._store.getDirectMessages(user, page = page, page_size = self._tweetPageSize))
		elif urlparts[3] == "followers":
			self._content = tuple(self._store.getFollowers(account, page = page, page_size = self._userPageSize))
		elif urlparts[3] == "friends":
			self._content = tuple(self._store.getFriends(account, page = page, page_size = self._userPageSize))
		#Parse template
		if urlparts[3] in ("followers", "friends"):
			vars = {}
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
			html = tinpy.build(self.theme["usersTemplate"], vars, strict = __debug__)
			reply.setContent(unicode(html).encode('utf-8'), "text/html; charset=UTF-8")
		else:
			vars = {}
			vars["Messages"] = ()
			pageUniqueId = 0
			for message in self._content:
				vars["Messages"] += (MessageWrapper(message, self._store, pageUniqueId),)
				pageUniqueId += 1
			vars["HasNextPage"] = True
			vars["HasPrevPage"] = page != 0
			vars["NextPage"] = "/".join(urlparts[0:5]) + "/" + str(page+1)
			vars["PrevPage"] = "/".join(urlparts[0:5]) + "/" + str(page-1)
			#Parse template
			html = tinpy.build(self.theme["messagesTemplate"], vars, strict = __debug__)
			reply.setContent(unicode(html).encode('utf-8'), "text/html; charset=UTF-8")
	
	def _reply(self, id):
		"""Handle javascript callback to create a reply for message or user with id"""
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
	
	def _direct(self, id):
		"""Handle javascript callback to create a direct for message or user with id"""
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
		if request.url().scheme() == "pwytter":	#and operation == self.GetOperation, not need since we shouldn't perform other requests
			assert operation == self.GetOperation, "the pwytter:// protocol does only support GET requests!"
			reply = PwytterReply(self, request.url(), self.GetOperation)
			self.view._setReplyContent(reply)
			return reply
		return QNetworkAccessManager.createRequest(self, operation, request, data)


class UserWrapper:
	def __init__(self, user, store, id):
		"""Wraps a user as if it was a dictionary
			For use in template system, as we don't want template designers to deal with pwytter backend internals
			
			user:	instance of User
			store:	instance of tweetstore, used later to add stuff like isFriend
			id:		Page specific id, note ONLY page unique!
					Used for getting hold of this user on the serverside.
			
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
			#Determine if we can reply to this user
			accounts = self.__store.getAccounts(self.__user.getService())
			for account in accounts:
				if account.getCapabilities().canReply(self.__user):
					return True
			return False
		if key == "CanSendDirectMessage":
			#Determine if we send direct messages to this user
			accounts = self.__store.getAccounts(self.__user.getService())
			for account in accounts:
				if account.getCapabilities().canDirect(self.__user):
					return True
			return False
		if key == "Id":
			return self.__id
		else:
			raise KeyError, "Key not found"
	
	def __repr__(self):
		return str(self.__user)

class MessageWrapper:
	def __init__(self, message, store, id):
		"""Wraps a message as if it was a dictionary
			For use in template system, as we don't want template designers to deal with pwytter backend internals
			
			message:	instance of Message
			store:		instance of tweetstore, used later to add stuff like isFriend
			id:			Page specific id, note ONLY page unique!
						Used for getting hold of this user on the serverside.
			
		"""
		self.__message = message
		self.__store = store
		self.__id = id
	
	def get(self, key, default = ""):
		try:
			return self.__getitem__(key)
		except KeyError:
			return default
	
	def __getitem__(self, key):
		if key == "Text":
			return self.__message.getMessage()
		if key == "User":
			return UserWrapper(self.__message.getUser(), self.__store, self.__id)
		if key == "Service":
			return self.__message.getService()
		if key == "Created":
			#TODO: Use a suitable date format
			return strftime("the %d of %m, %Y", localtime(self.__message.getCreated()))
		if key == "InReplyTo":
			return self.__message.getReplyTo()
		if key == "ReplyAt":
			return self.__message.getReplyAt()
		if key == "IsReply":
			return self.__message.isReply()
		if key == "IsReplyTo":
			return self.__message.getReplyTo() != None
		if key == "IsDirectMessage":
			return self.__message.isDirectMessage()
		if key == "DirectMessageAt":
			return self.__message.getDirectAt()
		if key == "CanReply":
			#Determine if we can reply to this message
			accounts = self.__store.getAccounts(self.__message.getService())
			for account in accounts:
				if account.getCapabilities().canReply(self.__message.getUser(), self.__message):
					return True
			return False
		if key == "CanSendDirectMessage":
			#Determine if we send direct messages as reply to this message
			accounts = self.__store.getAccounts(self.__message.getService())
			for account in accounts:
				if account.getCapabilities().canDirect(self.__message.getUser(), self.__message):
					return True
			return False
		if key == "Id":
			return self.__id
		else:
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
