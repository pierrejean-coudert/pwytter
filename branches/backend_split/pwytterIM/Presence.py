import xmpp
import photo
import pdb

import sys,time
GTALK_SERVER = "talk.google.com"
from PyQt4.QtCore import *

class PresenceStatus:
	
	def __init__(self):
		self.nmtostatus={}
		self.nmtoshow={}
		self.nmtopresence=[]
		self.selfStatus={}
		self.jid_photo_map={}
	def receive_presence(self,session, stanza):
	 	jid = stanza['from'].getStripped()
		if jid == self.username:
			self.selfStatus[self.username]=stanza.getType()
		
		else :
			if stanza.getType()== None :
                        	self.nmtostatus[jid]=stanza.getStatus()
                        	self.nmtoshow[jid]=stanza.getShow()
                        	if jid not in self.nmtopresence :
                                	self.nmtopresence.append(jid)
				
			else :
				print jid,stanza.getType()
				if jid in self.nmtopresence :
				
					self.nmtopresence.remove(jid)
    			try:
		  		vupdate = stanza.getTag('x', namespace='vcard-temp:x:update')
    		  		if not vupdate:
        	 			return
    		  		photo = vupdate.getTag('photo')
    		  		if not photo:
        				return
		  		photo =	photo.getData()
    			except Exception ,e:
				print "ERROR" ,e
			if not photo:
        			return
    			self.jid_photo_map[jid] = photo
    		

	def login(self,username,password):
		self.username=username
		self.password=password
    		id=xmpp.protocol.JID(self.username)
    		self.jabber=xmpp.Client(id.getDomain(),debug=[])
    		con=self.jabber.connect((GTALK_SERVER,5222))
    		if not con:
            		return False
		print "connected"
		self.download=Download(self.jabber)
    		#self.download.start()
    		try:
			auth=self.jabber.auth(id.getNode(),self.password,resource=id.getResource())
    		except Exception ,e :
			print "couldnt authenticate"
			return False
	
		if not auth:
			print "couldnt authenticate"
            		return False
    		print "authenticated"
		self.jabber.sendInitPresence()
    		self.jabber.RegisterHandler('presence', self.receive_presence)
    		photo.register_handler(self.jabber)
    		print "successfully connected"
    		return self.jabber

	def getDownload(self):
		return self.download

	def getFilename(self,jid):

                if jid in self.jid_photo_map:
                        
                        photo_filename = photo.get_photo(self.jid_photo_map[jid])
                        
                else:
                                photo_filename = ""

                return  photo_filename
	
	 
	def askForProbe(self)	:
	  Roster=self.jabber.getRoster()
          names=Roster.getItems()
          for name in names:
		print name
                pres=xmpp.Presence(to=name,typ="probe")
                try:
                        self.jabber.send(pres)
                except Exception,e:
                         print "Probe error",e
			 self.jabber=self.login(self.username,self.password)
			 print "calling log in again"

class Download(QThread):

	def __init__(self,j):
	       super(Download,self).__init__() 	
               self.j=j
	
	def run(self):
		#print 'Thread',self.getName(),'started'
		self.close=True
		while self.close:
		    try :
			print self.j 
			byte=self.j.Process(1)	
			print byte
			time.sleep(1)	
		    except Exception,e :
			print "error in process in Presence",e
	

