import xmpp
import photo
import pdb

import sys,time
GTALK_SERVER = "talk.google.com"
from PyQt4.QtCore import *

class PresenceStatus(QObject):
	
	def __init__(self,parent):
		super(PresenceStatus,self).__init__(parent)
		self.parent=parent
		self.parent.nmtostatus = {}
		self.parent.nmtoshow = {}
		self.parent.nmtopresence = []
		self.parent.selfStatus = {}
		self.mutex = QMutex()
		self.jid_photo_map = {}
		self.nameQueue = self.parent.nameQueue
                self.msgQueue = self.parent.msgQueue

		self.connect(self,SIGNAL("ping()"),self.parent.ping)

	def receive_presence(self,session, stanza):
	 	self.flag=0
		jid = stanza['from'].getStripped()
		if jid == self.username:
			self.parent.selfStatus[self.username] = stanza.getType()
		
		else :  
			
			if stanza.getType() == None :
				self.mutex.lock()
                        	self.parent.nmtostatus[jid] = stanza.getStatus()
                        	self.parent.nmtoshow[jid] = stanza.getShow()
                        			
				self.mutex.unlock()
				if jid not in self.parent.nmtopresence :
					self.mutex.lock()
	                                self.parent.nmtopresence.append(jid)
					self.mutex.unlock()
							
			else :
				
				if jid in self.parent.nmtopresence :
					self.mutex.lock()
					self.parent.nmtopresence.remove(jid)
					del self.parent.nmtoshow[jid]
					del self.parent.nmtostatus[jid]					
					self.mutex.unlock()
	  
	        try:
                   vupdate = stanza.getTag('x', namespace='vcard-temp:x:update')
                   if not vupdate:
                         return
                   photo = vupdate.getTag('photo')
                   if not photo:
                         return
                   photo = photo.getData()
                except Exception ,e:
                          pass 
                if not photo:
			 return
                
                self.jid_photo_map[jid] = photo
	

    		        
	def xmpp_message(self, con, event):
        	type = event.getType()
        	fromjid = event.getFrom().getStripped()

        	if type in ['message', 'chat', None] :
                  try:
                        
                        text=unicode(event.getBody())
                        if text!="None" :
				text = text + '\n'                                
                                self.nameQueue.put(fromjid)
                                self.msgQueue.put(text)
                                self.emit(SIGNAL("ping()"))
                                
                  except Exception,e:
                       pass 
                        

	def login(self,username,password):
		self.username = username
		self.password = password
    		id = xmpp.protocol.JID(self.username)
    		self.jabber = xmpp.Client(id.getDomain(),debug=[])
    		con = self.jabber.connect((GTALK_SERVER,5222))
    		if not con:
            		return False
		
		
    		try:
			auth = self.jabber.auth(id.getNode(),self.password,resource = id.getResource())
    		except Exception , e :
			pass
			return False
	
		if not auth:
			
            		return False
    
		self.jabber.sendInitPresence()
    		self.jabber.RegisterHandler('presence', self.receive_presence)
    		self.jabber.RegisterHandler('message',self.xmpp_message)

		photo.register_handler(self.jabber)
    		
    		return self.jabber

	

	def getFilename(self,jid):

                if jid in self.jid_photo_map:
                        
                        photo_filename = photo.get_photo(self.jid_photo_map[jid])
                        
                else:
                                photo_filename = "./Default.png"

                return  photo_filename
	
	 
	def askForProbe(self)	:
	  Roster=self.jabber.getRoster()
          names=Roster.getItems()
          for name in names:
	
                pres=xmpp.Presence(to=name,typ="probe")
                try:
                        self.jabber.send(pres)
                except Exception,e:
                        pass 
			self.jabber=self.login(self.username,self.password)
			 

class Download(QThread):

	def __init__(self,parent):
	       super(Download,self).__init__(parent)
	       self.parent=parent	 	
               self.jabber = parent.success
	
	def run(self):
		
		self.close = True
		while self.close :
		    try :
			 
			byte=self.jabber.Process(1)	
			
			time.sleep(0.5)	
		    except Exception,e :
		         pass	
	
	
