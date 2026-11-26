import json
import logging
import threading

from pathlib import Path
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from uuid import uuid4


BASE_DIR = Path(__file__).resolve().parent.parent
AUDIT_DIR = BASE_DIR / "logs"
AUDIT_FILE = AUDIT_DIR / "security_audit.jsonl"

MAX_LOG_SIZE = 5 * 1024 * 1024
BACKUP_COUNT = 5

_setup_lock = threading.Lock()

logger = logging.getLogger("astra.security.audit")
logger.setLevel(logging.INFO)
logger.propagate = False

ALLOWED_EVENTS = {
    "permission_granted",
    "permission_denied",
    "access_blocked",
    "tool_executed",
    "tool_failed",
    "screenshot_captured",
    "vision_requested",
    "clipboard_accessed",
    "file_accessed",
    "security_error",
    "system_test"
}

ALLOWED_STATUSES = {
    "success",
    "denied",
    "failed",
    "blocked",
    "pending"
}


def initialize_audit_logger():
    """Initialize the rotating security audit logger."""

    with _setup_lock:

        if logger.handlers:
            return

        AUDIT_DIR.mkdir(parents=True, exist_ok=True)

        handler = RotatingFileHandler(
            AUDIT_FILE,
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT,
            encoding="utf-8"
        )

        handler.setFormatter(
            logging.Formatter("%(message)s")
        )

        logger.addHandler(handler)


def log_security_event(
    event: str,
    tool_name: str,
    status: str
):
    """Record security metadata without storing private content."""

    try:

        if event not in ALLOWED_EVENTS:
            raise ValueError("Invalid security event")

        if status not in ALLOWED_STATUSES:
            raise ValueError("Invalid security status")

        if (
            not isinstance(tool_name, str)
            or not tool_name.isidentifier()
            or len(tool_name) > 100
        ):
            raise ValueError("Invalid tool name")

        initialize_audit_logger()

        record = {
            "event_id": uuid4().hex,
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
            "event": event,
            "tool": tool_name,
            "status": status,
            "application": "ASTRA"
        }

        logger.info(
            json.dumps(record, ensure_ascii=True)
        )

        return True

    except Exception:

        logging.getLogger(__name__).error(
            "ASTRA security audit logging failed."
        )

        return False
