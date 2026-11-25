from datetime import datetime, timedelta
from student.database import get_connection


def add_study_session(
    subject: str,
    semester: int,
    topic: str,
    study_date: str,
    start_time: str,
    duration_minutes: int = 60,
    priority: str = "Medium"
) -> str:
    """Schedule a study session. Date: YYYY-MM-DD. Time: HH:MM."""

    try:
        start = datetime.strptime(
            f"{study_date} {start_time}",
            "%Y-%m-%d %H:%M"
        )
    except ValueError:
        return "Use date YYYY-MM-DD and time HH:MM."

    study_date = start.strftime("%Y-%m-%d")
    start_time = start.strftime("%H:%M")
    priority = priority.strip().title()
    topic = topic.strip()

    if not topic:
        return "Please provide a study topic."

    if priority not in ("Low", "Medium", "High"):
        return "Priority must be Low, Medium or High."

    if not 1 <= duration_minutes <= 480:
        return "Duration must be between 1 and 480 minutes."

    end = start + timedelta(minutes=duration_minutes)

    if end.date() != start.date():
        return "Study sessions cannot extend past midnight."

    with get_connection() as conn:

        conn.execute("BEGIN IMMEDIATE")

        row = conn.execute("""
            SELECT id, name FROM subjects
            WHERE name = ? COLLATE NOCASE
            AND semester = ?
        """, (subject.strip(), semester)).fetchone()

        if row is None:
            return "Subject not registered for this semester."

        existing = conn.execute("""
            SELECT start_time, duration_minutes
            FROM study_sessions
            WHERE study_date = ?
        """, (study_date,)).fetchall()

        for session in existing:

            old_start = datetime.strptime(
                f"{study_date} {session['start_time']}",
                "%Y-%m-%d %H:%M"
            )

            old_end = old_start + timedelta(
                minutes=session["duration_minutes"]
            )

            if start < old_end and end > old_start:
                return "This session overlaps an existing study session."

        cursor = conn.execute("""
            INSERT INTO study_sessions (
                subject_id,
                topic,
                study_date,
                start_time,
                duration_minutes,
                priority
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            row["id"],
            topic,
            study_date,
            start_time,
            duration_minutes,
            priority
        ))

        session_id = cursor.lastrowid

    return (
        f"Study session scheduled successfully.\n"
        f"Session ID: {session_id}\n"
        f"Subject: {row['name']}\n"
        f"Topic: {topic}\n"
        f"Date: {study_date}\n"
        f"Time: {start_time}\n"
        f"Duration: {duration_minutes} minutes\n"
        f"Priority: {priority}"
    )


def list_study_sessions(study_date: str = "") -> str:
    """Retrieve study sessions for a date or all scheduled sessions."""

    query = """
        SELECT ss.*, s.name AS subject
        FROM study_sessions ss
        JOIN subjects s ON ss.subject_id = s.id
    """

    params = ()

    if study_date:
        try:
            study_date = datetime.strptime(
                study_date, "%Y-%m-%d"
            ).strftime("%Y-%m-%d")
        except ValueError:
            return "Use date format YYYY-MM-DD."

        query += " WHERE ss.study_date = ?"
        params = (study_date,)

    query += " ORDER BY ss.study_date, ss.start_time"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()

    if not rows:
        return "No study sessions scheduled."

    result = ["ASTRA Study Timetable:"]

    for row in rows:

        result.append(
            f"ID: {row['id']} | "
            f"{row['study_date']} | "
            f"{row['start_time']} | "
            f"{row['subject']} | "
            f"{row['topic']} | "
            f"{row['duration_minutes']} minutes | "
            f"{row['priority']} | "
            f"{row['status']}"
        )

    return "\n".join(result)


def complete_study_session(session_id: int) -> str:
    """Mark a scheduled study session as completed."""

    with get_connection() as conn:

        cursor = conn.execute("""
            UPDATE study_sessions
            SET status = 'Completed'
            WHERE id = ?
        """, (session_id,))

        updated = cursor.rowcount

    if updated == 0:
        return "Study session not found."

    return f"Study session {session_id} marked as completed."


def delete_study_session(session_id: int) -> str:
    """Delete a study session explicitly requested by the user."""

    with get_connection() as conn:

        cursor = conn.execute("""
            DELETE FROM study_sessions
            WHERE id = ?
        """, (session_id,))

        deleted = cursor.rowcount

    if deleted == 0:
        return "Study session not found."

    return f"Study session {session_id} deleted successfully."


def get_study_progress(study_date: str = "") -> str:
    """Calculate planned and completed study time for a date."""

    study_date = study_date or datetime.now().strftime("%Y-%m-%d")

    try:
        study_date = datetime.strptime(
            study_date, "%Y-%m-%d"
        ).strftime("%Y-%m-%d")
    except ValueError:
        return "Use date format YYYY-MM-DD."

    with get_connection() as conn:

        row = conn.execute("""
            SELECT
                COUNT(*) AS total_sessions,
                COALESCE(SUM(duration_minutes), 0)
                    AS planned_minutes,
                COALESCE(SUM(
                    CASE WHEN status = 'Completed'
                    THEN duration_minutes ELSE 0 END
                ), 0) AS completed_minutes,
                COALESCE(SUM(
                    CASE WHEN status = 'Completed'
                    THEN 1 ELSE 0 END
                ), 0) AS completed_sessions
            FROM study_sessions
            WHERE study_date = ?
        """, (study_date,)).fetchone()

    planned = row["planned_minutes"]
    completed = row["completed_minutes"]

    progress = round(completed / planned * 100) if planned else 0

    return (
        f"Study Progress: {study_date}\n"
        f"Total sessions: {row['total_sessions']}\n"
        f"Completed sessions: {row['completed_sessions']}\n"
        f"Planned study time: {planned} minutes\n"
        f"Completed session time: {completed} minutes\n"
        f"Progress: {progress}%"
    )