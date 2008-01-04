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

from Tkinter import *
try:
     from PIL import Image, ImageTk
except ImportError:
     import Image, ImageTk
from pwytter import __version__ as VERSION
from pwytter import __app_path__
import os

class Splash(Toplevel):
     def __init__(self, master):
         """(master) -> create a splash screen
         """
         Toplevel.__init__(self, master, bd=1, bg='#888888')
         self.main = master
         self.main.withdraw()
         self.overrideredirect(1)
#         im = Image.open(image)
#         self.image = ImageTk.PhotoImage(im)
         self.after_idle(self._centerOnScreen)
         self.update()
         self.lift()   
         #self.after(timeout, self.destroy)

     def _centerOnScreen(self):
         self.update_idletasks()
         width, height = self.width, self.height = \
                         self.winfo_width(), self.winfo_height() 
         xmax = self.winfo_screenwidth()
         ymax = self.winfo_screenheight()

         x0 = self.x0 = (xmax - self.winfo_reqwidth()) / 2 - width/2
         y0 = self.y0 = (ymax - self.winfo_reqheight()) / 2 - height/2
         self.geometry("+%d+%d" % (x0, y0))
         self.createWidgets()

     def createWidgets(self):
         self.Border=Frame(self,bg='white')

         self.logopil = Image.open(os.path.join(__app_path__,"media","pwytter.png"))
         self.logotk = ImageTk.PhotoImage(self.logopil)         
         self.Logo =Label(self.Border,image=self.logotk, bg="white")
    
         self.Box=Frame(self.Border,bg='white', padx=20, pady=15)
         self.Title =Label(self.Box,text=_("Pwytter"),font=('Helvetica', 14, 'bold'), bg="white", fg="black")
         self.Version =Label(self.Box,text=VERSION,font=('Helvetica', 14, 'bold'), bg="white", fg="black")
         self.Loading =Label(self.Box,text=_("Loading..."), bg="white", fg="black")
         self.Licence =Label(self.Box,text=_("Licence: GNU GPL v2"), bg="white", fg="black",pady=8)

         self.Title.pack()
         self.Version.pack()
         self.Loading.pack()
         self.Licence.pack()
         self.Logo.grid(row=0, column=0)
         self.Box.grid(row=0, column=1)
         self.Border.pack()
#         self.canvas = Canvas(self, height=self.width, width=self.height)
#         self.canvas.create_image(0,0, anchor=NW, image=self.image)
#         self.canvas.pack()

     def destroy(self):
         self.main.update()
         self.main.deiconify()
         self.withdraw()

if __name__ == "__main__":
     import os, time
     tk = Tk()
     s = Splash(tk)  
     time.sleep(15)
     s.destroy() 
     tk.mainloop()