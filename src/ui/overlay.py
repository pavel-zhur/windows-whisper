from PyQt5 import QtWidgets, QtCore, QtGui
import logging
import numpy as np  # Used for waveform calculations

logger = logging.getLogger(__name__)

class WaveformWidget(QtWidgets.QWidget):
    """Widget that displays an animated audio waveform"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(68)  # Increased by ~35% from 50
        self.setMinimumWidth(200)
        
        # Initialize waveform data with more points for smoother visualization
        self.waveform_data = [0.0] * 75
        
        # Animation timer - update faster for smoother animation
        self.animation_timer = QtCore.QTimer(self)
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_timer.start(16)  # ~60 FPS for smoother animation
        
        # Visual settings with more vibrant color
        self.color = QtGui.QColor(30, 220, 30)  # Even brighter and more saturated green
        self.recording = False
        
        # For smoother animation, we'll interpolate between values
        self.target_waveform = [0.0] * 75
        self.smoothing_factor = 0.25  # Adjusted for better responsiveness
        
        # Add averaging for smoother transitions
        self.last_levels = []
        self.max_levels = 3  # Reduced for more responsive visualization
        
    def start_recording(self):
        """Start the waveform animation"""
        self.recording = True
        self.update()
        
    def stop_recording(self):
        """Stop the waveform animation"""
        self.recording = False
        self.waveform_data = [0.0] * 75
        self.target_waveform = [0.0] * 75
        self.update()
    
    def update_animation(self):
        """Animate the waveform smoothly"""
        if not self.recording:
            # Gradually return to zero when not recording
            if any(abs(x) > 0.01 for x in self.waveform_data):
                self.waveform_data = [x * 0.9 for x in self.waveform_data]  # Slower fade out (was 0.8)
                self.update()
            return
            
        # Smooth transition to target values
        needs_update = False
        for i in range(len(self.waveform_data)):
            diff = self.target_waveform[i] - self.waveform_data[i]
            if abs(diff) > 0.001:  # More sensitive updates (was 0.01)
                self.waveform_data[i] += diff * self.smoothing_factor
                needs_update = True
                
        if needs_update:
            self.update()
            
    def add_level(self, level):
        """Add a new audio level to the waveform"""
        if not self.recording:
            return
            
        # Add to averaging buffer
        self.last_levels.append(level)
        if len(self.last_levels) > self.max_levels:
            self.last_levels.pop(0)
            
        # Calculate smoothed level with weighted average
        # Give more weight to recent levels
        weights = [0.5, 0.3, 0.2][:len(self.last_levels)]
        smoothed_level = sum(l * w for l, w in zip(reversed(self.last_levels), weights)) / sum(weights)
        
        # Shift existing target data left and add new smoothed level
        self.target_waveform = self.target_waveform[1:] + [smoothed_level]
        
    def paintEvent(self, event):
        """Draw the waveform"""
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        # Calculate dimensions
        width = self.width()
        height = self.height()
        center_y = height / 2
        
        # Draw waveform
        if self.recording or any(self.waveform_data):
            path = QtGui.QPainterPath()
            path.moveTo(0, center_y)
            
            point_width = width / (len(self.waveform_data) - 1) if len(self.waveform_data) > 1 else width
            
            # Draw top half of waveform with smoother curve and increased amplitude
            points = []
            for i, value in enumerate(self.waveform_data):
                x = i * point_width
                y = center_y - (value * center_y * 0.98)  # Increased amplitude to 98%
                points.append((x, y))
                
            # Create smooth curve through points
            if len(points) > 1:
                path.moveTo(points[0][0], points[0][1])
                for i in range(1, len(points) - 2):
                    x1 = (points[i][0] + points[i+1][0]) / 2
                    y1 = (points[i][1] + points[i+1][1]) / 2
                    path.quadTo(points[i][0], points[i][1], x1, y1)
                path.quadTo(points[-2][0], points[-2][1], points[-1][0], points[-1][1])
                
            # Draw bottom half (mirror) with smooth curve
            points = []
            for i in range(len(self.waveform_data) - 1, -1, -1):
                x = i * point_width
                y = center_y + (self.waveform_data[i] * center_y * 0.98)  # Increased amplitude to 98%
                points.append((x, y))
                
            if len(points) > 1:
                for i in range(1, len(points) - 2):
                    x1 = (points[i][0] + points[i+1][0]) / 2
                    y1 = (points[i][1] + points[i+1][1]) / 2
                    path.quadTo(points[i][0], points[i][1], x1, y1)
                path.quadTo(points[-2][0], points[-2][1], points[-1][0], points[-1][1])
            
            path.lineTo(0, center_y)
            
            # Fill the waveform with more vibrant gradient
            painter.setPen(QtCore.Qt.NoPen)
            gradient = QtGui.QLinearGradient(0, 0, 0, height)
            gradient.setColorAt(0, self.color.lighter(180))  # Even brighter top (was 160)
            gradient.setColorAt(0.5, self.color.lighter(130))  # Brighter middle
            gradient.setColorAt(1, self.color)  # Keep base color at bottom for contrast
            painter.setBrush(gradient)
            
            # Add glow effect
            glow = QtGui.QPainterPath(path)
            glow_brush = QtGui.QColor(30, 220, 30, 40)  # Semi-transparent glow
            painter.setBrush(glow_brush)
            painter.drawPath(glow)
            
            # Draw main waveform
            painter.setBrush(gradient)
            painter.drawPath(path)

class RecordingOverlay(QtWidgets.QWidget):
    """
    Floating overlay UI for the recording functionality with instant response
    """
    # Signals
    recording_done = QtCore.pyqtSignal()
    recording_cancelled = QtCore.pyqtSignal()
    recording_started = QtCore.pyqtSignal()  # Signal for actual recording start
    
    def __init__(self, opacity=0.9, parent=None):
        """
        Initialize the recording overlay with instant visibility and recording start
        
        Args:
            opacity (float): Window opacity (0.0-1.0)
            parent: Parent widget
        """
        super().__init__(parent)
        self.opacity = opacity
        self.profiles = {}  # Will be populated with profile data
        self.active_profile = 1
        
        # Set window properties first for faster display
        self.setWindowFlags(
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.Tool |
            QtCore.Qt.WindowDoesNotAcceptFocus  # Don't steal focus
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WA_ShowWithoutActivating)  # Show without taking focus
        self.setWindowOpacity(self.opacity)
        
        # Remove focus policies to prevent stealing focus
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        
        # Show window immediately before heavy initialization
        self.resize(300, 150)  # Adjusted size to fit profile display
        
        # Position in top-right corner
        from config import OVERLAY_POSITION, OVERLAY_MARGIN
        self.position_in_corner(OVERLAY_POSITION, OVERLAY_MARGIN)
        self.show()
        # Don't steal focus - the overlay should appear but not interfere
        
        # Fast initialization of basic UI elements (time-critical ones)
        self.timer_label = QtWidgets.QLabel("00:00")
        self.timer_label.setStyleSheet("color: white; font-weight: bold; font-size: 14px;")
        self.status_label = QtWidgets.QLabel("Recording...")
        self.status_label.setStyleSheet("color: white; font-size: 12px;")
        
        # Process events to ensure UI is displayed
        logger.debug("Recording overlay shown - setup complete")
        QtWidgets.QApplication.processEvents()  # Process pending events to ensure UI is displayed
        
        # Now initialize recording timer and remaining UI
        self.start_time = None
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        
        # Complete UI setup
        self.setup_ui()
        
        # Use a short timer to start recording after UI is fully displayed
        logger.debug("Setting up timer to emit recording_started signal with slight delay")
        QtCore.QTimer.singleShot(100, self._emit_recording_started)
        
    def setup_ui(self):
        """Set up the UI components"""
        # Main layout
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)  # Add some padding
        
        # Title bar
        title_layout = QtWidgets.QHBoxLayout()
        title_label = QtWidgets.QLabel("🎤 Recording")
        title_label.setStyleSheet("color: white; font-weight: bold; font-size: 14px;")
        title_layout.addWidget(title_label)
        
        # Add timer label (already created)
        title_layout.addWidget(self.timer_label)
        
        title_layout.addStretch()
        
        # Close button
        close_btn = QtWidgets.QPushButton("×")
        close_btn.setFixedSize(24, 24)  # Slightly larger
        close_btn.setStyleSheet("""
            QPushButton {
                color: white;
                background: transparent;
                border: none;
                font-size: 20px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 12px;
            }
        """)
        close_btn.setToolTip("Cancel recording")
        # Wrap the cancel_recording method for debugging
        def on_close_btn_clicked():
            logger.debug("Close button clicked by user")
            self.cancel_recording()
        close_btn.clicked.connect(on_close_btn_clicked)
        title_layout.addWidget(close_btn)
        
        # Add profile display
        self.profiles_label = QtWidgets.QLabel()
        self.profiles_label.setStyleSheet("color: #cccccc; font-size: 11px;")
        self.profiles_label.setWordWrap(True)
        
        # Add waveform widget
        self.waveform = WaveformWidget(self)
        
        # Status layout 
        status_layout = QtWidgets.QHBoxLayout()
        status_layout.addWidget(self.status_label)
        
        # Animation label (for recording indicator)
        self.animation_label = QtWidgets.QLabel("●")
        self.animation_label.setStyleSheet("color: red; font-size: 16px;")
        status_layout.addWidget(self.animation_label)
        
        # Setup recording indicator animation early
        self.animation_timer = QtCore.QTimer(self)
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_timer.start(500)  # Blink every 500ms
        self.animation_state = True
        
        # Button layout
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()  # Space on the left
        
        # Create a vertical layout for the Done button and its shortcut hint
        done_btn_layout = QtWidgets.QVBoxLayout()
        done_btn_layout.setSpacing(2)  # Reduce spacing between button and hint
        
        # Done button 
        self.done_btn = QtWidgets.QPushButton("Done")
        self.done_btn.setFixedWidth(100)  # Fixed width for consistency
        self.done_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.done_btn.clicked.connect(self.finish_recording)
        done_btn_layout.addWidget(self.done_btn)
        
        # Add space key hint
        self.space_hint = QtWidgets.QLabel("or press Space")
        self.space_hint.setStyleSheet("color: #aaaaaa; font-size: 9px; padding: 0;")
        self.space_hint.setAlignment(QtCore.Qt.AlignCenter)
        done_btn_layout.addWidget(self.space_hint)
        
        button_layout.addLayout(done_btn_layout)
        
        # Record Again button (initially hidden)
        self.record_again_btn = QtWidgets.QPushButton("Record Again")
        self.record_again_btn.setFixedWidth(120)  # Fixed width for consistency
        self.record_again_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.record_again_btn.clicked.connect(self.start_new_recording)
        self.record_again_btn.hide()  # Initially hidden
        button_layout.addWidget(self.record_again_btn)
        
        button_layout.addStretch()  # Space on the right
        
        # Add layouts to main layout
        main_layout.addLayout(title_layout)
        main_layout.addWidget(self.profiles_label)  # Add profiles display
        main_layout.addSpacing(5)
        main_layout.addWidget(self.waveform)  # Add waveform widget
        main_layout.addLayout(status_layout)
        main_layout.addSpacing(10)
        main_layout.addLayout(button_layout)
        
        # Set layout
        self.setLayout(main_layout)
        
        logger.info("Recording overlay UI setup complete")
        
    def start_recording(self):
        """Start the actual recording timer - called when audio recording starts"""
        self.start_time = QtCore.QTime.currentTime()
        self.timer.start(1000)  # Update every second
        self.waveform.start_recording()  # Start waveform animation
        logger.debug("Recording UI timer and waveform visualization started")
        
    def update_timer(self):
        """Update the timer display"""
        if self.start_time:
            elapsed = self.start_time.secsTo(QtCore.QTime.currentTime())
            minutes = elapsed // 60
            seconds = elapsed % 60
            self.timer_label.setText(f"{minutes:02d}:{seconds:02d}")
        
    def update_animation(self):
        """Update the recording indicator animation"""
        if self.animation_state:
            self.animation_label.setStyleSheet("color: red; font-size: 16px;")
        else:
            self.animation_label.setStyleSheet("color: transparent; font-size: 16px;")
        self.animation_state = not self.animation_state
        
    def position_in_corner(self, position="top-right", margin=100):
        """Position the widget in a screen corner"""
        screen = QtWidgets.QDesktopWidget().screenGeometry()
        
        if position == "top-right":
            x = screen.width() - self.width() - margin
            y = margin
        elif position == "top-left":
            x = margin
            y = margin
        elif position == "bottom-right":
            x = screen.width() - self.width() - margin
            y = screen.height() - self.height() - margin
        elif position == "bottom-left":
            x = margin
            y = screen.height() - self.height() - margin
        else:  # center (fallback)
            x = (screen.width() - self.width()) // 2
            y = (screen.height() - self.height()) // 2
            
        self.move(x, y)
        
    def center_on_screen(self):
        """Center the widget on screen"""
        self.position_in_corner("center")
        
    def finish_recording(self):
        """Signal that recording is done"""
        self.timer.stop()
        self.animation_timer.stop()
        self.waveform.stop_recording()  # Stop waveform animation
        self.status_label.setText("Processing...")
        self.done_btn.setEnabled(False)
        self.done_btn.setText("Please wait...")
        logger.info("Recording finished by user")
        self.recording_done.emit()
        
    def cancel_recording(self):
        """Signal that recording is cancelled"""
        logger.info("Recording cancelled by user - calling stack trace for debugging")
        import traceback
        stack_trace = ''.join(traceback.format_stack())
        logger.debug(f"Cancel recording stack trace:\n{stack_trace}")
        
        self.timer.stop()
        self.animation_timer.stop()
        self.waveform.stop_recording()  # Stop waveform animation
        self.recording_cancelled.emit()
        self.close()
        
    def show_transcription_result(self, success, text_or_error):
        """
        Show transcription result or error
        
        Args:
            success (bool): Whether transcription was successful
            text_or_error (str): Transcription text or error message
        """
        # Hide the space hint when showing results
        self.space_hint.hide()
        
        if success:
            self.status_label.setText("Copied to clipboard!")
            self.done_btn.setText("Close")
            self.done_btn.setEnabled(True)
            self.done_btn.clicked.disconnect()
            self.done_btn.clicked.connect(self.close)
            
            # Show Record Again button
            self.record_again_btn.show()
        else:
            self.status_label.setText("Transcription failed")
            error_dialog = QtWidgets.QMessageBox()
            error_dialog.setIcon(QtWidgets.QMessageBox.Critical)
            error_dialog.setWindowTitle("Error")
            error_dialog.setText("Failed to transcribe audio")
            error_dialog.setDetailedText(text_or_error)
            error_dialog.setStandardButtons(QtWidgets.QMessageBox.Retry | QtWidgets.QMessageBox.Cancel)
            
            result = error_dialog.exec_()
            
            if result == QtWidgets.QMessageBox.Retry:
                self.status_label.setText("Retrying...")
                self.recording_done.emit()  # Try again
            else:
                self.close()
        
    def showEvent(self, event):
        """Handle show event"""
        super().showEvent(event)
        # Don't set focus - we want to stay in background
        
    def paintEvent(self, event):
        """Custom paint event for rounded rectangle background"""
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        # Create rounded rectangle
        rect = self.rect()
        painter.setBrush(QtGui.QColor(40, 40, 40, 230))
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawRoundedRect(rect, 10, 10)
        
    def mousePressEvent(self, event):
        """Handle mouse press for dragging"""
        if event.button() == QtCore.Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
            
    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging"""
        if event.buttons() == QtCore.Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
            
    def keyPressEvent(self, event):
        """Handle key press events"""
        # If Space key is pressed
        if event.key() == QtCore.Qt.Key_Space:
            logger.debug(f"Space key pressed - timer active: {self.timer.isActive()}, button text: '{self.done_btn.text()}', enabled: {self.done_btn.isEnabled()}")
            
            # ONLY handle Space if we're in active recording mode
            if self.timer.isActive() and self.done_btn.isEnabled() and self.done_btn.text() == "Done":
                logger.debug("Space key - triggering finish_recording()")
                self.finish_recording()
            else:
                logger.debug("Space key - ignoring in current state")
            
            # Always consume the event to prevent it from being processed elsewhere
            event.accept()
            return
        
        # Handle Escape key - log it and don't let it auto-close the window
        if event.key() == QtCore.Qt.Key_Escape:
            logger.debug("Escape key pressed - ignoring to prevent accidental cancellation")
            event.accept()
            return
            
        # For all other keys, pass to parent
        super().keyPressEvent(event)

    def _emit_recording_started(self):
        """Emit the recording_started signal after a slight delay"""
        logger.debug("Emitting recording_started signal")
        self.recording_started.emit()

    def reset_for_recording(self):
        """Reset the overlay UI for a new recording session"""
        # Reset UI state
        self.status_label.setText("Recording...")
        self.status_label.setStyleSheet("color: white; font-size: 12px;")  # Reset to default style
        self.timer_label.setText("00:00")
        self.animation_timer.start(500)
        self.animation_state = True
        
        # Reset buttons
        self.done_btn.setText("Done")
        self.done_btn.setEnabled(True)
        if self.done_btn.receivers(self.done_btn.clicked) > 0:
            self.done_btn.clicked.disconnect()
        self.done_btn.clicked.connect(self.finish_recording)
        
        # Show space hint again
        self.space_hint.show()
        
        # Hide Record Again button
        self.record_again_btn.hide()
        
        # Reset any error state from previous recording
        self.start_time = None
        if self.timer.isActive():
            self.timer.stop()
        if self.waveform.recording:
            self.waveform.stop_recording()
        
    def start_new_recording(self):
        """Start a new recording"""
        # Reset the UI
        self.reset_for_recording()
        
        # Reset recording timers
        self.start_time = QtCore.QTime.currentTime()
        self.timer.start(1000)
        
        # Start waveform animation
        self.waveform.start_recording()
        
        # Make sure we have focus to capture key events
        self.raise_()
        self.activateWindow()
        self.setFocus()
        
        # Emit signal to start actual recording
        logger.info("Starting new recording")
        self.recording_started.emit()
    
    def set_profiles(self, profiles):
        """Set the available profiles"""
        self.profiles = profiles
        self._update_profiles_display()
        
    def update_active_profile(self, profile_number, profile_name):
        """Update the active profile"""
        self.active_profile = profile_number
        self._update_profiles_display()
        
    def _update_profiles_display(self):
        """Update the profiles label to show all profiles with active one highlighted"""
        if not self.profiles:
            return
            
        profile_parts = []
        for num, name in sorted(self.profiles.items()):
            if num == self.active_profile:
                # Highlight active profile
                profile_parts.append(f'<span style="color: #4CAF50; font-weight: bold;">{num}: {name}</span>')
            else:
                profile_parts.append(f'{num}: {name}')
                
        self.profiles_label.setText(' | '.join(profile_parts))
        
    def show_status(self, status_text, status_type="info"):
        """Show a status message"""
        if status_type == "processing":
            self.status_label.setText(status_text)
            self.status_label.setStyleSheet("color: #2196F3; font-size: 12px;")  # Blue for processing
        elif status_type == "success":
            self.status_label.setText(status_text)
            self.status_label.setStyleSheet("color: #4CAF50; font-size: 12px;")  # Green for success
        else:
            self.status_label.setText(status_text)
            self.status_label.setStyleSheet("color: white; font-size: 12px;")


class NotificationOverlay(QtWidgets.QWidget):
    """
    Small notification overlay for showing success/error messages
    """
    def __init__(self, message, icon_type="info", duration=2000, parent=None):
        """
        Initialize the notification overlay
        
        Args:
            message (str): Message to display
            icon_type (str): Icon type ("info", "success", "error")
            duration (int): Duration in milliseconds
            parent: Parent widget
        """
        super().__init__(parent)
        self.message = message
        self.icon_type = icon_type
        self.duration = duration
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the UI components"""
        # Window properties
        self.setWindowFlags(
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.Tool
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setWindowOpacity(0.9)
        
        # Main layout
        layout = QtWidgets.QHBoxLayout()
        
        # Icon
        icon_label = QtWidgets.QLabel()
        if self.icon_type == "success":
            icon_label.setText("✓")
            icon_label.setStyleSheet("color: #4CAF50; font-size: 16px; font-weight: bold;")
        elif self.icon_type == "error":
            icon_label.setText("×")
            icon_label.setStyleSheet("color: #f44336; font-size: 16px; font-weight: bold;")
        else:  # info
            icon_label.setText("ℹ")
            icon_label.setStyleSheet("color: #2196F3; font-size: 16px; font-weight: bold;")
            
        layout.addWidget(icon_label)
        
        # Message
        message_label = QtWidgets.QLabel(self.message)
        message_label.setStyleSheet("color: white;")
        layout.addWidget(message_label)
        
        # Set layout
        self.setLayout(layout)
        
        # Set size and position
        self.resize(self.sizeHint())
        self.position_at_bottom()
        
        # Auto-close timer
        QtCore.QTimer.singleShot(self.duration, self.close)
        
        # Fade-in animation
        self.fade_in()
        
    def position_at_bottom(self):
        """Position the notification at the bottom center of the screen"""
        screen = QtWidgets.QDesktopWidget().screenGeometry()
        size = self.geometry()
        x = (screen.width() - size.width()) // 2
        y = screen.height() - size.height() - 100  # 100px from bottom
        self.move(x, y)
        
    def fade_in(self):
        """Animate fade-in effect"""
        self.opacity_effect = QtWidgets.QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        
        self.fade_anim = QtCore.QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_anim.setDuration(300)
        self.fade_anim.setStartValue(0)
        self.fade_anim.setEndValue(1)
        self.fade_anim.start()
        
    def paintEvent(self, event):
        """Custom paint event for rounded rectangle background"""
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        # Create rounded rectangle
        rect = self.rect()
        painter.setBrush(QtGui.QColor(40, 40, 40, 230))
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawRoundedRect(rect, 10, 10)


def show_notification(message, icon_type="info", duration=2000):
    """
    Show a notification overlay
    
    Args:
        message (str): Message to display
        icon_type (str): Icon type ("info", "success", "error") 
        duration (int): Duration in milliseconds
    """
    notification = NotificationOverlay(message, icon_type, duration)
    notification.show()
    return notification 