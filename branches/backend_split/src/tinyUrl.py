#!/usr/bin/env python

"""
    Convert long urls into small urls using (for example) UrlTea    
    Hack by Thomas Chiroux
"""

import sys, getopt, urllib2
import threading 
  
class TinyUrl(object):  

    def __init__(self, twitText):
        self._gettingTinyUrl = False 
        self._twitText = twitText
              
    def _threadReduceUrl(self, url):
        #print 'starting thread'
        self._gettingTinyUrl = True
        # time.sleep(3) # to test the lag of the network
        newurl = self.getTiny(url)
        #print 'url found : |%s|%s| !' % (url, newurl)
        if (len(newurl) < len(url)):
            text = self._twitText.get()
            text = text.replace(url, newurl)
            #print text
            self._twitText.set(text)
        #print 'end of thread'
        self._gettingTinyUrl = False
              
    
    def getTiny(self, url):
        try:
            #  urltea : "http://urltea.com/api/text/?url="
            #  tinyurl : "http://tinyurl.com/api-create.php?url="
            requesturl="http://tinyurl.com/api-create.php?url="+url #+urllib.urlencode({"url":url})
            instream=urllib2.urlopen(requesturl)
            tinyurl=instream.read()
            instream.close()
            
            if len(tinyurl)==0:
                return url
        
            return tinyurl
        except IOError, e:
            raise "Failed !"
        
    def convertTinyUrl(self):
        if self._gettingTinyUrl == False :
            text = self._twitText.get()
            actualLength = len(text)
            if (text.endswith(' ')):
                precspace = text.rfind(' ', 0, actualLength-2)
                #print "precspace : %s" % precspace
                if precspace == -1:
                    precspace = 0
                pos = text.rfind('http://tinyurl.com', precspace, actualLength-2)
                if pos != -1 : # already shrinked
                    print "already shrinked"
                    return
                pos = text.rfind('http://', precspace, actualLength-2)
                if pos != -1 : # URL found, lets start a thread to shrink it !
                    print "start shrink"
                    url = text[pos:actualLength-1]
                    t = threading.Thread(target=self._threadReduceUrl,args=(url, ))
                    t.start()    
    
