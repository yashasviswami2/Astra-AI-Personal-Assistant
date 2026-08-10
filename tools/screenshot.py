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
