#!/usr/bin/env python3
import keyboard
import os
import logging
import queue
import threading

logger = logging.getLogger("whisper_app")

class ProfileSwitchingHotkey:
    def __init__(self, supported_profiles, on_profile_change, on_start, on_stop):
        self.keys_pressed = set()
        self.is_combo_active = False
        
        # Validate supported profiles
        if not supported_profiles:
            raise ValueError("supported_profiles cannot be empty")
            
        self.supported_profiles = set(supported_profiles)  # Profiles to detect
        self.on_profile_change = on_profile_change
        self.on_start = on_start
        self.on_stop = on_stop
        self.hook_active = False
        self.profile_file = "./.profile.txt"
        
        # Thread-safe event queue for keyboard events
        self.event_queue = queue.Queue()
        self.event_thread = None
        self.running = False
        
        # Load saved profile or default to 1, ensure it's supported
        loaded_profile = self._load_profile()
        if loaded_profile not in self.supported_profiles:
            self.current_profile = min(self.supported_profiles)  # First supported profile
            self._save_profile()  # Save the corrected profile
        else:
            self.current_profile = loaded_profile
        
        # Build the mapping and monitored keys based on supported profiles
        self.key_to_profile = {
            '!': 1, '@': 2, '#': 3, '$': 4, '%': 5,
            '^': 6, '&': 7, '*': 8, '(': 9, ')': 0
        }
        # Only monitor symbols for supported profiles
        self.monitored_symbols = {k for k, v in self.key_to_profile.items() if v in self.supported_profiles}
    
    def _load_profile(self):
        if not os.path.exists(self.profile_file):
            # File doesn't exist - new installation, use default
            return 1
        
        # File exists, try to read it
        try:
            with open(self.profile_file, 'r') as f:
                return int(f.read().strip())
        except Exception as e:
            logger.error(f"Failed to load profile from existing file: {e}")
            raise  # Fail if we can't read an existing file
    
    def _save_profile(self):
        try:
            with open(self.profile_file, 'w') as f:
                f.write(str(self.current_profile))
        except Exception as e:
            logger.warning(f"Failed to save profile to file: {e}")
    
    def _on_key_event(self, event):
        """CRITICAL: This runs in keyboard hook context - must be FAST and NEVER block!"""
        # Only queue relevant events - minimal processing
        monitored_keys = {'ctrl', 'shift'} | self.monitored_symbols
        if event.name in monitored_keys:
            try:
                # Queue event with timestamp - this is non-blocking
                self.event_queue.put_nowait({
                    'name': event.name,
                    'type': event.event_type,
                    'time': event.time
                })
            except queue.Full:
                # If queue is full, just drop the event - keyboard responsiveness is priority
                pass
        
        # Only suppress number keys when combo is active
        if (event.event_type == keyboard.KEY_DOWN and 
            event.name in self.monitored_symbols and 
            self.is_combo_active):
            return True  # Suppress the key
            
        return False  # Don't suppress other keys
    
    def _process_events(self):
        """Process keyboard events in a separate thread - can safely call callbacks here"""
        local_keys_pressed = set()
        local_combo_active = False
        
        while self.running:
            try:
                # Wait for events with timeout
                event = self.event_queue.get(timeout=0.1)
                
                if event['type'] == keyboard.KEY_DOWN:
                    # Add modifier keys to pressed set
                    if event['name'] in {'ctrl', 'shift'} and event['name'] not in local_keys_pressed:
                        local_keys_pressed.add(event['name'])
                        
                        # Check if we have both ctrl and shift
                        if {'ctrl', 'shift'} <= local_keys_pressed and not local_combo_active:
                            local_combo_active = True
                            self.is_combo_active = True  # Update shared state for suppression
                            try:
                                self.on_start(self.current_profile)
                            except Exception as e:
                                logger.error(f"Error in on_start callback: {e}")
                    
                    # Handle shifted number symbols when combo is active
                    elif event['name'] in self.monitored_symbols and local_combo_active:
                        profile_num = self.key_to_profile.get(event['name'])
                        if profile_num is not None and profile_num in self.supported_profiles:
                            if profile_num != self.current_profile:
                                self.current_profile = profile_num
                                self._save_profile()
                                try:
                                    self.on_profile_change(profile_num)
                                except Exception as e:
                                    logger.error(f"Error in on_profile_change callback: {e}")
                                    
                elif event['type'] == keyboard.KEY_UP:
                    # Remove key from pressed set
                    if event['name'] in local_keys_pressed:
                        local_keys_pressed.discard(event['name'])
                        
                        # Check if we no longer have both keys
                        if local_combo_active and not ({'ctrl', 'shift'} <= local_keys_pressed):
                            local_combo_active = False
                            self.is_combo_active = False  # Update shared state for suppression
                            try:
                                self.on_stop(self.current_profile)
                            except Exception as e:
                                logger.error(f"Error in on_stop callback: {e}")
                                
            except queue.Empty:
                # No events, just continue
                pass
            except Exception as e:
                logger.error(f"Error processing keyboard event: {e}")
    
    def start(self):
        if not self.hook_active:
            # Start event processing thread
            self.running = True
            self.event_thread = threading.Thread(target=self._process_events, daemon=True)
            self.event_thread.start()
            
            # Install keyboard hook
            keyboard.hook(self._on_key_event, suppress=False)
            self.hook_active = True
    
    def stop(self):
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
