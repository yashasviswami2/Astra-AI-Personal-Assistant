import os
import ctypes
from pathlib import Path
from utils.logger import get_logger
from config import settings

logger = get_logger()

# Define allowed user-space directories
USER_HOME = Path.expanduser(Path("~"))
SAFE_ROOTS = [
    USER_HOME / "Documents",
    USER_HOME / "Desktop",
    USER_HOME / "Downloads",
    Path("c:/Users/acer/Personal_Assistant")
]

def request_user_confirmation(action: str) -> bool:
    """
    Spawns a native Windows system modal confirmation dialog box.
    Blocks until user interacts.
    """
    try:
        logger.info(f"Security confirmation requested for: '{action}'")
        # MB_YESNO = 0x00000004, MB_ICONQUESTION = 0x00000020, MB_SYSTEMMODAL = 0x00001000
        # IDYES = 6
        result = ctypes.windll.user32.MessageBoxW(
            0,
            f"ASTRA is requesting permission to:\n\n--> {action}\n\nDo you want to allow this action?",
            "ASTRA - Security Confirmation",
            4 | 32 | 4000
        )
        approved = (result == 6)
        logger.info(f"Security confirmation result: {approved}")
        return approved
    except Exception as e:
        logger.error(f"Failed to show native MB: {e}")
        # PyAutoGUI fallback
        try:
            import pyautogui
            res = pyautogui.confirm(
                text=f"Allow ASTRA to:\n{action}?",
                title="ASTRA Security Check",
                buttons=["Yes", "No"]
            )
            return res == "Yes"
        except Exception as py_err:
            logger.error(f"PyAutoGUI fallback also failed: {py_err}")
            return False

def resolve_and_verify_path(path_str: str) -> Path:
    """
    Resolves a path string and verifies if it is within safe directories.
    Raises PermissionError if path is unsafe.
    """
    # Replace common placeholders
    path_str = path_str.replace("Desktop", str(USER_HOME / "Desktop"))
    path_str = path_str.replace("Documents", str(USER_HOME / "Documents"))
    path_str = path_str.replace("Downloads", str(USER_HOME / "Downloads"))
    
    target_path = Path(path_str).resolve()
    
    # Check if target_path is inside any of the SAFE_ROOTS
    for root in SAFE_ROOTS:
        if root.exists():
            resolved_root = root.resolve()
            # Target path must start with or be equal to a resolved safe root
            if target_path == resolved_root or resolved_root in target_path.parents:
                return target_path
                
    # Raise exception if unsafe
    logger.warning(f"Safety Block: Unsafe path access attempted: '{target_path}'")
    raise PermissionError(f"Access to path '{path_str}' is restricted for system safety.")

def list_directory(directory_path: str = None) -> str:
    """
    List files and folders in a specified directory.
    
    Args:
        directory_path (str, optional): The folder path. Defaults to Desktop.
        
    Returns:
        str: List of files/folders or error message.
    """
    if not directory_path:
        directory_path = str(USER_HOME / "Desktop")
        
    try:
        safe_path = resolve_and_verify_path(directory_path)
        if not safe_path.exists():
            return f"Directory does not exist: {directory_path}"
        if not safe_path.is_dir():
            return f"Path is not a directory: {directory_path}"
            
        items = os.listdir(safe_path)
        if not items:
            return f"Directory '{safe_path.name}' is empty."
            
        # Format output
        output = [f"Contents of {safe_path}:"]
        for item in items:
            item_path = safe_path / item
            prefix = "[DIR] " if item_path.is_dir() else "[FILE]"
            output.append(f"  {prefix} {item}")
        return "\n".join(output)
    except PermissionError as pe:
        return str(pe)
    except Exception as e:
        logger.error(f"Error listing directory {directory_path}: {e}")
        return f"Error listing directory: {str(e)}"

def read_text_file(file_path: str) -> str:
    """
    Read the contents of a text file.
    
    Args:
        file_path (str): Path to the text file.
        
    Returns:
        str: File content or error message.
    """
    try:
        safe_path = resolve_and_verify_path(file_path)
        if not safe_path.exists():
            return f"File not found: {file_path}"
        if not safe_path.is_file():
            return f"Path is not a file: {file_path}"
            
        # Limit read to 100KB to save memory
        size = safe_path.stat().st_size
        if size > 102400:
            return f"File is too large ({size} bytes). Max read limit is 100KB."
            
        with open(safe_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        return f"--- Content of {safe_path.name} ---\n{content}"
    except PermissionError as pe:
        return str(pe)
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return f"Error reading file: {str(e)}"

def write_text_file(file_path: str, content: str) -> str:
    """
    Write or overwrite text content to a file.
    
    Args:
        file_path (str): Target path.
        content (str): Content to write.
        
    Returns:
        str: Status message.
    """
    try:
        safe_path = resolve_and_verify_path(file_path)
        
        # Security Prompt
        action_msg = f"Write file '{safe_path.name}' at:\n{safe_path.parent}"
        if settings.SAFE_EXECUTION_MODE and not request_user_confirmation(action_msg):
            return "Action cancelled by user: Write operation declined."
            
        # Ensure directories exist
        safe_path.parent.mkdir(parents=True, exist_ok=True)
        with open(safe_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Successfully wrote file: {safe_path}")
        return f"Successfully wrote file to {safe_path.name}."
    except PermissionError as pe:
        return str(pe)
    except Exception as e:
        logger.error(f"Error writing file {file_path}: {e}")
        return f"Error writing file: {str(e)}"

def delete_file_safely(file_path: str) -> str:
    """
    Delete a file after explicit user confirmation.
    
    Args:
        file_path (str): File path to delete.
        
    Returns:
        str: Status message.
    """
    try:
        safe_path = resolve_and_verify_path(file_path)
        if not safe_path.exists():
            return f"File does not exist: {file_path}"
        if not safe_path.is_file():
            return f"Path is not a file: {file_path}"
            
        # Security Prompt (Always active for deletes, even if safe mode is disabled)
        action_msg = f"Permanently DELETE file:\n{safe_path}"
        if not request_user_confirmation(action_msg):
            return "Action cancelled by user: Delete operation declined."
            
        safe_path.unlink()
        logger.info(f"Deleted file: {safe_path}")
        return f"Successfully deleted file {safe_path.name}."
    except PermissionError as pe:
        return str(pe)
    except Exception as e:
        logger.error(f"Error deleting file {file_path}: {e}")
        return f"Error deleting file: {str(e)}"
