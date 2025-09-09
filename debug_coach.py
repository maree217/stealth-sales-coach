#!/usr/bin/env python3
"""
Debug version of sales coach with simplified pipeline and print-based output.
Use this to test and debug issues before integrating back to main system.
"""

import logging
import time
import numpy as np
from pathlib import Path
from datetime import datetime

from sales_coach.src.models.config import load_config
from sales_coach.src.models.conversation import ConversationTurn, Speaker
from sales_coach.src.audio.capture import AudioCaptureSystem
from sales_coach.src.audio.vad import create_vad
from sales_coach.src.audio.transcription import create_transcription_system
from sales_coach.src.llm.coaching import create_coaching_system

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class DebugSalesCoach:
    """Simplified sales coach for debugging."""
    
    def __init__(self):
        print("🔍 DEBUG SALES COACH")
        print("="*50)
        
        # Load config
        config_path = Path("config/default.yaml")
        self.config = load_config(config_path)
        
        # Stats
        self.stats = {
            "audio_chunks": 0,
            "voice_segments": 0,
            "transcription_calls": 0,
            "coaching_calls": 0,
            "coaching_successes": 0
        }
        
        # Components (will be initialized)
        self.audio_capture = None
        self.vad_system = None
        self.transcription_system = None
        self.coaching_system = None
        
        self.is_running = False
        self.start_time = None
        
        print("✅ Debug coach initialized")
    
    def initialize_components(self):
        """Initialize components with debug output."""
        print("\n🔧 INITIALIZING COMPONENTS")
        print("-" * 30)
        
        try:
            # Audio capture
            print("1. Audio Capture System...")
            self.audio_capture = AudioCaptureSystem(self.config.audio)
            self.audio_capture.set_audio_callback(self._handle_audio)
            print(f"   ✅ Device: {self.config.audio.input_device or 'default'}")
            
            # VAD
            print("2. Voice Activity Detection...")
            self.vad_system = create_vad(self.config.audio, adaptive=True)
            print(f"   ✅ Threshold: {self.config.audio.vad_threshold}")
            
            # Transcription  
            print("3. Speech-to-Text...")
            self.transcription_system = create_transcription_system(self.config.models)
            if self.transcription_system:
                self.transcription_system.set_turn_callback(self._handle_transcription)
                print(f"   ✅ Model: {self.config.models.whisper_model}")
            else:
                print("   ❌ Failed to load transcription")
                return False
            
            # Coaching
            print("4. AI Coaching System...")
            self.coaching_system = create_coaching_system(self.config.models, self.config.coaching)
            if self.coaching_system:
                self.coaching_system.set_coaching_callback(self._handle_coaching)
                print(f"   ✅ Model: {self.config.models.llm_model_name}")
            else:
                print("   ❌ Failed to load coaching")
                return False
            
            print("\n✅ All components ready!")
            return True
            
        except Exception as e:
            print(f"❌ Initialization failed: {e}")
            return False
    
    def _handle_audio(self, audio_chunk):
        """Handle audio with debug info."""
        self.stats["audio_chunks"] += 1
        
        # Show audio levels periodically
        if self.stats["audio_chunks"] % 20 == 0:
            rms = np.sqrt(np.mean(audio_chunk**2))
            bars = "█" * min(20, int(rms * 1000))
            print(f"🎤 Audio Level: [{bars:<20}] RMS={rms:.4f}")
        
        # Process with VAD
        timestamp = time.time()
        voice_segments = self.vad_system.process_audio_stream(audio_chunk, timestamp)
        
        if voice_segments:
            self.stats["voice_segments"] += len(voice_segments)
            print(f"🎯 Voice detected: {len(voice_segments)} segments")
            
            # Send to transcription
            self.transcription_system.process_voice_segments(voice_segments, [])
    
    def _handle_transcription(self, turn: ConversationTurn):
        """Handle transcription with debug info."""
        self.stats["transcription_calls"] += 1
        
        print(f"\n💬 TRANSCRIPTION #{self.stats['transcription_calls']}")
        print(f"   Speaker: {turn.speaker.value}")
        print(f"   Text: {turn.text}")
        print(f"   Confidence: {turn.confidence:.2f}")
        
        # Send to coaching
        if self.coaching_system:
            self.coaching_system.add_conversation_turn(turn)
    
    def _handle_coaching(self, coaching_response):
        """Handle coaching with debug info."""
        self.stats["coaching_calls"] += 1
        self.stats["coaching_successes"] += 1
        
        print(f"\n🧠 COACHING ADVICE #{self.stats['coaching_successes']}")
        print(f"   Priority: {coaching_response.primary_advice.priority.value}")
        print(f"   Category: {coaching_response.primary_advice.category.value}")
        print(f"   Insight: {coaching_response.primary_advice.insight}")
        print(f"   Action: {coaching_response.primary_advice.suggested_action}")
        print(f"   Confidence: {coaching_response.confidence:.2f}")
    
    def start(self):
        """Start the debug coach."""
        if not self.initialize_components():
            return False
        
        print(f"\n🚀 STARTING DEBUG COACH")
        print("=" * 50)
        
        try:
            # Start audio capture
            if not self.audio_capture.start_capture():
                print("❌ Failed to start audio capture")
                return False
            
            # Start transcription
            self.transcription_system.start()
            
            # Start coaching analysis  
            self.coaching_system.start_analysis()
            
            self.is_running = True
            self.start_time = time.time()
            
            print("✅ Debug coach is running!")
            print("\nREAL-TIME OUTPUT:")
            print("-" * 20)
            return True
            
        except Exception as e:
            print(f"❌ Failed to start: {e}")
            return False
    
    def stop(self):
        """Stop the debug coach."""
        print(f"\n🛑 STOPPING DEBUG COACH")
        
        try:
            if self.audio_capture:
                self.audio_capture.stop_capture()
            if self.transcription_system:
                self.transcription_system.stop()
            if self.coaching_system:
                self.coaching_system.stop_analysis()
            
            self.is_running = False
            
            # Show final stats
            duration = time.time() - self.start_time if self.start_time else 0
            print(f"\n📊 SESSION STATS ({duration:.1f}s)")
            print(f"   Audio chunks processed: {self.stats['audio_chunks']}")
            print(f"   Voice segments detected: {self.stats['voice_segments']}")
            print(f"   Transcription calls: {self.stats['transcription_calls']}")
            print(f"   Coaching attempts: {self.stats['coaching_calls']}")
            print(f"   Coaching successes: {self.stats['coaching_successes']}")
            
            success_rate = 0
            if self.stats['coaching_calls'] > 0:
                success_rate = self.stats['coaching_successes'] / self.stats['coaching_calls'] * 100
            
            print(f"   Coaching success rate: {success_rate:.1f}%")
            
            print("✅ Debug coach stopped")
            
        except Exception as e:
            print(f"❌ Error stopping: {e}")
    
    def run_interactive(self):
        """Run interactively with keyboard controls."""
        if not self.start():
            return
        
        print("\n⌨️  CONTROLS:")
        print("   - Press ENTER to show current stats")
        print("   - Type 'test' to trigger manual coaching test")
        print("   - Type 'quit' or Ctrl+C to stop")
        
        try:
            while self.is_running:
                user_input = input().strip().lower()
                
                if user_input == 'quit':
                    break
                elif user_input == 'test':
                    self._test_coaching()
                elif user_input == '':
                    # Show current stats
                    duration = time.time() - self.start_time
                    print(f"⏱️  Running for {duration:.1f}s | "
                          f"Audio: {self.stats['audio_chunks']} | "
                          f"Voice: {self.stats['voice_segments']} | "
                          f"Transcripts: {self.stats['transcription_calls']} | "
                          f"Coaching: {self.stats['coaching_successes']}")
                
        except KeyboardInterrupt:
            print("\n🛑 Interrupted by user")
        finally:
            self.stop()
    
    def _test_coaching(self):
        """Test coaching with dummy conversation."""
        print("\n🧪 TESTING COACHING...")
        
        # Create test conversation turn
        test_turn = ConversationTurn(
            speaker=Speaker.SALES_REP,
            text="Hello, can you hear me clearly? I'd like to discuss our enterprise solution.",
            timestamp=datetime.now(),
            confidence=0.95
        )
        
        print(f"   Sending test turn: {test_turn.text}")
        
        if self.coaching_system:
            self.coaching_system.add_conversation_turn(test_turn)
            
            # Force immediate analysis
            response = self.coaching_system.force_analysis()
            if response:
                print("   ✅ Manual coaching test succeeded")
            else:
                print("   ❌ Manual coaching test failed")
        else:
            print("   ❌ Coaching system not available")

def main():
    """Run the debug coach."""
    coach = DebugSalesCoach()
    coach.run_interactive()

if __name__ == "__main__":
    main()