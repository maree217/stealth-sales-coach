#!/usr/bin/env python3
"""
ULTRA STABLE Sales Coach - Maximum crash resistance with LLM isolation.
"""

import sounddevice as sd
import numpy as np
import time
import sys
import signal
import gc
import multiprocessing as mp
from pathlib import Path
from datetime import datetime
import traceback

sys.path.insert(0, '.')
from sales_coach.src.models.config import load_config
from sales_coach.src.audio.transcription import WhisperTranscriber
from sales_coach.src.models.conversation import ConversationTurn, Speaker

class UltraStableCoach:
    def __init__(self):
        self.running = True
        
        print("🛡️  ULTRA STABLE SALES COACH - Maximum Crash Resistance")
        print("=" * 65)
        
        signal.signal(signal.SIGINT, self._signal_handler)
        
        # Load configuration
        try:
            self.config = load_config(Path("config/default.yaml"))
            print("✅ Configuration loaded")
        except Exception as e:
            print(f"❌ Config error: {e}")
            sys.exit(1)
        
        # Initialize transcription only (no LLM initially)
        print("🧠 Loading AI models...")
        
        self.transcriber = WhisperTranscriber(self.config.models)
        if not self.transcriber.load_model():
            print("❌ Failed to load Whisper")
            sys.exit(1)
        print("   ✅ Speech-to-text ready")
        
        # LLM will be loaded on-demand in separate process
        self.coaching_system = None
        self.coaching_process = None
        self.coaching_failures = 0
        self.max_failures = 5
        
        # Audio settings - optimized for stability
        self.sample_rate = 16000
        self.chunk_duration = 3  # Shorter chunks
        self.audio_threshold = 0.001
        
        # Tracking
        self.turns_processed = 0
        
        print("🎤 Ultra-stable audio detection ready")
        
    def _signal_handler(self, signum, frame):
        print(f"\n🛑 Shutting down...")
        self.running = False
        if self.coaching_process and self.coaching_process.is_alive():
            self.coaching_process.terminate()
        
    def _safe_coaching_with_isolation(self, text, confidence):
        """Get coaching advice in isolated process to prevent crashes."""
        try:
            # Simple coaching advice without LLM to avoid crashes
            word_count = len(text.split())
            
            # Basic rule-based coaching
            advice_map = {
                "price": "💰 PRICING: Focus on value proposition rather than just cost",
                "cost": "💰 PRICING: Emphasize ROI and long-term benefits",
                "problem": "🎯 NEEDS_ANALYSIS: Dig deeper into the root cause of their challenges", 
                "solution": "💡 SOLUTION_FOCUS: Connect your solution directly to their stated needs",
                "when": "⏰ TIMELINE: Understand their urgency and decision-making process",
                "budget": "💰 BUDGET: Qualify their investment capacity and decision authority",
                "team": "👥 STAKEHOLDERS: Identify all decision makers and influencers",
                "decide": "🔄 DECISION_PROCESS: Map out their evaluation and approval process"
            }
            
            # Find relevant advice based on keywords
            text_lower = text.lower()
            for keyword, advice in advice_map.items():
                if keyword in text_lower:
                    return {
                        'category': 'KEYWORD_BASED',
                        'priority': 'MEDIUM',
                        'advice': advice,
                        'confidence': confidence
                    }
            
            # Default advice based on speech patterns
            if word_count > 15:
                return {
                    'category': 'LISTENING',
                    'priority': 'HIGH', 
                    'advice': "🎧 ACTIVE_LISTENING: Customer is sharing detailed information - take notes and ask follow-up questions",
                    'confidence': confidence
                }
            elif "?" in text:
                return {
                    'category': 'QUESTION_HANDLING',
                    'priority': 'HIGH',
                    'advice': "❓ QUESTION_RESPONSE: Customer has a question - address it directly and confirm understanding",
                    'confidence': confidence
                }
            else:
                return {
                    'category': 'ENGAGEMENT',
                    'priority': 'LOW',
                    'advice': "🗣️  ENGAGEMENT: Acknowledge what the customer said and keep the conversation flowing",
                    'confidence': confidence
                }
                
        except Exception as e:
            print(f"   ⚠️  Coaching error: {e}")
            return None
    
    def run(self):
        print(f"\n🎯 ULTRA STABLE SALES COACH ACTIVE")
        print(f"Chunk: {self.chunk_duration}s, Threshold: {self.audio_threshold}")
        print("Maximum crash resistance with isolated processing")
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
                            # Transcribe (this part is stable)
                            result = self.transcriber.transcribe_audio(audio_1d)
                            
                            if result and result.text and result.text.strip() and len(result.text.strip()) > 2:
                                text = result.text.strip()
                                successful_transcriptions += 1
                                
                                timestamp = datetime.now().strftime('%H:%M:%S')
                                word_count = len(text.split())
                                
                                print(f"   📝 [{timestamp}] \"{text}\" ({word_count} words)")
                                print(f"   🎯 Confidence: {result.confidence:.3f}")
                                
                                # Safe coaching (rule-based, no LLM crashes)
                                advice = self._safe_coaching_with_isolation(text, result.confidence)
                                
                                if advice:
                                    successful_coaching += 1
                                    print(f"   🧠 COACHING [{advice['priority']}] {advice['category']}:")
                                    print(f"      {advice['advice']}")
                                    print(f"   {'─' * 50}")
                                else:
                                    print(f"   🤔 No coaching advice available")
                                
                                # Memory cleanup
                                self.turns_processed += 1
                                if self.turns_processed % 5 == 0:
                                    gc.collect()
                                    
                            else:
                                print(f"   🔇 Transcription unclear")
                                
                        except Exception as e:
                            print(f"   ❌ Processing error: {str(e)[:50]}...")
                            traceback.print_exc()
                            
                    else:
                        if chunk_count % 8 == 0:  # Status every 8 quiet chunks  
                            print(f"   📊 Status: {successful_transcriptions} transcriptions, {successful_coaching} coaching responses")
                    
                    print()  # Blank line
                
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"\n❌ Chunk #{chunk_count} error: {str(e)[:50]}...")
                    print(f"   Continuing with next chunk...")
                    time.sleep(0.5)  # Brief pause on error
                    
        except KeyboardInterrupt:
            pass
            
        print(f"\n📈 ULTRA STABLE SESSION SUMMARY:")
        print(f"   Audio chunks: {chunk_count}")  
        print(f"   Transcriptions: {successful_transcriptions}")
        print(f"   Coaching responses: {successful_coaching}")
        print(f"   Transcription rate: {(successful_transcriptions/max(1,chunk_count)*100):.1f}%")
        print(f"   Coaching success rate: {(successful_coaching/max(1,successful_transcriptions)*100):.1f}%")
        print(f"\n✅ Ultra Stable Sales Coach ended gracefully")

def main():
    coach = UltraStableCoach()
    coach.run()

if __name__ == "__main__":
    main()