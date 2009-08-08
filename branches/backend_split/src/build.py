#!/usr/bin/env python

""" Build ui, ressources and translation files for Pwytter

    This script will build ressources and make all the different Qt designer files into base classes
    so that these need not be loaded and parsed at runtime.
    This script will also build qm files from all the translations available in ui/locale/
    To add or update a translation file run:
    pylupdate4 *.py ui/*.py -ts ui/locale/pwytter_<lang>.ts
    Where <lang> the language you wish to translate to, upon running this script the translation files
    will be released, e.g. converted to .qm files, and added to the translations.qrc file, which should
    never be alter manually, this ressource file will be compiled and used in Pwytter.
    Translators should run pylupdate4 before each release of Pwytter and check that the .ts files is
    translated. This build script does not update the .ts files.
"""

import os
from os import path
from glob import glob

commands = ("pyuic4 " + path.join("ui", "mainwindow.ui") + " -o " + path.join("ui", "ui_mainwindow.py"),
            "pyuic4 " + path.join("ui", "newtwitteraccountdialog.ui") + " -o " + path.join("ui", "ui_newtwitteraccountdialog.py"),
            "pyuic4 " + path.join("ui", "newidenticaaccountdialog.ui") + " -o " + path.join("ui", "ui_newidenticaaccountdialog.py"),
            "pyuic4 " + path.join("ui", "preferencesdialog.ui") + " -o " + path.join("ui", "ui_preferencesdialog.py"),
            "lrelease " + path.join("ui", "locale", "pwytter.*.ts"),
            "pyrcc4 " + path.join("ui", "ressources.qrc") + " -o " + path.join("ui", "ressources_rc.py")
)

def build():
    #Run commands defined above
    for command in commands:
        print command
        os.system(command)
    #Generate ressources file with translations
    print "Translations:"
    rc = open(path.join("ui", "translations.qrc"), "w")
    rc.write("""<RCC>\n  <qresource prefix="translations" >\n""")
    for translation in glob(path.join("ui", "locale", "pwytter.*.qm")):
        rc.write("    <file>" + translation[3:] + "</file>\n")
        print "    " + translation[18:-3]
    rc.write("  </qresource>\n</RCC>")
    rc.close()
    #Compile translations ressources file
    command = "pyrcc4 " + path.join("ui", "translations.qrc") + " -o " + path.join("ui", "translations_rc.py")
    print command
    os.system(command)

if __name__ == "__main__":
    build()
