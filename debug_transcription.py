#!/usr/bin/env python3
"""Debug transcription issue."""

import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from sales_coach.src.models.config import load_config
from sales_coach.src.audio.transcription import WhisperTranscriber

def test_transcription():
    """Test transcription with simple audio."""
    print("Testing transcription system...")
    
    # Load config
    config = load_config(Path("config/default.yaml"))
    
    # Create transcriber
    transcriber = WhisperTranscriber(config.models)
    
    print(f"Loading model: {config.models.whisper_model}")
    if not transcriber.load_model():
        print("❌ Failed to load transcription model")
        return False
    
    print(f"✅ Model loaded: {transcriber.model_type}")
    
    # Create simple audio data - sine wave at speech frequency
    duration = 2.0
    sample_rate = 16000  # Whisper prefers 16kHz
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    
    # Generate speech-like signal with multiple frequencies
    audio = np.zeros_like(t)
    audio += 0.3 * np.sin(2 * np.pi * 200 * t)  # Base frequency
    audio += 0.2 * np.sin(2 * np.pi * 400 * t)  # First harmonic
    audio += 0.1 * np.sin(2 * np.pi * 800 * t)  # Second harmonic
    
    # Add some modulation to make it more speech-like
    modulation = 0.5 + 0.3 * np.sin(2 * np.pi * 5 * t)
    audio *= modulation
    
    # Convert to float32
    audio = audio.astype(np.float32)
    
    print(f"Audio shape: {audio.shape}, dtype: {audio.dtype}")
    print(f"Audio range: {audio.min():.3f} to {audio.max():.3f}")
    
    # Transcribe
    print("Transcribing...")
    result = transcriber.transcribe_audio(audio)
    
    print(f"Result: {result}")
    if result:
        print(f"Text: '{result.text}'")
        print(f"Confidence: {result.confidence}")
        print(f"Language: {result.language}")
        print(f"Processing time: {result.processing_time:.2f}s")
    
    return result and result.text and len(result.text.strip()) > 0

if __name__ == "__main__":
    success = test_transcription()
    if success:
        print("✅ Transcription working!")
    else:
        print("❌ Transcription failed!")