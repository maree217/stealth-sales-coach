#!/usr/bin/env python3
"""
FINAL INTEGRATED SALES COACH
Based on component testing results:
- ✅ Display: Working perfectly
- ❌ LLM: Process isolation + fallback
- ⚠️  Audio: Higher threshold + better detection
- ✅ Integration: Step-by-step approach
"""

import sounddevice as sd
import numpy as np
import time
import sys
import signal
import gc
import subprocess
import tempfile
import json
from pathlib import Path
from datetime import datetime
from enum import Enum

sys.path.insert(0, '.')
from sales_coach.src.models.config import load_config
from sales_coach.src.audio.transcription import WhisperTranscriber
from sales_coach.src.models.conversation import ConversationTurn, Speaker

class CoachingCategory(Enum):
    QUESTIONING = "QUESTIONING"
    LISTENING = "LISTENING"
    OBJECTION_HANDLING = "OBJECTION_HANDLING"
    VALUE_PROPOSITION = "VALUE_PROPOSITION"
    CLOSING = "CLOSING"
    RAPPORT_BUILDING = "RAPPORT_BUILDING"

class CoachingPriority(Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class FinalIntegratedCoach:
    def __init__(self):
        self.running = True
        
        print("🚀 FINAL INTEGRATED SALES COACH")
        print("Based on comprehensive component testing")
        print("=" * 60)
        
        signal.signal(signal.SIGINT, self._signal_handler)
        
        # Load configuration
        try:
            self.config = load_config(Path("config/default.yaml"))
            print("✅ Configuration loaded")
        except Exception as e:
            print(f"❌ Config error: {e}")
            sys.exit(1)
        
        # Audio settings - optimized based on testing
        self.sample_rate = 16000
        self.chunk_duration = 3
        self.audio_threshold = 0.01  # Higher threshold based on testing
        
        # Initialize transcription
        print("🧠 Loading AI models...")
        self.transcriber = WhisperTranscriber(self.config.models)
        if not self.transcriber.load_model():
            print("❌ Failed to load Whisper")
            sys.exit(1)
        print("   ✅ Speech-to-text ready")
        
        # LLM coaching - isolated process approach
        self.llm_available = False
        self.llm_failures = 0
        self.max_llm_failures = 3
        
        print("   🔧 Testing LLM coaching availability...")
        if self._test_llm_availability():
            print("   ✅ AI coaching ready (process-isolated)")
            self.llm_available = True
        else:
            print("   ⚠️  Using fallback rule-based coaching")
            self.llm_available = False
        
        # Tracking
        self.chunk_count = 0
        self.transcription_count = 0
        self.coaching_count = 0
        self.session_start = datetime.now()
        
        print("🎤 Enhanced audio detection ready")
        self._show_audio_setup()
        
    def _signal_handler(self, signum, frame):
        print(f"\n🛑 Shutting down...")
        self.running = False
        
    def _show_audio_setup(self):
        """Show audio device information."""
        try:
            devices = sd.query_devices()
            input_devices = [(i, dev) for i, dev in enumerate(devices) if dev['max_input_channels'] > 0]
            
            print("   Available input devices:")
            for i, device in input_devices[:3]:  # Show first 3
                marker = " 👈 DEFAULT" if i == sd.default.device[0] else ""
                print(f"     {i}: {device['name']}{marker}")
                
            print(f"   Audio threshold: {self.audio_threshold} (optimized for speech)")
            
        except Exception as e:
            print(f"   ⚠️  Audio device info error: {e}")
    
    def _test_llm_availability(self):
        """Test if LLM coaching is available via subprocess."""
        try:
            # Create a simple LLM test script
            llm_test_script = f'''
import sys
sys.path.insert(0, '.')
from sales_coach.src.models.config import load_config
from sales_coach.src.llm.coaching import create_coaching_system
from pathlib import Path

try:
    config = load_config(Path("config/default.yaml"))
    # Reduce context to prevent timeout
    config.models.llm_context_length = 512
    config.models.llm_max_tokens = 50
    
    coaching_system = create_coaching_system(config.models, config.coaching)
    if coaching_system:
        print("SUCCESS:LLM_AVAILABLE")
    else:
        print("ERROR:LLM_FAILED_TO_LOAD")
except Exception as e:
    print(f"ERROR:{{str(e)[:50]}}")
'''
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(llm_test_script)
                script_path = f.name
            
            # Run with timeout
            result = subprocess.run([
                sys.executable, script_path
            ], capture_output=True, text=True, timeout=30)
            
            Path(script_path).unlink()  # Cleanup
            
            return result.returncode == 0 and "SUCCESS:LLM_AVAILABLE" in result.stdout
            
        except Exception as e:
            print(f"      LLM test error: {e}")
            return False
    
    def _get_coaching_advice(self, text, confidence):
        """Get coaching advice using available method."""
        if self.llm_available and self.llm_failures < self.max_llm_failures:
            # Try LLM coaching in subprocess
            advice = self._try_llm_coaching(text, confidence)
            if advice:
                return advice
            else:
                self.llm_failures += 1
                if self.llm_failures >= self.max_llm_failures:
                    print("   ⚠️  LLM coaching disabled due to repeated failures")
                    self.llm_available = False
        
        # Fallback to rule-based coaching
        return self._rule_based_coaching(text, confidence)
    
    def _try_llm_coaching(self, text, confidence):
        """Try LLM coaching with subprocess isolation."""
        try:
            # Create LLM coaching script
            coaching_script = f'''
import sys
import json
sys.path.insert(0, '.')
from sales_coach.src.models.config import load_config
from sales_coach.src.llm.coaching import create_coaching_system
from sales_coach.src.models.conversation import ConversationTurn, Speaker
from pathlib import Path
from datetime import datetime

try:
    config = load_config(Path("config/default.yaml"))
    # Use smaller context for stability
    config.models.llm_context_length = 512
    config.models.llm_max_tokens = 100
    
    coaching_system = create_coaching_system(config.models, config.coaching)
    if not coaching_system:
        print("ERROR:FAILED_TO_LOAD")
        sys.exit(1)
    
    turn = ConversationTurn(
        speaker=Speaker.UNKNOWN,
        text="{text}",
        timestamp=datetime.now(),
        confidence={confidence}
    )
    
    coaching_system.add_conversation_turn(turn)
    response = coaching_system.force_analysis()
    
    if response and response.primary_advice:
        advice = response.primary_advice
        result = {{
            "priority": advice.priority.value,
            "category": advice.category.value,
            "insight": advice.insight,
            "suggested_action": advice.suggested_action
        }}
        print(f"SUCCESS:{{json.dumps(result)}}")
    else:
        print("ERROR:NO_ADVICE_GENERATED")
        
except Exception as e:
    print(f"ERROR:{{str(e)[:100]}}")
'''
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(coaching_script)
                script_path = f.name
            
            # Run with short timeout
            result = subprocess.run([
                sys.executable, script_path
            ], capture_output=True, text=True, timeout=15)
            
            Path(script_path).unlink()  # Cleanup
            
            if result.returncode == 0 and "SUCCESS:" in result.stdout:
                json_str = result.stdout.split("SUCCESS:")[1].strip()
                advice_data = json.loads(json_str)
                
                return {
                    'priority': CoachingPriority(advice_data['priority']),
                    'category': CoachingCategory(advice_data['category']),
                    'insight': advice_data['insight'],
                    'suggested_action': advice_data['suggested_action']
                }
            else:
                return None
                
        except Exception:
            return None
    
    def _rule_based_coaching(self, text, confidence):
        """Fallback rule-based coaching system."""
        text_lower = text.lower()
        word_count = len(text.split())
        
        # Advanced rule-based coaching
        if any(word in text_lower for word in ['price', 'cost', 'expensive', 'budget', 'money']):
            return {
                'priority': CoachingPriority.HIGH,
                'category': CoachingCategory.OBJECTION_HANDLING,
                'insight': 'Customer is expressing price concerns',
                'suggested_action': 'Focus on value and ROI rather than just price. Ask about their cost of not solving the problem.'
            }
        elif any(word in text_lower for word in ['problem', 'challenge', 'issue', 'difficult']):
            return {
                'priority': CoachingPriority.HIGH,
                'category': CoachingCategory.QUESTIONING,
                'insight': 'Customer is sharing pain points - perfect discovery opportunity',
                'suggested_action': 'Ask follow-up questions to quantify the impact and urgency of their challenges.'
            }
        elif '?' in text:
            return {
                'priority': CoachingPriority.HIGH,
                'category': CoachingCategory.QUESTIONING,
                'insight': 'Customer is asking questions - shows engagement',
                'suggested_action': 'Answer clearly and then ask a follow-up question to maintain dialogue.'
            }
        elif any(word in text_lower for word in ['solution', 'help', 'solve', 'fix']):
            return {
                'priority': CoachingPriority.MEDIUM,
                'category': CoachingCategory.VALUE_PROPOSITION,
                'insight': 'Good opportunity to present your solution',
                'suggested_action': 'Connect your solution features directly to their specific needs and pain points.'
            }
        elif word_count > 20:
            return {
                'priority': CoachingPriority.MEDIUM,
                'category': CoachingCategory.LISTENING,
                'insight': 'Customer is sharing detailed information',
                'suggested_action': 'Listen actively, take notes, and summarize key points to show understanding.'
            }
        elif any(word in text_lower for word in ['hello', 'hi', 'thanks', 'thank']):
            return {
                'priority': CoachingPriority.LOW,
                'category': CoachingCategory.RAPPORT_BUILDING,
                'insight': 'Good rapport-building opportunity',
                'suggested_action': 'Acknowledge their time and transition smoothly into discovery questions.'
            }
        else:
            return {
                'priority': CoachingPriority.LOW,
                'category': CoachingCategory.LISTENING,
                'insight': 'Continue gathering information',
                'suggested_action': 'Keep the conversation flowing with open-ended questions and active listening.'
            }
    
    def run(self):
        print(f"\n🎯 FINAL INTEGRATED SALES COACH ACTIVE")
        print(f"Audio: {self.chunk_duration}s chunks, {self.audio_threshold} threshold")
        print(f"AI: {'LLM + Fallback' if self.llm_available else 'Rule-based'} coaching")
        print("Optimized based on component testing results")
        print("Press Ctrl+C to stop\n")
        
        try:
            while self.running:
                self.chunk_count += 1
                
                try:
                    # Record audio
                    print(f"🎙️  Chunk #{self.chunk_count} ({self.chunk_duration}s)...", end="", flush=True)
                    
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
                                self.transcription_count += 1
                                
                                timestamp = datetime.now().strftime('%H:%M:%S')
                                word_count = len(text.split())
                                
                                print(f"   📝 [{timestamp}] \"{text}\" ({word_count} words)")
                                print(f"   🎯 Confidence: {result.confidence:.3f}")
                                
                                # Get coaching advice
                                advice = self._get_coaching_advice(text, result.confidence)
                                
                                if advice:
                                    self.coaching_count += 1
                                    coach_type = "AI" if self.llm_available and self.llm_failures < self.max_llm_failures else "RULE"
                                    print(f"   🧠 {coach_type} COACHING [{advice['priority'].value}] {advice['category'].value}:")
                                    print(f"      💡 {advice['insight']}")
                                    print(f"      ▶️  {advice['suggested_action']}")
                                    print(f"   {'─' * 50}")
                                else:
                                    print(f"   🤔 No coaching advice available")
                                
                                # Memory cleanup
                                if self.transcription_count % 5 == 0:
                                    gc.collect()
                                    
                            else:
                                print(f"   🔇 Transcription unclear or too short")
                                
                        except Exception as e:
                            print(f"   ❌ Processing error: {str(e)[:50]}...")
                            
                    else:
                        if self.chunk_count % 10 == 0:  # Status every 10 quiet chunks
                            elapsed = (datetime.now() - self.session_start).total_seconds()
                            print(f"   📊 Status: {self.transcription_count} transcriptions, {self.coaching_count} coaching ({elapsed:.0f}s)")
                    
                    print()  # Blank line
                
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"\n❌ Chunk #{self.chunk_count} error: {str(e)[:50]}...")
                    time.sleep(1)  # Brief pause on error
                    
        except KeyboardInterrupt:
            pass
            
        # Session summary
        elapsed = (datetime.now() - self.session_start).total_seconds()
        print(f"\n📈 FINAL INTEGRATED SESSION SUMMARY:")
        print(f"   Session duration: {elapsed:.0f} seconds")
        print(f"   Audio chunks: {self.chunk_count}")  
        print(f"   Transcriptions: {self.transcription_count}")
        print(f"   Coaching responses: {self.coaching_count}")
        print(f"   Transcription rate: {(self.transcription_count/max(1,self.chunk_count)*100):.1f}%")
        print(f"   Coaching success rate: {(self.coaching_count/max(1,self.transcription_count)*100):.1f}%")
        print(f"   AI coaching: {'Available' if self.llm_available else 'Fallback mode'}")
        print(f"\n✅ Final Integrated Sales Coach ended gracefully")

def main():
    coach = FinalIntegratedCoach()
    coach.run()

if __name__ == "__main__":
    main()