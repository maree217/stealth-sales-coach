#!/usr/bin/env python3
"""
WORKING Sales Coach - Simplified version that actually works!
Based on successful audio + transcription test.
"""

import sounddevice as sd
import numpy as np
import time
import sys
import threading
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '.')
from sales_coach.src.models.config import load_config
from sales_coach.src.audio.transcription import WhisperTranscriber
from sales_coach.src.llm.coaching import create_coaching_system
from sales_coach.src.models.conversation import ConversationTurn, Speaker

class WorkingCoach:
    def __init__(self):
        print("🚀 WORKING SALES COACH")
        print("=" * 50)
        
        # Load config
        self.config = load_config(Path("config/default.yaml"))
        
        # Initialize systems
        print("Loading AI models...")
        self.transcriber = WhisperTranscriber(self.config.models)
        if not self.transcriber.load_model():
            print("❌ Failed to load Whisper")
            sys.exit(1)
        print("✅ Whisper loaded")
        
        self.coaching_system = create_coaching_system(self.config.models, self.config.coaching)
        if not self.coaching_system:
            print("❌ Failed to load coaching system")
            sys.exit(1)
        print("✅ Coaching system loaded")
        
        # Audio settings
        self.sample_rate = 16000
        self.chunk_duration = 3  # seconds
        self.running = True
        
    def detect_and_transcribe(self):
        """Continuously capture and transcribe audio."""
        print(f"\n🎤 Listening for audio...")
        print(f"Speak or play audio - processing every {self.chunk_duration} seconds")
        print("Press Ctrl+C to stop\n")
        
        chunk_count = 0
        
        while self.running:
            try:
                chunk_count += 1
                print(f"🔊 Recording chunk #{chunk_count} ({self.chunk_duration}s)...")
                
                # Record audio chunk
                audio_data = sd.rec(
                    int(self.chunk_duration * self.sample_rate), 
                    samplerate=self.sample_rate, 
                    channels=1, 
                    dtype=np.float32
                )
                sd.wait()
                
                # Check if audio was captured
                rms = np.sqrt(np.mean(audio_data**2))
                if rms < 0.001:
                    print(f"   📵 Silence (RMS: {rms:.6f})")
                    continue
                    
                print(f"   🎵 Audio detected (RMS: {rms:.6f})")
                
                # Transcribe
                audio_1d = audio_data.flatten()
                result = self.transcriber.transcribe_audio(audio_1d)
                
                if result and result.text and result.text.strip():
                    text = result.text.strip()
                    print(f"   📝 Transcription: '{text}'")
                    print(f"   🎯 Confidence: {result.confidence:.3f}")
                    
                    # Create conversation turn  
                    turn = ConversationTurn(
                        speaker=Speaker.UNKNOWN,  # Could add speaker detection later
                        text=text,
                        timestamp=datetime.now(),
                        confidence=result.confidence
                    )
                    
                    # Get coaching advice
                    self.coaching_system.add_conversation_turn(turn)
                    coaching_response = self.coaching_system.force_analysis()
                    
                    if coaching_response and coaching_response.primary_advice:
                        advice = coaching_response.primary_advice
                        print(f"   🧠 COACHING: [{advice.priority.value}] {advice.category.value}")
                        print(f"      💡 {advice.insight}")
                        print(f"      ▶️  {advice.suggested_action}")
                    else:
                        print(f"   🤔 No coaching advice generated")
                    
                else:
                    print(f"   🔇 No clear transcription")
                    
                print()  # Empty line for readability
                
            except KeyboardInterrupt:
                print("\n🛑 Stopping...")
                self.running = False
            except Exception as e:
                print(f"❌ Error in chunk #{chunk_count}: {e}")
                
    def start(self):
        """Start the sales coach."""
        try:
            self.detect_and_transcribe()
        except Exception as e:
            print(f"❌ Fatal error: {e}")
            
def main():
    """Run the working sales coach."""
    coach = WorkingCoach()
    coach.start()

if __name__ == "__main__":
    main()