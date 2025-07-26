#!/usr/bin/env python3
import keyboard
import logging
from src.global_hotkey_manager import GlobalHotkeyManager

# Set up logging to see debug messages
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_ctrl_shift():
    """Test the clean Ctrl+Shift detection"""
    
    def on_hotkey_triggered():
        # This is called when Ctrl+Shift is pressed and released cleanly
        print(f"\n✓ CLEAN CTRL+SHIFT DETECTED! Recording window would open here.\n")
    
    print("=" * 60)
    print("Ctrl+Shift Clean Press Detection Test")
    print("=" * 60)
    print("\nInstructions:")
    print("1. Press and hold Ctrl (left or right)")
    print("2. While holding Ctrl, press and hold Shift (left or right)")
    print("3. Release both keys (order doesn't matter)")
    print("4. You should see '✓ CLEAN CTRL+SHIFT DETECTED!'")
    print("\nIf you press ANY other key while holding Ctrl+Shift,")
    print("the combo will be cancelled and won't trigger.")
    print("\nPress Ctrl+C to exit")
    print("=" * 60)
    print()
    
    # Create hotkey manager with our callback
    hotkey_manager = GlobalHotkeyManager(on_hotkey_triggered)
    hotkey_manager.start()
    
    try:
        # Keep the program running
        keyboard.wait()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        hotkey_manager.stop()
        print("Test completed")

if __name__ == "__main__":
    test_ctrl_shift()