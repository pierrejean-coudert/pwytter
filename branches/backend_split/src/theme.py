# -*- coding: utf-8 -*-

"""Pwytter theme module

    This module loads and parses themes for Pwytter.
"""

import tinpy
import yaml
import os
import os.path
from PyQt4.QtCore import *


search_directories = ("./themes/",)
"""Tuple of search directories, ordered by importance.
    If two of the search directories contains a theme with the same name,
    the theme in the search directory that appears first in the tuple will
    be choosen used.
"""

def getThemes():
    """Returns all the available themes using a generator."""
    names = () #Tuple of the loaded names, to avoid returning the same name more than once.
    for directory in search_directories:
        for entry in os.listdir(unicode(directory)):
            path = os.path.join(directory, entry)
            if entry not in names and os.path.isdir(path) and os.path.isfile(os.path.join(path, "info.yaml")):
                names += (entry,)
                yield Theme(entry, path) #Return using generator to offer better performance

class Theme:
    """Simple wrapper class to access theme information.
    
        Accessing all theme information through instances of this class will make it easier to
        support old themes in newer versions of Pwytter.
    """
    def __init__(self, name = "default", path = None):
        """Create a instance of Theme.
        
            Note: name must the be theme name of a theme in one of the search directories.
        """
        self.__name = name
        #If path is not provided search for it
        if not path:
            for directory in search_directories:
                for entry in os.listdir(unicode(directory)):
                    if entry == name: #First check the name, then check if it's a dir that contains an yaml file
                        if os.path.isdir(os.path.join(directory, name)) and os.path.isfile(os.path.join(directory, name, "info.yaml")):
                            path = os.path.join(directory, name) #If it is a theme, set path and break
                            break
        if not path: #If we haven't got a path by now, the theme does not exists
            raise Exception, "A theme with the name '%' does not exist in any of the search directories.", name
        self.__path = path
        self.__info = yaml.load(open(os.path.join(self.__path, "info.yaml")).read())
        
    def getTitle(self):
        """Gets the title of the theme.
        
            The theme title is a non-unique string that may contain special characters.
            Use this string to represent this theme to the user.
        """
        return self.__info["Title"]
    
    def getName(self):
        """Gets the name of the theme.
        
            Theme name is unique name, not meant to be presented to the user.
        """
        return self.__name
    
    def getAuthors(self):
        """Gets the authors of this theme as a dictionary, with names as keys and e-mail addresses as values."""
        return self.__info["Authors"]
    
    def getWebsite(self):
        """Gets the website for this theme."""
        return self.__info["Website"]
        
    def getVersion(self):
        """Gets the version of this theme as float"""
        return self.__info["Version"]
        
    def getRequires(self):
        """Gets the version of the theme documentation, this theme is coded against."""
        return self.__info["Requires"]
        
    def getDescription(self):
        """Gets a description of this theme."""
        return self.__info["Description"]
        
    def getPreview(self):
        """Gets a preview of this theme as buffer."""
        return str(open(os.path.join(self.__path, "preview.png")).read())
        
    def __repr__(self):
        """Gets a string representation of this theme."""
        return "<theme.Theme instance loaded from '" + self.__path + "' at " + hex(id(self)) + ">"
        
    def __str__(self):
        """Gets the title of this theme"""
        return self.getTitle()

    def getPath(self):
        """Gets the path to the theme directory of this theme."""
        return self.__path

    __messagesTemplate = None
    __usersTemplate = None
    __detailedUserTemplate = None
    
    def getMessagesTemplate(self):
        """Gets the messages template for this theme."""
        if not self.__messagesTemplate:
            self.__messagesTemplate = tinpy.compile(open(os.path.join(self.__path, "Messages.tpl")).read())
        return self.__messagesTemplate
    
    def getUsersTemplate(self):
        """Gets the users template for this theme."""
        if not self.__usersTemplate:
            self.__usersTemplate = tinpy.compile(open(os.path.join(self.__path, "Users.tpl")).read())
        return self.__usersTemplate
    
    def getDetailedUserTemplate(self):
        """Gets the detailed user template for this theme."""
        if not self.__detailedUserTemplate:
            self.__detailedUserTemplate = tinpy.compile(open(os.path.join(self.__path, "DetailedUser.tpl")).read())
        return self.__detailedUserTemplate

    def getQtStylesheet(self):
        """Gets the Qt Stylesheet for this theme as string."""
        path = os.path.join(self.__path, "application.qss")
        if os.path.isfile(path):
            return open(path).read()
        else:
            return ""
