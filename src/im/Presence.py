import xmpp
import photo
import pdb

import sys,time
GTALK_SERVER = "talk.google.com"
#This line will just specify server for jabbber client in this case it is gtalk
from PyQt4.QtCore import *

class PresenceStatus(QObject):

	"""

	PresenceStatus class handles functionalities to log in to Gtalk server using login function
	as well as this class opens stream to accept or receive presence of the friends available in friend's list.
	Presence of friends is shown by three main parameters show,status and type .
	
	Note :-
	show is used when gtalk user sets his status as busy,away or available.
	type tells whether he is online or not.If user is online then typereturn will be  NONE.
	If user is not online then its type return will be unavailable.
	status will give you status message set by user.

	Apart from receiving presence of friends this class also recevied messages sent by friends during interactive conversation as replies, 
	it does the same using function xmpp_message 
	for e.g : I am chatting with three users say a,b,c then messages sent by all these three guys will be acccepted in xmpp_message 
	function and then they are processed.
	"""	 
	def __init__(self,parent):

		"""
		init will accept parent as login form, as well as it will set all the dictionaries to {}
		nmtostatus , nmtoshow and nmtopresence these dictionaries are used to store the status,show and presence resepctively.
		nmaeQueue will put name of sender in queue when messages comes as reply e.g I am chatting with two users say A & B then 
		whenever I get reply from user A then his name i.e A will be stored in nameQueue and his message or reply will be stored in 
		msgQueue 			
		
		Note : whenever message comes SIGNAL ping is emmited and it is connected to function ping defined in the login form.
		this signal is emmited so that further processing of messages can take place.We need further processing because consider 
		e.g we are talking with 3 users then also replies sent by them will be received as stream so we have to disntinguish who has sent what , 
		and after deciding sender and message we can send corresponding reply to respective window
		(where user types to send reply and view replies)
		"""

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
		
		"""

		this function is registered with xmpp_presence in login function.This function keeps track of presence sent by friends 
		whenever someone comes online then first this information is received using Process function called on instance of connection 
		like - cl.Process(1)
		and then actual information is processed in this function,so whenever any change regarding t presence of user is received,then this
		function will be called
		
		Note : this function also checks whether sender has any Avtar or photo and if he has then that photo is downloaded and 
		it is mapped to photo id and location of downloaded photo.
		This mapping takes place in jid_photo_map dictionary
		"""
	
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
		
		"""
		
		xmpp_message : This function is also registered in log in form and it is called whenever we get any reply from from person
		we are communicating with , the actual message is received using same function like cl.Process() and in this function
		name of sender and message are put in queues nameQueue and messageQueue respectively
		"""

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

		"""
		
		login : This function handles all login related activities, it authenticates user on gtalk server and
		return connection handler
		"""
	
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
		
		"""
		
		getFilename : As user id and photo's location are stored in jid_photo_map,
		this function just returns exact path of file name (in which photo is stored)
		if it doesnt get any path then it just returns path as Default.png
		"""

                if jid in self.jid_photo_map:
                        
                        photo_filename = photo.get_photo(self.jid_photo_map[jid])
                        
                else:
                                photo_filename = "./Default.png"

                return  photo_filename
	
	 
	def askForProbe(self)	:

	  """
	  
	  askForProbes : This function will send probe request to ask everyone for their presence,if we dont call this method then we will not get
	  accurate results
	  Note : Roster is our friedslist.
          """
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

	
	"""

	This class will create new thread to download the data
	data is downloaded using function Process() and after receiving data functions like receive_presence and xmpp_message
	will be called
	"""
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
	
	
