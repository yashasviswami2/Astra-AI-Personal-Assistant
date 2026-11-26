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

astra = ASTRAAgent()

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
        "gemini_configured": astra.api_configured,
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

        if not astra.api_configured:
            return jsonify({
                "error": "Gemini API is not configured. Check your .env file."
            }), 503

        response = astra.execute_query(message)

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
# =====================================
# ASTRA PERSONAL MEMORY API
# =====================================

from tools.personal_memory import (
    remember_information,
    forget_information
)


@app.route("/api/memory", methods=["GET"])
def api_personal_memory():

    with get_connection() as conn:

        rows = conn.execute("""
            SELECT *
            FROM personal_memory
            ORDER BY category, memory_key
        """).fetchall()

    return jsonify({
        "memories": [dict(row) for row in rows],
        "total": len(rows)
    })


@app.route("/api/memory", methods=["POST"])
def api_save_memory():

    data = request.get_json(silent=True) or {}

    key = data.get("key", "")
    value = data.get("value", "")
    category = data.get("category", "General")

    if not all(isinstance(item, str)
               for item in (key, value, category)):
        return jsonify({"error": "Invalid input."}), 400

    key = key.strip()
    value = value.strip()

    if not key or not value:
        return jsonify({
            "error": "Memory key and value are required."
        }), 400

    if len(key) > 100 or len(value) > 2000:
        return jsonify({
            "error": "Memory entry is too long."
        }), 400

    result = remember_information(key, value, category)

    return jsonify({
        "success": True,
        "message": result
    })


@app.route("/api/memory/<int:memory_id>", methods=["DELETE"])
def api_delete_memory(memory_id):

    with get_connection() as conn:

        cursor = conn.execute("""
            DELETE FROM personal_memory
            WHERE id = ?
        """, (memory_id,))

        deleted = cursor.rowcount

    if deleted == 0:
        return jsonify({
            "error": "Memory not found."
        }), 404

    return jsonify({
        "success": True
    })

# =====================================
# ASTRA STUDY PLANNER API
# =====================================

@app.route("/api/study/sessions", methods=["GET"])
def api_study_sessions():

    study_date = request.args.get(
        "date",
        datetime.now().strftime("%Y-%m-%d")
    )

    try:
        study_date = datetime.strptime(
            study_date, "%Y-%m-%d"
        ).strftime("%Y-%m-%d")

    except ValueError:
        return jsonify({"error": "Invalid date."}), 400

    with get_connection() as conn:

        rows = conn.execute("""
            SELECT ss.*, s.name AS subject
            FROM study_sessions ss
            JOIN subjects s ON ss.subject_id = s.id
            WHERE ss.study_date = ?
            ORDER BY ss.start_time
        """, (study_date,)).fetchall()

    sessions = [dict(row) for row in rows]

    planned = sum(
        s["duration_minutes"] for s in sessions
    )

    completed = sum(
        s["duration_minutes"] for s in sessions
        if s["status"] == "Completed"
    )

    return jsonify({
        "sessions": sessions,
        "stats": {
            "total": len(sessions),
            "completed": sum(
                s["status"] == "Completed"
                for s in sessions
            ),
            "planned_minutes": planned,
            "completed_minutes": completed,
            "progress": round(
                completed / planned * 100
            ) if planned else 0
        }
    })


@app.route(
    "/api/study/session/<int:session_id>/complete",
    methods=["POST"]
)
def api_complete_study_session(session_id):

    with get_connection() as conn:

        cursor = conn.execute("""
            UPDATE study_sessions
            SET status = 'Completed'
            WHERE id = ?
        """, (session_id,))

        updated = cursor.rowcount

    if updated == 0:
        return jsonify({
            "error": "Session not found."
        }), 404

    return jsonify({"success": True})


@app.route(
    "/api/study/session/<int:session_id>",
    methods=["DELETE"]
)
def api_delete_study_session(session_id):

    with get_connection() as conn:

        cursor = conn.execute("""
            DELETE FROM study_sessions
            WHERE id = ?
        """, (session_id,))

        deleted = cursor.rowcount

    if deleted == 0:
        return jsonify({
            "error": "Session not found."
        }), 404

    return jsonify({"success": True})

# =====================================
# ASTRA QUIZ ANALYTICS API
# =====================================

@app.route("/api/quiz/analytics", methods=["GET"])
def api_quiz_analytics():

    with get_connection() as conn:

        results = conn.execute("""
            SELECT q.*, s.name AS subject, s.semester
            FROM quiz_results q
            JOIN subjects s ON q.subject_id = s.id
            ORDER BY q.id DESC
        """).fetchall()

        performance = conn.execute("""
            SELECT
                s.name AS subject,
                s.semester,
                COUNT(q.id) AS quizzes,
                SUM(q.total_questions) AS questions,
                SUM(q.correct_answers) AS correct,
                ROUND(
                    100.0 * SUM(q.correct_answers)
                    / SUM(q.total_questions), 2
                ) AS accuracy
            FROM quiz_results q
            JOIN subjects s ON q.subject_id = s.id
            GROUP BY s.id, s.name, s.semester
            ORDER BY accuracy DESC
        """).fetchall()

        weak_topics = conn.execute("""
            SELECT
                s.name AS subject,
                s.semester,
                q.topic,
                COUNT(q.id) AS attempts,
                ROUND(
                    100.0 * SUM(q.correct_answers)
                    / SUM(q.total_questions), 2
                ) AS accuracy
            FROM quiz_results q
            JOIN subjects s ON q.subject_id = s.id
            GROUP BY s.id, s.name, s.semester,
                     q.topic COLLATE NOCASE
            HAVING
                100.0 * SUM(q.correct_answers)
                / SUM(q.total_questions) < 60
            ORDER BY accuracy ASC
        """).fetchall()

    total_questions = sum(
        row["total_questions"] for row in results
    )

    total_correct = sum(
        row["correct_answers"] for row in results
    )

    accuracy = round(
        total_correct / total_questions * 100, 2
    ) if total_questions else 0

    return jsonify({
        "stats": {
            "total_quizzes": len(results),
            "total_questions": total_questions,
            "correct_answers": total_correct,
            "accuracy": accuracy,
            "weak_topics": len(weak_topics)
        },
        "performance": [dict(row) for row in performance],
        "weak_topics": [dict(row) for row in weak_topics],
        "history": [dict(row) for row in results[:50]]
    })


@app.route("/api/quiz/result/<int:result_id>", methods=["DELETE"])
def api_delete_quiz_result(result_id):

    with get_connection() as conn:

        cursor = conn.execute("""
            DELETE FROM quiz_results
            WHERE id = ?
        """, (result_id,))

        deleted = cursor.rowcount

    if deleted == 0:
        return jsonify({
            "error": "Quiz result not found."
        }), 404

    return jsonify({"success": True})

# =====================================
# ASTRA MULTIMODAL VISION API
# =====================================

from tools.vision_tools import analyze_screen


@app.route("/api/vision/analyze", methods=["POST"])
def api_analyze_screen():

    data = request.get_json(silent=True) or {}

    question = data.get(
        "question",
        "Explain what is currently visible on my screen."
    )

    if not isinstance(question, str):
        return jsonify({
            "error": "Invalid question."
        }), 400

    question = question.strip()

    if not question or len(question) > 3000:
        return jsonify({
            "error": "Enter a valid question."
        }), 400

    result = analyze_screen(question)

    if not isinstance(result, dict):
        return jsonify({
            "error": "Unexpected vision response."
        }), 500

    if not result.get("success"):
        code = result.get("error_code", "VISION_ERROR")

        status = {
            "PERMISSION_DENIED": 403,
            "INVALID_QUESTION": 400,
            "API_KEY_MISSING": 503,
            "IMAGE_TOO_LARGE": 413
        }.get(code, 500)

        return jsonify({
            "success": False,
            "error": result.get("message", "Screen analysis failed."),
            "error_code": code
        }), status

    return jsonify({
        "success": True,
        "response": result["data"]["analysis"]
    })



# ASTRA FLASK SECURITY

app.config["MAX_CONTENT_LENGTH"] = 21 * 1024 * 1024

ASTRA_ALLOWED_HOSTS = {
    "127.0.0.1:5000",
    "localhost:5000"
}

ASTRA_ALLOWED_ORIGINS = {
    "http://127.0.0.1:5000",
    "http://localhost:5000"
}


@app.before_request
def enforce_astra_security():

    if request.remote_addr not in {"127.0.0.1", "::1"}:
        return jsonify({
            "error": "Remote access is not permitted."
        }), 403

    if request.host not in ASTRA_ALLOWED_HOSTS:
        return jsonify({
            "error": "Invalid request host."
        }), 403

    if request.path.startswith("/api/"):

        origin = request.headers.get("Origin")

        if origin and origin not in ASTRA_ALLOWED_ORIGINS:
            return jsonify({
                "error": "Cross-origin access denied."
            }), 403

        if request.headers.get("Sec-Fetch-Site") == "cross-site":
            return jsonify({
                "error": "Cross-site request denied."
            }), 403

        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:

            if origin and origin != request.host_url.rstrip("/"):
                return jsonify({
                    "error": "Request origin mismatch."
                }), 403

            if request.mimetype in {
                "application/x-www-form-urlencoded",
                "text/plain"
            }:
                return jsonify({
                    "error": "Unsupported request format."
                }), 415

            if request.mimetype == "multipart/form-data":
                if request.path != "/api/student/pdf" or not origin:
                    return jsonify({
                        "error": "Unauthorized multipart request."
                    }), 403


@app.after_request
def apply_astra_security_headers(response):

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"

    if request.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"

    return response


@app.errorhandler(413)
def astra_request_too_large(error):
    return jsonify({
        "error": "Request exceeds the permitted size."
    }), 413


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


