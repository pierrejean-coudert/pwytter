#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from os import path
#from pkg_resources import Requirement, resource_filename

from ui import translations_rc
from PyQt4.QtCore import QLocale, QTranslator
from PyQt4.QtGui import QApplication
from mainwindow import MainWindow
__version__ = "0.1"

import theme

def module_path():
    """ Gets the path where this module is placed
        This function works even if this module have been compiled with py2exe.
        See py2exe wiki: http://www.py2exe.org/index.cgi/WhereAmI
    """
    if hasattr(sys, "frozen"):
        return path.dirname(unicode(sys.executable, sys.getfilesystemencoding()))
    return path.dirname(unicode(__file__, sys.getfilesystemencoding()))

if __name__ == "__main__":
    #Setup search directories for themes
    theme.search_directories = ()
    #Simply guessing where to look for themes, resource_filename(Requirement.parse("Pwytter"), "themes/") doesn't work
    #TODO: Add user_themes here, e.g. themes installed without admin rights
    local_themes = path.join(module_path(), "themes")
    if path.isdir(local_themes):
        theme.search_directories += (local_themes,)
    installed_themes = path.join(sys.prefix, "share", "pwytter", "themes")
    if path.isdir(installed_themes):
        theme.search_directories += (installed_themes,)
    
    #Create application
    application = QApplication(sys.argv)
    #Load translations if available
    locale = QLocale.system().name()
    translator = QTranslator()
    if translator.load("pwytter." + locale, ":/translations/locale/"):
        application.installTranslator(translator)
    #Create main window
    mainWindow = MainWindow()
    mainWindow.show()
    #Start main loop
    sys.exit(application.exec_())
