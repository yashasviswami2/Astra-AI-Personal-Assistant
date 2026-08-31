from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
from pathlib import Path

# Add the JARVIS backend folder to Python's path
JARVIS_PATH = Path(__file__).resolve().parent.parent / "jarvis_backend"
sys.path.insert(0, str(JARVIS_PATH))

from agent import JarvisAgent

app = Flask(__name__)
CORS(app)

# Create JARVIS agent once when the server starts
jarvis = JarvisAgent()


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "online",
        "message": "JARVIS backend is running"
    })


@app.route("/ask", methods=["POST"])
def ask_jarvis():
    try:
        data = request.get_json()

        query = data.get("query", "").strip()

        if not query:
            return jsonify({
                "success": False,
                "response": "Please provide a question."
            }), 400

        print(f"User: {query}")

        response = jarvis.execute_query(query)

        print(f"JARVIS: {response}")

        return jsonify({
            "success": True,
            "response": response
        })

    except Exception as e:
        print(f"Error: {e}")

        return jsonify({
            "success": False,
            "response": "Sorry, I encountered an error.",
            "error": str(e)
        }), 500


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )