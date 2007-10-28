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

'''A Cache class for Pwytter based on python-twitter internal cache'''

import os
import md5
import tempfile
import time
import urllib2


class PwytterCacheError(Exception):
  '''Base exception class for FileCache related errors'''

class PwytterCache(object):

  DEPTH = 3

  def __init__(self,root_directory=None):
    self._InitializeRootDirectory(root_directory)

  def Get(self,key):
    path = self._GetPath(key)
    if os.path.exists(path):
      return open(path,"rb").read()
    else:
      return None

  def GetTimeout(self,key, timeout = 60):
      last_cached = self.GetCachedTime(key)
      if not last_cached or time.time() >= last_cached + timeout:
          return None
      else:
          return self.Get(key)
      
  def Set(self,key,data):
    path = self._GetPath(key)
    directory = os.path.dirname(path)
    if not os.path.exists(directory):
      try:
        os.makedirs(directory)
      except OSError, E :
        print "Path created by another thread"  
          
    if not os.path.isdir(directory):
      raise PwytterCacheError('%s exists but is not a directory' % directory)
    temp_fd, temp_path = tempfile.mkstemp()
    temp_fp = os.fdopen(temp_fd, 'wb')
    temp_fp.write(data)
    temp_fp.close()
    if not path.startswith(self._root_directory):
      raise PwytterCacheError('%s does not appear to live under %s' %
                            (path, self._root_directory))
    if os.path.exists(path):
      os.remove(path)
    os.rename(temp_path, path)

  def Remove(self,key):
    path = self._GetPath(key)
    if not path.startswith(self._root_directory):
      raise PwytterCacheError('%s does not appear to live under %s' %
                            (path, self._root_directory ))
    if os.path.exists(path):
      os.remove(path)

  def GetCachedTime(self,key):
    path = self._GetPath(key)
    if os.path.exists(path):
      return os.path.getmtime(path)
    else:
      return None

  def GetUrl(self, url, timeout=0):
      #LoadedImage=self._cache.Remove(imageurl)
      last_cached = self.GetCachedTime(url)
      # If the cached version is outdated then fetch another and store it
      if not last_cached or time.time() >= last_cached + timeout:
          data=urllib2.urlopen(url).read()
          self.Set(url,data)
      else:
          data=self.Get(url)
      return data
 
  def _GetUsername(self):
    '''Attempt to find the username in a cross-platform fashion.'''
    return os.getenv('USER') or \
        os.getenv('LOGNAME') or \
        os.getenv('USERNAME') or \
        os.getlogin() or \
        'nobody'

  def _GetTmpCachePath(self):
    username = self._GetUsername()
    cache_directory = 'python.cache_' + username
    return os.path.join(tempfile.gettempdir(), cache_directory)

  def _InitializeRootDirectory(self, root_directory):
    if not root_directory:
      root_directory = self._GetTmpCachePath()
    root_directory = os.path.abspath(root_directory)
    if not os.path.exists(root_directory):
      os.mkdir(root_directory)
    if not os.path.isdir(root_directory):
      raise PwytterCacheError('%s exists but is not a directory' %
                            root_directory)
    self._root_directory = root_directory

  def _GetPath(self,key):
    hashed_key = md5.new(key).hexdigest()
    return os.path.join(self._root_directory,
                        self._GetPrefix(hashed_key),
                        hashed_key)

  def _GetPrefix(self,hashed_key):
    return os.path.sep.join(hashed_key[0:PwytterCache.DEPTH])
    