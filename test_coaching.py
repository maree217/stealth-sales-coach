#!/usr/bin/env python3
"""
Test script to verify coaching system works with our fixes.
"""

from pathlib import Path
from datetime import datetime

from sales_coach.src.models.config import load_config
from sales_coach.src.models.conversation import ConversationTurn, Speaker, ConversationState
from sales_coach.src.llm.coaching import create_coaching_system

def test_coaching_system():
    """Test the coaching system with our fixes."""
    print("🧠 TESTING COACHING SYSTEM")
    print("=" * 40)
    
    # Load config
    config_path = Path("config/default.yaml")
    config = load_config(config_path)
    
    print(f"Model path: {config.models.llm_model_path}")
    
    # Create coaching system
    print("Loading coaching system...")
    coaching_system = create_coaching_system(config.models, config.coaching)
    
    if not coaching_system:
        print("❌ Failed to create coaching system")
        return False
    
    print("✅ Coaching system loaded")
    
    # Create test conversation
    turns = [
        ConversationTurn(
            speaker=Speaker.SALES_REP,
            text="Hello, can you hear me now?",
            timestamp=datetime.now(),
            confidence=0.95
        ),
        ConversationTurn(
            speaker=Speaker.CUSTOMER,
            text="Yes, I can hear you. What's this about?",
            timestamp=datetime.now(),
            confidence=0.88
        ),
        ConversationTurn(
            speaker=Speaker.SALES_REP,
            text="I wanted to discuss our enterprise software solution for your company.",
            timestamp=datetime.now(),
            confidence=0.92
        )
    ]
    
    print("\nAdding test conversation turns...")
    for i, turn in enumerate(turns, 1):
        print(f"Turn {i}: {turn.speaker.value}: {turn.text}")
        coaching_system.add_conversation_turn(turn)
    
    # Force analysis
    print("\nForcing coaching analysis...")
    response = coaching_system.force_analysis()
    
    if response:
        print("✅ Coaching analysis successful!")
        print(f"   Priority: {response.primary_advice.priority.value}")
        print(f"   Category: {response.primary_advice.category.value}")
        print(f"   Insight: {response.primary_advice.insight}")
        print(f"   Action: {response.primary_advice.suggested_action}")
        print(f"   Confidence: {response.confidence:.2f}")
        return True
    else:
        print("❌ Coaching analysis failed")
        return False

def main():
    """Run the test."""
    success = test_coaching_system()
    
    print(f"\n{'='*40}")
    if success:
        print("✅ ALL TESTS PASSED - Coaching system is working!")
    else:
        print("❌ TESTS FAILED - Check logs for errors")
    print("="*40)

if __name__ == "__main__":
    main()