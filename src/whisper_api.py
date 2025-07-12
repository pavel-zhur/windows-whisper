import requests
import json
import os
import logging
import time

logger = logging.getLogger("whisper_app")

class WhisperAPI:
    """
    Client for interacting with OpenAI's Whisper API
    """
    def __init__(self, api_key, api_endpoint):
        """
        Initialize the Whisper API client
        
        Args:
            api_key (str): OpenAI API key
            api_endpoint (str): Whisper API endpoint URL
        """
        self.api_key = api_key
        self.api_endpoint = api_endpoint
        logger.debug(f"WhisperAPI initialized with endpoint: {api_endpoint}")
        
    def transcribe(self, audio_file_path, model="whisper-1", language=None, prompt=None):
        """
        Transcribe audio using Whisper API
        
        Args:
            audio_file_path (str): Path to the audio file to transcribe
            model (str): Model to use (default: whisper-1)
            language (str, optional): Language for transcription
            prompt (str, optional): Prompt for transcription
            
        Returns:
            tuple: (success, text or error message)
        """
        if not os.path.exists(audio_file_path):
            error_msg = f"Audio file not found: {audio_file_path}"
            logger.error(error_msg)
            return False, error_msg
            
        try:
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
                    "model": model,
                    "response_format": "json"
                }
                
                if language:
                    data["language"] = language
                    logger.debug(f"Using language: {language}")
                
                if prompt:
                    data["prompt"] = prompt
                    logger.debug(f"Using prompt: {prompt}")
                
                logger.info(f"Sending request to Whisper API with model: {model}")
                start_time = time.time()
                
                response = requests.post(
                    self.api_endpoint,
                    headers=headers,
                    files=files,
                    data=data
                )
                
                elapsed_time = time.time() - start_time
                logger.debug(f"API request completed in {elapsed_time:.2f} seconds")
                
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