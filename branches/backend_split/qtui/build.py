#!/usr/bin/env python

import os

commands = ("pyuic4 mainwindow.ui -o ui_mainwindow.py",
			"pyuic4 newtwitteraccountdialog.ui -o ui_newtwitteraccountdialog.py",
			"pyuic4 newidenticaaccountdialog.ui -o ui_newidenticaaccountdialog.py",
			"pyrcc4 ressources.qrc -o ressources_rc.py"
)

for command in commands:
	print command
	os.system(command)
