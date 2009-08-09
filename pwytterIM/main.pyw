import sys,time,os

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from AddFriend import *
from login import *
import Presence 
from Chatting import *
from MainWindow import *
from ChatWindow import *
from Queue import *
import ReceiveAll

class LogInScreen(QDialog,Ui_frm_login):

	def __init__(self,parent=None) :
		photo_directory="./photos"
		if not os.path.exists(photo_directory):
		            os.makedirs(photo_directory)
		super(LogInScreen,self).__init__(parent)
		self.setupUi(self)
		self.connect(self.buttonSignIn,SIGNAL("clicked()"),self.authenticateUser)
		self.success=False
		self.connect(self,SIGNAL("rejected()"),self,SLOT("close()"))
		self.presence=Presence.PresenceStatus()
		self.stopadd=True
		self.AvailableList={}
		self.msg=""
		self.AuthenticationFlag=True

	def authenticateUser(self):
             
		self.threadRotate=Rotate(self)
		self.threadRotate.start()
		self.connect(self.threadRotate, SIGNAL("finished()"),self.threadRotate,SLOT("deleteLater()"))
                self.username=str(self.lEditUserName.text())
		self.password=str(self.lEditPassword.text())
		self.threadAuthenticate=Authenticate(self)
                self.threadAuthenticate.start()
                self.connect(self.threadAuthenticate, SIGNAL("finished()"),self.displayMainWindow)
		self.threadAuthenticateAllTheTime=AuthenticateAllTheTime(self)
		self.threadAuthenticateAllTheTime.start()
		
	def displayMainWindow(self):
		self.threadRotate.success=False		
		if self.AuthenticationFlag :
			#self.presence.askForProbe()
			self.download=self.presence.getDownload()
	                self.download.start()
			self.main_frm=MainWindow(self)
                	self.main_frm.show()
                	self.setHidden(True)
			time.sleep(8)
			self.addBuddies=AddBuddies(self)
			self.connect(self.addBuddies,SIGNAL("photoLoad()"),self.load)		
			self.addBuddies.start()
			self.nameQueue=Queue(10)
			self.msgQueue=Queue(10)
			self.connect(self,SIGNAL("popup()"),self.main_frm.popup)
			self.receivebot=ReceiveAll.ReceiveBot(self.success,self,self.nameQueue,self.msgQueue)
			#self.connect(self.receivebot,SIGNAL("ping()"),self.ping)
			self.receivedata=ReceiveAll.ReceiveData(self,self.success)
			self.receivebot.register_handlers()
			self.receivedata.start()
		else :
			 QMessageBox.warning(self,"Authentication error !","Please check your username and password !")
			 self.AuthenticationFlag=True
	def load(self):
	
		pic=QPixmap(self.addBuddies.path)
                ico=QIcon(pic)
                self.addBuddies.buddy.setIcon(ico)

	def closeAll(self):
	
		self.emit(SIGNAL("rejected()"))
		self.threadAuthenticateAllTheTime.close=False
	def ping(self):
		print "I m in ping"
		if not self.nameQueue.empty():
			self.sender=self.nameQueue.get()
		if not self.msgQueue.empty():
			self.msg=self.msgQueue.get()
		
		self.emit(SIGNAL("popup()"))
		

class AddBuddies(QThread):
	__pyqtSignals__=("photoLoad(QString,QListWidgetItem)")	
	def __init__(self,parent=None):
		super(AddBuddies,self).__init__(parent)	   
		self.presence=parent.presence
		self.login_frm=parent
		self.main_frm=parent.main_frm
		#self.connect(self,SIGNAL("photoLoad(QString,QListWidgetItem)"),parent.load)
		self.close=True
		self.Frndlist={}
		self.parent=parent
	def run(self):
				
		 	
		count=len(self.presence.nmtopresence)
               
                for i in range(count):
                        	try :
					nameOfFrnd=self.presence.nmtopresence[i]
				except Exception,e:
					print "Problem while adding",e
					pass
				self.addFriends(nameOfFrnd)	

		
		
		self.parent.AvailableList=self.Frndlist
		while self.close:
			time.sleep(20)
			present=self.Frndlist.keys()
			
		
			sortedlist=[]
			sortedlist=present
			sortedlist.sort()
			for changes in self.presence.nmtopresence :
				if changes in present:
					pass
				else :
				
					mutex.lock()
					self.addFriends(changes)
					mutex.unlock()
					time.sleep(1)
			
			for keyname in present:
				if keyname in self.presence.nmtopresence :
					pass
				else:
			
					index=0
					for temp in sortedlist 	:
						
						if keyname==temp :
							break
						index=index+1
					
					del self.Frndlist[keyname]
					try:
						mutex.lock()
						removeditem=self.main_frm.lstFrndList.takeItem(index)
						time.sleep(2)
						mutex.unlock()			
					except Exception,e:
						print "problem while removing",e
					
						
		        self.parent.AvailableList=self.Frndlist					
					
	def addFriends(self,name):
		  	
				self.buddy=QListWidgetItem()
                                self.path=self.presence.getFilename(name)
                                if  not self.path :
                                       self.path="./Default.png"
                                                       
                                self.emit(SIGNAL("photoLoad()"))
                                time.sleep(0.5)

                                nms=self.presence.nmtostatus[name]
				
                                if nms== None:
                                        nms="Available"
                                if len(nms)>40 :
                                        nms=nms[0:40]
                                        nms=nms+"..."
                                text=name
				if len(name)>45 :
                                        text=name[0:40]
                                        text=text+"..."
                                text=text+"\n"+nms
                              
                                self.buddy.setText(text)
                                self.Frndlist[name]=self.buddy
				#additem=self.Frndlist[frnd]
				
                                self.main_frm.lstFrndList.addItem(self.buddy)
                		self.main_frm.lstFrndList.setSortingEnabled(True)
                		self.main_frm.lstFrndList.sortItems(0)

	
		
class Authenticate(QThread):

	def __init__(self,frm):
		super(Authenticate,self).__init__(frm)
		self.login_frm=frm
		
	def run(self):
		 print "connecting"
		 self.login_frm.success = self.login_frm.presence.login(self.login_frm.username,self.login_frm.password)
		 if not self.login_frm.success :
			self.login_frm.AuthenticationFlag=False					
        			         
class AuthenticateAllTheTime(QThread):

        def __init__(self,frm):
                super(AuthenticateAllTheTime,self).__init__(frm)
                self.login_frm=frm
		self.close=True
		#self.connect(self,SIGNAL("reconnect()"),self.login_frm.threadAuthenticate,SLOT("start()"))
        def run(self):
		 time.sleep(60)	
                 while self.close:
			self.username=str(self.login_frm.username)
			#pres=xmpp.Presence(to=self.username,typ="probe")
			try:
				status=self.login_frm.presence.selfStatus[self.username]
				#self.login_frm.success.send(pres)
				if status == "unavailable":
					print "disconnected"
					raise Exception("disconnected")
			except Exception,e:
				print "disconnected error",e
				#self.login_frm.success.disconnect()
				self.login_frm.success = self.login_frm.presence.login(self.login_frm.username,self.login_frm.password)
				#self.emit(SIGNAL("reconnect()"))	

class Rotate(QThread):
        def __init__(self,frm):
                super(Rotate,self).__init__(frm)
                self.login_frm=frm
                self.login_frm.dSignIn.setNotchesVisible(True)
		self.success=True
        def run(self):
		i=0 
		while self.success:
                        self.login_frm.dSignIn.setValue(i)
			print self.success		
                        time.sleep(0.1)
                        i=i+10
			if i>=99 :
				i=0


class MainWindow(QMainWindow,Ui_BuddyList):

        def __init__(self,parent=None):

                super(MainWindow,self).__init__(parent)
                self.parent=parent
		self.setupUi(self)
	 	self.connect(self,SIGNAL("destroyed(QObject*)"),self,SLOT("closeEvent(QCloseEvent*)"))
		if not self.lstFrndList.hasMouseTracking():
			self.lstFrndList.setMouseTracking(True)
		self.connect(self.lstFrndList,SIGNAL("itemEntered(QListWidgetItem *)"),self.setToolTipText)
		self.connect(self.lstFrndList,SIGNAL("itemClicked(QListWidgetItem *)"),self.memberClicked)
		self.connect(self.action_Add_Contact,SIGNAL("triggered()"),self.addFriend)
		self.activeWindows={}
		pic=QPixmap("Available.png")
		icon=QIcon(pic)
		self.cmdSetStatus.addItem(icon,"Available")
		pic=QPixmap("Away.png")
		icon=QIcon(pic)
		self.cmdSetStatus.addItem(icon,"Away")
		pic=QPixmap("Dnd.png")
		icon=QIcon(pic)
		self.cmdSetStatus.addItem(icon,"Available")
		self.cmdSetStatus.addItem("Don't Disturb")
		
	def closeEvent(self,event):
               
                self.parent.download.close=False
                self.parent.stopadd=False
		self.parent.closeAll()
		self.close=False		
		
	def popup(self):
		print "I m in popup"
		keys=self.parent.AvailableList.keys()
		if self.parent.sender in keys :
			
			item=self.parent.AvailableList[self.parent.sender]
			
		akeys=self.activeWindows.keys()
		if not self.parent.sender in akeys :	
			
			self.chatHandle(item)
			
	def setToolTipText(self,member):
		sname=unicode(member.text())
	
		p=sname.find('\n')
		sname=sname[:p]
		sname=sname.rstrip()
		stext=self.parent.presence.nmtostatus[sname]

		imagepath=self.parent.presence.getFilename(sname)
		if imagepath:
			text= '<img src=%s style="float:left"></img><div style="float:left"><b>%s</b><br><br>%s</div>' % (imagepath,sname,stext)
		else :
			text='%s' % sname	
	
		member.setToolTip(text)

	def addFriend(self) :
		addFriend=AddFriend(self)
		addFriend.show()		
	

	def chatHandle(self,member):
		self.sname=unicode(member.text())
		print "I m in chat"
		p=self.sname.find('\n')
		self.sname=self.sname[:p]
		try :
			chat=Chat(self,self.parent.success,self.sname)
			chat.start()	
		except Exception ,e :
			pass
		mutex.lock()
		self.activeWindows[self.sname]=chat
		print "activeWindows before deletion",self.activeWindows.keys()
		mutex.unlock()
		if self.parent.msg!="" :
			chat.queue.put(self.parent.msg)

	def memberClicked(self,member):	
		self.sname=unicode(member.text())
		p=self.sname.find('\n')
                self.sname=self.sname[:p]
		print " I m in memberlist" ,self.sname
		chat=Chat(self,self.parent.success,self.sname)
		chat.start()
		self.activeWindows[self.sname]=chat
                 	
class Chat(QThread):
	def __init__(self,parent,jabber,sendTo):
		super(Chat,self).__init__(parent)
		self.parent=parent
		self.queue=Queue(10)
		self.window=ChatWindow(self.parent,sendTo)
                self.window.show()
		self.bot=Bot(jabber,sendTo,self.queue)
		receive=Receive(self.window,jabber)
		receive.start()	
	       	self.bot.register_handlers() 
		self.close=True
		self.connect(self,SIGNAL("gotMessage()"),self.window.getMessage)
		self.window.lblName.setText(sendTo)
		
		
	def run(self):
		
		while self.close :
				  if self.window.text.find('\n')>=0 :
			               
               				msg = self.window.text.rstrip('\r\n')
                			try:
						self.bot.stdio_message(msg)
					except Exception,e:
						print "error in chat",e
						#auth=Authenticate(self.parent.parent)
						#auth.start()		
					self.window.text=""
             			  time.sleep(1)
				  if not self.queue.empty() :
					self.window.receivedText=self.queue.get()
					
					self.window.receivedText=QString(self.window.receivedText)
					self.emit(SIGNAL("gotMessage()"))
					
							
class ChatWindow(QMainWindow,Ui_ChatWindow):

	def __init__(self,parent,sendTo):
		super(ChatWindow,self).__init__(parent)
		self.setupUi(self)
		self.connect(self.txtMsgSend,SIGNAL("textChanged()"),self.send)
		#self.connect(self,SIGNAL()
		self.parent=parent
		self.text=""
		self.receivedText=""
		self.connect(self,SIGNAL("destroyed(QObject*)"),self,SLOT("closeEvent(QCloseEvent*)"))
		#self.connect(self,SIGNAL("deleteMe()"),self.parent.destroyThread)
		self.sendTo=sendTo	
	
	def send(self):
		txt=self.txtMsgSend.toPlainText()
		txt=unicode(txt)	
		if txt.find('\n')>=0 :
			self.text=txt
			self.txtMsgSend.setText("")
			display=self.ShowChat.toPlainText()
			display=display+" Me :  "+self.text
			self.ShowChat.setText(display)

	def getMessage(self):
		 
		 display=self.ShowChat.toPlainText()
                 display=display +" " +self.sendTo + " :  "  + self.receivedText
                 try:
		 	self.ShowChat.setText(display)
		 except Exception ,e:
			print "problem while setting text",e	
			
	def closeEvent(self,event):
	  	try :
                        mutex.lock()
                        c1=self.parent.activeWindows[self.sendTo]
                        c1.terminate()
                        del self.parent.activeWindows[self.sendTo]
                        print "deleted"
                        mutex.unlock()
			print "activeWindows after deletion",self.parent.activeWindows.keys()
                except Exception,e:
                       print "problem while deleting",e
			



class AddFriend(QDialog,Ui_AddDialog):

	def __init__(self,parent):
		super(AddFriend,self).__init__(parent)
		self.setupUi(self)
		self.connect(self.btnAdd,SIGNAL("clicked()"),self.addme)
		self.connect(self,SIGNAL("closed()"),self,SLOT("close()"))
		self.parent=parent

	def addme(self):
		print "I m in add"
		frndsname=str(self.txtAddFrnd.text())
		if not frndsname.find("@gmail.com") > 0 :
				  QMessageBox.warning(self,"Authentication error !","Please check your username and password !")
		else :
		
			self.jabber=self.parent.parent.success
			pres=xmpp.Presence(to=frndsname,typ="subscribe")
			self.jabber.send(pres)
			print "add req sent"
			self.emit(SIGNAL("closed()"))			
			
		
mutex=QMutex()
app=QApplication(sys.argv)
form=LogInScreen()
form.show()
app.exec_()
