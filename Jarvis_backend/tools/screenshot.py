import time
from datetime import datetime
import pyautogui

from config import settings
from utils.logger import get_logger

import ctypes
from ctypes import wintypes


logger = get_logger()


# ==========================================
# WINDOWS CLIPBOARD SETUP
# ==========================================

OpenClipboard = ctypes.windll.user32.OpenClipboard
OpenClipboard.argtypes = [wintypes.HWND]
OpenClipboard.restype = wintypes.BOOL

EmptyClipboard = ctypes.windll.user32.EmptyClipboard
EmptyClipboard.restype = wintypes.BOOL

GetClipboardData = ctypes.windll.user32.GetClipboardData
GetClipboardData.argtypes = [wintypes.UINT]
GetClipboardData.restype = wintypes.HANDLE

SetClipboardData = ctypes.windll.user32.SetClipboardData
SetClipboardData.argtypes = [
    wintypes.UINT,
    wintypes.HANDLE
]
SetClipboardData.restype = wintypes.HANDLE

CloseClipboard = ctypes.windll.user32.CloseClipboard
CloseClipboard.restype = wintypes.BOOL

CF_UNICODETEXT = 13

GlobalAlloc = ctypes.windll.kernel32.GlobalAlloc
GlobalAlloc.argtypes = [
    wintypes.UINT,
    ctypes.c_size_t
]
GlobalAlloc.restype = wintypes.HGLOBAL

GlobalLock = ctypes.windll.kernel32.GlobalLock
GlobalLock.argtypes = [wintypes.HGLOBAL]
GlobalLock.restype = ctypes.c_void_p

GlobalUnlock = ctypes.windll.kernel32.GlobalUnlock
GlobalUnlock.argtypes = [wintypes.HGLOBAL]
GlobalUnlock.restype = wintypes.BOOL

GMEM_MOVEABLE = 0x0002


# ==========================================
# TAKE SCREENSHOT
# ==========================================

def take_screenshot() -> str:
    """
    Capture the full screen and save it to
    the configured JARVIS screenshots directory.

    Returns:
        str: Detailed success or error message.
    """

    try:

        # Make sure the screenshots directory exists
        settings.SCREENSHOT_DIR.mkdir(
            parents=True,
            exist_ok=True
        )


        # Generate unique timestamp
        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )


        filename = (
            f"screenshot_{timestamp}.png"
        )


        filepath = (
            settings.SCREENSHOT_DIR /
            filename
        )


        logger.info(
            f"Taking screenshot..."
        )

        logger.info(
            f"Screenshot destination: {filepath}"
        )


        # Capture screen
        screenshot = pyautogui.screenshot()


        # Save screenshot
        screenshot.save(filepath)


        # Verify that the file was actually created
        if not filepath.exists():

            logger.error(
                "Screenshot command completed but "
                "file was not found."
            )

            return (
                "Screenshot capture failed. "
                "The image file could not be verified."
            )


        # Get absolute path
        absolute_path = filepath.resolve()


        logger.info(
            f"Screenshot captured successfully: "
            f"{absolute_path}"
        )


        return (
            "Screenshot captured successfully. "
            f"Saved at: {absolute_path}"
        )


    except Exception as e:

        logger.error(
            f"Failed to capture screenshot: {e}",
            exc_info=True
        )


        return (
            "Failed to capture screenshot. "
            f"Reason: {str(e)}"
        )


# ==========================================
# GET CLIPBOARD
# ==========================================

def get_clipboard() -> str:
    """
    Get text content from the Windows clipboard.

    Returns:
        str: Clipboard text or status message.
    """

    if not OpenClipboard(0):

        return (
            "Error: Could not open system clipboard."
        )


    try:

        handle = GetClipboardData(
            CF_UNICODETEXT
        )


        if not handle:

            return (
                "Clipboard is empty or "
                "does not contain text."
            )


        ptr = GlobalLock(handle)


        if not ptr:

            return (
                "Error: Could not lock "
                "clipboard memory."
            )


        text = ctypes.c_wchar_p(
            ptr
        ).value


        GlobalUnlock(handle)


        return text if text else ""


    finally:

        CloseClipboard()


# ==========================================
# SET CLIPBOARD
# ==========================================

def set_clipboard(text: str) -> str:
    """
    Set text into the Windows clipboard.

    Args:
        text (str): Text to copy.

    Returns:
        str: Success or error message.
    """

    if not OpenClipboard(0):

        return (
            "Error: Could not open system clipboard."
        )


    try:

        EmptyClipboard()


        # Calculate memory required
        alloc_size = (
            (len(text) + 1)
            * ctypes.sizeof(ctypes.c_wchar)
        )


        h_mem = GlobalAlloc(
            GMEM_MOVEABLE,
            alloc_size
        )


        if not h_mem:

            return (
                "Error: Could not allocate "
                "clipboard memory."
            )


        ptr = GlobalLock(h_mem)


        if not ptr:

            return (
                "Error: Could not lock "
                "clipboard memory."
            )


        ctypes.memmove(
            ptr,
            ctypes.c_wchar_p(text),
            alloc_size
        )


        GlobalUnlock(h_mem)


        if not SetClipboardData(
            CF_UNICODETEXT,
            h_mem
        ):

            return (
                "Error: Failed to write "
                "data to clipboard."
            )


        return (
            "Successfully copied text "
            "to system clipboard."
        )


    finally:

        CloseClipboard()