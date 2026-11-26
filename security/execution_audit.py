from security.audit_logger import log_security_event


def audit_tool_result(tool_name, result):
    """Audit a tool result without recording private content."""

    if not isinstance(result, dict):
        return False

    status = result.get("status")
    error_code = result.get("error_code")

    if (
        status == "permission_denied"
        or error_code == "PERMISSION_DENIED"
    ):
        return log_security_event(
            "permission_denied",
            tool_name,
            "denied"
        )

    if error_code == "ACCESS_DENIED":
        return log_security_event(
            "access_blocked",
            tool_name,
            "blocked"
        )

    if result.get("success") is True:
        return log_security_event(
            "tool_executed",
            tool_name,
            "success"
        )

    if result.get("success") is False:
        return log_security_event(
            "tool_failed",
            tool_name,
            "failed"
        )

    return log_security_event(
        "tool_executed",
        tool_name,
        "pending"
    )
