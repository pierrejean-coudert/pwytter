#!/usr/bin/env python
# -*- coding: utf-8 -*-

import threading
from event import Event
import pickle
import database
from urllib2 import urlopen
import time

"""
Database tables:

tweets:
	id			message id
	message		text
	created		timestamp
	user		user id
	suid		service unique id, a unique id for this message on its service
	service		service id, this message exists on

users:
	id			user id
	name		
	username
	url
	decription
	location
	image		image id
	service		service id, this user exists on

images:
	id			image id
	url
	cached		timestamp
	image		BLOB or path to cached file


accounts:
	id			account id
	data		pickled instance of a subclass of Account
	service		service id

friends:
	id			user id
	account		account id

followers:
	id			user id
	account		account id

services:
	id			service id
	service		service name as text string

actions:
	id
	type		Text type of action, post_message, remove_friend, etc. that tells how param is to be treated
	param		some kind of data
	account		account id the action should be performed on


The TODO list:

public methods for tweetstore:
	addAccount()
	getMessages(newer = None, older = None, account = None, service = None, page = 0, page_size = -1)
	getFriends(account = None, service = None, page = 0, page_size = -1)
	getFollowers(account = None, service = None, page = 0, page_size = -1)
	getUsers(username = None, account = None, service = None, page = 0, page_size = -1)

Remove usage of TweetStore._getUsers() in:
	Message
	User
	Account

Update:
	twitter account type
	mockup account type

Fix serialization of:
	Message
	User

Save settings:
	TweetStore._cacheTimeout
	TweetStore._accounts, must be pickled and stored in database

Figure out what and how to add extra views etc. for instance integrate search feature.
"""

def asynchronous(f):
	"""Creates a threaded wrapper around f
		this method is used decorator to perform a method or 
		function on a thread. E.g. write:
		 @asynchronous
		 def myThreadFunc():
		 	#Something time consuming
		See: http://www.oreillynet.com/onlamp/blog/2006/07/pygtk_and_threading.html
		And: http://amix.dk/blog/viewEntry/19346
	"""
	def wrapper(*args):
		t = threading.Thread(target=f, args=args)
		t.start()
	return wrapper


class TweetStore:
	"""	Pwytter backend that manages accounts, connections, threading and database storage."""

	def __init__(self, database_path = ":memory"):
		"""Initialize an instance of TweetStore"""
		#Create/connect to database
		assert isinstance(database_path, basestring), "dbpath is not a string"
		self.__db = ThreadSafeDatabase(database_path)
		self.__database_path = database_path

		#Check that tables are present if not create them
		tables = []
		for row in self.__db.execute("SELECT name from sqlite_master WHERE type='table'"):
			tables += [row["name"]]
		if "tweets" not in tables:
			self.__db.execute("""
				CREATE TABLE tweets(
					id			INTEGER PRIMARY KEY,
					message		TEXT,
					created		INT,
					user		INT,
					suid		INT,
					service		INT)""")
		if "users" not in tables:
			self.__db.execute("""
				CREATE TABLE users(
					id			INTEGER PRIMARY KEY,
					name		TEXT,
					username	TEXT,
					url			TEXT
					decription	TEXT,
					location	TEXT,
					image		INT,
					service		INT)""")
		if "images" not in tables:
			self.__db.execute("""
				CREATE TABLE images(
					id			INTEGER PRIMARY KEY,
					url			TEXT,
					cached		INT,
					image		BLOB)""")
		if "accounts" not in tables:
			self.__db.execute("""
				CREATE TABLE accounts(
					id			INTEGER PRIMARY KEY,
					data		TEXT,
					service		INT)""")
		if "friends" not in tables:
			self.__db.execute("""
				CREATE TABLE friends(
					id			INT,
					account		INT)""")
		if "followers" not in tables:
			self.__db.execute("""
				CREATE TABLE followers(
					id			INT,
					account		INT)""")
		if "services" not in tables:
			self.__db.execute("""
				CREATE TABLE services(
					id			INTEGER PRIMARY KEY,
					service		TEXT)""")
		if "actions" not in tables:
			self.__db.execute("""
				CREATE TABLE actions(
					id			INTEGER PRIMARY KEY,
					type		TEXT,
					param		TEXT,
					account		INT)""")
		#TODO: load accounts from database
		#TODO: Give loaded accounts an instance of self as _store attribute

	@asynchronous
	def sync(self, account = None):
		"""	Synchronous database with services from one or all accounts
			account: The account to synchronize, defaults to synchronizing all accounts
		"""
		#If no account is specified sync all accounts in parallel
		if not account:
			for account in self.getAccounts():
				self.sync(account)
		else:
			assert isinstance(account, Account), "Cannot sync object that is not an instance of Account"
			#Synchronize, while aborting if user interaction is needed
			if not self._syncActions(account): return
			if not self._syncMessage(account): return
			if not self._syncFriends(account): return
			if not self._syncFollowers(account): return

	def _syncActions(self, account):
		"""	Execute actions stored locally on account

			When a tweet is posted, a friend added or other actions is performed it is stored in
			local database and then performed remotely when this method is called. Doing this
			enables offline usage.

			Return:	This method returns False on account error, e.g. service error, missing connection
					or bad authendication which requires user interaction, e.g. further synchronization
					should not be attempted, if this method returns False.
		"""
		for action in self.__db.execute("SELECT id, type, param FROM actions WHERE account = ?", account._getAccountID()):
			if action["type"] == "post_message":
				param = pickle.loads(actions["param"])
				if not account._postMessage(param["message"], param["user"]): return False
				self.__db.execute("DELETE FROM actions WHERE id = ?", action["id"])
			pass #TODO: Handle actions here
		return True
		

	def _syncMessage(self, account):
		"""	Synchronize messages from specified account

			Returns	False on transmission error, e.g. service error, missing connection or bad authendication.
					If false is return the account should not be attempted synchronized any further as user
					interaction is necessary.

			Note: This method operates synchronously, consumers of TweetStore should use sync() method
		"""
		assert isinstance(account, Account), "Cannot sync object that is not an instance of Account"
		msgs = account._getMessages()
		if msgs == False: return False
		for msg in msgs:
			self.__cacheMessage(msg)
		return True

	def _syncFriends(self, account):
		"""	Synchronize friends from specified account

			Returns	False on transmission error, e.g. service error, that requires user interaction.
			Note: This method operates synchroniously, consumers of TweetStore should not interface
			this method.
		"""
		assert isinstance(account, Account), "Cannot sync object that is not an instance of Account"
		friends = account._getFriends()
		if friends == False: return False
		#Get ids for the friend that the account returned
		friend_ids = []
		for friend in friends:
			friend_ids += [self.__cacheUser(friend)]
		account_id = account._getAccountID()
		for friend in self.__db.execute("SELECT id from friends WHERE account = ?", account_id):
			#Remove friends already associated from friend_ids and delete friends not in friend_ids
			if friend["id"] in friend_ids:
				friend_ids -= friend["id"]
			else:
				self.__db.execute("DELETE FROM friends WHERE account = ? AND id = ?", account_id, friend)
		#Insert new friends
		for friend in friend_ids:
			self.__db.execute("INSERT INTO friends (id, account) VALUES (?,?)", friend, account_id)
		return True

	def _syncFollowers(self, account):
		"""	Synchronize Followers from specified account

			Returns	False on transmission error, e.g. service error, that requires user interaction.
			Note: This method operates synchroniously, consumers of TweetStore should not interface
			this method.
		"""
		assert isinstance(account, Account), "Cannot sync object that is not an instance of Account"
		followers = account._getFollowers()
		if followers == False: return False
		#Get ids for the followers that the account returned
		follower_ids = []
		for follower in followers:
			follower_ids += [self.__cacheUser(follower)]
		account_id = account._getAccountID()
		for follower in self.__db.execute("SELECT id from followers WHERE account = ?", account_id):
			#Remove followers already associated from follower_ids and delete followers not in follower_ids
			if follower["id"] in follower_ids:
				follower_ids -= follower["id"]
			else:
				self.__db.execute("DELETE FROM followers WHERE account = ? AND id = ?", account_id, follower)
		#Insert new followers
		for follower in follower_ids:
			self.__db.execute("INSERT INTO followers (id, account) VALUES (?,?)", follower, account_id)
		return True

	def __cacheMessage(self, message):
		"""	Add a message to database if it is not already there
			returns the id of the message
		"""
		assert isinstance(message, Message), "message must be an instance of Message"
		created = message.getCreated()
		suid = message._getServiceUniqueId()
		service = message._getServiceID(self)
		msgtext = message.getMessage()
		userid = self.__cacheUser(message.getUser())
		for msg in self.__db.execute("SELECT id, message, user FROM tweets WHERE created = ? AND suid = ? AND service = ?", created, suid, service):
			if msg["message"] == msgtext and msg["user"] == userid:
				return msg["id"]
		return self.__db.execute("INSERT INTO tweets (message, created, user, suid, service) VALUES (?,?,?,?,?)", msgtext, created, userid, suid, service)

	def __cacheUser(self, user):
		"""	Add a user to database if it is not already there
			returns the id of the user
		"""
		assert isinstance(user, User), "user must be an instance of User"
		username = user.getUsername()
		service = user._getServiceID(self)
		img_id = user._getImageID()
		users = self.__db.fetchall("SELECT * FROM users WHERE username = ? AND service = ?", username, service)
		assert len(users) < 2, "Only one user with the same username and service should exist in the database"
		if len(users) == 0:
			params = [user.getName(), username, user.getUrl(), user.getDescription(), user.getLocation(), img_id, service]
			return self.__db.execute("INSERT INTO users (name, username, url, description, location, image, service ) values (?,?,?,?,?,?,?)", *params)
		fields = []
		params = []
		if users[0]["name"] != user.getName():
			fields += ["name"]
			params += [user.getName()]
		if users[0]["url"] != user.getUrl():
			fields += ["url"]
			params += [user.getUrl()]
		if users[0]["description"] != user.getDescription():
			fields += ["description"]
			params += [user.getDescription()]
		if users[0]["location"] != user.getLocation():
			fields += ["location"]
			params += [user.getLocation()]
		if users[0]["image"] != img_id:
			fields += ["image"]
			params += [img_id]
		if len(fields) > 0:
			sql = "UPDATE"
			for field in fields:	Message.getImage(store)
				sql += " SET " + field + " = ?"
			params += [username, service]
			sql += " WHERE username = ? AND service = ?"
			self.__db.execute(sql, *params)
		return users[0]["id"]

	@asynchronous
	def postMessage(self, account, message, user = None):
		"""	Post a message from an account to an optional user

			account:	Account the message should be posted to
			message:	Message instance to be posted
			user:		User to post this message to, default to None
						which posts it as an update.

			Note: This method operates asynchronously, and if message cannot be
			posted immidiately it will be stored in database and posted later.
		"""
		assert isinstance(account, Account), "account must be an instance of Account"
		assert isinstance(message, Message), "message must be an instance of Message"
		assert user == None or isinstance(user, User), "User must be None or an instance of User"
		if not account._postMessage(message, user):
			param = pickle.dumps({"message": message, "user" : user})
			self.__db.execute("INSERT INTO actions (type, param) VALUES (?, ?)", "post_message", param)

	def getAccounts(self, service = None, service_id = None):
		"""	Get accounts managed by this instance
			service: Specifiy which type of accounts is desired (optional)
			service_id: Id of the desired service type (optional)
		"""
		if service == None and service_id == None:
			return self._accounts
		elif service_id != None:
			assert isinstance(service_id, (int, long)), "service_id must be an integer"
			service = self.getService(service_id)
		else:
			assert isinstance(service, basestring), "service must be a string"
			accounts = []
			for account in self._accounts:
				if account.getService() == service:
					accounts += [account]
			return accounts

	def _catchImage(self, url):
		"""	Catch an image and return an id for it
		"""
		assert isinstance(url, basestring), "url must be a string"
		identifier = self.__db.fetchone("SELECT id, cached FROM images WHERE url = ? LIMIT 1", url)
		if not identifier:
			data = openurl(url).read()
			return self.__db.execute("INSERT INTO images (url, cached, image) VALUES (?, ?, ?)", url, time.time(), data)
		elif time.time() - identifier["cached"] > self.getCacheTimeout():
			data = openurl(url).read()
			self.__db.execute("UPDATE images SET image = ?, cached = ? WHERE id = ?", data, time.time(), identifier["id"])
		return identifier["id"]
	
	def _getImage(self, identifier):
		""" Get image from catch
		"""
		assert isinstance(identifier, (int, long)), "Image identifier must be an integer."
		#Connect to database and get the image
		image = self.__db.fetchone("SELECT image FROM images WHERE id = ? LIMIT 1", identifier)
		#If image is not in database
		assert image != None, "Image not found in database"
		if not image:
			return None	#TODO: Return some default image
		#If it was in database
		return image["image"]

	_cacheTimeout = 2678400
	def setCacheTimeout(self, timeout = 2678400):
		"""Set timeout for image cache in seconds
		"""
		self._cacheTimeout = timeout

	def getCacheTimeout(self):
		"""Get timeout for image cache in seconds
		"""
		return self._cacheTimeout

	def _getServiceID(self, service):
		"""	Gets a service ID, and registers it if not present
		"""
		assert isinstance(service, basestring), "service parameter must be a string"
		#Check if it is in database
		identifier = self.__db.fetchone("SELECT id FROM services WHERE service = ? LIMIT 1", service)
		#If not in database insert it
		if identifier == None:
			return self.__db.execute("INSERT INTO services (service) VALUES (?)", service)
		return identifier["id"]

	def _getService(self, identifier):
		"""	Gets a service name as string from an identifier
		"""
		assert isinstance(identifier, int), "Service identifier must be an integer"
		service = self.__db.fetchone("SELECT serivce FROM services WHERE id = ? LIMIT 1", identifier)
		if service == None:
			raise Exception, "Service does not exist in database"
		return service["id"]

	def _addAccount(self, account):
		pass	#See notes
		#Add to internal list
		#Add Account.GetUser() to database!

	def _getUser(self, identifier):
		"""	Get a user based on user id in database
		"""
		assert isinstance(identifier, (int, long)), "identifier must be an integer"
		user = self.__db.fetchone("SELECT * FROM users WHERE id = ? LIMIT 1", identifier)
		if not user:
			raise Exception, "Userid does not exists in database"
		return User(user["name"], user["username"], self._getService(user["service"]), user["url"], user["location"], user["description"], user["image"], user["service"])

	def _getUserID(self, username = None, service = None):
		"""	Gets a user id from username and service
			username:	Username of the user, who's id is wanted
			service:	Service unique string or integer identifier for the service

			return:	The internal database id of the user
		"""
		assert isinstance(username, basestring), "username must be a string"
		assert isinstance(service, (int, long, basestring), "service must be either an integer identifier or a service string."
		if isinstance(service, basestring):
			service = self._getServiceID(service)
		userid = self.__db.fetchone("SELECT id from users WHERE username = ? AND service = ? LIMIT 1", username, service)
		if not userid:
			raise Exception, "User not found in database"
		return userid["id"]

class User:
	def __init__(self, name, username, service, url, location, description, image_id, service_id = None):
		assert isinstance(store, TweetStore), "store must be an instance of TweetStore"
		assert isinstance(service, basestring, "service must be a string"
		self._service = service
		self.__image_id = image_id
		self._name = name
		self._username = username
		self._url = url
		self._location = location
		self._description = description
		self._service_id = service_id

	def getName(self):
		"""Gets the name of this user"""
		return self._name

	def getUsername(self):
		"""Gets the username of this user"""
		return self._username

	def getService(self):
		"""Gets the service this user exists on"""
		return self._service

	def getUrl(self):
		"""Get a url to the user page"""
		return self._url

	def getLocation(self):
		"""Gets the location of the user"""
		return self._location

	def getDescription(self):
		"""Gets the user decription"""
		return self._description

	def getImage(self, store):
		"""Gets a binary image"""
		assert isinstance(store, TweetStore), "store must be an instance of TweetStore"
		return store._getImage(self.getImageID())

	def _getServiceID(self, store):
		"""Gets the service ID for this user"""
		if not self._service_id:
			assert isinstance(store, TweetStore), "store must be an instance of TweetStore"
			self._service_id = store._getServiceID(self.getService())
		return self._service_id

	def _getImageID(self):
		"""Get image id of image for this user"""
		return self.__image_id

	def __str__(self):
		"""Get string representation of this user on this service"""
		return self.getUsername() + " - " + self.getService()

	def __getstate__(self):
		data = {}
		data["name"] = self.getName()
		data["username"] = self.getUsername()
		data["url"] = self.getUrl()
		data["location"] = self.getLocation()
		data["description"] = self.getDescription()
		data["image_id"] = self._getImageID()
		data["service"] = self.getService()
		return data

	def __setstate__(self, data):
		self._service = data["service"]
		self.__image_id = data["image_id"]
		self._name = data["name"]
		self._username = data["username"]
		self._url = data["url"]
		self._location = data["location"]
		self._description = data["description"]
		self._service_id = None

class Message:
	def __init__(self, msg, created, user, suid, service, service_id = None):
		assert isinstance(msg, basestring), "msg must be string"
		assert isinstance(user, User), "user must be an instance of User"
		assert isinstance(suid, (int, long)), "Service Unique Id (suid) must be an integer"
		assert isinstance(service, basestring), "service must be string"
		self._message = msg
		self._created = created
		self._user = user
		self._service = service
		self._suid = suid
		self._service_id = service_id
	
	def getMessage(self):
		"""Gets the message text"""
		return self._message
	
	def _getServiceUniqueId(self):
		"""Gets a message ID unique for this service"""
		return self._suid

	def getCreated(self):
		"""Gets the time of when this message was created"""
		return self._created
	
	def getUser(self):
		"""Gets the User who posted this message"""
		return self._user
	
	def getService(self):
		"""Gets the service on which this message exists"""
		return self._service

	def _getServiceID(self, store):
		"""Get unique identifier for the service this message is hosted in"""
		if not self._service_id:
			assert isinstance(store, TweetStore), "store must be an instance of TweetStore"
			self._service_id = store._getServiceID(self.getService())
		return self._service_id
		
class Account:
	def _getMessages(self):
		"""Returns messages in a list of tuples: [(message, created, username, account), ] or False
		If false is return user interaction is needed and status have been change to reflect this."""
		raise NotImplementedError, "_getMessages must be overwritten in subclasses of Account"

	def _getFriends(self):
		"""Returns friends in a list of User or False
		If False is returned user interactions is required to fix the problem.
		E.g. connection must be restored or account reauthendicated, anyway synchronization of 
		this account shouldn't preceed."""
		raise NotImplementedError, "_getFriends must be overwritten in subclasses of Account"
	
	def _getAccountID(self):
		raise NotImplementedError, "_getAccountID must be overwritten in subclasses of Account"

	def _setOwner(self, store):
		raise NotImplementedError, "_setOwner must be overwritten in subclasses of Account"

	def _getFollowers(self):
		"""Get followers as a list of followers"""
		raise NotImplementedError, "_getFollowers must be overwritten in subclasses of Account"

	def _postMessage(self, message, user = None):
		"""Post a message, as message or as update"""
		raise NotImplementedError, "_postMessage must be overwritten in subclasses of Account"

	def reauthendicate(password = None):
		"""Reauthendicate, called if status = 'bad authendication'
		Note this method changes password, if login is successful"""
		raise NotImplementedError, "reauthendicate must be overwritten in subclasses of Account"

	def __str__(self):
		"""Get string representation of this account, e.g. the user"""
		return str(self.getUser)

	def getUser(self):
		"""Gets the user of this account"""
		raise NotImplementedError, "getUser must be overwritten in subclasses of Account"

	def getService(self):
		"""Gets the name of the service that this account is connected to"""
		raise NotImplementedError, "getService must be overwritten in subclasses of Account"

	def getStatus(self):
		"""	Gets the current status of this account
			Can return:
			 * unconfigured
			 * offline
			 * idle
			 * updating
			 * bad authendication
		"""
		raise NotImplementedError, "getStatus must be overwritten in subclasses of Account"




