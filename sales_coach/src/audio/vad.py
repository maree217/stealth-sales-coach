"""Voice Activity Detection (VAD) system using Silero VAD."""

import torch
import numpy as np
import logging
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path
import threading
import time

from ..models.config import AudioConfig


logger = logging.getLogger(__name__)


@dataclass
class VoiceSegment:
    """Represents a segment of voice activity."""
    start_time: float
    end_time: float
    confidence: float
    audio_data: Optional[np.ndarray] = None
    
    @property
    def duration(self) -> float:
        return self.end_time - self.start_time


class SileroVAD:
    """Silero Voice Activity Detection implementation."""
    
    def __init__(self, config: AudioConfig):
        self.config = config
        self.model = None
        self.sample_rate = config.sample_rate
        self.threshold = config.vad_threshold
        
        # State tracking
        self.is_loaded = False
        self.current_speech_start: Optional[float] = None
        self.voice_segments: List[VoiceSegment] = []
        
        # Buffer for processing
        self.audio_buffer = []
        self.buffer_size = int(self.sample_rate * 0.5)  # 500ms buffer
        
        logger.info(f"Initializing Silero VAD with threshold {self.threshold}")
    
    def load_model(self) -> bool:
        """Load the Silero VAD model."""
        try:
            # Try to load Silero VAD model
            model, utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False,
                onnx=False
            )
            
            self.model = model
            self.get_speech_timestamps, self.save_audio, self.read_audio, self.VADIterator, self.collect_chunks = utils
            
            # Set model to evaluation mode
            self.model.eval()
            
            self.is_loaded = True
            logger.info("Silero VAD model loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load Silero VAD model: {e}")
            logger.info("Falling back to energy-based VAD")
            return False
    
    def detect_voice_activity(self, audio_chunk: np.ndarray) -> Tuple[bool, float]:
        """
        Detect voice activity in an audio chunk.
        
        Returns:
            Tuple of (has_voice, confidence)
        """
        # Apply noise gate - skip very quiet audio
        rms = np.sqrt(np.mean(audio_chunk**2))
        noise_gate_threshold = 0.0005  # Lowered for quiet microphones (was 0.01)
        
        if rms < noise_gate_threshold:
            return False, 0.0
        
        if not self.is_loaded:
            # Fallback to energy-based VAD
            return self._energy_based_vad(audio_chunk)
        
        try:
            # Ensure audio is the right type and shape
            if audio_chunk.dtype != np.float32:
                audio_chunk = audio_chunk.astype(np.float32)
            
            # Convert to tensor
            audio_tensor = torch.from_numpy(audio_chunk)
            
            # Silero VAD expects 16kHz audio
            if self.sample_rate != 16000:
                # Simple resampling (for production, use proper resampling)
                target_length = int(len(audio_chunk) * 16000 / self.sample_rate)
                audio_tensor = torch.nn.functional.interpolate(
                    audio_tensor.unsqueeze(0).unsqueeze(0),
                    size=target_length,
                    mode='linear',
                    align_corners=False
                ).squeeze()
            
            # Get voice probability
            with torch.no_grad():
                voice_prob = self.model(audio_tensor, 16000).item()
            
            has_voice = voice_prob > self.threshold
            
            return has_voice, voice_prob
            
        except Exception as e:
            logger.warning(f"Error in Silero VAD, falling back to energy-based: {e}")
            return self._energy_based_vad(audio_chunk)
    
    def _energy_based_vad(self, audio_chunk: np.ndarray) -> Tuple[bool, float]:
        """Fallback energy-based voice activity detection."""
        # Calculate RMS energy
        rms = np.sqrt(np.mean(audio_chunk**2))
        
        # Use higher threshold for energy-based VAD to reduce false positives
        energy_threshold = max(self.threshold, 0.05)  # Minimum 0.05 threshold
        
        has_voice = rms > energy_threshold
        confidence = min(1.0, rms / (energy_threshold * 2))
        
        return has_voice, confidence
    
    def process_audio_stream(self, audio_chunk: np.ndarray, timestamp: float) -> List[VoiceSegment]:
        """
        Process continuous audio stream and return completed voice segments.
        
        Args:
            audio_chunk: Audio data chunk
            timestamp: Timestamp of this chunk
            
        Returns:
            List of completed voice segments
        """
        has_voice, confidence = self.detect_voice_activity(audio_chunk)
        
        chunk_duration = len(audio_chunk) / self.sample_rate
        completed_segments = []
        
        if has_voice:
            # Voice detected
            if self.current_speech_start is None:
                # Start of new speech segment
                self.current_speech_start = timestamp
                self.audio_buffer = [audio_chunk.copy()]
            else:
                # Continuation of speech
                self.audio_buffer.append(audio_chunk.copy())
        else:
            # No voice detected
            if self.current_speech_start is not None:
                # End of speech segment
                segment = VoiceSegment(
                    start_time=self.current_speech_start,
                    end_time=timestamp,
                    confidence=confidence,
                    audio_data=np.concatenate(self.audio_buffer) if self.audio_buffer else None
                )
                
                # Only keep segments longer than minimum duration (e.g., 0.5 seconds)
                if segment.duration > 0.5:
                    completed_segments.append(segment)
                    self.voice_segments.append(segment)
                
                # Reset state
                self.current_speech_start = None
                self.audio_buffer = []
        
        return completed_segments
    
    def get_recent_segments(self, duration: float = 30.0) -> List[VoiceSegment]:
        """Get voice segments from the last N seconds."""
        if not self.voice_segments:
            return []
        
        current_time = time.time()
        cutoff_time = current_time - duration
        
        return [
            segment for segment in self.voice_segments
            if segment.end_time >= cutoff_time
        ]
    
    def cleanup_old_segments(self, keep_duration: float = 300.0) -> None:
        """Remove old voice segments to manage memory."""
        if not self.voice_segments:
            return
        
        current_time = time.time()
        cutoff_time = current_time - keep_duration
        
        # Keep only recent segments
        self.voice_segments = [
            segment for segment in self.voice_segments
            if segment.end_time >= cutoff_time
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get VAD statistics."""
        if not self.voice_segments:
            return {
                "total_segments": 0,
                "total_speech_duration": 0.0,
                "average_segment_duration": 0.0,
                "speech_ratio": 0.0
            }
        
        total_segments = len(self.voice_segments)
        total_duration = sum(segment.duration for segment in self.voice_segments)
        
        # Calculate speech ratio over last 5 minutes
        recent_segments = self.get_recent_segments(300.0)
        recent_speech_duration = sum(segment.duration for segment in recent_segments)
        speech_ratio = recent_speech_duration / 300.0 if recent_segments else 0.0
        
        return {
            "total_segments": total_segments,
            "total_speech_duration": total_duration,
            "average_segment_duration": total_duration / total_segments,
            "speech_ratio": min(1.0, speech_ratio),
            "recent_segments": len(recent_segments)
        }


class AdaptiveVAD:
    """Adaptive VAD that adjusts threshold based on environment."""
    
    def __init__(self, config: AudioConfig):
        self.config = config
        self.base_vad = SileroVAD(config)
        
        # Adaptive parameters
        self.noise_floor = 0.001
        self.noise_samples = []
        self.adaptation_window = 1000  # samples
        
        # Background noise estimation
        self.background_thread: Optional[threading.Thread] = None
        self.is_adapting = False
    
    def start_adaptation(self) -> None:
        """Start background noise adaptation."""
        self.is_adapting = True
        self.background_thread = threading.Thread(target=self._adaptation_worker)
        self.background_thread.daemon = True
        self.background_thread.start()
        
        logger.info("Started adaptive VAD background processing")
    
    def stop_adaptation(self) -> None:
        """Stop background noise adaptation."""
        self.is_adapting = False
        if self.background_thread and self.background_thread.is_alive():
            self.background_thread.join(timeout=1.0)
    
    def _adaptation_worker(self) -> None:
        """Background worker for noise adaptation."""
        while self.is_adapting:
            try:
                # Update noise floor estimation
                if len(self.noise_samples) > 100:
                    self.noise_floor = np.percentile(self.noise_samples[-100:], 20)
                    
                    # Adapt threshold based on noise floor
                    adaptive_threshold = max(
                        self.config.vad_threshold,
                        self.noise_floor * 3.0  # 3x noise floor
                    )
                    self.base_vad.threshold = adaptive_threshold
                
                time.sleep(1.0)  # Update every second
                
            except Exception as e:
                logger.error(f"Error in VAD adaptation: {e}")
    
    def detect_voice_activity(self, audio_chunk: np.ndarray) -> Tuple[bool, float]:
        """Detect voice activity with adaptation."""
        # Calculate energy for noise estimation
        energy = np.sqrt(np.mean(audio_chunk**2))
        
        # Use base VAD for detection
        has_voice, confidence = self.base_vad.detect_voice_activity(audio_chunk)
        
        # Update noise samples when no voice is detected
        if not has_voice:
            self.noise_samples.append(energy)
            if len(self.noise_samples) > self.adaptation_window:
                self.noise_samples = self.noise_samples[-self.adaptation_window:]
        
        return has_voice, confidence
    
    def process_audio_stream(self, audio_chunk: np.ndarray, timestamp: float) -> List[VoiceSegment]:
        """Process audio stream with adaptive VAD."""
        return self.base_vad.process_audio_stream(audio_chunk, timestamp)


def create_vad(config: AudioConfig, adaptive: bool = True) -> SileroVAD:
    """Factory function to create VAD instance."""
    if adaptive:
        vad = AdaptiveVAD(config)
    else:
        vad = SileroVAD(config)
    
    # Try to load the model
    if not vad.base_vad.load_model() if adaptive else not vad.load_model():
        logger.warning("Using fallback energy-based VAD")
    
    return vad