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
    """Manages hold-to-record global hotkeys for profiles"""
    
    recording_started = QtCore.pyqtSignal(int)  # Emits profile number when recording starts
    recording_stopped = QtCore.pyqtSignal()
    
    def __init__(self):
        """Initialize the hold-to-record hotkey manager for profiles"""
        super().__init__()
        self.is_recording = False
        self.active_profile = None
        self.keys_pressed = set()  # Track which keys are currently pressed
        
        # Profile hotkey combinations (Ctrl+1 through Ctrl+0)
        self.profile_combinations = {
            1: ['ctrl', '1'],
            2: ['ctrl', '2'], 
            3: ['ctrl', '3'],
            4: ['ctrl', '4'],
            5: ['ctrl', '5'],
            6: ['ctrl', '6'],
            7: ['ctrl', '7'],
            8: ['ctrl', '8'],
            9: ['ctrl', '9'],
            0: ['ctrl', '0']  # Ctrl+0 = profile 0 (or 10)
        }
        
        # All keys we need to monitor
        self.monitored_keys = {'ctrl', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0'}
        
        # Set up key event handlers - use hook for reliable detection
        keyboard.hook(self._on_key_event, suppress=False)
        logger.info(f"Hold-to-record profile hotkeys registered: Ctrl+1-0")
        
        # Test if keyboard hook is working at all
        logger.info("Testing keyboard hook registration...")
        try:
            test_pressed = keyboard.is_pressed('ctrl')
            logger.info(f"Keyboard library test - ctrl currently pressed: {test_pressed}")
        except Exception as e:
            logger.error(f"Keyboard library test failed: {e}")
        
    def _on_key_event(self, event):
        """Handle key events for profile hold-to-record"""
        try:
            # Skip if not one of our monitored keys
            if event.name not in self.monitored_keys:
                return
                
            if event.event_type == keyboard.KEY_DOWN:
                # Add key to pressed set (ignore repeats)
                if event.name not in self.keys_pressed:
                    self.keys_pressed.add(event.name)
                    logger.debug(f"Key pressed: {event.name}, currently pressed: {self.keys_pressed}")
                    
                    # Check if we have a complete profile combination and not already recording
                    if not self.is_recording:
                        for profile_num, key_combo in self.profile_combinations.items():
                            if set(key_combo) <= self.keys_pressed:
                                logger.info(f"Profile hold-to-record started: Ctrl+{profile_num % 10} (Profile {profile_num})")
                                self.is_recording = True
                                self.active_profile = profile_num
                                self.recording_started.emit(profile_num)
                                break
                        
            elif event.event_type == keyboard.KEY_UP:
                # Remove key from pressed set
                if event.name in self.keys_pressed:
                    self.keys_pressed.discard(event.name)
                    logger.debug(f"Key released: {event.name}, currently pressed: {self.keys_pressed}")
                    
                    # Check if recording should stop (if the active profile combination is no longer held)
                    if self.is_recording and self.active_profile is not None:
                        active_combo = self.profile_combinations[self.active_profile]
                        if not (set(active_combo) <= self.keys_pressed):
                            logger.info(f"Profile hold-to-record stopped: Profile {self.active_profile}")
                            self.is_recording = False
                            self.active_profile = None
                            self.recording_stopped.emit()
                        
        except Exception as e:
            logger.error(f"Error in profile hold-to-record event handler: {e}")
            
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

def setup_hold_to_record_hotkey():
    """Set up hold-to-record profile hotkeys"""
    try:
        return HoldToRecordHotkeyManager()
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