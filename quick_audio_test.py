#!/usr/bin/env python3
"""
Quick audio test to check if microphone is actually picking up sound.
"""

import sounddevice as sd
import numpy as np
import time

def quick_test():
    """Quick 5-second audio test."""
    print("🎤 QUICK AUDIO TEST (5 seconds)")
    print("=" * 40)
    print("Speak into your microphone now...")
    print()
    
    audio_data = []
    
    def callback(indata, frames, time, status):
        if status:
            print(f"Status: {status}")
        
        rms = np.sqrt(np.mean(indata**2))
        audio_data.append(rms)
        
        # Show level every 10 chunks
        if len(audio_data) % 10 == 0:
            bars = "█" * min(30, int(rms * 3000))
            print(f"Level: [{bars:<30}] RMS={rms:.4f}")
    
    try:
        with sd.InputStream(channels=1, samplerate=16000, callback=callback):
            time.sleep(5)
        
        print("\n📊 RESULTS:")
        if audio_data:
            avg = sum(audio_data) / len(audio_data)
            maximum = max(audio_data)
            print(f"Average level: {avg:.4f}")
            print(f"Maximum level: {maximum:.4f}")
            print(f"Chunks: {len(audio_data)}")
            
            if maximum < 0.001:
                print("❌ No audio detected")
            elif avg < 0.01:
                print("⚠️  Very low audio")
            elif avg < 0.05:
                print("⚠️  Low audio - speak louder")
            else:
                print("✅ Good audio levels!")
        else:
            print("❌ No data captured")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    quick_test()