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
import time
from urlparse import urlparse,urlunparse
from PIL import Image, ImageTk

import re
from htmlentitydefs import name2codepoint

class TwClientError(Exception):
  '''Base class for TwClient errors'''

def htmlentitydecode(s):
    return re.sub('&(%s);' % '|'.join(name2codepoint), 
            lambda m: unichr(name2codepoint[m.group(1)]), s)

def urlExtract(msg):
    urlstart = msg.find("http://")
    if urlstart > -1 :
        msgurl = msg[urlstart:].split(' ')[0]
        urlDetected = urlunparse(urlparse(msgurl)).split('"')[0]
        print "url detected:", urlDetected
    else:
        urlDetected = ''
    return urlDetected
    
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

class PwDeferedTimeline(object):
    """ An ansynchronous URL loader. It uses URL Filesystem caching
        It can use an _NewObjectFromURL function to create an object from the data
        This object is cached in a dict (url,object) in memory
    """
    def __init__(self, pwClient=None, timeout=500):
        self._pwClient = pwClient
        self._notAvailableTimeLine = notAvailableObject
        self._timeout = timeout
        
        self._urlQueue = Queue.Queue()
        self._objectQueue = Queue.Queue()
        self._urlCache = PwytterCache()
        self._dataCache = {}
        self._requestedUrls = []
        
    def _threadLoadData(self):
        timeline=self._urlQueue.get()
        data=self._pwClient()._getCurrentTimeLine()
        self._objectQueue.put((data_url, data))       
        #self._objectQueue.task_done()

    def _dataToCache(self):
        while not self._objectQueue.empty():
            timeline,dataObject = self._objectQueue.get() 
            self._dataCache[timeline]=dataObject
            #self._dataCache.task_done()

    def _requestData(self, timeline):
        if url not in self._requestedUrls:
            self._requestedUrls.append(timeline)
            self._urlQueue.put(timeline)
            t = threading.Thread(None,self._threadLoadData)
            t.setDaemon(True)
            t.start() 
            
    def getData(self, timeline):
        """  getData returns the object/data corresponding to url
             >>>>  (True, Object)
             If the requested URL is currently loading (in a separate thread) 
               getData returns then notAvailableObject object/data
             >>>>  (False, notAvailableObject)           
        """
        self._dataToCache()
        if timeline not in self._dataCache.keys() :
            self._requestData(timeline)
            time.sleep(self._timeout)
            self._dataToCache()
            if timeline not in self._dataCache.keys() :
               return False, self._notAvailableObject
        return True, self._dataCache[timeline]

class TwClient(object):
    def __init__(self, aVersion, aUser, aPassword):
        self.user, self.password = aUser, aPassword      
        self.api = twitter.Api(self.user,self.password)
        self.api.SetXTwitterHeaders('pwytter', 'http://www.pwytter.com/files/meta.xml', aVersion)       
        self.api.SetSource('pwytter')       

        self._cache= pwCache.PwytterCache()
        self._imageLoading = Image.open(os.path.join("media",'loading.png'))
        self._imageLoading.thumbnail((32,32),Image.ANTIALIAS)
        self._imageLoader=pwCache.PwDeferedLoader(NewObjectFromURL=self.ConvertImage, 
                                                    notAvailableObject=self._imageLoading, 
                                                    timeout=3600*24)

        self._favoriteLoader=pwCache.PwDeferedLoader(NewObjectFromURL=self.ConvertFavoriteHTML, 
                                                    notAvailableObject=False, 
                                                    timeout=3600*24,
                                                    urlReader= self.api._FetchUrl)
        self._statuses =[]
        self.texts = []
        self._friends = []
        self.Friends=[]
        self._followers = []
        self.Followers=[]
        self._usercache={}
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
        statuses=[]
        try:
            directs=self.api.GetDirectMessages()
            for direct in directs:
                try :
                    auser=self.userFromCache(direct.sender_screen_name)
                except :
                    auser=self.userFromCache('Pwytter')              
                extstatus = ExtStatus(               
                   created_at=direct.created_at,
                   id=direct.id,
                   text=direct.text,
                   user=auser,
                   type='direct')
                statuses += [extstatus]
        except Exception, e:
            print str(e)
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

    def createFavorite(self, screen_name, id):
        '''Favorites the status specified in the ID parameter as the authenticating user.  
    
        The twitter.Api instance must be authenticated and thee
        authenticating user must be the author of the specified status.
    
        Args:
          id: The numerical ID of the status you're trying to favorite.
        '''
        try:
          if id:
            int(id)
        except:
          raise TwClientError("id must be an integer")
        url = 'http://twitter.com/favourings/create/%s' % id
        json = self.api._FetchUrl(url)
        #update cache 
        url = 'http://twitter.com/%s/statuses/%s ' % (screen_name, id)
        self._cache.Set(url,str(True))

    def isFavorite(self, screen_name, id):
        '''Favorites the status specified in the ID parameter as the authenticating user.  
    
        The twitter.Api instance must be authenticated and thee
        authenticating user must be the author of the specified status.
    
        Args:
          screen_name :
          id: The numerical ID of the status you're trying to favorite.
    
        Returns:
          loaded, favorited
        '''
        try:
          if id:
            int(id)
        except:
          raise TwClientError("id must be an integer")
        url = 'http://twitter.com/%s/statuses/%s ' % (screen_name, id)
        return self._favoriteLoader.getData(url) 

    def ConvertFavoriteHTML(self, data):
        return data.find('Icon_star_full') > 0
        
    def destroyFavorite(self, screen_name,  id):
        '''Un-favorites the status specified in the ID parameter as the authenticating user.
    
        The twitter.Api instance must be authenticated and thee
        authenticating user must be the author of the specified status.
    
        Args:
          id: The numerical ID of the status you're trying to favorite.
        '''
        try:
          if id:
            int(id)
        except:
          raise TwClientError("id must be an integer")
        url = 'http://twitter.com/favourings/destroy/%s' % id
        json = self.api._FetchUrl(url)
        #update cache 
        url = 'http://twitter.com/%s/statuses/%s ' % (screen_name, id)
        self._cache.Set(url,str(False))
        
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
                
            loaded, favorited = False, False
            if s.type <> 'direct':
                loaded, favorited = self.isFavorite(s.user.screen_name, s.id)
                print "loaded",loaded, "favorited", favorited
                
            msg = htmlentitydecode(s.text).encode('latin-1','replace')                              
            self.texts.append({"name": s.user.screen_name.encode('latin-1','replace'),
                               "id": s.id,
                               "msg" : msg,
                               "msgunicode" : htmlentitydecode(s.text),
                               "url" : urlExtract(msg),
                               "time": "(%s)" % (atime),
                               "type" : s.type,
                               "user_url" : user_url,
                               "favorite" : favorited,
                               "favorite_updated" : loaded
                              })
                    
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
            
    def ConvertImage(self,image):
        returnImage = Image.open(StringIO.StringIO(image))
        returnImage.thumbnail((32,32),Image.ANTIALIAS)
        return returnImage
    
    def imageFromCache(self,name):
        auser = self.userFromCache(name)
        if not auser :                
            return False, self._imageLoading
        imageurl = auser.profile_image_url.encode('latin-1','replace')        
        return self._imageLoader.getData(imageurl)
           
    def _addUserToCache(self, aUser):
        if aUser.screen_name not in self._usercache.keys() :  
            self._usercache[aUser.screen_name]=aUser
        
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
