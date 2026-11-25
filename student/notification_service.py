import logging
import threading
import time

from datetime import datetime
from winotify import Notification, audio

from student.database import get_connection
from student.reminders import get_reminders


logger = logging.getLogger(__name__)


# =====================================
# ASTRA WINDOWS NOTIFICATION SERVICE
# =====================================

class AstraNotificationService:

    def __init__(self, interval=60):

        self.interval = interval
        self.stop_event = threading.Event()
        self.thread = None


    def notification_exists(self, key):

        with get_connection() as conn:

            row = conn.execute("""
                SELECT notification_key
                FROM notification_history
                WHERE notification_key = ?
            """, (key,)).fetchone()

        return row is not None


    def save_notification(self, key, kind, message):

        with get_connection() as conn:

            conn.execute("""
                INSERT OR IGNORE INTO notification_history (
                    notification_key,
                    notification_type,
                    message
                )
                VALUES (?, ?, ?)
            """, (key, kind, message))


    def show_notification(self, title, message):

        toast = Notification(
            app_id="ASTRA AI Assistant",
            title=title,
            msg=message,
            duration="short"
        )

        toast.set_audio(
            audio.Default,
            loop=False
        )

        toast.show()


    def check_reminders(self):

        reminders = get_reminders()

        for reminder in reminders:

            reminder_id = reminder.get("id", "")
            priority = reminder.get("priority", "Normal")
            kind = reminder.get("type", "Academic")
            deadline = reminder.get("deadline", "")
            message = reminder.get("message", "")

            today = datetime.now().strftime("%Y-%m-%d")

            key = (
                f"{reminder_id}:"
                f"{priority}:"
                f"{deadline}:"
                f"{today}"
            )

            if self.notification_exists(key):
                continue

            if not message:
                continue

            try:

                self.show_notification(
                    f"ASTRA | {kind.title()} Reminder",
                    message
                )

                self.save_notification(
                    key,
                    kind,
                    message
                )

                logger.info(
                    "ASTRA notification requested: %s",
                    key
                )

            except Exception:

                logger.exception(
                    "Unable to display ASTRA notification."
                )


    def run(self):

        logger.info(
            "ASTRA background notification service started."
        )

        while not self.stop_event.is_set():

            try:

                self.check_reminders()

            except Exception:

                logger.exception(
                    "ASTRA reminder check failed."
                )

            self.stop_event.wait(self.interval)


    def start(self):

        if self.thread and self.thread.is_alive():
            return

        self.stop_event.clear()

        self.thread = threading.Thread(
            target=self.run,
            name="ASTRA-Notifications",
            daemon=True
        )

        self.thread.start()


    def stop(self):

        self.stop_event.set()

        if self.thread:
            self.thread.join(timeout=5)


notification_service = AstraNotificationService()


if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s"
    )

    print("ASTRA Background Notification Service")
    print("Checking academic reminders every 60 seconds.")
    print("Press Ctrl+C to stop.")

    notification_service.start()

    try:

        while True:
            time.sleep(1)

    except KeyboardInterrupt:

        notification_service.stop()

        print("ASTRA notification service stopped.")