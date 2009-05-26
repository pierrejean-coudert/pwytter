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

'''Usefull tools used in Pwytter'''

import ImageTk
import tkBalloon
from Tkinter import *
from PIL import Image, ImageTk
import os
from os.path import dirname, join, abspath
import webbrowser

try:
    __app_path__ = abspath(dirname(__file__))
except:
    __app_path__ = abspath(dirname(sys.path[0]))       

class BusyManager:
    '''Busy cursor Manager'''

    def __init__(self, master):
        self.toplevel = master #widget.winfo_toplevel()
        self.widgets = {}

    def set(self, widget=None):

        # attach busy cursor to toplevel, plus all windows
        # that define their own cursor.

        if widget is None:
            w = self.toplevel # myself
        else:
            w = widget

        if not self.widgets.has_key(str(w)):
            try:
                # attach cursor to this widget
                cursor = w.cget("cursor")
                if cursor != "watch":
                    self.widgets[str(w)] = (w, cursor)
                    w.config(cursor="watch")
            except TclError:
                pass

        for w in w.children.values():
            self.set(w)

    def reset(self):
        # restore cursors
        for w, cursor in self.widgets.values():
            try:
                w.config(cursor=cursor)
            except TclError:
                pass
        self.widgets = {}
        
_imageFile = {}

def imageFromFile(name):
    global _imageFile
    if name not in _imageFile.keys() :
        _imageFile[name] = Image.open(os.path.join(__app_path__,"media",name))
        _imageFile[name].thumbnail((16,16),Image.ANTIALIAS)
    return _imageFile[name]
    
class ClickableImage(Label):
    def __init__(self, parent, imageName, clickCommand, aColor, aName, aHint=None):
        self._imageRef = ImageTk.PhotoImage(imageFromFile(imageName))
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
        
def takeKey(somedict, keyname, default=None):
    """
    Utility function to destructively read a key from a given dict.
    Same as the dict's 'takeKey' method, except that the key (if found)
    sill be deleted from the dictionary.
    """
    if somedict.has_key(keyname):
        val = somedict[keyname]
        del somedict[keyname]
    else:
        val = default
    return val

class LabelLink(Label):
    """
    """
    def __init__(self, parent, *args, **kw):
    
        self.cursor = takeKey(kw, 'cursor', 'hand2')
        self.link = takeKey(kw, 'link', 'http://www.google.com')
        Label.__init__(self, parent, **kw)
        
        self.config(
            cursor='hand2',
#            highlightbackground=self.bgsel,
            )
#    
#        self.frame = self.interior()
#        self.view = self.component('clipper')
#        self.view.configure(bg=self.bg, width=800)
#        self.items = []
#        self.selected = None

        self.hint =  tkBalloon.Balloon(self)     
        self.hint.settext(self.link)
        self.bind('<1>', self._userUrlClick)

    def setLink(self, aLink):
        self.link = aLink
        self.hint.settext(self.link)

    def _userUrlClick(self, event):
        try :
            webbrowser.open(self.link)
        except Exception,e :
            print str(e),'-> Cannot open Browser with url:',self.link
#        