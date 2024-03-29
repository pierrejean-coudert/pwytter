import sys
from os.path import dirname, join, abspath
print abspath(dirname(sys.path[0]))
sys.path.append(join(abspath(dirname(sys.path[0])),'src', 'twclient'))  
    
import time
import csv
import twclient
from pysqlite2 import dbapi2 as sqlite
import datetime
import threading
import urllib2
import re

class TwitterCrawler(object):
    def __init__(self):
        print "Twitter User crawler"
        self.tw=twclient.TwClient('0.5', 'pwytter', 'pwytter123')
        self.lastPublicScanTime=datetime.datetime.min
        
    def ConnectToDB(self):       
        self.con = sqlite.connect("users.sql")
        #self.con = sqlite.connect(":memory:")
        self.cur = self.con.cursor()
#  user.id
#  user.name
#  user.screen_name
#  user.location
#  user.description
#  user.profile_image_url
#  user.url
#  user.status
        
        try:
            self.con.execute("CREATE TABLE user(name VARCHAR(30) PRIMARY KEY, spiderdate TIMESTAMP)")
        except:
            pass
        self.InitMinScanDate()

    def ClearBadUsers(self):
        self.cur.execute("DELETE FROM user WHERE name=:who",{"who":u''})
        
    def InitMinScanDate(self):
        self.ClearBadUsers()
        try:
            self.cur.execute("SELECT MIN(spiderdate) FROM user")
            self.minScanDate=self.cur.fetchone()[0]
        except:
            self.minScanDate=datetime.datetime.min
        print "Min Scan Date",self.minScanDate
        
    def UserCount(self):
        self.cur.execute("SELECT COUNT(name) FROM user")
        return self.cur.fetchone()[0]

    def UserToScanCount(self):
        self.cur.execute("SELECT COUNT(name) FROM user WHERE spiderdate=:when",{"when":self.minScanDate})
        return self.cur.fetchone()[0]
            
    def AddUser(self,aName):
        self.cur.execute("SELECT * FROM user WHERE name=:who",{"who":aName})
        if not self.cur.fetchone():
            print '+ Adding',aName
            self.cur.execute('INSERT INTO user (name, spiderdate) VALUES (:who,:when)',{"who":aName, "when":datetime.datetime.min})
            self.con.commit()
    
    def SelectNextUserToCrawl(self):
        self.cur.execute("SELECT name FROM user WHERE spiderdate=:when LIMIT 5",{"when":self.minScanDate})
        try: 
            aUser= u''
            while aUser == u'':
                aUser= self.cur.fetchone()[0]
        except Exception,e:
            print '!SelectNextUserToCrawl:',str(e)
            aUser=None
        return aUser
    
    def AddFriends(self):
        friendsIgnoreCount= 21967
        friendNames = ['pwytter']
        friends = None
        while not friends:
            try:
                friends=self.tw.api.GetFriends()
            except Exception,e:
                print "!AddFriend:",str(e)
                
        for f in friends:
            friendNames.append(f.screen_name.encode('latin-1','replace'))
        print "friendNames", friendNames

        for aUser in Users[:friendsIgnoreCount]:
            aName= aUser[0]
            if aName not in friendNames:
                friendNames.append(aName)

        for aUser in Users:
            aName= aUser[0]
            if aName not in friendNames:
                try :
                    self.tw.api.CreateFriendship(aName)
                    friendsIgnoreCount +=1
                    print "**** Add friend:",aName,"No:",friendsIgnoreCount
                    for wait in range(56):
                        time.sleep(1)
                except Exception,e:
                    print "!AddFriend:",str(e)

    def ScanUserFriends(self, aName):
            friends = None
            retry = 0
            while not friends and retry<5:
                try:        
                    friends=self.tw.api.GetFriends(aName)
                except Exception,e:
                    print '!ScanUserFriends:',str(e)
                    print ' Try #',retry
                retry += 1
            if friends:
                for f in friends:
                    friendName= f.screen_name.encode('latin-1','replace')
                    self.AddUser(friendName)
            self.cur.execute('UPDATE user SET spiderdate=:when WHERE name=:who',{"who":aName, "when":datetime.datetime.now()})
            self.con.commit()


    def CrawlPublicTimeline(self):
        if datetime.datetime.now()-self.lastPublicScanTime> datetime.timedelta(seconds=5):
            self.lastPublicScanTime=datetime.datetime.now()
            print "-> Public TimeLineScan"

            s = urllib2.urlopen("http://twitter.com/").read()   
            for u in re.findall('<strong><a href="http://twitter\.com/.+">(.+)</a></strong>', s):
                self.AddUser(u)
        
            #for s in self.tw.api.GetPublicTimeline():
            #    self.AddUser(s.user.screen_name.encode('latin-1','replace'))
        
    def CrawlUsers(self):
        self.AddUser("pwytter")
        while True:
            try:
                self.CrawlPublicTimeline()
                username= self.SelectNextUserToCrawl()
                if username:
                    print '-> Scanning',username
                    self.ScanUserFriends(username)
                    count,toscan=self.UserCount(),self.UserToScanCount() 
                    scanned=count-toscan
                    print "   Scanned:",scanned, 'To Scan:',toscan, 'Total:',count, "Ratio:",1.0*toscan/scanned
                else:
                    self.InitMinScanDate()
            except Exception,e:
                print str(e)
          
if __name__ == "__main__":
    tc=TwitterCrawler()
    tc.ConnectToDB()
    
    global Users
    tc.cur.execute("SELECT name FROM user")
    Users=tc.cur.fetchall()
    t = threading.Thread(None,tc.AddFriends)
    t.setDaemon(True)
    t.start() 

    tc.CrawlUsers()
