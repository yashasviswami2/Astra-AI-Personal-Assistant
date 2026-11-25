import subprocess
import webbrowser
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from tools.student_tools import (
    get_student_profile,
    list_subjects,
    upcoming_deadlines
)

from tools.exam_tools import upcoming_exams
from tools.quiz_tools import identify_weak_topics
from tools.system_tools import get_system_status
from student.reminders import get_reminders


# =====================================
# SAFE DESKTOP ACTIONS
# =====================================

def open_calculator():
    subprocess.Popen(["calc.exe"])
    return "Calculator launch requested."


def open_notepad():
    subprocess.Popen(["notepad.exe"])
    return "Notepad launch requested."


def open_vscode():

    import os

    candidates = [
        Path(os.environ.get("LOCALAPPDATA", ""))
        / "Programs/Microsoft VS Code/Code.exe",

        Path(os.environ.get("ProgramFiles", ""))
        / "Microsoft VS Code/Code.exe"
    ]

    for path in candidates:

        if path.is_file():

            subprocess.Popen([str(path)])

            return "VS Code launch requested."

    raise RuntimeError("VS Code installation not found.")


def open_website(url):

    if not webbrowser.open(url, new=2):
        raise RuntimeError("Browser launch failed.")

    return "Browser launch requested."


# =====================================
# AVAILABLE AUTOMATION ACTIONS
# =====================================

AUTOMATION_ACTIONS = {

    "calculator": open_calculator,

    "notepad": open_notepad,

    "vscode": open_vscode,

    "google": lambda: open_website(
        "https://www.google.com"
    ),

    "github": lambda: open_website(
        "https://github.com"
    ),

    "stackoverflow": lambda: open_website(
        "https://stackoverflow.com"
    ),

    "google_scholar": lambda: open_website(
        "https://scholar.google.com"
    ),

    "wikipedia": lambda: open_website(
        "https://www.wikipedia.org"
    )
}


WORKFLOWS = {

    "study": [
        "calculator",
        "notepad",
        "google_scholar"
    ],

    "coding": [
        "vscode",
        "github",
        "stackoverflow"
    ],

    "research": [
        "google_scholar",
        "wikipedia",
        "google"
    ]
}


# =====================================
# WORKFLOW EXECUTION ENGINE
# =====================================

def execute_actions(actions):

    results = []

    for action in actions:

        try:

            message = AUTOMATION_ACTIONS[action]()

            results.append(
                f"[SUCCESS] {action}: {message}"
            )

        except Exception as error:

            results.append(
                f"[FAILED] {action}: {error}"
            )

    return "\n".join(results)


def start_study_mode() -> str:
    """Open the predefined academic study environment."""

    return (
        "ASTRA Study Mode\n\n"
        + execute_actions(WORKFLOWS["study"])
    )


def start_coding_mode() -> str:
    """Open VS Code and programming reference websites."""

    return (
        "ASTRA Coding Mode\n\n"
        + execute_actions(WORKFLOWS["coding"])
    )


def start_research_mode() -> str:
    """Open predefined academic research websites."""

    return (
        "ASTRA Research Mode\n\n"
        + execute_actions(WORKFLOWS["research"])
    )


def prepare_exam_environment() -> str:
    """Retrieve academic information for exam preparation."""

    return "\n\n".join([

        "ASTRA Exam Preparation Briefing",

        get_student_profile(),

        list_subjects(),

        upcoming_exams(7),

        upcoming_deadlines(7),

        identify_weak_topics()

    ])


def generate_daily_briefing() -> str:
    """Collect academic priorities and system information."""

    tasks = {

        "Student Profile": get_student_profile,

        "Subjects": list_subjects,

        "Deadlines": upcoming_deadlines,

        "Upcoming Exams": upcoming_exams,

        "System Status": get_system_status,

        "Reminders": get_reminders
    }

    sections = ["ASTRA Daily Intelligence Briefing"]

    with ThreadPoolExecutor(max_workers=4) as executor:

        futures = {
            name: executor.submit(function)
            for name, function in tasks.items()
        }

        for name, future in futures.items():

            try:

                result = future.result()

                sections.append(
                    f"\n{name}\n{result}"
                )

            except Exception as error:

                sections.append(
                    f"\n{name}\nUnavailable: {error}"
                )

    return "\n".join(sections)


def execute_custom_workflow(actions: list[str]) -> str:
    """
    Execute user-approved desktop actions.

    Supported actions:
    calculator, notepad, vscode, google,
    github, stackoverflow, google_scholar, wikipedia.
    """

    if not actions:
        return "No workflow actions provided."

    if len(actions) > 8:
        return "Maximum eight actions per workflow."

    actions = [
        action.strip().lower()
        for action in actions
    ]

    invalid = [
        action for action in actions
        if action not in AUTOMATION_ACTIONS
    ]

    if invalid:

        return (
            "Unsupported workflow actions: "
            + ", ".join(invalid)
        )

    return (
        "ASTRA Custom Workflow\n\n"
        + execute_actions(actions)
    )