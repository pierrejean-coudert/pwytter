import sys,xmpp
#!/usr/bin/python
import sys,os,xmpp,time,select
from PyQt4.QtCore import *
class ReceiveBot(QObject):
    def __init__(self,jabber,parent,nqueue,msgqueue):
        super(ReceiveBot,self).__init__(parent)
	self.jabber = jabber
      	self.nameQueue=nqueue
	self.msgQueue=msgqueue
	self.parent=parent
	self.connect(self,SIGNAL("ping()"),self.parent.ping)
    def register_handlers(self):
        self.jabber.RegisterHandler('message',self.xmpp_message)

    def xmpp_message(self, con, event):
        type = event.getType()
        fromjid = event.getFrom().getStripped()
        
	if type in ['message', 'chat', None] :
		 try:
                	sys.stdout.write(event.getBody() + '\n')
                	text=unicode(event.getBody())
                	if text!="None" :
                        	text=text+'\n'
                        	ReceivedTxt=text
                                self.nameQueue.put(fromjid)
				self.msgQueue.put(ReceivedTxt)
				self.emit(SIGNAL("ping()"))
                        	print "put in queue"
            	 except Exception,e:
                	print "error while putting in queue in receiveall",e

	     

class ReceiveData(QThread) :
 
   def __init__(self,parent,cl):
	super(ReceiveData,self).__init__(parent)
	self.cl=cl
	self.parent=parent
   def run(self) :
           
      while  self.parent.success:
         try:
		self.cl.Process(1)
         except Exception,e :
		print "error while in process Receive",e
	 time.sleep(1)
      


