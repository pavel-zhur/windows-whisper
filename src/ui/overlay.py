from PyQt5 import QtWidgets, QtCore, QtGui
import sys
import logging

logger = logging.getLogger(__name__)

class RecordingOverlay(QtWidgets.QWidget):
    """
    Floating overlay UI for the recording functionality
    """
    # Signals
    recording_done = QtCore.pyqtSignal()
    recording_cancelled = QtCore.pyqtSignal()
    recording_started = QtCore.pyqtSignal()  # New signal for actual recording start
    
    def __init__(self, opacity=0.9, parent=None):
        """
        Initialize the recording overlay
        
        Args:
            opacity (float): Window opacity (0.0-1.0)
            parent: Parent widget
        """
        super().__init__(parent)
        self.opacity = opacity
        
        # Initialize countdown
        self.countdown_timer = QtCore.QTimer(self)
        self.countdown_timer.timeout.connect(self.update_countdown)
        self.countdown_value = 2  # Start countdown from 2
        
        # Initialize recording timer
        self.start_time = None
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        
        self.setup_ui()
        
        # Ensure window is properly shown
        QtCore.QTimer.singleShot(100, self.ensure_visibility)
        
        # Start countdown
        self.start_countdown()
        
    def start_countdown(self):
        """Start the countdown before recording"""
        self.status_label.setText("Starting in...")
        self.timer_label.setText(str(self.countdown_value))
        self.countdown_timer.start(1000)  # Update every second
        self.done_btn.setEnabled(False)
        
    def update_countdown(self):
        """Update the countdown display"""
        self.countdown_value -= 1
        if self.countdown_value >= 0:
            self.timer_label.setText(str(self.countdown_value))
        else:
            self.countdown_timer.stop()
            self.start_recording()
            
    def start_recording(self):
        """Start the actual recording timer"""
        self.start_time = QtCore.QTime.currentTime()
        self.timer.start(1000)  # Update every second
        self.status_label.setText("Recording...")
        self.done_btn.setEnabled(True)
        self.recording_started.emit()
        
    def update_timer(self):
        """Update the timer display"""
        if self.start_time:
            elapsed = self.start_time.secsTo(QtCore.QTime.currentTime())
            minutes = elapsed // 60
            seconds = elapsed % 60
            self.timer_label.setText(f"{minutes:02d}:{seconds:02d}")
        
    def ensure_visibility(self):
        """Ensure the overlay is visible and on top"""
        if not self.isVisible():
            self.show()
        self.raise_()
        self.activateWindow()
        
    def setup_ui(self):
        """Set up the UI components"""
        # Window properties
        self.setWindowFlags(
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.Tool |
            QtCore.Qt.X11BypassWindowManagerHint  # Helps with some window managers
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WA_ShowWithoutActivating)
        self.setWindowOpacity(self.opacity)
        
        # Main layout
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)  # Add some padding
        
        # Title bar
        title_layout = QtWidgets.QHBoxLayout()
        title_label = QtWidgets.QLabel("🎤 Recording")
        title_label.setStyleSheet("color: white; font-weight: bold; font-size: 14px;")
        title_layout.addWidget(title_label)
        
        # Add timer label
        self.timer_label = QtWidgets.QLabel("00:00")
        self.timer_label.setStyleSheet("color: white; font-weight: bold; font-size: 14px;")
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
        close_btn.clicked.connect(self.cancel_recording)
        title_layout.addWidget(close_btn)
        
        # Status layout
        status_layout = QtWidgets.QHBoxLayout()
        self.status_label = QtWidgets.QLabel("Recording...")
        self.status_label.setStyleSheet("color: white; font-size: 12px;")
        status_layout.addWidget(self.status_label)
        
        # Animation label (for recording indicator)
        self.animation_label = QtWidgets.QLabel("●")
        self.animation_label.setStyleSheet("color: red; font-size: 16px;")
        status_layout.addWidget(self.animation_label)
        
        # Button layout
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()  # Center the button
        
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
        button_layout.addWidget(self.done_btn)
        button_layout.addStretch()  # Center the button
        
        # Add layouts to main layout
        main_layout.addLayout(title_layout)
        main_layout.addSpacing(5)
        main_layout.addLayout(status_layout)
        main_layout.addSpacing(10)
        main_layout.addLayout(button_layout)
        
        # Set layout
        self.setLayout(main_layout)
        
        # Set size and position
        self.resize(250, 120)  # Slightly larger
        self.center_on_screen()
        
        # Setup recording indicator animation
        self.setup_animation()
        
        logger.info("Recording overlay UI setup complete")
        
    def setup_animation(self):
        """Set up the recording indicator animation"""
        self.animation_timer = QtCore.QTimer(self)
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_timer.start(500)  # Blink every 500ms
        self.animation_state = True
        
    def update_animation(self):
        """Update the recording indicator animation"""
        if self.animation_state:
            self.animation_label.setStyleSheet("color: red; font-size: 16px;")
        else:
            self.animation_label.setStyleSheet("color: transparent; font-size: 16px;")
        self.animation_state = not self.animation_state
        
    def center_on_screen(self):
        """Center the widget on screen"""
        screen = QtWidgets.QDesktopWidget().screenGeometry()
        size = self.geometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)
        
    def finish_recording(self):
        """Signal that recording is done"""
        self.countdown_timer.stop()
        self.timer.stop()
        self.animation_timer.stop()
        self.status_label.setText("Processing...")
        self.done_btn.setEnabled(False)
        self.done_btn.setText("Please wait...")
        logger.info("Recording finished by user")
        self.recording_done.emit()
        
    def cancel_recording(self):
        """Signal that recording is cancelled"""
        self.countdown_timer.stop()
        self.timer.stop()
        self.animation_timer.stop()
        logger.info("Recording cancelled by user")
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
            self.status_label.setText("Copied to clipboard!")
            self.done_btn.setText("Close")
            self.done_btn.setEnabled(True)
            self.done_btn.clicked.disconnect()
            self.done_btn.clicked.connect(self.close)
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