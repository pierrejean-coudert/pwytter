#!/usr/bin
import sys,time,os
from Queue import *
import xmpp 
import pwNotifyParams
from PyQt4.QtGui import *
from PyQt4.QtCore import *

import Presence
from Mapping import *
from login import *
from AddFriend import * 
from MainWindow import *
from ChatWindow import *

sys.path.append('../tweetstore')
from tweetstore import Message, User



class LogInScreen(QDialog,Ui_frm_login):
    ''' 
     This class basically displays log in screen for IMclient 
    '''	
	
    def __init__(self , store , parent = None) :
	photo_directory="./photos"
        if not os.path.exists(photo_directory):
	  os.makedirs(photo_directory)
        
        self.nameQueue = Queue(10)
        self.msgQueue = Queue(10)
	
        super(LogInScreen,self).__init__(parent)
        self.setupUi(self)
	self.mutex = QMutex()	
        self.presence = Presence.PresenceStatus(self)
        self.success = False
	self.store = store
	print type(self.store)
        self.connect(self.buttonCancel,SIGNAL("clicked()"),self,SLOT("close()"))
        self.connect(self.buttonSignIn,SIGNAL("clicked()"),self.authenticateUser)
	
    
    def authenticateUser(self):

        self.username = str(self.lEditUserName.text())
        self.password = str(self.lEditPassword.text())
        if not self.username.find("@gmail.com") > 0 :

            self.username = self.username + "@gmail.com"
            
        self.threadRotate = Rotate(self)
        self.threadRotate.start()
       
        self.threadAuthenticate=Authenticate(self)
        self.threadAuthenticate.start()
        
	self.connect(self.threadRotate,SIGNAL("finished()"),self.threadRotate,SLOT("deleteLater()"))
	self.connect(self.threadAuthenticate,SIGNAL("finished()"),self.checkAuthentication)
	self.connect(self.threadAuthenticate,SIGNAL("finished()"),self.threadAuthenticate,SLOT("deleteLater()"))		
    
    def checkAuthentication(self) :	
	
        if self.success :

            self.threadRotate.success = False
	    self.presence.askForProbe()
	   
	    self.threadReAuthenticate = Authenticate(self)
	    self.threadReAuthenticate.start()
	 
	    self.connect(self.threadReAuthenticate,SIGNAL("finished()"),self.displayMainWindow)
	    self.connect(self.threadReAuthenticate,SIGNAL("finished()"),self.threadReAuthenticate,SLOT("deleteLater()"))
	    
			
        else :
	    self.threadRotate.success = False
	    QMessageBox.warning(self,"Authentication error !","Please check your username and password !")
            self.lEditPassword.setText("")
            


    def displayMainWindow(self):
	    
            self.download = Presence.Download(self)
            self.main_frm = MainWindow(self)
	    self.download.start()	
            
	    self.main_frm.show()
	    self.setHidden(True)
            time.sleep(9)
	    self.addBuddies = AddBuddies(self)
            self.connect(self.addBuddies,SIGNAL("photoLoad()"),self.load)
	    self.connect(self,SIGNAL("popup()"),self.main_frm.popup)
	    self.addBuddies.start()
	    mypath = self.presence.getFilename(self.username)	
	    try :
		pic=QPixmap(mypath)
                self.main_frm.lblPhoto.setPixmap(pic)    
	    except Exception ,e :
		pass
          	
    def load(self):

            pic=QPixmap(self.addBuddies.path)
            ico=QIcon(pic)
            self.addBuddies.buddy.setIcon(ico)
		  	    	
    def ping(self):
                
                if not self.nameQueue.empty():
                        self.sender=self.nameQueue.get()
                	if not self.msgQueue.empty():
                 	       self.msg=self.msgQueue.get()
	           	       self.emit(SIGNAL("popup()"))
	

class AddBuddies(QThread):
        

   def __init__(self,parent=None):
            
	    super(AddBuddies,self).__init__(parent)
            self.login_frm = parent
            self.main_frm = parent.main_frm
            self.close = True
            self.Frndlist = {}
            self.presence = parent.presence
	    self.deleteFrnds = [] 
	
   def run(self):


            count=len(self.login_frm.nmtopresence)
	   
            for i in range(count):
                  try :
                       nameOfFrnd=self.login_frm.nmtopresence[i]
                  except Exception,e:
                       pass 
                  self.addFriends(nameOfFrnd)



           
            while self.close:
		       	
                       time.sleep(30)
                       present = self.Frndlist.keys()
		       deleteCount = 0	

                       sortedlist = []
                       sortedlist = present
                       sortedlist.sort()
                       for changes in self.login_frm.nmtopresence :
                                if changes in present:
                                        pass
                                else :

					
                                        self.addFriends(changes)
                                        time.sleep(1)
		       len(present)
		       
                       for keyname in present:
                                if keyname in self.login_frm.nmtopresence :
                                        pass
                                else:
                                         
                                        index = 0
                                        for temp in sortedlist  :

                                                if keyname == temp :
                                                        break
                                                index = index+1
									
                                        self.deleteFrnds.append(keyname)
                                        try:
                                                if deleteCount > 0 :
						    index = index - deleteCount
						
						self.login_frm.mutex.lock()
						
                                                removeditem = self.main_frm.lstFrndList.takeItem(index)
						deleteCount = deleteCount + 1
						time.sleep(2)
						self.login_frm.mutex.unlock()
                                        except Exception,e:
                                                pass 
						pass	
		      
		       		
		       for frnd in self.deleteFrnds :
				
				if frnd in sortedlist :
		
					del self.Frndlist[frnd]
                       
		       self.deleteFrnds = [] 
		       keys = self.Frndlist.keys()	
		       for frnd in keys :
			
		       		listitem = self.Frndlist[frnd]
				try :
                			nmtoshw = self.login_frm.nmtoshow[frnd]
                			nms = self.login_frm.nmtostatus[frnd]
        			except Exception ,e :
                		        pass	
					pass
        			if nmtoshw == "away" :
                			nmtoshw = " Away "
        			elif nmtoshw == "dnd" :
                			nmtoshw = " Do Not Disturb "
        			else :
                			nmtoshw = " Available "
        			if nms == None:
              				nms ="Available"

        			if nms.find('\n') > 0 :
                				pos = nms.find('\n')
                				nms = nms[:pos]
        			if len(nms)>40 :
              					nms = nms[0:40]
              					nms = nms+"..."
        			text = frnd 

        			if len(text)>45 :
              				text = name[0:40]
              				text = text+"..."
        			text = text + nmtoshw + "\n" +nms
        			listitem.setText(text)
				

   def addFriends(self,name):
	
	self.buddy = QListWidgetItem()
        self.path = self.presence.getFilename(name)
        if  not self.path :
              self.path = "./Default.png"

        self.emit(SIGNAL("photoLoad()"))
        time.sleep(0.5)
	

	text =self.getText(name)
        self.buddy.setText(text)
        self.Frndlist[name] = self.buddy
               
        self.main_frm.lstFrndList.addItem(self.buddy)
		
        self.main_frm.lstFrndList.setSortingEnabled(True)
        self.main_frm.lstFrndList.sortItems(0)
		
	
   def getText(self,name) :
	try :
		nmtoshw = self.login_frm.nmtoshow[name]
	        nms = self.login_frm.nmtostatus[name]
	except Exception ,e :
		pass 
        if nmtoshw == "away" :
                nmtoshw = " Away "
        elif nmtoshw == "dnd" :
                nmtoshw = " Do Not Disturb "
        else :
                nmtoshw = " Available "
        if nms == None:
              nms ="Available"

        if nms.find('\n') > 0 :
                pos = nms.find('\n')
                nms = nms[:pos]
        if len(nms)>40 :
              nms = nms[0:40]
              nms = nms+"..."
        text = name

        if len(name)>45 :
              text = name[0:40]
              text = text+"..."
        text = text + nmtoshw + "\n" +nms
	return text
  	
class Rotate(QThread):
    
    def __init__(self,frm):
        super(Rotate,self).__init__(frm)
        self.login_frm = frm
        self.success = True
        self.login_frm.dSignIn.setNotchesVisible(True)


    def run(self):

        i=0
        while self.success:
            self.login_frm.dSignIn.setValue(i)
            time.sleep(0.1)
            i = i+10
            if i >= 99 :
                    i = 0




class Authenticate(QThread):

    def __init__(self,frm):

        super(Authenticate,self).__init__(frm)
        self.login_frm=frm
        

    def run(self):
               
                 self.login_frm.success = self.login_frm.presence.login(self.login_frm.username,self.login_frm.password)




    
class MainWindow(QMainWindow,Ui_BuddyList):

    def __init__(self,parent = None):

        super(MainWindow,self).__init__(parent)
        self.parent = parent
        self.setupUi(self)
        self.store = parent.store
	
	if not self.lstFrndList.hasMouseTracking():
                        self.lstFrndList.setMouseTracking(True)
	self.connect(self,SIGNAL("destroyed(QObject*)"),self,SLOT("closeEvent(QCloseEvent*)"))
        self.connect(self,SIGNAL("rejected()"),self.parent,SLOT("close()"))
	self.connect(self.action_Add_Contact,SIGNAL("triggered()"),self.addFriend)
	
	if not self.lstFrndList.hasMouseTracking():
                        self.lstFrndList.setMouseTracking(True)
        self.connect(self.lstFrndList,SIGNAL("itemEntered(QListWidgetItem *)"),self.setToolTipText)
        self.connect(self.lstFrndList,SIGNAL("itemClicked(QListWidgetItem *)"),self.memberClicked)
        self.connect(self.action_Quit,SIGNAL("triggered()"),self.quit)
        pic = QPixmap("Available.png")
        icon = QIcon(pic)
        self.cmdSetStatus.addItem(icon,"Available")
        pic = QPixmap("Away.png")
        icon = QIcon(pic)
        self.cmdSetStatus.addItem(icon,"Away")
        pic = QPixmap("Dnd.png")
        icon = QIcon(pic)
        self.cmdSetStatus.addItem(icon,"Don't Disturb")
	self.activeWindows = {}
        self.connect(self.cmdSetStatus , SIGNAL("currentIndexChanged(int)") , self.setShow)
	self.con = self.parent.success
        self.connect(self.lEditStatusUpdate,SIGNAL("textChanged()"),self.setStatus)
	self.lEditStatusUpdate.setToolTip("Enter Your Status Message !")
	self.connect(self.actionTwitter,SIGNAL("triggered()"),self.twitterMapping)
	self.by_user = self.store.getAccounts(service = "Twitter")[0].getUser()



    def quit(self):
		QCoreApplication.quit()

    def setShow(self, index) :
	
	show = self.cmdSetStatus.currentText()
	if show == "Available" :
		show = 'None'
	if show == "Away" :
		show = 'away'
	if show == "Don't Disturb" :
		show = 'dnd'
	try :
		self.con.send(xmpp.Presence(show = show))
	except Exception ,e :
		pass 

    def setStatus(self)	:
	
	status =unicode(self.lEditStatusUpdate.toPlainText())
        if status.find('\n') >= 0 :
                self.lEditStatusUpdate.setText("")
	try :
		self.con.send(xmpp.Presence(status = status))
	except Exception ,e :
		pass

    def popup(self):
                
                self.sender = self.parent.sender
		self.msg = self.parent.msg

		keys = self.activeWindows.keys()
		
		if  self.sender not in keys :
			member = self.parent.addBuddies.Frndlist
    		  	chat=ChatWindow(self,self.sender)
         		chat.show()
			chat.setWindowTitle(self.sender)
			text = self.sender + " :- " + self.msg
			chat.ShowChat.setText(text)
         		self.activeWindows[self.sender] = chat

		else :

			chat = self.activeWindows[self.sender]
			text = chat.ShowChat.toPlainText()
			text = text + self.sender + " :- " + self.msg
			chat.ShowChat.setText(text)
			
		
    def setToolTipText(self,member):
                fname = unicode(member.text())
		p = fname.find(' ')
		sname = fname[:p]
		              
                sname = sname.rstrip()
                try :
			stext = self.parent.nmtostatus[sname]
		except Exception ,e :
                        pass 
			stext = ""
		p = fname.find('\n')
	        imagepath = self.parent.presence.getFilename(sname)

		sname = fname[:p]
		
		try :
                  if imagepath:
                        text= '<img src=%s style="float:left"></img><div style="float:left"><b>%s</b><br><br>%s</div>' % (imagepath,sname,stext)
                  else :
                        text = '%s%s' % (sname,stext)

                except Exception ,e :
                       pass 	
		
		member.setToolTip(text)
  	
 		

    def memberClicked(self,member) :
	 
	sendTo = unicode(member.text())
	pos = sendTo.find(' ')
	 	
	sendTo = sendTo[:pos]
	sendTo = sendTo.rstrip() 
	keys = self.activeWindows.keys()
	if sendTo not in keys :
		chat=ChatWindow(self,sendTo)
		chat.show()
		chat.setWindowTitle(sendTo)
       		self.activeWindows[sendTo] = chat

    def closeEvent(self,event):
        	
	self.closeAll()
  
    def closeAll(self):
	self.parent.close=False
        self.emit(SIGNAL("rejected()"))

    def addFriend(self) :
                addFriend=AddFriend(self)
                addFriend.show()


    def twitterMapping(self) :

	twitterAccount = TwitterAccount(self)
	twitterAccount.show()
	
class ChatWindow(QMainWindow,Ui_ChatWindow):

        def __init__(self,parent,sendTo):
                super(ChatWindow,self).__init__(parent)
                self.setupUi(self)
		self.store = parent.store
		self.parent=parent
		self.sendTo = sendTo
		self.lblName.setText(self.sendTo)
		self.jabber = self.parent.parent.success
		self.by_user = parent.by_user
		self.connect(self,SIGNAL("destroyed(QObject*)"),self,SLOT("closeEvent(QCloseEvent*)"))
                self.connect(self.txtMsgSend,SIGNAL("textChanged()"),self.send)

	def send(self):
                text = self.txtMsgSend.toPlainText()
                text = unicode(text)
                if text.find('\n')>= 0 :
                        self.txtMsgSend.setText("")
                        display = self.ShowChat.toPlainText()
                        display = display + "Me :-  " + text
                        self.ShowChat.setText(display)
			try :
				msg = xmpp.protocol.Message(to=self.sendTo , body=text , typ='chat')
        			self.jabber.send(msg)
				print type(self.store)
				recipient = User(self.store, "abcdef1suyash", "twitter", "Gogtes Suyash")
				msg = Message(self.store,"Hello world",self.by_user, "twitter", reply_at = recipient)
				print "lets c"
				self.store.postMessage(msg)

			except Exception ,e :
				QMessageBox.warning(self,"Network error !","Message sending failed !")
			        print "error" , e   	

	
	def closeEvent(self,event):
                try :
                        
                    del self.parent.activeWindows[self.sendTo]
                                  
                except Exception,e:
                      pass

        def getMessage(self):

                 display=self.ShowChat.toPlainText()
                 display=display +" " +self.sendTo + " :  "  + self.receivedText
                 try:
                        self.ShowChat.setText(display)
                 except Exception ,e:
			pass                        


class AddFriend(QDialog,Ui_AddDialog):

        def __init__(self,parent):
                super(AddFriend,self).__init__(parent)
                self.setupUi(self)
                self.connect(self.btnAdd,SIGNAL("clicked()"),self.addme)
                self.connect(self,SIGNAL("closed()"),self,SLOT("close()"))
                self.parent=parent

        def addme(self):
                
                frndsname=str(self.txtAddFrnd.text())
                if not frndsname.find("@gmail.com") > 0 :
                                  QMessageBox.warning(self,"Invalid Input !","Please check entered name !")
                else :

                        self.jabber=self.parent.parent.success
        		pres=xmpp.Presence(to=frndsname,typ="subscribe")
                        self.jabber.send(pres)
                       
                        self.emit(SIGNAL("closed()"))          


class TwitterAccount(QDialog,Ui_Map) :

	def __init__(self,parent) :

		super(TwitterAccount,self).__init__(parent)
		self.setupUi(self)
		self.parent = parent
		self.store = parent.parent.store
		self.jabber = parent.parent.success
		self.connect(self.buttonMap,SIGNAL("clicked()"),self.write)
		self.connect(self.lstGmail,SIGNAL("itemClicked(QListWidgetItem *)"),self.setGText)
		self.connect(self.lstTwitter,SIGNAL("itemClicked(QListWidgetItem *)"),self.setTText)
		self.pw = pwNotifyParams.PwytterMapping(self.store)
                try :
			self.pw.readFromXML()
		except Exception ,e :
			print e
		Roster=self.jabber.getRoster()
         	names=Roster.getItems()
          	for name in names:
			self.lstGmail.addItem(name)
		self.lstGmail.sortItems(0)	

		for friend in self.store.getFriends():
                	username = str(friend.getUsername())
			self.lstTwitter.addItem(username)
	

	def setGText(self,member) :

		name = unicode(member.text())
		pos = name.find('@')
		self.Gtext = name[:pos]
		

	def setTText(self,member) :
		
		self.Ttext = str(member.text())

	def write(self) :
		if self.Ttext in self.pw.values.keys() :
			print "yes its present"	
		else :
	
			print "no its not present"	
		self.pw[self.Ttext] = self.Gtext

		self.pw.writeToXML()		
		

