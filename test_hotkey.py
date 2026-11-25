"""
test_hotkey.py — Standalone Hotkey Registration Test
=====================================================
Run with:  python test_hotkey.py
For best results, run as Administrator.
"""

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

print("=" * 55)
print("  ASTRA — Hotkey Registration Test")
print("=" * 55)
print()

# ── 1. Import keyboard ────────────────────────────────────────
try:
    import keyboard
    print("[OK] keyboard module imported")
except ImportError:
    print("[FAIL] keyboard not installed.")
    print("  → Run: pip install keyboard")
    sys.exit(1)

# ── 2. Try registering Ctrl+Alt+A ─────────────────────────────
print()
print("Registering hotkey: Ctrl + Alt + A ...")

pressed = [False]

def on_hotkey():
    pressed[0] = True
    print("[SUCCESS] ✅ Ctrl+Alt+A hotkey detected!")

try:
    hook = keyboard.add_hotkey("ctrl+alt+a", on_hotkey)
    print("[OK] Hotkey registered successfully.")
    print()
    print("⌨️  Press Ctrl + Alt + A now (you have 10 seconds)...")

    start = time.time()
    while time.time() - start < 10:
        if pressed[0]:
            break
        time.sleep(0.1)

    keyboard.remove_hotkey(hook)

    if not pressed[0]:
        print("[INFO] Hotkey was not pressed within 10 seconds.")
        print("  The hotkey registration itself succeeded — the library is working.")
        print("  Try pressing Ctrl+Alt+A next time ASTRA is running.")
    else:
        print()
        print("✅ Hotkeys are fully working on this system!")

except Exception as e:
    print(f"[FAIL] Could not register hotkey: {e}")
    print()
    print("  Possible fixes:")
    print("  1. Run this script as Administrator (right-click → 'Run as administrator')")
    print("  2. Check if another app is using Ctrl+Alt+A")
    print("  3. Some antivirus software blocks keyboard hooks — add Python as exception")
    print()
    print("  ASTRA will still work via the tray right-click menu even without hotkeys.")
    sys.exit(1)

print()
input("Press ENTER to exit...")
