#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from os import path

#If we can't get dependencies from the system, add the dependencies folder to search paths
#Most linux distributions will have yaml and simplejson as seperate packages.
try:
	import yaml
	import simplejson
except:
	sys.path += path.join(path.abspath(__file__), "dependencies")

from PyQt4.QtCore import QLocale, QTranslator
from PyQt4.QtGui import QApplication
from mainwindow import MainWindow
__version__ = "0.1"
	
if __name__ == "__main__":
	application = QApplication(sys.argv)
	mainWindow = MainWindow()
	mainWindow.show()
	#Start main loop
	sys.exit(application.exec_())
