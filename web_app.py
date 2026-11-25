from flask import Flask, render_template, request, jsonify
from pathlib import Path
import logging

from agent import ASTRAAgent
from voice.stt import stt_manager
from voice.tts import tts_manager

# ==========================================
# CONFIGURATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = Flask(
    __name__,
    template_folder=str(FRONTEND_DIR),
    static_folder=str(FRONTEND_DIR),
    static_url_path="/static"
)

jarvis = ASTRAAgent()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==========================================
# HOME PAGE
# ==========================================

@app.route("/")
def home():
    return render_template("index.html")


# ==========================================
# BACKEND HEALTH CHECK
# ==========================================

@app.route("/api/health")
def health():

    return jsonify({
        "status": "online",
        "gemini_configured": jarvis.api_configured,
        "voice_enabled": True
    })


# ==========================================
# AI CHAT
# ==========================================

@app.route("/api/chat", methods=["POST"])
def chat():

    try:

        data = request.get_json(silent=True) or {}
        message = data.get("message", "").strip()

        if not message:
            return jsonify({
                "error": "Please enter a message."
            }), 400

        if not jarvis.api_configured:
            return jsonify({
                "error": "Gemini API is not configured. Check your .env file."
            }), 503

        response = jarvis.execute_query(message)

        return jsonify({
            "response": response
        })

    except Exception:

        logger.exception("Chat endpoint error")

        return jsonify({
            "error": "Something went wrong while processing your message."
        }), 500


# ==========================================
# SPEECH TO TEXT
# ==========================================

@app.route("/api/listen", methods=["POST"])
def listen():

    try:

        logger.info("ASTRA: Microphone activated.")

        transcript = stt_manager.listen()

        if transcript is None:

            return jsonify({
                "transcript": "",
                "message": "Listening timed out or speech recognition failed."
            })

        if not transcript:

            return jsonify({
                "transcript": "",
                "message": "Speech could not be understood."
            })

        logger.info(f"ASTRA recognized: {transcript}")

        return jsonify({
            "transcript": transcript
        })

    except Exception:

        logger.exception("Speech recognition endpoint error")

        return jsonify({
            "error": "Could not access the microphone."
        }), 500


# ==========================================
# TEXT TO SPEECH
# ==========================================

@app.route("/api/speak", methods=["POST"])
def speak():

    try:

        data = request.get_json(silent=True) or {}
        text = data.get("text", "").strip()

        if not text:
            return jsonify({
                "error": "No text provided."
            }), 400

        # Use existing TTS manager.
        # Non-blocking so Flask can respond immediately.
        tts_manager.speak(text, block=False)

        return jsonify({
            "status": "speaking",
            "message": "ASTRA is speaking."
        })

    except Exception:

        logger.exception("Text-to-speech endpoint error")

        return jsonify({
            "error": "Could not start text-to-speech."
        }), 500


# ==========================================
# RUN ASTRA
# ==========================================

if __name__ == "__main__":

    print("\n===================================")
    print("       ASTRA AI ASSISTANT")
    print("===================================")
    print("Backend: ONLINE")
    print("Voice: ENABLED")
    print("Open: http://127.0.0.1:5000")
    print("===================================\n")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        threaded=True
    )
