from PyQt5 import QtCore, QtGui, QtWidgets
import logging
import keyboard

logger = logging.getLogger(__name__)

class HotkeyManager(QtCore.QObject):
    """Manages global hotkeys"""
    
    def __init__(self, shortcut_key, callback):
        """Initialize the hotkey manager"""
        super().__init__()
        self.callback = callback
        self.shortcut_key = shortcut_key.lower()
        
        # Register the hotkey
        keyboard.add_hotkey(self.shortcut_key, self._handle_hotkey, suppress=False)
        logger.info(f"Hotkey registered: {shortcut_key}")
        
    def _handle_hotkey(self):
        """Handle hotkey press"""
        try:
            logger.info("Hotkey triggered")
            # Use Qt's event loop to call the callback
            QtCore.QTimer.singleShot(0, self.callback)
        except Exception as e:
            logger.error(f"Error in hotkey callback: {e}")
            
    def unregister_all(self):
        """Unregister all hotkeys"""
        try:
            keyboard.unhook_all()
            logger.info("Hotkeys unregistered")
        except Exception as e:
            logger.error(f"Failed to unregister hotkeys: {e}")

def setup_hotkey(shortcut_key, callback):
    """Set up global hotkey"""
    try:
        return HotkeyManager(shortcut_key, callback)
    except Exception as e:
        logger.error(f"Failed to register hotkey: {e}")
        raise 