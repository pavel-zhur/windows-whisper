#!/usr/bin/env python3
import sys
import os
import logging
import time
import atexit
import signal
from PyQt5 import QtWidgets, QtCore

# Local imports
from config import (
    SHORTCUT_KEY, OPENAI_API_KEY, API_ENDPOINT, 
    WHISPER_MODEL, WHISPER_LANGUAGE, SAMPLE_RATE,
    MAX_RECORDING_SECONDS, get_temp_audio_path,
    validate_config
)
from src.audio import AudioRecorder
from src.hotkey import setup_hotkey
from src.whisper_api import WhisperAPI
from src.clipboard import copy_to_clipboard
from src.ui.overlay import RecordingOverlay, show_notification
from src.utils import setup_logging, clean_temp_files

# Set up logging
logger = setup_logging()

class WhisperApp(QtCore.QObject):
    """
    Main application class for Windows Whisper
    """
    def __init__(self):
        """Initialize the application"""
        super().__init__()
        
        # Validate configuration
        try:
            validate_config()
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            show_error_and_exit(str(e))
            
        # Initialize components
        self.audio_recorder = AudioRecorder(sample_rate=SAMPLE_RATE)
        self.whisper_api = WhisperAPI(
            api_key=OPENAI_API_KEY,
            api_endpoint=API_ENDPOINT,
            model=WHISPER_MODEL
        )
        
        # UI components
        self.recording_overlay = None
        
        # Set up hotkey
        try:
            self.hotkey_manager = setup_hotkey(SHORTCUT_KEY, self.start_recording)
            logger.info(f"Hotkey registered: {SHORTCUT_KEY}")
        except Exception as e:
            logger.error(f"Failed to register hotkey: {e}")
            show_error_and_exit(f"Failed to register hotkey: {e}")
            
        # Register cleanup
        atexit.register(self.cleanup)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        # Create system tray icon
        self.create_tray_icon()
        
        logger.info("Whisper app initialized successfully")
        
    def signal_handler(self, signum, frame):
        """Handle system signals"""
        logger.info(f"Received signal {signum}")
        self.cleanup()
        sys.exit(0)
        
    def create_tray_icon(self):
        """Create system tray icon"""
        self.tray_icon = QtWidgets.QSystemTrayIcon()
        
        # Set icon (placeholder - would need an actual icon file)
        self.tray_icon.setIcon(QtWidgets.QApplication.style().standardIcon(
            QtWidgets.QStyle.SP_MessageBoxInformation))
            
        # Create menu
        tray_menu = QtWidgets.QMenu()
        
        # Add actions
        exit_action = tray_menu.addAction("Exit")
        exit_action.triggered.connect(self.quit)
        
        # Set menu
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
        # Show startup notification
        self.tray_icon.showMessage(
            "Whisper Transcript", 
            f"Ready! Press {SHORTCUT_KEY} to start recording.",
            QtWidgets.QSystemTrayIcon.Information, 
            3000
        )
        
    def start_recording(self):
        """Start audio recording and show overlay"""
        logger.info("Starting recording...")
        
        # If already recording, don't start another session
        if self.recording_overlay is not None and self.recording_overlay.isVisible():
            logger.warning("Recording already in progress")
            return
            
        # Create and show recording overlay
        try:
            self.recording_overlay = RecordingOverlay()
            self.recording_overlay.recording_done.connect(self.process_recording)
            self.recording_overlay.recording_cancelled.connect(self.cancel_recording)
            self.recording_overlay.recording_started.connect(self._start_actual_recording)
            
            # Ensure overlay is shown and activated
            self.recording_overlay.show()
            self.recording_overlay.raise_()
            self.recording_overlay.activateWindow()
            
            # Force process events to ensure overlay is displayed
            QtWidgets.QApplication.processEvents()
            
            logger.info("Recording overlay created and shown")
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            if self.recording_overlay:
                self.recording_overlay.close()
                self.recording_overlay = None
            show_notification("Error", f"Failed to start recording: {e}", icon_type="error")
            
    def _start_actual_recording(self):
        """Start the actual audio recording after countdown"""
        try:
            # Start audio recording
            self.audio_recorder.start_recording(
                max_seconds=MAX_RECORDING_SECONDS
            )
            logger.info("Audio recording started")
        except Exception as e:
            logger.error(f"Failed to start audio recording: {e}")
            if self.recording_overlay:
                self.recording_overlay.close()
                self.recording_overlay = None
            show_notification("Error", f"Failed to start recording: {e}", icon_type="error")
        
    def process_recording(self):
        """Process the recorded audio"""
        logger.info("Processing recording...")
        
        # Stop recording
        self.audio_recorder.stop_recording()
        
        # Save to temp file
        temp_file_path = get_temp_audio_path()
        if not self.audio_recorder.save_wav(temp_file_path):
            logger.error("Failed to save audio file")
            self.show_error("Failed to save audio file")
            return
            
        # Send to Whisper API
        logger.info(f"Sending to Whisper API: {temp_file_path}")
        success, text_or_error = self.whisper_api.transcribe(
            temp_file_path, 
            language=WHISPER_LANGUAGE
        )
        
        if success:
            # Copy to clipboard
            if copy_to_clipboard(text_or_error):
                logger.info(f"Transcription copied to clipboard: {text_or_error[:30]}...")
                
                # Show success in the overlay
                if self.recording_overlay and self.recording_overlay.isVisible():
                    self.recording_overlay.show_transcription_result(True, text_or_error)
            else:
                logger.error("Failed to copy to clipboard")
                if self.recording_overlay and self.recording_overlay.isVisible():
                    self.recording_overlay.show_transcription_result(
                        False, "Failed to copy to clipboard"
                    )
        else:
            # Show error
            logger.error(f"Transcription error: {text_or_error}")
            if self.recording_overlay and self.recording_overlay.isVisible():
                self.recording_overlay.show_transcription_result(False, text_or_error)
                
        # Clean up temp file
        try:
            os.remove(temp_file_path)
            logger.info(f"Temporary audio file removed: {temp_file_path}")
        except Exception as e:
            logger.warning(f"Failed to remove temporary file: {e}")
            
    def cancel_recording(self):
        """Cancel the current recording"""
        logger.info("Recording cancelled")
        self.audio_recorder.stop_recording()
        
        # Clean up temp file
        temp_file_path = get_temp_audio_path()
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                logger.info(f"Temporary audio file removed: {temp_file_path}")
            except Exception as e:
                logger.warning(f"Failed to remove temporary file: {e}")
        
    def cleanup(self):
        """Clean up resources"""
        logger.info("Cleaning up resources...")
        
        # Unregister hotkey
        if hasattr(self, 'hotkey_manager'):
            self.hotkey_manager.unregister_all()
            
        # Remove any temporary files
        temp_file_path = get_temp_audio_path()
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except:
                pass
                
    def quit(self):
        """Quit the application"""
        logger.info("Exiting application")
        self.cleanup()
        QtWidgets.QApplication.quit()
        
        
def show_error_and_exit(message):
    """Show error dialog and exit"""
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
        
    error_dialog = QtWidgets.QMessageBox()
    error_dialog.setIcon(QtWidgets.QMessageBox.Critical)
    error_dialog.setWindowTitle("Error")
    error_dialog.setText("Whisper Transcript Error")
    error_dialog.setInformativeText(message)
    error_dialog.exec_()
    
    sys.exit(1)
        
        
def handle_exception(exc_type, exc_value, exc_traceback):
    """Global exception handler"""
    if issubclass(exc_type, KeyboardInterrupt):
        # Standard handling for keyboard interrupt
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
        
    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    
    
def main():
    """Main entry point"""
    # Set up exception handling
    sys.excepthook = handle_exception
    
    # Create Qt application
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Don't quit when all windows are closed
    app.setApplicationName("Whisper Transcript")
    
    # Start the application
    whisper_app = WhisperApp()
    
    # Start event loop
    sys.exit(app.exec_())
    
    
if __name__ == "__main__":
    main() 