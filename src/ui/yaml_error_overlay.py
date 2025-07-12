#!/usr/bin/env python3
import logging
from PyQt5 import QtWidgets, QtCore, QtGui

logger = logging.getLogger("whisper_app")

class YamlErrorOverlay(QtWidgets.QWidget):
    """Simple overlay for YAML validation errors"""
    
    # Signals
    open_editor_requested = QtCore.pyqtSignal()  # Emitted when user wants to open editor
    dismissed = QtCore.pyqtSignal()  # Emitted when overlay is dismissed
    
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.Tool
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setFixedSize(550, 350)
        
        # Center on screen
        self._center_on_screen()
        
        self._setup_ui()
        
    def _center_on_screen(self):
        """Center the overlay on the primary screen"""
        screen = QtWidgets.QApplication.primaryScreen()
        screen_rect = screen.geometry()
        
        x = (screen_rect.width() - self.width()) // 2
        y = (screen_rect.height() - self.height()) // 2
        
        self.move(x, y)
        
    def _setup_ui(self):
        """Set up the user interface"""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Main container with background
        container = QtWidgets.QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: rgba(60, 20, 20, 240);
                border-radius: 10px;
                border: 2px solid rgba(255, 100, 100, 100);
            }
        """)
        container_layout = QtWidgets.QVBoxLayout(container)
        container_layout.setContentsMargins(25, 25, 25, 25)
        container_layout.setSpacing(20)
        
        # Error icon and title
        header_layout = QtWidgets.QHBoxLayout()
        
        # Error icon
        icon_label = QtWidgets.QLabel("⚠")
        icon_label.setStyleSheet("""
            QLabel {
                color: #ff6b6b;
                font-size: 32px;
                font-weight: bold;
            }
        """)
        icon_label.setFixedSize(50, 50)
        icon_label.setAlignment(QtCore.Qt.AlignCenter)
        
        # Title
        title_label = QtWidgets.QLabel("Configuration Error")
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 18px;
                font-weight: bold;
            }
        """)
        
        header_layout.addWidget(icon_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        container_layout.addLayout(header_layout)
        
        # Error message
        self.error_message = QtWidgets.QLabel("Your profiles.yaml configuration file contains errors and cannot be loaded.")
        self.error_message.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 220);
                font-size: 13px;
                line-height: 1.4;
                margin: 10px 0;
            }
        """)
        self.error_message.setWordWrap(True)
        container_layout.addWidget(self.error_message)
        
        # Error details (if any)
        self.error_details = QtWidgets.QTextEdit()
        self.error_details.setStyleSheet("""
            QTextEdit {
                background-color: rgba(20, 20, 20, 180);
                border: 1px solid rgba(255, 255, 255, 50);
                border-radius: 5px;
                color: #ffaa88;
                font-family: 'Consolas', monospace;
                font-size: 11px;
                padding: 8px;
            }
        """)
        self.error_details.setMaximumHeight(80)
        self.error_details.setReadOnly(True)
        container_layout.addWidget(self.error_details)
        
        # Instructions
        instructions = QtWidgets.QLabel("Click 'Open Editor' to fix the configuration file, then restart the application.")
        instructions.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 180);
                font-size: 12px;
                font-style: italic;
                margin: 5px 0;
            }
        """)
        instructions.setWordWrap(True)
        container_layout.addWidget(instructions)
        
        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        
        dismiss_btn = QtWidgets.QPushButton("Dismiss")
        dismiss_btn.setFixedSize(100, 35)
        dismiss_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(120, 120, 120, 180);
                border: 1px solid rgba(255, 255, 255, 100);
                border-radius: 5px;
                color: white;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(140, 140, 140, 180);
            }
        """)
        dismiss_btn.clicked.connect(self._dismiss)
        
        open_editor_btn = QtWidgets.QPushButton("Open Editor")
        open_editor_btn.setFixedSize(120, 35)
        open_editor_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(220, 100, 50, 180);
                border: 1px solid rgba(255, 255, 255, 100);
                border-radius: 5px;
                color: white;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(240, 120, 70, 180);
            }
        """)
        open_editor_btn.clicked.connect(self._open_editor)
        open_editor_btn.setDefault(True)
        
        button_layout.addStretch()
        button_layout.addWidget(dismiss_btn)
        button_layout.addWidget(open_editor_btn)
        container_layout.addLayout(button_layout)
        
        layout.addWidget(container)
        
    def _open_editor(self):
        """Request to open the profiles editor"""
        logger.info("User requested to open profiles editor from error overlay")
        self.open_editor_requested.emit()
        self.hide()
        
    def _dismiss(self):
        """Dismiss the error overlay"""
        logger.info("YAML error overlay dismissed by user")
        self.dismissed.emit()
        self.hide()
        
    def show_error(self, error_message="", error_details=""):
        """Show the overlay with specific error information"""
        if error_message:
            self.error_message.setText(error_message)
        
        if error_details:
            self.error_details.setText(error_details)
            self.error_details.show()
        else:
            self.error_details.hide()
            
        self.show()
        self.raise_()
        self.activateWindow()
        
    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == QtCore.Qt.Key_Escape:
            self._dismiss()
        elif event.key() == QtCore.Qt.Key_Return or event.key() == QtCore.Qt.Key_Enter:
            self._open_editor()
        else:
            super().keyPressEvent(event)