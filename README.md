# ASTRA — AI Personal Assistant

### Advanced Smart Task and Reasoning Assistant

ASTRA is a Python-based intelligent desktop assistant designed
for academic productivity, personal assistance, system monitoring
and controlled desktop automation.

## Project Version

ASTRA 3.0 — University Project Edition

## Key Features

- Gemini-powered conversational intelligence
- Agentic tool execution
- Desktop automation
- Voice recognition and speech synthesis
- Student academic workspace
- Assignment and examination management
- PDF study assistant
- Intelligent study planner
- Quiz performance analytics
- Personal memory management
- Multimodal screen analysis
- System resource monitoring
- Productivity and focus tools
- Academic notifications
- Customizable dashboard
- Permission-based security architecture
- Structured security audit logging

## Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| Backend | Flask |
| Frontend | HTML, CSS, JavaScript |
| AI Engine | Google Gemini |
| Database | SQLite |
| Desktop Automation | PyAutoGUI |
| Speech Recognition | SpeechRecognition |
| Speech Synthesis | pyttsx3 |
| PDF Processing | pypdf |
| System Monitoring | psutil |
| Testing | Python unittest |
| Version Control | Git and GitHub |

## Installation

Clone the repository:

    git clone https://github.com/yashasviswami2/Astra-AI-Personal-Assistant.git

Create a Python virtual environment:

    python -m venv .venv

Activate the environment on Windows:

    .\.venv\Scripts\Activate.ps1

Install dependencies:

    python -m pip install -r requirements.txt

Configure your Gemini API key in a local .env file.

Never commit API keys or private configuration files.

## Running ASTRA

    python web_app.py

Open:

    http://127.0.0.1:5000

## Security Architecture

ASTRA includes a permission-based security design with:

- Tool permission classification
- Native Windows authorization dialogs
- Restricted filesystem access
- Protected file filtering
- Screenshot authorization
- Clipboard authorization
- Localhost API restrictions
- Structured security audit records

These controls are intended for a local desktop application.
They do not constitute a production-grade security sandbox.

## Testing

Run the automated test suite:

    python -m unittest discover -s tests -v

Validate installed dependencies:

    python -m pip check

## Current Limitations

- Primarily designed for Windows
- Internet connectivity required for Gemini functionality
- AI responses may contain inaccuracies
- Screen analysis transmits authorized images to Gemini
- Local database and audit logs are not encrypted
- Some desktop operations require manual authorization

## Future Scope

- Offline language model integration
- Cross-platform compatibility
- Advanced contextual memory
- Encrypted personal data storage
- Mobile companion application
- Improved autonomous task planning

## Academic Project

Bachelor of Technology — Computer Science and Engineering

School of Engineering and Technology

Mody University of Science and Technology

Academic Session: 2026-2027

## Project Team

- Yashasvi — 240115
- Yashika — 240116
- Tanishka — 240108

## Project Status

University project release candidate.
Final release is subject to successful integration testing.

