"""
test_gemini.py — Standalone Gemini API Test
============================================
Run with:
    python test_gemini.py
"""

import os
import sys
from pathlib import Path

# ─────────────────────────────────────────────────────────────
# 1. Project setup
# ─────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

print("=" * 55)
print("  ASTRA — Gemini API Test")
print("=" * 55)
print()


# ─────────────────────────────────────────────────────────────
# 2. Load .env
# ─────────────────────────────────────────────────────────────

try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")

    print("[OK] python-dotenv loaded")

except ImportError:
    print("[FAIL] python-dotenv is not installed.")
    print("Run:")
    print("    python -m pip install python-dotenv")
    sys.exit(1)


# ─────────────────────────────────────────────────────────────
# 3. Read API key
# ─────────────────────────────────────────────────────────────

api_key = os.getenv("GEMINI_API_KEY", "").strip()

if not api_key or api_key == "YOUR_GEMINI_API_KEY_HERE":
    print("[FAIL] GEMINI_API_KEY is not configured.")
    print()
    print("Open .env and add:")
    print("    GEMINI_API_KEY=YOUR_REAL_KEY")
    sys.exit(1)

masked = api_key[:6] + "..." + api_key[-4:]

print(f"[OK] GEMINI_API_KEY found: {masked}")


# ─────────────────────────────────────────────────────────────
# 4. Read model from .env
# ─────────────────────────────────────────────────────────────

model_name = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.6-flash"
).strip()

print(f"[OK] Model configured: {model_name}")


# ─────────────────────────────────────────────────────────────
# 5. Import new Google GenAI SDK
# ─────────────────────────────────────────────────────────────

try:
    from google import genai

    print("[OK] google-genai imported")

except ImportError:
    print()
    print("[FAIL] google-genai is not installed.")
    print()
    print("Install it with:")
    print("    python -m pip install google-genai")
    sys.exit(1)


# ─────────────────────────────────────────────────────────────
# 6. Create Gemini client
# ─────────────────────────────────────────────────────────────

print()
print(f"Connecting to model: {model_name}")
print("Sending test prompt: 'Say OK in exactly one word'...")
print()

try:

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=model_name,
        contents="Say OK in exactly one word."
    )

    reply = response.text.strip()

    print(f"[SUCCESS] Gemini replied: '{reply}'")
    print()
    print("✅ Gemini API is working correctly!")
    print()
    print("ASTRA's Gemini connection is ready.")

except Exception as e:

    error = str(e)

    print("[FAIL] Gemini API call failed.")
    print()
    print(f"Error: {error}")
    print()

    if "API key" in error or "API_KEY" in error or "401" in error:
        print("→ Check that your Gemini API key is valid.")

    elif "403" in error:
        print("→ Your API key/project may not have access to this API or model.")

    elif "404" in error:
        print(f"→ The model '{model_name}' is not available.")
        print("→ Check the current Gemini model name available to your API key.")

    elif "429" in error:
        print("→ Rate limit or quota reached.")

    elif "connection" in error.lower():
        print("→ Check your internet connection.")

    sys.exit(1)


print("=" * 55)