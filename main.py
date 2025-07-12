#!/usr/bin/env python3
import sys
import os
import logging
import time
import atexit
import signal
import threading
from PyQt5 import QtWidgets, QtCore, QtGui

# Local  imports
from config import (
    OPENAI_API_KEY, API_ENDPOINT, SAMPLE_RATE,
    MAX_RECORDING_SECONDS, get_temp_audio_path,
    validate_config, APP_NAME, APP_VERSION,
    OVERLAY_POSITION, OVERLAY_MARGIN
)
from src.audio import AudioRecorder
from src.profile_manager import ProfileManager
from src.profile_switching_hotkey import ProfileSwitchingHotkey
from src.whisper_api import WhisperAPI
from src.translation import TextTransformationService
from src.auto_type import AutoTyper
from src.ui.overlay import RecordingOverlay
from src.ui.token_overlay import ApiTokenOverlay
from src.ui.yaml_error_overlay import YamlErrorOverlay
from src.config_manager import ConfigManager
from src.utils import setup_logging, clean_temp_files

# Set up logging
logger = setup_logging()

class ProcessingWorker(QtCore.QThread):
    """Worker thread for processing recordings to keep UI responsive"""
    # Signals
    status_update = QtCore.pyqtSignal(str, str)  # status_text, status_type
    transcription_complete = QtCore.pyqtSignal(str)  # transcribed_text
    transformation_complete = QtCore.pyqtSignal(str)  # transformed_text
    processing_complete = QtCore.pyqtSignal(bool, str)  # success, final_text_or_error
    processing_error = QtCore.pyqtSignal(str)  # error_message
    
    def __init__(self, audio_recorder, whisper_api, transformation_service, 
                 profile_manager, current_profile_number, temp_file_path):
        super().__init__()
        self.audio_recorder = audio_recorder
        self.whisper_api = whisper_api
        self.transformation_service = transformation_service
        self.profile_manager = profile_manager
        self.current_profile_number = current_profile_number
        self.temp_file_path = temp_file_path
        
    def run(self):
        """Process the recording in a separate thread"""
        try:
            # Save audio file
            if not self.audio_recorder.save_wav(self.temp_file_path):
                self.processing_error.emit("Failed to save audio file")
                return
                
            # Get profile configuration
            if self.profile_manager:
                current_profile = self.profile_manager.get_profile(self.current_profile_number)
                whisper_config = current_profile.get('whisper', {})
            else:
                # Use default configuration if no profile manager
                whisper_config = {}
            
            # Transcribe
            self.status_update.emit("Transcribing...", "processing")
            logger.info(f"Sending to Whisper API with Profile {self.current_profile_number}: {self.temp_file_path}")
            
            success, text_or_error = self.whisper_api.transcribe(
                self.temp_file_path,
                model=whisper_config.get('model'),
                language=whisper_config.get('language'),
                prompt=whisper_config.get('prompt')
            )
            
            if not success:
                logger.error(f"Transcription error: {text_or_error}")
                self.processing_error.emit(text_or_error)
                return
                
            # Log and emit transcribed text
            logger.info(f"Transcribed: {text_or_error}")
            self.transcription_complete.emit(text_or_error)
            
            # Transform if needed
            if self.profile_manager:
                transformation_config = current_profile.get('transformation', {})
            else:
                transformation_config = {}
                
            if transformation_config and transformation_config.get('prompt'):
                self.status_update.emit("Transforming...", "processing")
                logger.info(f"Transforming text with Profile {self.current_profile_number}...")
                
                transform_success, transformed_text = self.transformation_service.transform_text(
                    text_or_error,
                    model=transformation_config.get('model'),
                    prompt=transformation_config.get('prompt')
                )
                
                if transform_success:
                    logger.info(f"Transformed: {transformed_text}")
                    self.transformation_complete.emit(transformed_text)
                    self.processing_complete.emit(True, transformed_text)
                else:
                    logger.error(f"Text transformation failed: {transformed_text}")
                    self.processing_error.emit(f"Transformation failed: {transformed_text}")
            else:
                # No transformation needed
                self.processing_complete.emit(True, text_or_error)
                
        except Exception as e:
            logger.error(f"Processing error: {e}")
            self.processing_error.emit(str(e))

class WhisperApp(QtCore.QObject):
    """
    Main application class for Windows Whisper
    """
    def __init__(self):
        """Initialize the application"""
        super().__init__()
        
        # Initialize with graceful API key handling
        self.api_key_missing = False
        try:
            validate_config()
        except ValueError as e:
            logger.warning(f"Configuration warning: {e}")
            # Don't exit - we'll handle missing API key gracefully
            self.api_key_missing = True
        
        # Worker thread reference
        self.processing_worker = None
        
        # Initialize profile manager with graceful YAML error handling
        self.yaml_error = False
        try:
            self.profile_manager = ProfileManager()
        except Exception as e:
            logger.error(f"Failed to initialize profile manager: {e}")
            self.yaml_error = True
            self.yaml_error_message = str(e)
            # Create a dummy profile manager to prevent crashes
            self.profile_manager = None
            
        # Initialize components
        self.audio_recorder = AudioRecorder(sample_rate=SAMPLE_RATE)
        # Initialize with empty API key if missing - will be set later
        api_key = OPENAI_API_KEY if not self.api_key_missing else ""
        self.whisper_api = WhisperAPI(api_key=api_key, api_endpoint=API_ENDPOINT)
        self.transformation_service = TextTransformationService()
        self.auto_typer = AutoTyper()
        
        # Connect auto-typer signals
        self.auto_typer.typing_finished.connect(self.on_auto_typing_finished)
        
        # Configuration manager
        self.config_manager = ConfigManager()
        self.config_manager.ensure_env_file_exists()
        
        # UI components
        self.is_recording = False
        self.current_overlay = None  # Track which overlay is currently active
        
        # Pre-create overlays to avoid Qt threading issues
        self.recording_overlay = RecordingOverlay()
        self.recording_overlay.recording_done.connect(self.process_recording)
        self.recording_overlay.recording_cancelled.connect(self.cancel_recording)
        self.recording_overlay.hide()  # Start hidden
        
        # Token setup overlay
        self.token_overlay = ApiTokenOverlay()
        self.token_overlay.token_saved.connect(self._on_token_saved)
        self.token_overlay.cancelled.connect(self._on_token_cancelled)
        self.token_overlay.hide()
        
        # YAML error overlay
        self.yaml_error_overlay = YamlErrorOverlay()
        self.yaml_error_overlay.open_editor_requested.connect(self.open_profiles_editor)
        self.yaml_error_overlay.dismissed.connect(self._on_yaml_error_dismissed)
        self.yaml_error_overlay.hide()
        
        # Set profiles in overlay (if profile manager is available)
        if self.profile_manager:
            all_profiles = self.profile_manager.get_all_profiles()
            profile_info = {num: self.profile_manager.get_profile_name(num) for num in all_profiles}
            self.recording_overlay.set_profiles(profile_info)
        
        # Set up profile switching hotkeys (if profile manager is available)
        if self.profile_manager:
            try:
                # Get available profile numbers from profile manager
                available_profiles = list(self.profile_manager.get_all_profiles().keys())
                
                # Initialize the profile switching hotkey manager
                self.hotkey_manager = ProfileSwitchingHotkey(
                    supported_profiles=available_profiles,
                    on_profile_change=self.on_profile_switched,
                    on_start=self.on_recording_mode_start,
                    on_stop=self.on_recording_mode_stop
                )
                
                self.hotkey_manager.start()
                
            except Exception as e:
                logger.error(f"Failed to register profile hotkeys: {e}")
                show_error_and_exit(f"Failed to register hotkeys: {e}")
        else:
            # No profile manager available, use default hotkey
            self.hotkey_manager = None
            
        # Register cleanup
        atexit.register(self.cleanup)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        # Don't pre-initialize audio to avoid mic activation on startup
        # self.audio_recorder.pre_initialize()
        
        # Create system tray icon
        self.create_tray_icon()
        
        logger.info(f"{APP_NAME} v{APP_VERSION} initialized successfully")
        
        # Show YAML error overlay if there were issues loading profiles
        if self.yaml_error:
            QtCore.QTimer.singleShot(1000, self._show_yaml_error)  # Delay to ensure UI is ready
    
    def _show_yaml_error(self):
        """Show YAML error overlay"""
        self.yaml_error_overlay.show_error(
            "Your profiles.yaml configuration file contains errors and cannot be loaded.",
            self.yaml_error_message
        )
        self.current_overlay = "yaml_error"
    
    def _hide_all_overlays(self):
        """Hide all overlays safely"""
        if self.recording_overlay and self.recording_overlay.isVisible():
            self.recording_overlay.hide()
        if self.token_overlay and self.token_overlay.isVisible():
            self.token_overlay.hide()
        if self.yaml_error_overlay and self.yaml_error_overlay.isVisible():
            self.yaml_error_overlay.hide()
        self.current_overlay = None
    
    def _check_api_token(self):
        """Check if API token is available and valid"""
        api_key = self.config_manager.get_api_key()
        if not api_key:
            return False, "No API token configured"
        
        valid, message = self.config_manager.validate_api_key_format(api_key)
        if not valid:
            return False, f"Invalid API token format: {message}"
            
        return True, "API token available"
    
    def show_token_setup(self):
        """Show the token setup overlay"""
        logger.info("Showing token setup overlay")
        self._hide_all_overlays()
        
        current_token = self.config_manager.get_api_key()
        self.token_overlay.show_overlay(current_token)
        self.current_overlay = "token"
        
    def _on_token_saved(self, token):
        """Handle token saved from overlay"""
        logger.info("Processing saved token")
        
        # Validate token format
        valid, message = self.config_manager.validate_api_key_format(token)
        if not valid:
            QtWidgets.QMessageBox.warning(None, "Invalid Token", f"Token validation failed: {message}")
            return
        
        # Save to .env file
        if self.config_manager.save_api_key(token):
            # Update the WhisperAPI instance with new token
            self.whisper_api.api_key = token
            logger.info("API token updated successfully")
            QtWidgets.QMessageBox.information(None, "Success", "API token saved successfully!")
        else:
            QtWidgets.QMessageBox.critical(None, "Error", "Failed to save API token. Please try again.")
            
        self.current_overlay = None
        
    def _on_token_cancelled(self):
        """Handle token setup cancelled"""
        logger.info("Token setup cancelled")
        self.current_overlay = None
        
    def open_profiles_editor(self):
        """Open profiles.yaml file in notepad"""
        import subprocess
        import os
        
        profiles_path = os.path.abspath("profiles.yaml")
        
        if not os.path.exists(profiles_path):
            QtWidgets.QMessageBox.warning(
                None, 
                "File Not Found", 
                f"profiles.yaml not found at:\n{profiles_path}"
            )
            return
            
        try:
            # Use notepad.exe on Windows
            subprocess.run(["notepad.exe", profiles_path], check=False)
            logger.info(f"Opened profiles editor: {profiles_path}")
        except Exception as e:
            logger.error(f"Failed to open profiles editor: {e}")
            QtWidgets.QMessageBox.critical(
                None,
                "Error",
                f"Failed to open editor:\n{str(e)}"
            )
    
    def _on_yaml_error_dismissed(self):
        """Handle YAML error overlay dismissed"""
        logger.info("YAML error overlay dismissed")
        self.current_overlay = None
    
    def on_profile_switched(self, profile_number):
        """Handle profile switching"""
        if not self.profile_manager:
            logger.warning("Profile manager not available")
            return
            
        profile_name = self.profile_manager.get_profile_name(profile_number)
        logger.info(f"Switched to Profile {profile_number}: {profile_name}")
        
        # Update tray icon to show new profile number
        if hasattr(self, 'tray_icon'):
            self._update_tray_icon()
            
        # Update overlay if it's visible (thread-safe)
        if hasattr(self, 'recording_overlay') and self.recording_overlay.isVisible():
            QtCore.QMetaObject.invokeMethod(
                self.recording_overlay, "update_active_profile",
                QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(int, profile_number),
                QtCore.Q_ARG(str, profile_name)
            )
    
    def on_recording_mode_start(self, profile_number):
        """Handle start of recording mode (Ctrl+Shift held)"""
        if not self.profile_manager:
            logger.info("Recording mode started - using default profile")
            QtCore.QMetaObject.invokeMethod(
                self, "start_recording",
                QtCore.Qt.QueuedConnection
            )
            return
            
        profile_name = self.profile_manager.get_profile_name(profile_number)
        logger.info(f"Recording mode started - Profile {profile_number}: {profile_name}")
        # Schedule start_recording_with_profile to run on main thread
        QtCore.QMetaObject.invokeMethod(
            self, "_start_recording_with_profile_slot",
            QtCore.Qt.QueuedConnection,
            QtCore.Q_ARG(int, profile_number)
        )
    
    def on_recording_mode_stop(self, profile_number):
        """Handle end of recording mode (Ctrl+Shift released)"""
        logger.info("Recording mode stopped")
        # Schedule stop_recording to run on main thread
        QtCore.QMetaObject.invokeMethod(
            self, "stop_recording",
            QtCore.Qt.QueuedConnection
        )

    def on_auto_typing_finished(self, success):
        """Handle completion of auto-typing"""
        if success:
            logger.info("Auto-typing completed successfully")
        else:
            logger.warning("Auto-typing failed")
            
    @QtCore.pyqtSlot(int)
    def _start_recording_with_profile_slot(self, profile_number):
        """Qt slot for starting recording with a specific profile"""
        self.start_recording_with_profile(profile_number)
        
    def start_recording_with_profile(self, profile_number):
        """Start recording with a specific profile"""
        if not self.profile_manager:
            logger.warning("Profile manager not available, using default recording")
            self.start_recording()
            return
            
        if not self.profile_manager.has_profile(profile_number):
            logger.warning(f"Profile {profile_number} not found, ignoring")
            return
            
        profile_name = self.profile_manager.get_profile_name(profile_number)
        logger.info(f"Starting recording with Profile {profile_number}: {profile_name}")
        
        # Start the regular recording process
        self.start_recording()
        
    def signal_handler(self, signum, frame):
        """Handle system signals"""
        logger.info(f"Received signal {signum}")
        self.cleanup()
        sys.exit(0)
        
    def _cleanup_overlay(self):
        """Hide the recording overlay safely"""
        if self.recording_overlay:
            try:
                self.recording_overlay.hide()
            except Exception as e:
                logger.error(f"Error hiding overlay: {e}")
        
    def create_tray_icon(self):
        """Create system tray icon"""
        self.tray_icon = QtWidgets.QSystemTrayIcon()
        
        # Create initial icon with profile number
        self._update_tray_icon()
            
        # Create menu
        tray_menu = QtWidgets.QMenu()
        
        # Add actions
        setup_token_action = tray_menu.addAction("Setup API Token")
        setup_token_action.triggered.connect(self.show_token_setup)
        
        edit_profiles_action = tray_menu.addAction("Edit Profiles")
        edit_profiles_action.triggered.connect(self.open_profiles_editor)
        
        tray_menu.addSeparator()
        
        exit_action = tray_menu.addAction("Exit")
        exit_action.triggered.connect(self.quit)
        
        # Set menu
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
        # Don't show startup notification
        
    def _update_tray_icon(self, recording=False):
        """Update tray icon with golden mic symbol and current profile number"""
        from PyQt5.QtGui import QPixmap, QPainter, QFont, QColor, QBrush, QLinearGradient
        
        # Create a 48x48 pixmap for better visibility
        pixmap = QPixmap(48, 48)
        pixmap.fill(QtCore.Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Golden gradient for the mic
        if recording:
            # Bright golden-red when recording
            gradient = QLinearGradient(12, 4, 28, 24)
            gradient.setColorAt(0, QColor(255, 215, 0))  # Gold
            gradient.setColorAt(0.5, QColor(255, 140, 0))  # Dark orange 
            gradient.setColorAt(1, QColor(220, 50, 50))  # Red
        else:
            # Classic golden mic when idle
            gradient = QLinearGradient(12, 4, 28, 24)
            gradient.setColorAt(0, QColor(255, 235, 100))  # Light gold
            gradient.setColorAt(0.5, QColor(255, 215, 0))  # Gold
            gradient.setColorAt(1, QColor(184, 134, 11))  # Dark golden rod
        
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QBrush(gradient))
        
        # Mic body (rounded rectangle) - larger and more elegant
        painter.drawRoundedRect(12, 4, 18, 24, 9, 9)
        
        # Mic grill lines for classic look
        painter.setPen(QtGui.QPen(QColor(0, 0, 0, 80), 1))
        for i in range(3):
            y = 8 + i * 6
            painter.drawLine(16, y, 26, y)
        
        # Mic stand
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QColor(120, 120, 120))
        painter.drawRect(19, 28, 4, 8)
        
        # Mic base
        painter.drawRect(10, 36, 20, 4)
        
        # Draw notification-style badge for profile number
        profile_str = str(self.hotkey_manager.current_profile) if hasattr(self, 'hotkey_manager') else "1"
        
        # Badge background - bright color for visibility
        badge_color = QColor(0, 120, 215)  # Blue badge (Windows accent blue)
        painter.setBrush(badge_color)
        painter.setPen(QtCore.Qt.NoPen)
        
        # Bigger badge for 48x48 icon
        badge_size = 20
        badge_x = 48 - badge_size - 2
        badge_y = 2
        painter.drawEllipse(badge_x, badge_y, badge_size, badge_size)
        
        # Draw profile number in badge - BIGGER font
        painter.setPen(QColor(255, 255, 255))  # White text
        font = QFont("Arial", 14, QFont.Bold)  # Increased to 14
        painter.setFont(font)
        
        badge_rect = QtCore.QRect(badge_x, badge_y, badge_size, badge_size)
        painter.drawText(badge_rect, QtCore.Qt.AlignCenter, profile_str)
        
        painter.end()
        
        # Set the icon
        self.tray_icon.setIcon(QtGui.QIcon(pixmap))
        
    def start_recording(self):
        """Start audio recording and show overlay with minimal delay"""
        logger.info("Starting recording...")
        
        # If already recording, don't start another session
        if self.is_recording:
            logger.debug("Recording already in progress")
            return
        
        # Check if API token is available
        token_valid, token_message = self._check_api_token()
        if not token_valid:
            logger.warning(f"Cannot start recording: {token_message}")
            self.show_token_setup()
            return
            
        self.is_recording = True
        
        # Update tray icon to show recording state
        if hasattr(self, 'tray_icon'):
            self._update_tray_icon(recording=True)
        
        try:
            logger.debug(f"Starting recording from thread: {threading.current_thread().name}")
            # Reset the overlay for a new recording
            self.recording_overlay.reset_for_recording()
            
            # Update active profile in overlay
            if self.hotkey_manager and self.profile_manager:
                current_profile = self.hotkey_manager.current_profile
                profile_name = self.profile_manager.get_profile_name(current_profile)
                self.recording_overlay.update_active_profile(current_profile, profile_name)
            
            # Show overlay
            self.recording_overlay.show()
            self.recording_overlay.raise_()
            # Don't call activateWindow() since we have WindowDoesNotAcceptFocus flag set
            
            logger.debug("Overlay shown, starting audio recording")
            # Start actual recording after UI is ready
            self._start_actual_recording()
        except Exception as e:
            logger.error(f"Failed to show recording overlay: {e}")
            self.is_recording = False
            self._cleanup_overlay()
        
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
            self._cleanup_overlay()
            
    def _recording_started_callback(self):
        """Called when audio recording has actually started"""
        # Now we can start the timer in the UI
        if self.recording_overlay:
            self.recording_overlay.start_recording()
        
    def _update_waveform(self, level):
        """Update the waveform visualization with new audio level"""
        # Skip if no overlay
        if not self.recording_overlay:
            return
            
        # Directly update the waveform - the waveform widget handles its own threading/timing
        try:
            if hasattr(self.recording_overlay, 'waveform'):
                self.recording_overlay.waveform.add_level(level)
        except Exception as e:
            # Log error but don't flood logs - this is called frequently
            if not hasattr(self, '_waveform_error_logged'):
                logger.error(f"Error updating waveform: {e}")
                self._waveform_error_logged = True
        
    def process_recording(self):
        """Process the recorded audio"""
        logger.info("Processing recording...")
        
        self.is_recording = False
        
        # Update tray icon to show not recording
        if hasattr(self, 'tray_icon'):
            self._update_tray_icon(recording=False)
        
        # Stop recording
        if not self.audio_recorder.stop_recording():
            logger.error("Failed to stop recording - no recording in progress")
            self._cleanup_overlay()
            return
        
        # Check if we have any recorded audio frames
        if not hasattr(self.audio_recorder, 'frames') or not self.audio_recorder.frames:
            logger.error("No audio data was recorded")
            self._cleanup_overlay()
            return
        
        # Get temp file path
        temp_file_path = get_temp_audio_path()
        
        # Create and start processing worker
        current_profile = 1  # Default profile
        if self.hotkey_manager:
            current_profile = self.hotkey_manager.current_profile
            
        self.processing_worker = ProcessingWorker(
            self.audio_recorder,
            self.whisper_api,
            self.transformation_service,
            self.profile_manager,
            current_profile,
            temp_file_path
        )
        
        # Connect signals
        self.processing_worker.status_update.connect(self._on_processing_status_update)
        self.processing_worker.processing_complete.connect(self._on_processing_complete)
        self.processing_worker.processing_error.connect(self._on_processing_error)
        
        # Start processing in background thread
        self.processing_worker.start()
    
    @QtCore.pyqtSlot(str, str)
    def _on_processing_status_update(self, status_text, status_type):
        """Handle status updates from processing worker"""
        if self.recording_overlay and self.recording_overlay.isVisible():
            self.recording_overlay.show_status(status_text, status_type)
    
    @QtCore.pyqtSlot(bool, str)
    def _on_processing_complete(self, success, final_text):
        """Handle processing completion"""
        if success:
            # Auto-type the result
            try:
                logger.info("Preparing to type text...")
                
                # Hide the overlay before auto-typing
                if self.recording_overlay:
                    self.recording_overlay.hide()
                
                # Start auto-typing directly
                logger.info(f"Starting auto-type for: {final_text[:30]}...")
                self.auto_typer.type_text_fast(final_text)
                
            except Exception as e:
                logger.error(f"Auto-typing error: {e}")
        
        # Clean up temp file
        temp_file_path = get_temp_audio_path()
        try:
            os.remove(temp_file_path)
        except Exception as e:
            logger.warning(f"Failed to remove temporary file: {e}")
            
        # Clean up worker
        if self.processing_worker:
            self.processing_worker.wait()
            self.processing_worker.deleteLater()
            self.processing_worker = None
    
    @QtCore.pyqtSlot(str)
    def _on_processing_error(self, error_message):
        """Handle processing errors"""
        logger.error(f"Processing error: {error_message}")
        
        # Check if this is an API authentication error
        if "401" in error_message or "authentication" in error_message.lower() or "api key" in error_message.lower():
            logger.warning("API authentication error detected, showing token setup")
            self._cleanup_overlay()
            self.show_token_setup()
        else:
            self._cleanup_overlay()
        
        # Clean up temp file
        temp_file_path = get_temp_audio_path()
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception as e:
                logger.warning(f"Failed to remove temporary file: {e}")
        
        # Clean up worker
        if self.processing_worker:
            self.processing_worker.wait()
            self.processing_worker.deleteLater()
            self.processing_worker = None
            
    def cancel_recording(self):
        """Cancel the current recording"""
        logger.debug("Recording cancelled")
        self.is_recording = False
        self.audio_recorder.stop_recording()
        
        # Update tray icon to show not recording
        if hasattr(self, 'tray_icon'):
            self._update_tray_icon(recording=False)
        
        # Clean up temp file
        temp_file_path = get_temp_audio_path()
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception as e:
                logger.warning(f"Failed to clean up temporary file: {e}")
                
        # Clean up overlay (if not already closed by auto-typing)
        self._cleanup_overlay()
        
    @QtCore.pyqtSlot()
    def stop_recording(self):
        """Stop audio recording and process the result"""
        logger.info("Stopping recording...")
        
        if self.recording_overlay:
            # Trigger the overlay's finish recording
            self.recording_overlay.finish_recording()
        else:
            logger.info("No recording overlay to stop")
            # If there's no overlay, we need to process the recording directly
            self.process_recording()
    
    def cleanup(self):
        """Clean up resources"""
        logger.info("Cleaning up resources...")
        
        # Stop hotkey manager
        if hasattr(self, 'hotkey_manager'):
            self.hotkey_manager.stop()
            
        # Clean up overlay
        if hasattr(self, 'recording_overlay') and self.recording_overlay:
            try:
                self.recording_overlay.close()
            except:
                pass
            
        # Remove any temporary files
        temp_file_path = get_temp_audio_path()
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception as e:
                logger.warning(f"Failed to remove temp directory: {e}")
                
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