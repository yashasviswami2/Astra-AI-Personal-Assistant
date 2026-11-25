from datetime import datetime, timedelta
from student.database import get_connection


# ==========================================
# STUDENT PROFILE
# ==========================================

def save_student_profile(
    name: str,
    course: str,
    branch: str,
    semester: int,
    university: str = ""
) -> str:
    """Save or update the student's academic profile."""

    if semester < 1:
        return "Please provide a valid semester."

    with get_connection() as conn:

        conn.execute("""
            INSERT INTO student_profile
            (id, name, course, branch, semester, university)
            VALUES (1, ?, ?, ?, ?, ?)

            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                course = excluded.course,
                branch = excluded.branch,
                semester = excluded.semester,
                university = excluded.university
        """, (name, course, branch, semester, university))

    return (
        f"Academic profile saved successfully. "
        f"Name: {name}, Course: {course}, "
        f"Branch: {branch}, Semester: {semester}, "
        f"University: {university}"
    )


def get_student_profile() -> str:
    """Retrieve the student's saved academic profile."""

    with get_connection() as conn:

        profile = conn.execute(
            "SELECT * FROM student_profile WHERE id = 1"
        ).fetchone()

    if not profile:
        return "No student profile has been created yet."

    return (
        f"Name: {profile['name']}\n"
        f"Course: {profile['course']}\n"
        f"Branch: {profile['branch']}\n"
        f"Semester: {profile['semester']}\n"
        f"University: {profile['university']}"
    )


# ==========================================
# SUBJECT MANAGEMENT
# ==========================================

def add_subject(name: str, semester: int) -> str:
    """Register a subject for a particular semester."""

    name = name.strip()

    if not name or semester < 1:
        return "Please provide a valid subject and semester."

    with get_connection() as conn:

        result = conn.execute("""
            INSERT OR IGNORE INTO subjects
            (name, semester)
            VALUES (?, ?)
        """, (name, semester))

        if result.rowcount == 0:
            return f"{name} is already registered."

    return f"{name} added to semester {semester}."


def list_subjects(semester: int = 0) -> str:
    """List saved subjects. Use zero to list all semesters."""

    with get_connection() as conn:

        if semester > 0:

            subjects = conn.execute("""
                SELECT * FROM subjects
                WHERE semester = ?
                ORDER BY name
            """, (semester,)).fetchall()

        else:

            subjects = conn.execute("""
                SELECT * FROM subjects
                ORDER BY semester, name
            """).fetchall()

    if not subjects:
        return "No subjects have been registered."

    return "\n".join(
        f"{s['name']} — Semester {s['semester']}"
        for s in subjects
    )


# ==========================================
# ASSIGNMENT MANAGEMENT
# ==========================================

def add_assignment(
    subject: str,
    title: str,
    deadline: str,
    semester: int
) -> str:
    """
    Save an assignment and its deadline.
    Deadline must use YYYY-MM-DD HH:MM format.
    """

    try:

        deadline = datetime.strptime(
            deadline, "%Y-%m-%d %H:%M"
        ).strftime("%Y-%m-%d %H:%M")

    except ValueError:

        return (
            "Invalid deadline. "
            "Use YYYY-MM-DD HH:MM format."
        )

    if not title.strip():
        return "Please provide an assignment title."

    with get_connection() as conn:

        record = conn.execute("""
            SELECT id FROM subjects
            WHERE name = ? COLLATE NOCASE
            AND semester = ?
        """, (subject.strip(), semester)).fetchone()

        if not record:
            return (
                f"Subject {subject} is not registered "
                f"for semester {semester}."
            )

        existing = conn.execute("""
            SELECT id FROM assignments
            WHERE subject_id = ?
            AND title = ? COLLATE NOCASE
            AND deadline = ?
        """, (
            record["id"], title.strip(), deadline
        )).fetchone()

        if existing:
            return (
                f"Assignment already exists. "
                f"ID: {existing['id']}"
            )

        result = conn.execute("""
            INSERT INTO assignments
            (subject_id, title, deadline)
            VALUES (?, ?, ?)
        """, (
            record["id"],
            title.strip(),
            deadline
        ))

        assignment_id = result.lastrowid

    return (
        f"Assignment saved successfully.\n"
        f"ID: {assignment_id}\n"
        f"Subject: {subject}\n"
        f"Assignment: {title}\n"
        f"Deadline: {deadline}"
    )


def list_assignments(
    status: str = "Pending"
) -> str:
    """
    Retrieve assignments.
    Status can be Pending, Completed or All.
    """

    status = status.strip().capitalize()

    if status not in ("Pending", "Completed", "All"):
        return "Invalid assignment status."

    with get_connection() as conn:

        query = """
            SELECT assignments.*, subjects.name AS subject
            FROM assignments
            JOIN subjects
            ON assignments.subject_id = subjects.id
        """

        if status == "All":

            rows = conn.execute(
                query + " ORDER BY deadline"
            ).fetchall()

        else:

            rows = conn.execute(
                query + """
                    WHERE assignments.status = ?
                    ORDER BY deadline
                """,
                (status,)
            ).fetchall()

    if not rows:
        return f"No {status.lower()} assignments found."

    return "\n".join(

        f"ID: {a['id']} | "
        f"{a['subject']} | "
        f"{a['title']} | "
        f"Due: {a['deadline']} | "
        f"{a['status']}"

        for a in rows
    )


def complete_assignment(assignment_id: int) -> str:
    """Mark an assignment as completed using its ID."""

    with get_connection() as conn:

        result = conn.execute("""
            UPDATE assignments
            SET status = 'Completed'
            WHERE id = ?
        """, (assignment_id,))

        if result.rowcount == 0:
            return "Assignment not found."

    return f"Assignment {assignment_id} marked completed."


# ==========================================
# DEADLINE INTELLIGENCE
# ==========================================

def upcoming_deadlines(days: int = 7) -> str:
    """
    Retrieve overdue and upcoming pending assignments
    within the specified number of days.
    """

    if days < 0:
        return "Please provide a non-negative number of days."

    now = datetime.now()
    end = now + timedelta(days=days)

    with get_connection() as conn:

        rows = conn.execute("""
            SELECT assignments.*, subjects.name AS subject
            FROM assignments
            JOIN subjects
            ON assignments.subject_id = subjects.id
            WHERE assignments.status = 'Pending'
            AND assignments.deadline <= ?
            ORDER BY assignments.deadline
        """, (
            end.strftime("%Y-%m-%d %H:%M"),
        )).fetchall()

    if not rows:
        return "No upcoming or overdue assignments."

    results = []

    for assignment in rows:

        deadline = datetime.strptime(
            assignment["deadline"],
            "%Y-%m-%d %H:%M"
        )

        if deadline < now:
            urgency = "OVERDUE"

        elif deadline - now <= timedelta(hours=24):
            urgency = "URGENT"

        else:
            urgency = "UPCOMING"

        results.append(
            f"{urgency}: {assignment['subject']} — "
            f"{assignment['title']} — "
            f"Due {assignment['deadline']}"
        )

    return "\n".join(results)