#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Setup script for Pwytter

    Setuptools and distutils does not appear to be designed for distributing
    applications, as it does not support private packages and modules, e.g. all
    modules and packages are installed in pythons system search directories.
    Instead of an application specific directory such as /usr/share/pwytter/.

    Instructions for Debian/Ubuntu package:
     - Install stdeb: http://github.com/astraw/stdeb
     - run setup.py sdist_dsc
     - navigate to ./deb_dist/pwytter-x.y.z/
     - run dpkg-buildpackage -rfakeroot -uc -us
    Note: This barely works and does NOT conform with Debian python policy!
"""

#Build stuff before setup
#from build import build
#TODO: Build all files...
#build()

from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages
import platform
__version__ = "0.1"

#Dictionary for platform specific options
platform_options = {}

#Linux specific options
if platform.system() == "Linux":
    pass
#Windows specific options
elif platform.system() == "Windows":
    pass
    #TODO: py2exe specifics
#OS X specific options
elif platform.system() == "Darwin":
    pass
    #TODO: py2app specifics

import os

def datafiles(target, source, dictionary = {}):
    """Generates a list of pairs of target directory and source files
       Recursively for all files in the source directory.

       Used to add themes as data files to setup()
    """
    for item in os.listdir(source):
        if item.startswith("."):
            continue
        item_target = os.path.join(target, item)
        item_source = os.path.join(source, item)
        if os.path.isfile(item_source):
            if target not in dictionary:
                dictionary[target] = []
            dictionary[target] += [item_source,]
        else:
            datafiles(item_target, item_source, dictionary)
    return dictionary.items()

setup(
    #Metadata
    name = "Pwytter",
    version = __version__,
    #TODO: Update contact info
    author = "Jonas Finnemann Jensen",
    author_email = "jopsen@gmail.com",
    #TODO: Improve documentation and add more meta data
    description = "A python client for microblog services.",
    license = "GPLv2",

    #About the package
    packages = find_packages(),
    py_modules = ["mainwindow", "newidenticaaccountdialog", "newtwitteraccountdialog", "preferencesdialog", "theme", "tinpy", "tweetview"],
    scripts = ["pwytter.pyw"],
    install_requires = ["pyyaml>=2.0", "simplejson>=1.9"],
    include_package_data = False,
    data_files = datafiles(os.path.join("share", "pwytter", "themes"), "themes"),
    #Platform specifics, py2exe, py2app, etc.
    **platform_options
)
