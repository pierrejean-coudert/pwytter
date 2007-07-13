#!/usr/bin/python
#
# Copyright 2007 Pierre-Jean Coudert. All Rights Reserved.

from distutils.core import setup
import py2exe
from pwytter import __version__ as VERSION
import glob
#PIL specific
#import Image
  
setup(  
  name = "pwytter",
  version = VERSION,
  author='Pierre-Jean Coudert',
  author_email='coudert@free.fr',
  description='A python client for Twitter',
  long_description='A python client for Twitter. Portable User Interface in Tk.',
  license='GPL 2',
  platforms=['any'],
  url='http://www.pwytter.com',
  keywords='twitter client python tkinter',
  packages=['twclient','simplejson'],
  package_dir={'twclient': 'twclient', 
               'simplejson': 'twclient:simplejson'},
  package_data={'twclient': ['doc/*.*']},
  py_modules = ['pwytter','tkBalloon'],
  data_files=[("text", glob.glob("*.txt")),
              "pwytter.ico",
              ("media",glob.glob("media\\*.*"))],
  #console=['pwytter.py'],
  windows = [
        {"script": "pwytter.py",
         "icon_resources": [(1, "pwytter.ico")]
        }]
)