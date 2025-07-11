import requests
import json
import logging
from config import OPENAI_API_KEY, TRANSFORMATION_PROMPT, TRANSFORMATION_MODEL

logger = logging.getLogger("whisper_app")

class TextTransformationService:
    """
    Service for transforming text using ChatGPT API (translation, tone improvement, etc.)
    """
    def __init__(self):
        self.api_key = OPENAI_API_KEY
        self.api_endpoint = "https://api.openai.com/v1/chat/completions"
        
    def transform_text(self, text):
        """
        Transform text using ChatGPT based on the configured transformation prompt
        
        Args:
            text (str): Original text to transform
            
        Returns:
            tuple: (success, transformed_text_or_error)
        """
        if not TRANSFORMATION_PROMPT:
            # No transformation requested, just return original text
            return True, text
            
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": TRANSFORMATION_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": f"{TRANSFORMATION_PROMPT}\n\nReturn ONLY the transformed text, no explanations or additional content."
                    },
                    {
                        "role": "user", 
                        "content": text
                    }
                ],
                "max_tokens": 500,
                "temperature": 0.3  # Lower temperature for more consistent results
            }
            
            logger.info(f"Transforming text using prompt: {TRANSFORMATION_PROMPT[:50]}...")
            
            response = requests.post(
                self.api_endpoint,
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                transformed_text = result["choices"][0]["message"]["content"].strip()
                logger.info(f"Text transformation successful: {len(transformed_text)} chars")
                return True, transformed_text
            else:
                error_msg = f"Transformation API Error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Text transformation error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
