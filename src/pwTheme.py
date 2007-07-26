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

import os

class pwTheme(object):
    def __init__(self, aName="black"):
        self._themePath = 'theme'
        self._themeFile = os.path.join(self._themePath, aName+'.pwt')        
        self.values={}
        self._initDefault()

    def _initDefault(self):
        self.values={
            'text#'     : "white",
            'bg#'       : "#1F242A",
            '1stLine#'  : "#484C4F",
            'line#'     : "#2F3237",
            'param#'    : "#585C5F",
            'timeline#' : "#484C4F",
            'me_bg#'    : "#2F3237", 
            'me_fg#'    : "#BBBBBB",
            'time#'     : "#BBBBBB",
            'message#'  : "#99CBFE",
            'messageUrl#': "#B9DBFF",
            'directMsg#': "#686C6F",
            'update#'   : "#FFBBBB",
            'twitEdit#' : "#2F3237"
            }
        
    def readFromFile(self):
        f = open(self._themeFile,'r')
        for line in f.readlines():
            color, value = line.split(':')
            color, value = color.strip(), value.strip()
            self.values[color] = value

    def __getitem__(self, aKey):
        return self.values[aKey]
        
    def __setitem__(self, aKey, value):
        self.values[aKey] = value
            
if __name__ == "__main__":
    th=pwTheme('blue')
    th.readFromFile()
    print th.values
