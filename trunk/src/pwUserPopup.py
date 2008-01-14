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
 
import Tkinter as tk   
import ImageTk
from pwTools import ClickableImage, LabelLink

class UserPopup(tk.Toplevel): 
    """
    """
    def __init__(self, parent=None, aUser='', aDelay=400): 
        tk.Toplevel.__init__(self,parent,bd=1,bg='black')  
        self._duration = aDelay 
        self._mousePoint = None
        self._tipwidth = 0
        self._tipheight = 0  
        self._inPopup = False
        self.parent = parent        
        self.withdraw()  
        self.overrideredirect(1)  
        self.transient() 
        self._bg = "#E0E0E0"
        
        self._frame = tk.Frame(self,bg=self._bg,bd=1)
        self._label = tk.Label(self._frame, bg=self._bg,justify='left')  
        self._labelTwitter = LabelLink(self._frame, bg=self._bg,justify='left')  
        self._labelUrl = LabelLink(self._frame, bg=self._bg,justify='left')  
        self._resizedImage = None
        self._tkImage = ImageTk.PhotoImage("RGB",(30,30))
        self._image = tk.Label(self._frame,image= self._tkImage)
        self._reply = ClickableImage(self._frame, \
                                        "arrow_undo.png", self._replyToUser, self._bg,"repl",
                                        _('Reply to this message...'))
        self._direct = ClickableImage(self._frame, \
                                        "arrow_right.png", self._directMessage, self._bg,"drct",\
                                        _('Direct Message...'))

        self._image.grid(row=0, column=0, rowspan=2, columnspan=2) 
        self._label.grid(row=0, column=2)  
        self._labelTwitter.grid(row=1, column=2)  
        self._labelUrl.grid(row=2, column=2)  
        self._reply.grid(row=2, column=0)  
        self._direct.grid(row=2, column=1)  
        
        self.parent.bind('<Enter>',self._delay)  
        self.parent.bind('<Button-1>',self._hide)  
        self.parent.bind('<Leave>',self._hide)  
        self._frame.bind('<Enter>',self._enterPopup)  
        self._frame.bind('<Leave>',self._leavePopup)  
        self._frame.bind('<Button-1>',self._leavePopup)  
        self._frame.pack()          
        self._frame.update_idletasks()         
        
    def setUser(self, twClient=None, aUser=''): 
        if not twClient:
            return
        loaded, aImage = twClient.imageFromCache(aUser)
        userObj = twClient.userFromCache(aUser)
        if aImage :
            try :   
                self._tkImage.paste(aImage)
            except:
                print "error pasting userPopup images:",aUser
        try :
            self._label["text"] = aUser+", "+userObj.location
        except:
            self._label["text"] = aUser
        self._labelTwitter["text"] = "http://twitter.com/"+aUser
        self._labelTwitter.setLink("http://twitter.com/"+aUser)
        self._labelUrl["text"] = userObj.url
        self._labelUrl.setLink(userObj.url)
               
        self._tipwidth = self._frame.winfo_width()  
        self._tipheight = self._frame.winfo_height()  
        self._frame.update_idletasks()  
        
    def gettext(self): 
        return self._labelUrl["text"]
        
    def disable(self): 
        self.parent.bind('<Enter>',self._disable)  
        
    def enable(self): 
        self.parent.bind('<Enter>',self._delay)  

    def _delay(self, event): 
        self._mousePoint = (event.x_root, event.y_root)
        self.action=self.parent.after(self._duration,self._display)
          
    def _display(self): 
        self.update_idletasks()  
        if not self._mousePoint :
            return           
        posX = min(self._mousePoint[0], self.winfo_screenwidth()-self._tipwidth-5)
        posY = max(0,self.parent.winfo_rooty()-self._tipheight+5)
        self.geometry('+%d+%d'%(posX,posY))  
        self.deiconify()  
        self.lift()        
        
    def _hide(self, event): 
        self.action = self.parent.after(self._duration, self._hidePopup)

    def _hidePopup(self): 
        if not self._inPopup:
            self.withdraw()  
            self.parent.after_cancel(self.action) 

    def _enterPopup(self, event):
        self._inPopup = True
        
    def _leavePopup(self, event):
        self._inPopup = False
        self._hidePopup()      
        
    def _disable(self, event): 
        self.withdraw()  
        self.action = self.parent.after(self._duration, self._nothing)

    def _nothing(self): 
        pass

    def _replyToUser(self, event): 
        pass
    
    def _directMessage(self, event): 
        pass
    