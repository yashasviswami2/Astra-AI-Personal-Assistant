import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# API Settings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
# Standard model for lightweight speed and tool use
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

# System Tray App Settings
APP_NAME = "ASTRA Assistant"
GLOBAL_HOTKEY = "ctrl+alt+a"  # Hotkey to trigger listening

# Voice Settings
TTS_RATE = int(os.getenv("TTS_RATE", 175))      # Words per minute
TTS_VOLUME = float(os.getenv("TTS_VOLUME", 1.0)) # 0.0 to 1.0
TTS_VOICE_GENDER = os.getenv("TTS_VOICE_GENDER", "female") # male/female

# Speech Recognition Settings
STT_LANGUAGE = "en-IN"
STT_ENERGY_THRESHOLD = 150
STT_DYNAMIC_ENERGY_THRESHOLD = False
STT_PAUSE_THRESHOLD = 0.8
STT_NON_SPEAKING_DURATION = 0.4
STT_AMBIENT_NOISE_DURATION = 2.0
STT_TIMEOUT = 15
STT_PHRASE_LIMIT = 10
MICROPHONE_INDEX = 1

# Paths
SCREENSHOT_DIR = BASE_DIR / "screenshots"
MEMORY_DIR = BASE_DIR / "memory"
LOG_DIR = BASE_DIR / "logs"

# Ensure directories exist
for directory in [SCREENSHOT_DIR, MEMORY_DIR, LOG_DIR]:
    directory.mkdir(exist_ok=True, parents=True)

# Safety Settings
SAFE_EXECUTION_MODE = True # Require confirmation for system modifications
RESTRICTED_COMMANDS = [
    "shutdown", "restart", "format", "rmdir /s", "del /f", "rm -rf", "mkfs"
]
ALLOWED_APP_LAUNCHES = {
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "notepad": "notepad.exe",
    "calc": "calc.exe",
    "vs code": "code",
    "cmd": "cmd.exe",
    "powershell": "powershell.exe"
}
