import os
import ctypes
from pathlib import Path

from utils.logger import get_logger
from config import settings


logger = get_logger()


# ============================================================
# SAFE USER DIRECTORIES
# ============================================================

USER_HOME = Path.home()

SAFE_ROOTS = [
    USER_HOME / "Documents",
    USER_HOME / "Desktop",
    USER_HOME / "Downloads",

    # OneDrive user folders
    USER_HOME / "OneDrive" / "Desktop",
    USER_HOME / "OneDrive" / "Documents",
    USER_HOME / "OneDrive" / "Downloads",
]


# ============================================================
# USER CONFIRMATION
# ============================================================

def request_user_confirmation(action: str) -> bool:
    """
    Shows a native Windows confirmation dialog.
    """

    try:

        logger.info(
            f"Security confirmation requested for: '{action}'"
        )

        result = ctypes.windll.user32.MessageBoxW(

            0,

            f"Jarvis is requesting permission to:\n\n"
            f"--> {action}\n\n"
            f"Do you want to allow this action?",

            "Jarvis - Security Confirmation",

            4 | 32 | 4000
        )

        approved = result == 6

        logger.info(
            f"Security confirmation result: {approved}"
        )

        return approved


    except Exception as e:

        logger.error(
            f"Failed to show native confirmation: {e}"
        )

        try:

            import pyautogui

            result = pyautogui.confirm(

                text=f"Allow Jarvis to:\n{action}?",

                title="Jarvis Security Check",

                buttons=["Yes", "No"]
            )

            return result == "Yes"


        except Exception as py_error:

            logger.error(
                f"PyAutoGUI fallback also failed: {py_error}"
            )

            return False


# ============================================================
# PATH SECURITY
# ============================================================

def resolve_and_verify_path(path_str: str) -> Path:
    """
    Resolve a path and make sure it is inside an allowed
    user directory.

    Allowed:
        Desktop
        Documents
        Downloads

    Absolute paths inside those directories are also allowed.
    """

    if not path_str:

        raise PermissionError(
            "No path was provided."
        )


    path_str = str(path_str).strip()


    # --------------------------------------------------------
    # Handle friendly folder names
    # --------------------------------------------------------

    friendly_paths = {

        "desktop":
            USER_HOME / "Desktop",

        "documents":
            USER_HOME / "Documents",

        "downloads":
            USER_HOME / "Downloads",

    }


    lower_path = path_str.lower()


    if lower_path in friendly_paths:

        target_path = friendly_paths[lower_path].resolve()


    else:

        target_path = Path(path_str).expanduser().resolve()


    # --------------------------------------------------------
    # Handle relative paths
    # --------------------------------------------------------

    if not Path(path_str).is_absolute():

        # Try relative path from Desktop first.
        desktop_candidate = (
            USER_HOME / "Desktop" / path_str
        ).resolve()

        if desktop_candidate.exists():

            target_path = desktop_candidate

        else:

            # Try relative path from Documents.
            documents_candidate = (
                USER_HOME / "Documents" / path_str
            ).resolve()

            if documents_candidate.exists():

                target_path = documents_candidate


    # --------------------------------------------------------
    # Security check
    # --------------------------------------------------------

    for root in SAFE_ROOTS:

        root = root.resolve()

        try:

            target_path.relative_to(root)

            return target_path

        except ValueError:

            continue


    logger.warning(
        f"Safety Block: Unsafe path access attempted: "
        f"'{target_path}'"
    )

    raise PermissionError(

        f"Access to path '{target_path}' "
        f"is restricted for system safety."
    )


# ============================================================
# LIST DIRECTORY
# ============================================================

def list_directory(directory_path: str = None) -> str:
    """
    List files and folders in a specified directory.

    If no directory is provided, Desktop is used.
    """

    if not directory_path:

        directory_path = "Desktop"


    try:

        safe_path = resolve_and_verify_path(
            directory_path
        )


        if not safe_path.exists():

            return (
                f"Directory does not exist: "
                f"{safe_path}"
            )


        if not safe_path.is_dir():

            return (
                f"Path is not a directory: "
                f"{safe_path}"
            )


        items = sorted(
            os.listdir(safe_path)
        )


        if not items:

            return (
                f"Directory '{safe_path.name}' "
                f"is empty."
            )


        output = [
            f"Contents of {safe_path}:"
        ]


        for item in items:

            item_path = safe_path / item

            if item_path.is_dir():

                prefix = "[DIR]"

            else:

                prefix = "[FILE]"


            output.append(
                f"  {prefix} {item}"
            )


        return "\n".join(output)


    except PermissionError as pe:

        return str(pe)


    except Exception as e:

        logger.error(
            f"Error listing directory "
            f"{directory_path}: {e}"
        )

        return (
            f"Error listing directory: "
            f"{str(e)}"
        )


# ============================================================
# READ TEXT FILE
# ============================================================

def read_text_file(file_path: str) -> str:
    """
    Read a text file from an allowed directory.
    """

    try:

        safe_path = resolve_and_verify_path(
            file_path
        )


        if not safe_path.exists():

            return (
                f"File not found: {file_path}"
            )


        if not safe_path.is_file():

            return (
                f"Path is not a file: {file_path}"
            )


        size = safe_path.stat().st_size


        if size > 102400:

            return (
                f"File is too large "
                f"({size} bytes). "
                f"Max read limit is 100KB."
            )


        with open(
            safe_path,
            "r",
            encoding="utf-8",
            errors="ignore"
        ) as file:

            content = file.read()


        return (
            f"--- Content of "
            f"{safe_path.name} ---\n"
            f"{content}"
        )


    except PermissionError as pe:

        return str(pe)


    except Exception as e:

        logger.error(
            f"Error reading file "
            f"{file_path}: {e}"
        )

        return (
            f"Error reading file: "
            f"{str(e)}"
        )


# ============================================================
# WRITE TEXT FILE
# ============================================================

def write_text_file(
    file_path: str,
    content: str
) -> str:

    """
    Write or overwrite a text file
    after user confirmation.
    """

    try:

        safe_path = resolve_and_verify_path(
            file_path
        )


        action_msg = (
            f"Write file "
            f"'{safe_path.name}' at:\n"
            f"{safe_path.parent}"
        )


        if (
            settings.SAFE_EXECUTION_MODE
            and not request_user_confirmation(
                action_msg
            )
        ):

            return (
                "Action cancelled by user: "
                "Write operation declined."
            )


        safe_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )


        with open(
            safe_path,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(content)


        logger.info(
            f"Successfully wrote file: "
            f"{safe_path}"
        )


        return (
            f"Successfully wrote file "
            f"to {safe_path.name}."
        )


    except PermissionError as pe:

        return str(pe)


    except Exception as e:

        logger.error(
            f"Error writing file "
            f"{file_path}: {e}"
        )

        return (
            f"Error writing file: "
            f"{str(e)}"
        )


# ============================================================
# DELETE FILE
# ============================================================

def delete_file_safely(
    file_path: str
) -> str:

    """
    Delete a file only after explicit
    user confirmation.
    """

    try:

        safe_path = resolve_and_verify_path(
            file_path
        )


        if not safe_path.exists():

            return (
                f"File does not exist: "
                f"{file_path}"
            )


        if not safe_path.is_file():

            return (
                f"Path is not a file: "
                f"{file_path}"
            )


        action_msg = (
            f"Permanently DELETE file:\n"
            f"{safe_path}"
        )


        if not request_user_confirmation(
            action_msg
        ):

            return (
                "Action cancelled by user: "
                "Delete operation declined."
            )


        safe_path.unlink()


        logger.info(
            f"Deleted file: {safe_path}"
        )


        return (
            f"Successfully deleted file "
            f"{safe_path.name}."
        )


    except PermissionError as pe:

        return str(pe)


    except Exception as e:

        logger.error(
            f"Error deleting file "
            f"{file_path}: {e}"
        )

        return (
            f"Error deleting file: "
            f"{str(e)}"
        )

def find_pdf_files(search_term: str = "") -> str:
    """
    Search safe user directories for PDF files.

    Args:
        search_term: Optional filename keyword.

    Returns:
        Matching PDF file paths.
    """

    try:
        search_term = search_term.lower().strip()

        matches = []

        for root in SAFE_ROOTS:

            if not root.exists():
                continue

            try:
                for pdf in root.rglob("*.pdf"):

                    if not pdf.is_file():
                        continue

                    filename = pdf.name.lower()

                    if not search_term or search_term in filename:
                        matches.append(str(pdf.resolve()))

            except (PermissionError, OSError):
                continue

        if not matches:
            return "No matching PDF files were found."

        # Remove duplicates
        matches = list(dict.fromkeys(matches))

        # Limit results
        matches = matches[:20]

        return (
            "Found PDF files:\n"
            + "\n".join(
                f"{index + 1}. {path}"
                for index, path in enumerate(matches)
            )
        )

    except Exception as e:

        logger.error(
            f"Error searching for PDF files: {e}"
        )

        return f"Failed to search for PDF files: {str(e)}"