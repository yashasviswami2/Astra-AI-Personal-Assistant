@echo off
SETLOCAL EnableDelayedExpansion
title Jarvis AI Assistant - Console Mode
cd /d "%~dp0"

echo.
echo  +============================================================+
echo    JARVIS AI ASSISTANT - CONSOLE DEBUG MODE
echo  +============================================================+
echo    Logs and errors are shown below.
echo    Keep this window open while Jarvis is running.
echo  +============================================================+
echo.

:: ── Use .venv if it exists (preferred) ──────────────────────────────────────
set "PYTHON_EXE="

if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
    echo [OK] Using virtual environment: .venv
    goto :run
)

:: ── Fallback: find clean Python (skip Anaconda) ─────────────────────────────
echo [WARN] .venv not found. Run setup_jarvis.bat first for best results.
echo        Falling back to system Python...
echo.

for %%P in (
    "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\python.exe"
    "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\python.exe"
    "C:\Python312\python.exe"
    "C:\Python311\python.exe"
) do (
    if exist %%P (
        %%P -c "import sys; exit(0 if 'anaconda' not in sys.executable.lower() else 1)" >nul 2>&1
        if !ERRORLEVEL!==0 (
            set "PYTHON_EXE=%%~P"
            goto :run
        )
    )
)

echo [ERROR] No working Python found and .venv is missing.
echo.
echo  Please run setup_jarvis.bat first!
echo.
pause
exit /b 1

:run
echo  Python: !PYTHON_EXE!
echo  Starting Jarvis...
echo  ------------------------------------------------------------
echo.

"!PYTHON_EXE!" main.py

echo.
echo  ------------------------------------------------------------
echo  Jarvis has stopped.
echo  ------------------------------------------------------------
echo.
echo  If you see an error above:
echo    1. Run setup_jarvis.bat to reinstall dependencies
echo    2. Make sure .env has a valid GEMINI_API_KEY
echo    3. Check logs\jarvis.log for full details
echo    4. Run as Administrator for hotkey support
echo.
pause
ENDLOCAL
