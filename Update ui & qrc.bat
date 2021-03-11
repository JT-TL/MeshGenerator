rem this script converts result from Qt Designer into python code
rem compile ui file from Qt Designer
"D:\Programs\Python37\Scripts\pyuic5.exe" -x design.ui -o design.py
rem compile resource file (icons, etc..)
"D:\Programs\Python37\Scripts\pyrcc5.exe" .\resources\main.qrc -o .\main_rc.py