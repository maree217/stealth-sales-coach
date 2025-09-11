#!/usr/bin/env python3
"""
Stealth Sales Coach - Main Entry Point

A clean, professional entry point for the Stealth Sales Coach system.
This serves as the primary interface to the final integrated coach.

Usage:
    python main.py          # Start the sales coach
    python main.py --help   # Show help
"""

import sys
import argparse
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from final_integrated_coach import FinalIntegratedCoach


def main():
    """Main entry point for the Stealth Sales Coach."""
    parser = argparse.ArgumentParser(
        description="Stealth Sales Coach - Local AI-powered real-time sales coaching",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python main.py                    # Start the coach with default settings
    
Features:
    • Real-time speech transcription using OpenAI Whisper
    • AI-powered coaching advice using Microsoft Phi-3.5-mini
    • Process-isolated LLM for stability
    • Automatic fallback to rule-based coaching
    • Optimized audio detection (0.01 threshold)
    • Live conversation analysis and coaching
        """
    )
    
    parser.add_argument(
        '--version', 
        action='version', 
        version='Stealth Sales Coach v1.2 - Final Integrated'
    )
    
    parser.add_argument(
        '--config',
        type=Path,
        default=Path("config/default.yaml"),
        help='Path to configuration file (default: config/default.yaml)'
    )
    
    parser.add_argument(
        '--audio-threshold',
        type=float,
        default=0.01,
        help='Audio detection threshold (default: 0.01)'
    )
    
    parser.add_argument(
        '--chunk-duration',
        type=int,
        default=3,
        help='Audio chunk duration in seconds (default: 3)'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run in test mode (shows system status and exits)'
    )
    
    args = parser.parse_args()
    
    try:
        # Create and configure the coach
        coach = FinalIntegratedCoach()
        
        # Override default settings if provided
        if args.audio_threshold != 0.01:
            coach.audio_threshold = args.audio_threshold
            print(f"🎛️  Audio threshold set to: {args.audio_threshold}")
            
        if args.chunk_duration != 3:
            coach.chunk_duration = args.chunk_duration
            print(f"⏱️  Chunk duration set to: {args.chunk_duration} seconds")
        
        if args.test:
            print("\n🧪 TEST MODE")
            print("=" * 50)
            print(f"✅ Configuration loaded: {args.config}")
            print(f"✅ Audio threshold: {coach.audio_threshold}")
            print(f"✅ Chunk duration: {coach.chunk_duration}s")
            print(f"✅ LLM available: {coach.llm_available}")
            print("✅ System ready for live coaching")
            print("\nTo start live coaching, run without --test flag")
            return 0
        
        # Start the coach
        coach.run()
        return 0
        
    except KeyboardInterrupt:
        print("\n👋 Sales Coach stopped by user")
        return 0
    except Exception as e:
        print(f"\n❌ Error starting Sales Coach: {e}")
        print("\nTroubleshooting:")
        print("1. Check that your microphone is working and accessible")
        print("2. Ensure all dependencies are installed: pip install -r requirements.txt")
        print("3. Verify the configuration file exists: config/default.yaml")
        print("4. Try running tests: python -m tests.test_automation")
        return 1


if __name__ == "__main__":
    sys.exit(main())