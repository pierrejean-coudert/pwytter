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

#TODO: Validate on Linux
#TODO: show parameter dialog if no XML file
#TODO: parameters : live refresh (line number...)
#TODO: Autoreconnect si mauvaise connection
#TODO: Friends : load and display dynamically
#TODO: Mac version: py2app

#TODO: multiple accounts as in http://funkatron.com/index.php/site/spaz_a_twitter_client_for_mac_os_x_windows_and_linux/
#TODO: Direct messages
#TODO: Replies
#TODO: Followers
#TODO: download only the required number of messages
#TODO: setup.py : twitter.py, simplejson, PIL
#TODO: POP3/IMAP client : http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/52299
#TODO: RSS Client : http://feedparser.org/, http://code.google.com/p/davtwitter/
#TODO: Masked password

#DONE: Improved UI : reduced width, better Balloon position
#DONE: Send X-Twitter header with url -> http://www.pwytter.com/files/meta.xml
#DONE: Friends : show/hide button

'''A Python Tkinter Twitter Client'''

__author__ = 'coudert@free.fr'
__version__ = '0.5'

from Tkinter import *
import tkBalloon
import twclient
import time
import webbrowser
import textwrap
from urlparse import urlparse,urlunparse
import os
import os.path
import xml.dom.minidom as dom
from PIL import Image, ImageTk

class PwytterParams(object):
    """Handle the Pwtytter configuration in an XML file pwytter.wml
    """
    def __init__(self):
        self.values={'user': '',
                     'password': '',
                     'refresh_rate' : '',
                     'nb_lines' : ''
                    }
    def _resetDefaults(self):
        self.values['user'] = 'pwytter'
        self.values['password'] = 'pwytter123'
        self.values['refresh_rate'] = '120'
        self.values['nb_lines'] = '4'

    def __getitem__(self, aKey):
        return self.values[aKey]
        
    def __setitem__(self, aKey, value):
        self.values[aKey] = value

    def readFromXML(self):
        try:
            self._paramDoc = dom.parse('pwytter.xml').documentElement
            assert self._paramDoc.tagName == 'pwytter'
            for val in self.values.keys(): 
                try :
                    node=self._paramDoc.getElementsByTagName(val)
                    self.values[val]=node[0].firstChild.data.strip()
                except Exception, e:
                    print '!! Exception in process_node_string'+str(e)
                    self.values[val]=''
        except:
            self._resetDefaults()
        print self.values
    
    def writeToXML(self):
        impl = dom.getDOMImplementation()
        self._paramDoc = impl.createDocument(None, 'pwytter', None)
        top_element = self._paramDoc.documentElement
        for val in self.values.keys(): 
            Element=self._paramDoc.createElement(val)
            Element.appendChild(self._paramDoc.createTextNode(str(self.values[val])))
            top_element.appendChild(Element)
        f=open('pwytter.xml', 'w')
        f.write(self._paramDoc.toprettyxml())
        f.close()
    
    
class MainPanel(Frame):
    """ Main tk Frame """
    def __init__(self, master=None):
        self._imageFile={}
        self._imageRef=[]
        self._needToRefreshMe = True
        self._imagesLoaded = True
        
        self._params = PwytterParams()
        self._params.readFromXML()
        
        print self._params.values
        
        self.tw=twclient.TwClient(__version__, self._params['user'], self._params['password'])
        self._applyParameters()
        
        self.twitText = StringVar()
        self.twitText.set('Enter your message here...')
        self.userVar = StringVar()
        self.passwordVar = StringVar()
        self.refreshVar = IntVar()
        self.linesVar = IntVar()
        
        Frame.__init__(self, master)
        self._bg="#1F242A"
        self['bg']=self._bg
        self.pack(ipadx=2, ipady=2)
        self._createWidgets()
        self._refreshMe()
        self._refreshTime = 0


    def _applyParameters(self):
        self._refreshRate = int(self._params['refresh_rate'])
        self._TwitLines = int(self._params['nb_lines'])
        self.tw.login(self._params['user'], self._params['password'])
        
    def _imagefromfile(self,name):
        if name not in self._imageFile.keys() :
            print "load file:",name
            self._imageFile[name] = Image.open(os.path.join("media",name))
            self._imageFile[name].thumbnail((16,16),Image.ANTIALIAS)
        return self._imageFile[name]

    def _createClickableImage(self, parent, imageName, clickCommand, aColor, aName, aHint=None):
        self._imageRef.append(ImageTk.PhotoImage(self._imagefromfile(imageName)))
        aLabel = Label(parent, image=self._imageRef[-1], bg=aColor, name=aName)
        if aHint:
            self._imageRef.append(tkBalloon.Balloon(aLabel,aHint))
        if clickCommand:
            aLabel.bind('<1>', clickCommand)
            aLabel["cursor"] = 'hand2'
        return aLabel

    def _createMySelfBox(self, aParent):
        me_bg, me_fg = "#2F3237", "#BBBBBB"
        self.MySelfBox = Frame(aParent, bg=me_bg)
        self.MyImageRef = ImageTk.PhotoImage("RGB",(48,48))
        self.MyImage = Label(self.MySelfBox,image=self.MyImageRef )
        self.MyImage.grid(row=0,column=0, rowspan=3, sticky=W,padx=5, pady=5)
        self.MyImageHint = tkBalloon.Balloon(self.MyImage)
        
        self.MyName = Label(self.MySelfBox,text="...",font=('helvetica', 14, 'bold'), bg=me_bg, fg="white")
        self.MyName.grid(row=0,column=1)
        self.MyNameHint = tkBalloon.Balloon(self.MyName)

        self.Param = self._createClickableImage(self.MySelfBox, "cog.png", 
                                        self._showParameters,me_bg, "para0")
        #self.ParamHint=tkBalloon.Balloon(self.Param, "Parameters...")
        self.Param.grid(row=0,column=2, sticky="E")

        self.MyUrl = Label(self.MySelfBox,text="http", bg=me_bg, fg=me_fg, cursor = 'hand2' )
        self.MyUrl.grid(row=1,column=1, columnspan=2)
        self.MyUrl.bind('<1>', self._userClick)

    def _createRefreshBox(self, parent):
        self.refreshBox = Frame(parent, width=500, bg=self._bg)
        self.ShowFriends = self._createClickableImage(self.refreshBox, "side_expand.png", 
                                        self._showFriends,self._bg, "frie0","Show friends")
        self.HideFriends = self._createClickableImage(self.refreshBox, "side_contract.png", 
                                        self._hideFriends,self._bg, "frie1","Hide friends")
        self.Time = Label(self.refreshBox, text="Current Time Unknown...", bg=self._bg, fg="white")
        self.TimeLine = Label(self.refreshBox,text="Timeline: "+self.tw.timeLineName(),\
                              bg="#484C4F", fg="white", cursor = 'hand2')
        self.TimeLineHint=tkBalloon.Balloon(self.TimeLine, "Swicth TimeLine")
        self.TimeLine.bind('<1>', self._timeLineClick)
        self.Refresh = self._createClickableImage(self.refreshBox, "arrow_refresh.png", 
                                        self.manualRefresh,self._bg, "refr0","Refresh")
        self.ShowFriends.grid(row=0,column=1, sticky="E")
        self.Time.grid(row=1,column=0,columnspan=2)
        self.TimeLine.grid(row=2,column=0, sticky="W")
        self.Refresh.grid(row=2,column=1, sticky="E")
                
    def _createParameterBox(self, aParent):
        param_bg="#585C5F"
        self.ParamEmpyBox = Frame(aParent, bg=self._bg)
        self.ParamInsideBox = Frame(aParent, width=500, bg=param_bg)
        
        self.UserLbl=Label(self.ParamInsideBox, text="User", bg=param_bg)
        self.UserEntry = Entry(self.ParamInsideBox,textvariable=self.userVar)
        self.PasswordLbl=Label(self.ParamInsideBox, text="Password", bg=param_bg)
        self.PasswordEntry = Entry(self.ParamInsideBox, textvariable=self.passwordVar)
        self.RefreshLbl=Label(self.ParamInsideBox, text="Refresh (s)", bg=param_bg)
        self.refreshEntry = Entry(self.ParamInsideBox, textvariable=self.refreshVar)
        self.LinesLbl=Label(self.ParamInsideBox, text="Lines", bg=param_bg)
        self.LinesEntry = Entry(self.ParamInsideBox, textvariable=self.linesVar)
        self.BtnBox=Frame(self.ParamInsideBox, bg=param_bg)
        self.CancelBtn=Button(self.BtnBox, text="Cancel",command=self._hideParameters)
        self.ApplyBtn=Button(self.BtnBox, text="Apply",command=self._saveParameters)
        
        self.UserLbl.grid(row=0,column=0,padx=5,pady=5,sticky=W)
        self.UserEntry.grid(row=0, column=1,padx=5,pady=5)
        self.PasswordLbl.grid(row=0,column=2,padx=5,pady=5,sticky=W)
        self.PasswordEntry.grid(row=0, column=3,padx=5,pady=5)
        self.RefreshLbl.grid(row=1,column=0,padx=5,pady=5,sticky=W)
        self.refreshEntry.grid(row=1, column=1,padx=5,pady=5)
        self.LinesLbl.grid(row=1,column=2,padx=5,pady=5,sticky=W)
        self.LinesEntry.grid(row=1, column=3,padx=5,pady=5)
        self.BtnBox.grid(row=2, column=0, columnspan=4, sticky=EW)
        self.CancelBtn.pack(padx=5,pady=5,side="right")
        self.ApplyBtn.pack(padx=5,pady=5,side="right")
       
    def _showParameters(self,par=None):
        self.userVar.set(self._params['user'])
        self.passwordVar.set(self._params['password'])
        self.refreshVar.set(self._params['refresh_rate'])
        self.linesVar.set(self._params['nb_lines'])
        self.ParamEmpyBox.pack_forget()
        self.ParamInsideBox.pack(expand=1,pady=2)

    def _hideParameters(self,par=None):
        self.ParamInsideBox.pack_forget()
        self.ParamEmpyBox.pack()

    def _saveParameters(self,par=None):
        self._params['user'] = self.userVar.get()
        self._params['password'] = self.passwordVar.get()
        self._params['refresh_rate'] = self.refreshVar.get()
        self._params['nb_lines']= self.linesVar.get()
        self._params.writeToXML()
        self._applyParameters()
        self._refreshMe()       
        self._hideParameters()

    def _createLine(self, aParent, linecolor, i):
        aLine={}
        aLine['Box']      = Frame(aParent,bg=linecolor)
        aLine['ImageRef'] = ImageTk.PhotoImage("RGB",(48,48))
        aLine['Image']    = Label(aLine['Box'],image=aLine['ImageRef'], \
                                       name="imag"+str(i), cursor="hand2")
        aLine['ImageHint']=  tkBalloon.Balloon(aLine['Image'])

        aLine['NameBox']  = Frame(aLine['Box'], bg=linecolor)
        aLine['Name']     = Label(aLine['NameBox'],text="...",bg=linecolor, name="name"+str(i),
                                     font=('arialblack',8,'bold'),fg="white", cursor="hand2")
        aLine['NameHint'] = tkBalloon.Balloon(aLine['Name'])
        aLine['Time']     = Label(aLine['NameBox'],text="...",bg=linecolor,\
                                     fg="#BBBBBB", justify="left")
        
        aLine['IconBox']  = Frame(aLine['Box'], bg=linecolor)
        aLine['Direct']   = self._createClickableImage(aLine['IconBox'], \
                                        "arrow_right.png", self.manualRefresh, linecolor,"drct"+str(i))
        aLine['Favorite'] = self._createClickableImage(aLine['IconBox'], \
                                        "asterisk_nb.png", self.manualRefresh, linecolor,"favo"+str(i))
        aLine['FavoriteHint']= tkBalloon.Balloon(aLine['Favorite'],"Favorite")
        aLine['UserUrl']  = self._createClickableImage(aLine['IconBox'], \
                                        "world_go.png", self._userUrlClick, linecolor,"uurl"+str(i))
        aLine['UserUrlHint']=  tkBalloon.Balloon(aLine['UserUrl'])
        aLine['UserUrlInvalid']= self._createClickableImage(aLine['IconBox'], \
                                        "world_nb.png", None, linecolor,"iurl"+str(i))
        
        aLine['Msg']      = Label(aLine['Box'],text="...",bg=linecolor, name=str(i),
                                    font=('arialblack',8,'bold'), fg="#99CBFE", width=57)
        aLine['MsgHint']=  tkBalloon.Balloon(aLine['Msg'])
            
        aLine['Image'].bind('<1>', self._nameClick)
        aLine['Image'].grid(row=0,column=0,rowspan=2, sticky='NW',padx=1,pady=2)
        
        aLine['NameBox'].grid(row=0,column=1, sticky='W') 
        aLine['Name'].bind('<1>', self._nameClick)
        aLine['Name'].grid(row=0,column=0, sticky='W',padx=1)
        aLine['Time'].grid(row=0,column=1, sticky='W') 

        aLine['IconBox'].grid(row=0,column=2, sticky='E') 
        aLine['Direct'].grid(row=0,column=0, rowspan=1, sticky='W')
        aLine['Favorite'].grid(row=0,column=1, rowspan=1, sticky='E')
        aLine['UserUrl'].grid(row=0,column=2, sticky='E')
        aLine['UserUrl'].grid_forget()           
        aLine['UserUrlInvalid'].grid(row=0,column=2, sticky='E')

        aLine['Msg'].grid(row=1,column=1,columnspan=2,rowspan=1, sticky='W',padx=1)
        aLine['Box'].grid(row=i,sticky=W,padx=0, pady=2, ipadx=1, ipady=1)
        return aLine

    def _createFriendZone(self, aParent):   
        self.friendsEmptyBox = Frame(aParent, bg=self._bg)
        self.friendsInsideBox = Frame(aParent, bg=self._bg)

        self.FriendImages=[]
        for i in range(20):
            aFriend={}
            aFriend['ImageRef'] = ImageTk.PhotoImage("RGB",(20,20))
            aFriend['Image']    = Label(self.friendsInsideBox,image=aFriend['ImageRef'], \
                                           name="frie"+str(i), cursor="hand2")
            aFriend['ImageHint']=  tkBalloon.Balloon(aFriend['Image'])
            self.FriendImages.append(aFriend)
            aFriend['Image'] .grid(row=int(i/4), column=i-(int(i/4)*4))
    
    def _showFriends(self,par=None):
        self.friendsEmptyBox.pack_forget()
        self.friendsInsideBox.pack(expand=1,padx=2)
        self.ShowFriends.grid_forget()
        self.HideFriends.grid(row=0,column=1, sticky="E")

    def _hideFriends(self,par=None):
        self.friendsInsideBox.pack_forget()
        self.friendsEmptyBox.pack()
        self.HideFriends.grid_forget()
        self.ShowFriends.grid(row=0,column=1, sticky="E")

    def _createWidgets(self):      
        self.MainZone = Frame(self, bg=self._bg)

        self._createMySelfBox(self.MainZone)
        self.MySelfBox.grid(row=0, column=0, padx=2, ipadx=6, pady=2, sticky="W")
       
        self._createRefreshBox(self.MainZone)
        self.refreshBox.grid(row=0, column=1, sticky="SE")

        self.ParameterBox = Frame(self.MainZone, bg=self._bg)
        self._createParameterBox(self.ParameterBox)
        self.ParameterBox.grid(row=1,column=0,columnspan=2)
        self._hideParameters()
                        
        self.LinesBox= Frame(self.MainZone,bg=self._bg) 
        self.Lines=[]       
        for i in range(self._TwitLines):           
            if i==0:
                self.Lines.append(self._createLine(self.LinesBox, "#484C4F",i))
            else:
                self.Lines.append(self._createLine(self.LinesBox, "#2F3237",i))
        self.LinesBox.grid(row=3, column=0,columnspan=2)

        self.EditParentBox = Frame(self.MainZone, bg=self._bg)
        self.RemainCar = Label(self.EditParentBox,text="...", bg=self._bg,\
                               fg="white" )
        self.RemainCar.pack(padx=5)
        self.editBox = Frame(self.EditParentBox, bg=self._bg)
        self.TwitEdit = Entry(self.editBox, width=68, textvariable=self.twitText,\
                              validate="key", validatecommand=self.editValidate, \
                              bg="#2F3237", fg="white", bd=0)
        self.TwitEdit.pack(side="left",padx=2, ipadx=2, ipady=2)
        self.SendImageRef = ImageTk.PhotoImage(Image.open(os.path.join("media","comment.png")))
        self.Send = Button(self.editBox, image=self.SendImageRef,\
                           command=self.sendTwit,default=ACTIVE, bg=self._bg)
        self.Send.pack(side="left", padx=2, ipadx=1, ipady=1)
        self.SendHint = tkBalloon.Balloon(self.Send, "Send")
        self.TwitEdit.bind("<Return>", self.sendTwit)
        self.editBox.pack()      
        self.EditParentBox.grid(row=4,column=0,columnspan=2, pady=2)
        
        self.MainZone.grid(column=0,sticky=W)

        self.FriendZone = Frame(self, bg=self._bg)
        self._createFriendZone(self.FriendZone)
        self.FriendZone.grid(row=0,column=1,sticky=E)
        self._hideFriends()

    def _refreshFriends(self):
        self.tw.getFriends()
        i=0
        for fname in self.tw.Friends:
            loaded, aImage= self.tw.imageFromCache(fname)
            self._imagesLoaded = self._imagesLoaded and loaded     
            try :   
                self.FriendImages[i]['ImageRef'].paste(aImage, (0,0,20,20))
            except:
                print "error pasting friends images:",fname
            self.FriendImages[i]['ImageHint'].settext("http://twitter.com/"+fname)
            self.FriendImages[i]['Image'].bind('<1>', self._friendClick)
            i=i+1

    def _refreshMe(self):
        print "refresh Me"
        self._refreshFriends()
        try:
            self._needToRefreshMe = not self.tw.getMyDetails()
            self.MyImageRef.paste(self.tw.myimage, (0,0,48,18))
            self.MyName["text"] = self.tw.me.screen_name.encode('latin-1')
            try:
                self.MyImageHint.settext("%s: %s %cLocation: %s" % (self.tw.me.name.encode('latin-1'),\
                                      self.tw.me.description.encode('latin-1'),13,\
                                      self.tw.me.location.encode('latin-1')))
                self.MyNameHint.settext(self.MyImageHint.gettext())
            except Exception, e:
                self.MyImageHint.settext('')
                self.MyNameHint.settext('')
            try:
                self.MyUrl["text"] = self.tw.me.url.encode('latin-1')
            except Exception, e:
                self.MyUrl["text"] = ''
                
        except Exception, e:
            print "_refreshMe Exception:",str(e)
            self._needToRefreshMe = True

            
    def _userClick(self,par=None):
        try :
            webbrowser.open(self.tw.me.url.encode('latin-1'))
        except Exception,e :
            print str(e),'-> Cannot open Browser with url:',self.tw.me.url.encode('latin-1')

    def _urlClick(self,par=None):
        lineIndex= int(par.widget.winfo_name())
        try :
            webbrowser.open(self.tw.texts[lineIndex]["url"])
        except Exception,e :
            print str(e),'-> Cannot open Browser with url:',self.tw.texts[lineIndex]["url"]

    def _nameClick(self,par=None):
        lineIndex= int(par.widget.winfo_name()[4:])
        try :
            webbrowser.open("http://twitter.com/"+self.tw.texts[lineIndex]["name"])
        except Exception,e :
            print str(e),'-> Cannot open Browser with url:',"http://twitter.com/"+self.tw.texts[lineIndex]["name"]
            
    def _friendClick(self,par=None):
        friendIndex= int(par.widget.winfo_name()[4:])
        url=self.FriendImages[friendIndex]['ImageHint'].gettext()

        try :
            webbrowser.open(url)
        except Exception,e :
            print str(e),'-> Cannot open Browser with url:',url

    def _userUrlClick(self,par=None):
        lineIndex= int(par.widget.winfo_name()[4:])
        userurl = self.tw.texts[lineIndex]["user_url"]
        if userurl != "":
            try :
                webbrowser.open(userurl)
            except Exception,e :
                print str(e),'-> Cannot open Browser with url:',userurl

    def _timeLineClick(self,par=None):
        self.tw.nextTimeLine()
        print "Switch to Timeline:",self.tw.timeLineName()
        self.TimeLine["text"] = "Timeline: "+self.tw.timeLineName()
        self._refreshTwitZone()
          
    def _displaylines(self, par=None):
        self._imagesLoaded=True
        for i in range(min(self._TwitLines,len(self.tw.texts))):
            name = self.tw.texts[i]["name"]
            loaded, aImage= self.tw.imageFromCache(name)
            self._imagesLoaded = self._imagesLoaded and loaded        
            try:
                self.Lines[i]['ImageRef'].paste(aImage, (0,0,20,20))
            except:
                print "error pasintg image:", name
            self.Lines[i]['Name']["text"]= name
            self.Lines[i]['ImageHint'].settext("http://twitter.com/"+name)
            self.Lines[i]['NameHint'].settext("http://twitter.com/"+name)
            self.Lines[i]['Time']["text"]= self.tw.texts[i]["time"]
            initText=self.tw.texts[i]["msg"].decode('latin-1','replace')
            self.Lines[i]['Msg']["text"]=textwrap.fill(initText, 70, break_long_words=True)
            urlstart = initText.find("http://")
            if urlstart > -1 :
                self.tw.texts[i]["url"] = urlunparse(urlparse(initText[urlstart:])).split('"')[0]
                self.Lines[i]['Msg'].bind('<1>', self._urlClick)
                self.Lines[i]['Msg']["cursor"] = 'hand2'
                self.Lines[i]['Msg']["fg"] = "#B9DBFF"
                self.Lines[i]['MsgHint'].settext(self.tw.texts[i]["url"])
                self.Lines[i]['MsgHint'].enable()
                print "url detected:",self.tw.texts[i]["url"]
            else:
                self.tw.texts[i]["url"] = ''
                self.Lines[i]['Msg'].bind('<1>', None)
                self.Lines[i]['Msg']["cursor"] = ''
                self.Lines[i]['Msg']["fg"] = "#99CBFE"    
                self.Lines[i]['MsgHint'].disable()
            if self.tw.texts[i]["user_url"] == '':
                self.Lines[i]['UserUrl'].bind('<1>', None)
                self.Lines[i]['UserUrl']["cursor"] = ''    
                self.Lines[i]['UserUrl'].grid_forget()           
                self.Lines[i]['UserUrlInvalid'].grid(row=0, column=2, sticky='E')
            else:
                self.Lines[i]['UserUrl'].bind('<1>', self._userUrlClick)
                self.Lines[i]['UserUrl']["cursor"] = 'hand2'
                self.Lines[i]['UserUrlHint'].settext(self.tw.texts[i]["user_url"])
                self.Lines[i]['UserUrlInvalid'].grid_forget() 
                self.Lines[i]['UserUrl'].grid(row=0, column=2, sticky='E')
                self.Lines[i]['UserUrl'].grid()
    
    def _refreshTwitZone(self):
        timestr = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
        self.Time["text"]= timestr
        try:
            self.tw.refresh()
            self._displaylines()
        except Exception, e :
            self.Time["text"]=textwrap.fill("Refresh error: "+timestr+" >> "+str(e), 50, break_long_words=True)           
#        finally:
#            pass

    def timer(self):
        if time.time()-self._refreshTime >= self._refreshRate :
            self._refreshTwitZone()
            self._refreshTime = time.time()
        if self._needToRefreshMe:
            self._refreshMe()
        if not self._imagesLoaded :
            self._displaylines()
        self.after(1000, self.timer)

    def sendTwit(self,par=None):
        self.tw.sendText(self.twitText.get())
        self.twitText.set('')
        self._refreshTwitZone()
        
    def manualRefresh(self,par=None):
        self._refreshTwitZone()
                   
    def editValidate(self):
        self.RemainCar["text"] =  "%d caracter(s) remaining" % (140-len(self.twitText.get().encode('latin-1')))
        return True
        
def MainLoop():
    rootTk = Tk()
    rootTk.title('Pwytter')
    if os.name == 'nt':
        rootTk.iconbitmap('pwytter.ico') 
    app = MainPanel(master=rootTk)
    #rootTk.attributes(alpha=0.5)
    rootTk.after(100,app.timer)
    try :
        app.mainloop()
    finally:
        rootTk.destroy()

if __name__ == "__main__":
    MainLoop()