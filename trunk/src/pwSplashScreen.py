from Tkinter import *
try:
     from PIL import Image, ImageTk
except ImportError:
     import Image, ImageTk
from pwytter import __version__ as VERSION

class Splash(Toplevel):
     def __init__(self, master):
         """(master) -> create a splash screen
         """
         Toplevel.__init__(self, master, bd=1, bg='#99CBFE')
         self.main = master
         self.main.withdraw()
         self.overrideredirect(1)
#         im = Image.open(image)
#         self.image = ImageTk.PhotoImage(im)
         self.after_idle(self.centerOnScreen)
         self.update()
         #self.after(timeout, self.destroy)

     def centerOnScreen(self):
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
     # Need to fill in here
         self.Box=Frame(self,bg='black', padx=1, pady=1)
         self.Title =Label(self.Box,text=_("Pwytter"),font=('Helvetica', 14, 'bold'), bg="black", fg="white")
         self.Title.pack()
         self.Version =Label(self.Box,text=VERSION,font=('Helvetica', 14, 'bold'), bg="black", fg="white")
         self.Version.pack()
         self.Loading =Label(self.Box,text=_("Loading..."), bg="black", fg="white")
         self.Loading.pack()
         self.Box.pack()
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
     time.sleep(5)
     s.destroy() 
     tk.mainloop()