from datetime import datetime


def get_current_time() -> str:
    """Get the current date and time from the user's computer."""
    now = datetime.now()

    return now.strftime(
        "The current time is %I:%M %p."
    )


def get_current_date() -> str:
    """Get the current date from the user's computer."""
    now = datetime.now()

    return now.strftime(
        "Today is %A, %d %B %Y."
    )