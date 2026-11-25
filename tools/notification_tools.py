from student.database import get_connection
from student.notification_service import notification_service


def send_test_notification() -> str:
    """Display a test Windows notification on user request."""

    try:

        notification_service.show_notification(
            "ASTRA AI Assistant",
            "Your Windows notification system is working."
        )

        return "Test notification submitted to Windows."

    except Exception as error:

        return f"Notification failed: {error}"


def get_notification_history() -> str:
    """Retrieve recent academic notification history."""

    with get_connection() as conn:

        rows = conn.execute("""
            SELECT *
            FROM notification_history
            ORDER BY sent_at DESC
            LIMIT 20
        """).fetchall()

    if not rows:

        return "No notification history available."

    result = ["ASTRA Notification History:"]

    for row in rows:

        result.append(
            f"\nType: {row['notification_type']}\n"
            f"Message: {row['message']}\n"
            f"Sent: {row['sent_at']} UTC"
        )

    return "\n".join(result)