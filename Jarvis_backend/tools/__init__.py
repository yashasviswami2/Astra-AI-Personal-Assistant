from tools.app_launcher import launch_app
from tools.browser import (
    open_url,
    web_search,
    fetch_page_text
)

from .file_manager import (
    list_directory,
    read_text_file,
    write_text_file,
    delete_file_safely,
    find_pdf_files
)

from tools.screenshot import (
    take_screenshot,
    get_clipboard,
    set_clipboard
)

from .pdf_summarizer import (
    extract_pdf_text
)

from .time_tools import (
    get_current_time,
    get_current_date
)


# ==========================================
# AVAILABLE JARVIS TOOLS
# ==========================================

AVAILABLE_TOOLS = {

    # --------------------------------------
    # APPLICATIONS
    # --------------------------------------

    "launch_app": launch_app,


    # --------------------------------------
    # WEB / BROWSER
    # --------------------------------------

    "open_url": open_url,
    "web_search": web_search,
    "fetch_page_text": fetch_page_text,


    # --------------------------------------
    # FILE MANAGEMENT
    # --------------------------------------

    "list_directory": list_directory,
    "read_text_file": read_text_file,
    "write_text_file": write_text_file,
    "delete_file_safely": delete_file_safely,

    # Search for PDFs by filename
    "find_pdf_files": find_pdf_files,


    # --------------------------------------
    # SCREENSHOT / CLIPBOARD
    # --------------------------------------

    "take_screenshot": take_screenshot,
    "get_clipboard": get_clipboard,
    "set_clipboard": set_clipboard,


    # --------------------------------------
    # PDF
    # --------------------------------------

    "extract_pdf_text": extract_pdf_text,


    # --------------------------------------
    # DATE / TIME
    # --------------------------------------

    "get_current_time": get_current_time,
    "get_current_date": get_current_date,
}