import unittest
import os
import tempfile
from src.audio import AudioRecorder

class TestAudioRecorder(unittest.TestCase):
    """Test cases for the AudioRecorder class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.recorder = AudioRecorder(sample_rate=16000, channels=1)
        self.temp_dir = tempfile.gettempdir()
        
    def test_initialization(self):
        """Test initialization of AudioRecorder"""
        self.assertEqual(self.recorder.sample_rate, 16000)
        self.assertEqual(self.recorder.channels, 1)
        self.assertFalse(self.recorder.is_recording)
        
    def test_start_stop_recording(self):
        """Test starting and stopping recording"""
        # Start recording
        result = self.recorder.start_recording(max_seconds=1)
        self.assertTrue(result)
        self.assertTrue(self.recorder.is_recording)
        
        # Stop recording
        result = self.recorder.stop_recording()
        self.assertTrue(result)
        self.assertFalse(self.recorder.is_recording)
        
    def test_save_wav_empty(self):
        """Test saving when no frames are available"""
        temp_file = os.path.join(self.temp_dir, "test_empty.wav")
        result = self.recorder.save_wav(temp_file)
        self.assertFalse(result)
        
        # Clean up
        if os.path.exists(temp_file):
            os.remove(temp_file)
            
if __name__ == "__main__":
    unittest.main() 