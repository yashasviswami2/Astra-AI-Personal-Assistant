from student.database import get_connection


def remember_information(
    key: str,
    value: str,
    category: str = "General"
) -> str:
    """Save or update personal information explicitly provided by the user."""

    key = key.strip().lower()
    value = value.strip()
    category = category.strip() or "General"

    if not key or not value:
        return "Memory key and value cannot be empty."

    if len(key) > 100 or len(value) > 2000:
        return "Memory entry is too long."

    with get_connection() as conn:

        conn.execute("""
            INSERT INTO personal_memory
                (memory_key, memory_value, category)
            VALUES (?, ?, ?)

            ON CONFLICT(memory_key)
            DO UPDATE SET
                memory_value = excluded.memory_value,
                category = excluded.category,
                updated_at = CURRENT_TIMESTAMP
        """, (key, value, category))

    return f"Remembered successfully: {key} = {value}"


def recall_information(key: str) -> str:
    """Retrieve a specific saved personal memory."""

    with get_connection() as conn:

        row = conn.execute("""
            SELECT memory_key, memory_value, category
            FROM personal_memory
            WHERE memory_key = ?
        """, (key.strip().lower(),)).fetchone()

    if row is None:
        return f"No saved memory found for '{key}'."

    return (
        f"{row['memory_key']}: {row['memory_value']}\n"
        f"Category: {row['category']}"
    )


def list_personal_memories(
    category: str = "All"
) -> str:
    """Retrieve all saved memories or memories in a specific category."""

    with get_connection() as conn:

        if category.lower() == "all":

            rows = conn.execute("""
                SELECT *
                FROM personal_memory
                ORDER BY category, memory_key
            """).fetchall()

        else:

            rows = conn.execute("""
                SELECT *
                FROM personal_memory
                WHERE category = ? COLLATE NOCASE
                ORDER BY memory_key
            """, (category.strip(),)).fetchall()

    if not rows:
        return "No personal memories found."

    result = ["ASTRA Personal Memory:"]

    for row in rows:

        result.append(
            f"- [{row['category']}] "
            f"{row['memory_key']}: "
            f"{row['memory_value']}"
        )

    return "\n".join(result)


def search_personal_memory(query: str) -> str:
    """Search saved personal memories using a keyword."""

    if not query.strip():
        return "Please provide a search keyword."

    keyword = f"%{query.strip()}%"

    with get_connection() as conn:

        rows = conn.execute("""
            SELECT *
            FROM personal_memory
            WHERE memory_key LIKE ?
               OR memory_value LIKE ?
               OR category LIKE ?
            ORDER BY memory_key
        """, (keyword, keyword, keyword)).fetchall()

    if not rows:
        return "No matching personal memories found."

    return "\n".join(
        f"[{row['category']}] "
        f"{row['memory_key']}: {row['memory_value']}"
        for row in rows
    )


def forget_information(key: str) -> str:
    """Delete a specific saved personal memory at the user's request."""

    with get_connection() as conn:

        cursor = conn.execute("""
            DELETE FROM personal_memory
            WHERE memory_key = ?
        """, (key.strip().lower(),))

        deleted = cursor.rowcount

    if deleted == 0:
        return f"No saved memory found for '{key}'."

    return f"Personal memory '{key}' deleted successfully."