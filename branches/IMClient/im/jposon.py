How to send a message using TweetStore:

store is assumed to be and instance of TweetStore

from tweetstore import Message, User

by_user = store.getAccounts(service = "twitter")[0].getUser()
#by_user is the user that posts this message, if I'm jopsen on twitter, this user will be jopsen

msg = Message("Hello world", by_user, "twitter")
store.postMessage(msg)

Now msg is a message written by the user of the first twitter account as an update...


If I wanted it to be a reply I'd write something like
recipient = User(store, "gogtes", "twitter", "Gogtes Suyash") 
msg = Message("Hello world", by_user, "twitter", reply_at = recipient)
store.postMessage(msg)
#This will post a reply from jopsen to gogtes on twitter. Assuming by_user is jopsen,

To ensure that you get the right user instances you can also use:
jopsen_user = store.getUser("jopsen", "twitter")
#Note this will raise exception if not in database



