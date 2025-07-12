#!/usr/bin/env python3
import logging
from PyQt5 import QtWidgets, QtCore, QtGui

logger = logging.getLogger("whisper_app")

class ApiTokenOverlay(QtWidgets.QWidget):
    """Simple overlay for API token input"""
    
    # Signals
    token_saved = QtCore.pyqtSignal(str)  # Emitted when token is saved
    cancelled = QtCore.pyqtSignal()  # Emitted when cancelled
    
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.Tool
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setFixedSize(500, 300)
        
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
                background-color: rgba(40, 40, 40, 240);
                border-radius: 10px;
                border: 2px solid rgba(255, 255, 255, 50);
            }
        """)
        container_layout = QtWidgets.QVBoxLayout(container)
        container_layout.setContentsMargins(25, 25, 25, 25)
        container_layout.setSpacing(20)
        
        # Title
        title_label = QtWidgets.QLabel("API Token Setup")
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 10px;
            }
        """)
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        container_layout.addWidget(title_label)
        
        # Description
        desc_label = QtWidgets.QLabel("Please enter your OpenAI API key to continue:")
        desc_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 200);
                font-size: 12px;
                margin-bottom: 10px;
            }
        """)
        desc_label.setWordWrap(True)
        desc_label.setAlignment(QtCore.Qt.AlignCenter)
        container_layout.addWidget(desc_label)
        
        # Token input
        self.token_input = QtWidgets.QLineEdit()
        self.token_input.setPlaceholderText("sk-...")
        self.token_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.token_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(60, 60, 60, 180);
                border: 2px solid rgba(255, 255, 255, 100);
                border-radius: 5px;
                padding: 10px;
                color: white;
                font-size: 12px;
                font-family: 'Consolas', monospace;
            }
            QLineEdit:focus {
                border-color: rgba(0, 120, 215, 200);
            }
        """)
        container_layout.addWidget(self.token_input)
        
        # Show/Hide password button
        show_hide_btn = QtWidgets.QPushButton("Show")
        show_hide_btn.setFixedSize(60, 30)
        show_hide_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(80, 80, 80, 180);
                border: 1px solid rgba(255, 255, 255, 100);
                border-radius: 4px;
                color: white;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: rgba(100, 100, 100, 180);
            }
        """)
        show_hide_btn.clicked.connect(self._toggle_password_visibility)
        
        input_container = QtWidgets.QHBoxLayout()
        input_container.addWidget(self.token_input)
        input_container.addWidget(show_hide_btn)
        container_layout.addLayout(input_container)
        
        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        
        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.setFixedSize(100, 35)
        cancel_btn.setStyleSheet("""
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
        cancel_btn.clicked.connect(self._cancel)
        
        save_btn = QtWidgets.QPushButton("Save")
        save_btn.setFixedSize(100, 35)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 120, 215, 180);
                border: 1px solid rgba(255, 255, 255, 100);
                border-radius: 5px;
                color: white;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(20, 140, 235, 180);
            }
        """)
        save_btn.clicked.connect(self._save_token)
        save_btn.setDefault(True)  # Enter key will trigger this
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        container_layout.addLayout(button_layout)
        
        layout.addWidget(container)
        
        # Connect Enter key to save
        self.token_input.returnPressed.connect(self._save_token)
        
        # Focus on input
        self.token_input.setFocus()
        
    def _toggle_password_visibility(self):
        """Toggle password visibility"""
        sender = self.sender()
        if self.token_input.echoMode() == QtWidgets.QLineEdit.Password:
            self.token_input.setEchoMode(QtWidgets.QLineEdit.Normal)
            sender.setText("Hide")
        else:
            self.token_input.setEchoMode(QtWidgets.QLineEdit.Password)
            sender.setText("Show")
            
    def _save_token(self):
        """Save the token"""
        token = self.token_input.text().strip()
        if not token:
            QtWidgets.QMessageBox.warning(self, "Invalid Token", "Please enter a valid API token.")
            return
            
        if not token.startswith("sk-"):
            reply = QtWidgets.QMessageBox.question(
                self, "Confirm Token", 
                "The token doesn't start with 'sk-'. Are you sure this is correct?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No
            )
            if reply == QtWidgets.QMessageBox.No:
                return
                
        logger.info("API token saved by user")
        self.token_saved.emit(token)
        self.hide()
        
    def _cancel(self):
        """Cancel token setup"""
        logger.info("Token setup cancelled by user")
        self.cancelled.emit()
        self.hide()
        
    def show_overlay(self, current_token=""):
        """Show the overlay with optional current token"""
        if current_token:
            self.token_input.setText(current_token)
        self.show()
        self.raise_()
        self.activateWindow()
        self.token_input.setFocus()
        self.token_input.selectAll()
        
    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == QtCore.Qt.Key_Escape:
            self._cancel()
        else:
            super().keyPressEvent(event)