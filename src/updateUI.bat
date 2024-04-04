@echo off
@echo run this file to update ui when edit in Qt Designer
echo -----------------------------------------
echo - PyQt Designer exec: Update resource
pyrcc5 resource.qrc -o resource_rc.py
echo - Done!
echo -----------------------------------------
echo - PyQt Designer exec: Update UI
pyuic5 -o sidebar_ui.py .\sidebar.ui
echo - Done!
echo -----------------------------------------

pushd ..
python3 ./src/main.py
popd