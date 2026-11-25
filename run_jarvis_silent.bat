@echo off
SETLOCAL EnableDelayedExpansion
cd /d "%~dp0"

:: ── Use .venv if it exists ───────────────────────────────────────────────────
set "PYTHON_EXE="

if exist ".venv\Scripts\pythonw.exe" (
    set "PYTHON_EXE=%~dp0.venv\Scripts\pythonw.exe"
    goto :launch
)

:: Fallback: find clean pythonw (skip Anaconda)
for %%P in (
    "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\pythonw.exe"
    "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\pythonw.exe"
    "C:\Python312\pythonw.exe"
    "C:\Python311\pythonw.exe"
) do (
    if exist %%P (
        set "PYTHON_EXE=%%~P"
        goto :launch
    )
)

:: Last resort - use python.exe (brief window flash)
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
    goto :launch
)

:: Try any pythonw.exe available on PATH
for /f "delims=" %%P in ('where pythonw.exe 2^>nul') do (
    set "PYTHON_EXE=%%~P"
    goto :launch
)

echo Python not found. Please run setup_ASTRA.bat first.
pause
exit /b 1

:launch
if /I "%PYTHON_EXE:~-10%"=="pythonw.exe" (
    start "" /B "!PYTHON_EXE!" main.py
) else (
    start "" /MIN "!PYTHON_EXE!" main.py
)
ENDLOCAL
