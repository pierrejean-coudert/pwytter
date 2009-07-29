#!/usr/bin/env python
# -*- coding: utf-8 -*-

import identica
import tweetstore
import urllib2
import event

service_string = "Identi.ca"

"""
This implementation uses a twitter module hacked to support identi.ca
Please fix bugs in this file in the twitteraccount module too.

This uses the twitter API available from identi.ca

See: http://www.dilella.org/?p=65
"""

class IdenticaAccount(tweetstore.Account):
	__api = None
	_user = None
	_status = "unconfigured"
	def __init__(self, username, password, owner, callback):
		"""	Creates an instance of IdenticaAccount
			username: Identi.ca username
			password: Identi.ca password
			owner: TweetStore you want this Account added to
			callback:	Callback for once this instance have attempted login
					Callback gets two parameters (self, success, message), bool and str
					Display message if success is False

			Remark: This instance may not be invoked untill callback have returned! It will be so on UI thread.
		"""
		assert isinstance(owner, tweetstore.TweetStore), "store must be an instance of TweetStore"
		self._username = username
		self._password = password
		self._store = owner
		self.__api = identica.Api(self._username, self._password, twitterserver='identi.ca/api')
		self.__serivceID = self._store._getServiceID(service_string)
		self.__loginCB = event.Event()
		self.__loginCB += callback
		self._status = "updating"
		#Create user in case we get an exception during download of real user
		self._user = tweetstore.User(self._store, self._username, service_string)
		self.__initialize()

	@tweetstore.asynchronous
	def __initialize(self):
		try:
			self._user = self.__parseUser(self.__api.GetUser(self._username))
		except urllib2.HTTPError, e:
			if e.code == 401:
				self.__loginCB.raiseEvent(False, "Authendication failed, ensure you entered the correct password")
			else:
				self.__loginCB.raiseEvent(False, "Login failed: " + str(e))
		except urllib2.URLError:
			self.__loginCB.raiseEvent(False, "Login failed, ensure internet connection\n error: " + str(e))
		except BaseException, e:
			self.__loginCB.raiseEvent(False, "Login failed: " + str(e))
		self._status = "idle"
		self._store._addAccount(self)
		self.__loginCB.raiseEvent(self, True, "Login successful")

	_store = None
	def _setOwner(self, store):
		assert isinstance(store, tweetstore.TweetStore), "Owner must be an instance of TweetStore"
		self._store = store

	def _getMessages(self):
		if not self._store: raise tweetstore.OwnerNotSetError, "Cannot created messages."
		self.__changeStatus("updating")
		try:
			#TODO: Use the since parameter and store it on the this class
			msgs = []
			for msg in self.__api.GetFriendsTimeline(self._username):
				msgs += [self.__parseMessage(msg)]
			for msg in self.__api.GetUserTimeline(self._username):
				msgs += [self.__parseMessage(msg)]
			for msg in self.__api.GetReplies():
				msgs += [self.__parseMessage(msg)]
			for msg in self.__api.GetDirectMessages():
				msgs += [self.__parseMessage(msg)]
		except urllib2.HTTPError, e:
			if e.code == 401:
				self.__changeStatus("bad authendication", True)
				return False
			else:
				raise e
		except urllib2.URLError:
			self.__changeStatus("offline")
			return False
		self.__changeStatus("idle")
		return msgs

	def _getFriends(self):
		if not self._store: raise tweetstore.OwnerNotSetError, "Cannot created User instances."
		self.__changeStatus("updating")
		try:
			friends = []
			for user in self.__api.GetFriends():
				friends += [self.__parseUser(user)]
		except urllib2.HTTPError, e:
			if e.code == 401:
				self.__changeStatus("bad authendication", True)
				return False
			else:
				raise e
		except urllib2.URLError:
			self.__changeStatus("offline")
			return False
		self.__changeStatus("idle")
		return friends
		
	def _getFollowers(self):
		if not self._store: raise tweetstore.OwnerNotSetError, "Cannot created User instances."
		self.__changeStatus("updating")
		try:
			followers = []
			for user in self.__api.GetFollowers():
				followers += [self.__parseUser(user)]
		except urllib2.HTTPError, e:
			if e.code == 401:
				self.__changeStatus("bad authendication", True)
				return False
			else:
				raise e
		except urllib2.URLError:
			self.__changeStatus("offline")
			return False
		self.__changeStatus("idle")
		return followers

	def _postMessage(self, message):
		if not self._store: raise tweetstore.OwnerNotSetError, "Cannot update account status changes."
		assert isinstance(message, tweetstore.Message), "message must be an instanc of Message"
		self.__changeStatus("updating")
		try:
			#TODO: Figure out how to post in reply to another message
			if message.getDirectAt() == None:
				msg = message.getMessage()
				if message.getReplyAt() != None and not msg.startswith("@" + message.getReplyAt().getUsername() + " "):
					msg = "@" + message.getReplyAt().getUsername() + " " + msg
				self.__api.PostUpdate(msg)
			else:
				self.__api.PostDirectMessage(message.getDirectAt().getUsername(), message.getMessage())
		except urllib2.HTTPError, e:
			if e.code == 401:
				self.__changeStatus("bad authendication", True)
				return False
			else:
				raise e
		except urllib2.URLError:
			self.__changeStatus("offline")
			return False
		self.__changeStatus("idle")
		return True

	def getStatus(self):
		"""Gets the status of this Account instance"""
		return self._status

	def getService(self):
		"""Gets the service type of this Account"""
		return service_string

	def getUser(self):
		"""Gets the user this Account instance is signed in with"""
		if self._user == None:
			if not self._store: raise tweetstore.OwnerNotSetError, "Cannot get User."
			user_id = self._store._getUserID(self._username, self._store._getServiceID(self.getService()))
			return self._store._getUser(user_id)
		return self._user

	def getCapabilities(self):
		"""Get account capabilities"""
		if not self._store: raise tweetstore.OwnerNotSetError, "Cannot assert capabilities without owner."
		return IdenticaCapabilities(self._store, self)

	def reauthendicate(password = None):
		"""Attempt login with another password

			To change username the account must be removed an a new account added
		"""
		if not self._store: raise tweetstore.OwnerNotSetError, "Cannot update account status changes."
		if password == None:
			password = self._password
		self.__api = identica.Api(self._username, password, twitterserver='identi.ca/api')
		self._store._updateAccount(self)
		self._store.sync(self)

	def __getstate__(self):
		data = {}
		data["username"] = self._username
		data["password"] = self._password
		return data

	def __setstate__(self, data):
		self._username = data["username"]
		self._password = data["password"]
		self._status = "offline"
		self._store = None
		self.__api = identica.Api(self._username, self._password, twitterserver='identi.ca/api')
		
	def __changeStatus(self, status, force = False):
		if force or self._status != status:
			self._status = status
			self._store.onStatusChange.raiseEvent(self, status)

	def __parseUser(self, user):
		return IdenticaUser(self._store, user)

	def __parseMessage(self, msg):
		return IdenticaMessage(self._store, self.__api, msg)


class IdenticaUser(tweetstore.User):
	"""Wrapper around identica.User"""
	def __init__(self, store, user):
		"""	Initialize a new identica user from an instance of identica.User
		"""
		assert isinstance(store, tweetstore.TweetStore), "store must be an instance of TweetStore"
		assert isinstance(user, identica.User), "user must be an instance of identica.User"
		self.__store = store
		self.__user = user
		self._image_id = self.__store._cacheImage(user.GetProfileImageUrl())
		self._service_id = None

	def getName(self):
		"""Gets the name of this user"""
		return self.__user.GetName()

	def getUsername(self):
		"""Gets the username of this user"""
		return self.__user.GetScreenName()

	def getService(self):
		"""Gets the service this user exists on"""
		return service_string

	def getUrl(self):
		"""Get a url to the user page"""
		return self.__user.GetUrl()

	def getLocation(self):
		"""Gets the location of the user"""
		return self.__user.GetLocation()

	def getDescription(self):
		"""Gets the user decription"""
		return self.__user.GetDescription()

	def getImage(self):
		"""Gets a binary image"""
		return self.__store._getImage(self._getImageID())

	def _getServiceID(self):
		"""Gets the service ID for this user"""
		if not self._service_id:
			self._service_id = self.__store._getServiceID(self.getService())
		return self._service_id

	def _getImageID(self):
		"""Get image id of image for this user"""
		return self._image_id

class IdenticaMessage(tweetstore.Message):
	"""Wrapper around identica.Status and identica.DirectMessage"""
	def __init__(self, store, api, message):
		assert isinstance(store, tweetstore.TweetStore), "store must be an instance of TweetStore"
		self.__store = store
		assert isinstance(api, identica.Api), "api must be an instance of identica.Api"
		assert isinstance(message, (identica.Status, identica.DirectMessage)), "message must be an instance of identica.Status or identica.DirectMessage"
		self.__message = message
		self._service_id = None
		#Check if it is a direct message
		if isinstance(message, identica.DirectMessage):
			self._user = IdenticaUser(store, api.GetUser(message.GetSenderScreenName()))
			self._direct_at = IdenticaUser(store, api.GetUser(message.GetRecipientScreenName()))
			self._reply_at = None
		else:
			#If it's a status
			self._user = IdenticaUser(store, message.GetUser())
			self._direct_at = None
			#Check if this is a reply
			if self.getMessage().startswith("@"):
				try:
					username = self.getMessage().split(" ", 1)[0][1:]
					self._reply_at = IdenticaUser(store, api.GetUser(username))
				except:
					self._reply_at = None
			else:
				self._reply_at = None
		#TODO: Figure out how to get reply to parameter if it exists for identica
		self._reply_to = None

	def getMessage(self):
		"""Gets the message text"""
		return self.__message.GetText()
	
	def _getServiceUniqueId(self):
		"""Gets a message ID unique for this service"""
		return self.__message.GetId()

	def getCreated(self):
		"""Gets the time of when this message was created"""
		return self.__message.GetCreatedAtInSeconds()
	
	def getUser(self):
		"""Gets the User who posted this message"""
		return self._user
	
	def getReplyAt(self):
		"""Gets the user this is a reply at, None if this is not a reply"""
		return self._reply_at

	def isReply(self):
		"""True if this message is a reply"""
		return self._reply_at != None

	def getReplyTo(self):
		"""Gets the message this is a reply to, None if none"""
		return self._reply_to

	def getDirectAt(self):
		"""User this message is direct at, None if this is not a direct message"""
		return self._direct_at

	def isDirectMessage(self):
		"""True if this a direct message"""
		return self._direct_at != None

	def getService(self):
		"""Gets the service on which this message exists"""
		return service_string

	def _getServiceID(self):
		"""Get unique identifier for the service this message is hosted in"""
		if not self._service_id:
			self._service_id = self.__store._getServiceID(self.getService())
		return self._service_id

class IdenticaCapabilities(tweetstore.AccountCapabilities):
	def __init__(self, store, account):
		assert isinstance(store, tweetstore.TweetStore), "store must be an instance of tweetstore"
		self._store = store
		self._account = account
	
	def canReply(self, user, message = None):
		return user.getService() == service_string
	
	def replyPrefix(self, user):
		return "@" + user.getUsername() + " "
		
	def isReplyPrefix(self, text):
		if text.startswith("@"):
			parts = text[1:].split(" ")
			if len(parts) == 1:
					return False
			return tweetstore.User(self._store, parts[0], service_string)
		return False
	
	def canDirect(self, user, message = None):
		#Identica accounts can only send direct message to people who follow them
		return self._store.isFollower(user, self._account)
	
	#TODO: Consider support the "d <username>" prefix, do it if serverside of webservices do
	def directPrefix(self, user):
		return u""
		
	def isDirectPrefix(self, text):
		return False
	
	def updateMessageSize(self):
		return 140
		
	def replyMessageSize(self):
		return 140
		
	def directMessageSize(self):
		return 140
