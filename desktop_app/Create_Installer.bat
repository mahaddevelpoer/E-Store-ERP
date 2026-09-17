@echo off
echo =======================================================
echo   ElectroStore POS & Inventory System Installer Builder
echo =======================================================
echo.
echo Installing requirements...
python -m pip install -r requirements.txt
python -m pip install pyinstaller

echo.
echo Building standalone executable bundle...
python -m PyInstaller --noconfirm --onedir --windowed --name "ElectroStore_POS_Setup" main.py

echo.
echo =======================================================
echo   BUILD COMPLETE! 
echo   Executable Location: dist\ElectroStore_POS_Setup\ElectroStore_POS_Setup.exe
echo =======================================================
pause
