#!/usr/bin/env python3
"""
STABLE Sales Coach - Crash-resistant version with memory management.
"""

import sounddevice as sd
import numpy as np
import time
import sys
import signal
import gc
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '.')
from sales_coach.src.models.config import load_config
from sales_coach.src.audio.transcription import WhisperTranscriber
from sales_coach.src.llm.coaching import create_coaching_system
from sales_coach.src.models.conversation import ConversationTurn, Speaker

class StableSalesCoach:
    def __init__(self):
        self.running = True
        
        print("💪 STABLE SALES COACH - Crash-Resistant Version")
        print("=" * 60)
        
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
            print("❌ Failed to load Whisper")
            sys.exit(1)
        print("   ✅ Speech-to-text ready")
        
        # Coaching
        self.coaching_system = create_coaching_system(self.config.models, self.config.coaching)
        if not self.coaching_system:
            print("❌ Failed to load coaching AI")
            sys.exit(1)
        print("   ✅ AI coaching ready")
        
        # Audio settings
        self.sample_rate = 16000
        self.chunk_duration = 4  # Shorter chunks for stability
        self.audio_threshold = 0.001
        
        # Stability tracking
        self.coaching_errors = 0
        self.max_coaching_errors = 3
        self.turns_processed = 0
        
        print("\n🎤 Stable audio detection ready")
        
    def _signal_handler(self, signum, frame):
        print(f"\n🛑 Shutting down...")
        self.running = False
        
    def _safe_coaching_analysis(self, turn):
        """Safely attempt coaching analysis with error handling."""
        try:
            self.coaching_system.add_conversation_turn(turn)
            coaching_response = self.coaching_system.force_analysis()
            
            if coaching_response and coaching_response.primary_advice:
                self.coaching_errors = 0  # Reset error counter on success
                return coaching_response.primary_advice
            else:
                return None
                
        except Exception as e:
            self.coaching_errors += 1
            print(f"   ⚠️  Coaching error #{self.coaching_errors}: {str(e)[:50]}...")
            
            if self.coaching_errors >= self.max_coaching_errors:
                print(f"   🔄 Restarting coaching system due to repeated errors...")
                try:
                    # Reinitialize coaching system
                    self.coaching_system = create_coaching_system(self.config.models, self.config.coaching)
                    self.coaching_errors = 0
                    print(f"   ✅ Coaching system restarted")
                except Exception as restart_error:
                    print(f"   ❌ Failed to restart coaching: {restart_error}")
                    
            return None
    
    def run(self):
        print(f"\n🎯 STABLE SALES COACH ACTIVE")
        print(f"Chunk: {self.chunk_duration}s, Threshold: {self.audio_threshold}")
        print("Built-in crash resistance and memory management")
        print("Press Ctrl+C to stop\n")
        
        chunk_count = 0
        successful_transcriptions = 0
        successful_coaching = 0
        
        try:
            while self.running:
                chunk_count += 1
                
                try:
                    # Record audio
                    print(f"🎙️  Chunk #{chunk_count} ({self.chunk_duration}s)...", end="", flush=True)
                    
                    audio_data = sd.rec(
                        int(self.chunk_duration * self.sample_rate), 
                        samplerate=self.sample_rate, 
                        channels=1, 
                        dtype=np.float32
                    )
                    sd.wait()
                    
                    # Analyze audio
                    audio_1d = audio_data.flatten()
                    rms = np.sqrt(np.mean(audio_1d**2))
                    
                    print(f" RMS:{rms:.4f}")
                    
                    if rms > self.audio_threshold:
                        print(f"   🔊 Processing audio...")
                        
                        try:
                            # Transcribe
                            result = self.transcriber.transcribe_audio(audio_1d)
                            
                            if result and result.text and result.text.strip() and len(result.text.strip()) > 2:
                                text = result.text.strip()
                                successful_transcriptions += 1
                                
                                timestamp = datetime.now().strftime('%H:%M:%S')
                                word_count = len(text.split())
                                
                                print(f"   📝 [{timestamp}] \"{text}\" ({word_count} words)")
                                print(f"   🎯 Confidence: {result.confidence:.3f}")
                                
                                # Safe coaching analysis
                                turn = ConversationTurn(
                                    speaker=Speaker.UNKNOWN,
                                    text=text,
                                    timestamp=datetime.now(),
                                    confidence=result.confidence
                                )
                                
                                advice = self._safe_coaching_analysis(turn)
                                
                                if advice:
                                    successful_coaching += 1
                                    print(f"   🧠 COACHING [{advice.priority.value}] {advice.category.value}:")
                                    print(f"      💡 {advice.insight}")
                                    print(f"      ▶️  {advice.suggested_action}")
                                    print(f"   {'─' * 50}")
                                else:
                                    print(f"   🤔 No coaching advice available")
                                
                                # Memory cleanup every 10 turns
                                self.turns_processed += 1
                                if self.turns_processed % 10 == 0:
                                    gc.collect()
                                    
                            else:
                                print(f"   🔇 Transcription unclear")
                                
                        except Exception as e:
                            print(f"   ❌ Processing error: {str(e)[:50]}...")
                            
                    else:
                        if chunk_count % 5 == 0:  # Status every 5 quiet chunks
                            print(f"   📊 Status: {successful_transcriptions} transcriptions, {successful_coaching} coaching responses")
                    
                    print()  # Blank line
                
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"\n❌ Chunk #{chunk_count} error: {str(e)[:50]}...")
                    time.sleep(1)  # Brief pause on error
                    
        except KeyboardInterrupt:
            pass
            
        print(f"\n📈 STABLE SESSION SUMMARY:")
        print(f"   Audio chunks: {chunk_count}")  
        print(f"   Transcriptions: {successful_transcriptions}")
        print(f"   Coaching responses: {successful_coaching}")
        print(f"   Transcription rate: {(successful_transcriptions/max(1,chunk_count)*100):.1f}%")
        print(f"   Coaching success rate: {(successful_coaching/max(1,successful_transcriptions)*100):.1f}%")
        print(f"\n✅ Stable Sales Coach ended gracefully")

def main():
    coach = StableSalesCoach()
    coach.run()

if __name__ == "__main__":
    main()