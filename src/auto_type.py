import time
import logging
import keyboard
import pyperclip
from PyQt5 import QtCore

logger = logging.getLogger("whisper_app")

class AutoTypingWorker(QtCore.QThread):
    """Worker thread for auto-typing to avoid blocking the main UI thread"""
    typing_finished = QtCore.pyqtSignal(bool)  # True if successful
    
    def __init__(self, text):
        super().__init__()
        self.text = text
        
    def run(self):
        """Run the auto-typing in a separate thread"""
        try:
            success = self._send_text_clipboard(self.text)
            self.typing_finished.emit(success)
        except Exception as e:
            self.typing_finished.emit(False)
    
    def _send_text_clipboard(self, text):
        """
        Reliable method using clipboard and Ctrl+V
        
        Args:
            text (str): Text to send
            
        Returns:
            bool: True if successful
        """
        try:
            
            # Small delay to ensure the previous app regains focus
            time.sleep(0.2)
            
            # Save current clipboard content
            try:
                original_clipboard = pyperclip.paste()
            except Exception:
                original_clipboard = ""
            
            # Copy our text to clipboard
            pyperclip.copy(text)
            time.sleep(0.1)  # Wait for clipboard to update
            
            # Verify clipboard was set correctly
            if pyperclip.paste() != text:
                logger.error("Failed to copy text to clipboard")
                return False
            
            # Send Ctrl+V to paste
            keyboard.send('ctrl+v')
            time.sleep(0.1)
            
            # Restore original clipboard (optional, comment out if not needed)
            try:
                if original_clipboard:
                    pyperclip.copy(original_clipboard)
            except Exception as e:
                logger.error(f"Could not restore original clipboard: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error with clipboard method: {e}")
            return False

class AutoTyper(QtCore.QObject):
    """
    Handles automatic typing of transcribed text using reliable clipboard method
    """
    typing_finished = QtCore.pyqtSignal(bool)  # True if successful
    
    def __init__(self):
        super().__init__()
        self.current_worker = None
    
    def type_text_fast(self, text):
        """
        Type text using clipboard method in a separate thread (most reliable)
        
        Args:
            text (str): Text to type
        """
        
        if not text or not text.strip():
            logger.warning("No text to type")
            self.typing_finished.emit(False)
            return
            
        try:
            
            # Clean up any existing worker
            if self.current_worker and self.current_worker.isRunning():
                self.current_worker.terminate()
                self.current_worker.wait(1000)  # Wait up to 1 second
            
            # Create and start worker thread
            self.current_worker = AutoTypingWorker(text)
            self.current_worker.typing_finished.connect(self._on_typing_finished)
            self.current_worker.start()
            
        except Exception as e:
            logger.error(f"Error during auto-typing setup: {e}")
            self.typing_finished.emit(False)
    
    def _on_typing_finished(self, success):
        """Handle completion of auto-typing worker"""
        if not success:
            logger.error("Auto-typing failed")
            
        self.typing_finished.emit(success)
        
        # Clean up worker
        if self.current_worker:
            self.current_worker.deleteLater()
            self.current_worker = None
