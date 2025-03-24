from src.audio import AudioRecorder
import time
import os

def test_audio_recorder():
    """Test the AudioRecorder class functionality"""
    
    # Create recorder instance
    recorder = AudioRecorder(sample_rate=16000, channels=1)
    output_file = "module_test_recording.wav"
    
    try:
        print("Testing AudioRecorder module...")
        
        # Test starting recording
        print("* Starting recording (3 seconds)...")
        if not recorder.start_recording(max_seconds=3):
            print("Failed to start recording!")
            return
            
        # Record for 3 seconds
        time.sleep(3)
        
        # Stop recording
        print("* Stopping recording...")
        if not recorder.stop_recording():
            print("Failed to stop recording!")
            return
            
        # Save the recording
        print(f"* Saving to {output_file}...")
        if not recorder.save_wav(output_file):
            print("Failed to save recording!")
            return
            
        print("* Success! Recording saved.")
        print(f"* File size: {os.path.getsize(output_file)} bytes")
        
    finally:
        # Clean up
        if os.path.exists(output_file):
            os.remove(output_file)
            print("* Cleaned up test file")

if __name__ == "__main__":
    test_audio_recorder() 