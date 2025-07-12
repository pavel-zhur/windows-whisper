#!/usr/bin/env python3
import keyboard
import time
from src.profile_switching_hotkey import ProfileSwitchingHotkey

def test_ctrl_shift():
    """Test function using the ProfileSwitchingHotkey class"""
    
    def on_profile_change(profile_num):
        print(f"SW {profile_num}")
    
    def on_start(profile_num):
        print(f"ON {profile_num}")
    
    def on_stop(profile_num):
        print("OFF")
    
    # Test with profiles 1,2,3,4,5,7,0 (keys 1,2,3,4,5,7,0)
    supported_profiles = [2, 3, 4, 5, 7, 0]
    hotkey_manager = ProfileSwitchingHotkey(supported_profiles, on_profile_change, on_start, on_stop)
    hotkey_manager.start()
    
    try:
        # Keep the program running
        keyboard.wait()
    except KeyboardInterrupt:
        pass
    finally:
        hotkey_manager.stop()

if __name__ == "__main__":
    test_ctrl_shift()
