from tweetstore import User, Message, Account

"""
Mockup account implementation

Meant to make it easy to debug tweetstore and consumers.
"""

#TODO: Make this class work for newer version of TweetStore

class MockupAccount(tweetstore.Account):
	store = None
	status = "idle"
	def __init__(self, service = "MockupService", store):
		self.service = service
		self.counter = 0
		self._store = store
		
	def _getMessages(self):
		msgs = []
		msgs += [self.__genMessage()]
		self.counter += 1
		msgs += [self.__genMessage()]
		self.counter += 1
		return msgs

	def _getFriends(self):
		friends = []
		friends += [self.__genUser("FakeFriend")]
		self.counter += 1
		friends += [self.__genUser("FakeFriend")]
		return friends
	
	def _getFollowers(self):
		followers = []
		followers += [self.__genUser("FakeFollower")]
		self.counter += 1
		followers += [self.__genUser("FakeFollower")]
		return followers
		
	def _postMessage(self, message, user = None):
		return True

	def reauthendicate(password = None):
		self._store.onStatusChange.raiseEvent(self, "idle")

	def getUser(self):
		img_id = self._store._catchImage("http://static.twitter.com/images/default_profile_bigger.png")
		return User("FakeMe", "fakeme", self.service, img_id, self._store)

	def getService(self):
		return self.service
		
	def getStatus(self):
		return self.status

	def __genUser(self, name = "FakeUser"):
		img_id = self._store._catchImage("http://static.twitter.com/images/default_profile_bigger.png")
		return User(name + " " + self.counter, "usernumber" + self.counter, self.service, img_id, self._store)
	
	def __getMessage(self):
		return Message("Message number " + self.counter, time.time(), self.__genUser("FakePoster"))
		
	def __getstate__(self):
		data = {}
		data["service"] = self.service
		data["counter"] = self.counter
		return data

	def __setstate__(self, data):
		self.service = data["service"]
		self.counter = data["counter"]


