import sys
import time
from PyQt5 import QtWidgets, QtCore
from main import WhisperApp
from config import SHORTCUT_KEY
import keyboard
import logging

logger = logging.getLogger(__name__)

class IntegrationTest:
    """Test the complete workflow integration"""
    
    def __init__(self):
        """Initialize the test"""
        self.app = QtWidgets.QApplication(sys.argv)
        self.whisper_app = None
        
    def simulate_workflow(self):
        """Simulate a complete recording workflow"""
        print("Starting integration test...")
        print(f"* Creating WhisperApp instance")
        
        try:
            # Create WhisperApp instance
            self.whisper_app = WhisperApp()
            
            # Wait a bit for initialization
            time.sleep(2)
            
            print(f"\n* Simulating workflow:")
            print(f"1. Press {SHORTCUT_KEY} to start recording")
            print("2. Wait 3 seconds")
            print("3. Click 'Done' to stop recording")
            print("4. Wait for transcription")
            print("5. Check clipboard")
            print("\nStarting in 3 seconds...")
            time.sleep(3)
            
            # Simulate hotkey press
            print(f"\n* Simulating {SHORTCUT_KEY} press...")
            keyboard.press('ctrl')
            time.sleep(0.1)  # Small delay between key presses
            keyboard.press('space')
            time.sleep(0.1)  # Hold for a moment
            keyboard.release('space')
            keyboard.release('ctrl')
            
            # Wait for overlay to appear
            time.sleep(1)
            print("* Checking for recording overlay...")
            
            # Find and verify overlay
            overlay = self.whisper_app.recording_overlay
            if not overlay:
                print("Error: Recording overlay is None!")
                return False
            
            if not overlay.isVisible():
                print("Error: Recording overlay is not visible!")
                return False
                
            print("* Recording overlay found and visible")
            
            # Wait for recording
            print("* Recording for 3 seconds...")
            time.sleep(3)
            
            # Click the Done button
            print("* Clicking 'Done' button...")
            QtCore.QTimer.singleShot(100, overlay.done_btn.click)
            
            # Wait for processing
            print("* Waiting for transcription...")
            time.sleep(5)
            
            return True
            
        except Exception as e:
            print(f"Error during test: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    def run(self):
        """Run the integration test"""
        try:
            success = self.simulate_workflow()
            
            if success:
                print("\nTest completed successfully!")
                print("* Check your clipboard for the transcription")
            else:
                print("\nTest failed!")
                
            # Keep the application running for a bit to see results
            QtCore.QTimer.singleShot(5000, self.app.quit)
            return self.app.exec_()
            
        except KeyboardInterrupt:
            print("\nTest interrupted by user")
            return 1
        finally:
            if self.whisper_app:
                self.whisper_app.cleanup()

def main():
    """Main entry point"""
    test = IntegrationTest()
    sys.exit(test.run())

if __name__ == "__main__":
    main() 