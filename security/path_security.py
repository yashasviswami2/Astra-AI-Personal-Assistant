import os
import stat
from pathlib import Path

from utils.logger import get_logger


logger = get_logger()

USER_HOME = Path.home()

MAX_TEXT_READ_BYTES = 100 * 1024
MAX_TEXT_WRITE_BYTES = 1024 * 1024
MAX_PDF_BYTES = 20 * 1024 * 1024
MAX_PDF_PAGES = 100


# ==========================================
# ALLOWED DIRECTORIES
# ==========================================

def get_safe_roots():
    """Return existing approved user directories."""

    candidates = [
        USER_HOME / "Desktop",
        USER_HOME / "Documents",
        USER_HOME / "Downloads",
    ]

    # Support Windows OneDrive directories.
    for variable in (
        "OneDrive",
        "OneDriveConsumer",
        "OneDriveCommercial",
    ):
        location = os.environ.get(variable)

        if location:
            root = Path(location)

            candidates.extend([
                root / "Desktop",
                root / "Documents",
            ])

    roots = set()

    for path in candidates:
        if path.is_dir():
            roots.add(path.resolve())

    return roots


# ==========================================
# PROTECTED FILES
# ==========================================

PROTECTED_NAMES = {
    ".env",
    ".git",
    ".ssh",
    ".aws",
    ".venv",
    ".gnupg",
    ".gitconfig",
    ".npmrc",
    ".pypirc",
    "credentials.json",
    "secrets.json",
    "passwords.txt",
    "config.py",
    "id_rsa",
    "id_ed25519",
    "ntuser.dat",
    "login data",
    "cookies",
    "local state",
}

PROTECTED_DIRECTORIES = {
    "appdata",
    "windows",
    "system32",
    "program files",
    "program files (x86)",
    "programdata",
    "$recycle.bin",
}

PROTECTED_EXTENSIONS = {
    ".pem",
    ".key",
    ".pfx",
    ".p12",
    ".kdbx",
    ".db",
    ".sqlite",
    ".sqlite3",
    ".db-wal",
    ".db-shm",
    ".exe",
    ".dll",
    ".sys",
    ".lnk",
}

SENSITIVE_KEYWORDS = {
    "password",
    "credential",
    "secret",
    "api_key",
    "apikey",
    "private_key",
    "access_token",
}


# ==========================================
# SECURITY HELPERS
# ==========================================

def block_access(reason):
    """Log and reject an unsafe file operation."""

    logger.warning(
        "FILE SECURITY | Access blocked | %s",
        reason
    )

    raise PermissionError(reason)


def is_protected_path(path):
    """Check whether a path contains protected components."""

    for part in path.parts:
        name = part.casefold()

        if name in PROTECTED_NAMES:
            return True

        if name in PROTECTED_DIRECTORIES:
            return True

        if name.startswith(".env."):
            return True

        if any(
            keyword in name
            for keyword in SENSITIVE_KEYWORDS
        ):
            return True

        if Path(name).suffix in PROTECTED_EXTENSIONS:
            return True

    return False


def reject_unsafe_links(path):
    """Reject symbolic links and Windows reparse points."""

    for component in (path, *path.parents):

        try:
            info = component.lstat()

        except FileNotFoundError:
            continue

        attributes = getattr(
            info,
            "st_file_attributes",
            0
        )

        reparse_flag = getattr(
            stat,
            "FILE_ATTRIBUTE_REPARSE_POINT",
            0x400
        )

        if (
            component.is_symlink()
            or attributes & reparse_flag
        ):
            block_access(
                "Symbolic links and reparse points "
                "are not permitted."
            )


# ==========================================
# CENTRAL PATH VALIDATION
# ==========================================

def resolve_and_verify_path(path_str):
    """Resolve and validate a user-space file path."""

    if not isinstance(path_str, str):
        block_access("Invalid path type.")

    path_str = path_str.strip()

    if not path_str:
        block_access("Empty file path.")

    if any(ord(char) < 32 for char in path_str):
        block_access("Invalid characters in path.")

    normalized = path_str.replace("/", "\\")

    # Reject network paths and Windows device paths.
    if normalized.startswith("\\\\"):
        block_access(
            "Network and device paths are restricted."
        )

    # Expand user-home notation.
    target = Path(path_str).expanduser()

    # Reject Windows alternate data streams.
    if ":" in str(target)[len(target.drive):]:
        block_access(
            "Alternate data streams are restricted."
        )

    if target.drive and not target.is_absolute():
        block_access("Drive-relative paths are restricted.")

    if ".." in target.parts:
        block_access("Parent-directory traversal is restricted.")

    # Resolve friendly folder names.
    if not target.is_absolute():

        parts = target.parts

        if parts and parts[0].casefold() in {
            "desktop",
            "documents",
            "downloads",
        }:
            folder_name = parts[0].casefold()

            matches = [
                root
                for root in get_safe_roots()
                if root.name.casefold() == folder_name
            ]

            if len(matches) != 1:
                block_access(
                    "Folder location is ambiguous or unavailable. "
                    "Use an absolute path."
                )

            target = matches[0].joinpath(*parts[1:])

        else:
            block_access(
                "Use an absolute path or an approved "
                "user directory."
            )

    if is_protected_path(target):
        block_access("Protected file or directory.")

    reject_unsafe_links(target)

    resolved = target.resolve()

    if is_protected_path(resolved):
        block_access("Protected destination.")

    safe_roots = get_safe_roots()

    if not any(
        resolved == root or root in resolved.parents
        for root in safe_roots
    ):
        block_access(
            "Path is outside approved user directories."
        )

    return resolved


# ==========================================
# FILE SIZE VALIDATION
# ==========================================

def validate_file_size(path, max_bytes):

    if not path.is_file():
        raise ValueError("The specified path is not a file.")

    size = path.stat().st_size

    if size > max_bytes:
        block_access(
            f"File exceeds the allowed limit "
            f"of {max_bytes} bytes."
        )

    return size
