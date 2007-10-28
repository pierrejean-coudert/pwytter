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
import pwCache
import urllib2
import StringIO
import os.path
import Queue
import threading
import simplejson
from PIL import Image, ImageTk

import re
from htmlentitydefs import name2codepoint

class TwClientError(Exception):
  '''Base class for TwClient errors'''

def htmlentitydecode(s):
    return re.sub('&(%s);' % '|'.join(name2codepoint), 
            lambda m: unichr(name2codepoint[m.group(1)]), s)
    
StatusType = ['standard', 'reply', 'direct']    

class ExtStatus(twitter.Status):
    def __init__(self, created_at=None, id=None, text=None,
                 user=None, now=None, type='standard'):
        twitter.Status.__init__(self,created_at,id,text,user,now)
        self._type = type        
        
    def GetType(self):
        '''Get the type of this status.
        '''
        return self._type

    def SetType(self, type):
        '''Set the type of this status.
        '''
        self._type = type

    type = property(GetType, SetType,
                    doc='The type of this status.')        

class TwClient(object):
    def __init__(self, aVersion, aUser, aPassword):
        self.user, self.password = aUser, aPassword      
        self.api = twitter.Api(self.user,self.password)
        self.api.SetXTwitterHeaders('pwytter', 'http://www.pwytter.com/files/meta.xml', aVersion)       
        self.api.SetSource('pwytter')       

        self._cache= pwCache.PwytterCache()
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
        
        self.timeLines=("User","Friends","Replies","Direct", "Composite","Public")
        self._currentTimeLine = "Friends"
        
        self.VersionOK = self._checkversion(aVersion)
        
    def _checkversion(self, aVersion):
        versionURL="http://www.pwytter.com/files/PWYTTER-VERSION.txt"
        try:
            lastVersion= urllib2.urlopen(versionURL).read()
            print 'lastVersion',lastVersion
        except Exception,e:
            print "Unable to check Pwytter Version:",str(e)
            lastVersion = aVersion
        return lastVersion == aVersion
        
    def login(self, aUser, aPassword):
        self.user, self.password = aUser, aPassword     
        self.api.SetCredentials(self.user, self.password)

    def getMyDetails(self):
        self.me = self.userFromCache(self.user)       
        loaded, self.myimage = self.imageFromCache(self.user)
        print "My details",self.me
        return loaded

    def setTimeLine(self, timelineName):
        if timelineName in self.timeLines:
            self._currentTimeLine = timelineName

    def timeLineName(self):
        return self._currentTimeLine
       
    def _getCurrentTimeLine(self):
        if self._currentTimeLine=="Public":
            self._statuses = self.StatusesToExt(self.api.GetPublicTimeline(),'standard')
        elif self._currentTimeLine=="User":
            self._statuses = self.StatusesToExt(self.api.GetUserTimeline(self.user),'standard')
        elif self._currentTimeLine=="Replies":
            self._statuses = self.StatusesToExt(self.api.GetReplies(),'reply')
        elif self._currentTimeLine=="Direct":
            self._statuses = self.getDirectsAsStatuses()
#        elif self._currentTimeLine=="Favorites":
#            self._statuses = self.StatusesToExt(self.api.GetFavorites(self.user),'standard')                       
        elif self._currentTimeLine=="Composite":
            self._statuses = self.StatusesToExt(self.api.GetFriendsTimeline(),'standard') \
                                + self.StatusesToExt(self.api.GetReplies(),'reply') \
                                + self.getDirectsAsStatuses()
            self._statuses.sort(key=ExtStatus.GetCreatedAtInSeconds,
                                reverse=True)
        else :
            self._statuses = self.StatusesToExt(self.api.GetFriendsTimeline(),'standard')

    def StatusesToExt(self, aTimeline, aType):
        """ return a status list as a ExtStatus list
        """
        statuses=[]
        for status in aTimeline:
            extstatus = ExtStatus(               
               created_at=status.created_at,
               id=status.id,
               text=status.text,
               user=status.user,
               type=aType)
            statuses += [extstatus]
        return statuses
            
    def getDirectsAsStatuses(self):
        """ return a DirectMessages list as a ExtStatus list
        """
        directs=self.api.GetDirectMessages()
        statuses=[]
        for direct in directs:
            auser=self.api.GetUser(direct.sender_id)
            status = ExtStatus(               
               created_at=direct.created_at,
               id=direct.id,
               text=direct.text,
               user=auser,
               type='direct')
            statuses += [status]
        return statuses


#    def getFavorites(self, user=None):
#        '''Fetch the sequence of favorited twitter.Status messages for a user
#    
#        The twitter.Api instance must be authenticated if the user is private.
#    
#        Args:
#          user:
#            Specifies the ID or screen name of the user for whom to return
#            the friends_timeline.  If unspecified, the username and password
#            must be set in the twitter.Api instance.  [optional]
#    
#        Returns:
#          A sequence of twitter.Status instances, one for each message
#        '''
#        url = 'http://twitter.com/favorites.json'
#        if not user and not self._username:
#          raise TwitterError("User must be specified if API is not authenticated.")
#        parameters = {}
#        if user:
#          parameters['id'] = user
#        json = self.api._FetchUrl(url, parameters=parameters)
#        data = simplejson.loads(json)
#        return [Status.NewFromJsonDict(x) for x in data]

    def createFavorite(self, id):
        '''Favorites the status specified in the ID parameter as the authenticating user.  
    
        The twitter.Api instance must be authenticated and thee
        authenticating user must be the author of the specified status.
    
        Args:
          id: The numerical ID of the status you're trying to favorite.
    
        Returns:
          A twitter.Status instance representing the status message
        '''
        try:
          if id:
            int(id)
        except:
          raise TwClientError("id must be an integer")
        #url = 'http://twitter.com/favorites/create/%s.json' % id
        url = 'http://twitter.com/favourings/create/%s' % id
        json = self.api._FetchUrl(url)
        #data = simplejson.loads(json)
        return None #Status.NewFromJsonDict(data)

    def isFavorite(self, screen_name, id):
        '''Favorites the status specified in the ID parameter as the authenticating user.  
    
        The twitter.Api instance must be authenticated and thee
        authenticating user must be the author of the specified status.
    
        Args:
          screen_name :
          id: The numerical ID of the status you're trying to favorite.
    
        Returns:
          A twitter.Status instance representing the status message
        '''
        try:
          if id:
            int(id)
        except:
          raise TwClientError("id must be an integer")
        url = 'http://twitter.com/%s/statuses/%s ' % (screen_name, id)
        favocache = self._cache.GetTimeout(url,3600*24)
        if not favocache:
            html = self.api._FetchUrl(url)
            favorited = html.find('Icon_star_full') > 0
            print str(favorited)
            self._cache.Set(url,str(favorited))
        else :
            favorited = (favocache == "True")
        return favorited 

    def destroyFavorite(self, id):
        '''Un-favorites the status specified in the ID parameter as the authenticating user.
    
        The twitter.Api instance must be authenticated and thee
        authenticating user must be the author of the specified status.
    
        Args:
          id: The numerical ID of the status you're trying to favorite.
    
        Returns:
          A twitter.Status instance representing the un-favorited status message
        '''
        try:
          if id:
            int(id)
        except:
          raise TwClientError("id must be an integer")
        #url = 'http://twitter.com/favorites/destroy/%s.json' % id
        url = 'http://twitter.com/favourings/destroy/%s' % id
        json = self.api._FetchUrl(url)
        #data = simplejson.loads(json)
        return None #Status.NewFromJsonDict(data)

        
    def refresh(self):
        self._getCurrentTimeLine()
        self.texts=[]
        for s in self._statuses :
            self._addUserToCache(s.user)
            atime= s.relative_created_at
#            try:
#                atime= s.relative_created_at.encode('latin-1','replace')
#            except Exception, e:
#                print "Time conversion error:",e
#                atime = "..."
            print s
            try :
                user_url = s.user.url.encode('latin-1','replace')
            except Exception, e:
                user_url = ""
            self.texts.append({"name": s.user.screen_name.encode('latin-1','replace'),
                               "id": s.id,
                               "msg" : s.text.encode('latin-1','replace'),
                               "msgunicode" : htmlentitydecode(s.text),
                               "time": "(%s)" % (atime),
                               "type" : s.type,
                               "user_url" : user_url,
                               "favorite" : False,
                               "favorite_updated" : False
                              })
            if self.texts[-1]['type'] <> 'direct':
                pass
                print s.id,self.isFavorite(s.user.screen_name, s.id)
                    
    def sendText(self,aText):
        self._statuses = self.api.PostUpdate(aText)
        
    def sendDirectMessage(self, aUser, aText):
        return self.api.PostDirectMessage(aUser, aText)

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
        imageurl = auser.profile_image_url #.encode('latin-1')        
        LoadedImage=self._cache.GetUrl(imageurl, timeout=3600*24)
        returnImage = Image.open(StringIO.StringIO(LoadedImage))
        returnImage.thumbnail((32,32),Image.ANTIALIAS)
        self._imageQueue.put((aUserName,returnImage))
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
            self._usercache[aUser.screen_name]=aUser
            self._imagesToCache()
            self._requestImage(aUser.screen_name)
        
    def userFromCache(self, name):
        if name not in self._usercache.keys() :  
            userDict = self._cache.GetTimeout('user//'+name, timeout = 3600)
            if userDict :
                aUser = twitter.User.NewFromJsonDict(simplejson.loads(userDict))
                print "load from cache user:", name
            else:
                aUser = self.api.GetUser(name)  
                self._cache.Set('user//'+name,aUser.AsJsonString())
                print "load from api user:", name            
            self._addUserToCache(aUser)       
            return aUser
        else :     
            return self._usercache[name]
