"""Audio capture system for macOS using CoreAudio and ScreenCaptureKit."""

import sounddevice as sd
import numpy as np
import threading
import queue
import time
import logging
from typing import Optional, Callable, List, Dict, Any
from dataclasses import dataclass
from pathlib import Path

from ..models.config import AudioConfig


logger = logging.getLogger(__name__)


@dataclass
class AudioDevice:
    """Audio device information."""
    index: int
    name: str
    channels: int
    sample_rate: float
    is_input: bool
    is_output: bool


class AudioDeviceManager:
    """Manages audio device detection and selection."""
    
    def __init__(self):
        self.devices: List[AudioDevice] = []
        self._update_devices()
    
    def _update_devices(self) -> None:
        """Update the list of available audio devices."""
        self.devices = []
        
        try:
            devices = sd.query_devices()
            for idx, device in enumerate(devices):
                self.devices.append(AudioDevice(
                    index=idx,
                    name=device['name'],
                    channels=device['max_input_channels'],
                    sample_rate=device['default_samplerate'],
                    is_input=device['max_input_channels'] > 0,
                    is_output=device['max_output_channels'] > 0
                ))
        except Exception as e:
            logger.error(f"Failed to query audio devices: {e}")
    
    def get_input_devices(self) -> List[AudioDevice]:
        """Get all available input devices."""
        return [d for d in self.devices if d.is_input]
    
    def get_output_devices(self) -> List[AudioDevice]:
        """Get all available output devices."""
        return [d for d in self.devices if d.is_output]
    
    def find_device(self, name_pattern: str) -> Optional[AudioDevice]:
        """Find device by name pattern."""
        name_lower = name_pattern.lower()
        for device in self.devices:
            if name_lower in device.name.lower():
                return device
        return None
    
    def get_default_input_device(self) -> Optional[AudioDevice]:
        """Get the default input device."""
        try:
            default_device = sd.query_devices(kind='input')
            for device in self.devices:
                if device.name == default_device['name'] and device.is_input:
                    return device
        except Exception as e:
            logger.error(f"Failed to get default input device: {e}")
        
        # Fallback to first input device
        input_devices = self.get_input_devices()
        return input_devices[0] if input_devices else None
    
    def get_best_capture_device(self) -> Optional[AudioDevice]:
        """Get the best device for capturing system + mic audio."""
        # Priority order for device selection
        preferred_patterns = [
            "aggregate",  # Aggregate device with BlackHole
            "blackhole",  # BlackHole directly
            "soundflower",  # Alternative audio routing
            "multi-output",  # Multi-output device
        ]
        
        for pattern in preferred_patterns:
            device = self.find_device(pattern)
            if device and device.is_input:
                logger.info(f"Found preferred capture device: {device.name}")
                return device
        
        # Fallback to default input device
        device = self.get_default_input_device()
        if device:
            logger.warning(f"Using fallback device: {device.name}")
        
        return device


class AudioBuffer:
    """Thread-safe circular audio buffer."""
    
    def __init__(self, max_size: int = 1000):
        self.buffer = queue.Queue(maxsize=max_size)
        self.lock = threading.Lock()
        self.dropped_chunks = 0
    
    def put(self, audio_chunk: np.ndarray) -> bool:
        """Add audio chunk to buffer. Returns False if buffer is full."""
        try:
            self.buffer.put_nowait(audio_chunk.copy())
            return True
        except queue.Full:
            self.dropped_chunks += 1
            logger.warning(f"Audio buffer full, dropped {self.dropped_chunks} chunks")
            return False
    
    def get(self, timeout: float = 0.1) -> Optional[np.ndarray]:
        """Get audio chunk from buffer."""
        try:
            return self.buffer.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def size(self) -> int:
        """Get current buffer size."""
        return self.buffer.qsize()
    
    def clear(self) -> None:
        """Clear the buffer."""
        with self.lock:
            while not self.buffer.empty():
                try:
                    self.buffer.get_nowait()
                except queue.Empty:
                    break


class AudioCaptureSystem:
    """Main audio capture system with device management and fallbacks."""
    
    def __init__(self, config: AudioConfig):
        self.config = config
        self.device_manager = AudioDeviceManager()
        self.audio_buffer = AudioBuffer(config.max_buffer_size)
        
        # State
        self.is_capturing = False
        self.current_device: Optional[AudioDevice] = None
        self.stream: Optional[sd.InputStream] = None
        
        # Callbacks
        self.audio_callback: Optional[Callable[[np.ndarray], None]] = None
        
        # Threading
        self._capture_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Statistics
        self.chunks_processed = 0
        self.total_duration = 0.0
        self.last_chunk_time = 0.0
        
        logger.info("Audio capture system initialized")
    
    def set_audio_callback(self, callback: Callable[[np.ndarray], None]) -> None:
        """Set callback function for processed audio chunks."""
        self.audio_callback = callback
    
    def _select_capture_device(self) -> Optional[AudioDevice]:
        """Select the best available capture device."""
        # Update device list
        self.device_manager._update_devices()
        
        # Try user-specified device first
        if self.config.input_device:
            device = self.device_manager.find_device(self.config.input_device)
            if device and device.is_input:
                logger.info(f"Using user-specified device: {device.name}")
                return device
            else:
                logger.warning(f"User-specified device '{self.config.input_device}' not found")
        
        # Try to find the best capture device
        device = self.device_manager.get_best_capture_device()
        if device:
            logger.info(f"Selected capture device: {device.name}")
            return device
        
        logger.error("No suitable audio capture device found")
        return None
    
    def _audio_stream_callback(self, indata: np.ndarray, frames: int, 
                              time_info: Any, status: sd.CallbackFlags) -> None:
        """Callback for audio stream."""
        if status:
            logger.warning(f"Audio stream status: {status}")
        
        # Add to buffer
        self.audio_buffer.put(indata[:, 0] if indata.ndim > 1 else indata)
        
        # Update statistics
        self.chunks_processed += 1
        self.last_chunk_time = time.time()
    
    def _process_audio_chunks(self) -> None:
        """Process audio chunks from buffer."""
        logger.info("Audio processing thread started")
        
        while not self._stop_event.is_set():
            # Get audio chunk from buffer
            audio_chunk = self.audio_buffer.get(timeout=0.1)
            
            if audio_chunk is not None:
                # Update duration
                chunk_duration = len(audio_chunk) / self.config.sample_rate
                self.total_duration += chunk_duration
                
                # Call user callback if set
                if self.audio_callback:
                    try:
                        self.audio_callback(audio_chunk)
                    except Exception as e:
                        logger.error(f"Error in audio callback: {e}")
        
        logger.info("Audio processing thread stopped")
    
    def start_capture(self) -> bool:
        """Start audio capture."""
        if self.is_capturing:
            logger.warning("Audio capture already running")
            return True
        
        # Select capture device
        self.current_device = self._select_capture_device()
        if not self.current_device:
            return False
        
        try:
            # Create audio stream
            self.stream = sd.InputStream(
                device=self.current_device.index,
                channels=1,  # Mono for simplicity
                samplerate=self.config.sample_rate,
                blocksize=int(self.config.sample_rate * self.config.chunk_duration / 10),
                callback=self._audio_stream_callback,
                dtype=np.float32
            )
            
            # Start stream
            self.stream.start()
            
            # Start processing thread
            self._stop_event.clear()
            self._capture_thread = threading.Thread(target=self._process_audio_chunks)
            self._capture_thread.start()
            
            self.is_capturing = True
            logger.info(f"Audio capture started on device: {self.current_device.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start audio capture: {e}")
            self.stop_capture()
            return False
    
    def stop_capture(self) -> None:
        """Stop audio capture."""
        if not self.is_capturing:
            return
        
        logger.info("Stopping audio capture...")
        
        # Stop processing thread
        self._stop_event.set()
        if self._capture_thread and self._capture_thread.is_alive():
            self._capture_thread.join(timeout=2.0)
        
        # Stop audio stream
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception as e:
                logger.error(f"Error stopping audio stream: {e}")
            finally:
                self.stream = None
        
        # Clear buffer
        self.audio_buffer.clear()
        
        self.is_capturing = False
        self.current_device = None
        
        logger.info("Audio capture stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current capture status."""
        return {
            "is_capturing": self.is_capturing,
            "current_device": self.current_device.name if self.current_device else None,
            "chunks_processed": self.chunks_processed,
            "total_duration": self.total_duration,
            "buffer_size": self.audio_buffer.size(),
            "dropped_chunks": self.audio_buffer.dropped_chunks,
            "last_chunk_time": self.last_chunk_time
        }
    
    def list_devices(self) -> List[Dict[str, Any]]:
        """List all available audio devices."""
        self.device_manager._update_devices()
        return [
            {
                "index": device.index,
                "name": device.name,
                "channels": device.channels,
                "sample_rate": device.sample_rate,
                "is_input": device.is_input,
                "is_output": device.is_output
            }
            for device in self.device_manager.devices
        ]


class AudioTestUtility:
    """Utility for testing audio capture setup."""
    
    @staticmethod
    def test_device(device_index: int, duration: float = 5.0, 
                   sample_rate: int = 16000) -> Dict[str, Any]:
        """Test a specific audio device."""
        results = {
            "success": False,
            "error": None,
            "rms_levels": [],
            "peak_level": 0.0,
            "silence_ratio": 0.0
        }
        
        try:
            recording = []
            
            def callback(indata, frames, time, status):
                if status:
                    print(f"Status: {status}")
                recording.append(indata.copy())
                
                # Calculate RMS for real-time monitoring
                rms = np.sqrt(np.mean(indata**2))
                results["rms_levels"].append(float(rms))
            
            with sd.InputStream(
                device=device_index,
                channels=1,
                samplerate=sample_rate,
                callback=callback
            ):
                sd.sleep(int(duration * 1000))
            
            if recording:
                audio_data = np.concatenate(recording)
                results["peak_level"] = float(np.max(np.abs(audio_data)))
                
                # Calculate silence ratio (samples below threshold)
                silence_threshold = 0.01
                silence_samples = np.sum(np.abs(audio_data) < silence_threshold)
                results["silence_ratio"] = silence_samples / len(audio_data)
                
                results["success"] = True
            
        except Exception as e:
            results["error"] = str(e)
        
        return results
    
    @staticmethod
    def find_best_input_device() -> Optional[int]:
        """Find the best input device by testing all available devices."""
        device_manager = AudioDeviceManager()
        input_devices = device_manager.get_input_devices()
        
        best_device = None
        best_score = -1
        
        for device in input_devices:
            print(f"Testing device: {device.name}")
            results = AudioTestUtility.test_device(device.index, duration=3.0)
            
            if results["success"]:
                # Score based on peak level and low silence ratio
                score = results["peak_level"] * (1 - results["silence_ratio"])
                print(f"  Score: {score:.3f}")
                
                if score > best_score:
                    best_score = score
                    best_device = device.index
            else:
                print(f"  Error: {results['error']}")
        
        return best_device