"""Speech-to-text transcription system using Whisper."""

import numpy as np
import logging
import threading
import queue
import time
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass
from pathlib import Path
import tempfile
import os

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    whisper = None

try:
    import whisper_cpp as whisper_cpp
    WHISPER_CPP_AVAILABLE = True
except ImportError:
    WHISPER_CPP_AVAILABLE = False
    whisper_cpp = None

from ..models.config import ModelConfig
from ..models.conversation import ConversationTurn, Speaker
from .vad import VoiceSegment
from .diarization import SpeakerSegment


logger = logging.getLogger(__name__)


@dataclass
class TranscriptionResult:
    """Result of transcription process."""
    text: str
    confidence: float
    language: Optional[str] = None
    segments: Optional[List[Dict]] = None
    processing_time: float = 0.0


class WhisperTranscriber:
    """Whisper-based speech-to-text transcription."""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.model = None
        self.is_loaded = False
        self.model_type = "whisper"  # or "whisper_cpp"
        
        # Processing queue for real-time transcription
        self.transcription_queue = queue.Queue(maxsize=100)
        self.result_callback: Optional[Callable[[TranscriptionResult], None]] = None
        
        # Worker thread
        self.worker_thread: Optional[threading.Thread] = None
        self.is_running = False
        
        # Statistics
        self.total_transcriptions = 0
        self.total_processing_time = 0.0
        
        logger.info(f"Initializing Whisper transcriber with model: {config.whisper_model}")
    
    def load_model(self) -> bool:
        """Load the Whisper model."""
        try:
            # Try whisper_cpp first (faster)
            if WHISPER_CPP_AVAILABLE and self._try_load_whisper_cpp():
                return True
            
            # Fallback to regular whisper
            if WHISPER_AVAILABLE and self._try_load_whisper():
                return True
            
            logger.error("No Whisper implementation available")
            return False
            
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            return False
    
    def _try_load_whisper_cpp(self) -> bool:
        """Try to load whisper.cpp model."""
        try:
            model_path = self._get_whisper_cpp_model_path()
            if not model_path or not model_path.exists():
                logger.warning(f"Whisper.cpp model not found at {model_path}")
                return False
            
            self.model = whisper_cpp.Whisper.from_pretrained(
                str(model_path),
                n_threads=4
            )
            
            self.model_type = "whisper_cpp"
            self.is_loaded = True
            logger.info(f"Loaded whisper.cpp model: {model_path}")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to load whisper.cpp: {e}")
            return False
    
    def _try_load_whisper(self) -> bool:
        """Try to load regular Whisper model."""
        try:
            self.model = whisper.load_model(self.config.whisper_model)
            self.model_type = "whisper"
            self.is_loaded = True
            logger.info(f"Loaded Whisper model: {self.config.whisper_model}")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to load Whisper: {e}")
            return False
    
    def _get_whisper_cpp_model_path(self) -> Optional[Path]:
        """Get path to whisper.cpp model file."""
        # Common locations for whisper.cpp models
        model_name = f"ggml-{self.config.whisper_model}.bin"
        
        possible_paths = [
            Path.home() / ".cache" / "whisper.cpp" / model_name,
            Path("models_cache") / model_name,
            Path("/usr/local/share/whisper.cpp") / model_name,
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        return None
    
    def transcribe_audio(self, audio_data: np.ndarray, 
                        language: Optional[str] = None) -> TranscriptionResult:
        """
        Transcribe audio data to text.
        
        Args:
            audio_data: Audio waveform (float32, mono, 16kHz recommended)
            language: Optional language hint
            
        Returns:
            TranscriptionResult with text and metadata
        """
        if not self.is_loaded:
            return TranscriptionResult(
                text="",
                confidence=0.0,
                processing_time=0.0
            )
        
        start_time = time.time()
        
        try:
            if self.model_type == "whisper_cpp":
                result = self._transcribe_whisper_cpp(audio_data, language)
            else:
                result = self._transcribe_whisper(audio_data, language)
            
            processing_time = time.time() - start_time
            result.processing_time = processing_time
            
            # Update statistics
            self.total_transcriptions += 1
            self.total_processing_time += processing_time
            
            return result
            
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            return TranscriptionResult(
                text="",
                confidence=0.0,
                processing_time=time.time() - start_time
            )
    
    def _transcribe_whisper_cpp(self, audio_data: np.ndarray, 
                               language: Optional[str]) -> TranscriptionResult:
        """Transcribe using whisper.cpp."""
        # Ensure audio is float32 and normalized
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)
        
        # Whisper.cpp expects audio normalized to [-1, 1]
        if np.max(np.abs(audio_data)) > 1.0:
            audio_data = audio_data / np.max(np.abs(audio_data))
        
        result = self.model.transcribe(audio_data, language=language or "en")
        
        return TranscriptionResult(
            text=result["text"].strip(),
            confidence=1.0,  # whisper.cpp doesn't provide confidence
            language=result.get("language"),
            segments=result.get("segments")
        )
    
    def _transcribe_whisper(self, audio_data: np.ndarray, 
                           language: Optional[str]) -> TranscriptionResult:
        """Transcribe using regular Whisper."""
        # Ensure audio is float32
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)
        
        # Whisper expects audio normalized to [-1, 1]
        if np.max(np.abs(audio_data)) > 1.0:
            audio_data = audio_data / np.max(np.abs(audio_data))
        
        result = self.model.transcribe(
            audio_data,
            language=language,
            task="transcribe",
            word_timestamps=True,
            verbose=False
        )
        
        # Calculate average confidence from segments
        confidence = 0.0
        if "segments" in result and result["segments"]:
            confidences = []
            for segment in result["segments"]:
                if "avg_logprob" in segment:
                    # Convert log probability to approximate confidence
                    conf = np.exp(segment["avg_logprob"])
                    confidences.append(conf)
            
            if confidences:
                confidence = np.mean(confidences)
        
        return TranscriptionResult(
            text=result["text"].strip(),
            confidence=confidence,
            language=result.get("language"),
            segments=result.get("segments")
        )
    
    def set_result_callback(self, callback: Callable[[TranscriptionResult], None]) -> None:
        """Set callback for transcription results."""
        self.result_callback = callback
    
    def start_real_time_processing(self) -> None:
        """Start real-time transcription processing."""
        if self.is_running:
            logger.warning("Real-time processing already running")
            return
        
        self.is_running = True
        self.worker_thread = threading.Thread(target=self._transcription_worker)
        self.worker_thread.daemon = True
        self.worker_thread.start()
        
        logger.info("Started real-time transcription processing")
    
    def stop_real_time_processing(self) -> None:
        """Stop real-time transcription processing."""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=2.0)
        
        logger.info("Stopped real-time transcription processing")
    
    def queue_audio_for_transcription(self, audio_data: np.ndarray, 
                                    timestamp: float,
                                    speaker: Optional[Speaker] = None) -> bool:
        """Queue audio data for transcription."""
        try:
            self.transcription_queue.put_nowait({
                "audio_data": audio_data.copy(),
                "timestamp": timestamp,
                "speaker": speaker
            })
            return True
        except queue.Full:
            logger.warning("Transcription queue full, dropping audio")
            return False
    
    def _transcription_worker(self) -> None:
        """Worker thread for real-time transcription."""
        logger.info("Transcription worker thread started")
        
        while self.is_running:
            try:
                # Get audio from queue
                item = self.transcription_queue.get(timeout=0.1)
                
                audio_data = item["audio_data"]
                timestamp = item["timestamp"]
                speaker = item.get("speaker")
                
                # Skip very short audio segments (assume 16kHz sample rate)
                if len(audio_data) < 16000 * 0.5:  # < 0.5 seconds
                    continue
                
                # Transcribe
                result = self.transcribe_audio(audio_data)
                
                if result.text and result.text.strip():
                    # Add metadata
                    result.timestamp = timestamp
                    result.speaker = speaker
                    
                    # Call result callback if set
                    if self.result_callback:
                        try:
                            self.result_callback(result)
                        except Exception as e:
                            logger.error(f"Error in transcription callback: {e}")
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in transcription worker: {e}")
        
        logger.info("Transcription worker thread stopped")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get transcription statistics."""
        avg_processing_time = 0.0
        if self.total_transcriptions > 0:
            avg_processing_time = self.total_processing_time / self.total_transcriptions
        
        return {
            "is_loaded": self.is_loaded,
            "model_type": self.model_type,
            "model_name": self.config.whisper_model,
            "total_transcriptions": self.total_transcriptions,
            "total_processing_time": self.total_processing_time,
            "average_processing_time": avg_processing_time,
            "queue_size": self.transcription_queue.qsize(),
            "is_running": self.is_running
        }


class TranscriptionPipeline:
    """Complete transcription pipeline combining VAD, diarization, and Whisper."""
    
    def __init__(self, transcriber: WhisperTranscriber):
        self.transcriber = transcriber
        self.conversation_turns: List[ConversationTurn] = []
        
        # Set up transcription callback
        self.transcriber.set_result_callback(self._handle_transcription_result)
        
        # External callbacks
        self.turn_callback: Optional[Callable[[ConversationTurn], None]] = None
    
    def set_turn_callback(self, callback: Callable[[ConversationTurn], None]) -> None:
        """Set callback for new conversation turns."""
        self.turn_callback = callback
    
    def process_voice_segments(self, voice_segments: List[VoiceSegment],
                              speaker_segments: List[SpeakerSegment]) -> None:
        """Process voice segments with speaker information."""
        for voice_segment in voice_segments:
            if voice_segment.audio_data is None:
                continue
            
            # Find corresponding speaker
            speaker = self._find_speaker_for_segment(
                voice_segment.start_time,
                voice_segment.end_time,
                speaker_segments
            )
            
            # Queue for transcription
            self.transcriber.queue_audio_for_transcription(
                voice_segment.audio_data,
                voice_segment.start_time,
                speaker
            )
    
    def _find_speaker_for_segment(self, start_time: float, end_time: float,
                                 speaker_segments: List[SpeakerSegment]) -> Optional[Speaker]:
        """Find the speaker for a voice segment."""
        # Find overlapping speaker segments
        overlapping = []
        
        for speaker_segment in speaker_segments:
            if (speaker_segment.start_time <= end_time and 
                speaker_segment.end_time >= start_time):
                
                overlap = min(speaker_segment.end_time, end_time) - max(speaker_segment.start_time, start_time)
                overlapping.append((speaker_segment, overlap))
        
        if not overlapping:
            return None
        
        # Return speaker with maximum overlap
        best_segment = max(overlapping, key=lambda x: x[1])[0]
        
        # Map speaker ID to role (this would be determined by the diarization system)
        # For now, return UNKNOWN - the diarization system should handle role mapping
        return Speaker.UNKNOWN
    
    def _handle_transcription_result(self, result: TranscriptionResult) -> None:
        """Handle transcription result and create conversation turn."""
        if not result.text or not result.text.strip():
            return
        
        # Create conversation turn
        speaker = getattr(result, 'speaker', None) or Speaker.UNKNOWN
        turn = ConversationTurn(
            speaker=speaker,
            text=result.text.strip(),
            timestamp=getattr(result, 'timestamp', time.time()),
            confidence=result.confidence
        )
        
        self.conversation_turns.append(turn)
        
        # Call turn callback if set
        if self.turn_callback:
            try:
                self.turn_callback(turn)
            except Exception as e:
                logger.error(f"Error in turn callback: {e}")
    
    def get_recent_turns(self, count: int = 10) -> List[ConversationTurn]:
        """Get recent conversation turns."""
        return self.conversation_turns[-count:] if len(self.conversation_turns) >= count else self.conversation_turns
    
    def clear_history(self) -> None:
        """Clear conversation history."""
        self.conversation_turns.clear()
    
    def start(self) -> None:
        """Start the transcription pipeline."""
        self.transcriber.start_real_time_processing()
    
    def stop(self) -> None:
        """Stop the transcription pipeline."""
        self.transcriber.stop_real_time_processing()


def create_transcription_system(config: ModelConfig) -> Optional[TranscriptionPipeline]:
    """Factory function to create transcription system."""
    transcriber = WhisperTranscriber(config)
    
    if not transcriber.load_model():
        logger.error("Failed to load any Whisper model")
        return None
    
    pipeline = TranscriptionPipeline(transcriber)
    return pipeline