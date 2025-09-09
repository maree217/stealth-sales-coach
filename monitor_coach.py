#!/usr/bin/env python3
"""
Monitoring version - uses microphone like the working background processes.
"""

import logging
import time
import numpy as np
from pathlib import Path
from datetime import datetime

from sales_coach.src.models.config import load_config
from sales_coach.src.models.conversation import ConversationTurn, Speaker
from sales_coach.src.audio.capture import AudioCaptureSystem

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class MonitorCoach:
    """Live monitoring of audio capture."""
    
    def __init__(self):
        print("🎤 AUDIO MONITOR")
        print("="*50)
        
        # Load config
        config_path = Path("config/default.yaml")
        self.config = load_config(config_path)
        
        # Override to use microphone like working processes
        self.config.audio.input_device = "MacBook Air Microphone"
        self.config.audio.vad_threshold = 0.05  # Lower than 0.3 but higher than 0.02
        
        # Stats
        self.stats = {
            "audio_chunks": 0,
            "audio_levels": [],
            "max_level": 0.0
        }
        
        self.is_running = False
        self.start_time = None
        
        print(f"✅ Using device: {self.config.audio.input_device}")
        print(f"✅ VAD threshold: {self.config.audio.vad_threshold}")
    
    def _handle_audio(self, audio_chunk):
        """Handle audio with real-time monitoring."""
        self.stats["audio_chunks"] += 1
        
        # Calculate audio level
        rms = np.sqrt(np.mean(audio_chunk**2))
        self.stats["audio_levels"].append(rms)
        self.stats["max_level"] = max(self.stats["max_level"], rms)
        
        # Show audio levels frequently
        if self.stats["audio_chunks"] % 5 == 0:
            bars = "█" * min(30, int(rms * 3000))
            noise_gate_check = "✅ PASS" if rms > 0.01 else "❌ BLOCKED"
            vad_check = "🎯 VOICE" if rms > self.config.audio.vad_threshold else "🔇 QUIET"
            
            print(f"🎤 #{self.stats['audio_chunks']:4d} | RMS={rms:.4f} | [{bars:<30}] | {noise_gate_check} | {vad_check}")
        
        # Show max level every 50 chunks
        if self.stats["audio_chunks"] % 50 == 0:
            avg_level = sum(self.stats["audio_levels"][-50:]) / min(50, len(self.stats["audio_levels"]))
            print(f"📊 Last 50 chunks: Avg={avg_level:.4f}, Max={self.stats['max_level']:.4f}")
    
    def start_monitoring(self):
        """Start audio monitoring."""
        print(f"\n🚀 STARTING AUDIO MONITOR")
        print("=" * 50)
        
        try:
            # Audio capture only
            print("Loading audio capture...")
            self.audio_capture = AudioCaptureSystem(self.config.audio)
            self.audio_capture.set_audio_callback(self._handle_audio)
            
            # Start capture
            if not self.audio_capture.start_capture():
                print("❌ Failed to start audio capture")
                return False
            
            self.is_running = True
            self.start_time = time.time()
            
            print("✅ Audio monitor is running!")
            print("\nREAL-TIME AUDIO LEVELS:")
            print("-" * 70)
            print("Legend:")
            print("  🎤 = Audio chunk number")
            print("  RMS = Audio energy level")
            print("  ████ = Visual level meter")
            print("  ✅ PASS / ❌ BLOCKED = Noise gate (0.01 threshold)")
            print("  🎯 VOICE / 🔇 QUIET = VAD trigger")
            print("-" * 70)
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to start: {e}")
            return False
    
    def stop(self):
        """Stop monitoring."""
        print(f"\n🛑 STOPPING MONITOR")
        
        try:
            if self.audio_capture:
                self.audio_capture.stop_capture()
            
            duration = time.time() - self.start_time if self.start_time else 0
            avg_level = sum(self.stats["audio_levels"]) / len(self.stats["audio_levels"]) if self.stats["audio_levels"] else 0
            
            print(f"\n📊 SESSION SUMMARY ({duration:.1f}s)")
            print(f"   Audio chunks: {self.stats['audio_chunks']}")
            print(f"   Average level: {avg_level:.4f}")
            print(f"   Max level: {self.stats['max_level']:.4f}")
            print(f"   Chunks/sec: {self.stats['audio_chunks']/duration:.1f}")
            
            if avg_level < 0.001:
                print("⚠️  Very low audio levels - check microphone permissions")
            elif avg_level > 0.1:
                print("✅ Good audio levels detected")
            else:
                print("⚠️  Moderate audio levels - speak louder or check setup")
            
            self.is_running = False
            print("✅ Monitor stopped")
            
        except Exception as e:
            print(f"❌ Error stopping: {e}")
    
    def run_interactive(self):
        """Run interactively."""
        if not self.start_monitoring():
            return
        
        print("\n⌨️  CONTROLS:")
        print("   - Press ENTER to show current stats")
        print("   - Type 'quit' or Ctrl+C to stop")
        
        try:
            while self.is_running:
                user_input = input().strip().lower()
                
                if user_input == 'quit':
                    break
                elif user_input == '':
                    # Show current stats
                    duration = time.time() - self.start_time
                    recent_avg = sum(self.stats["audio_levels"][-10:]) / min(10, len(self.stats["audio_levels"]))
                    print(f"⏱️  Running: {duration:.1f}s | Chunks: {self.stats['audio_chunks']} | Recent avg: {recent_avg:.4f} | Max: {self.stats['max_level']:.4f}")
                
        except KeyboardInterrupt:
            print("\n🛑 Interrupted by user")
        except EOFError:
            print("\n🛑 Input stream closed")
        finally:
            self.stop()

def main():
    """Run the monitor."""
    monitor = MonitorCoach()
    monitor.run_interactive()

if __name__ == "__main__":
    main()