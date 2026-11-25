from tools.app_launcher import launch_app
from tools.browser import open_url, web_search, fetch_page_text
from tools.file_manager import list_directory, read_text_file, write_text_file, delete_file_safely
from tools.screenshot import take_screenshot, get_clipboard, set_clipboard
from tools.pdf_summarizer import extract_pdf_text
from .time_tools import get_current_time

# Map of tool names to functions for dynamic agent execution
AVAILABLE_TOOLS = {
    "launch_app": launch_app,
    "open_url": open_url,
    "web_search": web_search,
    "fetch_page_text": fetch_page_text,
    "list_directory": list_directory,
    "read_text_file": read_text_file,
    "write_text_file": write_text_file,
    "delete_file_safely": delete_file_safely,
    "take_screenshot": take_screenshot,
    "get_clipboard": get_clipboard,
    "set_clipboard": set_clipboard,
    "extract_pdf_text": extract_pdf_text,
    "get_current_time": get_current_time,
}