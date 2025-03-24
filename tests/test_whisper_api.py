import unittest
import os
import tempfile
from unittest.mock import MagicMock, patch
from src.whisper_api import WhisperAPI

class TestWhisperAPI(unittest.TestCase):
    """Test cases for the WhisperAPI class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.api_key = "test_api_key"
        self.api_endpoint = "https://api.example.com/whisper"
        self.model = "whisper-test"
        self.whisper_api = WhisperAPI(self.api_key, self.api_endpoint, self.model)
        
    def test_initialization(self):
        """Test initialization of WhisperAPI"""
        self.assertEqual(self.whisper_api.api_key, self.api_key)
        self.assertEqual(self.whisper_api.api_endpoint, self.api_endpoint)
        self.assertEqual(self.whisper_api.model, self.model)
        
    def test_transcribe_file_not_found(self):
        """Test transcription when file doesn't exist"""
        non_existent_file = "/path/to/non_existent_file.wav"
        success, error = self.whisper_api.transcribe(non_existent_file)
        
        self.assertFalse(success)
        self.assertIn("not found", error)
        
    @patch('requests.post')
    def test_transcribe_success(self, mock_post):
        """Test successful transcription"""
        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        temp_file.close()
        
        try:
            # Mock successful API response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"text": "This is a test transcription"}
            mock_post.return_value = mock_response
            
            # Call the method
            success, text = self.whisper_api.transcribe(temp_file.name)
            
            # Assertions
            self.assertTrue(success)
            self.assertEqual(text, "This is a test transcription")
            mock_post.assert_called_once()
            
        finally:
            # Clean up
            os.unlink(temp_file.name)
            
    @patch('requests.post')
    def test_transcribe_api_error(self, mock_post):
        """Test API error during transcription"""
        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        temp_file.close()
        
        try:
            # Mock error API response
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.text = "Bad Request"
            mock_post.return_value = mock_response
            
            # Call the method
            success, error = self.whisper_api.transcribe(temp_file.name)
            
            # Assertions
            self.assertFalse(success)
            self.assertIn("API Error", error)
            self.assertIn("400", error)
            mock_post.assert_called_once()
            
        finally:
            # Clean up
            os.unlink(temp_file.name)
            
if __name__ == "__main__":
    unittest.main() 