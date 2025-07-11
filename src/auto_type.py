import time
import logging
import keyboard
import pyperclip
from PyQt5 import QtCore

logger = logging.getLogger("whisper_app")

class AutoTyper(QtCore.QObject):
    """
    Handles automatic typing of transcribed text using reliable clipboard method
    """
    typing_finished = QtCore.pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.typing_speed = 0.01  # Seconds between characters
        
    def type_text(self, text):
        """
        Type text character by character with realistic speed
        
        Args:
            text (str): Text to type
        """
        if not text or not text.strip():
            logger.warning("No text to type")
            self.typing_finished.emit()
            return
            
        try:
            logger.info(f"Auto-typing {len(text)} characters: '{text[:50]}...'")
            
            # Small delay to ensure the previous app regains focus
            time.sleep(0.2)
            
            # Type character by character with small delays
            for i, char in enumerate(text):
                try:
                    keyboard.write(char)
                    time.sleep(self.typing_speed)
                except Exception as e:
                    logger.warning(f"Failed to type character '{char}' at position {i}: {e}")
                    continue
                
                # Log progress every 50 characters
                if (i + 1) % 50 == 0:
                    logger.debug(f"Typed {i + 1}/{len(text)} characters")
            
            logger.info("Auto-typing completed successfully")
            self.typing_finished.emit()
            
        except Exception as e:
            logger.error(f"Error while typing: {e}")
            # Fallback to clipboard if typing fails
            self._send_text_clipboard(text)
            self.typing_finished.emit()
    
    def type_text_fast(self, text):
        """
        Type text using clipboard method (most reliable)
        
        Args:
            text (str): Text to type
        """
        if not text or not text.strip():
            logger.warning("No text to type")
            self.typing_finished.emit()
            return
            
        try:
            logger.info(f"Auto-typing {len(text)} characters using clipboard: '{text[:50]}...'")
            
            # Use clipboard method for maximum reliability
            success = self._send_text_clipboard(text)
            
            if success:
                logger.info("Auto-typing completed successfully using clipboard method")
            else:
                logger.error("Clipboard method failed")
                
            self.typing_finished.emit()
            
        except Exception as e:
            logger.error(f"Error during auto-typing: {e}")
            # Final fallback - just copy to clipboard
            try:
                pyperclip.copy(text)
                logger.warning("Auto-typing failed, text copied to clipboard for manual paste")
            except Exception as clipboard_error:
                logger.error(f"Even clipboard copy failed: {clipboard_error}")
            
            self.typing_finished.emit()
    
    def _send_text_clipboard(self, text):
        """
        Reliable method using clipboard and Ctrl+V
        
        Args:
            text (str): Text to send
            
        Returns:
            bool: True if successful
        """
        try:
            logger.debug("Using clipboard method for auto-typing")
            
            # Small delay to ensure the previous app regains focus
            time.sleep(0.2)
            
            # Save current clipboard content
            try:
                original_clipboard = pyperclip.paste()
            except:
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
            except:
                pass  # Don't fail if we can't restore clipboard
            
            return True
            
        except Exception as e:
            logger.error(f"Error with clipboard method: {e}")
            return False
