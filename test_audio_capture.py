#!/usr/bin/env python3
"""
Phase 3: Audio Capture Pipeline Test
Test audio detection, thresholds, and transcription separately.
"""

import sounddevice as sd
import numpy as np
import time
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '.')
from sales_coach.src.models.config import load_config
from sales_coach.src.audio.transcription import WhisperTranscriber

class AudioCaptureTest:
    def __init__(self):
        print("🎙️  AUDIO CAPTURE PIPELINE TEST")
        print("=" * 50)
        
        # Load config
        try:
            self.config = load_config(Path("config/default.yaml"))
            print("✅ Config loaded")
        except Exception as e:
            print(f"❌ Config error: {e}")
            sys.exit(1)
        
        # Audio settings for testing
        self.sample_rate = 16000
        self.test_duration = 3  # seconds
        
    def test_audio_devices(self):
        """Test available audio devices."""
        print("\n🔍 Testing Audio Devices")
        print("-" * 30)
        
        try:
            devices = sd.query_devices()
            input_devices = [(i, dev) for i, dev in enumerate(devices) if dev['max_input_channels'] > 0]
            
            print("Available input devices:")
            for i, device in input_devices:
                marker = " 👈 DEFAULT" if i == sd.default.device[0] else ""
                print(f"  {i}: {device['name']} ({device['max_input_channels']} ch){marker}")
            
            # Test default device
            default_device = sd.default.device[0]
            print(f"\nTesting default device: {devices[default_device]['name']}")
            
            # Record 1 second of audio
            test_audio = sd.rec(self.sample_rate, samplerate=self.sample_rate, channels=1, dtype=np.float32)
            sd.wait()
            
            rms = np.sqrt(np.mean(test_audio**2))
            max_amp = np.max(np.abs(test_audio))
            
            print(f"  Audio test: RMS={rms:.6f}, Max={max_amp:.6f}")
            
            if rms > 0.00001:
                print("  ✅ Audio device working")
                return True
            else:
                print("  ⚠️  Very low audio signal detected")
                return False
                
        except Exception as e:
            print(f"❌ Audio device test failed: {e}")
            return False
    
    def test_audio_thresholds(self):
        """Test different audio thresholds."""
        print("\n📊 Testing Audio Thresholds")
        print("-" * 30)
        
        thresholds = [0.00001, 0.0001, 0.001, 0.005, 0.01]
        
        print("Recording 5 seconds of audio to test thresholds...")
        print("Please speak or play audio now...")
        
        # Record continuous audio
        audio_data = sd.rec(int(5 * self.sample_rate), samplerate=self.sample_rate, channels=1, dtype=np.float32)
        sd.wait()
        
        # Split into 1-second chunks
        chunk_size = self.sample_rate
        chunks = [audio_data[i:i+chunk_size] for i in range(0, len(audio_data), chunk_size)]
        
        print("\nAnalyzing chunks with different thresholds:")
        print("Chunk | RMS     | " + " | ".join([f">{t:5.3f}" for t in thresholds]))
        print("-" * 60)
        
        for i, chunk in enumerate(chunks):
            if len(chunk) < chunk_size:
                continue
                
            rms = np.sqrt(np.mean(chunk**2))
            results = ["✓" if rms > t else "✗" for t in thresholds]
            
            print(f"  {i+1}   | {rms:.5f} | " + " | ".join([f"  {r}  " for r in results]))
        
        print("\nRecommendations:")
        for threshold in thresholds:
            chunk_count = sum(1 for chunk in chunks if np.sqrt(np.mean(chunk**2)) > threshold)
            if chunk_count >= 2:  # At least 2 chunks triggered
                print(f"  Threshold {threshold:.3f}: {chunk_count}/5 chunks - Good sensitivity")
                break
        else:
            print("  Consider lowering threshold or checking audio input")
        
        return True
    
    def test_whisper_transcription(self):
        """Test Whisper transcription separately."""
        print("\n🗣️  Testing Whisper Transcription")
        print("-" * 30)
        
        try:
            # Initialize Whisper
            print("Loading Whisper model...")
            transcriber = WhisperTranscriber(self.config.models)
            
            if not transcriber.load_model():
                print("❌ Failed to load Whisper model")
                return False
            
            print("✅ Whisper model loaded")
            
            # Record audio for transcription
            print(f"\nRecording {self.test_duration} seconds for transcription...")
            print("Please speak clearly:")
            
            for i in range(3, 0, -1):
                print(f"{i}...", end=" ", flush=True)
                time.sleep(1)
            print("Recording!")
            
            audio_data = sd.rec(
                int(self.test_duration * self.sample_rate), 
                samplerate=self.sample_rate, 
                channels=1, 
                dtype=np.float32
            )
            sd.wait()
            
            # Check audio quality
            audio_1d = audio_data.flatten()
            rms = np.sqrt(np.mean(audio_1d**2))
            max_amp = np.max(np.abs(audio_1d))
            
            print(f"Audio quality: RMS={rms:.6f}, Max={max_amp:.6f}")
            
            if rms < 0.001:
                print("⚠️  Very quiet audio, transcription may fail")
            
            # Transcribe
            print("Transcribing...")
            start_time = time.time()
            result = transcriber.transcribe_audio(audio_1d)
            transcription_time = time.time() - start_time
            
            print(f"Transcription took: {transcription_time:.2f} seconds")
            
            if result and result.text and result.text.strip():
                text = result.text.strip()
                print(f"✅ Transcription successful:")
                print(f"   Text: \"{text}\"")
                print(f"   Confidence: {result.confidence:.3f}")
                print(f"   Language: {getattr(result, 'language', 'unknown')}")
                
                # Check for quality issues
                if len(text) < 5:
                    print("⚠️  Very short transcription - may indicate audio issues")
                if result.confidence < 0.5:
                    print("⚠️  Low confidence - audio quality may be poor")
                
                return True
            else:
                print("❌ Transcription failed or empty")
                return False
                
        except Exception as e:
            print(f"❌ Transcription test failed: {e}")
            return False
    
    def test_continuous_capture(self):
        """Test continuous audio capture for phantom detection."""
        print("\n🔄 Testing Continuous Capture (Phantom Detection)")
        print("-" * 30)
        
        print("Monitoring audio for 30 seconds to detect phantom transcriptions...")
        print("Please remain quiet for the first 15 seconds, then speak normally.")
        
        # Initialize Whisper
        transcriber = WhisperTranscriber(self.config.models)
        if not transcriber.load_model():
            print("❌ Failed to load Whisper for continuous test")
            return False
        
        chunk_duration = 3
        total_chunks = 10  # 30 seconds total
        phantom_detections = 0
        real_detections = 0
        
        for chunk_num in range(1, total_chunks + 1):
            is_quiet_period = chunk_num <= 5  # First 15 seconds should be quiet
            
            print(f"\nChunk {chunk_num}/10 ({'QUIET' if is_quiet_period else 'SPEAK'}):", end=" ", flush=True)
            
            # Record audio
            audio_data = sd.rec(
                int(chunk_duration * self.sample_rate), 
                samplerate=self.sample_rate, 
                channels=1, 
                dtype=np.float32
            )
            sd.wait()
            
            # Analyze audio
            audio_1d = audio_data.flatten()
            rms = np.sqrt(np.mean(audio_1d**2))
            
            print(f"RMS:{rms:.6f}", end=" ")
            
            # Test transcription if above threshold
            if rms > 0.001:
                print("- Processing...", end=" ")
                
                try:
                    result = transcriber.transcribe_audio(audio_1d)
                    
                    if result and result.text and result.text.strip() and len(result.text.strip()) > 2:
                        text = result.text.strip()
                        print(f"TRANSCRIBED: \"{text[:30]}...\"")
                        
                        if is_quiet_period:
                            phantom_detections += 1
                            print(f"      ⚠️  PHANTOM DETECTION during quiet period")
                        else:
                            real_detections += 1
                            print(f"      ✅ Real speech detected")
                    else:
                        print("No clear transcription")
                        
                except Exception as e:
                    print(f"Transcription error: {str(e)[:30]}...")
            else:
                print("- Below threshold")
        
        # Summary
        print(f"\n📊 Continuous Capture Results:")
        print(f"   Real detections: {real_detections}")
        print(f"   Phantom detections: {phantom_detections}")
        print(f"   Phantom rate: {(phantom_detections/5)*100:.1f}% (should be <20%)")
        
        return phantom_detections <= 1  # At most 1 phantom detection acceptable
    
    def run_all_audio_tests(self):
        """Run all audio tests."""
        print("Starting comprehensive audio testing...\n")
        
        results = {}
        
        # Test 1: Audio devices
        try:
            results['audio_devices'] = self.test_audio_devices()
        except Exception as e:
            print(f"❌ Audio devices test failed: {e}")
            results['audio_devices'] = False
        
        # Test 2: Audio thresholds
        try:
            results['audio_thresholds'] = self.test_audio_thresholds()
        except Exception as e:
            print(f"❌ Audio thresholds test failed: {e}")
            results['audio_thresholds'] = False
        
        # Test 3: Whisper transcription
        try:
            results['whisper_transcription'] = self.test_whisper_transcription()
        except Exception as e:
            print(f"❌ Whisper transcription test failed: {e}")
            results['whisper_transcription'] = False
        
        # Test 4: Continuous capture (only if other tests pass)
        if results.get('whisper_transcription', False):
            try:
                results['continuous_capture'] = self.test_continuous_capture()
            except Exception as e:
                print(f"❌ Continuous capture test failed: {e}")
                results['continuous_capture'] = False
        else:
            print("\n⚠️  Skipping continuous capture test due to transcription issues")
            results['continuous_capture'] = False
        
        # Summary
        print("\n" + "=" * 50)
        print("AUDIO CAPTURE TEST RESULTS")
        print("=" * 50)
        
        for test_name, success in results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
        
        overall_success = sum(results.values()) >= 3  # At least 3/4 tests pass
        print(f"\nOverall Result: {'✅ AUDIO SYSTEM WORKING' if overall_success else '❌ AUDIO ISSUES DETECTED'}")
        
        if not overall_success:
            print("\nRecommendations:")
            if not results.get('audio_devices'):
                print("- Check microphone permissions and audio device connections")
            if not results.get('whisper_transcription'):
                print("- Verify Whisper model installation and audio quality")
            if not results.get('continuous_capture'):
                print("- Increase audio threshold to reduce phantom detections")
        
        return overall_success

def main():
    tester = AudioCaptureTest()
    tester.run_all_audio_tests()

if __name__ == "__main__":
    main()