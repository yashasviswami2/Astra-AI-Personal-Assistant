@echo off
:: Change to the folder of this batch file
cd /d "%~dp0"

:: Start ASTRA using pythonw.exe so no console window remains open
start "" "C:\Users\acer\AppData\Local\Programs\Python\Python312\pythonw.exe" main.py

exit
