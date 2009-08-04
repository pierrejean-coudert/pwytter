#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from os import path
from pkg_resources import Requirement, resource_filename

from PyQt4.QtCore import QLocale, QTranslator
from PyQt4.QtGui import QApplication
from mainwindow import MainWindow
__version__ = "0.1"

import theme

if __name__ == "__main__":
    #Setup search directories for themes
    theme.search_directories = ()
    #Simply guessing where to look for themes, resource_filename(Requirement.parse("Pwytter"), "themes/") doesn't work
    #TODO: Add user_themes here, e.g. themes installed without admin rights
    local_themes = path.join(path.dirname(__file__), "themes")
    if path.isdir(local_themes):
        theme.search_directories += (local_themes,)
    installed_themes = path.join(sys.prefix, "share", "pwytter", "themes")
    if path.isdir(installed_themes):
        theme.search_directories += (installed_themes,)

    #Create application and main window
    application = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    #Start main loop
    sys.exit(application.exec_())
