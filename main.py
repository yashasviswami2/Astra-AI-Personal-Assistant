"""
ASTRA Windows AI Assistant — Main Entry Point
=============================================
Handles step-by-step initialization with detailed console/file logging.
Every phase prints its status so silent failures are eliminated.
"""

import os
import sys
import time
import logging
from pathlib import Path

from config import settings

# ──────────────────────────────────────────────
# STEP 0 ─ Ensure working directory is project root
# ──────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent
os.chdir(PROJECT_ROOT)

# ──────────────────────────────────────────────
# ANACONDA GUARD — detect broken environment early
# ──────────────────────────────────────────────
_exe = sys.executable.lower()
if "anaconda" in _exe or "conda" in _exe:
    print()
    print("=" * 60)
    print("  ERROR: Running inside Anaconda Python (broken environment)")
    print("=" * 60)
    print(f"  Detected: {sys.executable}")
    print()
    print("  This Anaconda install is missing '_socket' and cannot run.")
    print()
    print("  FIX — Use ONE of these options:")
    print()
    print("  Option A (Recommended):")
    print("    Double-click  setup_ASTRA.bat")
    print("    Then double-click  run_ASTRA_console.bat")
    print()
    print("  Option B (from terminal):")
    print(r"    .venv\Scripts\python.exe main.py")
    print()
    print("  Option C (from terminal):")
    venv_python = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
    if venv_python.exists():
        print(f"    {venv_python} main.py")
    else:
        print(r"    C:\Users\acer\AppData\Local\Programs\Python\Python312\python.exe main.py")
    print()
    print("=" * 60)
    input("Press ENTER to exit...")
    sys.exit(1)


# ──────────────────────────────────────────────
# STEP 1 ─ Bootstrap early logger (before any imports that might fail)
# ──────────────────────────────────────────────
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True, parents=True)
LOG_FILE = LOG_DIR / "ASTRA.log"

# Configure the root logger so every module shares it
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),           # console
        logging.FileHandler(LOG_FILE, encoding="utf-8")  # file
    ]
)
logger = logging.getLogger("ASTRA.Main")

BANNER = """
+==================================================+
|        ASTRA WINDOWS AI ASSISTANT v2.0          |
|        Powered by Google Gemini                  |
+==================================================+
"""

def step(n: int, title: str) -> None:
    """Print a visible step header to make startup progress easy to track."""
    bar = "-" * 50
    logger.info(f"\n{bar}\n  STEP {n}: {title}\n{bar}")


# ──────────────────────────────────────────────
# STEP 2 ─ Dependency Verification
# ──────────────────────────────────────────────
REQUIRED_PACKAGES = {
    "google.generativeai":  "google-generativeai",
    "dotenv":               "python-dotenv",
    "speech_recognition":   "SpeechRecognition",
    "pyttsx3":              "pyttsx3",
    "pystray":              "pystray",
    "PIL":                  "Pillow",
    "keyboard":             "keyboard",
    "pyautogui":            "pyautogui",
    "pyperclip":            "pyperclip",
    "PyPDF2":               "PyPDF2",
    "psutil":               "psutil",
}

def verify_dependencies() -> bool:
    """Check all required Python packages. Returns True only if all are present."""
    step(2, "Checking Required Packages")
    import importlib.util

    missing = []
    for module, pip_name in REQUIRED_PACKAGES.items():
        spec = importlib.util.find_spec(module)
        if spec is None:
            logger.error(f"  [MISSING] {pip_name}  (import name: {module})")
            missing.append(pip_name)
        else:
            logger.info(f"  [OK]      {pip_name}")

    if missing:
        logger.critical("\n" + "=" * 50)
        logger.critical("  MISSING PACKAGES -- run this command to fix:")
        logger.critical(f"  pip install {' '.join(missing)}")
        logger.critical("=" * 50)
        return False

    logger.info("  All required packages are present.")
    return True


# ──────────────────────────────────────────────
# STEP 3 ─ Environment / .env Loading
# ──────────────────────────────────────────────
def load_environment() -> bool:
    """Load .env and validate GEMINI_API_KEY. Returns True if key is present."""
    step(3, "Loading Environment Variables (.env)")

    env_file = PROJECT_ROOT / ".env"

    # Create template if missing
    if not env_file.exists():
        logger.warning("  .env file not found. Creating template...")
        try:
            env_file.write_text(
                "# ========================================\n"
                "# ASTRA AI Assistant — Environment Config\n"
                "# ========================================\n\n"
                "# Get your key at https://aistudio.google.com/\n"
                "GEMINI_API_KEY=YOUR_GEMINI_API_KEY_HERE\n\n"
                "GEMINI_MODEL=gemini-2.5-flash\n\n"
                "TTS_RATE=175\n"
                "TTS_VOLUME=1.0\n"
                "TTS_VOICE_GENDER=female\n",
                encoding="utf-8"
            )
            logger.info(f"  Template .env created at: {env_file}")
        except Exception as e:
            logger.error(f"  Could not create .env template: {e}")
    else:
        logger.info(f"  .env file found: {env_file}")

    from dotenv import load_dotenv
    load_dotenv(dotenv_path=env_file, override=True)
    logger.info("  dotenv loaded successfully.")

    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key or api_key == "YOUR_GEMINI_API_KEY_HERE":
        logger.critical(
            "  [FAIL] GEMINI_API_KEY is not set!\n"
            "  Open the .env file and paste your real API key.\n"
            "  Get one free at: https://aistudio.google.com/"
        )
        return False

    masked = api_key[:6] + "..." + api_key[-4:]
    logger.info(f"  [OK] GEMINI_API_KEY loaded: {masked}")
    return True


# ──────────────────────────────────────────────
# STEP 4 ─ Gemini API Connection Test
# ──────────────────────────────────────────────
def test_gemini_connection() -> bool:
    """Try a lightweight Gemini call to confirm the key and internet work."""
    step(4, "Testing Gemini API Connection")
    try:
        import google.generativeai as genai
        api_key = os.getenv("GEMINI_API_KEY", "")
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        genai.configure(api_key=api_key)

        model = genai.GenerativeModel(model_name)
        resp = model.generate_content("Say 'OK' in one word.", 
                                       generation_config={"max_output_tokens": 5})
        reply = resp.text.strip()
        logger.info(f"  [OK] Gemini connection OK - model replied: '{reply}'")
        return True

    except Exception as e:
        err = str(e)
        if "API_KEY_INVALID" in err or "400" in err:
            logger.error("  [FAIL] API key is invalid. Check your GEMINI_API_KEY in .env")
        elif "quota" in err.lower():
            logger.error("  [FAIL] API quota exceeded. Check your Google AI Studio quota.")
        elif "ConnectionError" in err or "Failed to connect" in err:
            logger.error("  [FAIL] No internet connection detected.")
        else:
            logger.error(f"  [FAIL] Gemini test failed: {e}")
        return False


# ──────────────────────────────────────────────
# STEP 5 ─ Microphone Check
# ──────────────────────────────────────────────
def check_microphone() -> bool:
    """Detect available microphone devices. Warns but does NOT block startup."""
    step(5, "Checking Microphone Availability")
    try:
        import speech_recognition as sr
        mics = sr.Microphone.list_microphone_names()
        if not mics:
            logger.warning("  [WARN] No microphone devices found.")
            logger.warning("  Voice input will be disabled. Connect a microphone and restart.")
            return False

        logger.info(f"  [OK] {len(mics)} microphone(s) detected:")
        for i, name in enumerate(mics[:10]):
            logger.info(f"    [{i}] {name}")

        device_index = settings.MICROPHONE_INDEX
        if device_index is not None:
            logger.info(f"  [INFO] Configured microphone index: {device_index}")

        # Quick open-and-close test
        try:
            with sr.Microphone(device_index=device_index) as source:
                logger.info("  [OK] Microphone opened successfully.")
        except OSError as oe:
            logger.warning(f"  [WARN] Could not open configured/default mic: {oe}")
            logger.warning("  Try running as Administrator or check mic privacy settings.")
            return False

        return True

    except Exception as e:
        logger.warning(f"  [WARN] Microphone check error: {e}")
        return False


# ──────────────────────────────────────────────
# STEP 6 ─ Hotkey Registration Test
# ──────────────────────────────────────────────
def test_hotkey_registration() -> bool:
    """Validate that the keyboard library can register hooks."""
    step(6, "Testing Hotkey Registration (Ctrl+Alt+A)")
    try:
        import keyboard
        # Try adding a test hotkey and immediately removing it
        h = keyboard.add_hotkey("ctrl+alt+a", lambda: None)
        keyboard.remove_hotkey(h)
        logger.info("  [OK] keyboard library hotkey registration works.")
        return True
    except Exception as e:
        logger.warning(f"  [WARN] Hotkey registration failed: {e}")
        logger.warning("  Tip: Try running as Administrator for global hotkeys.")
        logger.warning("  The tray icon will still appear -- use the tray menu to start listening.")
        return False


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────
def main():
    print(BANNER)
    logger.info(f"Python: {sys.executable} — version {sys.version}")
    logger.info(f"Project root: {PROJECT_ROOT}")
    logger.info(f"Log file: {LOG_FILE}")

    # ── Dependency check (hard stop if packages missing)
    if not verify_dependencies():
        logger.critical("Startup aborted: missing packages. Install them then restart.")
        input("\nPress ENTER to exit...")
        sys.exit(1)

    # ── Environment loading (hard stop if no API key)
    env_ok = load_environment()

    # ── Gemini test (soft warning only — don't block if offline)
    if env_ok:
        gemini_ok = test_gemini_connection()
        if not gemini_ok:
            logger.warning("  Gemini test failed — assistant will start but AI responses may not work.")
    else:
        logger.warning("  Skipping Gemini test (no valid API key).")

    # ── Microphone check (soft warning — assistant still runs)
    mic_ok = check_microphone()
    if not mic_ok:
        logger.warning("  Microphone unavailable — voice input disabled for this session.")

    # ── Hotkey test (soft warning — tray still works without hotkeys)
    test_hotkey_registration()

    # ── Launch tray application
    step(7, "Starting System Tray Application")
    logger.info("  Launching ASTRATrayApp — look for the icon near WiFi/battery icons.")
    logger.info("  NOTE: Windows may hide new icons in the ^ hidden tray. Drag it to the taskbar!")

    try:
        from tray_app import ASTRATrayApp
        app = ASTRATrayApp()
        app.run()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received. Shutting down...")
    except Exception as e:
        logger.critical(f"Fatal error in tray application: {e}", exc_info=True)
        input("\nFatal error — check logs/ASTRA.log for details.\nPress ENTER to exit...")
        sys.exit(1)


if __name__ == "__main__":
    main()
