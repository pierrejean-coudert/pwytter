# -*- coding: utf-8 -*-

import threading
from event import Event
import pickle
from database import ThreadSafeDatabase
from urllib2 import urlopen
import time
import urllib
import sqlite3

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

replies:
	id			Tweet id
	reply_to	Tweet id this is a reply to, 0 if none
	direct_at	User id this is a reply at

direct_messages:
	id			Tweet id
	reply_to	Tweet id this is a reply to, 0 if none
	direct_at	User id this is a reply at

settings:
	key
	value

notification_blacklist:
	id				User id
	blacklisted		Bool, true if user is blacklisted, false if user is not blacklisted.

The TODO list:
	notification_blacklist		list of user identifiers no notifications are wanted for.
	settings_table				Settings for frontend, notifications settings (filter strings)
	onNewNotification
	refactor _syncMessages
		Add __newTweets = (), and __newReplies, etc.
		Add and integer called __synching_accounts = 0
			Add one to this when an account is being synchronized
			Remove one when account is done synchronizing
			When it hits 0, raise onNewTweets with __newTweets and argument, and clear __newTweets

public methods for tweetstore:
	BlockFollower(User)
	AddFriend(User)
	RemoveFriend(User)
	

Implement search queries
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

	onStatusChange = Event()
	"""Occurs whenever an account changes status
		Eventhandlers should take two parameters: account and status
	"""
	
	onSyncCompleted = Event()
	"""Occurs whenever synchronization have been completed.
	
		Note: If multiple calls to sync() is made before this event is called, this event will ONLY be raised one
		time, e.g. when all these synchronization requests have been completed.
		Eventhandlers should take any parameters to handle this event.
	"""

	onNewTweets = Event()
	"""Occurs whenever the onSyncCompleted is raised and there's new tweets in the timeline
		Eventhandlers should take a tuple of new tweets as parameter.
	"""
	
	onNewReplies = Event()
	"""Occurs whenever the onSyncCompleted is raised and there's a new reply at the user of the account
		Eventhandlers should take a tuple of new replies as parameter.
	"""
	
	onNewDirectMessages = Event()
	"""Occurs whenever the onSyncCompleted is raised and there's a new direct message at the user of the account
		Eventhandlers should take a tuple of new direct messages as parameter.
	"""

	onNewFollowers = Event()
	"""Occurs whenever the onSyncCompleted is raised and there's a new follower
		Eventhandlers should take a tuple of new followers as parameter.
	"""
	
	onNewFriends = Event()
	"""Occurs wheneverthe the onSyncCompleted is raised and there's a new friend
		Eventhandlers should take a tuple of new friends as parameter.
	"""
	
	settings = None
	"""Settings object that has string keys and object values, used to store settings.
		This is an instance of CatchedSettings, see it's documentation for more information.
	"""

	notification = None
	"""NotificationEngine for this instance of TweetStore, access this object to change
		notification settings and handle the onNotification event
		
		Note: This is an instance of NotificationEngine.
	"""

	def __init__(self, database_path = ":memory:"):
		"""Initialize an instance of TweetStore"""
		#Create/connect to database
		assert isinstance(database_path, basestring), "dbpath is not a string"
		self.__db = ThreadSafeDatabase(database_path)
		self.__database_path = database_path

		#Check that tables are present if not create them
		tables = ()
		for row in self.__db.execute("SELECT name from sqlite_master WHERE type='table'"):
			tables += (row["name"],)
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
					url			TEXT,
					description	TEXT,
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
		if "replies" not in tables:
			self.__db.execute("""
				CREATE TABLE replies(
					id			INT,
					reply_at	INT,
					reply_to	INT)""")
		if "direct_messages" not in tables:
			self.__db.execute("""
				CREATE TABLE direct_messages(
					id			INT,
					direct_at	INT,
					reply_to	INT)""")
		#Restore settings
		self.settings = CatchedSettings(self.__db)
		#Restore notification engine
		if "notification" in self.settings:
			self.notification = self.settings["notification"]
			self.notification._setOwner(self, self.__db)
		else:
			self.notification = NotificationEngine(self, self.__db)
		#Load accounts from database
		self.__restoreAccounts()

	def save(self):
		"""Save settings in database"""
		#Store notification engine
		self.settings["notification"] = self.notification
		#Store accounts and save database
		self.__storeAccounts()
		self.__db.commit()
		self.__db.close()
	
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
			#Start synchronization
			self.notification._beginSync()
			#Synchronize, while aborting if user interaction is needed
			try:
				run = self._syncActions(account)
				if run: run = self._syncFriends(account)
				if run: run = self._syncFollowers(account)
				if run: run = self._syncMessages(account)
				self.__db.commit()
			finally:
				#End synchronization
				self.notification._endSync()

	def _syncActions(self, account):
		"""	Execute actions stored locally on account

			When a tweet is posted, a friend added or other actions is performed it is stored in
			local database and then performed remotely when this method is called. Doing this
			enables offline usage.

			Return:	This method returns False on account error, e.g. service error, missing connection
					or bad authendication which requires user interaction, e.g. further synchronization
					should not be attempted, if this method returns False.
		"""
		for action in self.__db.execute("SELECT id, type, param FROM actions WHERE account = ?", self.__getAccountID(account)):
			if action["type"] == "post_message":
				if not account._postMessage(Message(self, data = action["param"])): return False
				self.__db.execute("DELETE FROM actions WHERE id = ?", action["id"])
			pass #TODO: Handle more actions here
		return True
		
	def _syncMessages(self, account):
		"""	Synchronize messages from specified account

			Returns	False on transmission error, e.g. service error, missing connection or bad authendication.
					If false is return the account should not be attempted synchronized any further as user
					interaction is necessary.

			Note: This method operates synchronously, consumers of TweetStore should use sync() method
		"""
		assert isinstance(account, Account), "Cannot sync object that is not an instance of Account"
		msgs = account._getMessages()
		if msgs == False: return False
		acUserID = self._getUserID(account.getUser().getUsername(), account.getService())
		acID = self.__getAccountID(account)
		for msg in msgs:
			#Cache the message, and check if it's a new message
			if self.__cacheMessage(msg):
				#If's a new reply at this account add it to new replies
				if msg.isReply() and msg.getReplyAt()._dbid == acUserID:
					self.notification._newReply(msg)
				#If it's a direct message to this account add it to new direct messages
				if msg.isDirectMessage() and msg.getDirectAt()._dbid == acUserID:
					self.notification._newDirectMessage(msg)
				#Check if it's in the timeline, if so, add it to the tuple of new tweets
				isOnTimeline = self.__db.fetchone("SELECT COUNT(id) FROM friends WHERE id = ? AND account = ?", msg.getUser()._dbid, acID)
				if isOnTimeline > 0:
					self.notification._newTweet(msg)
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
			self.__cacheUser(friend)
			friend_ids += [friend._dbid]
		account_id = self.__getAccountID(account)
		for friend in self.__db.execute("SELECT id from friends WHERE account = ?", account_id):
			#Remove friends already associated from friend_ids and delete friends not in friend_ids
			if friend["id"] in friend_ids:
				friend_ids.remove(friend["id"])
			else:
				self.__db.execute("DELETE FROM friends WHERE account = ? AND id = ?", account_id, friend)
		#Insert new friends
		for friend_id in friend_ids:
			self.__db.execute("INSERT INTO friends (id, account) VALUES (?,?)", friend_id, account_id)
		#For each friend that we've found
		for friend in friends:
			#Make a notification of new friends
			if friend._dbid in friend_ids:
				self.notification._newFriend(friend)
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
			self.__cacheUser(follower)
			follower_ids += [follower._dbid]
		account_id = self.__getAccountID(account)
		for follower in self.__db.execute("SELECT id from followers WHERE account = ?", account_id):
			#Remove followers already associated from follower_ids and delete followers not in follower_ids
			if follower["id"] in follower_ids:
				follower_ids.remove(follower["id"])
			else:
				self.__db.execute("DELETE FROM followers WHERE account = ? AND id = ?", account_id, follower["id"])
		#Insert new followers
		for follower_id in follower_ids:
			self.__db.execute("INSERT INTO followers (id, account) VALUES (?,?)", follower_id, account_id)
		#For each follower that we've found
		for follower in followers:
			#Make a notification of new followers
			if follower._dbid in follower_ids:
				self.notification._newFollower(follower)
		return True

	def __cacheMessage(self, message):
		"""	Add a message to database if it is not already there
			returns a boolean indicating if it was added to the cache
			
			Note: The database id of the cached message is added to the message instance as _dbid
		"""
		assert isinstance(message, Message), "message must be an instance of Message"
		created = message.getCreated()
		suid = message._getServiceUniqueId()
		service = message._getServiceID()
		msgtext = message.getMessage()
		user = message.getUser()
		self.__cacheUser(user)
		for msg in self.__db.execute("SELECT id, message, user FROM tweets WHERE created = ? AND suid = ? AND service = ?", created, suid, service):
			if msg["message"] == msgtext and msg["user"] == user._dbid:
				message._dbid = msg["id"]
				return False
		sql = "INSERT INTO tweets (message, created, user, suid, service) VALUES (?,?,?,?,?)"
		identifier = self.__db.execute(sql, msgtext, created, user._dbid, suid, service)
		message._dbid = identifier
		if message.isReply():
			at = message.getReplyAt()
			self.__cacheUser(at)
			to = message.getReplyTo()
			if to != None:
				self.__cacheMessage(to)
				to = to._dbid
			else:
				to = 0
			self.__db.execute("INSERT INTO replies (id, reply_at, reply_to) VALUES (?, ?, ?)", identifier, at._dbid, to)
		if message.isDirectMessage():
			at = message.getDirectAt()
			self.__cacheUser(at)
			to = message.getReplyTo()
			if to != None:
				self.__cacheMessage(to)
				to = to._dbid
			else:
				to = 0
			self.__db.execute("INSERT INTO direct_messages (id, direct_at, reply_to) VALUES (?, ?, ?)", identifier, at._dbid, to)
		return True

	def __cacheUser(self, user):
		"""	Add a user to database if it is not already there
			returns a boolean indicating whether it was just cached
			
			Note: The database id of the cached user is added to the user instance as _dbid
		"""
		assert isinstance(user, User), "user must be an instance of User"
		username = user.getUsername()
		service = user._getServiceID()
		img_id = user._getImageID()
		#TODO: Add a last_updated field to users table, and only update name, location etc. whenever this has expired
		users = self.__db.fetchall("SELECT * FROM users WHERE username = ? AND service = ?", username, service)
		assert len(users) < 2, "Only one user with the same username and service should exist in the database"
		if len(users) == 0:
			params = [user.getName(), username, user.getUrl(), user.getDescription(), user.getLocation(), img_id, service]
			user._dbid = self.__db.execute("INSERT INTO users (name, username, url, description, location, image, service ) values (?,?,?,?,?,?,?)", *params)
			return True
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
			sql = "UPDATE users SET "
			for field in fields:
				sql += field + " = ?,"
			sql = sql[:-1]
			params += [username, service]
			sql += " WHERE username = ? AND service = ?"
			self.__db.execute(sql, *params)
		user._dbid = users[0]["id"]
		return False

	@asynchronous
	def postMessage(self, message):
		"""	Post a message

			message:	Message instance to be posted
			
			Note that the user of the message must match the user of an account.
			Replies are can be created by setting the reply_at on message, direct
			message can be created by setting the direct_at on message. Messages
			can be sent as a reply to a specific message using reply_to.

			Remarks: This method operates asynchronously, and if message cannot be
			posted immidiately it will be stored in database and posted later.
		"""
		assert isinstance(message, Message), "message must be an instance of Message"
		user = message.getUser()
		account = None
		for ac in self.getAccounts(message.getUser().getService()):
			if ac.getUser().getUsername() == user.getUsername():
				account = ac
		if account == None:
			raise Exception, "TweetStore this not hold an account for this user!"
		if not account._postMessage(message):
			self.__db.execute("INSERT INTO actions (type, param, account) VALUES (?, ?, ?)", "post_message", message.dumps(), self.__getAccountID(account))
			self.__db.commit()

	def getOutbox(self, account = None, page = 0, page_size = 0):
		"""Gets messages waiting for transmission by a specified account, or all accounts if none specified

			account:	Account to get outgoing messages for, default to all
			page:		Page number to return, default to 0
			page_size:	Number of entries on each page, default to 0, meaning unlimited

			Note: Please set page_size unless all messages are wanted. This method returns a
			generator, so performance should be quite good.
		"""
		assert isinstance(page, (int, long)), "page number must be a positive integer"
		assert isinstance(page_size, (int, long)), "page_size must be a positive integer"
		assert account == None or isinstance(account, Account), "if provided account must be an instance of Account"
		sql = "SELECT id, param FROM actions WHERE type = ?"
		params = ("post_message",)
		if account:
			sql += " AND account = ?"
			params += (self.__getAccountID(account))
		sql += " ORDER BY id"
		#Do paging
		if page_size > 0:
			sql += " LIMIT ?"
			params += (page_size,)
			sql += " OFFSET ?"
			params += (page * page_size,)
		#Execute sql statement
		for action in self.__db.execute(sql, *params):
			#Deserialize and return each message using a generator
			msg = Message(self, data = action["param"])
			msg._outboxID = action["id"]	#This ID is used if message is to be deleted later on
			yield msg

	def removeFromOutbox(self, message):
		"""Removes a given message from Outbox
			
			Returns True if the message was found and successfully removed.
			
			Note: The message instance passed to this method must originate from TweetStore.getOutbox().
		"""
		#Instances from getOutbox has an _outboxID attribute
		if not hasattr(msg, "_outboxID"):
			return False
		#Delete the message
		self.__db.execute("DELETE FROM actions WHERE id = ?", msg._outboxID)
		return True

	def _cacheImage(self, url):
		"""	Catch an image and return an id for it
		"""
		assert isinstance(url, basestring), "url must be a string"
		identifier = self.__db.fetchone("SELECT id, cached FROM images WHERE url = ? LIMIT 1", url)
		if not identifier:
			data = urlopen("http://" + urllib.quote(url[7:])).read()
			return self.__db.execute("INSERT INTO images (url, cached, image) VALUES (?, ?, ?)", url, time.time(), sqlite3.Binary(data))
		elif time.time() - identifier["cached"] > self.getCacheTimeout():
			data = urlopen("http://" + urllib.quote(url[7:])).read()
			self.__db.execute("UPDATE images SET image = ?, cached = ? WHERE id = ?", sqlite3.Binary(data), time.time(), identifier["id"])
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
		service = self.__db.fetchone("SELECT service FROM services WHERE id = ? LIMIT 1", identifier)
		if service == None:
			raise Exception, "Service does not exist in database"
		return service["service"]

	def _getUser(self, identifier):
		"""	Get a user based on user id in database
		"""
		assert isinstance(identifier, (int, long)), "identifier must be an integer"
		user = self.__db.fetchone("SELECT * FROM users WHERE id = ? LIMIT 1", identifier)
		if not user:
			raise NotInDatabaseError, "Userid does not exists in database"
		return self.__parseUserRow(user)

	def _getUserID(self, username, service):
		"""	Gets a user id from username and service
			username:	Username of the user, who's id is wanted
			service:	Service unique string or integer identifier for the service

			return:	The internal database id of the user
		"""
		assert isinstance(username, basestring), "username must be a string"
		assert isinstance(service, (int, long, basestring)), "service must be either an integer identifier or a service string."
		if isinstance(service, basestring):
			service = self._getServiceID(service)
		userid = self.__db.fetchone("SELECT id from users WHERE username = ? AND service = ? LIMIT 1", username, service)
		if not userid:
			raise NotInDatabaseError, "User not found in database"
		return userid["id"]

	def getUser(self, username, service):
		"""Gets a user from username and service
			
			username:	Username of the user, who is wanted
			service:	Service unique string or integer identifier for the service
			
			Returns instance of User or None, if not in database
		"""
		#Try to get the user
		try:
			identifier = self._getUserID(username, service)
			return self._getUser(identifier)
		except NotInDatabaseError:
			#If not in database return None
			return None

	__accounts = {}
	def _addAccount(self, account):
		for ID, AC in self.__accounts.items():
			if account == AC:
				assert False, "account is already added"
				return
		#Caching the user
		self.__cacheUser(account.getUser())
		#Should already be done, as accounts need to get a TweetStore in their constructor
		#this is needed since accounts could cache images for users otherwise.
		account._setOwner(self)

		#Serialize and insert into database
		data = pickle.dumps(account)
		service_id = self._getServiceID(account.getService())
		ID = self.__db.execute("INSERT INTO accounts (data, service) VALUES (?, ?)", data, service_id)
		self.__db.commit()
		
		#Use database identifier for internal dictionary
		self.__accounts[ID] = account

		#Sync the newly added account
		self.sync(account)
		
	def removeAccount(self, account):
		"""	Remove an account
			This deletes friend and follower associations for this account, but not tweets and users
		"""
		assert isinstance(account ,Account), "account must be an instance of Account"
		ID = self.__getAccountID(account)
		#Remove from out account list
		del self.__accounts[ID]
		#Delete the cached account
		self.__db.execute("DELETE FROM accounts WHERE id = ?", ID);
		#Delete associated friends, not the users, just the friend associations
		self.__db.execute("DELETE FROM friends WHERE account = ?", ID);
		#Delete associated followers, not the users, just the follower associations
		self.__db.execute("DELETE FROM followers WHERE account = ?", ID);

	def __getAccountID(self, account):
		"""Get the ID of an account"""
		assert isinstance(account, Account), "account must be an instance of Account"
		for ID, AC in self.__accounts.items():
			if account == AC:
				return ID
		raise Exception, "Account does not exist"

	def __getAccountFromID(self, identifier):
		"""Gets an account from its ID"""
		assert isinstance(identifier, (int, long)), "Account identifier must be integer"
		if not identifier in self.__accounts:
			raise Exception, "No account has matching identifier"
		return self.__accounts[identifier]

	def getAccounts(self, service = None):
		"""	Get accounts managed by this instance
			service: Specifiy which type of accounts is desired (optional)
		"""
		if service == None:
			return self.__accounts.values()
		
		assert isinstance(service, (basestring, int, long)), "service must be a string or an identifier"

		if isinstance(service, (int, long)):
			service = self.getService(service_id)

		accounts = []
		for account in self.__accounts.values():
			if account.getService() == service:
				accounts += [account]
		return accounts

	def __restoreAccounts(self):
		"""Restore all accounts from database"""
		accounts = self.__db.execute("SELECT * FROM accounts")
		for rc in accounts:
			account = pickle.loads(rc["data"].encode())
			self.__accounts[rc["id"]] = account
			account._setOwner(self)

	def __storeAccounts(self):
		"""Store all accounts in database"""
		for identifier, account in self.__accounts.items():
			data = pickle.dumps(account)
			self.__db.execute("UPDATE accounts SET data = ? WHERE id = ?", identifier, data)

	def getTimeline(self, account = None, page = 0, page_size = 0):
		"""Gets timeline from a specified account, or all accounts if none specified

			account:	Account to get timeline from, default to all
			page:		Page number to return, default to 0
			page_size:	Number of entries on each page, default to 0, meaning unlimited

			Note: Please set page_size unless all messages are wanted. This method returns a
			generator, so performance should be quite good.
		"""
		assert isinstance(page, (int, long)), "page number must be a positive integer"
		assert isinstance(page_size, (int, long)), "page_size must be a positive integer"
		#Prepare sql statement
		params = []
		if account != None:
			assert isinstance(account, Account), "account must be an instance of Account"
			params += [self.__getAccountID(account)]*2
			sql = "SELECT * FROM tweets WHERE user IN (SELECT id FROM friends WHERE account = ?) AND id NOT IN (SELECT id FROM direct_messages) AND id NOT IN (SELECT id FROM replies WHERE reply_at NOT IN (SELECT id FROM friends WHERE account = ?))"
		else:
			sql = "SELECT * FROM tweets WHERE user IN (SELECT id FROM friends) AND id NOT IN (SELECT id FROM direct_messages) AND id NOT IN (SELECT id FROM replies WHERE reply_at NOT IN (SELECT id FROM friends))"
		sql += " ORDER BY created DESC"
		if page_size > 0:
			sql += " LIMIT ?"
			params += [page_size]
			sql += " OFFSET ?"
			params += [page * page_size]
		#Execute sql
		msgs = self.__db.execute(sql, *params)
		#Return using generator
		for msg in msgs:
			yield self.__parseTweetRow(msg)

	def getFriends(self, account = None, page = 0, page_size = 0):
		"""Get friends from specified account or all accounts (default)

			account:	Account to get friends from, default to all
			page:		Page number to return, default to 0
			page_size:	Number of entries on each page, default to 0, meaning unlimited

			Note: Please set page_size unless all friends are wanted. This method returns a
			generator, so performance should be quite good.
		"""
		assert isinstance(page, (int, long)) and page >= 0, "page number must be a positive integer"
		assert isinstance(page_size, (int, long)) and page_size >= 0, "page_size must be a positive integer"
		assert account == None or isinstance(account, Account), "if account is specified it must be an instance of Account"
		#Prepare sql statement
		params = ()
		sql = "SELECT * FROM users WHERE id IN (SELECT id FROM friends"
		if account != None:
			sql += " WHERE account = ?"
			params += (self.__getAccountID(account),)
		sql += ") ORDER BY name"
		if page_size > 0:
			sql += " LIMIT ?"
			params += (page_size,)
			sql += " OFFSET ?"
			params += (page * page_size,)
		#Execute sql statement
		friends = self.__db.execute(sql, *params)
		#Return user generator
		for friend in friends:
			yield self.__parseUserRow(friend)

	def getFollowers(self, account = None, page = 0, page_size = 0):
		"""Get followers from specified account or all accounts (default)

			account:	Account to get followers from, default to all
			page:		Page number to return, default to 0
			page_size:	Number of entries on each page, default to 0, meaning unlimited

			Note: Please set page_size unless all followers are wanted. This method returns a
			generator, so performance should be quite good.
		"""
		assert isinstance(page, (int, long)) and page >= 0, "page number must be a positive integer"
		assert isinstance(page_size, (int, long)) and page_size >= 0, "page_size must be a positive integer"
		assert account == None or isinstance(account, Account), "if account is specified it must be an instance of Account"
		#Prepare sql statement
		params = ()
		sql = "SELECT * FROM users WHERE id IN (SELECT id FROM followers"
		if account != None:
			sql += " WHERE account = ?"
			params += (self.__getAccountID(account),)
		sql += ") ORDER BY name"
		if page_size > 0:
			sql += " LIMIT ?"
			params += (page_size,)
			sql += " OFFSET ?"
			params += (page * page_size,)
		#Execute sql statement
		followers = self.__db.execute(sql, *params)
		#Return user generator
		for follower in followers:
			yield self.__parseUserRow(follower)
			
	def getCachedUsers(self, service = None, page = 0, page_size = 0):
		"""Get all users cached in the database for a specified service, default to all.
			This method is used for created notifications black/whitelist.
		
			service:	Service string or identifier for which all cached users are wanted.
			page:		Page number to return, default to 0
			page_size:	Number of entries on each page, default to 0, meaning unlimited
			
			Note: Please set page_size unless all users are wanted. This method returns a
			generator, so performance should be quite good.
		"""
		assert isinstance(page, (int, long)) and page >= 0, "page number must be a positive integer"
		assert isinstance(page_size, (int, long)) and page_size >= 0, "page_size must be a positive integer"
		assert service == None or isinstance(service, (basestring, int, long)), "if service is specified it must be a string or an identifier."
		#Prepare sql statement
		params = ()
		sql = "SELECT * FROM users"
		#If service is provided
		if service:
			sql += " WHERE service = ?"
			if isinstance(service, (basestring)):
				service += (self._getServiceID(service),)
			params += (service,)
		#Add ordering
		sql += " ORDER BY name"
		#Add possible paging
		if page_size > 0:
			sql += " LIMIT ?"
			params += (page_size,)
			sql += " OFFSET ?"
			params += (page * page_size,)
		#Execute sql statement
		users = self.__db.execute(sql, *params)
		#Return user generator
		for user in users:
			yield self.__parseUserRow(user)

	def getReplies(self, To = None, From = None, page = 0, page_size = 0):
		"""Get replies

			To:			Get replies that are for this user, defaults to all
			From:		Get replies that are from this user, defaults to all
			page:		Page number to return, default to 0
			page_size:	Number of entries on each page, default to 0, meaning unlimited

			Note: Please set page_size unless all replies are wanted. This method returns a
			generator, so performance should be quite good.
		"""
		assert isinstance(page, (int, long)) and page >= 0, "page number must be a positive integer"
		assert isinstance(page_size, (int, long)) and page_size >= 0, "page_size must be a positive integer"		
		params = []
		sql = "SELECT * FROM tweets WHERE "
		#Add to condition
		if To == None:
			sql += "id IN (SELECT id FROM replies)"
		else:
			assert isinstance(To, User), "to must be an instance of User"
			params += [To._getServiceID()]
			sql += "id IN (SELECT id FROM replies WHERE reply_at = ?)"
		#Add optional from condition
		if From != None:
			assert isinstance(From, User), "from must be an instance of User"
			sql += " AND user = ?"
			params += [From._getServiceID()]
		#Order by creation
		sql += " ORDER BY created DESC"
		#Create optional pagnation
		if page_size > 0:
			sql += " LIMIT ?"
			params += [page_size]
			sql += " OFFSET ?"
			params += [page * page_size]
		#Execute sql
		msgs = self.__db.execute(sql, *params)
		#Return using generator
		for msg in msgs:
			yield self.__parseTweetRow(msg)

	def getDirectMessages(self, To = None, From = None, page = 0, page_size = 0):
		"""Get direct messages

			To:			Get direct messages that are for this user, defaults to all
			From:		Get direct messages that are from this user, defaults to all
			page:		Page number to return, default to 0
			page_size:	Number of entries on each page, default to 0, meaning unlimited

			Note: Please set page_size unless all direct messages are wanted. This method returns a
			generator, so performance should be quite good.
		"""
		assert isinstance(page, (int, long)) and page >= 0, "page number must be a positive integer"
		assert isinstance(page_size, (int, long)) and page_size >= 0, "page_size must be a positive integer"		
		params = []
		sql = "SELECT * FROM tweets WHERE "
		#Add to condition
		if To == None:
			sql += "id IN (SELECT id FROM direct_messages)"
		else:
			assert isinstance(To, User), "to must be an instance of User"
			params += [To._getServiceID()]
			sql += "id IN (SELECT id FROM direct_messages WHERE direct_at = ?)"
		#Add optional from condition
		if From != None:
			assert isinstance(From, User), "from must be an instance of User"
			sql += " AND user = ?"
			params += [From._getServiceID()]
		#Order by creation
		sql += " ORDER BY created DESC"
		#Create optional pagnation
		if page_size > 0:
			sql += " LIMIT ?"
			params += [page_size]
			sql += " OFFSET ?"
			params += [page * page_size]
		#Execute sql
		msgs = self.__db.execute(sql, *params)
		#Return using generator
		for msg in msgs:
			yield self.__parseTweetRow(msg)

	def isFriend(self, user, account = None):
		"""Returns True if the user is a friend of the given account
		
			user:		User to determine if is a friend
			account:	Account the user should be a friend of, default to None meaning all accounts
			
			Note: The account must be added to this TweetStore and synchronized.
		"""
		assert isinstance(user, User), "user must be an instance of User"
		assert isinstance(account, Account) or account == None, "account must be None or an instance of Account"
		service_id = self._getServiceID(user.getService())
		sql = "SELECT COUNT(id) as relations FROM friends WHERE id = ?"
		try:
			params = (self._getUserID(user.getUsername(), service_id),)
		except NotInDatabaseError:
			#If username for the specified service isn't in database it cannot be a friend
			return False
		#If account is provided add it to the query
		if account:
			sql += " AND account = ?"
			params += (self.__getAccountID(account),)
		#Execute query, user is friend if relations is bigger than 0
		row = self.__db.fetchone(sql, *params)
		return row["relations"] > 0
		
	def isFollower(self, user, account = None):
		"""Returns True if the user is a follower of the given account
		
			user:		User to determine if is a follower
			account:	Account the user should be a follower of, default to None meaning all accounts
			
			Note: The account must be added to this TweetStore and synchronized.
		"""
		assert isinstance(user, User), "user must be an instance of User"
		assert isinstance(account, Account) or account == None, "account must be None or an instance of Account"
		service_id = self._getServiceID(user.getService())
		sql = "SELECT COUNT(id) as relations FROM followers WHERE id = ?"
		try:
			params = (self._getUserID(user.getUsername(), service_id),)
		except NotInDatabaseError:
			#If username for the specified service isn't in database it cannot be a follower
			return False
		#If account is provided add it to the query
		if account:
			sql += " AND account = ?"
			params += (self.__getAccountID(account),)
		#Execute query, user is follower if relations is bigger than 0
		row = self.__db.fetchone(sql, *params)
		return row["relations"] > 0

	def __parseTweetRow(self, row):
		"""Parse a database from the table of tweets"""
		return CachedMessage(self, self.__db, row)

	def __parseUserRow(self, row):
		"""Parse a database from the table of users"""
		return CachedUser(self, row)
		

class NotificationEngine:
	"""Simple component that contains notification related logic of TweetStore"""
	def __init__(self, store, database):
		self._setOwner(store, database)
		
	def __getstate__(self):
		"""Serialize settings"""
		data = {}
		data["Notification/blacklistStrings"] 			= self.blacklistStrings
		data["Notification/whitelistStrings"] 			= self.whitelistStrings
		data["Notification/blacklistByDefault"] 		= self.blacklistByDefault
		data["Notification/notifyOnNewTweets"] 			= self.notifyOnNewTweets
		data["Notification/notifyOnNewReplies"] 		= self.notifyOnNewReplies
		data["Notification/notifyOnNewDirectMessages"] 	= self.notifyOnNewDirectMessages
		data["Notification/notifyOnNewFollowers"] 		= self.notifyOnNewFollowers
		data["Notification/notifyOnNewFriends"] 		= self.notifyOnNewFriends
		data["Notification/notifyOnSynchronized"] 		= self.notifyOnSynchronized
		return data
		
	def __setstate__(self, data):
		"""Deserialize settings"""
		self.blacklistStrings 			= data["Notification/blacklistStrings"]
		self.whitelistStrings 			= data["Notification/whitelistStrings"]
		self.blacklistByDefault 		= data["Notification/blacklistByDefault"]
		self.notifyOnNewTweets 			= data["Notification/notifyOnNewTweets"]
		self.notifyOnNewReplies 		= data["Notification/notifyOnNewReplies"]
		self.notifyOnNewDirectMessages	= data["Notification/notifyOnNewDirectMessages"]
		self.notifyOnNewFollowers 		= data["Notification/notifyOnNewFollowers"]
		self.notifyOnNewFriends 		= data["Notification/notifyOnNewFriends"]
		self.notifyOnSynchronized 		= data["Notification/notifyOnSynchronized"]
	
	def _setOwner(self, store, database):
		"""Set TweetStore and database associated with this instance, needed when deserializing"""
		assert isinstance(database, ThreadSafeDatabase), "database must be an instance of ThreadSafeDatabase"
		assert isinstance(store, TweetStore), "store must be an instance of TweetStore"
		self.__db = database
		self.__store = store
		#Check that tables are present if not create them
		tables = ()
		for row in self.__db.execute("SELECT name from sqlite_master WHERE type='table'"):
			tables += (row["name"],)
		if "notification_blacklist" not in tables:
			self.__db.execute("""
				CREATE TABLE notification_blacklist(
					id			INT,
					blacklisted	INT)""")
	
	def blacklist(self, user):
		"""Blacklist a user, this means no notification about tweets from this user will appear."""
		if not self.__store: raise OwnerNotSetError, "Cannot blacklist user."
		assert isinstance(user, User), "user must be an instance of User"
		#Get the user id
		try:
			user_id = self.__store._getUserID(user.getUsername(), user.getService())
		except NotInDatabaseError:
			self.__cacheUser(user)
			user_id = user._dbid
		#Check if already in the blacklist
		row = self.__db.fetchone("SELECT blacklisted FROM notification_blacklist WHERE id = ? LIMIT 1", user_id)
		#If user is in the black/whitelist and whitelisted:
		if row and row["blacklisted"] == 0:
			self.__db.execute("UPDATE notification_blacklist SET blacklisted = 1 WHERE id = ?", user_id)
		elif not row:	#If user is not in the black/whitelist
			self.__db.execute("INSERT INTO notification_blacklist (id, blacklisted) VALUES (?, 1)", user_id)
	
	def whitelist(self, user):
		"""Whitelist a user, this means that all notification about tweets from this user will appear."""
		if not self.__store: raise OwnerNotSetError, "Cannot whitelist user."
		assert isinstance(user, User), "user must be an instance of User"
		#Get the user id
		try:
			user_id = self.__store._getUserID(user.getUsername(), user.getService())
		except NotInDatabaseError:
			self.__cacheUser(user)
			user_id = user._dbid
		#Check if already in the blacklist
		row = self.__db.fetchone("SELECT blacklisted FROM notification_blacklist WHERE id = ? LIMIT 1", user_id)
		#If user is in the black/whitelist and blacklisted:
		if row and row["blacklisted"] == 1:
			self.__db.execute("UPDATE notification_blacklist SET blacklisted = 0 WHERE id = ?", user_id)
		elif not row:	#If user is not in the black/whitelist
			self.__db.execute("INSERT INTO notification_blacklist (id, blacklisted) VALUES (?, 0)", user_id)

	def isBlacklisted(self, user):
		"""Return True if the user is blacklist and False if the user if whitelisted,
			If the user is not in the black/whitelist, blacklistByDefault is returned.
		"""
		if not self.__store: raise OwnerNotSetError, "Cannot check user."
		assert isinstance(user, User), "user must be an instance of User"
		#Get the user id
		try:
			user_id = self.__store._getUserID(user.getUsername(), user.getService())
		except NotInDatabaseError:
			#Return the default state if user is not in the black/whitelist
			return self.blacklistByDefault
		#Check if already in the blacklist
		row = self.__db.fetchone("SELECT blacklisted FROM notification_blacklist WHERE id = ? LIMIT 1", user_id)
		if not row:
			return self.blacklistByDefault
		#If user is in the black/whitelist
		return row["blacklisted"] == 1
	
	blacklistStrings = ()
	"""Tuple of strings (unicode) that if present in a message blocks it's notification"""
	
	whitelistStrings = ()
	"""Tuple of strings (unicode) that if present in a message overwrites any blocks of notification"""
	
	blacklistByDefault = False
	"""Block notifications from all users who are not explicitly whitelisted."""
	
	def __isBlocked(self, message):
		"""Returns True if the messags blocked, e.g. user is blacklist or it contains a blacklist string."""
		assert isinstance(message, Message), "message must be an instance of Message"
		#Check if message contains whitelist strings
		for string in self.whitelistStrings:
			if string in message.getMessage():
				return False
		#Check if message contains blacklist strings
		for string in self.blacklistStrings:
			if string in message.getMessage():
				return True
		#If it doesn't contain a whitelist or blacklist string, check if user is blocked
		return self.isBlacklisted(message.getUser())
	
	notifyOnNewTweets = True
	"""Generate a notification whenever a new tweet appears in the timeline."""
	
	notifyOnNewReplies = True
	"""Generate a notification whenever a new reply at the user appears."""
	
	notifyOnNewDirectMessages = True
	"""Generate a notification whenever a new direct message to the user appears."""
	
	notifyOnNewFollowers = True
	"""Generate a notification whenever a new follower of the user appears."""
	
	notifyOnNewFriends = False
	"""Generate a notification whenever a new friend of the user appears."""
	
	notifyOnSynchronized = True
	"""Generate a notification when synchronization is completed."""
	
	onNotification = Event()
	"""Occurs whenever there's is a notification that should be shown to the user
		Eventhandlers should take three parameters, notification title, notification text and an optional image (as buffer or None)
	"""
	
	__synchronizing = 0
	"""Synchronizatoin semaphor, used to determine when all synchronizations are completed."""
	
	def _beginSync(self):
		"""Inform the notification engine that synchronization of an account is starting"""
		self.__synchronizing += 1
		
	def _endSync(self):
		"""Inform the notification engine that synchronization of an account has ended, this may possibly raise events"""
		self.__synchronizing -= 1
		if self.__synchronizing == 0:
			if not self.__store: raise OwnerNotSetError, "Cannot end synchronization."
			#Get the states and reset them, do this at once to avoid concurrency issues
			newTweets = self.__newTweets
			self.__newTweets = ()
			newReplies = self.__newReplies
			self.__newReplies = ()
			newDirectMessages = self.__newDirectMessages
			self.__newDirectMessages = ()
			newFollowers = self.__newFollowers
			self.__newFollowers = ()
			newFriends = self.__newFriends
			self.__newFriends = ()
			
			#Raise synchronization completed event
			self.__store.onSyncCompleted.raiseEvent()
			
			#Generate events
			if len(newTweets) > 0:
				self.__store.onNewTweets.raiseEvent(newTweets)
			if len(newReplies) > 0:
				self.__store.onNewReplies.raiseEvent(newReplies)
			if len(newDirectMessages) > 0:
				self.__store.onNewDirectMessages.raiseEvent(newDirectMessages)
			if len(newFollowers) > 0:
				self.__store.onNewFollowers.raiseEvent(newFollowers)
			if len(newFriends) > 0:
				self.__store.onNewFriends.raiseEvent(newFriends)
			
			#Generate synchronization completed notification, to sum up
			if self.notifyOnSynchronized:
				msgs = ()
				if len(newTweets) > 0:
					msgs += (str(len(newTweets)) + " new tweets",) 
				if len(newReplies) > 0:
					msgs += (str(len(newReplies)) + " new replies",) 
				if len(newDirectMessages) > 0:
					msgs += (str(len(newDirectMessages)) + " new direct messages",) 
				if len(newFollowers) > 0:
					msgs += (str(len(newFollowers)) + " new followers",) 
				if len(newFriends) > 0:		
					msgs += (str(len(newFriends)) + " new friends",)
				if len(msgs) == 0:
					notification = "You have nothing new."
				elif len(msgs) == 1:
					notification = "You have " + msgs[0] + "."
				else:
					notification = "You have " + ", ".join(msgs[:-1]) + " and " + msgs[-1] + "."
				#Raise the notification event
				self.onNotification.raiseEvent("Synchronization completed", notification, None)	#TODO: Consider having a image
	
	__newTweets = ()
	"""Tuple of new tweets from users timeline that appeared during synchronization"""
	
	__newReplies = ()
	"""Tuple of new replies at the user that appeared during synchronization"""
	
	__newDirectMessages = ()
	"""Tuple of new direct messages to the user that appeared during synchronization"""
	
	__newFollowers = ()
	"""Tuple of new followers of the user that appeared during synchronization"""
	
	__newFriends = ()
	"""Tuple of new friends of the user that appeared during synchronization"""
	
	def _newTweet(self, message):
		"""Inform the notification engine that a new tweets from users timeline appeared during synchronization"""
		assert isinstance(message, Message), "message must an instance of Message"
		self.__newTweets += (message,)
		#Generate event if needed
		if self.notifyOnNewTweets and not self.__isBlocked(message):
			self.onNotification.raiseEvent("New tweet by " + message.getUser().getName(), message.getMessage(), message.getUser().getImage())
	
	def _newReply(self, message):
		"""Inform the notification engine that a new reply at the user appeared during synchronization"""
		assert isinstance(message, Message), "message must an instance of Message"
		self.__newReplies += (message,)
		#Generate event if needed
		if self.notifyOnNewReplies and not self.__isBlocked(message):
			self.onNotification.raiseEvent("New reply from " + message.getUser().getName(), message.getMessage(), message.getUser().getImage())
		
	def _newDirectMessage(self, message):
		"""Inform the notification engine that a new direct message to the user appeared during synchronization"""
		assert isinstance(message, Message), "message must an instance of Message"
		self.__newDirectMessages += (message,)
		#Generate event if needed
		if self.notifyOnNewDirectMessages and not self.__isBlocked(message):
			self.onNotification.raiseEvent("New direct message from " + message.getUser().getName(), message.getMessage(), message.getUser().getImage())
	
	def _newFollower(self, user):
		"""Inform the notification engine that a new follower of the user user appeared during synchronization"""
		assert isinstance(user, User), "user must an instance of User"
		self.__newFollowers += (user,)
		#Generate event if needed
		if self.notifyOnNewFollowers and not self.isBlacklisted(user):
			self.onNotification.raiseEvent("New follower", user.getName() + " on " + user.getService() + " is now following you.", user.getImage())
	
	def _newFriend(self, user):
		"""Inform the notification engine that a new friend of the user user appeared during synchronization"""
		assert isinstance(user, User), "user must an instance of User"
		self.__newFriends += (user,)
		#Generate event if needed
		if self.notifyOnNewFriends and not self.isBlacklisted(user):
			self.onNotification.raiseEvent("New friend", user.getName() + " on " + user.getService() + " is now a friend of yours.", user.getImage())
	

class CatchedSettings:
	"""	Simple database wrapper for store settings
	
		This type acts as a dictionary, e.g. consumers can add, get and remove keys as in a directionary.
		This type also supports the in keyword. The keys and values are stored in a database table as pickled
		strings, this may not offer a good performance, however, if this was to become a problem this class
		could be implemented more effectively.
		Note: For performance issues, keys are NOT pickled and only string keys is supported.
	"""
	def __init__(self, database):
		assert isinstance(database, ThreadSafeDatabase), "database must be an instance of ThreadSafeDatabase"
		self.__db = database
		#Check that tables are present if not create them
		tables = ()
		for row in self.__db.execute("SELECT name from sqlite_master WHERE type='table'"):
			tables += (row["name"],)
		if "settings" not in tables:
			self.__db.execute("""
				CREATE TABLE settings(
					key		TEXT,
					value	TEXT)""")
		self.__db.commit()
	
	def __getitem__(self, key):
		"""Get settings value from key
		
			Note: Key must be a string
		"""
		if not isinstance(key, basestring):
			raise TypeError, "key must be a string"
		value = self.__db.fetchone("SELECT value FROM settings WHERE key = ? LIMIT 1", key)
		if not value:
			raise KeyError, "Key does not exist in settings"
		return pickle.loads(str(value["value"]))
	
	def get(self, key, default = None):
		"""Gets settings value from key, if key doesn't exist return default, which defaults to None
		
			Note: Key must be a string. This method offers better performance than __contains__ and 
			__getitem__ that can be used to perform the same task.
		"""
		if not isinstance(key, basestring):
			raise TypeError, "key must be a string"
		value = self.__db.fetchone("SELECT value FROM settings WHERE key = ? LIMIT 1", key)
		if not value:
			return default
		return pickle.loads(str(value["value"]))
	
	def __setitem__(self, key, value):
		"""Set settings value for a given key
		
			Note: Key must be a string
		"""
		if not isinstance(key, basestring):
			raise TypeError, "key must be a string"
		value = pickle.dumps(value)
		oldValue = self.__db.fetchone("SELECT value FROM settings WHERE key = ? LIMIT 1", key)
		if oldValue:
			if oldValue != value:
				self.__db.execute("UPDATE settings SET value = ? WHERE key = ?", sqlite3.Binary(value), key)
		else:
			self.__db.execute("INSERT INTO settings (key, value) VALUES (?, ?)", key, sqlite3.Binary(value))
	
	def __delitem__(self, key):
		"""Delete settings value for a given key
		
			Note: Key must be a string
		"""
		if not isinstance(key, basestring):
			raise TypeError, "key must be a string"
		self.__db.execute("DELETE FROM settings WHERE key = ?", key)
		
	def __contains__(self, key):
		"""Gets if a value for a given key exists
		
			Note: Key must be a string
		"""
		if not isinstance(key, basestring):
			raise TypeError, "key must be a string"
		value = self.__db.fetchone("SELECT key FROM settings WHERE key = ? LIMIT 1", key)
		return value != None
	

class User:
	def __init__(self, store, username = None, service = None, name = None, url = "", location = "Unknown", description = "", image_id = None, data = None):
		"""Initialize a new instance of User

			store:			TweetStore associated with this User
			username:		Username (service unique)
			service:		Service string or identifier
			name:			Name of the user (optional)
			url:			Url for the user (optional)
			location:		Location of the user (optional)
			description:	Description of the user (optional)
			image_id:		id of the image in the TweetStore, for this user (optional)
			data:			Data string this instance should be restored from, created using User.dumps()
							This paramter excludes all the other parameters except store, which is always needed
		"""
		assert isinstance(store, TweetStore), "store must be an instance of TweetStore"
		self.__store = store
		#if we are restoring from serialized data
		if data != None:
			if not isinstance(data, str):
				data = data.encode()
			data = pickle.loads(data)
			self._service = data["service"]
			self._service_id = data["service_id"]
			self._username = data["username"]
			self._url = data["url"]
			self._location = data["location"]
			self._description = data["description"]
			self.__image_id = data["image_id"]
			self._name = data["name"]
			return None
		#If creating new instance
		else:
			assert isinstance(username, basestring), "username must be provided"
			assert isinstance(service, (int, long, basestring)), "service must be provided as string or integer"
			if isinstance(service, (basestring)):
				self._service = service
				self._service_id = None
			else:
				self._service = None
				self._service_id = service
			self._username = username
			self._url = url
			self._location = location
			self._description = description
			self.__image_id = image_id
			self.__store = store
			if not name:
				self._name = username + " on " + self.getService()
			else:
				self._name = name

	def dumps(self):
		""" Dump this instance of user to a string.

			This object cannot be pickled, as it may need a reference to a TweetStore, however, so inorder
			to allow subclasses of this class, serialization of a user instance is done using 
			data = User.dumps(), the object is restored using User(store, data = data)
		"""
		data = {}
		data["username"] = self.getUsername()
		data["service"] = self.getService()
		data["service_id"] = self._getServiceID()
		data["name"] = self.getName()
		data["url"] = self.getUrl()
		data["location"] =  self.getLocation()
		data["description"] = self.getDescription()
		data["image_id"] = self._getImageID()
		return pickle.dumps(data)

	def getName(self):
		"""Gets the name of this user"""
		return self._name

	def getUsername(self):
		"""Gets the username of this user"""
		return self._username

	def getService(self):
		"""Gets the service this user exists on"""
		if not self._service:
			return self.__store._getService(self._service_id)
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
		return self.__image_id

	def __str__(self):
		"""Get string representation of this user on this service"""
		return self.getUsername() + " - " + self.getService()

	def __eq__(self, other):
		"""Compare username and service of two users"""
		if isinstance(other, User):
			return self.getUsername() == other.getUsername() and self.getService() == other.getService()
		return NotImplemented
		
	def __ne__(self, other):
		"""Compare username and service of two users"""
		result = self.__eq__(other)
		if result is NotImplemented:
			return result
		return not result


class CachedUser(User):
	"""Subclass of User, for representation of users already in database"""

	def __init__(self, store, row):
		"""	Initialize new instance of CachedUser

			store:		TweetStore where this user is cached
			row:		sqlite3.Row, of this user
		"""
		assert isinstance(store, TweetStore), "store must be an instance of TweetStore"
		self.__store = store
		self._row = row
		self._service = None

	def getName(self):
		"""Gets the name of this user"""
		return self._row["name"]

	def getUsername(self):
		"""Gets the username of this user"""
		return self._row["username"]

	def getService(self):
		"""Gets the service this user exists on"""
		if not self._service:
			self._service = self.__store._getService(self._row["service"])
		return self._service

	def getUrl(self):
		"""Get a url to the user page"""
		return self._row["url"]

	def getLocation(self):
		"""Gets the location of the user"""
		return self._row["location"]

	def getDescription(self):
		"""Gets the user decription"""
		return self._row["description"]

	def getImage(self):
		"""Gets a binary image"""
		return self.__store._getImage(self._getImageID())

	def _getServiceID(self):
		"""Gets the service ID for this user"""
		return self._row["service"]

	def _getImageID(self):
		"""Get image id of image for this user"""
		return self._row["image"]

class Message:
	"""Message abstraction for TweetStore
	
		Remarks:
		Serialization of this instance is done using dumps() and it is deserialized using the constructor, by providing the store and data arguments only.
		Serialization is done in this manner so that subclass of this class does not need to implement any serialization.
		
		Notes on terminology:
		"reply at" is the user a reply is at, to might be more appropriate, but "reply_to" is used for the message that a message is in-reply-to. For
		consistency "direct at" is the user a direct message is sendt to.
	"""
	
	def __init__(self, store, message = None, user = None, service = None, created = None, suid = 0, reply_at = None, reply_to = None, direct_at = None, data = None):
		""" Create an instance of Message

			store:		TweetStore associated with this Message instance
			message:	Message text
			user:		User who wrote this message
			created:	Timestamp of message creation (optional, defaults to now)
			service:	Service string or identifier (optional, defaults to whatever user has)
			suid:		Service unique identifier, need not be unique (optional)
			reply_at:	User who this message is to (optional)
			reply_to:	Message this message is a reply to (optional)
			direct_at:	User this message is direct to (optional)
			data: 		Data string this instance should be restored from, created using Message.dumps()
						This paramter excludes all the other parameters except store, which is always needed

			Notice: reply_at and direct_at are mutually exclusive, but reply_to can be provided for both.
		"""
		assert isinstance(store, TweetStore), "store must be an instance of TweetStore"
		self.__store = store
		#If we are restoring from serialized data
		if data != None:
			if not isinstance(data, str):
				data = data.encode()
			data = pickle.loads(data)
			self._message = data["message"]
			self._created = data["created"]
			self._service = data["service"]
			self._service_id = data["service_id"]
			self._suid = data["suid"]
			self._user = User(self.__store, data = data["user"])
			self._reply_at = User(self.__store, data = data["reply_at"])
			self._reply_to = Message(self.__store, data = data["reply_to"])
			self._direct_at = User(self.__store, data = data["direct_at"])
			return None
		#If creating new instance
		else:
			assert isinstance(message, basestring), "message must be string"
			assert isinstance(user, User), "user must be an instance of User"
			assert isinstance(suid, (int, long)), "Service Unique Id (suid) must be an integer"
			if service == None:
				service = user.getService()
			assert isinstance(service, (basestring, int, long)), "service must be string or identifier"
			assert reply_at == None or isinstance(reply_at, User), "reply_at must be an instance of user"
			assert direct_at == None or isinstance(direct_at, User), "direct_at must be an instance of User"
			assert reply_to == None or isinstance(reply_to, Message), "reply_to must be an instance of Message"
			self._message = message
			self._created = created or time.time()
			if isinstance(service, (basestring)):
				self._service = service
				self._service_id = None
			else:
				self._service = None
				self._service_id = service
			self._suid = suid
			self._user = user
			self._reply_at = reply_at
			self._reply_to = reply_to
			self._direct_at = direct_at

	def dumps(self):
		""" Dump this instance of Message to a string.

			This object cannot be pickled, as it may need a reference to a TweetStore, however, so inorder
			to allow subclasses of this class, serialization of a Message instance is done using 
			data = Message.dumps(), the object is restored using Message(store, data = data)
		"""
		data = {}
		data["message"] = self.getMessage()
		data["created"] = self.getCreated()
		data["service"] = self.getService()
		data["service_id"] = self._getServiceID()
		data["suid"] = self._getServiceUniqueId()
		data["user"] = self.getUser().dumps()
		#Dump reply_at user
		if self.isReply():
			data["reply_at"] = self.getReplyAt().dumps()
		else:
			data["reply_at"] = None
		#Dump direct_at user
		if self.isDirectMessage():
			data["direct_a"] = self.getDirectAt().dumps()
		else:
			data["direct_a"] = None
		#Dump reply_to user
		if self.getReplyTo() != None:
			data["reply_to"] = self.getReplyTo().dumps()
		else:
			data["reply_to"] = None
		return pickle.dumps(data)

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
		if not self._service:
			return self.__store._getService(self._service_id)
		return self._service

	def _getServiceID(self):
		"""Get unique identifier for the service this message is hosted in"""
		if not self._service_id:
			self._service_id = self.__store._getServiceID(self.getService())
		return self._service_id

class CachedMessage(Message):
	"""Subclass of Message for lazily loading users for messages in database"""
	def __init__(self, store, db, row):
		"""	Initialize new instance of CachedMessage

			store:		TweetStore where this message is cached
			db:			ThreadSafeDatabase database connection, used for lazy loading
			row:		sqlite3.Row, of this message, must have ALL fields

			Note: User, reply and direct message information is loaded lazily.
		"""
		assert isinstance(store, TweetStore), "store must be an instance of TweetStore"
		assert isinstance(db, ThreadSafeDatabase), "db must be an instance of ThreadSafeDatabase"
		self.__store = store
		self.__db = db
		self._row = row
		self._service = None
		self._is_reply = None
		self._is_direct = None

	def getMessage(self):
		"""Gets the message text"""
		return self._row["message"]
	
	def _getServiceUniqueId(self):
		"""Gets a message ID unique for this service"""
		return self._row["suid"]

	def getCreated(self):
		"""Gets the time of when this message was created"""
		return self._row["created"]
	
	def getUser(self):
		"""Gets the User who posted this message"""
		return self.__store._getUser(self._row["user"])
	
	def getReplyAt(self):
		"""Gets the user this is a reply at, None if this is not a reply"""
		if self.isReply():
			return self._reply_at
		return None

	def isReply(self):
		"""True if this message is a reply"""
		if self._is_reply == None:
			reply = self.__db.fetchone("SELECT reply_to, reply_at FROM replies WHERE id = ? LIMIT 1", self._row["id"])
			if reply:
				self._reply_at = reply["reply_at"]
				self._reply_to = reply["reply_to"]
				self._is_reply = True
			else:
				self._is_reply = False
		return self._is_reply

	def getReplyTo(self):
		"""Gets the message this is a reply to, None if none"""
		if self.isReply() or self.isDirectMessage():
			return self._reply_to
		return None

	def getDirectAt(self):
		"""User this message is direct at, None if this is not a direct message"""
		if self.isDirectMessage():
			return self._direct_at
		return None

	def isDirectMessage(self):
		"""True if this a direct message"""
		if self._is_direct == None:
			direct = self.__db.fetchone("SELECT reply_to, direct_at FROM direct_messages WHERE id = ? LIMIT 1", self._row["id"])
			if direct:
				self._direct_at = reply["direct_at"]
				self._reply_to = reply["reply_to"]
				self._is_direct = True
			else:
				self._is_direct = False
		return self._is_direct

	def getService(self):
		"""Gets the service on which this message exists"""
		if not self._service:
			self._service = self.__store._getService(self._row["service"])
		return self._service

	def _getServiceID(self):
		"""Get unique identifier for the service this message is hosted in"""
		return self._row["service"]

class OwnerNotSetError(Exception):
	"""Thrown if method is called before the instance have been assigned an owner"""
	def __init__(self, text = None):
		self._text = text
	def __str__(self):
		if test:
			return "Account has no owner: " + text
		else:
			return "Account has no owner."
			
class NotInDatabaseError(Exception):
	"""Thrown if item is not in database
		
		This can only be thrown by internal methods that assumes an item is database
	"""
	def __init__(self, text = None):
		self._text = text
	def __str__(self):
		if test:
			return "Item not in database: " + text
		else:
			return "Item not in database."

class Account:
	"""	Abstractions for an account for TweetStore

		Note: How subclasses of this is initialized should not matter to TweetStore, however, 
		subclasses should at all times return a user from getUser(). The other methods should
		also work, unless offline, once TweetStore._addAccount have been called.
		See: twitteraccount.TwitterAccount for an example of how to do this.
		
		Remarks:
		Instance of Account should be serializable, overwrite __getstate__ and __setstate__ to
		alter the serialization behavior. Note that (de)serialization should not access any
		network ressources synchronously, e.g. perform network requests and wait for the
		response. This applies to all other methods as well unless explicitly stated otherwise.
	"""
	def _getMessages(self):
		"""Returns messages as a list of Message or False
		
		If false is returned user interaction is needed and status have been changed to reflect this.
		E.g. connection must be restored or account reauthendicated, anyway synchronization of 
		this account shouldn't preceed.
		
		This method should return all messages that need to be cached. E.g. the users timeline, replies to
		the user and direct messages to the user.
		This method may access network ressources synchronously.
		"""
		raise NotImplementedError, "_getMessages must be overwritten in subclasses of Account"

	def _getFriends(self):
		"""Returns friends as a list of User or False
		
		If false is returned user interaction is needed and status have been changed to reflect this.
		E.g. connection must be restored or account reauthendicated, anyway synchronization of 
		this account shouldn't preceed.
		
		This method may access network ressources synchronously.
		"""
		raise NotImplementedError, "_getFriends must be overwritten in subclasses of Account"

	def _getFollowers(self):
		"""Get followers as a list of User or False
		
		If false is returned user interaction is needed and status have been changed to reflect this.
		E.g. connection must be restored or account reauthendicated, anyway synchronization of 
		this account shouldn't preceed.
		
		This method may access network ressources synchronously.
		"""
		raise NotImplementedError, "_getFollowers must be overwritten in subclasses of Account"

	def _postMessage(self, message):
		"""Post a message

			If the message is a reply or a direct message it should be posted as such.

			If authendication fails or service is offline, return False and change the status to
			reflect this.
			
			This method may access network ressources synchronously.
		"""
		raise NotImplementedError, "_postMessage must be overwritten in subclasses of Account"

	def reauthendicate(self, password = None):
		"""Reauthendicate, called if status = 'bad authendication'
		
			This method attempts authendication with the old password if None is provided,
			if another password it attempts authendication with that password. And stores the
			new password if it's successfull.
			
			This method may access network ressources synchronously.
			
			Remarks: No implementation of this method have been tested, and this part of the API
			may be subject to changes, as an asynchronious method probably will be preffered.
		"""
		raise NotImplementedError, "reauthendicate must be overwritten in subclasses of Account"

	def _setOwner(self, store):
		"""Sets the owner of this Account, must be called before, getUser(), reauthendicate or any of the
			_get....() methods are called.
			
			When a new instance of an Account is created the owner should be passed as an argument to the constructor,
			so that settings the owner shouldn't be necessary. However, after deserialization this method need be called.
		"""
		raise NotImplementedError, "set owner must be implemented in subclasses of Account"

	def __str__(self):
		"""Get string representation of this account, e.g. the user"""
		return str(self.getUser())

	def getUser(self):
		"""Gets the user of this account"""
		raise NotImplementedError, "getUser must be overwritten in subclasses of Account"

	def getService(self):
		"""Gets the name of the service that this account is connected to."""
		raise NotImplementedError, "getService must be overwritten in subclasses of Account"

	def getStatus(self):
		"""	Gets the current status of this account
			Can return:
			 * unconfigured
			 * offline
			 * idle
			 * updating
			 * bad authendication
			 
			Note: When status changes the onStatusChange event on the TweetStore instance 
			associated with this account should be raised.
		"""
		raise NotImplementedError, "getStatus must be overwritten in subclasses of Account"

	def getCapabilities(self):
		"""Returns an subclass of AccountCapabilities that describes the capabilities that this account has."""
		raise NotImplementedError, "getCapabilities must be overwritten in subclasses of Account"

class AccountCapabilities:
	"""	Describes the capabilities of an Account
	"""
	def canReply(self, user, message = None):
		"""	Returns True if a reply to the given user is possible
		
			user:		User you wish to test for reply ability to
			message:	Message the reply will be in-reply-to, some protocols might need this.
		"""
		raise NotImplementedError, "canReply must be overwritten in subclasses of AccountCapabilities"
	
	def replyPrefix(self, user):
		"""	Returns a message prefix for a reply at the given user
		
			Note: If prefixes are not needed for replies, then return an empty string, unicode please.
		"""
		raise NotImplementedError, "replyPrefix must be overwritten in subclasses of AccountCapabilities"
		
	def isReplyPrefix(self, text):
		"""	Returns the user that the text is a reply at, or False if text is not a reply by prefix.
		
			Note: A user returned by this method may only have username and nothing more.
			Consumers should remember to check if canReply for the returned user of this method returns True.
			If replies by prefixing is not supported then always return False.
		"""
		raise NotImplementedError, "isReplyPrefix must be overwritten in subclasses of AccountCapabilities"
	
	def canDirect(self, user, message = None):
		"""	Returns True if direct messages can be send to the given user
		
			user:		User you wish to test if direct messages can be send to
			message:	Message the direct message will be in-reply-to, some protocols might need this.
		"""
		raise NotImplementedError, "canDirect must be overwritten in subclasses of AccountCapabilities"

	def directPrefix(self, user):
		"""	Returns a message prefix for a direct message at the given user
			
			Note: If direct messages doesn't need a prefix this method should return an empty unicode string.
		"""
		raise NotImplementedError, "directPrefix must be overwritten in subclasses of AccountCapabilities"
		
	def isDirectPrefix(self, text):
		"""	Returns the user that the text is a direct message at, or False if text is not a direct message
		
			Note: A user returned by this method may only have username and nothing more.
			Consumers should remember to check if canDirect for the returned user of this method returns True.
			If direct messages by prefixing is not supported then always return False
		"""
		raise NotImplementedError, "isDirectPrefix must be overwritten in subclasses of AccountCapabilities"
		
	def updateMessageSize(self):
		"""Number of characters an update can consist of, 2 to the power of 16 if there's no practical limit"""
		raise NotImplementedError, "updateMessageSize must be overwritten in subclasses of AccountCapabilities"
		
	def replyMessageSize(self):
		"""Number of characters a reply can consist of, 2 to the power of 16 if there's no practical limit"""
		raise NotImplementedError, "replyMessageSize must be overwritten in subclasses of AccountCapabilities"
		
	def directMessageSize(self):
		"""Number of characters a direct message can consist of, 2 to the power of 16 if there's no practical limit"""
		raise NotImplementedError, "directMessageSize must be overwritten in subclasses of AccountCapabilities"
		
