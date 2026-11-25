"""
test_mic.py — Standalone Microphone Test
=========================================
Run with:  python test_mic.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

print("=" * 55)
print("  ASTRA — Microphone Test")
print("=" * 55)
print()

# ── 1. Import SpeechRecognition ───────────────────────────────
try:
    import speech_recognition as sr
    print("[OK] SpeechRecognition imported")
except ImportError:
    print("[FAIL] SpeechRecognition not installed.")
    print("  → Run: pip install SpeechRecognition")
    sys.exit(1)

# ── 2. Check PyAudio (required for mic input) ─────────────────
try:
    import pyaudio
    print("[OK] PyAudio imported")
except ImportError:
    print("[WARN] PyAudio not installed — microphone input will fail.")
    print("  → Run: pip install pyaudio")
    print("  → If that fails on Windows, try: pip install pipwin && pipwin install pyaudio")
    print()

# ── 3. List available microphones ────────────────────────────
print()
print("Listing available microphones...")
try:
    mics = sr.Microphone.list_microphone_names()
    if not mics:
        print("[FAIL] No microphones found!")
        print("  → Connect a microphone or headset and try again.")
        print("  → Check Windows Settings → Privacy → Microphone (allow apps to use mic).")
        sys.exit(1)

    print(f"[OK] {len(mics)} microphone(s) found:")
    for i, name in enumerate(mics):
        print(f"  [{i}] {name}")
except Exception as e:
    print(f"[FAIL] Could not list microphones: {e}")
    sys.exit(1)

# ── 4. Load config settings if available ─────────────────────
print()
mic_index = None
try:
    from config import settings
    mic_index = settings.MICROPHONE_INDEX
    print(f"[OK] Loaded config settings. MICROPHONE_INDEX = {mic_index}")
except Exception:
    print("[WARN] Could not load config settings; using default microphone.")

# ── 5. Open selected microphone ─────────────────────────────
print()
if mic_index is None:
    print("Opening default microphone...")
else:
    print(f"Opening microphone index {mic_index}...")

try:
    with sr.Microphone(device_index=mic_index) as source:
        r = sr.Recognizer()
        r.energy_threshold = getattr(settings, 'STT_ENERGY_THRESHOLD', 300)
        r.dynamic_energy_threshold = getattr(settings, 'STT_DYNAMIC_ENERGY_THRESHOLD', True)
        r.pause_threshold = getattr(settings, 'STT_PAUSE_THRESHOLD', 0.7)
        print("[OK] Microphone opened. Calibrating ambient noise...")
        r.adjust_for_ambient_noise(source, duration=2)
        print(f"[OK] Energy threshold set to: {r.energy_threshold:.1f}")
        print()
        print("🎤 Speak now! (10 second window)...")
        try:
            audio = r.listen(source, timeout=10, phrase_time_limit=10)
            print("[OK] Audio captured — sending to Google Speech Recognition...")
            text = r.recognize_google(audio, language="en-US")
            print(f"[SUCCESS] You said: '{text}'")
            print()
            print("✅ Microphone is working correctly!")
        except sr.WaitTimeoutError:
            print("[INFO] No speech detected in 10 seconds — timeout.")
            print("  The microphone hardware is likely OK if you did not speak.")
        except sr.UnknownValueError:
            print("[INFO] Audio captured but not understood — mic hardware is OK.")
        except sr.RequestError as e:
            print(f"[FAIL] Google Speech API error: {e}")
            print("  → Check your internet connection.")
except OSError as e:
    print(f"[FAIL] Could not open microphone: {e}")
    print("  → Run as Administrator, or check Windows Privacy settings → Microphone.")
    sys.exit(1)
except Exception as e:
    print(f"[FAIL] Unexpected microphone error: {e}")
    sys.exit(1)

print()
input("Press ENTER to exit...")
