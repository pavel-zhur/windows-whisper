#!/usr/bin/env python3
import keyboard
import logging
import queue
import threading
import time

logger = logging.getLogger("whisper_app")

class GlobalHotkeyManager:
    """
    Manages global hotkey detection for Windows Whisper.
    Currently only detects clean Ctrl+Shift press/release to open recording window.
    """
    
    def __init__(self, on_hotkey_triggered):
        """
        Initialize the hotkey manager.
        
        Args:
            on_hotkey_triggered: Callback function to call when Ctrl+Shift is detected
        """
        self.on_hotkey_triggered = on_hotkey_triggered
        self.hook_active = False
        
        # Thread-safe event queue for keyboard events
        self.event_queue = queue.Queue()
        self.event_thread = None
        self.running = False
        
        # State tracking for clean Ctrl+Shift detection
        self.ctrl_pressed = False
        self.shift_pressed = False
        self.other_key_pressed = False
        self.combo_start_time = None
    
    def _on_key_event(self, event):
        """CRITICAL: This runs in keyboard hook context - must be FAST and NEVER block!"""
        # Queue all events for processing in separate thread
        try:
            self.event_queue.put_nowait({
                'name': event.name,
                'type': event.event_type,
                'time': event.time
            })
        except queue.Full:
            # If queue is full, just drop the event
            pass
        
        return False  # Never suppress keys
    
    def _process_events(self):
        """Process keyboard events in a separate thread"""
        while self.running:
            try:
                event = self.event_queue.get(timeout=0.1)
                
                if event['type'] == keyboard.KEY_DOWN:
                    if event['name'] in ['ctrl', 'left ctrl', 'right ctrl']:
                        if not self.ctrl_pressed:
                            self.ctrl_pressed = True
                            # Only start combo timer when BOTH keys are pressed
                            if self.shift_pressed and not self.combo_start_time:
                                self.combo_start_time = time.time()
                            logger.debug("Ctrl pressed")
                    elif event['name'] in ['shift', 'left shift', 'right shift']:
                        if not self.shift_pressed:
                            self.shift_pressed = True
                            # Only start combo timer when BOTH keys are pressed
                            if self.ctrl_pressed and not self.combo_start_time:
                                self.combo_start_time = time.time()
                            logger.debug("Shift pressed")
                    else:
                        # Any other key pressed - invalidate the combo
                        if self.ctrl_pressed or self.shift_pressed:
                            self.other_key_pressed = True
                            logger.debug(f"Other key pressed during combo: {event['name']}")
                
                elif event['type'] == keyboard.KEY_UP:
                    if event['name'] in ['ctrl', 'left ctrl', 'right ctrl']:
                        if self.ctrl_pressed:
                            logger.debug("Ctrl released")
                            self.ctrl_pressed = False
                            
                            # If both are now released, check for clean combo
                            if not self.ctrl_pressed and not self.shift_pressed and self.combo_start_time:
                                if not self.other_key_pressed:
                                    # Clean Ctrl+Shift press and release!
                                    elapsed = time.time() - self.combo_start_time
                                    logger.info(f"Clean Ctrl+Shift combo detected (duration: {elapsed:.2f}s)")
                                    try:
                                        self.on_hotkey_triggered()
                                    except Exception as e:
                                        logger.error(f"Error in hotkey callback: {e}")
                                self._reset_combo_state()
                                
                    elif event['name'] in ['shift', 'left shift', 'right shift']:
                        if self.shift_pressed:
                            logger.debug("Shift released")
                            self.shift_pressed = False
                            
                            # If both are now released, check for clean combo
                            if not self.ctrl_pressed and not self.shift_pressed and self.combo_start_time:
                                if not self.other_key_pressed:
                                    # Clean Ctrl+Shift press and release!
                                    elapsed = time.time() - self.combo_start_time
                                    logger.info(f"Clean Ctrl+Shift combo detected (duration: {elapsed:.2f}s)")
                                    try:
                                        self.on_hotkey_triggered()
                                    except Exception as e:
                                        logger.error(f"Error in hotkey callback: {e}")
                                self._reset_combo_state()
                    
            except queue.Empty:
                # No events, just continue
                pass
            except Exception as e:
                logger.error(f"Error processing keyboard event: {e}")
    
    def _reset_combo_state(self):
        """Reset the combo detection state"""
        self.other_key_pressed = False
        self.combo_start_time = None
        # Reset key states if somehow they're stuck
        if not self.ctrl_pressed and not self.shift_pressed:
            # Normal case - both already false
            pass
        else:
            # Edge case - reset stuck keys
            logger.debug("Resetting stuck key states")
            self.ctrl_pressed = False
            self.shift_pressed = False
    
    def start(self):
        """Start listening for global hotkeys"""
        if not self.hook_active:
            # Start event processing thread
            self.running = True
            self.event_thread = threading.Thread(target=self._process_events, daemon=True)
            self.event_thread.start()
            
            # Install keyboard hook
            keyboard.hook(self._on_key_event, suppress=False)
            self.hook_active = True
            logger.info("Global hotkey manager started - listening for Ctrl+Shift")
    
    def stop(self):
        """Stop listening for global hotkeys"""
        if self.hook_active:
            # Stop processing thread
            self.running = False
            if self.event_thread:
                self.event_thread.join(timeout=1.0)
            
            # Unhook keyboard
            keyboard.unhook_all()
            self.hook_active = False
            
            # Clear any remaining events
            while not self.event_queue.empty():
                try:
                    self.event_queue.get_nowait()
                except:
                    pass
            
            logger.info("Global hotkey manager stopped")