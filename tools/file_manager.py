from send2trash import send2trash

from utils.logger import get_logger
from utils.tool_response import tool_success, tool_error

from security.confirmation import request_user_confirmation

from security.path_security import (
    resolve_and_verify_path,
    is_protected_path,
    validate_file_size,
    MAX_TEXT_READ_BYTES,
    MAX_TEXT_WRITE_BYTES,
)


logger = get_logger()

MAX_DIRECTORY_ITEMS = 200


# ==========================================
# LIST DIRECTORY
# ==========================================

def list_directory(directory_path: str = None):
    """List files and folders in an approved directory."""

    try:
        safe_path = resolve_and_verify_path(
            directory_path or "Desktop"
        )

        if not safe_path.is_dir():
            return tool_error(
                "Directory does not exist.",
                "INVALID_DIRECTORY"
            )

        items = []
        truncated = False

        for item in safe_path.iterdir():

            if is_protected_path(item):
                continue

            try:
                resolve_and_verify_path(str(item))
            except (PermissionError, OSError):
                continue

            if len(items) >= MAX_DIRECTORY_ITEMS:
                truncated = True
                break

            items.append({
                "name": item.name,
                "type": (
                    "directory" if item.is_dir()
                    else "file"
                )
            })

        logger.info("FILE SECURITY | Directory listed")

        return tool_success(
            f"Found {len(items)} accessible items.",
            {
                "directory": str(safe_path),
                "items": items,
                "truncated": truncated
            }
        )

    except PermissionError:
        return tool_error(
            "Directory access denied.",
            "ACCESS_DENIED"
        )

    except Exception:
        logger.exception("Directory listing failed")

        return tool_error(
            "Unable to list directory.",
            "DIRECTORY_ERROR"
        )


# ==========================================
# READ TEXT FILE
# ==========================================

def read_text_file(file_path: str):
    """Read a text file within approved directories."""

    try:
        safe_path = resolve_and_verify_path(file_path)

        validate_file_size(
            safe_path,
            MAX_TEXT_READ_BYTES
        )

        with safe_path.open("rb") as file:
            raw = file.read(MAX_TEXT_READ_BYTES + 1)

        if len(raw) > MAX_TEXT_READ_BYTES:
            return tool_error(
                "File exceeds the reading limit.",
                "FILE_TOO_LARGE"
            )

        content = raw.decode("utf-8")

        logger.info("FILE SECURITY | Text file read")

        return tool_success(
            f"Successfully read {safe_path.name}.",
            {
                "filename": safe_path.name,
                "content": content
            }
        )

    except PermissionError:
        return tool_error(
            "File access denied.",
            "ACCESS_DENIED"
        )

    except UnicodeDecodeError:
        return tool_error(
            "File is not valid UTF-8 text.",
            "INVALID_TEXT_FILE"
        )

    except Exception:
        logger.exception("File reading failed")

        return tool_error(
            "Unable to read file.",
            "READ_ERROR"
        )


# ==========================================
# WRITE TEXT FILE
# ==========================================

def write_text_file(file_path: str, content: str):
    """Write text after explicit user approval."""

    try:
        safe_path = resolve_and_verify_path(file_path)

        if not isinstance(content, str):
            return tool_error(
                "Content must be text.",
                "INVALID_CONTENT"
            )

        encoded_content = content.encode("utf-8")

        if len(encoded_content) > MAX_TEXT_WRITE_BYTES:
            return tool_error(
                "Content exceeds the 1 MB writing limit.",
                "FILE_TOO_LARGE"
            )

        if safe_path.exists():
            return tool_error(
                "Overwriting existing files is disabled.",
                "FILE_ALREADY_EXISTS"
            )

        approved = request_user_confirmation(
            "write_text_file",
            {
                "path": str(safe_path),
                "content": content
            }
        )

        if not approved:
            return tool_error(
                "Write operation was not approved.",
                "PERMISSION_DENIED"
            )

        safe_path = resolve_and_verify_path(file_path)

        safe_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        safe_path = resolve_and_verify_path(file_path)

        # Exclusive creation prevents accidental overwrite.
        with safe_path.open("xb") as file:
            file.write(encoded_content)

        logger.info("FILE SECURITY | Text file created")

        return tool_success(
            f"Successfully created {safe_path.name}.",
            {"path": str(safe_path)}
        )

    except PermissionError:
        return tool_error(
            "File access denied.",
            "ACCESS_DENIED"
        )

    except FileExistsError:
        return tool_error(
            "The file already exists.",
            "FILE_ALREADY_EXISTS"
        )

    except Exception:
        logger.exception("File writing failed")

        return tool_error(
            "Unable to write file.",
            "WRITE_ERROR"
        )


# ==========================================
# SAFE FILE DELETION
# ==========================================

def delete_file_safely(file_path: str):
    """Move a file to the Recycle Bin after approval."""

    try:
        safe_path = resolve_and_verify_path(file_path)

        if not safe_path.is_file():
            return tool_error(
                "File does not exist.",
                "FILE_NOT_FOUND"
            )

        approved = request_user_confirmation(
            "delete_file_safely",
            {
                "path": str(safe_path),
                "operation": "Move to Windows Recycle Bin"
            }
        )

        if not approved:
            return tool_error(
                "Deletion was not approved.",
                "PERMISSION_DENIED"
            )

        safe_path = resolve_and_verify_path(file_path)

        if not safe_path.is_file():
            return tool_error(
                "File no longer exists.",
                "FILE_NOT_FOUND"
            )

        send2trash(str(safe_path))

        logger.info(
            "FILE SECURITY | File moved to Recycle Bin"
        )

        return tool_success(
            f"{safe_path.name} moved to the Recycle Bin."
        )

    except PermissionError:
        return tool_error(
            "File access denied.",
            "ACCESS_DENIED"
        )

    except Exception:
        logger.exception("Safe deletion failed")

        return tool_error(
            "Unable to move file to the Recycle Bin.",
            "DELETE_ERROR"
        )