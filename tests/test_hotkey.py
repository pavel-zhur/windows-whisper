import keyboard
import sys
import time
from threading import Event

def on_hotkey_pressed():
    """Callback function when hotkey is pressed"""
    print("\nHotkey (Ctrl+Space) pressed!")
    return True

def test_hotkey():
    """Test hotkey detection"""
    print("Testing hotkey functionality...")
    print("Press Ctrl+Space to test the hotkey")
    print("Press Esc to exit")
    
    # Create an event to handle exit
    exit_event = Event()
    
    # Register the hotkey
    try:
        keyboard.add_hotkey('ctrl+space', on_hotkey_pressed)
        print("* Hotkey registered successfully")
        
        # Register escape to exit
        keyboard.add_hotkey('esc', lambda: exit_event.set())
        
        # Wait until Esc is pressed
        while not exit_event.is_set():
            sys.stdout.write(".")
            sys.stdout.flush()
            time.sleep(1)
            
    except Exception as e:
        print(f"Error registering hotkey: {e}")
    finally:
        # Clean up
        keyboard.unhook_all()
        print("\n* Cleaned up hotkey bindings")

if __name__ == "__main__":
    test_hotkey() 