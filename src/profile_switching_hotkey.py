#!/usr/bin/env python3
import keyboard
import os
import logging

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
        try:
            if os.path.exists(self.profile_file):
                with open(self.profile_file, 'r') as f:
                    return int(f.read().strip())
        except Exception as e:
            logger.warning(f"Failed to load profile from file: {e}")
        return 1  # Default to profile 1
    
    def _save_profile(self):
        try:
            with open(self.profile_file, 'w') as f:
                f.write(str(self.current_profile))
        except Exception as e:
            logger.warning(f"Failed to save profile to file: {e}")
    
    def _on_key_event(self, event):
        # Monitor ctrl, shift, and only symbols for supported profiles
        monitored_keys = {'ctrl', 'shift'} | self.monitored_symbols
        if event.name not in monitored_keys:
            return False
            
        if event.event_type == keyboard.KEY_DOWN:
            # Add modifier keys to pressed set (ignore repeats)
            if event.name in {'ctrl', 'shift'} and event.name not in self.keys_pressed:
                self.keys_pressed.add(event.name)
                
                # Check if we have both ctrl and shift
                if {'ctrl', 'shift'} <= self.keys_pressed and not self.is_combo_active:
                    self.is_combo_active = True
                    self.on_start(self.current_profile)
            
            # Handle shifted number symbols when combo is active
            elif event.name in self.monitored_symbols:
                if self.is_combo_active:
                    profile_num = self.key_to_profile.get(event.name)
                    if profile_num is not None and profile_num in self.supported_profiles:
                        if profile_num != self.current_profile:  # Only trigger if different
                            self.current_profile = profile_num
                            self._save_profile()
                            self.on_profile_change(profile_num)
                    return True  # Suppress the key when combo is active
                return False  # Don't suppress if combo not active
                    
        elif event.event_type == keyboard.KEY_UP:
            # Remove key from pressed set
            if event.name in self.keys_pressed:
                self.keys_pressed.discard(event.name)
                
                # Check if we no longer have both keys
                if self.is_combo_active and not ({'ctrl', 'shift'} <= self.keys_pressed):
                    self.is_combo_active = False
                    self.on_stop(self.current_profile)
        
        return False  # Don't suppress modifier keys
    
    def start(self):
        if not self.hook_active:
            keyboard.hook(self._on_key_event, suppress=False)
            self.hook_active = True
    
    def stop(self):
        if self.hook_active:
            keyboard.unhook_all()
            self.hook_active = False
