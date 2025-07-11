import requests
import json
import os
import logging
import time
from config import WHISPER_LANGUAGE, WHISPER_PROMPT

logger = logging.getLogger("whisper_app")

class WhisperAPI:
    """
    Client for interacting with OpenAI's Whisper API
    """
    def __init__(self, api_key, api_endpoint, model="whisper-1"):
        """
        Initialize the Whisper API client
        
        Args:
            api_key (str): OpenAI API key
            api_endpoint (str): Whisper API endpoint URL
            model (str): Whisper model to use (default: whisper-1)
        """
        self.api_key = api_key
        self.api_endpoint = api_endpoint
        self.model = model  # Use the specified model
        logger.debug(f"WhisperAPI initialized with endpoint: {api_endpoint}, model: {self.model}")
        
        # Debug the prompt loading
        logger.info(f"WHISPER_PROMPT loaded from config: '{WHISPER_PROMPT}'")
        logger.info(f"WHISPER_LANGUAGE loaded from config: '{WHISPER_LANGUAGE}'")
        
    def transcribe(self, audio_file_path):
        """
        Transcribe audio using Whisper API
        
        Args:
            audio_file_path (str): Path to the audio file to transcribe
            
        Returns:
            tuple: (success, text or error message)
        """
        if not os.path.exists(audio_file_path):
            error_msg = f"Audio file not found: {audio_file_path}"
            logger.error(error_msg)
            return False, error_msg
            
        try:
            # Log file details
            file_size = os.path.getsize(audio_file_path)
            logger.debug(f"Processing audio file: {audio_file_path} (size: {file_size/1024:.1f} KB)")
            
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }
            
            with open(audio_file_path, "rb") as audio_file:
                files = {
                    "file": (os.path.basename(audio_file_path), audio_file, "audio/wav")
                }
                
                data = {
                    "model": self.model,
                    "response_format": "json"
                }
                
                # Only add language if it's explicitly set
                if WHISPER_LANGUAGE:
                    data["language"] = WHISPER_LANGUAGE
                    logger.info(f"Using language setting: {WHISPER_LANGUAGE}")
                else:
                    logger.info("No language specified - OpenAI will auto-detect and not translate")
                
                # Only add prompt if it's explicitly set
                logger.info(f"Checking WHISPER_PROMPT value: '{WHISPER_PROMPT}' (type: {type(WHISPER_PROMPT)})")
                if WHISPER_PROMPT:
                    data["prompt"] = WHISPER_PROMPT
                    logger.info(f"Using custom prompt: {WHISPER_PROMPT}")
                else:
                    logger.info("No custom prompt - using OpenAI defaults")
                
                logger.info(f"Sending request to Whisper API with model: {self.model}")
                start_time = time.time()
                
                response = requests.post(
                    self.api_endpoint,
                    headers=headers,
                    files=files,
                    data=data
                )
                
                elapsed_time = time.time() - start_time
                logger.debug(f"API request completed in {elapsed_time:.2f} seconds with status code: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    transcription = result.get("text", "").strip()
                    logger.info(f"Transcription successful: {len(transcription)} chars")
                    logger.debug(f"First 100 chars of transcription: {transcription[:100]}...")
                    return True, transcription
                else:
                    error_msg = f"API Error: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    return False, error_msg
                    
        except Exception as e:
            error_msg = f"Transcription error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
            
    def get_usage_info(self):
        """Get current Whisper API usage information (placeholder - not implemented)"""
        # This would require additional API calls to OpenAI's usage endpoints
        # Left as placeholder for potential future implementation
        return {
            "available": True,
            "usage": "Unknown"
        } 