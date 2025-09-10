#!/usr/bin/env python3
"""
Live debugging script - run this while playing audio.
Shows real-time diagnostics of what the system is detecting.
"""

import asyncio
import sys
import time
import threading
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

from sales_coach.src.models.config import load_config
from sales_coach.src.audio.capture import AudioCaptureSystem
from sales_coach.src.audio.vad import create_vad
from sales_coach.src.audio.transcription import WhisperTranscriber
from sales_coach.src.llm.coaching import create_coaching_system
from sales_coach.src.models.conversation import ConversationTurn, Speaker

class LiveDebugger:
    def __init__(self):
        print("🔧 LIVE DEBUGGER STARTING...")
        
        # Load config
        try:
            self.config = load_config(Path("config/default.yaml"))
            print("✅ Config loaded")
        except Exception as e:
            print(f"❌ Config failed: {e}")
            sys.exit(1)
        
        # Initialize components
        self.audio_capture = None
        self.vad = None
        self.transcriber = None
        self.coaching_system = None
        
        # Stats
        self.audio_chunks_received = 0
        self.speech_segments_detected = 0
        self.transcriptions_generated = 0
        
        # Running state
        self.is_running = False
        
    def initialize_components(self):
        """Initialize all system components."""
        print("\n🔧 INITIALIZING COMPONENTS...")
        
        # Audio capture
        try:
            self.audio_capture = AudioCaptureSystem(self.config.audio)
            print("✅ Audio capture system ready")
        except Exception as e:
            print(f"❌ Audio capture failed: {e}")
            return False
        
        # VAD
        try:
            self.vad = create_vad(self.config.audio, adaptive=True)
            if hasattr(self.vad, 'base_vad'):
                loaded = self.vad.base_vad.load_model()
            else:
                loaded = self.vad.load_model()
            print(f"✅ VAD ready (Silero loaded: {loaded})")
        except Exception as e:
            print(f"❌ VAD failed: {e}")
            return False
            
        # Transcription
        try:
            self.transcriber = WhisperTranscriber(self.config.models)
            transcriber_loaded = self.transcriber.load_model()
            print(f"✅ Transcriber ready (loaded: {transcriber_loaded})")
        except Exception as e:
            print(f"❌ Transcriber failed: {e}")
            return False
            
        # Coaching
        try:
            self.coaching_system = create_coaching_system(self.config.models, self.config.coaching)
            if self.coaching_system:
                print("✅ Coaching system ready")
            else:
                print("❌ Coaching system failed to initialize")
                return False
        except Exception as e:
            print(f"❌ Coaching failed: {e}")
            return False
            
        return True
    
    def audio_callback(self, audio_chunk):
        """Process incoming audio chunks."""
        self.audio_chunks_received += 1
        
        if self.audio_chunks_received % 10 == 0:
            # Show audio level every 10th chunk
            rms = np.sqrt(np.mean(audio_chunk**2))
            print(f"🎤 Audio chunk #{self.audio_chunks_received}: RMS={rms:.4f}, Shape={audio_chunk.shape}")
        
        # VAD processing
        try:
            timestamp = time.time()
            voice_segments = self.vad.process_audio_stream(audio_chunk, timestamp)
            
            if voice_segments:
                self.speech_segments_detected += len(voice_segments)
                print(f"🗣️  SPEECH DETECTED! Segments: {len(voice_segments)}")
                
                # Process each voice segment
                for segment in voice_segments:
                    self.process_voice_segment(segment)
                    
        except Exception as e:
            print(f"❌ VAD processing error: {e}")
    
    def process_voice_segment(self, voice_segment):
        """Process a detected voice segment."""
        try:
            print(f"🎯 Processing voice segment: {voice_segment.start_time:.2f}s-{voice_segment.end_time:.2f}s, confidence={voice_segment.confidence:.2f}")
            
            if voice_segment.audio_data is not None and len(voice_segment.audio_data) > 8000:  # At least 0.5s at 16kHz
                # Transcribe
                result = self.transcriber.transcribe_audio(voice_segment.audio_data)
                
                if result and result.text and result.text.strip():
                    self.transcriptions_generated += 1
                    text = result.text.strip()
                    print(f"📝 TRANSCRIPTION #{self.transcriptions_generated}: '{text}' (confidence: {result.confidence:.2f})")
                    
                    # Create conversation turn
                    turn = ConversationTurn(
                        speaker=Speaker.UNKNOWN,  # We'd need diarization for this
                        text=text,
                        timestamp=voice_segment.start_time,
                        confidence=result.confidence
                    )
                    
                    # Get coaching
                    self.coaching_system.add_conversation_turn(turn)
                    coaching_response = self.coaching_system.force_analysis()
                    
                    if coaching_response and coaching_response.primary_advice:
                        advice = coaching_response.primary_advice
                        print(f"🧠 COACHING: [{advice.priority.value}] {advice.category.value}: {advice.insight}")
                        print(f"   Action: {advice.suggested_action}")
                    else:
                        print("🤔 No coaching advice generated")
                else:
                    print("🔇 No transcription from segment")
            else:
                print("⏸️  Segment too short for transcription")
                
        except Exception as e:
            print(f"❌ Voice segment processing error: {e}")
    
    def start_monitoring(self):
        """Start live monitoring."""
        if not self.initialize_components():
            print("❌ Component initialization failed")
            return
            
        print(f"\n🎬 STARTING LIVE MONITORING...")
        print(f"Available audio devices:")
        devices = self.audio_capture.device_manager.get_input_devices()
        for device in devices:
            print(f"  • {device.name} ({device.channels} channels)")
        
        print(f"\n🎤 Now speak or play audio...")
        print(f"📊 Will show: Audio levels → VAD → Transcription → Coaching")
        print(f"Press Ctrl+C to stop\n")
        
        # Set up audio callback
        self.audio_capture.set_audio_callback(self.audio_callback)
        
        # Start capture
        self.is_running = True
        if not self.audio_capture.start_capture():
            print("❌ Failed to start audio capture")
            return
            
        try:
            # Keep running and show stats
            while self.is_running:
                time.sleep(5)
                print(f"\n📈 STATS: Audio chunks: {self.audio_chunks_received}, Speech segments: {self.speech_segments_detected}, Transcriptions: {self.transcriptions_generated}")
                
        except KeyboardInterrupt:
            print(f"\n🛑 Stopping...")
            self.is_running = False
            self.audio_capture.stop_capture()
            print(f"Final stats - Chunks: {self.audio_chunks_received}, Speech: {self.speech_segments_detected}, Transcriptions: {self.transcriptions_generated}")

def main():
    debugger = LiveDebugger()
    debugger.start_monitoring()

if __name__ == "__main__":
    main()