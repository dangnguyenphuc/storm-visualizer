@echo off
@echo run this file to update ui when edit in Qt Designer
echo -----------------------------------------
echo - PyQt Designer exec: Update resource
pyrcc5 .\src\resource.qrc -o .\src\resource_rc.py
echo - Done!
echo -----------------------------------------
echo - PyQt Designer exec: Update UI
pyuic5 -o .\src\Frontend.py .\src\Frontend.ui
echo - Done!
echo -----------------------------------------

python3 .\src\main.py
