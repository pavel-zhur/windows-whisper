import sys
import pyaudio
import keyboard
import requests
from PyQt5.QtCore import QT_VERSION_STR
import numpy as np
import pkg_resources

def test_environment():
    """Test if all required packages are properly installed"""
    print("Python version:", sys.version)
    print("\nRequired packages:")
    print("PyAudio version:", pyaudio.__version__)
    # Get keyboard version from pkg_resources instead
    keyboard_version = pkg_resources.get_distribution('keyboard').version
    print("Keyboard version:", keyboard_version)
    print("Requests version:", requests.__version__)
    print("PyQt5 version:", QT_VERSION_STR)
    print("NumPy version:", np.__version__)
    
    # Test keyboard module functionality
    print("\nTesting keyboard module...")
    print("Registered hotkeys:", keyboard._hooks)

if __name__ == "__main__":
    test_environment() 