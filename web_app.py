from flask import Flask, render_template, request, jsonify
from pathlib import Path
import logging
from student.database import get_connection
from datetime import datetime, timedelta

from student.pdf_assistant import analyze_pdf
from io import BytesIO

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

# ==========================================
# ASTRA STUDENT DASHBOARD API
# ==========================================

@app.route("/api/student/dashboard")
def student_dashboard():

    try:

        with get_connection() as conn:

            profile = conn.execute(
                "SELECT * FROM student_profile WHERE id = 1"
            ).fetchone()

            subjects = conn.execute("""
                SELECT * FROM subjects
                ORDER BY semester, name
            """).fetchall()

            assignments = conn.execute("""
                SELECT assignments.*,
                       subjects.name AS subject
                FROM assignments
                JOIN subjects
                ON assignments.subject_id = subjects.id
                ORDER BY deadline
            """).fetchall()

        now = datetime.now()

        assignment_data = []

        for row in assignments:

            item = dict(row)

            deadline = datetime.strptime(
                item["deadline"], "%Y-%m-%d %H:%M"
            )

            if item["status"] == "Completed":
                item["urgency"] = "Completed"

            elif deadline < now:
                item["urgency"] = "Overdue"

            elif deadline - now <= timedelta(hours=24):
                item["urgency"] = "Urgent"

            else:
                item["urgency"] = "Upcoming"

            assignment_data.append(item)

        return jsonify({

            "profile": dict(profile) if profile else None,

            "subjects": [dict(s) for s in subjects],

            "assignments": assignment_data,

            "stats": {

                "subjects": len(subjects),

                "total": len(assignments),

                "pending": sum(
                    a["status"] == "Pending"
                    for a in assignments
                ),

                "completed": sum(
                    a["status"] == "Completed"
                    for a in assignments
                ),

                "overdue": sum(
                    a["urgency"] == "Overdue"
                    for a in assignment_data
                )
            }
        })

    except Exception:

        logger.exception("Student dashboard error")

        return jsonify({
            "error": "Could not load academic data."
        }), 500


@app.route(
    "/api/student/assignment/<int:assignment_id>/complete",
    methods=["POST"]
)
def finish_assignment(assignment_id):

    with get_connection() as conn:

        result = conn.execute("""
            UPDATE assignments
            SET status = 'Completed'
            WHERE id = ?
        """, (assignment_id,))

        if result.rowcount == 0:

            return jsonify({
                "error": "Assignment not found."
            }), 404

    return jsonify({
        "status": "success"
    })

# ASTRA ACADEMIC REMINDERS API

from student.reminders import get_reminders


@app.route("/api/student/reminders")
def academic_reminders():

    return jsonify({
        "reminders": get_reminders()
    })


@app.route("/api/student/exams")
def academic_exams():

    with get_connection() as conn:

        rows = conn.execute("""
            SELECT exams.*, subjects.name AS subject
            FROM exams
            JOIN subjects
            ON exams.subject_id = subjects.id
            ORDER BY exam_date
        """).fetchall()

    return jsonify({
        "exams": [dict(row) for row in rows]
    })

# ASTRA PDF STUDY ASSISTANT

@app.route("/api/student/pdf", methods=["POST"])
def study_pdf():

    try:

        uploaded_file = request.files.get("pdf")

        if not uploaded_file:
            return jsonify({
                "error": "Please upload a PDF file."
            }), 400

        if not uploaded_file.filename.lower().endswith(".pdf"):
            return jsonify({
                "error": "Only PDF files are supported."
            }), 400

        mode = request.form.get("mode", "summary")
        question = request.form.get("question", "").strip()

        if mode == "ask" and not question:
            return jsonify({
                "error": "Please enter your question."
            }), 400

        max_size = 20 * 1024 * 1024

        content = uploaded_file.stream.read(max_size + 1)

        if len(content) > max_size:
            return jsonify({
                "error": "Maximum PDF size is 20 MB."
            }), 400

        if not content.startswith(b"%PDF-"):
            return jsonify({
                "error": "Invalid PDF file."
            }), 400

        result = analyze_pdf(
            BytesIO(content),
            mode,
            question
        )

        return jsonify(result)

    except ValueError as error:

        return jsonify({
            "error": str(error)
        }), 400

    except Exception:

        logger.exception("PDF analysis failed")

        return jsonify({
            "error": "Unable to analyze the PDF. Check the terminal."
        }), 500

    # ASTRA LIVE SYSTEM MONITOR

import psutil
import platform
from pathlib import Path


@app.route("/api/system/status")
def system_status():

    ram = psutil.virtual_memory()
    disk = psutil.disk_usage(Path.home().anchor)
    battery = psutil.sensors_battery()

    return jsonify({
        "cpu": psutil.cpu_percent(interval=0.2),
        "ram": ram.percent,
        "ram_total": round(ram.total / (1024 ** 3), 2),
        "ram_available": round(ram.available / (1024 ** 3), 2),
        "disk": disk.percent,
        "disk_free": round(disk.free / (1024 ** 3), 2),
        "battery": battery.percent if battery else None,
        "charging": battery.power_plugged if battery else None,
        "os": platform.system(),
        "cores": psutil.cpu_count()
    })

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


