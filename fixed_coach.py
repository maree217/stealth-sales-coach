#!/usr/bin/env python3
"""
FIXED Sales Coach - More sensitive audio detection, better stability.
"""

import sounddevice as sd
import numpy as np
import time
import sys
import signal
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '.')
from sales_coach.src.models.config import load_config
from sales_coach.src.audio.transcription import WhisperTranscriber
from sales_coach.src.llm.coaching import create_coaching_system
from sales_coach.src.models.conversation import ConversationTurn, Speaker

class FixedSalesCoach:
    def __init__(self):
        self.running = True
        
        print("🔧 FIXED SALES COACH - Enhanced Audio Detection")
        print("=" * 60)
        
        # Setup graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        
        # Load configuration
        try:
            self.config = load_config(Path("config/default.yaml"))
            print("✅ Configuration loaded")
        except Exception as e:
            print(f"❌ Config error: {e}")
            sys.exit(1)
        
        # Initialize AI systems
        print("🧠 Loading AI models...")
        
        # Transcription
        self.transcriber = WhisperTranscriber(self.config.models)
        if not self.transcriber.load_model():
            print("❌ Failed to load Whisper transcription model")
            sys.exit(1)
        print("   ✅ Speech-to-text ready")
        
        # Coaching
        self.coaching_system = create_coaching_system(self.config.models, self.config.coaching)
        if not self.coaching_system:
            print("❌ Failed to load coaching AI")
            sys.exit(1)
        print("   ✅ AI coaching ready")
        
        # Audio settings - MORE SENSITIVE
        self.sample_rate = 16000
        self.chunk_duration = 5  # Longer chunks for better capture
        self.audio_threshold = 0.001  # Much lower threshold
        
        print("\n🎤 Enhanced audio detection ready")
        self._show_audio_devices()
        
    def _signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully."""
        print(f"\n🛑 Shutting down...")
        self.running = False
        
    def _show_audio_devices(self):
        """Show available audio devices."""
        try:
            devices = sd.query_devices()
            input_devices = [(i, dev) for i, dev in enumerate(devices) if dev['max_input_channels'] > 0]
            
            print("   Available input devices:")
            for i, device in input_devices:
                marker = " 👈 DEFAULT" if i == sd.default.device[0] else ""
                print(f"     {i}: {device['name']}{marker}")
        except Exception as e:
            print(f"   ⚠️  Audio device error: {e}")
        
    def run(self):
        """Run the sales coach continuously."""
        print(f"\n🎯 ENHANCED SALES COACH ACTIVE")
        print(f"Chunk size: {self.chunk_duration}s, Threshold: {self.audio_threshold}")
        print("Lower threshold = more sensitive audio detection")
        print("Press Ctrl+C to stop\n")
        
        chunk_count = 0
        successful_transcriptions = 0
        total_words = 0
        
        try:
            while self.running:
                chunk_count += 1
                
                try:
                    # Record audio chunk
                    print(f"🎙️  Recording chunk #{chunk_count} ({self.chunk_duration}s)...", end="", flush=True)
                    
                    audio_data = sd.rec(
                        int(self.chunk_duration * self.sample_rate), 
                        samplerate=self.sample_rate, 
                        channels=1, 
                        dtype=np.float32
                    )
                    sd.wait()
                    
                    # Check audio level
                    audio_1d = audio_data.flatten()
                    rms = np.sqrt(np.mean(audio_1d**2))
                    max_amplitude = np.max(np.abs(audio_1d))
                    
                    print(f" RMS:{rms:.4f}, Max:{max_amplitude:.4f}")
                    
                    # Process if above threshold (much more sensitive now)
                    if rms > self.audio_threshold:
                        print(f"   🔊 Processing (above threshold {self.audio_threshold})")
                        
                        try:
                            # Transcribe
                            result = self.transcriber.transcribe_audio(audio_1d)
                            
                            if result and result.text and result.text.strip() and len(result.text.strip()) > 2:
                                text = result.text.strip()
                                successful_transcriptions += 1
                                word_count = len(text.split())
                                total_words += word_count
                                
                                timestamp = datetime.now().strftime('%H:%M:%S')
                                print(f"   📝 [{timestamp}] \"{text}\" ({word_count} words)")
                                print(f"   🎯 Confidence: {result.confidence:.3f}")
                                
                                # Generate coaching advice
                                turn = ConversationTurn(
                                    speaker=Speaker.UNKNOWN,
                                    text=text,
                                    timestamp=datetime.now(),
                                    confidence=result.confidence
                                )
                                
                                self.coaching_system.add_conversation_turn(turn)
                                coaching_response = self.coaching_system.force_analysis()
                                
                                if coaching_response and coaching_response.primary_advice:
                                    advice = coaching_response.primary_advice
                                    
                                    print(f"   🧠 COACHING [{advice.priority.value}] {advice.category.value}:")
                                    print(f"      💡 {advice.insight}")
                                    print(f"      ▶️  {advice.suggested_action}")
                                    print(f"   {'─' * 55}")
                                else:
                                    print(f"   🤔 No coaching advice generated")
                                    
                            else:
                                if result and result.text:
                                    print(f"   🔇 Transcription too short: '{result.text.strip()}'")
                                else:
                                    print(f"   🔇 No clear transcription")
                                    
                        except Exception as e:
                            print(f"   ❌ Processing error: {e}")
                            
                    else:
                        print(f"   🔇 Below threshold ({rms:.4f} < {self.audio_threshold})")
                    
                    print()  # Blank line for readability
                
                except Exception as e:
                    print(f"\n❌ Error in chunk #{chunk_count}: {e}")
                    
        except KeyboardInterrupt:
            pass  # Handled by signal handler
            
        print(f"\n📈 ENHANCED SESSION SUMMARY:")
        print(f"   Audio chunks processed: {chunk_count}")  
        print(f"   Successful transcriptions: {successful_transcriptions}")
        print(f"   Total words captured: {total_words}")
        print(f"   Success rate: {(successful_transcriptions/max(1,chunk_count)*100):.1f}%")
        print(f"   Average words per transcription: {total_words/max(1,successful_transcriptions):.1f}")
        print(f"\n✅ Enhanced Sales Coach session ended")

def main():
    """Run the fixed sales coach."""
    coach = FixedSalesCoach()
    coach.run()

if __name__ == "__main__":
    main()