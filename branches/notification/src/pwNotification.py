import urllib
import time
import sys
import os
from pwTools import platform
import os.path
from pwytter import __app_path__

if platform() == 'linux' :
    import pygst
    import pygtk
    pygst.require('0.10')
    pygtk.require('2.0')
    import pynotify
    import gtk
    import gst

class PwytterNotify(object):
    """Manages history of Twitter status updates."""

    def __init__(self,api):
        self.api = api
        self.image_directory = "~/.pwytter/images"
        self.image_storage = os.path.expanduser(self.image_directory)
        self._DefaultImagePath =  os.path.join(__app_path__,'media')
        self._DefaultFileName = os.path.join(self._DefaultImagePath,'loading.png')
        if not os.path.exists(self.image_storage):
            os.makedirs(self.image_storage)

    def _display_count(self,user,count) :
        text = " %s ,you have %d new tweets" % (user,count)
        imagenm = "pwytter.png"
        if count!=0:
               self._send_note("Pwytter",text,imagenm)

    def _notify_tweet(self, status):
            self.status = status
            try:
                username = status.user.screen_name.encode('latin-1','replace')
            except AttributeError:
                username = status.sender_screen_name.encode('latin-1','replace')
            #Find image
            imagepath = self._cached_image(username)
            # Markup Hyperlinks
            text = status.text
            if "http://" in text:
                for i in text.split():
                    if i.startswith("http://"):
                        text = text.replace(i, \
                               '<a href="' + i + '">' + i + '</a>')

            # Call notification
            self._send_note(username, text, imagepath )


    def _cached_image(self, username):
        """Check for already downloaded profile image."""
        for i in os.listdir(self.image_storage):
            if i.startswith(username + "."):
                  return i


    def _send_note(self,user, message, imageurl):
        """Send the note to the desktop."""

        if not imageurl:
            #imageurl= self._paramFileName
            try:
                profile_image = self.status.user.profile_image_url
            except AttributeError:
                profile_image = self.api.GetUser(\
                                user).GetProfileImageUrl()
            fileextension = profile_image.rpartition('.')[-1]
            imageurl = self.image_storage + "/" + user + "." + fileextension
            try :
              urllib.urlretrieve(profile_image, imageurl)
            except Exception,e :
                print "time out",e
                imageurl = self._DefaultFileName
        else :
            imageurl = self.image_storage+ "/" + imageurl


        try:
            ascii_message = message.encode('ascii','replace')
            print imageurl
            if platform() == 'linux' :
               print "Linux notifications"
               if not pynotify.init("Pwytter"):
                   try :
                        raise Exception('pynotify is not initialized')
                   except Exception ,inst :
                        print "Error :",inst
               self._create_sound()
               note = pynotify.Notification(user, ascii_message, imageurl)
               if not note.show():
                   try :
                      raise Exception('failed to send notification')
                   except Exception ,inst:
                      print "Error :",inst
            elif platform() == 'windows' :
               str = 'growlnotify /t:"%s" /a:"pwytter" /r:""  /i:"%s"  /s:true "%s"' % (user,imageurl,ascii_message)
               os.system(str)
            elif platform() == 'mac' :
               str = 'growlnotify -t "%s" -a "pwytter" -i "%s" -m"%s"\n' % (user,imageurl,ascii_message)
               os.system(str)
        except Exception,e :
            print "notify error",e

    def _create_sound(self):
        # This will create pipeline pwytter
        self.pipeline = gst.Pipeline("pwytter")
        # This will create element filesrc
        self.filesrc = gst.element_factory_make("filesrc", "source")
        try :
          if not self.filesrc :
             raise Exception('couldnt fine plugin \"filesrc\"')
        except Exception ,e :
            print "Error :" ,e
        # This will set location property of filesrc
        self.filesrc.set_property('location',"ringin.mp3")
        # Add filesrc to pipeline
        self.pipeline.add(self.filesrc)

        # This will create elements like mad ,audioconvert , audioresample and sink
        self.mad = gst.element_factory_make("mad","mad")
        self.audioconvert = gst.element_factory_make("audioconvert","convert")
        self.audioresample = gst.element_factory_make("audioresample","resample")
        self.sink = gst.element_factory_make("osssink", "sink")


        # This will add  elements like mad , audioconvert ,audioresample ,sink
        self.pipeline.add(self.mad)
        self.pipeline.add(self.audioconvert)
        self.pipeline.add(self.audioresample)
        self.pipeline.add(self.sink)

        # This will link filesrc -> mad -> audioconvert -> audioresample ->sink
        self.filesrc.link(self.mad)
        self.mad.link(self.audioconvert)
        self.audioconvert.link(self.audioresample)
        self.audioresample.link(self.sink)

        # This will set state of pipeline to playing
        self.pipeline.set_state(gst.STATE_PLAYING)
        time.sleep(1)
        # Deallocate all resources
        self.pipeline.set_state(gst.STATE_NULL)


