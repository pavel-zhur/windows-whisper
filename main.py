#!/usr/bin/env python3
import sys
import os
import logging
import time
import atexit
import signal
from PyQt5 import QtWidgets, QtCore

# Local  imports
from config import (
    SHORTCUT_KEY, OPENAI_API_KEY, API_ENDPOINT, 
    WHISPER_MODEL, WHISPER_LANGUAGE, SAMPLE_RATE,
    MAX_RECORDING_SECONDS, get_temp_audio_path,
    validate_config, APP_NAME, APP_VERSION,
    AUTO_TYPE_ENABLED, HOLD_TO_RECORD, OVERLAY_POSITION, OVERLAY_MARGIN,
    TRANSFORMATION_PROMPT
)
from src.audio import AudioRecorder
from src.hotkey import setup_hold_to_record_hotkey, HoldToRecordHotkeyManager
from src.whisper_api import WhisperAPI
from src.translation import TextTransformationService
from src.clipboard import copy_to_clipboard
from src.auto_type import AutoTyper
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
        self.transformation_service = TextTransformationService()
        self.auto_typer = AutoTyper()
        
        # Log language setting
        if WHISPER_LANGUAGE:
            logger.debug(f"Using language setting: {WHISPER_LANGUAGE}")
        else:
            logger.debug("No language specified - OpenAI will auto-detect language")
        
        # UI components
        self.recording_overlay = None
        self.is_recording = False
        
        # Set up hold-to-record hotkey
        try:
            logger.info(f"Setting up hold-to-record hotkey: {SHORTCUT_KEY}")
            self.hotkey_manager = setup_hold_to_record_hotkey(SHORTCUT_KEY)
            
            # Connect signals
            self.hotkey_manager.recording_started.connect(self.start_recording)
            self.hotkey_manager.recording_stopped.connect(self.stop_recording)
            
            logger.info(f"Hold-to-record hotkey registered successfully: {SHORTCUT_KEY}")
        except Exception as e:
            logger.error(f"Failed to register hold-to-record hotkey: {e}")
            show_error_and_exit(f"Failed to register hotkey: {e}")
            
        # Register cleanup
        atexit.register(self.cleanup)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        # Pre-initialize audio system to reduce startup delay
        self.audio_recorder.pre_initialize()
        logger.debug("Audio system pre-initialized during app startup")
        
        # Create system tray icon
        self.create_tray_icon()
        
        logger.info(f"{APP_NAME} v{APP_VERSION} initialized successfully")
        
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
            f"{APP_NAME}", 
            f"v{APP_VERSION} ready! Hold {SHORTCUT_KEY} to record.",
            QtWidgets.QSystemTrayIcon.Information, 
            3000
        )
        
    def start_recording(self):
        """Start audio recording and show overlay with minimal delay"""
        logger.info("Starting recording...")
        
        # If already recording, don't start another session
        if self.is_recording:
            logger.debug("Recording already in progress")
            return
            
        self.is_recording = True
        
        # Create and show recording overlay
        try:
            # Create the overlay - it will show itself immediately and emit recording_started
            self.recording_overlay = RecordingOverlay()
            self.recording_overlay.recording_done.connect(self.process_recording)
            self.recording_overlay.recording_cancelled.connect(self.cancel_recording)
            self.recording_overlay.recording_started.connect(self._start_actual_recording)
            
            logger.info("Recording overlay created and shown")
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            self.is_recording = False
            if self.recording_overlay:
                self.recording_overlay.close()
                self.recording_overlay = None
            show_notification("Error", f"Failed to start recording: {e}", icon_type="error")
        
    def _start_actual_recording(self):
        """Start the actual audio recording immediately"""
        try:
            logger.debug("Starting audio recording immediately")
            # Start audio recording with level callback and recording callback
            self.audio_recorder.start_recording(
                max_seconds=MAX_RECORDING_SECONDS,
                level_callback=self._update_waveform if self.recording_overlay else None,
                callback_fn=self._recording_started_callback
            )
            logger.debug("Audio recording started")
        except Exception as e:
            logger.error(f"Failed to start audio recording: {e}")
            if self.recording_overlay:
                self.recording_overlay.close()
                self.recording_overlay = None
            show_notification("Error", f"Failed to start recording: {e}", icon_type="error")
            
    def _recording_started_callback(self):
        """Called when audio recording has actually started"""
        logger.debug("Audio recording started")
        # Now we can start the timer in the UI
        if self.recording_overlay and self.recording_overlay.isVisible():
            self.recording_overlay.start_recording()
        
    def _update_waveform(self, level):
        """Update the waveform visualization with new audio level"""
        if self.recording_overlay and hasattr(self.recording_overlay.waveform, 'add_level'):
            # Use the improved add_level method which handles smooth transitions
            self.recording_overlay.waveform.add_level(level)
        
    def process_recording(self):
        """Process the recorded audio"""
        logger.info("Processing recording...")
        
        self.is_recording = False
        
        # Stop recording
        if not self.audio_recorder.stop_recording():
            logger.error("Failed to stop recording - no recording in progress")
            show_notification("No recording to process", icon_type="error")
            return
        
        # Check if we have any recorded audio frames
        if not hasattr(self.audio_recorder, 'frames') or not self.audio_recorder.frames:
            logger.error("No audio data was recorded")
            show_notification("No audio was recorded", icon_type="error")
            return
        
        # Save to temp file
        temp_file_path = get_temp_audio_path()
        if not self.audio_recorder.save_wav(temp_file_path):
            logger.error("Failed to save audio file")
            show_notification("Failed to save audio file", icon_type="error")
            return
            
        # Send to Whisper API
        logger.info(f"Sending to Whisper API: {temp_file_path}")
        success, text_or_error = self.whisper_api.transcribe(
            temp_file_path
        )
        
        logger.info(f"Whisper API result - Success: {success}, Text/Error: {text_or_error}")
        
        if success:
            # Transform the text if transformation is enabled
            if TRANSFORMATION_PROMPT:
                logger.info(f"Transforming text...")
                transform_success, final_text = self.transformation_service.transform_text(text_or_error)
                
                if transform_success:
                    logger.info(f"Text transformation successful: {final_text[:50]}...")
                else:
                    logger.error(f"Text transformation failed: {final_text}")
                    final_text = text_or_error  # Fall back to original text
            else:
                final_text = text_or_error
            
            if AUTO_TYPE_ENABLED:
                # Auto-type the result
                try:
                    # Close the overlay first to avoid interfering with typing
                    if self.recording_overlay and self.recording_overlay.isVisible():
                        self.recording_overlay.close()
                        self.recording_overlay = None
                    
                    # Additional delay to ensure overlay is fully closed
                    QtCore.QTimer.singleShot(100, lambda: self.auto_typer.type_text_fast(final_text))
                    logger.info(f"Transcription will be auto-typed: {final_text[:30]}...")
                    
                except Exception as e:
                    logger.error(f"Auto-typing error: {e}")
                    # Fallback to clipboard
                    copy_to_clipboard(final_text)
                    show_notification("Auto-typing failed, copied to clipboard", icon_type="warning")
            else:
                # Copy to clipboard
                if copy_to_clipboard(final_text):
                    logger.debug(f"Transcription copied to clipboard: {final_text[:30]}...")
                    show_notification("Transcription copied to clipboard", icon_type="success")
        else:
            # Show error
            logger.error(f"Transcription error: {text_or_error}")
            show_notification(f"Transcription error: {text_or_error}", icon_type="error")
                
        # Clean up temp file
        try:
            os.remove(temp_file_path)
            logger.debug(f"Temporary audio file removed: {temp_file_path}")
        except Exception as e:
            logger.warning(f"Failed to remove temporary file: {e}")
            
        # Clean up overlay
        if self.recording_overlay and self.recording_overlay.isVisible():
            self.recording_overlay.close()
            self.recording_overlay = None
            
    def cancel_recording(self):
        """Cancel the current recording"""
        logger.debug("Recording cancelled")
        self.is_recording = False
        self.audio_recorder.stop_recording()
        
        # Clean up temp file
        temp_file_path = get_temp_audio_path()
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                logger.debug("Temporary audio file cleaned up")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary file: {e}")
                
        # Clean up overlay
        if self.recording_overlay and self.recording_overlay.isVisible():
            self.recording_overlay.close()
            self.recording_overlay = None
        
    def stop_recording(self):
        """Stop audio recording and process the result"""
        logger.info("Stopping recording...")
        
        if self.recording_overlay and self.recording_overlay.isVisible():
            # Trigger the overlay's finish recording
            self.recording_overlay.finish_recording()
        else:
            logger.info("No recording overlay to stop")
            # If there's no overlay, we need to process the recording directly
            self.process_recording()
    
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