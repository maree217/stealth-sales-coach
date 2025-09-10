#!/usr/bin/env python3
"""
Debug version of working coach to identify issues.
"""

import sounddevice as sd
import numpy as np
import time
import sys
import traceback
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '.')
from sales_coach.src.models.config import load_config
from sales_coach.src.audio.transcription import WhisperTranscriber
from sales_coach.src.llm.coaching import create_coaching_system
from sales_coach.src.models.conversation import ConversationTurn, Speaker

def test_single_cycle():
    """Test one complete cycle: record -> transcribe -> coach."""
    print("🧪 SINGLE CYCLE TEST")
    print("=" * 40)
    
    # Load config
    print("Loading config...")
    config = load_config(Path("config/default.yaml"))
    print("✅ Config loaded")
    
    # Load transcriber
    print("Loading transcriber...")
    transcriber = WhisperTranscriber(config.models)
    if not transcriber.load_model():
        print("❌ Transcriber failed")
        return
    print("✅ Transcriber loaded")
    
    # Load coaching system
    print("Loading coaching system...")
    coaching_system = create_coaching_system(config.models, config.coaching)
    if not coaching_system:
        print("❌ Coaching system failed")
        return
    print("✅ Coaching system loaded")
    
    # Record audio
    print("\n🎤 Recording 3 seconds of audio...")
    print("SPEAK NOW!")
    
    sample_rate = 16000
    duration = 3
    
    try:
        audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype=np.float32)
        sd.wait()
        
        audio_1d = audio_data.flatten()
        rms = np.sqrt(np.mean(audio_1d**2))
        
        print(f"📊 Audio captured: RMS={rms:.6f}, Shape={audio_1d.shape}")
        
        if rms < 0.001:
            print("❌ No audio detected")
            return
            
        # Transcribe
        print("🔄 Transcribing...")
        try:
            result = transcriber.transcribe_audio(audio_1d)
            
            if result and result.text and result.text.strip():
                text = result.text.strip()
                print(f"✅ Transcription: '{text}'")
                print(f"   Confidence: {result.confidence:.3f}")
                
                # Coach
                print("🧠 Getting coaching advice...")
                try:
                    turn = ConversationTurn(
                        speaker=Speaker.UNKNOWN,
                        text=text,
                        timestamp=datetime.now(),
                        confidence=result.confidence
                    )
                    
                    coaching_system.add_conversation_turn(turn)
                    coaching_response = coaching_system.force_analysis()
                    
                    if coaching_response and coaching_response.primary_advice:
                        advice = coaching_response.primary_advice
                        print(f"✅ COACHING SUCCESS:")
                        print(f"   Priority: {advice.priority.value}")
                        print(f"   Category: {advice.category.value}")
                        print(f"   Insight: {advice.insight}")
                        print(f"   Action: {advice.suggested_action}")
                    else:
                        print("❌ No coaching advice generated")
                        
                except Exception as e:
                    print(f"❌ Coaching error: {e}")
                    traceback.print_exc()
                    
            else:
                print("❌ No transcription result")
                print(f"   Result: {result}")
                
        except Exception as e:
            print(f"❌ Transcription error: {e}")
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ Audio recording error: {e}")
        traceback.print_exc()

def main():
    """Run single cycle test."""
    test_single_cycle()

if __name__ == "__main__":
    main()