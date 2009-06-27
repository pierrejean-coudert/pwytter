# -*- coding: utf-8 -*-

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtNetwork import *
from PyQt4.QtWebKit import *

from time import strftime, localtime
import webbrowser

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
	def __init__(self, parent = None):
		#Initialize the underlying widget
		QWebView.__init__(self, parent)
		
		#Delgate all links, then we'll manually load those we want :)
		self.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
		self.connect(self.page(), SIGNAL("linkClicked(QUrl)"), self.linkClicked)

	def setStore(self, store):
		self.store = store
		#Use NetworkAccessManager that implements pwytter://
		oldManager = self.page().networkAccessManager()
		self.manager = NetworkAccessManager(oldManager, store, self)
		self.page().setNetworkAccessManager(self.manager)
		
		#Set the theme
		self.setTheme()

	tweetPageSize = 5
	def setTweetPageSize(self, tweetPageSize):
		"""Set tweet page size"""
		self.tweetPageSize = tweetPageSize

	userPageSize = 3
	def setUserPageSize(self, userPageSize):
		"""Set user page size"""
		self.userPageSize = userPageSize

	theme = {}
	def setTheme(self, theme = "default"):
		self.theme["messagesTemplate"] = open("themes/" + theme + "/Messages.tpl").read()
		self.theme["usersTemplate"] = open("themes/" + theme + "/Users.tpl").read()
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

class PwytterReply(QNetworkReply):
	def __init__(self, parent, url, operation, store, view):
		QNetworkReply.__init__(self, parent)
		
		#Save store and theme
		self.store = store
		self.view = view
		
		#Set content and header
		#self.setHeader(QNetworkRequest.ContentTypeHeader, QVariant("text/html; charset=ASCII"))
		#self.content = "<html><head><title>Test</title></head><body>This is a test.</body></html>"
		
		urlparts = str(url.toString()).split("/")
		if urlparts[2] == "view":
			#Get the account
			account = None
			for ac in store.getAccounts():
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
				data = self.store.getTimeline(account, page = page, page_size = view.tweetPageSize)
			elif urlparts[3] == "replies":
				data = self.store.getReplies(user, page = page, page_size = view.tweetPageSize)
			elif urlparts[3] == "direct messages":
				data = self.store.getDirectMessages(user, page = page, page_size = view.tweetPageSize)
			elif urlparts[3] == "followers":
				data = self.store.getFollowers(account, page = page, page_size = view.userPageSize)
			elif urlparts[3] == "friends":
				data = self.store.getFriends(account, page = page, page_size = view.userPageSize)
			
			#Parse template
			if urlparts[3] in ("followers", "friends"):
				#Parse users template
				header, template, footer = view.theme["usersTemplate"].split("{foreach}", 2)
				html = QString(header)
				for user in data:
					msg = QString(template)
					msg = msg.replace("{name}", user.getName())
					msg = msg.replace("{service}", user.getService())
					msg = msg.replace("{img}", "pwytter://image/cache/" + str(user._getImageID()))
					html += msg
				html += footer
				html = html.replace("{next}", "/".join(urlparts[0:5]) + "/" + str(page+1))
				html = html.replace("{prev}", "/".join(urlparts[0:5]) + "/" + str(page-1))
				self.content = str(html)
			else:
				#Parse messages template
				header, template, footer = view.theme["messagesTemplate"].split("{foreach}", 2)
				html = QString(header)
				for message in data:
					msg = QString(template)
					msg = msg.replace("{date}", strftime("the %d of %m, %Y", localtime(message.getCreated())))
					msg = msg.replace("{message}", message.getMessage())
					msg = msg.replace("{name}", message.getUser().getName())
					msg = msg.replace("{img}", "pwytter://image/cache/" + str(message.getUser()._getImageID()))
					html += msg
				html += footer
				html = html.replace("{next}", "/".join(urlparts[0:5]) + "/" + str(page+1))
				html = html.replace("{prev}", "/".join(urlparts[0:5]) + "/" + str(page-1))
				self.content = str(html)
			#Set content type
			self.setHeader(QNetworkRequest.ContentTypeHeader, QVariant("text/html; charset=UTF-8"))
		elif urlparts[2] == "image":
			if urlparts[3] == "cache":
				img_id = int(urlparts[4])
				data = self.store._getImage(img_id)
				self.content = str(data)
			elif urlparts[3] == "theme":
				image = "themes/" + view.theme["name"] + "/Images/" + urlparts[4]
				self.content = open(image).read()
		else:
			print "Invalid url: " + url.toString()
			self.content = "<h1>404</h1><br>File not found!" 
			self.setHeader(QNetworkRequest.ContentTypeHeader, QVariant("text/html; charset=UTF-8"))
		
		#Remarks: If we are ever to do async requests, this is where we shall break, and the following including setting self.content
		#should then be performed by an eventhandler
		self.offset = 0
		self.setHeader(QNetworkRequest.ContentLengthHeader, QVariant(len(self.content)))
		QTimer.singleShot(0, self, SIGNAL("readyRead()"))
		QTimer.singleShot(0, self, SIGNAL("finished()"))
		self.open(self.ReadOnly | self.Unbuffered)
		self.setUrl(url)
	
	def abort(self):
		pass
    
	def bytesAvailable(self):
		return len(self.content) - self.offset
    
	def isSequential(self):
		return True
    
	def readData(self, maxSize):
		if self.offset < len(self.content):
			end = min(self.offset + maxSize, len(self.content))
			data = self.content[self.offset:end]
			self.offset = end
			return data

class NetworkAccessManager(QNetworkAccessManager):
	def __init__(self, oldManager, store, view):
		QNetworkAccessManager.__init__(self)
		self.store = store
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
			if operation != self.GetOperation:
				print "We're performing something other than get requests to pwytter://, this is bad!!!"
			reply = PwytterReply(self, request.url(), self.GetOperation, self.store, self.view)
			return reply
		return QNetworkAccessManager.createRequest(self, operation, request, data)
