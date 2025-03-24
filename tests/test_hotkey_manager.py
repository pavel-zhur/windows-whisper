from src.hotkey import HotkeyManager
import time
import sys
from threading import Event

def test_hotkey_manager():
    """Test the enhanced HotkeyManager functionality"""
    
    # Create counters for callbacks
    callback_counts = {'space': 0, 'esc': 0}
    exit_event = Event()
    
    # Create callback functions
    def on_space():
        callback_counts['space'] += 1
        print(f"\nCtrl+Space pressed! (count: {callback_counts['space']})")
        
    def on_esc():
        callback_counts['esc'] += 1
        print(f"\nEsc pressed! (count: {callback_counts['esc']})")
        exit_event.set()
    
    # Create hotkey manager
    manager = HotkeyManager()
    
    try:
        print("Testing HotkeyManager...")
        print("* Registering hotkeys...")
        
        # Register hotkeys
        if not manager.register_hotkey('ctrl+space', on_space):
            print("Failed to register Ctrl+Space!")
            return
            
        if not manager.register_hotkey('esc', on_esc):
            print("Failed to register Esc!")
            return
            
        print("* Hotkeys registered successfully")
        print("* Press Ctrl+Space multiple times to test")
        print("* Press Esc to exit")
        
        # Test disable/enable
        time.sleep(2)
        print("\n* Disabling hotkeys for 3 seconds...")
        manager.disable()
        time.sleep(3)
        print("* Re-enabling hotkeys...")
        manager.enable()
        
        # Wait for exit
        while not exit_event.is_set():
            sys.stdout.write(".")
            sys.stdout.flush()
            time.sleep(1)
            
        print("\n\nTest results:")
        print(f"* Ctrl+Space pressed: {callback_counts['space']} times")
        print(f"* Esc pressed: {callback_counts['esc']} times")
        
    finally:
        # Clean up
        manager.unregister_all()
        print("* Cleaned up hotkey bindings")

if __name__ == "__main__":
    test_hotkey_manager() 