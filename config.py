import os
from dotenv import load_dotenv
import json
import tempfile

# Load environment variables from .env file
load_dotenv()

# API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Recording settings
MAX_RECORDING_SECONDS = int(os.getenv("MAX_RECORDING_SECONDS", 300))
SAMPLE_RATE = int(os.getenv("SAMPLE_RATE", 16000))
CHANNELS = 1  # Mono recording
TEMP_DIR = tempfile.gettempdir()

# Whisper API settings
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "whisper-1") 
API_ENDPOINT = "https://api.openai.com/v1/audio/transcriptions"

# UI settings
UI_THEME = os.getenv("UI_THEME", "light")
UI_OPACITY = float(os.getenv("UI_OPACITY", 0.9))

# Hotkey settings
SHORTCUT_KEY = "ctrl+space"

def validate_config():
    """Validate that all required configuration is available"""
    if not OPENAI_API_KEY:
        raise ValueError("OpenAI API key is not set. Please set OPENAI_API_KEY in .env file.")
    
    return True

def get_temp_audio_path():
    """Generate a temporary path for the audio file"""
    return os.path.join(TEMP_DIR, "whisper_recording_temp.wav") 