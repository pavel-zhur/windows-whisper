from PyQt5 import QtCore, QtGui, QtWidgets
import logging
import keyboard
import time

logger = logging.getLogger("whisper_app")

class SimpleHotkeyManager(QtCore.QObject):
    """Simple hotkey manager using keyboard.add_hotkey"""
    
    recording_started = QtCore.pyqtSignal()
    
    def __init__(self, shortcut_key):
        """Initialize the simple hotkey manager"""
        super().__init__()
        self.shortcut_key = shortcut_key.lower()
        
        # Register the hotkey
        try:
            logger.debug(f"Attempting to register hotkey: {self.shortcut_key}")
            keyboard.add_hotkey(self.shortcut_key, self._handle_hotkey, suppress=False)
            logger.info(f"Simple hotkey registered successfully: {shortcut_key}")
            
            # Test if the keyboard library is working
            logger.debug("Testing keyboard library...")
            test_result = keyboard.is_pressed('ctrl')
            logger.debug(f"Keyboard test result (ctrl pressed): {test_result}")
            
        except Exception as e:
            logger.error(f"Failed to register simple hotkey: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
        
    def _handle_hotkey(self):
        """Handle hotkey press"""
        try:
            logger.debug("Simple hotkey triggered")
            # Use Qt's event loop to call the callback
            QtCore.QTimer.singleShot(0, self.recording_started.emit)
        except Exception as e:
            logger.error(f"Error in simple hotkey callback: {e}")
            
    def unregister_all(self):
        """Unregister all hotkeys"""
        try:
            keyboard.unhook_all()
            logger.debug("Simple hotkeys unregistered")
        except Exception as e:
            logger.error(f"Failed to unregister simple hotkeys: {e}")

class HoldToRecordHotkeyManager(QtCore.QObject):
    """Manages hold-to-record global hotkeys"""
    
    recording_started = QtCore.pyqtSignal()
    recording_stopped = QtCore.pyqtSignal()
    
    def __init__(self, shortcut_key):
        """Initialize the hold-to-record hotkey manager"""
        super().__init__()
        self.shortcut_key = shortcut_key.lower()
        self.is_recording = False
        self.is_pressed = False
        self.keys_pressed = set()  # Track which keys are currently pressed
        
        # Parse the shortcut key
        self.keys = self._parse_shortcut(shortcut_key)
        logger.info(f"Parsed keys for '{shortcut_key}': {self.keys}")
        
        # Set up key event handlers - use hook for reliable detection
        keyboard.hook(self._on_key_event, suppress=False)
        logger.info(f"Hold-to-record hotkey registered: {shortcut_key}")
        
        # Test if keyboard hook is working at all
        logger.info("Testing keyboard hook registration...")
        try:
            test_pressed = keyboard.is_pressed('ctrl')
            logger.info(f"Keyboard library test - ctrl currently pressed: {test_pressed}")
        except Exception as e:
            logger.error(f"Keyboard library test failed: {e}")
        
    def _parse_shortcut(self, shortcut):
        """Parse shortcut string into individual keys"""
        parts = shortcut.lower().replace(' ', '').split('+')
        keys = []
        for part in parts:
            if part == 'win':
                keys.append('windows')
            elif part == 'ctrl':
                keys.append('ctrl')
            elif part == 'alt':
                keys.append('alt')
            elif part == 'shift':
                keys.append('shift')
            else:
                keys.append(part)
        return keys
        
    def _on_key_event(self, event):
        """Handle key events - properly filter for physical key presses only"""
        try:
            # Skip if not one of our keys
            if event.name not in self.keys:
                return
                
            # This is the critical fix: only process the FIRST key down event, ignore repeats
            if event.event_type == keyboard.KEY_DOWN:
                # Add key to pressed set
                if event.name not in self.keys_pressed:
                    self.keys_pressed.add(event.name)
                    logger.debug(f"Key pressed: {event.name}, currently pressed: {self.keys_pressed}")
                    
                    # Check if we now have the complete combination
                    if not self.is_pressed and set(self.keys) <= self.keys_pressed:
                        self.is_pressed = True
                        if not self.is_recording:
                            logger.info("Hold-to-record: Starting recording")
                            self.is_recording = True
                            self.recording_started.emit()
                        
            elif event.event_type == keyboard.KEY_UP:
                # Remove key from pressed set
                if event.name in self.keys_pressed:
                    self.keys_pressed.discard(event.name)
                    logger.debug(f"Key released: {event.name}, currently pressed: {self.keys_pressed}")
                    
                    # Check if we no longer have the complete combination
                    if self.is_pressed and not (set(self.keys) <= self.keys_pressed):
                        self.is_pressed = False
                        if self.is_recording:
                            logger.info("Hold-to-record: Stopping recording")
                            self.is_recording = False
                            self.recording_stopped.emit()
        except Exception as e:
            logger.error(f"Error in key event handler: {e}")
            
    def _is_hotkey_combination(self):
        """Check if the hotkey combination is currently pressed"""
        try:
            return set(self.keys) <= self.keys_pressed
        except Exception as e:
            logger.error(f"Error checking hotkey combination: {e}")
            return False
            
    def unregister_all(self):
        """Unregister all hotkeys"""
        try:
            keyboard.unhook_all()
            logger.debug("Hold-to-record hotkeys unregistered")
        except Exception as e:
            logger.error(f"Failed to unregister hotkeys: {e}")

class HotkeyManager(QtCore.QObject):
    """Manages global hotkeys (legacy single-press)"""
    
    def __init__(self, shortcut_key, callback):
        """Initialize the hotkey manager"""
        super().__init__()
        self.callback = callback
        self.shortcut_key = shortcut_key.lower()
        
        # Register the hotkey
        keyboard.add_hotkey(self.shortcut_key, self._handle_hotkey, suppress=False)
        logger.debug(f"Hotkey registered: {shortcut_key}")
        
    def _handle_hotkey(self):
        """Handle hotkey press"""
        try:
            logger.debug("Hotkey triggered")
            # Use Qt's event loop to call the callback
            QtCore.QTimer.singleShot(0, self.callback)
        except Exception as e:
            logger.error(f"Error in hotkey callback: {e}")
            
    def unregister_all(self):
        """Unregister all hotkeys"""
        try:
            keyboard.unhook_all()
            logger.debug("Hotkeys unregistered")
        except Exception as e:
            logger.error(f"Failed to unregister hotkeys: {e}")

def setup_hold_to_record_hotkey(shortcut_key):
    """Set up hold-to-record global hotkey"""
    try:
        return HoldToRecordHotkeyManager(shortcut_key)
    except Exception as e:
        logger.error(f"Failed to register hold-to-record hotkey: {e}")
        raise

def setup_hotkey(shortcut_key, callback):
    """Set up global hotkey"""
    try:
        return HotkeyManager(shortcut_key, callback)
    except Exception as e:
        logger.error(f"Failed to register hotkey: {e}")
        raise

def setup_simple_hotkey(shortcut_key):
    """Set up simple global hotkey for testing"""
    try:
        return SimpleHotkeyManager(shortcut_key)
    except Exception as e:
        logger.error(f"Failed to register simple hotkey: {e}")
        raise