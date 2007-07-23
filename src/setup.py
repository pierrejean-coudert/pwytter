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

from distutils.core import setup
import os
if os.name=='nt':
    import py2exe
import glob
#PIL specific
#import Image

from pwytter import __version__ as VERSION

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
               'simplejson': 'twclient/simplejson'},
  #package_data={'twclient': glob.glob('twclient/doc/*.*')},
  py_modules = ['pwytter','tkBalloon'],
  data_files=[("text", glob.glob("*.txt")),
              "pwytter.ico",
              ("media",glob.glob("media\\*.*"))],
  #console=['pwytter.py']
  windows = [
        {"script": "pwytter.py",
         "icon_resources": [(1, "pwytter.ico")]
        }]
)