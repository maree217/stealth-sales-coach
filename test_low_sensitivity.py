#!/usr/bin/env python3
"""
Test the updated low sensitivity configuration.
"""

import logging
import time
import numpy as np
from pathlib import Path
from datetime import datetime

from sales_coach.src.models.config import load_config
from sales_coach.src.audio.capture import AudioCaptureSystem

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_low_sensitivity():
    """Test the low sensitivity configuration."""
    print("🔧 TESTING LOW SENSITIVITY CONFIGURATION")
    print("=" * 50)
    
    # Load low sensitivity config
    config_path = Path("config/low_sensitivity.yaml")
    config = load_config(config_path)
    
    print(f"✅ Loaded config from {config_path}")
    print(f"   Audio device: {config.audio.input_device}")
    print(f"   VAD threshold: {config.audio.vad_threshold}")
    print(f"   Noise gate: 0.0005 (hardcoded in VAD)")
    print()
    
    # Stats tracking
    stats = {
        "audio_chunks": 0,
        "audio_levels": [],
        "max_level": 0.0,
        "vad_triggers": 0
    }
    
    def handle_audio(audio_chunk):
        """Handle audio with monitoring."""
        stats["audio_chunks"] += 1
        
        # Calculate audio level
        rms = np.sqrt(np.mean(audio_chunk**2))
        stats["audio_levels"].append(rms)
        stats["max_level"] = max(stats["max_level"], rms)
        
        # Check thresholds
        noise_gate_pass = rms > 0.0005  # New noise gate threshold
        vad_trigger = rms > config.audio.vad_threshold  # 0.002
        
        if vad_trigger:
            stats["vad_triggers"] += 1
        
        # Show every 5th chunk
        if stats["audio_chunks"] % 5 == 0:
            bars = "█" * min(30, int(rms * 3000))
            gate_status = "✅ PASS" if noise_gate_pass else "❌ BLOCK"
            vad_status = "🎯 VAD" if vad_trigger else "🔇 QUIET"
            
            print(f"🎤 #{stats['audio_chunks']:4d} | RMS={rms:.4f} | [{bars:<30}] | {gate_status} | {vad_status}")
    
    try:
        print("Starting audio capture with low sensitivity settings...")
        print("Speak into your microphone (test for 10 seconds)")
        print()
        
        # Create and start audio capture
        audio_capture = AudioCaptureSystem(config.audio)
        audio_capture.set_audio_callback(handle_audio)
        
        if not audio_capture.start_capture():
            print("❌ Failed to start audio capture")
            return False
        
        print("📊 REAL-TIME MONITORING:")
        print("-" * 80)
        
        # Run for 10 seconds
        start_time = time.time()
        time.sleep(10)
        
        # Stop capture
        audio_capture.stop_capture()
        duration = time.time() - start_time
        
        print("\n" + "=" * 80)
        print("📊 TEST RESULTS:")
        print(f"   Duration: {duration:.1f}s")
        print(f"   Total chunks: {stats['audio_chunks']}")
        print(f"   Chunks/second: {stats['audio_chunks']/duration:.1f}")
        print(f"   Average level: {sum(stats['audio_levels'])/len(stats['audio_levels']):.4f}")
        print(f"   Maximum level: {stats['max_level']:.4f}")
        print(f"   VAD triggers: {stats['vad_triggers']}")
        print(f"   VAD trigger rate: {stats['vad_triggers']/stats['audio_chunks']*100:.1f}%")
        
        if stats['vad_triggers'] > 0:
            print("✅ SUCCESS: VAD is now triggering with low sensitivity settings!")
            print("   The system should now detect your voice.")
        elif stats['max_level'] > 0.001:
            print("⚠️  Audio detected but VAD threshold may still be too high")
            print(f"   Consider lowering VAD threshold below {stats['max_level']:.4f}")
        else:
            print("❌ No significant audio detected")
        
        return stats['vad_triggers'] > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_low_sensitivity()
    print(f"\n{'='*50}")
    if success:
        print("✅ LOW SENSITIVITY TEST PASSED")
        print("The system is now configured to detect quiet microphones!")
    else:
        print("❌ TEST FAILED - May need further threshold adjustments")
    print("="*50)