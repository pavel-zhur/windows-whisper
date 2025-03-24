import requests
import json
import os
import logging
import time

logger = logging.getLogger(__name__)

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
        self.model = "whisper-1"  # Enforcing whisper-1 as it's the only available API model
        
    def transcribe(self, audio_file_path, language=None):
        """
        Transcribe audio using Whisper API
        
        Args:
            audio_file_path (str): Path to the audio file to transcribe
            language (str, optional): Language code (e.g., 'en')
            
        Returns:
            tuple: (success, text or error message)
        """
        if not os.path.exists(audio_file_path):
            error_msg = f"Audio file not found: {audio_file_path}"
            logger.error(error_msg)
            return False, error_msg
            
        try:
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
                
                if language:
                    data["language"] = language
                    
                logger.info(f"Sending request to Whisper API with model: {self.model}")
                start_time = time.time()
                
                response = requests.post(
                    self.api_endpoint,
                    headers=headers,
                    files=files,
                    data=data
                )
                
                elapsed_time = time.time() - start_time
                logger.info(f"API request completed in {elapsed_time:.2f} seconds")
                
                if response.status_code == 200:
                    result = response.json()
                    transcription = result.get("text", "").strip()
                    logger.info(f"Transcription successful: {len(transcription)} chars")
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