@echo off
title Launching E-Store POS...
cd /d "%~dp0"

if exist "dist\E-Store_POS\E-Store_POS.exe" (
    echo Starting compiled E-Store POS application...
    start "" "dist\E-Store_POS\E-Store_POS.exe"
) else (
    echo Starting E-Store POS via Python...
    "C:\Users\HP\AppData\Local\Programs\Python\Python314\python.exe" main.py
)
