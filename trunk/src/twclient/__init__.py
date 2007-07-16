#!/usr/bin/python
#
#   Author : Pierre-Jean Coudert
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; version 2 of the License.
# 
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
 
 
"""
  The Twitter Client encapsulated for Pwytter
"""

import twitter
import urllib2
import StringIO
import os.path
import Queue
import threading
from PIL import Image, ImageTk

class TwClient(object):
    def __init__(self, aVersion, aUser, aPassword):
        self.user, self.password = aUser, aPassword      
        self.api = twitter.Api(self.user,self.password)
        self.api.SetCache(None)
        self.api.SetXTwitterHeader('Pwytter', 'http://www.pwytter.com/files/meta.xml', aVersion)       

        self._imageLoading = Image.open(os.path.join("media",'loading.png'))
        self._imageLoading.thumbnail((32,32),Image.ANTIALIAS)
                       
        self._statuses =[]
        self.texts = []
        self._friends = []
        self.Friends=[]
        self._followers = []
        self.Followers=[]
        #Cache
        self._usercache={}
        self._imagecache={}        
        self._requestedImageList=[]
        self._imageQueue=Queue.Queue()
        self._userQueue=Queue.Queue()
        
        self._timeLines=("Public","User","Friends")
        self._currentTimeLine = 1

    def login(self, aUser, aPassword):
        self.user, self.password = aUser, aPassword     
        self.api.SetCredentials(self.user, self.password)

    def getMyDetails(self):
        self.me = self.userFromCache(self.user)       
        loaded, self.myimage = self.imageFromCache(self.user)
        print "My details",self.me
        return loaded

    def nextTimeLine(self):
        self._currentTimeLine +=1
        if self._currentTimeLine>=len(self._timeLines):
            self._currentTimeLine = 0

    def timeLineName(self):
        return self._timeLines[self._currentTimeLine]
       
    def _getCurrentTimeLine(self):
        if self._timeLines[self._currentTimeLine]=="Public":
            self._statuses = self.api.GetPublicTimeline()
        elif self._timeLines[self._currentTimeLine]=="User":
            self._statuses = self.api.GetUserTimeline(self.user)
        else :
            self._statuses = self.api.GetFriendsTimeline()
            
    def refresh(self):
        self._getCurrentTimeLine()
        self.texts=[]
        for s in self._statuses :
            self._addUserToCache(s.user)
            try:
                atime= s.relative_created_at.encode('latin-1','replace')
            except Exception, e:
                print "Time conversion error:",e
                atime = "..."
            print s
            try :
                user_url = s.user.url.encode('latin-1','replace')
            except Exception, e:
                user_url = ""
            self.texts.append({"name": s.user.screen_name.encode('latin-1','replace'),
                               "msg" : s.text.encode('latin-1','replace'),
                               "time": "(%s)" % (atime),
                               "user_url" : user_url
                              })
                    
    def sendText(self,atext):
        self._statuses = self.api.PostUpdate(atext)
        
    def getFriends(self):
        self._friends = self.api.GetFriends()
        self.Friends=[]
        for f in self._friends :
            self._addUserToCache(f)
            friendName= f.screen_name.encode('latin-1','replace')
            self.Friends.append(friendName)

    def getFollowers(self):
        self._followers = self.api.GetFollowers()
        self.Followers=[]
        for f in self._followers :
            self._addUserToCache(f)
            fName= f.screen_name.encode('latin-1','replace')
            self.Followers.append(fName)
            
    def _threadLoadUserImage(self):
        aUserName=self._userQueue.get()
        print "load image:",aUserName
        auser = self.userFromCache(aUserName)
        if not auser :                
            return None
        imageurl = auser.profile_image_url.encode('latin-1')
        returnImage = Image.open(StringIO.StringIO(urllib2.urlopen(imageurl).read()))
        returnImage.thumbnail((32,32),Image.ANTIALIAS)
        self._imageQueue.put((aUserName,returnImage))
        print "image loaded:",aUserName, auser
        #self._userQueue.task_done()

    def _imagesToCache(self):
        while not self._imageQueue.empty():
            aName,aImage = self._imageQueue.get() 
            self._imagecache[aName]=aImage
            #self._imageQueue.task_done()

    def _requestImage(self, aUserName):
        if aUserName not in self._requestedImageList:
            self._requestedImageList.append(aUserName)
            self._userQueue.put(aUserName)
            t = threading.Thread(None,self._threadLoadUserImage)
            t.setDaemon(True)
            t.start() 
            
    def imageFromCache(self,name):
        self._imagesToCache()
        if name not in self._imagecache.keys() :
            self._requestImage(name)
            return False, self._imageLoading
        else :     
            return True, self._imagecache[name]
            
    def _addUserToCache(self, aUser):
        if aUser.screen_name not in self._usercache.keys() :  
            print "add user to cache:",aUser.screen_name
            self._usercache[aUser.screen_name]=aUser
            self._imagesToCache()
            self._requestImage(aUser.screen_name)
        
    def userFromCache(self,name):
        if name not in self._usercache.keys() :  
            print "load user:", name
            aUser=self.api.GetUser(name)  
            self._addUserToCache(aUser)       
            return aUser
        else :     
            return self._usercache[name]
