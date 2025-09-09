#!/usr/bin/env python3
"""
Audio diagnostic tool to test different devices and noise levels.
Helps diagnose microphone permissions and audio capture issues.
"""

import sounddevice as sd
import numpy as np
import time
from datetime import datetime

def list_audio_devices():
    """List all available audio devices."""
    print("📻 AVAILABLE AUDIO DEVICES")
    print("=" * 50)
    
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        device_type = []
        if device['max_inputs'] > 0:
            device_type.append("INPUT")
        if device['max_outputs'] > 0:
            device_type.append("OUTPUT")
        
        print(f"{i:2d}: {device['name']}")
        print(f"    Type: {'/'.join(device_type)}")
        print(f"    Channels: In={device['max_inputs']}, Out={device['max_outputs']}")
        print(f"    Sample Rate: {device['default_samplerate']} Hz")
        print()

def test_device_basic(device_name=None, duration=5):
    """Test basic audio capture from a device."""
    print(f"🎤 TESTING AUDIO CAPTURE")
    print("=" * 50)
    
    if device_name:
        print(f"Device: {device_name}")
    else:
        print("Device: Default input device")
    print(f"Duration: {duration} seconds")
    print(f"Sample rate: 16000 Hz")
    print()
    
    try:
        # Audio parameters
        sample_rate = 16000
        chunk_size = 1024
        
        audio_data = []
        
        def audio_callback(indata, frames, time, status):
            if status:
                print(f"Audio status: {status}")
            
            # Calculate RMS level
            rms = np.sqrt(np.mean(indata**2))
            audio_data.append(rms)
            
            # Visual level meter
            bars = "█" * min(40, int(rms * 5000))
            noise_gate = "✅ PASS" if rms > 0.01 else "❌ BLOCKED"
            vad_level = "🎯 VOICE" if rms > 0.05 else "🔇 QUIET"
            
            print(f"\r🎤 RMS={rms:.4f} [{bars:<40}] {noise_gate} {vad_level}", end="", flush=True)
        
        # Start recording
        print("Starting audio capture... (speak into microphone)")
        print("Level meter: [████████████████████████████████████████]")
        print("Thresholds: Noise gate=0.01, VAD=0.05")
        print()
        
        with sd.InputStream(
            device=device_name,
            channels=1,
            samplerate=sample_rate,
            blocksize=chunk_size,
            callback=audio_callback
        ):
            time.sleep(duration)
        
        print("\n")
        
        # Analysis
        if audio_data:
            avg_level = sum(audio_data) / len(audio_data)
            max_level = max(audio_data)
            
            print("📊 RESULTS:")
            print(f"   Chunks processed: {len(audio_data)}")
            print(f"   Average level: {avg_level:.4f}")
            print(f"   Maximum level: {max_level:.4f}")
            print(f"   Chunks/second: {len(audio_data)/duration:.1f}")
            
            if max_level < 0.001:
                print("❌ No audio detected - check microphone permissions")
                print("   → Go to System Preferences > Security & Privacy > Microphone")
                print("   → Ensure Terminal/Python has microphone access")
            elif max_level < 0.01:
                print("⚠️  Very low audio - microphone may not be working properly")
            elif avg_level < 0.05:
                print("⚠️  Low audio levels - speak louder or adjust microphone")
            else:
                print("✅ Good audio levels detected!")
            
            return True
        else:
            print("❌ No audio data captured")
            return False
            
    except Exception as e:
        print(f"\n❌ Error testing device: {e}")
        return False

def test_permissions():
    """Test microphone permissions specifically."""
    print("🔐 TESTING MICROPHONE PERMISSIONS")
    print("=" * 50)
    
    try:
        # Try to access default input device
        print("Attempting to access default microphone...")
        
        with sd.InputStream(channels=1, samplerate=16000, blocksize=1024):
            print("✅ Microphone access granted")
            time.sleep(0.5)
            
        return True
        
    except sd.PortAudioError as e:
        print(f"❌ PortAudio error: {e}")
        if "Invalid device" in str(e):
            print("   → No default input device found")
        elif "unanticipated host error" in str(e).lower():
            print("   → Likely microphone permission denied")
            print("   → Go to System Preferences > Security & Privacy > Microphone")
            print("   → Enable access for Terminal or your Python environment")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def interactive_test():
    """Interactive audio testing."""
    print("🎯 INTERACTIVE AUDIO TESTING")
    print("=" * 50)
    
    while True:
        print("\nOptions:")
        print("1. List all audio devices")
        print("2. Test default microphone (5 seconds)")
        print("3. Test specific device")
        print("4. Test microphone permissions")
        print("5. Exit")
        
        choice = input("\nChoose option (1-5): ").strip()
        
        if choice == "1":
            list_audio_devices()
        elif choice == "2":
            test_device_basic(duration=5)
        elif choice == "3":
            list_audio_devices()
            device_input = input("\nEnter device number or name: ").strip()
            try:
                device_id = int(device_input)
                device_name = device_id
            except ValueError:
                device_name = device_input
            
            duration = input("Test duration in seconds (default 5): ").strip()
            try:
                duration = int(duration) if duration else 5
            except ValueError:
                duration = 5
            
            test_device_basic(device_name, duration)
        elif choice == "4":
            test_permissions()
        elif choice == "5":
            break
        else:
            print("Invalid option")

def main():
    """Run audio diagnostics."""
    print("🔧 AUDIO DIAGNOSTIC TOOL")
    print("=" * 50)
    print("This tool helps diagnose audio capture issues.")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Quick permission test
    print("Quick permission check...")
    if test_permissions():
        print("✅ Basic microphone access working")
        print()
        interactive_test()
    else:
        print("\n❌ Microphone access issues detected")
        print("\nTo fix:")
        print("1. Open System Preferences")
        print("2. Go to Security & Privacy > Privacy > Microphone")
        print("3. Enable access for Terminal and/or Python")
        print("4. Restart this tool")

if __name__ == "__main__":
    main()