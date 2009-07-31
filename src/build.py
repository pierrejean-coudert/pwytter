#!/usr/bin/env python

import os
from os import path

commands = ("pyuic4 " + path.join("ui", "mainwindow.ui") + " -o " + path.join("ui", "ui_mainwindow.py"),
            "pyuic4 " + path.join("ui", "newtwitteraccountdialog.ui") + " -o " + path.join("ui", "ui_newtwitteraccountdialog.py"),
            "pyuic4 " + path.join("ui", "newidenticaaccountdialog.ui") + " -o " + path.join("ui", "ui_newidenticaaccountdialog.py"),
            "pyuic4 " + path.join("ui", "preferencesdialog.ui") + " -o " + path.join("ui", "ui_preferencesdialog.py"),
            "pyrcc4 " + path.join("ui", "ressources.qrc") + " -o " + path.join("ui", "ressources_rc.py")
)

for command in commands:
    print command
    os.system(command)
