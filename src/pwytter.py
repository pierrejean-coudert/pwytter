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

_imageFile = {}
def imagefromfile(name):
    global _imageFile
    if name not in _imageFile.keys() :
        print "load file:",name
        _imageFile[name] = Image.open(os.path.join("media",name))
        _imageFile[name].thumbnail((16,16),Image.ANTIALIAS)
    return _imageFile[name]

class ClickableImage(Label):
    def __init__(self, parent, imageName, clickCommand, aColor, aName, aHint=None):
        self._imageRef = ImageTk.PhotoImage(imagefromfile(imageName))
        self._hint = None
        Label.__init__(self, parent, image=self._imageRef, bg=aColor, name=aName)
        if aHint:
            self._hint = tkBalloon.Balloon(self,aHint)
        if clickCommand:
            self.bind('<1>', clickCommand)
            self["cursor"] = 'hand2'
    
    def config(self,**options):
        if "text" in options.keys():
            self._hint.settext(options["text"])
        Label.config(self, options)
 
class MainPanel(Frame):
    """ Main tk Frame """
    def __init__(self, master=None):
        Frame.__init__(self, master)
        #self._imageFile={}
        #self._imageRef=[]
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

        self._languages={"English":"en_US",
                         "French":"fr_FR"
                        }

        try:
            self._params.readFromXML()
        except:
            self._needToShowParameters = True
                
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
        
        self._bg=self._display['bg#']
        self['bg']=self._bg
        self.pack(ipadx=2, ipady=2)
        self._create_widgets()
        self._refresh_mySelfBox()
        if not self.tw.VersionOK:
            self._showUpdatePwytter()
        if self._needToShowParameters:
            self._showParameters()            
        self._refreshTime = 0

    def _setLanguage(self, aLanguage='English'):
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

        if aLanguage in self._languages:
            self._currentLanguage=aLanguage
        else:
            self._currentLanguage='English'
        try:
            langFr = gettext.translation('pwytter',locale_path,languages=[self._languages[self._currentLanguage]])
            langFr.install()    
        except Exception,e:
            print str(e)
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
        self._setLanguage(self._params['language'])
        self._bg=self._display['bg#']
        self['bg']=self._bg
        
    def _create_mySelfBox(self, aParent):
        self.MySelfBox = Frame(aParent)
        self.MyImageRef = ImageTk.PhotoImage("RGB",(48,48))
        self.MyImage = Label(self.MySelfBox,image=self.MyImageRef )
        self.MyImageHint = tkBalloon.Balloon(self.MyImage)       
        self.MyName = Label(self.MySelfBox,text="...",font=('Helvetica', 14, 'bold'))
        self.MyNameHint = tkBalloon.Balloon(self.MyName)
        self.ParametersShow = ClickableImage(self.MySelfBox, "cog.png", 
                                        self._showParameters,self._display['me_bg#'], "para0", _("Parameters..."))
        self.MyUrl = Label(self.MySelfBox,text="http", cursor = 'hand2' )

        self._theme_mySelfBox()
        
        self.MyImage.grid(row=0,column=0, rowspan=3, sticky=W,padx=5, pady=5)
        self.MyName.grid(row=0,column=1)
        self.ParametersShow.grid(row=0,column=2, sticky="E")
        self.MyUrl.grid(row=1,column=1, columnspan=2)
        self.MyUrl.bind('<1>', self._userClick)

    def _theme_mySelfBox(self):
        self.ParametersShow.config(bg= self._display['me_bg#'], text = _("Parameters..."))
        self.MySelfBox["bg"] = self._display['me_bg#']
        self.MyName.config(bg= self._display['me_bg#'],fg=self._display['text#'])
        self.MyUrl.config(bg= self._display['me_bg#'], fg= self._display['me_fg#'])
        
    def _refresh_mySelfBox(self):
        self._theme_mySelfBox()
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

    def _create_RefreshBox(self, parent):
        self.refreshBox = Frame(parent, width=500)
        self.PwytterLink = ClickableImage(self.refreshBox, "home.png", 
                                        self._homeclick,self._bg, "pwyt0",_("Pwytter web site..."))
        self.ShowFriends = ClickableImage(self.refreshBox, "side_expand.png", 
                                        self._showFriends,self._bg, "frie0",_("Show friends"))
        self.HideFriends = ClickableImage(self.refreshBox, "side_contract.png", 
                                        self._hideFriends,self._bg, "frie1",_("Hide friends"))
        self.Time = Label(self.refreshBox)
        self.TimeLine = Label(self.refreshBox, cursor = 'hand2')
        self.TimeLineHint=tkBalloon.Balloon(self.TimeLine, _("Switch TimeLine"))
        self.Refresh = ClickableImage(self.refreshBox, "arrow_refresh.png", 
                                        self.manualRefresh,self._bg, "refr0", _("Refresh"))
        self._theme_RefreshBox()
        self.PwytterLink.grid(row=0,column=0, sticky="W")
        self.ShowFriends.grid(row=0,column=1, sticky="E")
        self.Time.grid(row=1,column=0,columnspan=2)
        self.TimeLine.grid(row=2,column=0, sticky="W")
        self.TimeLine.bind('<1>', self._timeLineClick)
        self.Refresh.grid(row=2,column=1, sticky="E")
                
    def _theme_RefreshBox(self):
        self.refreshBox.config(bg=self._bg)
        self.PwytterLink.config(bg=self._bg, text=_("Pwytter web site..."))
        self.ShowFriends.config(bg=self._bg, text=_("Show friends"))
        self.HideFriends.config(bg=self._bg, text=_("Hide friends"))
        self.Time.config(text=_("Current Time Unknown..."), bg=self._bg, fg=self._display['text#'])
        self.TimeLine.config(text=_("Timeline: %s") % (self.tw.timeLineName()),\
                             bg=self._display['timeline#'], fg=self._display['text#'])
        self.TimeLineHint.settext(_("Switch TimeLine"))
        self.Refresh.config(bg=self._bg, text=_("Refresh"))

    def _create_updateBox(self, aParent):
        update_bg=self._display['update#']
        self.UpdateEmptyBox = Frame(aParent)
        self.UpdateInsideBox = Frame(aParent, width=500)
        self.UpdateCancel = ClickableImage(self.UpdateInsideBox, "cross.png", 
                                        self._hideUpdate, update_bg, "upca0", _("Cancel"))
        self.UpdateLbl=Label(self.UpdateInsideBox, font=self._display['fontLink'], cursor="hand2")
        self.UpdateLbl.bind('<1>', self._updateClick)
        self.UpdateGo = ClickableImage(self.UpdateInsideBox, "page_go.png", 
                                        self._updateClick, update_bg, "upgo0", _("Update now..."))

        self.UpdateCancel.grid(row=0,column=0,padx=5,pady=5,sticky=W)
        self.UpdateLbl.grid(row=0,column=1,padx=5,pady=5,sticky=W)
        self.UpdateGo.grid(row=0,column=2,padx=5,pady=5,sticky=W)
        self._theme_updateBox()
        
    def _theme_updateBox(self):
        update_bg=self._display['update#']
        self.UpdateEmptyBox.config(bg=self._bg)
        self.UpdateInsideBox.config(bg=update_bg)
        self.UpdateCancel.config(bg=update_bg, text=_("Cancel"))
        self.UpdateLbl.config(text=_("A new Pwytter release is available. You should upgrade now !"), 
                              bg=update_bg)
        self.UpdateGo.config(bg=update_bg, text=_("Update now..."))

    def _create_parameterBox(self, aParent):
        param_bg=self._display['param#']        
        self.ParamEmpyBox = Frame(aParent)
        self.ParamInsideBox = Frame(aParent, width=500)
        
        self.ParamCancel = ClickableImage(self.ParamInsideBox, \
                                        "cross.png", self._hideParameters, 
                                        param_bg,"parcancel", _('Cancel'))
        self.CreateAccountLbl=Label(self.ParamInsideBox, font=self._display['fontLink'],
                                    cursor="hand2")
        self.UserLbl=Label(self.ParamInsideBox)
        self.UserEntry = Entry(self.ParamInsideBox,textvariable=self.userVar)
        self.PasswordLbl=Label(self.ParamInsideBox)
        self.PasswordEntry = Entry(self.ParamInsideBox, textvariable=self.passwordVar,
                                   show='*')
        self.RefreshLbl=Label(self.ParamInsideBox)
        self.refreshEntry = Entry(self.ParamInsideBox, textvariable=self.refreshVar)
        self.LinesLbl=Label(self.ParamInsideBox)
        self.LinesEntry = Entry(self.ParamInsideBox, textvariable=self.linesVar)
        self.BtnBox=Frame(self.ParamInsideBox)
        self.ApplyBtn=Button(self.BtnBox, command=self._saveParameters)

        self.ThemeLbl=Label(self.ParamInsideBox)
        self.themeVar = StringVar(self.ParamInsideBox)
        self.themeVar.set(self.Theme.themeName) # default value
        self.ThemeBox = OptionMenu(self.ParamInsideBox, self.themeVar, *self.Theme.themeList)

        self.LanguageLbl=Label(self.ParamInsideBox)
        self.languageVar = StringVar(self.ParamInsideBox)
        self.languageVar.set(self._currentLanguage) # default value
        self.LanguageBox = OptionMenu(self.ParamInsideBox, self.languageVar, *self._languages.keys())

        self._theme_parameterBox()
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
       
    def _theme_parameterBox(self):
        param_bg=self._display['param#']        
        self.ParamEmpyBox.config(bg=self._bg)
        self.ParamInsideBox.config(bg=param_bg)
        
        self.ParamCancel.config(bg=param_bg,text=_('Cancel'))
        self.CreateAccountLbl.config(text= _("Click here to create a Free Twitter Account..."), 
                                    bg=param_bg, fg=self._display['text#'])
        self.UserLbl.config(text=_("User"), bg=param_bg)
        self.PasswordLbl.config(text=_("Password"), bg=param_bg)
        self.RefreshLbl.config(text=_("Refresh (s)"), bg=param_bg)
        self.LinesLbl.config(text=_("Lines"), bg=param_bg)
        self.BtnBox.config(bg=param_bg)
        self.ApplyBtn.config(text=_("Apply"))
        self.ThemeLbl.config(text=_("Theme"), bg=param_bg)
        self.LanguageLbl.config(text=_("Language"), bg=param_bg)

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
        self._params['language']= self.languageVar.get()
        self._params.writeToXML()
        self._applyParameters()
        self._hideParameters()
        
        self._theme_widgets()
        self._theme_parameterBox()
        self._theme_RefreshBox()
        self._theme_friendsBox()
        self._theme_updateBox()        

        self._refresh_mySelfBox()       
        self.manualRefresh()

    def _createLine(self, aParent, i):
        linecolor = self._display['line#']
        aLine={}
        aLine['Box']      = Frame(aParent)
        aLine['ImageRef'] = ImageTk.PhotoImage("RGB",(48,48))
        aLine['Image']    = Label(aLine['Box'],image=aLine['ImageRef'], \
                                       name="imag"+str(i), cursor="hand2")
        aLine['ImageHint']=  tkBalloon.Balloon(aLine['Image'])

        aLine['NameBox']  = Frame(aLine['Box'])
        aLine['Name']     = Label(aLine['NameBox'],text="...", name="name"+str(i),
                                     font=self._display['fontName'], cursor="hand2")
        aLine['NameHint'] = tkBalloon.Balloon(aLine['Name'])
        aLine['Time']     = Label(aLine['NameBox'],text="...", justify="left")
        aLine['IconBox']  = Frame(aLine['Box'], bg=linecolor)
        aLine['Direct']   = ClickableImage(aLine['IconBox'], \
                                        "arrow_right.png", self._showDirectMessage, linecolor,"drct"+str(i),\
                                        _('Direct Message...'))
        aLine['DirectInvalid']   = ClickableImage(aLine['IconBox'], \
                                        "arrow_nb.png", None, linecolor,"drci"+str(i))
        aLine['Favorite'] = ClickableImage(aLine['IconBox'], \
                                        "asterisk_nb.png", self.manualRefresh, linecolor,"favo"+str(i))
        aLine['FavoriteHint']= tkBalloon.Balloon(aLine['Favorite'],"Favorite")
        aLine['UserUrl']  = ClickableImage(aLine['IconBox'], \
                                        "world_go.png", self._userUrlClick, linecolor,"uurl"+str(i))
        aLine['UserUrlHint']=  tkBalloon.Balloon(aLine['UserUrl'])
        aLine['UserUrlInvalid']= ClickableImage(aLine['IconBox'], \
                                        "world_nb.png", None, linecolor,"iurl"+str(i))        
        aLine['Msg']      = Label(aLine['Box'],text="...", name=str(i),\
                                  font=self._display['fontMsg'],\
                                  width=self._display['widthMsg'])
        aLine['MsgHint']=  tkBalloon.Balloon(aLine['Msg'])
        directColor = self._display['directMsg#']
        aLine['DirectBox']      = Frame(aLine['Box'], padx=3, pady=2)
        aLine['DirectBoxEmpty'] = Frame(aLine['Box'])
        aLine['DirectCancel']   = ClickableImage(aLine['DirectBox'], \
                                        "cross.png", self._hideDirectMessage, \
                                        directColor,"dcan"+str(i),_('Cancel'))
        aLine['DirectEdit']     =   Entry(aLine['DirectBox'], width=self._display['widthDirectMsg'],\
                              textvariable=self.directText, validate="key", \
                              bd=0, name="dedi"+str(i))
        aLine['DirectSend'] = ClickableImage(aLine['DirectBox'], \
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
        aLine['DirectBoxEmpty'].grid(row=2,column=0,columnspan=3,rowspan=1, sticky='W',padx=1)
        self._theme_Line(aLine, i)
        return aLine

    def _theme_Line(self, aLine, index):
        if index==0: 
            linecolor = self._display['1stLine#']
        else:
            linecolor = self._display['line#']
        aLine['Box'].config(bg=linecolor)
        aLine['NameBox'].config(bg=linecolor)
        aLine['Name'].config(bg=linecolor, fg=self._display['text#'])
        aLine['Time'].config(bg=linecolor,fg=self._display['time#'])
        aLine['IconBox'].config(bg=linecolor)
        aLine['Direct'].config(bg=linecolor,text=_('Direct Message...'))
        aLine['DirectInvalid'].config(bg=linecolor)
        aLine['Favorite'].config(bg=linecolor)
        aLine['UserUrl'].config(bg=linecolor)
        aLine['UserUrlInvalid'].config(bg=linecolor)
        aLine['Msg'].config(bg=linecolor, fg=self._display['message#'])
        directColor = self._display['directMsg#']
        aLine['DirectBox'].config(bg=directColor)
        aLine['DirectBoxEmpty'].config(bg=linecolor)
        aLine['DirectCancel'].config(bg=directColor, text=_('Cancel'))
        aLine['DirectEdit'].config(bg=self._bg, fg=self._display['text#'])
        aLine['DirectSend'].config(bg=directColor, text=_('Send'))
 
    def _displaylines(self, par=None):
        self._imagesLoaded=True
        i=0
        for i in range(min(self._TwitLines,len(self.tw.texts))):
            if i+1>len(self.Lines) :
                self.Lines.append(self._createLine(self.LinesBox, i))
            self._theme_Line(self.Lines[i], i)
            
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
        
    def _create_friendsBox(self, aParent):   
        self.friendsEmptyBox = Frame(aParent)
        self.friendsInsideBox = Frame(aParent)
        self.FriendImages=[]
        self.FriendTitle = Label(self.friendsInsideBox)
        for i in range(2):
            self._createFriendImage(self.friendsInsideBox,i,"friend")

        self.followersEmptyBox = Frame(aParent)
        self.followersInsideBox = Frame(aParent)
        self.FollowerImages=[]
        self.FollowerTitle = Label(self.followersInsideBox)
        for i in range(2):
            self._createFriendImage(self.followersInsideBox,i,"follower")

        self._theme_friendsBox()
        self.FriendTitle.grid(row=0,column=0,columnspan=self._display['friendcolumn'])
        self.FollowerTitle.grid(row=0,column=0,columnspan=self._display['friendcolumn'])

    def _theme_friendsBox(self):
        self.friendsEmptyBox.config(bg=self._bg)
        self.friendsInsideBox.config(bg=self._bg)
        self.FriendTitle.config(text=_("Following"), bg=self._bg, fg=self._display['text#'])

        self.followersEmptyBox.config(bg=self._bg)
        self.followersInsideBox.config(bg=self._bg)
        self.FollowerTitle.config(text=_("Followers"), bg=self._bg, fg=self._display['text#'])
                
    def _refresh_friendsBox(self):
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

    def _showUpdatePwytter(self,par=None):
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

    def _create_widgets(self):      
        self.MainZone = Frame(self)
        self._create_mySelfBox(self.MainZone)
        self._create_RefreshBox(self.MainZone)
        self.ParameterBox = Frame(self.MainZone)
        self._create_parameterBox(self.ParameterBox)
        self.LinesBox= Frame(self.MainZone) 
        self.Lines=[]       
        for i in range(self._TwitLines):           
            self.Lines.append(self._createLine(self.LinesBox, i))
        self.EditParentBox = Frame(self.MainZone, bg=self._bg)
        self.RemainCar = Label(self.EditParentBox,text="...")
        self.editBox = Frame(self.EditParentBox)
        self.TwitEdit = Entry(self.editBox, width=self._display['widthTwit'],\
                              textvariable=self.twitText, bd=0)
        self.Send = ClickableImage(self.editBox, "comment.png", 
                                   self.sendTwit,self._bg, "send0",_("Send"))
        self.UpdateZone = Frame(self)
        self._create_updateBox(self.UpdateZone)
        self.FriendZone = Frame(self)
        self._create_friendsBox(self.FriendZone)

        self.MySelfBox.grid(row=0, column=0, padx=2, ipadx=6, pady=2, sticky="W")
        self.refreshBox.grid(row=0, column=1, sticky="SE")
        self.ParameterBox.grid(row=1,column=0,columnspan=2)
        self._hideParameters()
        self.LinesBox.grid(row=3, column=0,columnspan=2)
        self.RemainCar.pack(padx=5)
        self.TwitEdit.pack(side="left",padx=2, ipadx=2, ipady=2)
        self.Send.pack(side="left", padx=2, ipadx=1, ipady=1)       
        self.TwitEdit.bind("<Return>", self.sendTwit)
        self.TwitEdit.bind('<Button-1>',self.emptyTwit)  
        self.twitText.trace("w", self.editValidate)
        self.editBox.pack()      
        self.EditParentBox.grid(row=4,column=0,columnspan=2, pady=2)       
        self.UpdateZone.grid(row=0,column=0)
        self.MainZone.grid(row=1,column=0,sticky=W)
        self.FriendZone.grid(row=1,column=1,sticky=NE)
        self._hideFriends()
        self._theme_widgets()
        
    def _theme_widgets(self):      
        self.MainZone.config(bg=self._bg)
        self.ParameterBox.config(bg=self._bg)
        self.LinesBox.config(bg=self._bg) 
        self.EditParentBox.config(bg=self._bg)
        self.RemainCar.config(bg=self._bg, fg=self._display['text#'] )
        self.editValidate()       
        self.editBox.config(bg=self._bg)
        self.TwitEdit.config(bg=self._display['twitEdit#'], fg=self._display['text#'])
        self.Send.config(bg=self._bg, text=_("Send"))
        self.UpdateZone.config(bg=self._bg)
        self.FriendZone.config(bg=self._bg)
   
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
                self._refresh_mySelfBox()
                self._displaylines()
            if not self._imagesFriendsLoaded :
                self._refresh_friendsBox()
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
