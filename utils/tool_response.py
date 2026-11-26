def tool_success(message, data=None):
    """Create a standardized successful tool response."""

    return {
        "success": True,
        "status": "success",
        "message": str(message),
        "data": data
    }


def tool_error(message, code="TOOL_ERROR"):
    """Create a standardized failed tool response."""

    return {
        "success": False,
        "status": "error",
        "message": str(message),
        "error_code": code
    }


def normalize_tool_response(result):
    """Support structured responses and existing legacy tools."""

    if isinstance(result, dict):

        if isinstance(result.get("success"), bool):
            return result

    if result is None:

        return tool_error(
            "The tool returned no result.",
            "EMPTY_RESPONSE"
        )

    return {
        "success": None,
        "status": "unverified",
        "message": str(result)
    }
