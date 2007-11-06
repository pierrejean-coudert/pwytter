rmdir /s /q build
rmdir /s /q dist
python setup.py py2exe

"C:\Program Files\ISTool\ISTool.exe" -compile win32_setup\pwytter_setup_script.iss

