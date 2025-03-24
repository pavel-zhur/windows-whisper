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
    Handles audio recording functionality
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
        self.start_delay = 1.5  # Delay in seconds before recording starts
        self.level_callback = None  # Callback for audio levels
        logger.debug(f"AudioRecorder initialized with sample_rate={sample_rate}, channels={channels}, chunk={chunk}")
        
    def start_recording(self, max_seconds=None, callback_fn=None, level_callback=None):
        """
        Start recording audio
        
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
            logger.debug(f"Setting max recording duration to {max_seconds} seconds")
            
        self.level_callback = level_callback
        self.frames = []
        self.is_recording = True
        
        # Initialize PyAudio before the delay
        try:
            self.pyaudio = pyaudio.PyAudio()
            self.stream = self.pyaudio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk
            )
            logger.debug("Audio stream initialized successfully")
            # Clear any initial buffer
            self.stream.read(self.chunk)
        except Exception as e:
            logger.error(f"Failed to initialize audio: {e}")
            self.is_recording = False
            return False
            
        # Start recording in a separate thread
        self.recording_thread = threading.Thread(
            target=self._record,
            args=(callback_fn,)
        )
        self.recording_thread.daemon = True
        self.recording_thread.start()
        
        logger.info("Recording started")
        return True
        
    def stop_recording(self):
        """
        Stop the current recording
        
        Returns:
            bool: True if recording stopped successfully
        """
        if not self.is_recording:
            logger.warning("No recording in progress")
            return False
            
        self.is_recording = False
        if self.recording_thread:
            self.recording_thread.join(timeout=2.0)
            
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception as e:
                logger.error(f"Error closing audio stream: {e}")
                
        if self.pyaudio:
            self.pyaudio.terminate()
            self.pyaudio = None
            
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
        """Calculate audio level from raw audio data"""
        try:
            # Convert bytes to numpy array
            audio_data = np.frombuffer(data, dtype=np.int16)
            
            # Calculate RMS value
            rms = np.sqrt(np.mean(np.square(audio_data)))
            
            # Convert to range 0.0-1.0 (assuming 16-bit audio)
            level = min(1.0, rms / 32768.0)
            
            return level
        except Exception as e:
            logger.error(f"Error calculating audio level: {e}")
            return 0.0
        
    def _record(self, callback_fn=None):
        """Record audio from the microphone"""
        try:
            # Add initial delay
            logger.debug(f"Waiting {self.start_delay} seconds before starting recording...")
            time.sleep(self.start_delay)
            
            # Notify that recording is actually starting
            if callback_fn:
                callback_fn()
                logger.debug("Recording callback function executed")
            
            start_time = time.time()
            frame_count = 0
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
                    if self.level_callback:
                        level = self._calculate_audio_level(data)
                        self.level_callback(level)
                    
                    if frame_count % 100 == 0:  # Log every 100 frames
                        logger.debug(f"Recording in progress: {current_time:.1f} seconds, {frame_count} frames captured")
                except Exception as e:
                    logger.error(f"Error reading audio data: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Error in recording thread: {e}")
        finally:
            self.is_recording = False
            logger.debug(f"Recording stopped. Total frames: {len(self.frames)}, Duration: {time.time() - start_time:.1f} seconds") 