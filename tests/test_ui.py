import sys
from PyQt5 import QtWidgets
from src.ui.overlay import RecordingOverlay, show_notification
import time

class TestUI:
    """Test the UI overlay functionality"""
    
    def __init__(self):
        """Initialize the test"""
        self.app = QtWidgets.QApplication(sys.argv)
        self.overlay = None
        
    def test_recording_overlay(self):
        """Test the recording overlay"""
        print("Testing recording overlay...")
        
        # Create and show overlay
        self.overlay = RecordingOverlay()
        
        # Connect signals
        self.overlay.recording_done.connect(self.on_recording_done)
        self.overlay.recording_cancelled.connect(self.on_recording_cancelled)
        
        # Show the overlay
        self.overlay.show()
        print("* Overlay shown - you should see it on screen")
        print("* Try:")
        print("  - Dragging the overlay window")
        print("  - Clicking 'Done' button")
        print("  - Clicking 'X' to cancel")
        print("  - Observe the blinking recording indicator")
        
    def test_notification(self):
        """Test notifications"""
        print("\nTesting notifications...")
        
        # Show different types of notifications
        show_notification("Info notification", "info", 2000)
        time.sleep(2.5)
        
        show_notification("Success notification", "success", 2000)
        time.sleep(2.5)
        
        show_notification("Error notification", "error", 2000)
        time.sleep(2.5)
        
    def test_transcription_result(self):
        """Test showing transcription results"""
        if self.overlay:
            print("\nTesting transcription results...")
            
            # Test successful transcription
            print("* Showing successful transcription")
            self.overlay.show_transcription_result(True, "This is a test transcription")
            time.sleep(2)
            
            # Test failed transcription
            print("* Showing failed transcription")
            self.overlay.show_transcription_result(False, "API Error: Something went wrong")
            
    def on_recording_done(self):
        """Handle recording done signal"""
        print("\n* Recording done signal received")
        self.test_transcription_result()
        
    def on_recording_cancelled(self):
        """Handle recording cancelled signal"""
        print("\n* Recording cancelled signal received")
        
    def run(self):
        """Run all UI tests"""
        try:
            # Test recording overlay
            self.test_recording_overlay()
            
            # Test notifications
            self.test_notification()
            
            # Start event loop
            return self.app.exec_()
            
        except KeyboardInterrupt:
            print("\nTest interrupted by user")
            return 1
        finally:
            if self.overlay:
                self.overlay.close()

def main():
    """Main entry point"""
    test = TestUI()
    sys.exit(test.run())

if __name__ == "__main__":
    main() 