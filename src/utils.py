import os
import sys
import logging
import tempfile
import time
from datetime import datetime

class ColoredConsoleFormatter(logging.Formatter):
    """Custom formatter that colors specific messages"""
    
    GRAY = '\033[90m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    
    def format(self, record):
        # Format the message using parent formatter
        formatted = super().format(record)
        
        # Check if this is a transcription or transformation message
        msg = record.getMessage()
        if any(keyword in msg for keyword in ['Transcribed:', 'Transformed:', 'Starting auto-type for:']):
            # White for transcribed/transformed content
            return f"{self.WHITE}{formatted}{self.RESET}"
        else:
            # Gray for everything else
            return f"{self.GRAY}{formatted}{self.RESET}"

def setup_logging(log_level=logging.DEBUG):
    """
    Set up logging configuration
    
    Args:
        log_level: Logging level (default: INFO)
        
    Returns:
        logger: Configured logger
    """
    logger = logging.getLogger("whisper_app")
    logger.setLevel(log_level)
    
    # Create formatters
    plain_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    colored_formatter = ColoredConsoleFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create console handler with colored formatter
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(colored_formatter)
    
    # Create file handler with plain formatter
    log_file = os.path.join(tempfile.gettempdir(), "whisper_app.log")
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(plain_formatter)
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    logger.info(f"Logging initialized. Log file: {log_file}")
    return logger
    
def get_resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller
    
    Args:
        relative_path (str): Path relative to the script
        
    Returns:
        str: Absolute path to resource
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
        
    return os.path.join(base_path, relative_path)
    
def clean_temp_files(file_paths, max_age_seconds=3600):
    """
    Clean up temporary files
    
    Args:
        file_paths (list): List of file paths to check and potentially delete
        max_age_seconds (int): Maximum age in seconds (default: 1 hour)
        
    Returns:
        int: Number of files deleted
    """
    deleted_count = 0
    current_time = time.time()
    
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                file_age = current_time - os.path.getmtime(file_path)
                
                if file_age > max_age_seconds:
                    os.remove(file_path)
                    deleted_count += 1
        except Exception as e:
            logging.error(f"Error deleting temporary file {file_path}: {e}")
            
    return deleted_count
    
def format_time_duration(seconds):
    """
    Format time duration in seconds to a human-readable string
    
    Args:
        seconds (float): Duration in seconds
        
    Returns:
        str: Formatted duration string
    """
    minutes, seconds = divmod(int(seconds), 60)
    if minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s" 