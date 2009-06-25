#!/usr/bin/env python
# -*- coding: utf-8 -*-

import twitter
import tweetstore
import urllib2
import event

service_string = "Twitter"

"""
Notes:

Twitter test user:

username:	pwdebug
password:	pwytter

Use this user to test things... The account already follower Jessica Simpson so anything posted
can't possibly make it worse.
"""

class TwitterAccount(tweetstore.Account):
	__api = None
	_user = None
	_status = "unconfigured"
	def __init__(self, username, password, owner, callback):
		"""	Creates an instance of TwitterAccount
			username: Twitter username
			password: Twitter password
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
		self.__api = twitter.Api(self._username, self._password)
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
				self.__loginCB.raiseEvent(self, False, "Authendication failed, ensure you entered the correct password")
			else:
				self.__loginCB.raiseEvent(self, False, "Login failed: " + str(e))
		except urllib2.URLError:
			self.__loginCB.raiseEvent(self, False, "Login failed, ensure internet connection\n error: " + str(e))
		except BaseException, e:
			self.__loginCB.raiseEvent(self, False, "Login failed: " + str(e))
		else:
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

	def reauthendicate(password = None):
		"""Attempt login with another password

			To change username the account must be removed an a new account added
		"""
		if not self._store: raise tweetstore.OwnerNotSetError, "Cannot update account status changes."
		if password == None:
			password = self._password
		self.__api = twitter.Api(self._username, password)
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
		self.__api = twitter.Api(self._username, self._password)
		
	def __changeStatus(self, status, force = False):
		if force or self._status != status:
			self._status = status
			self._store.onStatusChange.raiseEvent(self, status)

	def __parseUser(self, user):
		return TwitterUser(self._store, user)

	def __parseMessage(self, msg):
		return TwitterMessage(self._store, self.__api, msg)


class TwitterUser(tweetstore.User):
	"""Wrapper around twitter.User"""
	def __init__(self, store, user):
		"""	Initialize a new Twitter user from an instance of twitter.User
		"""
		assert isinstance(store, tweetstore.TweetStore), "store must be an instance of TweetStore"
		assert isinstance(user, twitter.User), "user must be an instance of twitter.User"
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

class TwitterMessage(tweetstore.Message):
	"""Wrapper around twitter.Status and twitter.DirectMessage"""
	def __init__(self, store, api, message):
		assert isinstance(store, tweetstore.TweetStore), "store must be an instance of TweetStore"
		self.__store = store
		assert isinstance(api, twitter.Api), "api must be an instance of twitter.Api"
		assert isinstance(message, (twitter.Status, twitter.DirectMessage)), "message must be an instance of twitter.Status or twitter.DirectMessage"
		self.__message = message
		self._service_id = None
		#Check if it is a direct message
		if isinstance(message, twitter.DirectMessage):
			self._user = TwitterUser(store, api.GetUser(message.GetSenderScreenName()))
			self._direct_at = TwitterUser(store, api.GetUser(message.GetRecipientScreenName()))
			self._reply_at = None
		else:
			#If it's a status
			self._user = TwitterUser(store, message.GetUser())
			self._direct_at = None
			#Check if this is a reply
			if self.getMessage().startswith("@"):
				try:
					username = self.getMessage().split(" ", 1)[0][1:]
					self._reply_at = TwitterUser(store, api.GetUser(username))
				except:
					self._reply_at = None
			else:
				self._reply_at = None
		#TODO: Figure out how to get reply to parameter if it exists for twitter
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
