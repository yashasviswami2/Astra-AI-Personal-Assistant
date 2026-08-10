@echo off
SETLOCAL EnableDelayedExpansion
title Jarvis Setup
cd /d "%~dp0"

echo.
echo  +============================================================+
echo    JARVIS AI ASSISTANT - ONE-TIME SETUP
echo  +============================================================+
echo.

:: ── STEP 1: Find clean Python 3.11 or 3.12 (avoid Anaconda) ────────────────
echo [STEP 1] Finding Python installation...
set "PYTHON_EXE="

:: Prefer standard Python install paths (not Anaconda)
for %%P in (
    "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\python.exe"
    "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\python.exe"
    "C:\Python312\python.exe"
    "C:\Python311\python.exe"
) do (
    if exist %%P (
        :: Make sure it is NOT Anaconda
        %%P -c "import sys; exit(0 if 'anaconda' not in sys.executable.lower() and 'conda' not in sys.executable.lower() else 1)" >nul 2>&1
        if !ERRORLEVEL!==0 (
            set "PYTHON_EXE=%%~P"
            goto :found_python
        )
    )
)

:: Try python on PATH but skip if it is Anaconda
where python >nul 2>&1
if %ERRORLEVEL%==0 (
    for /f "tokens=*" %%i in ('where python') do (
        set "_candidate=%%i"
        echo !_candidate! | findstr /i "anaconda conda" >nul 2>&1
        if !ERRORLEVEL! NEQ 0 (
            set "PYTHON_EXE=!_candidate!"
            goto :found_python
        )
    )
)

echo [ERROR] No clean (non-Anaconda) Python found!
echo.
echo  Please install Python 3.12 from: https://www.python.org/downloads/
echo  During install: check "Add Python to PATH"
echo  Then run this script again.
echo.
pause
exit /b 1

:found_python
echo [OK] Python found: !PYTHON_EXE!
"!PYTHON_EXE!" --version
echo.

:: ── STEP 2: Create virtual environment ─────────────────────────────────────
echo [STEP 2] Creating virtual environment (.venv)...
if exist ".venv\Scripts\python.exe" (
    echo [OK] .venv already exists - skipping creation.
) else (
    "!PYTHON_EXE!" -m venv .venv
    if !ERRORLEVEL! NEQ 0 (
        echo [ERROR] Failed to create .venv
        pause
        exit /b 1
    )
    echo [OK] .venv created.
)
echo.

:: Point all subsequent commands to .venv
set "VENV_PYTHON=%~dp0.venv\Scripts\python.exe"
set "VENV_PIP=%~dp0.venv\Scripts\pip.exe"

:: ── STEP 3: Upgrade pip ─────────────────────────────────────────────────────
echo [STEP 3] Upgrading pip...
"!VENV_PYTHON!" -m pip install --upgrade pip --quiet
echo [OK] pip upgraded.
echo.

:: ── STEP 4: Install all required packages ───────────────────────────────────
echo [STEP 4] Installing required packages...
echo  (This may take 2-5 minutes on first run)
echo.

"!VENV_PYTHON!" -m pip install ^
    "google-generativeai>=0.8.0" ^
    "python-dotenv>=1.0.0" ^
    "SpeechRecognition>=3.10.0" ^
    "pyttsx3>=2.90" ^
    "pystray>=0.19.0" ^
    "Pillow>=10.0.0" ^
    "keyboard>=0.13.5" ^
    "pyautogui>=0.9.54" ^
    "pyperclip>=1.8.2" ^
    "PyPDF2>=3.0.0" ^
    "pypdf>=4.0.0" ^
    "psutil>=5.9.0" ^
    "playwright>=1.40.0"

if !ERRORLEVEL! NEQ 0 (
    echo [ERROR] Some packages failed to install. Check output above.
    pause
    exit /b 1
)
echo.

:: ── STEP 5: Install PyAudio (with fallback) ─────────────────────────────────
echo [STEP 5] Installing PyAudio (microphone support)...
"!VENV_PYTHON!" -m pip install pyaudio --quiet
if !ERRORLEVEL! NEQ 0 (
    echo [WARN] Direct pyaudio install failed. Trying pipwin fallback...
    "!VENV_PYTHON!" -m pip install pipwin --quiet
    "!VENV_PYTHON!" -m pipwin install pyaudio
    if !ERRORLEVEL! NEQ 0 (
        echo [WARN] PyAudio could not be installed automatically.
        echo        Voice input may not work. You can still use Gemini AI text features.
        echo        Manual fix: download wheel from https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
    ) else (
        echo [OK] PyAudio installed via pipwin.
    )
) else (
    echo [OK] PyAudio installed.
)
echo.

:: ── STEP 6: Install Playwright browsers ─────────────────────────────────────
echo [STEP 6] Installing Playwright Chromium browser...
"!VENV_PYTHON!" -m playwright install chromium --quiet
echo [OK] Playwright Chromium installed.
echo.

:: ── STEP 7: Create required folders ─────────────────────────────────────────
echo [STEP 7] Creating project folders...
if not exist "logs"        mkdir logs
if not exist "memory"      mkdir memory
if not exist "screenshots" mkdir screenshots
echo [OK] Folders ready.
echo.

:: ── STEP 8: Check .env and API key ──────────────────────────────────────────
echo [STEP 8] Checking .env configuration...
if not exist ".env" (
    echo [WARN] .env file not found. Creating template...
    (
        echo # =========================================
        echo # Jarvis AI Assistant - Environment Config
        echo # =========================================
        echo.
        echo # Get your free API key at: https://aistudio.google.com/
        echo GEMINI_API_KEY=YOUR_GEMINI_API_KEY_HERE
        echo.
        echo GEMINI_MODEL=gemini-2.5-flash
        echo TTS_RATE=175
        echo TTS_VOLUME=1.0
        echo TTS_VOICE_GENDER=female
    ) > .env
    echo [WARN] .env template created.
    echo        IMPORTANT: Open .env and replace YOUR_GEMINI_API_KEY_HERE with your real key!
) else (
    findstr /i "YOUR_GEMINI_API_KEY_HERE" .env >nul 2>&1
    if !ERRORLEVEL!==0 (
        echo [WARN] .env exists but GEMINI_API_KEY is still set to placeholder!
        echo        Open .env and replace YOUR_GEMINI_API_KEY_HERE with your real key.
    ) else (
        echo [OK] .env file looks configured.
    )
)
echo.

:: ── STEP 9: Run quick package verification ──────────────────────────────────
echo [STEP 9] Verifying installed packages...
"!VENV_PYTHON!" -c "
import importlib.util, sys
pkgs = {
    'google.generativeai': 'google-generativeai',
    'dotenv': 'python-dotenv',
    'speech_recognition': 'SpeechRecognition',
    'pyttsx3': 'pyttsx3',
    'pystray': 'pystray',
    'PIL': 'Pillow',
    'keyboard': 'keyboard',
    'pyautogui': 'pyautogui',
    'pyperclip': 'pyperclip',
    'PyPDF2': 'PyPDF2',
    'psutil': 'psutil',
}
missing = []
for mod, pip in pkgs.items():
    ok = importlib.util.find_spec(mod) is not None
    print(f'  {\"[OK]\" if ok else \"[MISSING]\"} {pip}')
    if not ok:
        missing.append(pip)
if missing:
    print()
    print(f'  Missing: {chr(32).join(missing)}')
    sys.exit(1)
else:
    print()
    print('  All core packages present.')
"
if !ERRORLEVEL! NEQ 0 (
    echo [ERROR] Some packages are missing. Please re-run this script.
    pause
    exit /b 1
)
echo.

:: ── Done ────────────────────────────────────────────────────────────────────
echo  +============================================================+
echo    SETUP COMPLETE!
echo  +============================================================+
echo.
echo  Next steps:
echo    1. If you see a .env warning above, open .env and add your API key.
echo       Get a free key at: https://aistudio.google.com/
echo.
echo    2. Double-click  run_jarvis_console.bat  to start Jarvis with logs.
echo    3. Double-click  run_jarvis_silent.bat   to start silently.
echo.
echo  All logs are saved in: logs\jarvis.log
echo.
pause
ENDLOCAL