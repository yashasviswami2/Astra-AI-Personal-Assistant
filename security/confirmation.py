import ctypes
import json
import threading

from security.permissions import get_tool_permission
from utils.logger import get_logger


logger = get_logger()

_confirmation_lock = threading.Lock()

MAX_CONFIRMATION_LENGTH = 3000


# ==========================================
# PRIVACY WARNINGS
# ==========================================

PRIVACY_WARNINGS = {

    "analyze_screen": (
        "Your screenshot will be sent to Gemini "
        "for analysis."
    ),

    "take_screenshot": (
        "Your screenshot may contain private "
        "or confidential information."
    ),

    "read_text_file": (
        "The contents of this file may be sent "
        "to Gemini for processing."
    ),

    "extract_pdf_text": (
        "Extracted PDF content may be sent "
        "to Gemini for processing."
    ),

    "list_directory": (
        "File and folder names may be shared "
        "with Gemini."
    ),

    "get_clipboard": (
        "Your clipboard may contain passwords "
        "or other private information. Its contents "
        "may be sent to Gemini."
    ),

    "recall_information": (
        "Stored personal information may be "
        "shared with Gemini."
    ),

    "write_text_file": (
        "ASTRA will attempt to create a local file."
    ),

    "delete_file_safely": (
        "ASTRA will attempt to move the selected "
        "file to the Windows Recycle Bin."
    ),

    "forget_information": (
        "The selected personal memory will be removed "
        "from ASTRA's memory database."
    ),

    "execute_custom_workflow": (
        "ASTRA will execute the requested "
        "sequence of automation actions."
    ),
}


# ==========================================
# SECURITY CONFIRMATION
# ==========================================

def request_user_confirmation(
    tool_name,
    arguments=None
):
    """Request explicit authorization for a tool."""

    try:

        if not isinstance(tool_name, str):
            return False

        permission = get_tool_permission(tool_name)

        action_details = json.dumps(
            arguments or {},
            indent=2,
            ensure_ascii=False,
            default=str
        )

        # Reject actions that cannot be fully inspected.
        if len(action_details) > MAX_CONFIRMATION_LENGTH:

            logger.warning(
                "SECURITY | Confirmation rejected | "
                "Arguments exceed display limit | %s",
                tool_name
            )

            return False

        message = (
            "ASTRA SECURITY REQUEST\n\n"
            f"Action: {tool_name}\n"
            f"Permission: {permission.value.upper()}\n\n"
            f"Action details:\n{action_details}\n"
        )

        privacy_warning = PRIVACY_WARNINGS.get(tool_name)

        if privacy_warning:

            message += (
                "\nIMPORTANT SECURITY NOTICE:\n"
                f"{privacy_warning}\n"
            )

        message += (
            "\nOnly approve this request if you "
            "understand and authorize the action.\n\n"
            "Do you want to continue?"
        )

        logger.info(
            "SECURITY | Confirmation requested | %s",
            tool_name
        )

        with _confirmation_lock:

            result = ctypes.windll.user32.MessageBoxW(
                None,
                message,
                "ASTRA | Security Confirmation",

                0x00000004 |  # Yes / No
                0x00000030 |  # Warning icon
                0x00000100 |  # Default button: No
                0x00040000    # Foreground window
            )

        approved = result == 6

        logger.info(
            "SECURITY | Tool: %s | Decision: %s",
            tool_name,
            "APPROVED" if approved else "DENIED"
        )

        return approved

    except Exception:

        logger.exception(
            "SECURITY | Confirmation failed"
        )

        # Fail closed.
        return False


# ASTRA PERMISSION AUDIT INTEGRATION

from security.audit_logger import log_security_event

_original_request_user_confirmation = request_user_confirmation


def request_user_confirmation(tool_name, arguments=None):
    """Request authorization and audit the permission decision."""

    try:

        approved = (
            _original_request_user_confirmation(
                tool_name,
                arguments
            ) is True
        )

    except Exception:

        log_security_event(
            "security_error",
            tool_name,
            "failed"
        )

        return False

    if approved:

        log_security_event(
            "permission_granted",
            tool_name,
            "success"
        )

    else:

        log_security_event(
            "permission_denied",
            tool_name,
            "denied"
        )

    return approved
