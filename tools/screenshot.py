import time
from datetime import datetime
import pyautogui
from config import settings
from utils.logger import get_logger
import ctypes
from ctypes import wintypes

logger = get_logger()

# Native Windows Clipboard ctypes Setup
OpenClipboard = ctypes.windll.user32.OpenClipboard
OpenClipboard.argtypes = [wintypes.HWND]
OpenClipboard.restype = wintypes.BOOL

EmptyClipboard = ctypes.windll.user32.EmptyClipboard
EmptyClipboard.restype = wintypes.BOOL

GetClipboardData = ctypes.windll.user32.GetClipboardData
GetClipboardData.argtypes = [wintypes.UINT]
GetClipboardData.restype = wintypes.HANDLE

SetClipboardData = ctypes.windll.user32.SetClipboardData
SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
SetClipboardData.restype = wintypes.HANDLE

CloseClipboard = ctypes.windll.user32.CloseClipboard
CloseClipboard.restype = wintypes.BOOL

CF_UNICODETEXT = 13

GlobalAlloc = ctypes.windll.kernel32.GlobalAlloc
GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
GlobalAlloc.restype = wintypes.HGLOBAL

GlobalLock = ctypes.windll.kernel32.GlobalLock
GlobalLock.argtypes = [wintypes.HGLOBAL]
GlobalLock.restype = ctypes.c_void_p

GlobalUnlock = ctypes.windll.kernel32.GlobalUnlock
GlobalUnlock.argtypes = [wintypes.HGLOBAL]
GlobalUnlock.restype = wintypes.BOOL

GMEM_MOVEABLE = 0x0002

def take_screenshot() -> str:
    """
    Take a full-screen screenshot and save it to the screenshots directory.
    
    Returns:
        str: Success or error message.
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        filepath = settings.SCREENSHOT_DIR / filename
        
        logger.info(f"Taking screenshot, destination: {filepath}")
        screenshot = pyautogui.screenshot()
        screenshot.save(filepath)
        
        return f"Successfully took screenshot. Saved as {filename} in your screenshots folder."
    except Exception as e:
        logger.error(f"Failed to capture screenshot: {e}")
        return f"Failed to capture screenshot: {str(e)}"

def get_clipboard() -> str:
    """
    Get text content from the Windows clipboard using native Win32 API.
    
    Returns:
        str: Text content of the clipboard or status message.
    """
    if not OpenClipboard(0):
        return "Error: Could not open system clipboard."
    try:
        handle = GetClipboardData(CF_UNICODETEXT)
        if not handle:
            return "Clipboard is empty or does not contain text."
        ptr = GlobalLock(handle)
        if not ptr:
            return "Error: Could not lock clipboard memory."
        text = ctypes.c_wchar_p(ptr).value
        GlobalUnlock(handle)
        return text if text else ""
    finally:
        CloseClipboard()

def set_clipboard(text: str) -> str:
    """
    Set text content into the Windows clipboard using native Win32 API.
    
    Args:
        text (str): The text to write to clipboard.
        
    Returns:
        str: Success or error message.
    """
    if not OpenClipboard(0):
        return "Error: Could not open system clipboard."
    try:
        EmptyClipboard()
        # Calculate memory size for unicode wide character string + null terminator
        alloc_size = (len(text) + 1) * ctypes.sizeof(ctypes.c_wchar)
        h_mem = GlobalAlloc(GMEM_MOVEABLE, alloc_size)
        ptr = GlobalLock(h_mem)
        ctypes.memmove(ptr, ctypes.c_wchar_p(text), alloc_size)
        GlobalUnlock(h_mem)
        
        if not SetClipboardData(CF_UNICODETEXT, h_mem):
            return "Error: Failed to write data to clipboard."
        return "Successfully copied text to system clipboard."
    finally:
        CloseClipboard()



# ASTRA SECURITY WRAPPERS

from security.confirmation import request_user_confirmation
from utils.tool_response import tool_success, tool_error
from uuid import uuid4

MAX_CLIPBOARD_LENGTH = 2000

_original_get_clipboard = get_clipboard
_original_set_clipboard = set_clipboard


def take_screenshot():
    """Capture and save a screenshot after explicit approval."""
    try:
        directory = settings.SCREENSHOT_DIR.resolve()

        filename = (
            datetime.now().strftime("screenshot_%Y%m%d_%H%M%S_")
            + uuid4().hex[:12]
            + ".png"
        )

        filepath = directory / filename

        if not request_user_confirmation(
            "take_screenshot",
            {"destination": str(filepath)}
        ):
            return tool_error(
                "Screenshot permission denied.",
                "PERMISSION_DENIED"
            )

        directory.mkdir(parents=True, exist_ok=True)

        with pyautogui.screenshot() as image:
            with filepath.open("xb") as output:
                image.save(output, format="PNG")

        logger.info("SECURITY | Screenshot saved")

        return tool_success(
            "Screenshot captured successfully.",
            {"filename": filename, "path": str(filepath)}
        )

    except Exception as error:
        logger.error(
            "SECURITY | Screenshot failed | %s",
            type(error).__name__
        )

        return tool_error(
            "Screenshot capture failed.",
            "SCREENSHOT_ERROR"
        )


def get_clipboard():
    """Read clipboard text only after explicit approval."""
    try:
        if not request_user_confirmation(
            "get_clipboard",
            {"warning": "Clipboard text may be shared with the AI."}
        ):
            return tool_error(
                "Clipboard access denied.",
                "PERMISSION_DENIED"
            )

        result = _original_get_clipboard()

        if result.startswith("Error:"):
            return tool_error(result, "CLIPBOARD_ERROR")

        if len(result) > MAX_CLIPBOARD_LENGTH:
            return tool_error(
                "Clipboard text exceeds the permitted length.",
                "CLIPBOARD_TOO_LARGE"
            )

        logger.info("SECURITY | Clipboard read authorized")

        return tool_success(
            "Clipboard read completed.",
            {"text": result}
        )

    except Exception:
        return tool_error(
            "Clipboard read failed.",
            "CLIPBOARD_ERROR"
        )


def set_clipboard(text: str):
    """Modify clipboard text only after explicit approval."""
    try:
        if not isinstance(text, str):
            return tool_error(
                "Clipboard content must be text.",
                "INVALID_INPUT"
            )

        if len(text) > MAX_CLIPBOARD_LENGTH or "\\x00" in text:
            return tool_error(
                "Invalid clipboard content.",
                "INVALID_INPUT"
            )

        if not request_user_confirmation(
            "set_clipboard",
            {"text": text}
        ):
            return tool_error(
                "Clipboard modification denied.",
                "PERMISSION_DENIED"
            )

        result = _original_set_clipboard(text)

        if result.startswith("Error:"):
            return tool_error(result, "CLIPBOARD_ERROR")

        logger.info("SECURITY | Clipboard write authorized")

        return tool_success("Clipboard updated successfully.")

    except Exception:
        return tool_error(
            "Clipboard modification failed.",
            "CLIPBOARD_ERROR"
        )
