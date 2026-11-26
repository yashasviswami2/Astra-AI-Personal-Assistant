from enum import Enum


class PermissionLevel(str, Enum):

    SAFE = "safe"
    SENSITIVE = "sensitive"
    RESTRICTED = "restricted"


TOOL_PERMISSIONS = {

    # Desktop tools
    "get_current_time": PermissionLevel.SAFE,
    "launch_app": PermissionLevel.SENSITIVE,
    "open_url": PermissionLevel.SENSITIVE,

    # File operations
    "list_directory": PermissionLevel.SENSITIVE,
    "read_text_file": PermissionLevel.SENSITIVE,
    "write_text_file": PermissionLevel.RESTRICTED,
    "delete_file_safely": PermissionLevel.RESTRICTED,
    "extract_pdf_text": PermissionLevel.SENSITIVE,

    # Privacy-sensitive tools
    "take_screenshot": PermissionLevel.RESTRICTED,
    "analyze_screen": PermissionLevel.RESTRICTED,
    "get_clipboard": PermissionLevel.SENSITIVE,
    "set_clipboard": PermissionLevel.SENSITIVE,

    # Automation
    "start_study_mode": PermissionLevel.SENSITIVE,
    "start_coding_mode": PermissionLevel.SENSITIVE,
    "start_research_mode": PermissionLevel.SENSITIVE,
    "execute_custom_workflow": PermissionLevel.RESTRICTED,

    # Personal memory
    "remember_information": PermissionLevel.SENSITIVE,
    "recall_information": PermissionLevel.SENSITIVE,
    "forget_information": PermissionLevel.RESTRICTED,

    # Academic records
    "list_subjects": PermissionLevel.SAFE,
    "list_assignments": PermissionLevel.SAFE,
    "list_exams": PermissionLevel.SAFE,
    "delete_study_session": PermissionLevel.RESTRICTED,
    "delete_quiz_result": PermissionLevel.RESTRICTED,

    # System monitoring
    "get_system_status": PermissionLevel.SAFE,
    "get_battery_status": PermissionLevel.SAFE,
    "get_system_information": PermissionLevel.SENSITIVE,
}


def get_tool_permission(tool_name):

    return TOOL_PERMISSIONS.get(
        tool_name,
        PermissionLevel.RESTRICTED
    )


def requires_confirmation(tool_name):

    return get_tool_permission(tool_name) in (
        PermissionLevel.SENSITIVE,
        PermissionLevel.RESTRICTED
    )


def get_permission_summary():

    return {
        name: level.value
        for name, level in TOOL_PERMISSIONS.items()
    }