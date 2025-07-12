import os
from dotenv import load_dotenv
import json
import tempfile

# Application version
APP_VERSION = "0.2.0"
APP_NAME = "Windows Whisper"

# Load environment variables from .env file
load_dotenv()

# API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
API_ENDPOINT = "https://api.openai.com/v1/audio/transcriptions"

# Recording settings
MAX_RECORDING_SECONDS = int(os.getenv("MAX_RECORDING_SECONDS", 300))
SAMPLE_RATE = int(os.getenv("SAMPLE_RATE", 16000))
CHANNELS = 1  # Mono recording
TEMP_DIR = tempfile.gettempdir()

# UI settings
UI_THEME = os.getenv("UI_THEME", "light")
UI_OPACITY = float(os.getenv("UI_OPACITY", 0.9))
OVERLAY_POSITION = "top-right"
OVERLAY_MARGIN = 100  # pixels from corner

def validate_config():
    """Validate that all required configuration is available"""
    if not OPENAI_API_KEY:
        raise ValueError("OpenAI API key is not set. Please set OPENAI_API_KEY in .env file.")
    
    return True

def get_temp_audio_path():
    """Generate a temporary path for the audio file"""
    return os.path.join(TEMP_DIR, "whisper_recording_temp.wav") 