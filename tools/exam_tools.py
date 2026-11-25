from datetime import datetime
from student.database import get_connection


def add_exam(
    subject: str,
    exam_date: str,
    semester: int,
    syllabus: str = ""
) -> str:
    """
    Save an examination date and syllabus.
    Date format must be YYYY-MM-DD.
    """

    try:
        exam_date = datetime.strptime(
            exam_date, "%Y-%m-%d"
        ).strftime("%Y-%m-%d")

    except ValueError:
        return "Invalid date. Use YYYY-MM-DD format."

    with get_connection() as conn:

        record = conn.execute("""
            SELECT id FROM subjects
            WHERE name = ? COLLATE NOCASE
            AND semester = ?
        """, (subject.strip(), semester)).fetchone()

        if not record:
            return f"Subject {subject} is not registered."

        existing = conn.execute("""
            SELECT id FROM exams
            WHERE subject_id = ?
            AND exam_date = ?
        """, (record["id"], exam_date)).fetchone()

        if existing:
            conn.execute("""
                UPDATE exams
                SET syllabus = ?
                WHERE id = ?
            """, (syllabus, existing["id"]))

        else:
            conn.execute("""
                INSERT INTO exams
                (subject_id, exam_date, syllabus)
                VALUES (?, ?, ?)
            """, (
                record["id"],
                exam_date,
                syllabus
            ))

    return (
        f"Exam saved successfully.\n"
        f"Subject: {subject}\n"
        f"Date: {exam_date}\n"
        f"Syllabus: {syllabus or 'Not provided'}"
    )


def list_exams() -> str:
    """Retrieve saved examinations and their syllabus."""

    with get_connection() as conn:

        rows = conn.execute("""
            SELECT exams.*, subjects.name AS subject
            FROM exams
            JOIN subjects
            ON exams.subject_id = subjects.id
            ORDER BY exam_date
        """).fetchall()

    if not rows:
        return "No examinations have been registered."

    today = datetime.now().date()

    results = []

    for exam in rows:

        date = datetime.strptime(
            exam["exam_date"], "%Y-%m-%d"
        ).date()

        remaining = (date - today).days

        if remaining < 0:
            status = "Exam date passed"

        elif remaining == 0:
            status = "TODAY"

        else:
            status = f"{remaining} days remaining"

        results.append(
            f"ID: {exam['id']}\n"
            f"Subject: {exam['subject']}\n"
            f"Date: {exam['exam_date']}\n"
            f"Status: {status}\n"
            f"Syllabus: {exam['syllabus'] or 'Not provided'}"
        )

    return "\n\n".join(results)


def get_exam_syllabus(subject: str) -> str:
    """Retrieve the syllabus of upcoming exams for a subject."""

    today = datetime.now().strftime("%Y-%m-%d")

    with get_connection() as conn:

        rows = conn.execute("""
            SELECT exams.*, subjects.name AS subject
            FROM exams
            JOIN subjects
            ON exams.subject_id = subjects.id
            WHERE subjects.name = ? COLLATE NOCASE
            AND exams.exam_date >= ?
            ORDER BY exam_date
        """, (subject.strip(), today)).fetchall()

    if not rows:
        return f"No upcoming exam found for {subject}."

    return "\n\n".join(
        f"Subject: {exam['subject']}\n"
        f"Exam date: {exam['exam_date']}\n"
        f"Syllabus: {exam['syllabus'] or 'Not provided'}"
        for exam in rows
    )


def upcoming_exams(days: int = 7) -> str:
    """Find examinations occurring within the specified days."""

    if days < 0:
        return "Please provide a valid number of days."

    today = datetime.now().date()

    with get_connection() as conn:

        rows = conn.execute("""
            SELECT exams.*, subjects.name AS subject
            FROM exams
            JOIN subjects
            ON exams.subject_id = subjects.id
            ORDER BY exam_date
        """).fetchall()

    results = []

    for exam in rows:

        exam_date = datetime.strptime(
            exam["exam_date"], "%Y-%m-%d"
        ).date()

        remaining = (exam_date - today).days

        if 0 <= remaining <= days:

            results.append(
                f"{exam['subject']} | "
                f"{exam['exam_date']} | "
                f"{remaining} days remaining"
            )

    return (
        "\n".join(results)
        if results
        else "No upcoming examinations in this period."
    )