rem rmdir /s /q build
rmdir /s /q dist
rem python setup.py sdist --formats=gztar
python setup.py sdist --formats=zip
