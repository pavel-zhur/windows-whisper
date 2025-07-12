import pyaudio
import wave
import threading
import time
import os
import logging
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)

class AudioRecorder:
    """
    Handles audio recording functionality with minimal delay
    """
    def __init__(self, sample_rate=16000, channels=1, chunk=1024):
        """
        Initialize the audio recorder
        
        Args:
            sample_rate (int): Sample rate in Hz (default: 16000)
            channels (int): Number of audio channels (default: 1 for mono)
            chunk (int): Frames per buffer (default: 1024)
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk = chunk
        self.pyaudio = None
        self.stream = None
        self.frames = []
        self.is_recording = False
        self.recording_thread = None
        self.max_seconds = 300  # Default max recording time
        self.level_callback = None  # Callback for audio levels
        
        # Initialize PyAudio immediately
        try:
            self.pyaudio = pyaudio.PyAudio()
        except Exception as e:
            logger.error(f"Failed to initialize PyAudio: {e}")
            self.pyaudio = None
            
        
    def pre_initialize(self):
        """
        Pre-initialize PyAudio to reduce latency during recording start
        """
        # If PyAudio is not yet initialized, initialize it
        if self.pyaudio is None:
            try:
                self.pyaudio = pyaudio.PyAudio()
            except Exception as e:
                logger.error(f"Failed to pre-initialize PyAudio: {e}")
                return False
        
        # Open and close a test stream to "warm up" the audio system
        try:
            test_stream = self.pyaudio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk
            )
            # Read a single chunk to initialize everything
            test_stream.read(self.chunk)
            # Close test stream
            test_stream.stop_stream()
            test_stream.close()
            return True
        except Exception as e:
            logger.error(f"Failed to pre-initialize audio stream: {e}")
            return False
    
    def start_recording(self, max_seconds=None, callback_fn=None, level_callback=None):
        """
        Start recording audio immediately with minimal delay
        
        Args:
            max_seconds (int): Maximum recording duration in seconds
            callback_fn (callable): Function to call when recording actually starts
            level_callback (callable): Function to call with audio levels (0.0-1.0)
            
        Returns:
            bool: True if recording started successfully
        """
        if self.is_recording:
            logger.warning("Recording already in progress")
            return False
            
        if max_seconds:
            self.max_seconds = max_seconds
            
        self.level_callback = level_callback
        self.frames = []
        self.is_recording = True
        
        # Ensure PyAudio is initialized
        if self.pyaudio is None:
            try:
                self.pyaudio = pyaudio.PyAudio()
            except Exception as e:
                logger.error(f"Failed to initialize audio: {e}")
                self.is_recording = False
                return False
                
        # Open audio stream with minimal overhead
        try:
            self.stream = self.pyaudio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk
            )
            
            # Start callback immediately without any delay
            if callback_fn:
                callback_fn()
            
            # Start recording thread with no delay
            self.recording_thread = threading.Thread(
                target=self._record,
                args=(None,)  # No callback here - already called
            )
            self.recording_thread.daemon = True
            self.recording_thread.start()
            
            logger.info("Recording started with minimal delay")
            return True
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            self.is_recording = False
            return False
            
    def _record(self, callback_fn=None):
        """Record audio from the microphone with no initial delay"""
        try:
            start_time = time.time()
            frame_count = 0
            
            # Check if the stream is properly initialized
            if not self.stream:
                logger.error("Stream is not initialized, cannot record audio")
                self.is_recording = False
                return
                
            # Read first chunk of data to ensure initialization
            try:
                initial_data = self.stream.read(self.chunk, exception_on_overflow=False)
                self.frames.append(initial_data)
            except Exception as e:
                logger.error(f"Failed to read initial audio data: {e}")
                self.is_recording = False
                return
                
            # Start reading audio immediately
            while self.is_recording:
                current_time = time.time() - start_time
                if current_time > self.max_seconds:
                    logger.info(f"Maximum recording time reached ({self.max_seconds} seconds)")
                    break
                    
                try:
                    data = self.stream.read(self.chunk, exception_on_overflow=False)
                    self.frames.append(data)
                    frame_count += 1
                    
                    # Calculate and send audio level
                    if self.level_callback and frame_count % 2 == 0:  # Reduced frequency for performance
                        level = self._calculate_audio_level(data)
                        self.level_callback(level)
                    
                except Exception as e:
                    logger.error(f"Error reading audio data: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Error in recording thread: {e}")
        finally:
            self.is_recording = False
            
    def stop_recording(self):
        """
        Stop the current recording
        
        Returns:
            bool: True if recording stopped successfully
        """
        if not self.is_recording:
            logger.warning("No recording in progress")
            return False
            
        # Check if we have any frames before stopping
        if not self.frames:
            logger.warning("Recording is active but no frames were captured - attempting to read more data")
            try:
                # Try to read one more chunk of data before giving up
                if self.stream and self.is_recording:
                    data = self.stream.read(self.chunk, exception_on_overflow=False)
                    self.frames.append(data)
            except Exception as e:
                logger.error(f"Failed to read additional audio data: {e}")
            
        self.is_recording = False
        if self.recording_thread:
            self.recording_thread.join(timeout=1.0)  # Reduced timeout
            
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
            except Exception as e:
                logger.error(f"Error closing audio stream: {e}")
                
        # Log the number of frames collected
        logger.info("Recording stopped")
        return True
        
    def save_wav(self, file_path):
        """
        Save the recorded audio to a WAV file
        
        Args:
            file_path (str): Path to save the WAV file
            
        Returns:
            bool: True if file saved successfully
        """
        if not self.frames:
            logger.error("No audio data to save")
            return False
            
        try:
            wf = wave.open(file_path, 'wb')
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(self.frames))
            wf.close()
            logger.info(f"Audio saved to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving audio file: {e}")
            return False
            
    def _calculate_audio_level(self, data):
        """
        Calculate audio level from raw audio data
        
        Args:
            data (bytes): Raw audio data
            
        Returns:
            float: Audio level between 0.0 and 1.0
        """
        try:
            # Convert bytes to numpy array
            audio_data = np.frombuffer(data, dtype=np.int16)
            
            # Calculate RMS value
            rms = np.sqrt(np.mean(np.square(audio_data.astype(np.float32))))
            
            # Set noise floor and normalization values
            noise_floor = 500  # Adjust for typical indoor ambient noise
            max_level = 15000  # Typical maximum for normal speech
            
            # Apply noise gate
            if rms < noise_floor:
                return 0.0
                
            # Normalize with adjusted range and log scaling
            normalized = (rms - noise_floor) / (max_level - noise_floor)
            normalized = max(0.0, min(normalized, 1.0))
            
            # Apply log scaling for better dynamics
            level = np.log10(normalized * 9 + 1) / np.log10(10)
            
            return level
            
        except Exception as e:
            logger.error(f"Error calculating audio level: {e}")
            return 0.0 