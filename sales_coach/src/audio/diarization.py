"""Speaker diarization system using pyannote.audio."""

import torch
import numpy as np
import logging
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
import threading
import time
import tempfile
import os

try:
    from pyannote.audio import Pipeline
    from pyannote.core import Annotation, Segment
    PYANNOTE_AVAILABLE = True
except ImportError:
    PYANNOTE_AVAILABLE = False
    Pipeline = None
    Annotation = None
    Segment = None

from ..models.config import ModelConfig
from ..models.conversation import Speaker, SpeakerProfile
from .vad import VoiceSegment


logger = logging.getLogger(__name__)


@dataclass
class SpeakerSegment:
    """Represents a segment with speaker identification."""
    start_time: float
    end_time: float
    speaker_id: str
    confidence: float
    audio_data: Optional[np.ndarray] = None
    
    @property
    def duration(self) -> float:
        return self.end_time - self.start_time


class SpeakerDiarization:
    """Speaker diarization using pyannote.audio."""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.pipeline: Optional[Pipeline] = None
        self.is_loaded = False
        
        # Speaker tracking
        self.known_speakers: Dict[str, SpeakerProfile] = {}
        self.speaker_segments: List[SpeakerSegment] = []
        
        # Real-time processing
        self.audio_buffer: List[Tuple[np.ndarray, float]] = []  # (audio, timestamp)
        self.buffer_duration = 30.0  # seconds
        self.processing_overlap = 5.0  # seconds
        
        logger.info("Initializing speaker diarization system")
    
    def load_model(self) -> bool:
        """Load the pyannote.audio diarization pipeline."""
        if not PYANNOTE_AVAILABLE:
            logger.error("pyannote.audio not available. Install with: pip install pyannote.audio")
            return False
        
        try:
            # Load the diarization pipeline
            # You'll need to authenticate with HuggingFace for some models
            self.pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=True  # Set HF_TOKEN environment variable
            )
            
            # Set device
            if torch.cuda.is_available():
                self.pipeline = self.pipeline.to(torch.device("cuda"))
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                self.pipeline = self.pipeline.to(torch.device("mps"))
            
            self.is_loaded = True
            logger.info("Pyannote speaker diarization pipeline loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load pyannote pipeline: {e}")
            logger.info("Falling back to simple speaker detection")
            return False
    
    def diarize_audio(self, audio_data: np.ndarray, sample_rate: int = 16000) -> List[SpeakerSegment]:
        """
        Perform speaker diarization on audio data.
        
        Args:
            audio_data: Audio waveform
            sample_rate: Sample rate of the audio
            
        Returns:
            List of speaker segments
        """
        if not self.is_loaded:
            return self._fallback_diarization(audio_data, sample_rate)
        
        try:
            # Save audio to temporary file (pyannote expects file input)
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Write audio file
            import soundfile as sf
            sf.write(temp_path, audio_data, sample_rate)
            
            try:
                # Run diarization
                diarization = self.pipeline(temp_path)
                
                segments = []
                for turn, _, speaker in diarization.itertracks(yield_label=True):
                    segment = SpeakerSegment(
                        start_time=turn.start,
                        end_time=turn.end,
                        speaker_id=speaker,
                        confidence=1.0,  # pyannote doesn't provide confidence scores
                        audio_data=None  # We don't store audio data in segments
                    )
                    segments.append(segment)
                
                logger.debug(f"Diarized audio into {len(segments)} segments")
                return segments
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except Exception as e:
            logger.error(f"Error in pyannote diarization: {e}")
            return self._fallback_diarization(audio_data, sample_rate)
    
    def _fallback_diarization(self, audio_data: np.ndarray, sample_rate: int) -> List[SpeakerSegment]:
        """Fallback speaker detection when pyannote is not available."""
        # Simple energy-based speaker detection
        # This is a very basic implementation - in practice you'd want more sophisticated methods
        
        chunk_size = sample_rate * 2  # 2-second chunks
        segments = []
        
        for i in range(0, len(audio_data), chunk_size):
            chunk = audio_data[i:i + chunk_size]
            start_time = i / sample_rate
            end_time = min((i + chunk_size) / sample_rate, len(audio_data) / sample_rate)
            
            # Simple speaker assignment based on energy characteristics
            # This is a placeholder - real implementation would use more features
            rms = np.sqrt(np.mean(chunk**2))
            
            # Assign speaker based on energy level (very crude)
            if rms > 0.02:
                speaker_id = "SPEAKER_1" if (i // chunk_size) % 2 == 0 else "SPEAKER_2"
            else:
                continue  # Skip silent segments
            
            segment = SpeakerSegment(
                start_time=start_time,
                end_time=end_time,
                speaker_id=speaker_id,
                confidence=0.5,  # Low confidence for fallback method
                audio_data=None
            )
            segments.append(segment)
        
        return segments
    
    def process_voice_segments(self, voice_segments: List[VoiceSegment]) -> List[SpeakerSegment]:
        """Process voice segments and identify speakers."""
        if not voice_segments:
            return []
        
        # Concatenate voice segments into continuous audio
        audio_chunks = []
        timestamps = []
        
        for segment in voice_segments:
            if segment.audio_data is not None:
                audio_chunks.append(segment.audio_data)
                timestamps.append((segment.start_time, segment.end_time))
        
        if not audio_chunks:
            return []
        
        # Combine audio segments
        combined_audio = np.concatenate(audio_chunks)
        
        # Perform diarization
        speaker_segments = self.diarize_audio(combined_audio, self.config.sample_rate)
        
        # Map back to original timestamps
        # This is simplified - in practice you'd need more sophisticated mapping
        for segment in speaker_segments:
            # Adjust timestamps to match original voice segments
            if timestamps:
                base_time = timestamps[0][0]
                segment.start_time += base_time
                segment.end_time += base_time
        
        return speaker_segments
    
    def identify_speaker_roles(self, speaker_segments: List[SpeakerSegment]) -> Dict[str, Speaker]:
        """
        Map speaker IDs to roles (SALES_REP vs CUSTOMER).
        
        This is a heuristic-based approach that could be improved with:
        - Voice characteristics analysis
        - Speaking pattern analysis
        - User feedback/training
        """
        if not speaker_segments:
            return {}
        
        # Count speaking time for each speaker
        speaker_times = {}
        for segment in speaker_segments:
            if segment.speaker_id not in speaker_times:
                speaker_times[segment.speaker_id] = 0.0
            speaker_times[segment.speaker_id] += segment.duration
        
        # Sort speakers by speaking time
        sorted_speakers = sorted(speaker_times.items(), key=lambda x: x[1], reverse=True)
        
        # Heuristic: Assume the person who talks more is the sales rep
        # This could be configurable or learned from user behavior
        role_mapping = {}
        
        if len(sorted_speakers) >= 2:
            # Primary speaker (more talking) = Sales Rep
            role_mapping[sorted_speakers[0][0]] = Speaker.SALES_REP
            # Secondary speaker = Customer
            role_mapping[sorted_speakers[1][0]] = Speaker.CUSTOMER
        elif len(sorted_speakers) == 1:
            # Only one speaker detected - assume sales rep
            role_mapping[sorted_speakers[0][0]] = Speaker.SALES_REP
        
        # Additional speakers get UNKNOWN role
        for speaker_id, _ in sorted_speakers[2:]:
            role_mapping[speaker_id] = Speaker.UNKNOWN
        
        logger.info(f"Speaker role mapping: {role_mapping}")
        return role_mapping
    
    def create_speaker_profiles(self, speaker_segments: List[SpeakerSegment]) -> None:
        """Create or update speaker profiles based on segments."""
        role_mapping = self.identify_speaker_roles(speaker_segments)
        
        for segment in speaker_segments:
            speaker_id = segment.speaker_id
            role = role_mapping.get(speaker_id, Speaker.UNKNOWN)
            
            if speaker_id not in self.known_speakers:
                # Create new speaker profile
                profile = SpeakerProfile(
                    speaker=role,
                    voice_characteristics={
                        "speaker_id": speaker_id,
                        "total_duration": segment.duration
                    },
                    speaking_patterns={
                        "average_segment_length": segment.duration,
                        "segments_count": 1
                    }
                )
                self.known_speakers[speaker_id] = profile
                
            else:
                # Update existing profile
                profile = self.known_speakers[speaker_id]
                profile.voice_characteristics["total_duration"] += segment.duration
                
                # Update speaking patterns
                old_count = profile.speaking_patterns["segments_count"]
                old_avg = profile.speaking_patterns["average_segment_length"]
                new_avg = (old_avg * old_count + segment.duration) / (old_count + 1)
                
                profile.speaking_patterns["average_segment_length"] = new_avg
                profile.speaking_patterns["segments_count"] = old_count + 1
                
                profile.update_profile({})  # Update timestamp and confidence
    
    def get_speaker_for_segment(self, start_time: float, end_time: float) -> Optional[Speaker]:
        """Get the speaker role for a given time segment."""
        # Find speaker segments that overlap with the given time range
        overlapping_segments = []
        
        for segment in self.speaker_segments:
            if (segment.start_time <= end_time and segment.end_time >= start_time):
                overlap_duration = min(segment.end_time, end_time) - max(segment.start_time, start_time)
                overlapping_segments.append((segment, overlap_duration))
        
        if not overlapping_segments:
            return None
        
        # Find the segment with maximum overlap
        best_segment = max(overlapping_segments, key=lambda x: x[1])[0]
        
        # Map speaker ID to role
        if best_segment.speaker_id in self.known_speakers:
            return self.known_speakers[best_segment.speaker_id].speaker
        
        return Speaker.UNKNOWN
    
    def process_real_time(self, audio_chunk: np.ndarray, timestamp: float) -> List[SpeakerSegment]:
        """Process audio chunk for real-time speaker diarization."""
        # Add to buffer
        self.audio_buffer.append((audio_chunk, timestamp))
        
        # Remove old audio from buffer
        buffer_start_time = timestamp - self.buffer_duration
        self.audio_buffer = [
            (chunk, ts) for chunk, ts in self.audio_buffer
            if ts >= buffer_start_time
        ]
        
        # Check if we have enough audio to process
        if len(self.audio_buffer) < 10:  # Need at least 10 chunks
            return []
        
        # Process buffer every few seconds
        if len(self.audio_buffer) % 10 != 0:  # Process every 10 chunks
            return []
        
        try:
            # Combine audio from buffer
            audio_chunks = [chunk for chunk, _ in self.audio_buffer]
            combined_audio = np.concatenate(audio_chunks)
            
            # Perform diarization
            segments = self.diarize_audio(combined_audio)
            
            # Adjust timestamps
            base_time = self.audio_buffer[0][1]
            for segment in segments:
                segment.start_time += base_time
                segment.end_time += base_time
            
            # Update speaker segments
            self.speaker_segments.extend(segments)
            
            # Create/update speaker profiles
            self.create_speaker_profiles(segments)
            
            return segments
            
        except Exception as e:
            logger.error(f"Error in real-time diarization processing: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get diarization statistics."""
        return {
            "is_loaded": self.is_loaded,
            "known_speakers": len(self.known_speakers),
            "total_segments": len(self.speaker_segments),
            "speaker_profiles": {
                speaker_id: {
                    "role": profile.speaker.value,
                    "confidence": profile.confidence,
                    "segments_analyzed": profile.samples_analyzed
                }
                for speaker_id, profile in self.known_speakers.items()
            }
        }


def create_diarization_system(config: ModelConfig) -> SpeakerDiarization:
    """Factory function to create speaker diarization system."""
    system = SpeakerDiarization(config)
    
    if not system.load_model():
        logger.warning("Using fallback speaker detection")
    
    return system