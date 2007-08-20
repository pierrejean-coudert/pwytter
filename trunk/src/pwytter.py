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

'''A Python Tkinter Twitter Client'''

import sys
from os.path import dirname, join, abspath
try:
    sys.path.append(join(abspath(dirname(__file__)), 'twclient'))  
except:
    sys.path.append(join(abspath(dirname(sys.path[0])), 'twclient'))  
        
__author__ = 'Pierre-Jean Coudert <coudert@free.fr>'
__version__ = '0.7'
APP_NAME = "pwytter"

from Tkinter import *
import tkBalloon
import pwSplashScreen
import twclient
import pwParam
import pwTools
import pwTheme
import time
import webbrowser
import textwrap
from urlparse import urlparse,urlunparse
import os
import os.path
from PIL import Image, ImageTk
import gettext
import locale
 
class MainPanel(Frame):
    """ Main tk Frame """
    def __init__(self, master=None):
        self._imageFile={}
        self._imageRef=[]
        self._needToRefreshMe = True
        self._imagesLoaded = True
        self._imagesFriendsLoaded = True
        self._needToShowParameters = False
        self._busy = pwTools.BusyManager(master)
        self._params = pwParam.PwytterParams()

        self.Theme = None
        self._display={
            'fontName':('Helvetica',8,'bold'),
            'fontMsg':('Helvetica',8,'bold'),
            'fontLink':('Helvetica',9,'underline'),
            'widthMsg':58,
            'widthTwit':69,
            'widthDirectMsg':66,
            'friendcolumn':6
            }
        if os.name=='mac':
            self._display.update({
                'fontName':('Helvetica',9,'bold'),
                'fontMsg':('Helvetica',9,'bold'),
                'fontLink':('Helvetica',9,'underline'),
                'widthMsg':61,
                'widthTwit':61,
                'widthDirectMsg':58
                })
        if os.name=='posix':
            self._display.update({
                'fontName':"Helvetica 12 bold",
                'fontMsg': "Helvetica",
                'fontLink':"Helvetica 12 underline",
                'widthMsg':61,
                'widthTwit':62,
                'widthDirectMsg':59
                })

        self._loadTheme(self._params['theme'])

        try:
            self._params.readFromXML()
        except:
            self._needToShowParameters = True
        self._setLanguage('fr_FR')
        
        self.tw=twclient.TwClient(__version__, self._params['user'], self._params['password'])       
        self._applyParameters()

        self._defaultTwitText = _('Enter your message here...')
        self.twitText = StringVar()
        self.twitText.set(self._defaultTwitText)
        self.directText = StringVar()
        self.directText.set(_('Enter your direct message here...'))
        self.userVar = StringVar()
        self.passwordVar = StringVar()
        self.refreshVar = IntVar()
        self.linesVar = IntVar()
        Frame.__init__(self, master)
        
        self._bg=self._display['bg#']
        self['bg']=self._bg
        self.pack(ipadx=2, ipady=2)
        self._createWidgets()
        self._refreshMe()
        if not self.tw.VersionOK:
            self._showUpdate()
        if self._needToShowParameters:
            self._showParameters()            
        self._refreshTime = 0

    def _setLanguage(self, locale_name='en_US'):
        #Get the local directory since we are not installing anything
        locale_path = os.path.join(os.path.realpath(os.path.dirname(sys.argv[0])),"locale")
        langs = []
        lc, encoding = locale.getdefaultlocale()
        if (lc): langs = [lc]
        # Now lets get all of the supported languages on the system
        language = os.environ.get('LANGUAGE', None)
        if (language): langs += language.split(":")
        langs += ["fr_FR", "en_US"]
        gettext.bindtextdomain(APP_NAME, locale_path)
        gettext.textdomain(APP_NAME)

        langFr = gettext.translation('pwytter',locale_path,languages=[locale_name])
        langFr.install()    
        # Get the language to use
    #        self.lang = gettext.translation(APP_NAME, self.locale_path
    #            , languages=langs, fallback = True)
    
    def _loadTheme(self, aName):
        if self.Theme:
          self.Theme.setTheme(aName)
        else:
          self.Theme=pwTheme.pwTheme(aName)
        self._display.update(self.Theme.values)

    def _applyParameters(self):
        self._refreshRate = int(self._params['refresh_rate'])
        self._TwitLines = int(self._params['nb_lines'])
        self.tw.login(self._params['user'], self._params['password'])
        self._loadTheme(self._params['theme'])
        
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
        me_bg, me_fg = self._display['me_bg#'],self._display['me_fg#']
        self.MySelfBox = Frame(aParent, bg=me_bg)
        self.MyImageRef = ImageTk.PhotoImage("RGB",(48,48))
        self.MyImage = Label(self.MySelfBox,image=self.MyImageRef )
        self.MyImage.grid(row=0,column=0, rowspan=3, sticky=W,padx=5, pady=5)
        self.MyImageHint = tkBalloon.Balloon(self.MyImage)       
        self.MyName = Label(self.MySelfBox,text="...",font=('Helvetica', 14, 'bold'), bg=me_bg, fg=self._display['text#'])
        self.MyName.grid(row=0,column=1)
        self.MyNameHint = tkBalloon.Balloon(self.MyName)
        self.Param = self._createClickableImage(self.MySelfBox, "cog.png", 
                                        self._showParameters,me_bg, "para0", _("Parameters..."))
        self.Param.grid(row=0,column=2, sticky="E")
        self.MyUrl = Label(self.MySelfBox,text="http", bg=me_bg, fg=me_fg, cursor = 'hand2' )
        self.MyUrl.grid(row=1,column=1, columnspan=2)
        self.MyUrl.bind('<1>', self._userClick)

    def _refreshMe(self):
        try:
            self._imagesFriendsLoaded = False
            self._needToRefreshMe = not self.tw.getMyDetails()
            self.MyImageRef.paste(self.tw.myimage, (0,0,48,18))
            self.MyName["text"] = self.tw.me.screen_name.encode('latin-1')
            try:
                self.MyImageHint.settext(_("%s: %s %cLocation: %s") % (self.tw.me.name.encode('latin-1'),\
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

    def _createRefreshBox(self, parent):
        self.refreshBox = Frame(parent, width=500, bg=self._bg)
        self.PwytterLink = self._createClickableImage(self.refreshBox, "home.png", 
                                        self._homeclick,self._bg, "pwyt0",_("Pwytter web site..."))
        self.ShowFriends = self._createClickableImage(self.refreshBox, "side_expand.png", 
                                        self._showFriends,self._bg, "frie0",_("Show friends"))
        self.HideFriends = self._createClickableImage(self.refreshBox, "side_contract.png", 
                                        self._hideFriends,self._bg, "frie1",_("Hide friends"))
        self.Time = Label(self.refreshBox, text=_("Current Time Unknown..."), bg=self._bg, fg=self._display['text#'])
        self.TimeLine = Label(self.refreshBox,text=_("Timeline: %s") % (self.tw.timeLineName()),\
                              bg=self._display['timeline#'], fg=self._display['text#'], cursor = 'hand2')
        self.TimeLineHint=tkBalloon.Balloon(self.TimeLine, _("Switch TimeLine"))
        self.TimeLine.bind('<1>', self._timeLineClick)
        self.Refresh = self._createClickableImage(self.refreshBox, "arrow_refresh.png", 
                                        self.manualRefresh,self._bg, "refr0", _("Refresh"))
        self.PwytterLink.grid(row=0,column=0, sticky="W")
        self.ShowFriends.grid(row=0,column=1, sticky="E")
        self.Time.grid(row=1,column=0,columnspan=2)
        self.TimeLine.grid(row=2,column=0, sticky="W")
        self.Refresh.grid(row=2,column=1, sticky="E")
                
    def _createUpdateBox(self, aParent):
        update_bg=self._display['update#']
        self.UpdateEmptyBox = Frame(aParent, bg=self._bg)
        self.UpdateInsideBox = Frame(aParent, width=500, bg=update_bg)
        self.UpdateCancel = self._createClickableImage(self.UpdateInsideBox, "cross.png", 
                                        self._hideUpdate, update_bg, "upca0", _("Cancel"))
        self.UpdateLbl=Label(self.UpdateInsideBox, text=_("A new Pwytter release is available. You should upgrade now !"), 
                             bg=update_bg, font=self._display['fontLink'], cursor="hand2")
        self.UpdateLbl.bind('<1>', self._updateClick)
        self.UpdateGo = self._createClickableImage(self.UpdateInsideBox, "page_go.png", 
                                        self._updateClick, update_bg, "upgo0", _("Update now..."))

        self.UpdateCancel.grid(row=0,column=0,padx=5,pady=5,sticky=W)
        self.UpdateLbl.grid(row=0,column=1,padx=5,pady=5,sticky=W)
        self.UpdateGo.grid(row=0,column=2,padx=5,pady=5,sticky=W)

    def _createParameterBox(self, aParent):
        param_bg=self._display['param#']        
        self.ParamEmpyBox = Frame(aParent, bg=self._bg)
        self.ParamInsideBox = Frame(aParent, width=500, bg=param_bg)
        
        self.ParamCancel = self._createClickableImage(self.ParamInsideBox, \
                                        "cross.png", self._hideParameters, 
                                        param_bg,"parcancel", _('Cancel'))
        self.CreateAccountLbl=Label(self.ParamInsideBox, text= _("Click here to create a Free Twitter Account..."), 
                                    bg=param_bg, font=self._display['fontLink'],
                                    cursor="hand2", fg=self._display['text#'])
        self.UserLbl=Label(self.ParamInsideBox, text=_("User"), bg=param_bg)
        self.UserEntry = Entry(self.ParamInsideBox,textvariable=self.userVar)
        self.PasswordLbl=Label(self.ParamInsideBox, text=_("Password"), bg=param_bg)
        self.PasswordEntry = Entry(self.ParamInsideBox, textvariable=self.passwordVar,
                                   show='*')
        self.RefreshLbl=Label(self.ParamInsideBox, text=_("Refresh (s)"), bg=param_bg)
        self.refreshEntry = Entry(self.ParamInsideBox, textvariable=self.refreshVar)
        self.LinesLbl=Label(self.ParamInsideBox, text=_("Lines"), bg=param_bg)
        self.LinesEntry = Entry(self.ParamInsideBox, textvariable=self.linesVar)
        self.BtnBox=Frame(self.ParamInsideBox, bg=param_bg)
        self.ApplyBtn=Button(self.BtnBox, text=_("Apply"), command=self._saveParameters)

        self.ThemeLbl=Label(self.ParamInsideBox, text=_("Theme"), bg=param_bg)
        self.themeVar = StringVar(self.ParamInsideBox)
        self.themeVar.set(self.Theme.themeName) # default value
        self.ThemeBox = OptionMenu(self.ParamInsideBox, self.themeVar, *self.Theme.themeList)

        self.LanguageLbl=Label(self.ParamInsideBox, text=_("Language"), bg=param_bg)
        self.LanguageVar = StringVar(self.ParamInsideBox)
        self.LanguageVar.set("one") # default value
        self.LanguageBox = OptionMenu(self.ParamInsideBox, self.LanguageVar, "one", "two", "three")

        self.ParamCancel.grid(row=0,column=0,padx=5,pady=5,sticky=NW)
        self.CreateAccountLbl.bind('<1>', self._createAccountClick)
        self.CreateAccountLbl.grid(row=0,column=1, columnspan=3,padx=5,pady=5)
        self.UserLbl.grid(row=1,column=0,padx=5,pady=5,sticky=W)
        self.UserEntry.grid(row=1, column=1,padx=5,pady=5)
        self.PasswordLbl.grid(row=1,column=2,padx=5,pady=5,sticky=W)
        self.PasswordEntry.grid(row=1, column=3,padx=5,pady=5)
        self.RefreshLbl.grid(row=2,column=0,padx=5,pady=5,sticky=W)
        self.refreshEntry.grid(row=2, column=1,padx=5,pady=5)
        self.LinesLbl.grid(row=2,column=2,padx=5,pady=5,sticky=W)
        self.LinesEntry.grid(row=2, column=3,padx=5,pady=5)
        self.ThemeLbl.grid(row=3, column=0, padx=5, pady=5, sticky=W)   
        self.ThemeBox.grid(row=3, column=1, padx=5, pady=5, sticky=W)      
        self.LanguageLbl.grid(row=3, column=2, padx=5, pady=5, sticky=W)   
        self.LanguageBox.grid(row=3, column=3, padx=5, pady=5, sticky=W)      
        self.BtnBox.grid(row=4, column=3, columnspan=4, sticky=EW)
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
        self._params['theme']= self.themeVar.get()
        self._params.writeToXML()
        self._applyParameters()
        self._hideParameters()
        self._refreshMe()       
        self.manualRefresh()

    def _createLine(self, aParent, i):
        linecolor = self._display['line#']
        if i==0: linecolor = self._display['1stLine#']
        aLine={}
        aLine['Box']      = Frame(aParent,bg=linecolor)
        aLine['ImageRef'] = ImageTk.PhotoImage("RGB",(48,48))
        aLine['Image']    = Label(aLine['Box'],image=aLine['ImageRef'], \
                                       name="imag"+str(i), cursor="hand2")
        aLine['ImageHint']=  tkBalloon.Balloon(aLine['Image'])

        aLine['NameBox']  = Frame(aLine['Box'], bg=linecolor)
        aLine['Name']     = Label(aLine['NameBox'],text="...",bg=linecolor, name="name"+str(i),
                                     font=self._display['fontName'],fg=self._display['text#'], cursor="hand2")
        aLine['NameHint'] = tkBalloon.Balloon(aLine['Name'])
        aLine['Time']     = Label(aLine['NameBox'],text="...",bg=linecolor,\
                                     fg=self._display['time#'], justify="left")
        
        aLine['IconBox']  = Frame(aLine['Box'], bg=linecolor)
        aLine['Direct']   = self._createClickableImage(aLine['IconBox'], \
                                        "arrow_right.png", self._showDirectMessage, linecolor,"drct"+str(i),\
                                        _('Direct Message...'))
        aLine['DirectInvalid']   = self._createClickableImage(aLine['IconBox'], \
                                        "arrow_nb.png", None, linecolor,"drci"+str(i))
        aLine['Favorite'] = self._createClickableImage(aLine['IconBox'], \
                                        "asterisk_nb.png", self.manualRefresh, linecolor,"favo"+str(i))
        aLine['FavoriteHint']= tkBalloon.Balloon(aLine['Favorite'],"Favorite")
        aLine['UserUrl']  = self._createClickableImage(aLine['IconBox'], \
                                        "world_go.png", self._userUrlClick, linecolor,"uurl"+str(i))
        aLine['UserUrlHint']=  tkBalloon.Balloon(aLine['UserUrl'])
        aLine['UserUrlInvalid']= self._createClickableImage(aLine['IconBox'], \
                                        "world_nb.png", None, linecolor,"iurl"+str(i))        
        aLine['Msg']      = Label(aLine['Box'],text="...",bg=linecolor, name=str(i),\
                                  font=self._display['fontMsg'], fg=self._display['message#'],\
                                  width=self._display['widthMsg'])
        aLine['MsgHint']=  tkBalloon.Balloon(aLine['Msg'])
        directColor = self._display['directMsg#']
        aLine['DirectBox']      = Frame(aLine['Box'], bg=directColor, padx=3, pady=2)
        aLine['DirectBoxEmpty'] = Frame(aLine['Box'], bg=linecolor)
        aLine['DirectCancel']   = self._createClickableImage(aLine['DirectBox'], \
                                        "cross.png", self._hideDirectMessage, \
                                        directColor,"dcan"+str(i),_('Cancel'))
        aLine['DirectEdit']     =   Entry(aLine['DirectBox'], width=self._display['widthDirectMsg'],\
                              textvariable=self.directText, validate="key", \
                              bg=self._bg, fg=self._display['text#'], bd=0, name="dedi"+str(i))
        aLine['DirectSend'] = self._createClickableImage(aLine['DirectBox'], \
                                        "comment.png", self._sendDirectMessage, directColor,\
                                        "dsen"+str(i), _('Send'))
        aLine['DirectCancel'].grid(row=0,column=0, sticky='W',padx=1)
        aLine['DirectEdit'].grid(row=0,column=1, padx=1)
        aLine['DirectSend'].grid(row=0,column=2, sticky='E',padx=1)

        aLine['Image'].bind('<1>', self._nameClick)
        aLine['Image'].grid(row=0,column=0,rowspan=2, sticky='NW',padx=1,pady=2)        
        aLine['NameBox'].grid(row=0,column=1, sticky='W') 
        aLine['Name'].bind('<1>', self._nameClick)
        aLine['Name'].grid(row=0,column=0, sticky='W',padx=1)
        aLine['Time'].grid(row=0,column=1, sticky='W') 
        aLine['IconBox'].grid(row=0,column=2, sticky='E') 
        aLine['Direct'].grid_forget()
        aLine['DirectInvalid'].grid(row=0,column=0, rowspan=1, sticky='W')
        aLine['Favorite'].grid(row=0,column=1, rowspan=1, sticky='E')
        aLine['UserUrl'].grid(row=0,column=2, sticky='E')
        aLine['UserUrl'].grid_forget()           
        aLine['UserUrlInvalid'].grid(row=0,column=2, sticky='E')
        aLine['Msg'].grid(row=1,column=1,columnspan=2,rowspan=1, sticky='W',padx=1)
        aLine['Box'].grid(row=i,sticky=W,padx=0, pady=2, ipadx=1, ipady=1)
        aLine['DirectBox'].grid_forget()
        #aLine['DirectBox'].grid(row=2,column=0,columnspan=3,rowspan=1, sticky='W',padx=1)
        aLine['DirectBoxEmpty'].grid(row=2,column=0,columnspan=3,rowspan=1, sticky='W',padx=1)
        return aLine
 
    def _displaylines(self, par=None):
        self._imagesLoaded=True
        i=0
        for i in range(min(self._TwitLines,len(self.tw.texts))):
            if i+1>len(self.Lines) :
                self.Lines.append(self._createLine(self.LinesBox, i))
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
            if name==self.MyName["text"]:
                self.Lines[i]['Direct'].grid_forget()
                self.Lines[i]['DirectInvalid'].grid(row=0,column=0, rowspan=1, sticky='W')
            else:
                self.Lines[i]['DirectInvalid'].grid_forget()
                self.Lines[i]['Direct'].grid(row=0,column=0, rowspan=1, sticky='W')
            initText=self.tw.texts[i]["msg"].decode('latin-1','replace')
            #self.Lines[i]['Msg']["text"]=textwrap.fill(initText, 70, break_long_words=True)
            self.Lines[i]['Msg']["text"]=textwrap.fill(self.tw.texts[i]["msgunicode"], 70, break_long_words=True)           
            urlstart = initText.find("http://")
            if urlstart > -1 :
                self.tw.texts[i]["url"] = urlunparse(urlparse(initText[urlstart:])).split('"')[0]
                self.Lines[i]['Msg'].bind('<1>', self._urlClick)
                self.Lines[i]['Msg']["cursor"] = 'hand2'
                self.Lines[i]['Msg']["fg"] = self._display['messageUrl#']
                self.Lines[i]['MsgHint'].settext(self.tw.texts[i]["url"])
                self.Lines[i]['MsgHint'].enable()
                print "url detected:",self.tw.texts[i]["url"]
            else:
                self.tw.texts[i]["url"] = ''
                self.Lines[i]['Msg'].bind('<1>', None)
                self.Lines[i]['Msg']["cursor"] = ''
                self.Lines[i]['Msg']["fg"] = self._display['message#']
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
            self.Lines[i]['Box'].grid(row=i,sticky=W,padx=0, pady=2, ipadx=1, ipady=1)
        for i in range(i+1,len(self.Lines)):
            self.Lines[i]['Box'].grid_forget()
    
    def _createFriendImage(self, aParent, index, type):   
        aFriend={}
        aFriend['ImageRef'] = ImageTk.PhotoImage("RGB",(20,20))
        c=self._display['friendcolumn']
        if type=="friend":
            aFriend['Image']    = Label(aParent,image=aFriend['ImageRef'], \
                                           name="frie"+str(index), cursor="hand2")
            aFriend['ImageHint']=  tkBalloon.Balloon(aFriend['Image'])
            self.FriendImages.append(aFriend)
        else:
            aFriend['Image']    = Label(aParent,image=aFriend['ImageRef'], \
                                           name="foll"+str(index), cursor="hand2")
            aFriend['ImageHint']=  tkBalloon.Balloon(aFriend['Image'])
            self.FollowerImages.append(aFriend)
        aFriend['Image'].grid(row=1+int(index/c), column=index-(int(index/c)*c), padx=1, pady=1)
        return aFriend
        
    def _createFriendZone(self, aParent):   
        self.friendsEmptyBox = Frame(aParent, bg=self._bg)
        self.friendsInsideBox = Frame(aParent, bg=self._bg)
        self.FriendImages=[]
        self.FriendTitle = Label(self.friendsInsideBox,text=_("Following"), bg=self._bg, 
                                 fg=self._display['text#'])
        self.FriendTitle.grid(row=0,column=0,columnspan=self._display['friendcolumn'])
        for i in range(2):
            self._createFriendImage(self.friendsInsideBox,i,"friend")

        self.followersEmptyBox = Frame(aParent, bg=self._bg)
        self.followersInsideBox = Frame(aParent, bg=self._bg)
        self.FollowerImages=[]
        self.FollowerTitle = Label(self.followersInsideBox,text=_("Followers"), bg=self._bg, 
                                   fg=self._display['text#'])
        self.FollowerTitle.grid(row=0,column=0,columnspan=self._display['friendcolumn'])
        for i in range(2):
            self._createFriendImage(self.followersInsideBox,i,"follower")
    
    def _refreshFriends(self):
        try:
            self.tw.getFriends()
            i=0
            self._imagesFriendsLoaded = True
            for fname in self.tw.Friends[:30]:
                if i+1>len(self.FriendImages) :
                    self._createFriendImage(self.friendsInsideBox,i, "friend")
                loaded, aImage= self.tw.imageFromCache(fname)
                self._imagesFriendsLoaded = self._imagesFriendsLoaded and loaded     
                try :   
                    self.FriendImages[i]['ImageRef'].paste(aImage, (0,0,20,20))
                except:
                    print "error pasting friends images:",fname
                self.FriendImages[i]['ImageHint'].settext("http://twitter.com/"+fname)
                self.FriendImages[i]['Image'].bind('<1>', self._friendClick)
                c=self._display['friendcolumn']
                self.FriendImages[i]['Image'].grid(row=1+int(i/c), column=i-(int(i/c)*c), padx=1, pady=1)
                i=i+1
            for i in range(i,len(self.FriendImages)):
                self.FriendImages[i]['Image'].grid_forget()
        except Exception,e :
            print str(e),"-> Can't get friends"
            
        try:
            self.tw.getFollowers()
            i=0
            for fname in self.tw.Followers[:30]:
                if i+1>len(self.FollowerImages) :
                    self._createFriendImage(self.followersInsideBox,i, "follower")
                loaded, aImage= self.tw.imageFromCache(fname)
                self._imagesFriendsLoaded = self._imagesFriendsLoaded and loaded     
                try :   
                    self.FollowerImages[i]['ImageRef'].paste(aImage, (0,0,20,20))
                except:
                    print "error pasting friends images:",fname
                self.FollowerImages[i]['ImageHint'].settext("http://twitter.com/"+fname)
                self.FollowerImages[i]['Image'].bind('<1>', self._friendClick)
                c=self._display['friendcolumn']
                self.FollowerImages[i]['Image'].grid(row=1+int(i/c), column=i-(int(i/c)*c), padx=1, pady=1)
                i=i+1
            for i in range(i,len(self.FollowerImages)):
                self.FollowerImages[i]['Image'].grid_forget()        
        except Exception,e :
            print str(e),"-> Can't get followers"

    def _showFriends(self,par=None):
        self.friendsEmptyBox.pack_forget()
        self.friendsInsideBox.pack(expand=1,padx=2)
        self.followersEmptyBox.pack_forget()
        self.followersInsideBox.pack(expand=1,padx=2)
        self.ShowFriends.grid_forget()
        self.HideFriends.grid(row=0,column=1, sticky="E")

    def _hideFriends(self,par=None):
        self.friendsInsideBox.pack_forget()
        self.friendsEmptyBox.pack()
        self.followersInsideBox.pack_forget()
        self.followersEmptyBox.pack(expand=1,padx=2)
        self.HideFriends.grid_forget()
        self.ShowFriends.grid(row=0,column=1, sticky="E")

    def _showUpdate(self,par=None):
        self.UpdateEmptyBox.grid_forget()
        self.UpdateInsideBox.grid(row=0,column=0)

    def _hideUpdate(self,par=None):
        self.UpdateInsideBox.grid_forget()
        self.UpdateEmptyBox.grid(row=0,column=0)

    def _showDirectMessage(self,par=None):
        lineIndex= int(par.widget.winfo_name()[4:])
        self.Lines[lineIndex]['DirectBoxEmpty'].grid_forget()
        self.Lines[lineIndex]['DirectBox'].grid(row=2,column=0,columnspan=3,rowspan=1, sticky='W',padx=1)

    def _hideDirectMessage(self,par=None):
        lineIndex= int(par.widget.winfo_name()[4:])
        self.Lines[lineIndex]['DirectBox'].grid_forget()
        self.Lines[lineIndex]['DirectBoxEmpty'].grid(row=2,column=0,columnspan=3,rowspan=1, sticky='W',padx=1)
        
    def _sendDirectMessage(self,par=None):
        self._busy.set()
        try:
            lineIndex= int(par.widget.winfo_name()[4:])
            try:
                print self.tw.sendDirectMessage(self.tw.texts[lineIndex]["name"], self.directText.get())
            except Exception,e :
                print str(e),'-> error sending direct msg:',self.directText.get(),'to',self.tw.texts[lineIndex]["name"]
            self._hideDirectMessage(par)
        finally:
            self._busy.reset()

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
            self.Lines.append(self._createLine(self.LinesBox, i))
        self.LinesBox.grid(row=3, column=0,columnspan=2)

        self.EditParentBox = Frame(self.MainZone, bg=self._bg)
        self.RemainCar = Label(self.EditParentBox,text="...", bg=self._bg,\
                               fg=self._display['text#'] )
        self.RemainCar.pack(padx=5)
        self.editBox = Frame(self.EditParentBox, bg=self._bg)
        self.TwitEdit = Entry(self.editBox, width=self._display['widthTwit'],\
                              textvariable=self.twitText,\
                              bg=self._display['twitEdit#'], fg=self._display['text#'], bd=0)
        self.TwitEdit.pack(side="left",padx=2, ipadx=2, ipady=2)
        self.Send = self._createClickableImage(self.editBox, "comment.png", 
                                        self.sendTwit,self._bg, "send0",_("Send"))
        self.Send.pack(side="left", padx=2, ipadx=1, ipady=1)       
        self.TwitEdit.bind("<Return>", self.sendTwit)
        self.TwitEdit.bind('<Button-1>',self.emptyTwit)  
        self.twitText.trace("w", self.editValidate)
        self.editValidate()
        
        self.editBox.pack()      
        self.EditParentBox.grid(row=4,column=0,columnspan=2, pady=2)
        
        self.UpdateZone = Frame(self, bg=self._bg)
        self._createUpdateBox(self.UpdateZone)

        self.FriendZone = Frame(self, bg=self._bg)
        self._createFriendZone(self.FriendZone)

        self.UpdateZone.grid(row=0,column=0)
        self.MainZone.grid(row=1,column=0,sticky=W)
        self.FriendZone.grid(row=1,column=1,sticky=NE)

        self._hideFriends()
           
    def _openweb(self,url):
        try :
            webbrowser.open(url)
        except Exception,e :
            print str(e),'-> Cannot open Browser with url:',url

    def _homeclick(self,par=None):
        self._openweb('http://www.pwytter.com')

    def _userClick(self,par=None):
        self._openweb(self.tw.me.url.encode('latin-1'))

    def _createAccountClick(self,par=None):
        self._openweb('https://twitter.com/signup')
        
    def _updateClick(self,par=None):
        self._openweb('http://www.pwytter.com/download')
        
    def _urlClick(self,par=None):
        lineIndex= int(par.widget.winfo_name())
        self._openweb(self.tw.texts[lineIndex]["url"])

    def _nameClick(self,par=None):
        lineIndex= int(par.widget.winfo_name()[4:])
        self._openweb("http://twitter.com/"+self.tw.texts[lineIndex]["name"])
            
    def _friendClick(self,par=None):
        friendIndex= int(par.widget.winfo_name()[4:])
        self._openweb(self.FriendImages[friendIndex]['ImageHint'].gettext())

    def _userUrlClick(self,par=None):
        lineIndex= int(par.widget.winfo_name()[4:])
        userurl = self.tw.texts[lineIndex]["user_url"]
        if userurl != "": self._openweb(userurl)

    def _timeLineClick(self,par=None):
        self._busy.set()
        try:
            self.tw.nextTimeLine()
            print "Switch to Timeline:",self.tw.timeLineName()
            self.TimeLine["text"] = _("Timeline: %s") %(self.tw.timeLineName())
            self._refreshTwitZone()
        finally:
            self._busy.reset()
  
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
        try:
            if time.time()-self._refreshTime >= self._refreshRate :
                self._refreshTwitZone()
                self._refreshTime = time.time()
            if not self._imagesLoaded :
                self._displaylines()
            if self._needToRefreshMe:
                self._refreshMe()
                self._displaylines()
            if not self._imagesFriendsLoaded :
                self._refreshFriends()
        finally:
            self.after(1000, self.timer)

    def sendTwit(self,par=None):
        self._busy.set()
        try:
            self.tw.sendText(self.twitText.get())
            self.twitText.set('')
            self._refreshTwitZone()
        finally:
            self._busy.reset()
        
    def emptyTwit(self,par=None):
        if self.twitText.get() == self._defaultTwitText:
            self.twitText.set('')
        
    def manualRefresh(self,par=None):
        self._busy.set()
        try:
            self._refreshTwitZone()
        finally:
            self._busy.reset()
 
    def editValidate(self, *dummy):
        actualLenghth=len(self.twitText.get())
        if actualLenghth>140:
            self.twitText.set(self.twitText.get()[:140])
        else:
            self.RemainCar["text"] =  _("%d character(s) left") % (140-actualLenghth)

def _initTranslation():
    """Translation stuff : init locale and get text"""       
    gettext.install(APP_NAME)
       
if __name__ == "__main__":
    _initTranslation()
    rootTk = Tk()
    rootTk.title('Pwytter %s' % (__version__))
    rootTk.resizable(width=0, height=0) 
    if os.name == 'nt':
        rootTk.iconbitmap(os.path.join("media",'pwytter.ico')) 
    s = pwSplashScreen.Splash(rootTk)
    app = MainPanel(master=rootTk)
    app.timer()
    s.destroy() 
    app.mainloop()
