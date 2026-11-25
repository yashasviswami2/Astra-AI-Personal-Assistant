from student.database import get_connection


def save_quiz_result(
    subject: str,
    semester: int,
    topic: str,
    total_questions: int,
    correct_answers: int,
    difficulty: str = "Medium",
    feedback: str = ""
) -> str:
    """Save the result of a completed academic quiz."""

    if total_questions <= 0:
        return "Total questions must be greater than zero."

    if not 0 <= correct_answers <= total_questions:
        return "Invalid number of correct answers."

    topic = topic.strip()

    if not topic:
        return "Please provide a quiz topic."

    difficulty = difficulty.strip().title()

    if difficulty not in ("Easy", "Medium", "Hard"):
        return "Difficulty must be Easy, Medium or Hard."

    percentage = round(
        correct_answers / total_questions * 100, 2
    )

    with get_connection() as conn:

        row = conn.execute("""
            SELECT id, name
            FROM subjects
            WHERE name = ? COLLATE NOCASE
            AND semester = ?
        """, (subject.strip(), semester)).fetchone()

        if row is None:
            return "Subject not registered for this semester."

        cursor = conn.execute("""
            INSERT INTO quiz_results (
                subject_id,
                topic,
                total_questions,
                correct_answers,
                percentage,
                difficulty,
                feedback
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            row["id"],
            topic,
            total_questions,
            correct_answers,
            percentage,
            difficulty,
            feedback
        ))

        result_id = cursor.lastrowid

    return (
        f"Quiz result saved successfully.\n"
        f"Result ID: {result_id}\n"
        f"Subject: {row['name']}\n"
        f"Topic: {topic}\n"
        f"Score: {correct_answers}/{total_questions}\n"
        f"Percentage: {percentage}%\n"
        f"Difficulty: {difficulty}"
    )


def list_quiz_results(subject: str = "") -> str:
    """Retrieve previous quiz results."""

    query = """
        SELECT q.*, s.name AS subject, s.semester
        FROM quiz_results q
        JOIN subjects s ON q.subject_id = s.id
    """

    params = ()

    if subject.strip():

        query += " WHERE s.name = ? COLLATE NOCASE"

        params = (subject.strip(),)

    query += " ORDER BY q.id DESC LIMIT 50"

    with get_connection() as conn:

        rows = conn.execute(query, params).fetchall()

    if not rows:
        return "No quiz results found."

    result = ["ASTRA Quiz History:"]

    for row in rows:

        result.append(
            f"\nID: {row['id']}\n"
            f"Subject: {row['subject']}\n"
            f"Semester: {row['semester']}\n"
            f"Topic: {row['topic']}\n"
            f"Score: {row['correct_answers']}/"
            f"{row['total_questions']}\n"
            f"Percentage: {row['percentage']}%\n"
            f"Difficulty: {row['difficulty']}\n"
            f"Feedback: {row['feedback']}\n"
            f"Date: {row['created_at']}"
        )

    return "\n".join(result)


def get_academic_performance() -> str:
    """Calculate overall and subject-wise quiz performance."""

    with get_connection() as conn:

        rows = conn.execute("""
            SELECT
                s.name AS subject,
                s.semester,
                COUNT(q.id) AS quizzes,
                SUM(q.total_questions) AS questions,
                SUM(q.correct_answers) AS correct,
                ROUND(
                    100.0 * SUM(q.correct_answers)
                    / SUM(q.total_questions), 2
                ) AS average_score
            FROM quiz_results q
            JOIN subjects s ON q.subject_id = s.id
            GROUP BY s.id, s.name, s.semester
            ORDER BY average_score DESC
        """).fetchall()

    if not rows:
        return "No academic performance data available."

    total_quizzes = sum(row["quizzes"] for row in rows)
    total_questions = sum(row["questions"] for row in rows)
    total_correct = sum(row["correct"] for row in rows)

    overall = round(
        total_correct / total_questions * 100, 2
    )

    result = [
        "ASTRA Academic Performance Report",
        f"Total quizzes: {total_quizzes}",
        f"Total questions: {total_questions}",
        f"Overall accuracy: {overall}%",
        "\nSubject-wise Performance:"
    ]

    for row in rows:

        result.append(
            f"{row['subject']} "
            f"(Semester {row['semester']}): "
            f"{row['average_score']}% "
            f"across {row['quizzes']} quizzes"
        )

    return "\n".join(result)


def identify_weak_topics(
    threshold: float = 60.0
) -> str:
    """Identify topics with quiz accuracy below a threshold."""

    if not 0 <= threshold <= 100:
        return "Threshold must be between 0 and 100."

    with get_connection() as conn:

        rows = conn.execute("""
            SELECT
                s.name AS subject,
                s.semester,
                q.topic,
                COUNT(q.id) AS attempts,
                SUM(q.total_questions) AS questions,
                ROUND(
                    100.0 * SUM(q.correct_answers)
                    / SUM(q.total_questions), 2
                ) AS average_score
            FROM quiz_results q
            JOIN subjects s ON q.subject_id = s.id
            GROUP BY s.id, s.name, s.semester,
                     q.topic COLLATE NOCASE
            HAVING
                100.0 * SUM(q.correct_answers)
                / SUM(q.total_questions) < ?
            ORDER BY average_score ASC
        """, (threshold,)).fetchall()

    if not rows:
        return (
            "No recorded topics below the selected threshold. "
            "More quizzes may be needed for meaningful analysis."
        )

    result = ["Topics Requiring Revision:"]

    for row in rows:

        result.append(
            f"- {row['subject']} "
            f"(Semester {row['semester']}) | "
            f"{row['topic']} | "
            f"Accuracy: {row['average_score']}% | "
            f"Attempts: {row['attempts']} | "
            f"Questions: {row['questions']}"
        )

    return "\n".join(result)


def delete_quiz_result(result_id: int) -> str:
    """Delete a quiz result explicitly requested by the user."""

    with get_connection() as conn:

        cursor = conn.execute("""
            DELETE FROM quiz_results
            WHERE id = ?
        """, (result_id,))

        deleted = cursor.rowcount

    if deleted == 0:
        return "Quiz result not found."

    return f"Quiz result {result_id} deleted successfully."