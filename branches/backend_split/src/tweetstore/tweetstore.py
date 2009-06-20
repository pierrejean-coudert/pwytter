#!/usr/bin/env python
# -*- coding: utf-8 -*-

import threading
from event import Event
import pickle
import database
from urllib2 import urlopen
import time
import urllib

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

The TODO list:

public methods for tweetstore:
	blockFollower(User)
	AddFriend(User)
	RemoveFriend(User)

Implement search queries
Add more events:
	onAccountAdded
	onNewFollower
	onNewTweet
	onNewReply
	onNewDirectMessaage
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

	"""Occurs whenever an account changes status"""
	onStatusChange = Event()

	def __init__(self, database_path = ":memory:"):
		"""Initialize an instance of TweetStore"""
		#Create/connect to database
		assert isinstance(database_path, basestring), "dbpath is not a string"
		self.__db = database.ThreadSafeDatabase(database_path)
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

		#Load accounts from database
		self.__restoreAccounts()

	def __del__(self):
		"""Save settings in database"""
		self.__storeAccounts()

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
			if not self._syncMessages(account): return
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
		account_id = self.__getAccountID(account)
		for friend in self.__db.execute("SELECT id from friends WHERE account = ?", account_id):
			#Remove friends already associated from friend_ids and delete friends not in friend_ids
			if friend["id"] in friend_ids:
				friend_ids.remove(friend["id"])
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
		account_id = self.__getAccountID(account)
		for follower in self.__db.execute("SELECT id from followers WHERE account = ?", account_id):
			#Remove followers already associated from follower_ids and delete followers not in follower_ids
			if follower["id"] in follower_ids:
				follower_ids.remove(follower["id"])
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
		service = message._getServiceID()
		msgtext = message.getMessage()
		userid = self.__cacheUser(message.getUser())
		for msg in self.__db.execute("SELECT id, message, user FROM tweets WHERE created = ? AND suid = ? AND service = ?", created, suid, service):
			if msg["message"] == msgtext and msg["user"] == userid:
				return msg["id"]
		sql = "INSERT INTO tweets (message, created, user, suid, service) VALUES (?,?,?,?,?)"
		identifier = self.__db.execute(sql, msgtext, created, userid, suid, service)
		if message.isReply():
			at = self.__cacheUser(message.getReplyAt())
			to = message.getReplyTo()
			if to != None:
				to = self.__cacheMessage(to)
			else:
				to = 0
			self.__db.execute("INSERT INTO replies (id, reply_at, reply_to) VALUES (?, ?, ?)", identifier, at, to)
		if message.isDirectMessage():
			at = self.__cacheUser(message.getDirectTo())
			to = message.getReplyTo()
			if to != None:
				to = self.__cacheMessage(to)
			else:
				to = 0
			self.__db.execute("INSERT INTO direct_messages (id, direct_at, reply_to) VALUES (?, ?, ?)", identifier, at, to)
		return identifier

	def __cacheUser(self, user):
		"""	Add a user to database if it is not already there
			returns the id of the user
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
			sql = "UPDATE users SET "
			for field in fields:
				sql += field + " = ?,"
			sql = sql[:-1]
			params += [username, service]
			sql += " WHERE username = ? AND service = ?"
			self.__db.execute(sql, *params)
		return users[0]["id"]

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

	def _cacheImage(self, url):
		"""	Catch an image and return an id for it
		"""
		assert isinstance(url, basestring), "url must be a string"
		identifier = self.__db.fetchone("SELECT id, cached FROM images WHERE url = ? LIMIT 1", url)
		if not identifier:
			data = urlopen("http://" + urllib.quote(url[7:])).read()
			return self.__db.execute("INSERT INTO images (url, cached, image) VALUES (?, ?, ?)", url, time.time(), data)
		elif time.time() - identifier["cached"] > self.getCacheTimeout():
			data = urlopen("http://" + urllib.quote(url[7:])).read()
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
			raise Exception, "Userid does not exists in database"
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
			raise Exception, "User not found in database"
		return userid["id"]

	__accounts = {}
	def _addAccount(self, account):
		for ID, AC in self.__accounts:
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

		#Use database identifier for internal dictionary
		self.__accounts[ID] = account

		#Sync the newly added account
		self.sync(account)

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
			account = pickle.loads(rc["data"])
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
		assert isinstance(page, (int, long)), "page number must be an integer"
		assert isinstance(page_size, (int, long)), "page_size must be an integer"
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
			sql = " OFFSET ?"
			params += [page * page_size]
			sql = " LIMIT ?"
			params += [page_size]
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
		assert isinstance(page, (int, long)) and page >= 0, "page number must be an integer"
		assert isinstance(page_size, (int, long)) and page_size >= 0, "page_size must be an integer"
		assert account == None or isinstance(account, Account), "if account is specified it must be an instance of Account"
		#Prepare sql statement
		params = []
		sql = "SELECT * FROM users WHERE id IN (SELECT id FROM friends"
		if account != None:
			sql += " WHERE account = ?"
			params += [self.__getAccountID(account)]
		sql += ") ORDER BY name"
		if page_size > 0:
			sql = " OFFSET ?"
			params += [page * page_size]
			sql = " LIMIT ?"
			params += [page_size]
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
		assert isinstance(page, (int, long)) and page >= 0, "page number must be an integer"
		assert isinstance(page_size, (int, long)) and page_size >= 0, "page_size must be an integer"
		assert account == None or isinstance(account, Account), "if account is specified it must be an instance of Account"
		#Prepare sql statement
		params = []
		sql = "SELECT * FROM users WHERE id IN (SELECT id FROM followers"
		if account != None:
			sql += " WHERE account = ?"
			params += [self.__getAccountID(account)]
		sql += ") ORDER BY name"
		if page_size > 0:
			sql = " OFFSET ?"
			params += [page * page_size]
			sql = " LIMIT ?"
			params += [page_size]
		#Execute sql statement
		followers = self.__db.execute(sql, *params)
		#Return user generator
		for follower in followers:
			yield self.__parseUserRow(follower)

	def getReplies(self, To = None, From = None, page = 0, page_size = 0):
		"""Get replies

			To:			Get replies that are for this user, defaults to all
			From:		Get replies that are from this user, defaults to all
			page:		Page number to return, default to 0
			page_size:	Number of entries on each page, default to 0, meaning unlimited

			Note: Please set page_size unless all replies are wanted. This method returns a
			generator, so performance should be quite good.
		"""
		assert isinstance(page, (int, long)) and page >= 0, "page number must be an integer"
		assert isinstance(page_size, (int, long)) and page_size >= 0, "page_size must be an integer"		
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
			sql = " OFFSET ?"
			params += [page * page_size]
			sql = " LIMIT ?"
			params += [page_size]
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
		assert isinstance(page, (int, long)) and page >= 0, "page number must be an integer"
		assert isinstance(page_size, (int, long)) and page_size >= 0, "page_size must be an integer"		
		params = []
		sql = "SELECT * FROM tweets WHERE "
		#Add to condition
		if To == None:
			sql += "id IN (SELECT id FROM direct_messages)"
		else:
			assert isinstance(To, User), "to must be an instance of User"
			params += [To._getServiceID()]
			sql += "id IN (SELECT id FROM direct_message WHERE at = ?)"
		#Add optional from condition
		if From != None:
			assert isinstance(From, User), "from must be an instance of User"
			sql += " AND user = ?"
			params += [From._getServiceID()]
		#Order by creation
		sql += " ORDER BY created DESC"
		#Create optional pagnation
		if page_size > 0:
			sql = " OFFSET ?"
			params += [page * page_size]
			sql = " LIMIT ?"
			params += [page_size]
		#Execute sql
		msgs = self.__db.execute(sql, *params)
		#Return using generator
		for msg in msgs:
			yield self.__parseTweetRow(msg)

	def __parseTweetRow(self, row):
		"""Parse a database from the table of tweets"""
		return CachedMessage(self, self.__db, row)
		#user = self._getUser(self.row["user"])
		#service = self._getService(row["service"])
		#return Message(row["Message"], row["created"], user, row["suid"], service, row["service"])

	def __parseUserRow(self, row):
		"""Parse a database from the table of users"""
		return CachedUser(self, row)
		#return User(row["name"], row["username"], self._getService(row["service"]), row["url"], row["location"], row["description"], row["image"], row["service"])
		

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
	def __init__(self, store, message = None, user = None, service = None, created = None, suid = 0, reply_at = None, reply_to = None, direct_at = None, data = None):
		""" Create an instance of Message

			store:		TweetStore associated with this Message instance
			message:	Message text
			user:		User who wrote this message
			created:	Timestamp of message creation
			service:	Service string or identifier
			suid:		Service unique identifier, need not be unique
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
			self._reply_to = User(self.__store, data = data["reply_to"])
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
		assert isinstance(db, database.ThreadSafeDatabase), "db must be an instance of ThreadSafeDatabase"
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
	"""Thrown if method on account is called before the instance have been assigned an owner"""
	def __init__(self, text = None):
		self._text = text
	def __str__(self):
		if test:
			return "Account has no owner: " + text
		else:
			return "Account has no owner."

class Account:
	"""	An account for TweetStore

		How accounts subclasses of this is initialized should not matter to TweetStore,
		however, subclasses should at all times return a user from getUser(). The other
		methods should also work, unless offline, once TweetStore.addAccount is called.
	"""
	def _getMessages(self):
		"""Returns messages in a list of tuples: [(message, created, username, account), ] or False
		If false is return user interaction is needed and status have been changed to reflect this.

		This method should return all messages that need to be cached. E.g. the users timeline, replies to
		the user.
		"""
		raise NotImplementedError, "_getMessages must be overwritten in subclasses of Account"

	def _getFriends(self):
		"""Returns friends in a list of User or False
		If False is returned user interactions is required to fix the problem.
		E.g. connection must be restored or account reauthendicated, anyway synchronization of 
		this account shouldn't preceed.
		"""
		raise NotImplementedError, "_getFriends must be overwritten in subclasses of Account"

	def _getFollowers(self):
		"""Get followers as a list of followers"""
		raise NotImplementedError, "_getFollowers must be overwritten in subclasses of Account"

	def _postMessage(self, message):
		"""Post a message

			If authendication fails or service is offline, onStatusChange event on store should be raised.
		"""
		raise NotImplementedError, "_postMessage must be overwritten in subclasses of Account"

	def reauthendicate(self, password = None):
		"""Reauthendicate, called if status = 'bad authendication'
		Note this method changes password, if login is successfull
		"""
		raise NotImplementedError, "reauthendicate must be overwritten in subclasses of Account"

	def _setOwner(self, store):
		"""Sets the owner of this Account, must be called before, getUser(), reauthendicate or any of the
			_get....() methods are called."""
		raise NotImplementedError, "set owner must be implemented in subclasses of Account"

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
