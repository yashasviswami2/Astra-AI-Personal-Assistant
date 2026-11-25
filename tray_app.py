"""
ASTRA Tray Application
=======================
Full-featured pystray-based system tray app with:
 - Color-coded status icon (idle/listening/processing/sleep)
 - Ctrl+Alt+A global hotkey (with graceful fallback)
 - Expanded tray menu including test utilities
 - Robust multithreading — tray loop never dies silently
"""

import os
import sys
import time
import threading
import webbrowser
import subprocess
import logging
from pathlib import Path

# pystray / Pillow
import pystray
from PIL import Image, ImageDraw, ImageFont

# Project modules
from config import settings
from utils.logger import get_logger
from agent import ASTRAAgent
from memory.conversation import memory

logger = get_logger()

# ── Optional modules (may be absent — handled gracefully) ──────────────────
try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False
    logger.warning("keyboard module not installed — hotkeys disabled.")

try:
    from voice.stt import stt_manager
    STT_AVAILABLE = True
except Exception as e:
    STT_AVAILABLE = False
    stt_manager = None
    logger.warning(f"Speech-to-text unavailable: {e}")

try:
    from voice.tts import tts_manager
    TTS_AVAILABLE = True
except Exception as e:
    TTS_AVAILABLE = False
    tts_manager = None
    logger.warning(f"Text-to-speech unavailable: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Icon generation
# ─────────────────────────────────────────────────────────────────────────────

# State → (fill_color, ring_color)
STATE_COLORS = {
    "idle":       ((70,  130, 180, 255), (120, 180, 220, 200)),   # steel blue
    "listening":  ((46,  204, 113, 255), ( 80, 240, 140, 200)),   # bright green
    "processing": ((241, 196,  15, 255), (255, 220,  50, 200)),   # amber
    "sleep":      ((100, 100, 110, 255), (150, 150, 160, 200)),   # grey
    "error":      ((231,  76,  60, 255), (255, 120, 100, 200)),   # red
}

def create_state_icon(state: str) -> Image.Image:
    """Create a 64×64 RGBA icon for the given state string."""
    fill, ring = STATE_COLORS.get(state, STATE_COLORS["idle"])
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Outer glow ring
    draw.ellipse([2, 2, 62, 62], outline=ring, width=5)
    # Filled circle
    draw.ellipse([10, 10, 54, 54], fill=fill)
    # White cross (generic "J" mark feel)
    cx, cy = 32, 32
    arm = 10
    draw.line([cx - arm, cy, cx + arm, cy], fill=(255, 255, 255, 200), width=3)
    draw.line([cx, cy - arm, cx, cy + arm], fill=(255, 255, 255, 200), width=3)

    return img


# ─────────────────────────────────────────────────────────────────────────────
# Main Tray Application class
# ─────────────────────────────────────────────────────────────────────────────

class ASTRATrayApp:
    def __init__(self):
        self.state = "idle"
        self.icon = None
        self.running = True
        self.cancel_requested = False
        self.work_thread: threading.Thread | None = None
        self.hotkey_hook = None

        logger.info("ASTRATrayApp initializing agent...")
        try:
            self.agent = ASTRAAgent()
        except Exception as e:
            logger.error(f"Agent init failed: {e}")
            self.agent = None

    # ── Menu ────────────────────────────────────────────────────────────────

    def create_menu(self) -> pystray.Menu:
        return pystray.Menu(
            pystray.MenuItem(
                "▶  Start Listening",
                self.start_listening,
                enabled=lambda _: self.state == "idle" and STT_AVAILABLE,
            ),
            pystray.MenuItem(
                "⏹  Stop Listening",
                self.stop_listening,
                enabled=lambda _: self.state == "listening",
            ),
            pystray.MenuItem(
                "💤  Sleep Mode",
                self.toggle_sleep,
                checked=lambda _: self.state == "sleep",
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("🎤  Test Microphone",  self._menu_test_mic),
            pystray.MenuItem("🤖  Test Gemini API",  self._menu_test_gemini),
            pystray.MenuItem("📁  Open Logs Folder", self._menu_open_logs),
            pystray.MenuItem("🗑  Clear Memory",     self.clear_memory),
            pystray.MenuItem("📊  Open Dashboard",   self.open_dashboard),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("❌  Exit Completely",  self.exit_app),
        )

    # ── State management ────────────────────────────────────────────────────

    def set_state(self, new_state: str) -> None:
        self.state = new_state
        if self.icon:
            try:
                self.icon.icon = create_state_icon(new_state)
                self.icon.title = f"{settings.APP_NAME} — {new_state.capitalize()}"
            except Exception as e:
                logger.debug(f"Icon update error (non-fatal): {e}")
        logger.info(f"[STATE] → {new_state.upper()}")

    # ── Run ─────────────────────────────────────────────────────────────────

    def run(self) -> None:
        """Start pystray. Blocks the calling thread until exit."""
        logger.info("Building tray icon...")
        initial_img = create_state_icon("idle")

        self.icon = pystray.Icon(
            name="ASTRAAssistant",
            icon=initial_img,
            title=f"{settings.APP_NAME} — Idle",
            menu=self.create_menu(),
        )

        # Register hotkey in a background thread so pystray.run() isn't blocked
        threading.Thread(target=self._register_hotkeys_safe, daemon=True).start()

        # Generate dashboard HTML
        try:
            self.generate_dashboard_html()
        except Exception as e:
            logger.warning(f"Dashboard generation failed (non-fatal): {e}")

        # Greet user
        self._speak("ASTRA is ready. Right-click the tray icon or press Ctrl Alt A.", block=False)

        logger.info("Tray icon running — right-click it near the WiFi/battery icons.")
        logger.info("If icon is hidden, click the '^' arrow on the taskbar to find it.")

        # pystray.run() blocks here until icon.stop() is called
        self.icon.run()

    # ── Hotkey ──────────────────────────────────────────────────────────────

    def _register_hotkeys_safe(self) -> None:
        """Register global hotkey in a daemon thread — failures are non-fatal."""
        if not KEYBOARD_AVAILABLE:
            logger.warning("keyboard not available; hotkeys skipped.")
            return

        time.sleep(1)  # Let pystray settle first
        try:
            self.hotkey_hook = keyboard.add_hotkey(
                settings.GLOBAL_HOTKEY, self.on_hotkey_pressed
            )
            logger.info(f"Hotkey '{settings.GLOBAL_HOTKEY}' registered OK.")
        except Exception as e:
            logger.warning(
                f"Hotkey registration failed: {e}\n"
                "  → Use the tray 'Start Listening' menu item instead.\n"
                "  → Try running as Administrator if hotkeys are required."
            )

    def on_hotkey_pressed(self) -> None:
        if self.state == "idle":
            logger.info("Hotkey pressed → starting listen cycle.")
            self.start_listening()
        elif self.state == "listening":
            logger.info("Hotkey pressed → stopping listen.")
            self.stop_listening()
        elif self.state == "sleep":
            logger.info("Hotkey pressed but ASTRA is sleeping — wake via tray menu.")
        else:
            logger.info(f"Hotkey pressed but state is '{self.state}' — ignored.")

    # ── Listening ───────────────────────────────────────────────────────────

    def start_listening(self, icon=None, item=None) -> None:
        if self.state != "idle":
            logger.info(f"Start-listen ignored (current state: {self.state}).")
            return
        if not STT_AVAILABLE:
            logger.warning("Cannot listen — speech recognition unavailable.")
            self._speak("Microphone is not available.", block=False)
            return

        self.cancel_requested = False
        self.set_state("listening")
        self._play_listen_beep()
        self.work_thread = threading.Thread(
            target=self._listen_and_process_loop, daemon=True
        )
        self.work_thread.start()

    def _listen_and_process_loop(self) -> None:
        try:
            while not self.cancel_requested:
                text = stt_manager.listen()

                if self.cancel_requested:
                    logger.info("Processing cancelled by user.")
                    break

                if text is None:
                    logger.info("No speech detected; continuing to listen.")
                    continue

                text = text.strip().lower()
                logger.info(f"User said: '{text}'")

                if not text:
                    logger.info("Audio unclear; asking user to repeat.")
                    self._speak("Please repeat.", block=True)
                    continue

                if self._is_stop_command(text):
                    logger.info(f"Stop command received: '{text}'")
                    self._speak("Stopping listening.", block=True)
                    self.cancel_requested = True
                    break

                self.set_state("processing")
                response = self._process_command(text)

                if self.cancel_requested:
                    logger.info("Response cancelled before speaking.")
                    break

                self._speak(response, block=True)
                self.set_state("listening")

        except Exception as e:
            logger.error(f"Listen/process loop error: {e}", exc_info=True)
            self._speak("I ran into an internal error.", block=False)
        finally:
            if self.state not in ("sleep", "idle"):
                self.set_state("idle")

    def stop_listening(self, icon=None, item=None) -> None:
        logger.info("Stop listening requested.")
        self.cancel_requested = True
        self.set_state("idle")

    # ── Sleep ────────────────────────────────────────────────────────────────

    def toggle_sleep(self, icon=None, item=None) -> None:
        if self.state == "sleep":
            self.set_state("idle")
            self._speak("ASTRA is awake.", block=False)
        else:
            self.stop_listening()
            self.set_state("sleep")
            self._speak("Entering sleep mode.", block=False)

    # ── Menu actions ─────────────────────────────────────────────────────────

    def clear_memory(self, icon=None, item=None) -> None:
        memory.clear()
        logger.info("Conversation memory cleared.")
        self._speak("Memory cleared.", block=False)

    def open_dashboard(self, icon=None, item=None) -> None:
        dashboard_path = settings.BASE_DIR / "dashboard.html"
        logger.info(f"Opening dashboard: {dashboard_path}")
        webbrowser.open(dashboard_path.as_uri())

    def _menu_open_logs(self, icon=None, item=None) -> None:
        log_dir = str(settings.LOG_DIR)
        logger.info(f"Opening logs folder: {log_dir}")
        subprocess.Popen(["explorer", log_dir], shell=False)

    def _menu_test_mic(self, icon=None, item=None) -> None:
        """Run mic test in background thread so tray stays responsive."""
        threading.Thread(target=self._run_test_mic, daemon=True).start()

    def _is_stop_command(self, text: str) -> bool:
        stop_phrases = [
            "stop listening",
            "exit",
            "shutdown assistant",
        ]
        return any(phrase in text for phrase in stop_phrases)

    def _process_command(self, text: str) -> str:
        """Handle local command shortcuts before falling back to the Gemini agent."""
        if text == "open chrome":
            self._speak("Opening Chrome.", block=False)
            try:
                subprocess.Popen(["cmd", "/c", "start", "chrome"], shell=False)
                return "Opened Chrome."
            except Exception as e:
                logger.error(f"Failed to open Chrome: {e}")
                return "I couldn't open Chrome."

        if text == "open youtube":
            webbrowser.open("https://www.youtube.com")
            return "Opening YouTube."

        if text.startswith("search "):
            query = text[len("search "):].strip()
            if query:
                webbrowser.open(f"https://www.google.com/search?q={query.replace(' ', '+')}")
                return f"Searching Google for {query}."

        if text == "play music":
            webbrowser.open("https://music.youtube.com")
            return "Playing music."

        if text == "stop music":
            if KEYBOARD_AVAILABLE:
                try:
                    keyboard.send("play/pause media")
                    return "Toggling music playback."
                except Exception as e:
                    logger.error(f"Failed to send media key: {e}")
            return "I couldn't stop music from here."

        if text == "what time is it":
            return time.strftime("It is %I:%M %p.")

        if text == "shutdown computer":
            try:
                subprocess.Popen(["shutdown", "/s", "/t", "10"], shell=False)
                return "Shutting down the computer in 10 seconds."
            except Exception as e:
                logger.error(f"Shutdown command failed: {e}")
                return "I couldn't shut down the computer."

        if self.agent:
            return self.agent.execute_query(text)

        return "The AI agent is not available. Please check your API key."

    def _run_test_mic(self) -> None:
        logger.info("[TEST] Testing microphone...")
        if not STT_AVAILABLE:
            logger.error("[TEST] SpeechRecognition not available.")
            self._speak("Microphone test failed — speech recognition not installed.", block=False)
            return
        try:
            import speech_recognition as sr
            from config import settings as cfg

            mics = sr.Microphone.list_microphone_names()
            logger.info(f"[TEST] {len(mics)} microphone(s) found:")
            for idx, name in enumerate(mics):
                logger.info(f"  [{idx}] {name}")

            device_index = cfg.MICROPHONE_INDEX
            if device_index is not None:
                selected = (
                    f"{device_index}: {mics[device_index]}"
                    if 0 <= device_index < len(mics)
                    else "INVALID INDEX"
                )
            else:
                selected = "default device"
            logger.info(f"[TEST] Using microphone: {selected}")

            with sr.Microphone(device_index=device_index) as source:
                r = sr.Recognizer()
                r.energy_threshold = cfg.STT_ENERGY_THRESHOLD
                r.dynamic_energy_threshold = cfg.STT_DYNAMIC_ENERGY_THRESHOLD
                r.pause_threshold = cfg.STT_PAUSE_THRESHOLD
                logger.info("[TEST] Microphone opened. Calibrating ambient noise...")
                r.adjust_for_ambient_noise(source, duration=cfg.STT_AMBIENT_NOISE_DURATION)
                logger.info("[TEST] Noise calibration complete.")

            self._speak(f"Microphone test passed. {len(mics)} device(s) found.", block=False)
        except Exception as e:
            logger.error(f"[TEST] Microphone test failed: {e}")
            self._speak("Microphone test failed. Check logs for details.", block=False)

    def _menu_test_gemini(self, icon=None, item=None) -> None:
        threading.Thread(target=self._run_test_gemini, daemon=True).start()

    def _run_test_gemini(self) -> None:
        logger.info("[TEST] Testing Gemini API...")
        if not self.agent or not self.agent.api_configured:
            logger.error("[TEST] Agent not configured.")
            self._speak("Gemini test failed — API key may be missing.", block=False)
            return
        try:
            response = self.agent.execute_query("Say the word OK in exactly one word.")
            logger.info(f"[TEST] Gemini replied: {response}")
            self._speak(f"Gemini test passed. Reply: {response}", block=False)
        except Exception as e:
            logger.error(f"[TEST] Gemini test error: {e}")
            self._speak("Gemini test failed. Check logs for details.", block=False)

    # ── Exit ─────────────────────────────────────────────────────────────────

    def exit_app(self, icon=None, item=None) -> None:
        logger.info("Exit requested by user.")
        self.running = False
        self.cancel_requested = True

        # Remove hotkeys
        if KEYBOARD_AVAILABLE and self.hotkey_hook:
            try:
                keyboard.unhook_all()
                logger.info("Hotkeys unregistered.")
            except Exception:
                pass

        self._speak("Shutting down. Goodbye.", block=True)

        # Stop pystray loop
        if self.icon:
            self.icon.stop()

    # ── TTS helper ───────────────────────────────────────────────────────────

    def _play_listen_beep(self) -> None:
        try:
            import winsound
            winsound.Beep(750, 120)
        except Exception:
            pass

    def _speak(self, text: str, block: bool = True) -> None:
        """Safe TTS wrapper — does nothing if TTS unavailable."""
        if TTS_AVAILABLE and tts_manager:
            try:
                tts_manager.speak(text, block=block)
            except Exception as e:
                logger.debug(f"TTS error (non-fatal): {e}")
        else:
            logger.info(f"[TTS disabled] Would say: {text}")

    # ── Dashboard HTML generation ─────────────────────────────────────────

    def generate_dashboard_html(self) -> None:
        dashboard_path = settings.BASE_DIR / "dashboard.html"
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ASTRA AI Assistant — Dashboard</title>
    <style>
        :root {{
            --bg: #0d1117; --surface: #161b22; --card: #21262d;
            --border: #30363d; --accent: #58a6ff; --text: #c9d1d9;
            --muted: #8b949e; --green: #3fb950; --red: #f85149;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: var(--bg); color: var(--text); padding: 40px 20px; }}
        .container {{ max-width: 860px; margin: auto; }}
        h1 {{ font-size: 2rem; color: var(--accent); margin-bottom: 4px; }}
        .subtitle {{ color: var(--muted); margin-bottom: 30px; font-size: .9rem; }}
        .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px; }}
        .card {{ background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 20px; }}
        .card h3 {{ color: var(--accent); font-size: 1rem; margin-bottom: 12px; }}
        .card p {{ font-size: .88rem; line-height: 1.7; color: var(--muted); }}
        .badge {{ display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: .78rem; font-weight: 600; }}
        .badge-blue {{ background: #1f6feb; color: #fff; }}
        .badge-green {{ background: #1a4731; color: var(--green); }}
        code {{ background: #111; padding: 2px 6px; border-radius: 4px; color: #ff7b72; font-size: .85rem; }}
        a {{ color: var(--accent); text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .full {{ grid-column: 1 / -1; }}
        .tip {{ background: #1c2128; border-left: 3px solid var(--accent); padding: 10px 14px; border-radius: 0 6px 6px 0; font-size: .85rem; color: var(--muted); margin-top: 8px; }}
    </style>
</head>
<body>
<div class="container">
    <h1>🤖 ASTRA AI Assistant</h1>
    <p class="subtitle">Windows System Tray Assistant — Powered by Google Gemini</p>
    <div class="grid">
        <div class="card">
            <h3>Status</h3>
            <p>App Status: <span class="badge badge-green">● Running</span></p>
            <p style="margin-top:8px">Hotkey: <span class="badge badge-blue">{settings.GLOBAL_HOTKEY}</span></p>
        </div>
        <div class="card">
            <h3>AI Model</h3>
            <p>Model: <code>{settings.GEMINI_MODEL}</code></p>
            <p style="margin-top:8px">TTS Rate: <code>{settings.TTS_RATE} wpm</code></p>
        </div>
        <div class="card">
            <h3>Quick Links</h3>
            <p><a href="file:///{settings.LOG_DIR.resolve()}">📁 Open Logs Folder</a></p>
            <p><a href="file:///{settings.MEMORY_DIR.resolve()}">🧠 Open Memory Folder</a></p>
            <p><a href="file:///{settings.SCREENSHOT_DIR.resolve()}">📸 Open Screenshots</a></p>
        </div>
        <div class="card">
            <h3>Tray Menu Actions</h3>
            <p>▶ Start Listening<br>⏹ Stop Listening<br>💤 Sleep Mode<br>🎤 Test Microphone<br>🤖 Test Gemini<br>❌ Exit</p>
        </div>
        <div class="card full">
            <h3>Troubleshooting Tips</h3>
            <div class="tip">🔹 <strong>Icon not visible?</strong> Click the <code>^</code> arrow on the taskbar and drag ASTRA to the visible area.</div>
            <div class="tip">🔹 <strong>Hotkey not working?</strong> Run <code>run_ASTRA_console.bat</code> as Administrator.</div>
            <div class="tip">🔹 <strong>No voice output?</strong> Check Windows Sound settings → Output device.</div>
            <div class="tip">🔹 <strong>API errors?</strong> Open <code>.env</code> and verify your <code>GEMINI_API_KEY</code>.</div>
        </div>
    </div>
    <p style="text-align:center;color:var(--muted);font-size:.8rem;margin-top:20px">ASTRA Assistant &copy; 2026 — <a href="https://aistudio.google.com/">Get Gemini API Key</a></p>
</div>
</body>
</html>"""
        dashboard_path.write_text(html, encoding="utf-8")
        logger.debug(f"Dashboard written to {dashboard_path}")
