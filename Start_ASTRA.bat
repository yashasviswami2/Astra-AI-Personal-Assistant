@echo off

title ASTRA AI Desktop Assistant

cd /d "%~dp0"

echo ==========================================
echo       ASTRA 3.0 AI DESKTOP ASSISTANT
echo ==========================================

if not exist ".venv\Scripts\python.exe" (
    echo Python virtual environment not found.
    pause
    exit /b 1
)

echo Starting background notification service...

start "ASTRA Notifications" /min ".venv\Scripts\python.exe" -m student.notification_service

echo Starting ASTRA web server...

start "ASTRA Server" /min ".venv\Scripts\python.exe" web_app.py

timeout /t 4 /nobreak >nul

echo Opening ASTRA Dashboard...

start "" "http://127.0.0.1:5000"

exit