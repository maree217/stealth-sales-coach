#!/usr/bin/env python3
"""
🚀 PRODUCTION SALES COACH
Fully working real-time sales coaching system.

Usage:
    python run_sales_coach.py

The system will:
1. Listen to your microphone continuously  
2. Transcribe speech in real-time
3. Provide AI coaching advice for sales conversations
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

class ProductionSalesCoach:
    def __init__(self):
        self.running = True
        
        print("🚀 SALES COACH - Real-time AI Coaching")
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
        
        # Audio settings
        self.sample_rate = 16000
        self.chunk_duration = 4  # Process every 4 seconds
        
        print("\n🎤 Audio system ready")
        self._show_audio_devices()
        
    def _signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully."""
        print(f"\n🛑 Shutting down gracefully...")
        self.running = False
        
    def _show_audio_devices(self):
        """Show available audio devices."""
        devices = sd.query_devices()
        input_devices = [(i, dev) for i, dev in enumerate(devices) if dev['max_input_channels'] > 0]
        
        if input_devices:
            print("   Available input devices:")
            for i, device in input_devices[:3]:  # Show first 3
                print(f"     • {device['name']} ({device['max_input_channels']} ch)")
        
        default = sd.default.device
        print(f"   Using default device: {default}")
        
    def run(self):
        """Run the sales coach continuously."""
        print(f"\n🎯 SALES COACH ACTIVE")
        print(f"Processing audio every {self.chunk_duration} seconds")
        print("Speak naturally during calls - coaching will appear automatically")
        print("Press Ctrl+C to stop\n")
        
        chunk_count = 0
        successful_transcriptions = 0
        
        try:
            while self.running:
                chunk_count += 1
                
                # Record audio chunk
                try:
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
                    
                    # Only process if there's meaningful audio
                    if rms > 0.005:  # Threshold for speech
                        print(f"🔊 Processing audio #{chunk_count} (level: {rms:.4f})")
                        
                        # Transcribe
                        result = self.transcriber.transcribe_audio(audio_1d)
                        
                        if result and result.text and result.text.strip() and len(result.text.strip()) > 3:
                            text = result.text.strip()
                            successful_transcriptions += 1
                            
                            print(f"📝 [{datetime.now().strftime('%H:%M:%S')}] \"{text}\"")
                            print(f"   Confidence: {result.confidence:.2f}")
                            
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
                                
                                # Format coaching output
                                print(f"🧠 COACHING [{advice.priority.value}] {advice.category.value}:")
                                print(f"   💡 {advice.insight}")
                                print(f"   ▶️  {advice.suggested_action}")
                                
                                # Add visual separator
                                print(f"   {'─' * 50}")
                            
                        else:
                            # Low confidence or short transcription
                            if chunk_count % 5 == 0:  # Show status every 5 chunks
                                print(f"📊 Status: {successful_transcriptions} transcriptions from {chunk_count} audio chunks")
                    
                    else:
                        # Silence - show minimal status
                        if chunk_count % 10 == 0:  # Show status every 10 silent chunks
                            print(f"🔇 Listening... ({chunk_count} chunks processed, {successful_transcriptions} transcribed)")
                
                except Exception as e:
                    print(f"❌ Error in chunk #{chunk_count}: {e}")
                    
        except KeyboardInterrupt:
            pass  # Handled by signal handler
            
        print(f"\n📈 SESSION SUMMARY:")
        print(f"   Audio chunks processed: {chunk_count}")  
        print(f"   Successful transcriptions: {successful_transcriptions}")
        print(f"   Success rate: {(successful_transcriptions/chunk_count*100):.1f}%")
        print(f"\n✅ Sales Coach session ended")

def main():
    """Run the production sales coach."""
    coach = ProductionSalesCoach()
    coach.run()

if __name__ == "__main__":
    main()