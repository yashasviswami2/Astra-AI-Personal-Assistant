import subprocess
import os
import shutil
from config import settings
from utils.logger import get_logger

logger = get_logger()

def launch_app(app_name: str) -> str:
    """
    Launch a local application on Windows.
    
    Args:
        app_name (str): Name of the application (e.g., 'notepad', 'chrome', 'vs code').
        
    Returns:
        str: Status message indicating success or failure.
    """
    app_name_lower = app_name.lower().strip()
    logger.info(f"Attempting to launch application: '{app_name_lower}'")
    
    # Check against explicit settings configuration
    for key, path in settings.ALLOWED_APP_LAUNCHES.items():
        if key in app_name_lower or app_name_lower in key:
            try:
                # If path is on system PATH, attempt to resolve it
                executable = path
                if not os.path.isabs(path):
                    resolved = shutil.which(path)
                    if resolved:
                        executable = resolved
                    else:
                        # Attempt direct execution via shell
                        subprocess.Popen(path, shell=True, close_fds=True, start_new_session=True)
                        return f"Successfully launched {key}."
                
                # Enforce file extension safety
                if executable.endswith(('.bat', '.cmd', '.vbs', '.js', '.sh', '.ps1')):
                    logger.warning(f"Safety Block: Prevented execution of scripted binary: {executable}")
                    return f"Execution of script {os.path.basename(executable)} is blocked for safety."
                
                logger.info(f"Spawning background process for: {executable}")
                subprocess.Popen([executable], close_fds=True, start_new_session=True)
                return f"Successfully launched {key}."
            except Exception as e:
                logger.error(f"Error launching {key}: {e}")
                return f"Failed to launch {key}: {str(e)}"
    
    # If not explicitly configured, try to resolve via system PATH
    # Strip dangerous characters to prevent shell injection
    clean_name = "".join(c for c in app_name_lower if c.isalnum() or c in "._- ")
    if not clean_name:
        return "Invalid application name provided."
        
    if clean_name.endswith(('.bat', '.cmd', '.vbs', '.js', '.sh', '.ps1')):
        return "Execution of script files is blocked for security reasons."
        
    # Search system PATH for the binary
    resolved = shutil.which(clean_name) or shutil.which(clean_name + ".exe")
    if resolved:
        try:
            logger.info(f"Spawning PATH resolved binary: {resolved}")
            subprocess.Popen([resolved], close_fds=True, start_new_session=True)
            return f"Successfully launched {clean_name}."
        except Exception as e:
            return f"Failed to launch {clean_name} from PATH: {str(e)}"
            
    # Try running via cmd shell for general command matching (restricted to pure alphanumeric keys)
    if clean_name.isalnum():
        try:
            logger.info(f"Attempting to start '{clean_name}' via Windows start shell.")
            subprocess.Popen(f"start {clean_name}", shell=True, close_fds=True, start_new_session=True)
            return f"Attempted to launch {clean_name} via Windows shell."
        except Exception as e:
            return f"Failed to run shell command: {str(e)}"

    return f"Could not find or launch application '{app_name}'. You can add it to config/settings.py."
