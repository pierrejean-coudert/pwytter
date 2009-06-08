#!/usr/bin/env python
# -*- coding: utf-8 -*-

import twitter
import tweetstore
import urllib2
import event

__service = "Twitter"

#TODO: Cleanup and rewrite this class to match the new scheme.

class TwitterAccount(tweetstore.Account):
	_service = "Twitter"
	__api = None
	_user = None
	_status = "unconfigured"
	def __init__(self, username, password, store, callback):
		"""	Creates an instance of TwitterAccount
			username: Twitter username
			password: Twitter password
			store: TweetStore you want this Account added to
			callback:	Callback for once this instance have attempted login
					Callback gets two parameters (success, message), bool and str
					Display message if success is False

			Remark: This instance may not be invoked untill callback have returned! It will be so on UI thread.
		"""
		assert isinstance(store, tweetstore.TweetStore), "store must be an instance of TweetStore"
		self._username = username
		self._password = password
		self._store = store
		self.__api = twitter.Api(self._username, self._password)
		self.__serivceID = self._store.getServiceID(__service)
		self.__loginCB = event.Event()
		self.__loginCB += callback
		self._status = "updating"
		#TODO: Do this on a thread!
		try:
			self.__api.getFriends()	#Checks if we're logged in
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
		self.__loginCB.raiseEvent(True, "Login successful")

	__lastPublicTimelineID = None
	def _getMessages(self):
		try:
			msgs = []
			rawdata = self.__api.GetPublicTimeline(self.__lastPublicTimelineID)
			for msg in rawdata:
				msgs += [self.__parseMessage(msg)]
				self.__lastPublicTimelineID = msg.GetId()
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

	def _postMessage(self, message, user = None):
		assert isinstance(message, tweetstore.Message), "message must be an instanc of Message"
		assert user == None or isinstance(user, tweetstore.User), "user must be none or instance of User"
		try:
			if user = None:
				self.__api.PostUpdate(message.getMessage())
			else
				self.__api.PostDirectMessage(user.getUsername(), message.getMessage())
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
		return self._status

	def getService(self):
		return __service

	def getUser(self):
		if self._user == None:
			users = self._store.getUsers(self._username, service_id = self._serviceID)
			assert users != [], "The user associated with an Account should be in database"
			assert len(users) == 1, "There shouldn't be more than one user when username and serivce identifier is specified"
			self._user = users[0]
		return self._user

	def reauthendicate(password = None):
		if password == None:
			password = self.password
		self.__api = twitter.Api(self.username, password)
		self._store._updateAccount(self)
		self._store.sync(self)

	def __getstate__(self):
		data = {}
		data["username"] = self._username
		data["password"] = self._password
		data["serviceID"] = self._serviceID
		return data

	def __setstate__(self, data):
		self._username = data["username"]	#TODO: Remember _store must be set from TweetStore
		self._password = data["password"]
		self._serviceID = data["serviceID"]
		self._status = "offline"
		self.__api = twitter.Api(self.username, password)
		
	def __changeStatus(self, status, force = False):
		if force or self.status != status:
			self.status = status
			self._store.onStatusChange.raiseEvent(self, status)

	def __parseUser(self, user):
		assert isinstance(user, twitter.User), "Parameter user must be of type twitter.User"
		name = user.GetName()
		username = user.GetScreenName()
		url = user.GetUrl()
		description = user.GetDescription()
		location = user.GetLocation()
		image_url = user.GetProfileImageUrl()
		image_id = self._store._catchImage(image_url)
		return tweetstore.User(name, username, self.getService(), url, location, description, image_id, self._store)

	def __parseMessage(self, msg):
		assert isinstance(msg, twitter.Status), "msg must be an instance of twitter.Message"
		user = self.__parseUser(msg.GetUser())
		return tweetstore.Message(msg.GetText(), msg.GetCreatedAtInSecounds(), user, self.getService())

#TODO: Use this base class of tweetstore.Message to parse twitter messages
class Message(tweetstore.Message):
	def __init__(self, message, store):
		assert isinstance(msg, twitter.Status), "msg must be an instance of twitter.Message"
		self._user = User(msg.GetUser(), store)
		self._message = msg.GetText()
		self._created = msg.GetCreatedAtInSecounds()
		self._suid = msg.GetId()

	def getCreated(self):
		"""Gets the time of when this message was created"""
		return self._created
	
	def getUser(self):
		"""Gets the User who posted this message"""
		return self._user
	
	def getService(self):
		"""Gets the service on which this message exists"""
		return __service


