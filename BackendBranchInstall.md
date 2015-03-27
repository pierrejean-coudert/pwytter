These installation methods should only be used by developers and beta testers.

# Get Source Code #
```
svn checkout http://pwytter.googlecode.com/svn/branches/backend_split/src/ pwytter-qt
```

for registered developper
```
svn checkout https://pwytter.googlecode.com/svn/branches/backend_split/src/ pwytter-qt --username your.user.name
```

# Windows #

## Dependencies ##
  * [Python 2.6](http://python.org/ftp/python/2.6.2/python-2.6.2.msi)
  * [PyQT](http://www.riverbankcomputing.co.uk/software/pyqt/download)
  * pyyaml
  * simplejson
  * [py2exe](http://py2exe.org/) (optional)

If you wish to build py2exe bundles using the included setup.py script, pyyaml and simplejson must be installed and extracted, e.g. not installed as compressed eggs. You can install and extract pyyaml and simplejson using `easy_install -Z pyyaml` and `easy_install -Z simplejson`. Alternately, if you don't wish to build bundles using py2exe, pyyaml and simplejson can be installed using `setup.py develop` (the setup.py script is included in the source folder).

Note: if you ever need to [install setuptools (easy\_install) on windows for python 2.6, here is the procedure](http://stackoverflow.com/questions/309412/how-to-setup-setuptools-for-python-2-6-on-windows).

# Ubuntu/Debian #

## Dependencies ##
  * python-yaml >= 3.0
  * python-simplejson >= 1.9
  * python-qt4 >= 4.4

All dependencies can be installed using the package manager.

# Run Pwytter #
```
python pwytter.pyw
```