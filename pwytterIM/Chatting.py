import sys,xmpp
from PyQt4.QtCore import *
#!/usr/bin/python
# $Id: xtalk.py,v 1.2 2006/10/06 12:30:42 normanr Exp $
import sys,os,xmpp,time,select
import threading,pdb
from Queue import *
class Bot:

    def __init__(self,jabber,remotejid,queue):
        self.jabber = jabber
        self.remotejid = remotejid
	ReceivedTxt=""	
	self.queue=queue
		
    def register_handlers(self):
        self.jabber.RegisterHandler('message',self.xmpp_message)

    def xmpp_message(self, con, event):
        type = event.getType()
        fromjid = event.getFrom().getStripped()
        if type in ['message', 'chat', None] and fromjid == self.remotejid:
            try:
		sys.stdout.write(event.getBody() + '\n')
		text=unicode(event.getBody())
		if text!="None" :
			text=text+'\n'
			ReceivedTxt=text			
			print "got",ReceivedTxt
			self.queue.put(ReceivedTxt)
			print "put in queue"			
	    except Exception,e:
		print "error in bot",e

    def stdio_message(self, message):
        m = xmpp.protocol.Message(to=self.remotejid,body=message,typ='chat')
        self.jabber.send(m)
        pass

       

class Receive(QThread) :
  
   def __init__(self,parent,cl):
        super(Receive,self).__init__(parent)
	self.cl=cl
	self.parent=parent
   def run(self) :
      #print 'Thread', self.getName(), 'started.'
      self.close=True
      while self.close :
        try:
		self.cl.Process(1)
        	time.sleep(1)
	except Exception,e:
		print "error in chatting process",e
		pass
	

