import pyaudio
import wave
import time
import sys

def test_recording(duration=5, output_file="test_recording.wav"):
    """
    Record audio for a specified duration and save to a WAV file
    
    Args:
        duration (int): Recording duration in seconds
        output_file (str): Output WAV file path
    """
    # Audio parameters
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000

    print(f"Starting {duration} second test recording...")
    
    # Initialize PyAudio
    p = pyaudio.PyAudio()
    
    try:
        # Open stream
        stream = p.open(format=FORMAT,
                       channels=CHANNELS,
                       rate=RATE,
                       input=True,
                       frames_per_buffer=CHUNK)
        
        print("* Recording...")
        
        # Record data
        frames = []
        for i in range(0, int(RATE / CHUNK * duration)):
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)
            # Print progress
            sys.stdout.write(f"\rRecording: {i*CHUNK/RATE:.1f}s / {duration}s")
            sys.stdout.flush()
            
        print("\n* Done recording")
        
        # Stop and close the stream
        stream.stop_stream()
        stream.close()
        
        # Save the recorded data as a WAV file
        wf = wave.open(output_file, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        print(f"* Recording saved to {output_file}")
        
    finally:
        # Terminate the PortAudio interface
        p.terminate()

if __name__ == "__main__":
    # Record for 5 seconds
    test_recording() 