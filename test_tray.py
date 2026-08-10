"""
test_tray.py — Standalone System Tray Icon Test
================================================
Run with:  python test_tray.py
This will display a test icon in the system tray for 15 seconds.
Look for it near the WiFi/battery icons (or in the ^ hidden area).
"""

import sys
import time
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

print("=" * 55)
print("  JARVIS — System Tray Icon Test")
print("=" * 55)
print()

# ── 1. Import pystray ─────────────────────────────────────────
try:
    import pystray
    print("[OK] pystray imported")
except ImportError:
    print("[FAIL] pystray not installed.")
    print("  → Run: pip install pystray")
    sys.exit(1)

# ── 2. Import Pillow ──────────────────────────────────────────
try:
    from PIL import Image, ImageDraw
    print("[OK] Pillow (PIL) imported")
except ImportError:
    print("[FAIL] Pillow not installed.")
    print("  → Run: pip install pillow")
    sys.exit(1)

# ── 3. Create a test icon ─────────────────────────────────────
def make_icon(color, size=64):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, 60, 60], outline=(200, 200, 200, 255), width=4)
    draw.ellipse([12, 12, 52, 52], fill=color)
    draw.line([25, 32, 39, 32], fill=(255, 255, 255, 220), width=3)
    draw.line([32, 25, 32, 39], fill=(255, 255, 255, 220), width=3)
    return img

print()
print("[OK] Test icon created (green = active)")
print()
print("=" * 55)
print("  ▶ LOOK FOR THE ICON near WiFi/battery icons!")
print("  ▶ If not visible, click the '^' arrow on taskbar.")
print("  ▶ Icon will auto-close after 15 seconds.")
print("     OR right-click the icon → 'Exit Test'")
print("=" * 55)
print()

# ── 4. Create pystray icon ────────────────────────────────────
test_icon_ref = [None]
exit_event = threading.Event()

def do_exit(icon, item):
    print("[OK] Exit clicked — stopping test icon.")
    icon.stop()
    exit_event.set()

def auto_close():
    """Auto-stop after 15 seconds."""
    time.sleep(15)
    if test_icon_ref[0] and not exit_event.is_set():
        print("[OK] 15-second timer elapsed — stopping test icon.")
        test_icon_ref[0].stop()
        exit_event.set()

try:
    img = make_icon((46, 204, 113, 255))  # bright green
    icon = pystray.Icon(
        name="JarvisTest",
        icon=img,
        title="Jarvis Test Icon ✓ — Right-click → Exit Test",
        menu=pystray.Menu(
            pystray.MenuItem("✅  Jarvis Tray Test — WORKING!", lambda *_: None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("❌  Exit Test", do_exit),
        )
    )
    test_icon_ref[0] = icon

    # Start auto-close timer
    t = threading.Thread(target=auto_close, daemon=True)
    t.start()

    print("Tray icon is starting...")
    icon.run()  # blocks until icon.stop()

    print()
    print("✅ Tray icon test PASSED!")
    print("  If you saw the icon, pystray is working correctly on your system.")

except Exception as e:
    print(f"[FAIL] Tray icon test failed: {e}")
    print()
    print("  Possible fixes:")
    print("  1. Make sure pystray is installed:  pip install pystray pillow")
    print("  2. Try running as Administrator")
    print("  3. Check Windows notification area is not fully disabled in Settings")
    sys.exit(1)

print()
input("Press ENTER to exit...")
