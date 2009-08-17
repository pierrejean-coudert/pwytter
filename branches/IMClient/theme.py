# -*- coding: utf-8 -*-

"""Pwytter theme module

    This module loads and parses themes for Pwytter.
"""

import tinpy
import yaml
import os
import os.path
from PyQt4.QtCore import *

version = (0, 1, 0)
""" Version of the theme documentation that this module supports

    For more information see: http://code.google.com/p/pwytter/wiki/PwytterThemeDocumentation#Versioning
"""

class InvalidThemeError(Exception):
    """Thrown if the theme being loaded is invalid."""
    def __init__(self, name = None, text = None):
        self._name = name
        self._text = text
    def __str__(self):
        if self._name:
            msg = "Theme " + self._name + " is invalid"
        else:
            msg = "Theme is invalid"
        if self._text:
            return msg + ": " + self._text
        else:
            return msg + ", ensure compliance with Pwytter theme documentation."

class ThemeNotFoundError(Exception):
    """Thrown if the theme being loaded is not found."""
    def __init__(self, name = None):
        self._name = name
    
    def __str__(self):
        if self._name:
            return "Theme " + self._name + " was not found in the search directories."
        else:
            return "Theme was not found in the search directories."

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
            if entry not in names and os.path.isdir(path):
                try:
                    #Return using generator to offer better performance
                    yield Theme(entry, path)
                    names += (entry,)
                except InvalidThemeError:
                    continue

class Theme:
    """Simple wrapper class to access theme information.
    
        Accessing all theme information through instances of this class will make it easier to
        support old themes in newer versions of Pwytter.
    """
    def __init__(self, name = "default", path = None):
        """Create a instance of Theme.
        
            Note: name must the be theme name of a theme in one of the search directories.
            This constructor will raise an exception if the theme is not valid.
        """
        self.__name = name
        #If path is not provided search for it
        for directory in search_directories:
            if path: break
            for entry in os.listdir(unicode(directory)):
                if entry == name: #First check the name, then check if it's a dir that contains an yaml file
                    if os.path.isdir(os.path.join(directory, name)) and os.path.isfile(os.path.join(directory, name, "info.yaml")):
                        path = os.path.join(directory, name) #If it is a theme, set path and break
                        break
        if not path: #If we haven't got a path by now, the theme does not exists
            raise ThemeNotFoundError, name
        self.__path = path
        
        #Load meta information
        try:
            self.__info = yaml.load(open(os.path.join(self.__path, "info.yaml")).read())
        except IOError:
            raise InvalidThemeError(name, "A theme must contain a info.yaml file.")
        
        #Validate theme
        #Consider placing this code in a if __debug__: so that it only gets executed during debug
        try:
            #Check required API version
            if not isinstance(self.__info["Requires"], basestring):
                raise InvalidThemeError(name, "info.yaml key 'Requires' must be a string.")
            #Parse API version
            t_api = self.__info["Requires"].split(".")
            t_api = int(t_api[0]), int(t_api[1]), int(t_api[2])
            #If the theme is coded against a future version of theme documentation
            if version[0] > t_api[0] or version[1] > t_api[1]:
                raise InvalidThemeError(name, "Theme reqiures newer version of Pwytter.")
            #Check that all the fields that must be strings are strings
            strings = ("Title", "Website", "Version", "Description")
            for string in strings:
                if not isinstance(self.__info[string], basestring):
                    raise InvalidThemeError(name, "info.yaml key '" + string + "' must be a string.")
            #Check that authors is a dict and all it's keys and values are strings
            if not isinstance(self.__info["Authors"], dict):
                raise InvalidThemeError(name, "info.yaml key 'Authors' must be a dictionary.")
            for author, email in self.__info["Authors"].items():
                if not isinstance(author, basestring):
                    raise InvalidThemeError(name, "Author entries, e.g. keys, in the info.yaml key 'Authors' dictionary must be a string.")
                if not isinstance(email, basestring):
                    raise InvalidThemeError(name, "Email entries, e.g. values, in the info.yaml key 'Authors' dictionary must be a string.")
            #Check that preview.png exists
            if not os.path.isfile(os.path.join(self.__path, "preview.png")):
                raise InvalidThemeError(name, "Theme doesn't contain a 'preview.png' image.")
            #Check that templates exists
            templates = ("Messages.tpl", "Users.tpl", "DetailedUser.tpl")
            for template in templates:
                if not os.path.isfile(os.path.join(self.__path, template)):
                    raise InvalidThemeError(name, "Theme doesn't contain a '" + template + "' file as template.")
            #If QtStyles is provided check if it's a list/tuple of strings
            if "QtStyles" in self.__info:
                if not isinstance(self.__info["QtStyles"], (list, tuple)):
                    raise InvalidThemeError(name, "info.yaml key 'QtStyles' must be a list if provided.")
                for style in self.__info["QtStyles"]:
                    if not isinstance(style, basestring):
                        raise InvalidThemeError(name, "All entries in the 'QtStyles' list in info.yaml must be strings.")
        except KeyError, error:
            if len(error.args) > 0:
                raise InvalidThemeError(name, "Metainfo key for " + error.args[0] + " is missing in info.yaml")
            else:
                raise InvalidThemeError(name, "Metainfo key missing in info.yaml")
        
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
        """Gets the version of this theme as string"""
        return self.__info["Version"]
        
    def getRequires(self):
        """Gets the version of the theme documentation, this theme is coded against."""
        return self.__info["Requires"]
        
    def getDescription(self):
        """Gets a description of this theme."""
        return self.__info["Description"]
        
    def getPreview(self):
        """Gets a preview of this theme as buffer."""
        return open(os.path.join(self.__path, "preview.png"), "rb").read()
        
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

    def getQStyles(self):
        """Gets a list of strings identifing QStyles.
            If the first style on the list on unavailable use the next,
            and if none of them are available use the default style.
        """
        try:
            return self.__info["QtStyles"]
        except KeyError:
            return []
