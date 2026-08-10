"""
test_gemini.py — Standalone Gemini API Test
============================================
Run with:  python test_gemini.py
"""

import os
import sys
from pathlib import Path

# Ensure project root is on path
ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

print("=" * 55)
print("  JARVIS — Gemini API Test")
print("=" * 55)
print()

# ── 1. Load .env ──────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=ROOT / ".env")
    print("[OK] python-dotenv loaded")
except ImportError:
    print("[FAIL] python-dotenv not installed.  Run: pip install python-dotenv")
    sys.exit(1)

# ── 2. Check API key ──────────────────────────────────────────
api_key = os.getenv("GEMINI_API_KEY", "")
if not api_key or api_key == "YOUR_GEMINI_API_KEY_HERE":
    print("[FAIL] GEMINI_API_KEY not set in .env")
    print("  → Open .env and paste your real API key.")
    sys.exit(1)

masked = api_key[:6] + "..." + api_key[-4:]
print(f"[OK] GEMINI_API_KEY found: {masked}")

# ── 3. Import google-generativeai ─────────────────────────────
try:
    import google.generativeai as genai
    print("[OK] google-generativeai imported")
except ImportError:
    print("[FAIL] google-generativeai not installed.  Run: pip install google-generativeai")
    sys.exit(1)

# ── 4. Configure and test ─────────────────────────────────────
model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
print(f"\nConnecting to model: {model_name}")
print("Sending test prompt: 'Say OK in exactly one word'...")
print()

try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)
    response = model.generate_content(
        "Say OK in exactly one word.",
        generation_config={"max_output_tokens": 10}
    )
    reply = response.text.strip()
    print(f"[SUCCESS] Gemini replied: '{reply}'")
    print()
    print("✅ Gemini API is working correctly!")
except Exception as e:
    err = str(e)
    print(f"[FAIL] Gemini call failed: {e}")
    if "API_KEY_INVALID" in err or "400" in err:
        print("  → Your API key is invalid. Get a new one at https://aistudio.google.com/")
    elif "quota" in err.lower():
        print("  → API quota exceeded. Check usage at https://aistudio.google.com/")
    elif "ConnectionError" in err or "Failed to connect" in err or "Name or service" in err:
        print("  → No internet. Check your connection.")
    elif "404" in err:
        print(f"  → Model '{model_name}' not found. Try 'gemini-2.5-flash' in .env")
    sys.exit(1)

print()
input("Press ENTER to exit...")
