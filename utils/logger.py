"""
utils/logger.py
===============
Centralised logger for all ASTRA modules.
Writes to both console (INFO+) and logs/ASTRA.log (DEBUG+).
"""

import logging
import sys
from pathlib import Path

# Force stdout/stderr to UTF-8 on Windows to prevent UnicodeEncodeError
# (Windows cmd/PowerShell defaults to CP1252 which can't encode many Unicode chars)
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass  # Python < 3.7 doesn't have reconfigure()

# Resolve log directory relative to THIS file (utils/logger.py → project root/logs/)
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True, parents=True)

LOG_FILE = LOG_DIR / "ASTRA.log"

CONSOLE_FORMAT = "%(asctime)s  %(levelname)-8s  %(message)s"
FILE_FORMAT    = "%(asctime)s  %(levelname)-8s  %(name)s — %(filename)s:%(lineno)d — %(message)s"
DATE_FORMAT    = "%H:%M:%S"

def _setup_logger() -> logging.Logger:
    logger = logging.getLogger("ASTRAAssistant")

    # Prevent duplicate handlers if module is reloaded
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Console handler — INFO and above
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter(CONSOLE_FORMAT, datefmt=DATE_FORMAT))
    logger.addHandler(ch)

    # File handler — DEBUG and above
    try:
        fh = logging.FileHandler(LOG_FILE, encoding="utf-8", mode="a")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter(FILE_FORMAT, datefmt=DATE_FORMAT))
        logger.addHandler(fh)
    except Exception as e:
        logger.warning(f"Could not open log file {LOG_FILE}: {e}")

    return logger


_logger = _setup_logger()


def get_logger() -> logging.Logger:
    """Return the shared ASTRA logger instance."""
    return _logger
