import urllib
import pickle
import time
import sys
import os
from os.path import dirname, join, abspath

try:
    __app_path__ = abspath(dirname(__file__))
except:
    __app_path__ = abspath(dirname(sys.path[0]))

sys.path.append(join(__app_path__, 'simplejson'))
sys.path.append(join(__app_path__,'twclient'))
sys.path.append(join(__app_path__,'media'))

from twclient import twitter,simplejson

STORAGE_DIRECTORY = "~/.twitter"
IMAGE_DIRECTORY = "~/.twitter/images"

if os.name=='posix' :
    import pygtk
    pygtk.require('2.0')
    import pynotify
    import gtk


class TwitterStatus(object):
    """Manages history of Twitter status updates."""

    def __init__(self,user,passwd):

        self.user=user
        self.passwd=passwd
        self.count=0
        self.api=twitter.Api(username=user,password=passwd)
        self.store = {}
        self.storage = os.path.expanduser(STORAGE_DIRECTORY)
        self.image_storage = os.path.expanduser(IMAGE_DIRECTORY)
        if not os.path.exists(self.image_storage):
            os.makedirs(self.image_storage)

    def save(self):
        """Save storage file to disk."""
        filename = open(self.storage + "/twitter.pkl", 'w')
        pickle.dump(self.store, filename)
        filename.close()

    def load(self):
        """Load storage file from disk."""
        try:
            filename = open(self.storage + "/twitter.pkl", 'r')
            self.store = pickle.load(filename)
            filename.close()
        except IOError:
            self.store = {}
    def count_update(self,status) :
        """ this will count total number of updates that are unread"""
        if status.id not in self.store.keys():
            self.count=self.count+1

    def display_count(self) :
        text= self.user
        text= text + ", You have %d" % self.count
        text=text+" "+ " new tweets"
        imagenm="pwytter.png"
        if self.count!=0:
               send_note("Pwytter",text,imagenm)

    def check_status(self, status):
        """Check if a status update has already been stored.
        If not then store it and send a notification."""
        if status.id not in self.store.keys():
            try:
                username = status.user.name
            except AttributeError:
                username = status.sender_screen_name
            try:
                profile_image = status.user.profile_image_url
            except AttributeError:
                profile_image = self.api.GetUser(\
                                username).GetProfileImageUrl()

            # Find the image
            imagepath = self.cached_image(username)
            if not imagepath:
                imagepath = self.download_image(username,
                            profile_image)

            # Markup Hyperlinks
            text = status.text
            if "http://" in text:
                for i in text.split():
                    if i.startswith("http://"):
                        text = text.replace(i, \
                               '<a href="' + i + '">' + i + '</a>')

            # Call notification
            send_note(username, text, imagepath )

            # Add to dict
            self.store[status.id] = status

    def download_image(self, username, image_url):
        """Download new profile image."""
        fileextension = image_url.rpartition('.')[-1]
        targetname = self.image_storage + "/" + username + "." + fileextension
        urllib.urlretrieve(image_url, targetname)
        return targetname

    def cached_image(self, username):
        """Check for already downloaded profile image."""
        for i in os.listdir(self.image_storage):
            if i.startswith(username + "."):
                return i
            else:
                return None

def send_note(user, message, imageurl):
    """Send the note to the desktop."""
    if os.name == 'posix' :
        print "Linux notifications"
        if not pynotify.init("Pwytter"):
           sys.exit(1)
        note = pynotify.Notification(user, message, imageurl)
        if not note.show():
            print "Failed to send notification"
            sys.exit(1)
    else :
     str="growlnotify /t:\""+ user +"\""
     str=str+" "+ "/a:\"pwytter\"" +" "+ "/r:\"\"" +" "
     str=str+"/i:\""+imageurl + "\""
     str=str+ " /s:\"true\""
     str=str+ " \""+message+"\""
     os.system(str)








