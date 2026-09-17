@echo off
title E-Store POS & Management System - Setup Wizard
color 0A
cls

echo ====================================================================
echo                 E-STORE POS SETUP WIZARD
echo ====================================================================
echo.
echo Welcome to the E-Store POS & Management System Installation Wizard.
echo This wizard will build and package E-Store POS into your system.
echo.
echo [1/3] Verifying Python Environment & Installing Required Libraries...
"C:\Users\HP\AppData\Local\Programs\Python\Python314\python.exe" -m pip install -r requirements.txt
"C:\Users\HP\AppData\Local\Programs\Python\Python314\python.exe" -m pip install pyinstaller pywebview

echo.
echo [2/3] Compiling Fluent Desktop Package (E-Store POS)...
"C:\Users\HP\AppData\Local\Programs\Python\Python314\python.exe" -m PyInstaller --noconfirm --onefile --windowed --add-data "src/web;src/web" --name "E-Store_POS_Fluent_Setup" app.py

echo.
echo [3/3] Creating E-Store Desktop Shortcut...
powershell -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut([System.IO.Path]::Combine([Environment]::GetFolderPath('Desktop'), 'E-Store POS.lnk'));$s.TargetPath='%~dp0dist\E-Store_POS_Fluent_Setup.exe';$s.WorkingDirectory='%~dp0dist';$s.Save()"

echo.
echo ====================================================================
echo              INSTALLATION COMPLETED SUCCESSFULLY!
echo ====================================================================
echo.
echo  - Desktop Shortcut created: 'E-Store POS.lnk'
echo  - Executable Path: %~dp0dist\E-Store_POS_Fluent_Setup.exe
echo.
echo Press any key to launch E-Store POS now...
pause > nul
start "" "%~dp0dist\E-Store_POS_Fluent_Setup.exe"
