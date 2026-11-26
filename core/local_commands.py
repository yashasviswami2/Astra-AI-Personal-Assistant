
import re
import subprocess
import os
from datetime import datetime
from pathlib import Path

import psutil
from security.confirmation import request_user_confirmation


def launch_local_app(app_name):

    windows = Path(os.environ.get("SystemRoot", r"C:\Windows"))
    program_files = Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
    local_appdata = Path(os.environ.get("LOCALAPPDATA", ""))

    applications = {
        "calculator": [
            windows / "System32" / "calc.exe"
        ],
        "notepad": [
            windows / "System32" / "notepad.exe"
        ],
        "file explorer": [
            windows / "explorer.exe"
        ],
        "google chrome": [
            program_files / "Google/Chrome/Application/chrome.exe",
            Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
            local_appdata / "Google/Chrome/Application/chrome.exe"
        ],
        "vs code": [
            local_appdata / "Programs/Microsoft VS Code/Code.exe",
            program_files / "Microsoft VS Code/Code.exe"
        ]
    }

    if app_name not in applications:
        return None

    executable = next(
        (p for p in applications[app_name] if p.is_file()),
        None
    )

    if executable is None:
        return f"I could not locate {app_name} on this computer."

    try:
        approved = request_user_confirmation(
            "launch_app",
            {"app_name": app_name, "path": str(executable)}
        )

        if approved is not True:
            return "Application launch cancelled."

        subprocess.Popen([str(executable)], shell=False)

        return f"Launched {app_name}."

    except Exception:
        return f"I could not open {app_name}."


def execute_local_command(query):

    if not isinstance(query, str):
        return None

    command = query.lower().strip()

    command = re.sub(
        r"^(?:(?:hey|hello|hi)\s+)?astra\b[\s,]*",
        "",
        command
    ).strip(" .!?")

    if command in {
        "what is the current time",
        "what time is it",
        "tell me the time",
        "current time"
    }:
        return datetime.now().strftime(
            "The current time is %I:%M %p."
        )

    if command in {
        "what is today's date",
        "tell me the date",
        "current date",
        "what is the date today"
    }:
        return datetime.now().strftime(
            "Today is %A, %d %B %Y."
        )

    if command in {
        "battery percentage",
        "battery status",
        "what is my battery percentage",
        "how much battery is left"
    }:
        battery = psutil.sensors_battery()

        if battery is None:
            return "Battery information is unavailable."

        return f"Your battery is at {battery.percent:.0f} percent."

    if command in {
        "cpu usage",
        "check cpu usage",
        "what is my cpu usage"
    }:
        return f"CPU usage is {psutil.cpu_percent(interval=0.5)} percent."

    if command in {
        "ram usage",
        "check ram usage",
        "memory usage"
    }:
        return f"RAM usage is {psutil.virtual_memory().percent} percent."

    if command in {
        "system status",
        "check system status"
    }:
        cpu = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory().percent

        return f"CPU usage is {cpu} percent. RAM usage is {ram} percent."

    aliases = {
        "open chrome": "google chrome",
        "open google chrome": "google chrome",
        "launch chrome": "google chrome",
        "open calculator": "calculator",
        "launch calculator": "calculator",
        "open notepad": "notepad",
        "open file explorer": "file explorer",
        "open explorer": "file explorer",
        "open vs code": "vs code",
        "open visual studio code": "vs code"
    }

    if command in aliases:
        return launch_local_app(aliases[command])

    return None
