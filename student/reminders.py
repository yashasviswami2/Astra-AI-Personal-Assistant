from datetime import datetime, timedelta
from student.database import get_connection


def get_reminders():
    """Retrieve urgent academic reminders."""

    now = datetime.now()
    tomorrow = now + timedelta(hours=24)
    exam_limit = now.date() + timedelta(days=3)

    reminders = []

    with get_connection() as conn:

        assignments = conn.execute("""
            SELECT assignments.*, subjects.name AS subject
            FROM assignments
            JOIN subjects
            ON assignments.subject_id = subjects.id
            WHERE assignments.status = 'Pending'
            AND assignments.deadline <= ?
            ORDER BY deadline
        """, (
            tomorrow.strftime("%Y-%m-%d %H:%M"),
        )).fetchall()

        exams = conn.execute("""
            SELECT exams.*, subjects.name AS subject
            FROM exams
            JOIN subjects
            ON exams.subject_id = subjects.id
            WHERE exam_date BETWEEN ? AND ?
            ORDER BY exam_date
        """, (
            now.date().isoformat(),
            exam_limit.isoformat()
        )).fetchall()

    for assignment in assignments:

        deadline = datetime.strptime(
            assignment["deadline"],
            "%Y-%m-%d %H:%M"
        )

        overdue = deadline < now

        reminders.append({
            "id": f"assignment-{assignment['id']}",
            "type": "assignment",
            "priority": "Overdue" if overdue else "Urgent",
            "title": assignment["title"],
            "subject": assignment["subject"],
            "deadline": assignment["deadline"],
            "message": (
                f"Your {assignment['subject']} assignment "
                f"{'is overdue' if overdue else 'is due within 24 hours'}."
            )
        })

    for exam in exams:

        date = datetime.strptime(
            exam["exam_date"], "%Y-%m-%d"
        ).date()

        remaining = (date - now.date()).days

        reminders.append({
            "id": f"exam-{exam['id']}",
            "type": "exam",
            "priority": "Exam",
            "title": f"{exam['subject']} Examination",
            "subject": exam["subject"],
            "deadline": exam["exam_date"],
            "message": (
                f"Your {exam['subject']} exam is today."
                if remaining == 0
                else f"Your {exam['subject']} exam is in "
                     f"{remaining} day(s)."
            )
        })

    return reminders


def check_academic_reminders() -> str:
    """Check urgent assignments and upcoming examination reminders."""

    reminders = get_reminders()

    if not reminders:
        return "You have no urgent academic reminders."

    return "\n".join(
        f"{item['priority']}: {item['message']}"
        for item in reminders
    )