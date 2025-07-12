from PyQt5 import QtWidgets, QtCore, QtGui
import logging
import numpy as np  # Used for waveform calculations

logger = logging.getLogger(__name__)

# UI Constants
class OverlayConstants:
    # Font settings
    FONT_FAMILY = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    
    # Sizes scaled down by 1.5x (66% of original)
    TIMER_FONT_SIZE = 37  # was 56
    STATUS_FONT_SIZE = 19  # was 28
    PROFILE_NUMBER_FONT_SIZE = 16  # was 24
    PROFILE_NAME_FONT_SIZE = 17  # was 26
    PROFILE_NAME_INACTIVE_SIZE = 16  # was 24
    
    # Colors
    COLOR_WHITE = "#ffffff"
    COLOR_BLUE = "#0084ff"
    COLOR_SUCCESS = "#4CAF50"
    COLOR_GRAY_TEXT = "#999999"
    COLOR_GRAY_NUMBER = "#888888"
    COLOR_BLUE_BG = "rgba(0, 132, 255, 0.1)"
    COLOR_WHITE_BG = "rgba(255, 255, 255, 0.1)"
    
    # Sizes scaled down by 1.5x
    WINDOW_WIDTH = 373  # was 560
    WINDOW_HEIGHT = 320  # was 480
    CLOSE_BUTTON_SIZE = 27  # was 40
    PROFILE_PILL_SIZE = 27  # was 40
    PROFILE_CONTAINER_HEIGHT = 29  # was 44
    WAVEFORM_HEIGHT = 67  # was 100
    
    # Spacing scaled down by 1.5x
    PROFILE_SPACING = 5  # was 8
    PROFILE_CONTAINER_SPACING = 8  # was 12
    
    # Border radius scaled down by 1.5x
    PILL_RADIUS = 13  # was 20
    CONTAINER_RADIUS = 15  # was 22
    
    @staticmethod
    def get_font_style(size, color=COLOR_WHITE, weight=None):
        """Generate font style string"""
        style = f"""
            color: {color};
            font-size: {size}px;
            font-family: {OverlayConstants.FONT_FAMILY};
        """
        if weight:
            style = style.strip() + f"\n            font-weight: {weight};\n        "
        return style

class WaveformWidget(QtWidgets.QWidget):
    """Widget that displays an animated audio waveform"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(40)  # Reduced for scaled down UI
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
        
        # Auto-scaling parameters
        self.max_seen_level = 0.1  # Start with low max
        self.level_decay = 0.99   # Slowly decay the max level
        
        # Animation states
        self.animation_mode = "recording"  # recording, transcribing, transforming
        self.pulse_phase = 0.0
        
    def start_recording(self):
        """Start the waveform animation"""
        self.recording = True
        self.animation_mode = "recording"
        self.update()
        
    def stop_recording(self):
        """Stop the waveform animation"""
        self.recording = False
        self.waveform_data = [0.0] * 75
        self.target_waveform = [0.0] * 75
        self.update()
        
    def set_mode(self, mode):
        """Set animation mode: recording, transcribing, transforming"""
        self.animation_mode = mode
        self.pulse_phase = 0.0
        self.update()
    
    def update_animation(self):
        """Animate the waveform smoothly"""
        if self.animation_mode == "recording":
            if not self.recording:
                # Gradually return to zero when not recording
                if any(abs(x) > 0.01 for x in self.waveform_data):
                    self.waveform_data = [x * 0.9 for x in self.waveform_data]  # Slower fade out
                    self.update()
                return
                
            # Smooth transition to target values
            needs_update = False
            for i in range(len(self.waveform_data)):
                diff = self.target_waveform[i] - self.waveform_data[i]
                if abs(diff) > 0.001:
                    self.waveform_data[i] += diff * self.smoothing_factor
                    needs_update = True
                    
            if needs_update:
                self.update()
                
        elif self.animation_mode == "transcribing":
            # Pulsing dots animation
            self.pulse_phase += 0.1
            if self.pulse_phase > 2 * np.pi:
                self.pulse_phase -= 2 * np.pi
            self.update()
            
        elif self.animation_mode == "transforming":
            # Wave animation
            self.pulse_phase += 0.15
            if self.pulse_phase > 2 * np.pi:
                self.pulse_phase -= 2 * np.pi
            self.update()
            
    def add_level(self, level):
        """Add a new audio level to the waveform"""
        if not self.recording:
            return
            
        # Update max seen level (with decay)
        self.max_seen_level *= self.level_decay
        if level > self.max_seen_level:
            self.max_seen_level = level
            
        # Ensure minimum max level
        self.max_seen_level = max(self.max_seen_level, 0.05)
        
        # Add to averaging buffer
        self.last_levels.append(level)
        if len(self.last_levels) > self.max_levels:
            self.last_levels.pop(0)
            
        # Calculate smoothed level with weighted average
        weights = [0.5, 0.3, 0.2][:len(self.last_levels)]
        smoothed_level = sum(l * w for l, w in zip(reversed(self.last_levels), weights)) / sum(weights)
        
        # Auto-scale to always use full display range
        # This ensures even quiet sounds are visible
        if self.max_seen_level > 0:
            normalized = smoothed_level / self.max_seen_level
            # Apply gentle compression to prevent clipping
            if normalized > 0.8:
                normalized = 0.8 + (normalized - 0.8) * 0.5
            normalized = min(normalized, 1.0)
        else:
            normalized = 0.0
        
        # Shift existing target data left and add new normalized level
        self.target_waveform = self.target_waveform[1:] + [normalized]
        
    def paintEvent(self, event):
        """Draw the waveform"""
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        # Calculate dimensions
        width = self.width()
        height = self.height()
        center_y = height / 2
        
        # Draw zero line only for recording mode
        if self.animation_mode == "recording":
            painter.setPen(QtGui.QPen(QtGui.QColor(100, 100, 100, 100), 1, QtCore.Qt.DashLine))
            painter.drawLine(0, int(center_y), width, int(center_y))
        
        if self.animation_mode == "transcribing":
            # Draw pulsing dots for transcribing
            self._draw_transcribing_animation(painter, width, height)
        elif self.animation_mode == "transforming":
            # Draw flowing wave for transforming
            self._draw_transforming_animation(painter, width, height)
        elif self.recording or any(self.waveform_data):
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
            
    def _draw_transcribing_animation(self, painter, width, height):
        """Draw animated dots for transcribing state"""
        dot_count = 5
        dot_size = 5  # Reduced from 8
        spacing = 15  # Reduced from 20
        total_width = (dot_count - 1) * spacing
        start_x = (width - total_width) / 2
        y = height / 2
        
        painter.setPen(QtCore.Qt.NoPen)
        
        for i in range(dot_count):
            x = start_x + i * spacing
            # Create pulsing effect with phase offset
            phase = self.pulse_phase - i * 0.3
            scale = 0.5 + 0.5 * np.sin(phase)
            
            # Color transitions from blue to lighter blue with higher opacity
            color = QtGui.QColor(0, 132, 255)
            color.setAlpha(int(150 + 105 * scale))  # Increased base alpha
            painter.setBrush(color)
            
            size = dot_size * (0.8 + 0.4 * scale)  # Slightly larger dots
            painter.drawEllipse(QtCore.QPointF(x, y), size, size)
            
    def _draw_transforming_animation(self, painter, width, height):
        """Draw flowing wave animation for transforming state"""
        painter.setPen(QtCore.Qt.NoPen)
        
        # Create gradient wave
        path = QtGui.QPainterPath()
        path.moveTo(0, height / 2)
        
        points = 50
        for i in range(points + 1):
            x = i * width / points
            phase = (x / width) * 4 * np.pi - self.pulse_phase * 2
            y = height / 2 + np.sin(phase) * height * 0.2  # Reduced amplitude from 0.3
            
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
        
        # Complete the path
        path.lineTo(width, height)
        path.lineTo(0, height)
        path.closeSubpath()
        
        # Gradient from purple to blue with higher opacity
        gradient = QtGui.QLinearGradient(0, 0, width, 0)
        gradient.setColorAt(0, QtGui.QColor(147, 51, 234, 220))  # Purple with higher alpha
        gradient.setColorAt(0.5, QtGui.QColor(59, 130, 246, 220))  # Blue with higher alpha
        gradient.setColorAt(1, QtGui.QColor(147, 51, 234, 220))  # Purple with higher alpha
        
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
        self.resize(OverlayConstants.WINDOW_WIDTH, OverlayConstants.WINDOW_HEIGHT)
        
        # Position in top-right corner
        from config import OVERLAY_POSITION, OVERLAY_MARGIN
        self.position_in_corner(OVERLAY_POSITION, OVERLAY_MARGIN)
        # Don't show on init - will be shown when recording starts
        
        # Fast initialization of basic UI elements (time-critical ones)
        self.timer_label = QtWidgets.QLabel("00:00")
        self.timer_label.setStyleSheet(OverlayConstants.get_font_style(
            OverlayConstants.TIMER_FONT_SIZE, 
            OverlayConstants.COLOR_WHITE, 
            600
        ))
        self.status_label = QtWidgets.QLabel("Recording")
        self.status_label.setStyleSheet(OverlayConstants.get_font_style(
            OverlayConstants.STATUS_FONT_SIZE,
            OverlayConstants.COLOR_WHITE
        ))
        
        # Process events to ensure UI is displayed
        logger.debug("Recording overlay shown - setup complete")
        QtWidgets.QApplication.processEvents()  # Process pending events to ensure UI is displayed
        
        # Now initialize recording timer and remaining UI
        self.start_time = None
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        
        # Complete UI setup
        self.setup_ui()
        
        # Don't emit recording_started automatically
        
    def setup_ui(self):
        """Set up the UI components"""
        # Main layout with proper spacing
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(30, 20, 30, 20)
        main_layout.setSpacing(16)
        
        # Top section - Timer and close button
        top_layout = QtWidgets.QHBoxLayout()
        top_layout.setSpacing(0)
        
        # Timer section (left aligned)
        timer_section = QtWidgets.QVBoxLayout()
        timer_section.setSpacing(4)
        timer_section.addWidget(self.timer_label)
        timer_section.addWidget(self.status_label)
        top_layout.addLayout(timer_section)
        
        top_layout.addStretch()
        
        # Close button
        close_btn = QtWidgets.QPushButton("×")
        close_btn.setFixedSize(OverlayConstants.CLOSE_BUTTON_SIZE, OverlayConstants.CLOSE_BUTTON_SIZE)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                color: #999999;
                background: transparent;
                border: none;
                font-size: {int(OverlayConstants.CLOSE_BUTTON_SIZE * 0.8)}px;
                font-weight: 300;
                border-radius: {OverlayConstants.CLOSE_BUTTON_SIZE // 2}px;
            }}
            QPushButton:hover {{
                color: #ffffff;
                background: rgba(255, 255, 255, 0.1);
            }}
        """)
        close_btn.setToolTip("Cancel recording")
        def on_close_btn_clicked():
            logger.debug("Close button clicked by user")
            self.cancel_recording()
        close_btn.clicked.connect(on_close_btn_clicked)
        top_layout.addWidget(close_btn)
        
        # Profile pills display - vertical layout
        self.profiles_widget = QtWidgets.QWidget()
        self.profiles_layout = QtWidgets.QVBoxLayout(self.profiles_widget)
        self.profiles_layout.setContentsMargins(0, 0, 0, 0)
        self.profiles_layout.setSpacing(OverlayConstants.PROFILE_SPACING)
        self.profile_labels = []  # Store label widgets for updating
        
        # Add waveform widget with better sizing
        self.waveform = WaveformWidget(self)
        self.waveform.setFixedHeight(OverlayConstants.WAVEFORM_HEIGHT)
        
        # Add layouts to main layout
        main_layout.addLayout(top_layout)
        main_layout.addSpacing(8)
        main_layout.addWidget(self.waveform)
        main_layout.addSpacing(12)
        main_layout.addWidget(self.profiles_widget)
        main_layout.addStretch()
        
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
        self.waveform.stop_recording()  # Stop waveform animation
        self.status_label.setText("Processing...")
        logger.info("Recording finished by user")
        self.recording_done.emit()
        
    def cancel_recording(self):
        """Signal that recording is cancelled"""
        logger.info("Recording cancelled by user")
        
        self.timer.stop()
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
        if success:
            self.status_label.setText("Complete!")
        else:
            self.status_label.setText("Failed")
            # Just close after showing error briefly
            QtCore.QTimer.singleShot(1500, self.close)
        
    def showEvent(self, event):
        """Handle show event"""
        super().showEvent(event)
        # Don't set focus - we want to stay in background
        
    def paintEvent(self, event):
        """Custom paint event for rounded rectangle background"""
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        # Create rounded rectangle with subtle shadow
        rect = self.rect()
        
        # Shadow
        shadow_color = QtGui.QColor(0, 0, 0, 80)
        painter.setBrush(shadow_color)
        painter.setPen(QtCore.Qt.NoPen)
        shadow_rect = rect.adjusted(2, 2, 2, 2)
        painter.drawRoundedRect(shadow_rect, 12, 12)
        
        # Main background
        painter.setBrush(QtGui.QColor(30, 30, 30, 240))
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawRoundedRect(rect, 12, 12)
        
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
        # Ignore all key events - no keyboard interaction
        event.accept()

    def _emit_recording_started(self):
        """Emit the recording_started signal after a slight delay"""
        logger.debug("Emitting recording_started signal")
        self.recording_started.emit()

    def reset_for_recording(self):
        """Reset the overlay UI for a new recording session"""
        # Reset UI state
        self.status_label.setText("Recording")
        self.status_label.setStyleSheet(OverlayConstants.get_font_style(
            OverlayConstants.STATUS_FONT_SIZE,
            OverlayConstants.COLOR_WHITE
        ))
        self.timer_label.setText("00:00")
        
        # Reset any error state from previous recording
        self.start_time = None
        if self.timer.isActive():
            self.timer.stop()
        if self.waveform.recording:
            self.waveform.stop_recording()
        
        # Reset waveform animation state
        self.waveform.set_mode("recording")
        self.waveform.pulse_phase = 0.0
        self.waveform.update()
        
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
        
    @QtCore.pyqtSlot(int, str)
    def update_active_profile(self, profile_number, profile_name):
        """Update the active profile"""
        self.active_profile = profile_number
        self._update_profiles_display()
        
    def _update_profiles_display(self):
        """Update the profiles display with pill-style indicators"""
        # Clear existing labels
        for label in self.profile_labels:
            label.deleteLater()
        self.profile_labels.clear()
        
        # Clear existing layout items
        while self.profiles_layout.count():
            item = self.profiles_layout.takeAt(0)
            if item:
                item.widget().deleteLater() if item.widget() else None
        
        if not self.profiles:
            return
            
        # Create container for each profile (number + name)
        for num in sorted(self.profiles.keys()):
            if num > 5:  # Only show first 5 profiles to avoid crowding
                break
            
            # Container widget
            container = QtWidgets.QWidget()
            container.setFixedHeight(OverlayConstants.PROFILE_CONTAINER_HEIGHT)
            container_layout = QtWidgets.QHBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(OverlayConstants.PROFILE_CONTAINER_SPACING)
            
            # Number pill
            num_label = QtWidgets.QLabel(str(num))
            num_label.setAlignment(QtCore.Qt.AlignCenter)
            num_label.setFixedSize(OverlayConstants.PROFILE_PILL_SIZE, OverlayConstants.PROFILE_PILL_SIZE)
            
            # Profile name
            name_label = QtWidgets.QLabel(self.profiles[num])
            
            if num == self.active_profile:
                # Active profile - highlighted
                container.setStyleSheet(f"""
                    QWidget {{
                        background-color: {OverlayConstants.COLOR_BLUE_BG};
                        border-radius: {OverlayConstants.CONTAINER_RADIUS}px;
                    }}
                """)
                num_label.setStyleSheet(f"""
                    QLabel {{
                        background-color: {OverlayConstants.COLOR_BLUE};
                        color: white;
                        border-radius: {OverlayConstants.PILL_RADIUS}px;
                        font-size: {OverlayConstants.PROFILE_NUMBER_FONT_SIZE}px;
                        font-weight: 600;
                        font-family: {OverlayConstants.FONT_FAMILY};
                    }}
                """)
                name_label.setStyleSheet(OverlayConstants.get_font_style(
                    OverlayConstants.PROFILE_NAME_FONT_SIZE,
                    OverlayConstants.COLOR_WHITE,
                    500
                ))
            else:
                # Inactive profile
                num_label.setStyleSheet(f"""
                    QLabel {{
                        background-color: {OverlayConstants.COLOR_WHITE_BG};
                        color: {OverlayConstants.COLOR_GRAY_NUMBER};
                        border-radius: {OverlayConstants.PILL_RADIUS}px;
                        font-size: {OverlayConstants.PROFILE_NUMBER_FONT_SIZE}px;
                        font-family: {OverlayConstants.FONT_FAMILY};
                    }}
                """)
                name_label.setStyleSheet(OverlayConstants.get_font_style(
                    OverlayConstants.PROFILE_NAME_INACTIVE_SIZE,
                    OverlayConstants.COLOR_GRAY_TEXT
                ))
            
            container_layout.addWidget(num_label)
            container_layout.addWidget(name_label)
            container_layout.addStretch()
            
            self.profiles_layout.addWidget(container)
            self.profile_labels.append(container)
        
    def show_status(self, status_text, status_type="info"):
        """Show a status message"""
        if status_type == "processing":
            self.status_label.setText(status_text)
            self.status_label.setStyleSheet(OverlayConstants.get_font_style(
                OverlayConstants.STATUS_FONT_SIZE,
                OverlayConstants.COLOR_BLUE
            ))
            # Update waveform animation based on status
            if "Transcribing" in status_text:
                self.waveform.set_mode("transcribing")
            elif "Transforming" in status_text:
                self.waveform.set_mode("transforming")
        elif status_type == "success":
            self.status_label.setText(status_text)
            self.status_label.setStyleSheet(OverlayConstants.get_font_style(
                OverlayConstants.STATUS_FONT_SIZE,
                OverlayConstants.COLOR_SUCCESS
            ))
        else:
            self.status_label.setText(status_text)
            self.status_label.setStyleSheet(OverlayConstants.get_font_style(
                OverlayConstants.STATUS_FONT_SIZE,
                OverlayConstants.COLOR_WHITE
            ))


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