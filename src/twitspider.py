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

class Spider(object):
    def __init__(self):
        print "Twitter User spider"
        self.tw=twclient.TwClient('0.5', 'pwytter', 'pwytter123')
        
    def ConnectToDB(self):       
        self.con = sqlite.connect("users.sql")
        #self.con = sqlite.connect(":memory:")
        self.cur = self.con.cursor()
        try:
            self.con.execute("CREATE TABLE user(name VARCHAR(30) PRIMARY KEY, spiderdate TIMESTAMP)")
        except:
            pass
        self.cur.execute("DELETE FROM user WHERE name=:who",{"who":u''})

        self.InitMinScanDate()
        
    def InitMinScanDate(self):
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
#        else:
#            print '- Already in:',aName
    
    def SelectNextUserToSpid(self):
        self.cur.execute("SELECT name FROM user WHERE spiderdate=:when LIMIT 5",{"when":self.minScanDate})
        try: 
            aUser= u''
            while aUser == u'':
                aUser= self.cur.fetchone()[0]
        except Exception,e:
            print 'SelectNextUserToSpid',str(e)
            aUser=None
        print 'Next to Scan',aUser,'len:',len(aUser)
        return aUser
    
    def AddFriends(self):
        friendsIgnoreCount=4206
        friendNames = ['pwytter']
        friends = None
        while not friends:
            try:
                friends=self.tw.api.GetFriends()
            except Exception,e:
                print str(e)
                
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
                    print "**** Add friend:",aName
                    for wait in range(56):
                        time.sleep(1)
                except Exception,e:
                    print str(e)

    def ScanUserFriends(self, aName):
            friends = None
            retry = 0
            while not friends and retry<5:
                try:        
                    friends=self.tw.api.GetFriends(aName)
                except Exception,e:
                    print 'ScanUserFriends error:',str(e)
                    print 'Try #',retry
                retry += 1
            if friends:
                for f in friends:
                    friendName= f.screen_name.encode('latin-1','replace')
                    self.AddUser(friendName)
            self.cur.execute('UPDATE user SET spiderdate=:when WHERE name=:who',{"who":aName, "when":datetime.datetime.now()})
            self.con.commit()
        
    def LoadUsers(self):
        self.AddUser("pwytter")
        while True:
            try:
                username= self.SelectNextUserToSpid()
                if username:
                    self.ScanUserFriends(username)
                    count,toscan=self.UserCount(),self.UserToScanCount() 
                    scanned=count-toscan
                    print "Scanned:",scanned, 'To Scan:',toscan, 'Total:',count, "Ratio:",1.0*toscan/scanned
                else:
                    self.InitMinScanDate()
            except Exception,e:
                print str(e)
          
if __name__ == "__main__":
    sp=Spider()
    sp.ConnectToDB()
    
    global Users
    sp.cur.execute("SELECT name FROM user")
    Users=sp.cur.fetchall()
    t = threading.Thread(None,sp.AddFriends)
    t.setDaemon(True)
    t.start() 

    sp.LoadUsers()
