#!/usr/bin/env python3
"""
Simple direct test - bypass all complexity, just grab audio and show what's happening.
"""

import sounddevice as sd
import numpy as np
import time
import sys

def test_audio_direct():
    """Test audio capture directly without any processing."""
    print("🎤 DIRECT AUDIO TEST")
    print("=" * 40)
    
    # List devices
    devices = sd.query_devices()
    print("Available audio devices:")
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            print(f"  {i}: {device['name']} ({device['max_input_channels']} channels)")
    
    print(f"\nDefault input device: {sd.default.device}")
    
    # Test audio capture
    try:
        print("\nTesting audio capture for 5 seconds...")
        print("SPEAK NOW or play audio!")
        
        # Record for 5 seconds
        duration = 5  # seconds
        sample_rate = 16000
        
        audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype=np.float32)
        sd.wait()  # Wait until recording is finished
        
        # Analyze the recording
        rms = np.sqrt(np.mean(audio_data**2))
        max_val = np.max(np.abs(audio_data))
        
        print(f"\n📊 AUDIO ANALYSIS:")
        print(f"   Duration: {duration}s")
        print(f"   Sample rate: {sample_rate}Hz") 
        print(f"   Shape: {audio_data.shape}")
        print(f"   RMS level: {rms:.6f}")
        print(f"   Max level: {max_val:.6f}")
        print(f"   Data type: {audio_data.dtype}")
        
        if rms > 0.001:
            print("✅ AUDIO DETECTED - Something was recorded!")
            
            # Save for inspection
            import wave
            with wave.open('test_recording.wav', 'w') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                audio_int16 = (audio_data * 32767).astype(np.int16)
                wav_file.writeframes(audio_int16.tobytes())
            print("💾 Saved as 'test_recording.wav'")
            
            return True
        else:
            print("❌ NO AUDIO - Silence detected")
            print("   Check:")
            print("   1. Microphone permissions")
            print("   2. Correct input device")
            print("   3. Audio levels")
            return False
            
    except Exception as e:
        print(f"❌ Audio capture error: {e}")
        return False

def test_whisper_on_recording():
    """Test Whisper on the recorded audio."""
    import os
    if not os.path.exists('test_recording.wav'):
        print("❌ No test recording found")
        return False
        
    print("\n🗣️  TESTING WHISPER...")
    
    try:
        # Load the recording
        import wave
        with wave.open('test_recording.wav', 'rb') as wav_file:
            frames = wav_file.readframes(-1)
            audio_data = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
        
        # Quick Whisper test
        sys.path.insert(0, '.')
        from sales_coach.src.models.config import load_config
        from sales_coach.src.audio.transcription import WhisperTranscriber
        
        from pathlib import Path
        config = load_config(Path("config/default.yaml"))
        transcriber = WhisperTranscriber(config.models)
        
        if transcriber.load_model():
            print("✅ Whisper model loaded")
            result = transcriber.transcribe_audio(audio_data)
            
            if result and result.text:
                print(f"📝 TRANSCRIPTION: '{result.text}'")
                print(f"   Confidence: {result.confidence:.3f}")
                return True
            else:
                print("❌ No transcription result")
                return False
        else:
            print("❌ Failed to load Whisper model")
            return False
            
    except Exception as e:
        print(f"❌ Whisper test error: {e}")
        return False

def main():
    print("🔥 AGGRESSIVE DEBUGGING MODE")
    print("This will test audio capture and transcription step by step\n")
    
    # Test 1: Direct audio capture
    audio_ok = test_audio_direct()
    
    if audio_ok:
        # Test 2: Whisper transcription
        whisper_ok = test_whisper_on_recording()
        
        if whisper_ok:
            print("\n✅ SUCCESS - Both audio and transcription working!")
        else:
            print("\n⚠️  Audio works but transcription failed")
    else:
        print("\n❌ FAILED - No audio detected")
        print("Fix audio capture before testing transcription")

if __name__ == "__main__":
    main()