#!/usr/bin/env python3
"""
Phase 1: Standalone LLM Test - Text input only, no audio/transcription
Test different context sizes and memory management for stable coaching.
"""

import sys
import time
import gc
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '.')
from sales_coach.src.models.config import load_config
from sales_coach.src.llm.coaching import create_coaching_system
from sales_coach.src.models.conversation import ConversationTurn, Speaker

class StandaloneLLMTest:
    def __init__(self):
        print("🧪 STANDALONE LLM COACHING TEST")
        print("=" * 50)
        
        # Load config
        try:
            self.config = load_config(Path("config/default.yaml"))
            print(f"✅ Config loaded - LLM context: {self.config.models.llm_context_length}")
        except Exception as e:
            print(f"❌ Config error: {e}")
            sys.exit(1)
    
    def test_context_sizes(self):
        """Test different context sizes to find stable limit."""
        print("\n🔍 Testing Different Context Sizes")
        print("-" * 40)
        
        context_sizes = [512, 1024, 2048, 4096, 8192]
        
        for context_size in context_sizes:
            print(f"\nTesting context size: {context_size}")
            
            # Temporarily modify config
            original_context = self.config.models.llm_context_length
            self.config.models.llm_context_length = context_size
            
            try:
                coaching_system = create_coaching_system(self.config.models, self.config.coaching)
                
                if coaching_system:
                    print(f"   ✅ LLM loaded successfully with {context_size} context")
                    
                    # Test simple coaching
                    result = self._test_simple_coaching(coaching_system)
                    if result:
                        print(f"   ✅ Coaching successful")
                    else:
                        print(f"   ❌ Coaching failed")
                    
                    # Cleanup
                    del coaching_system
                    gc.collect()
                    time.sleep(1)
                else:
                    print(f"   ❌ Failed to load LLM with {context_size} context")
                    
            except Exception as e:
                print(f"   ❌ Error with {context_size} context: {str(e)[:50]}...")
            
            # Restore original context
            self.config.models.llm_context_length = original_context
    
    def _test_simple_coaching(self, coaching_system):
        """Test simple coaching scenario."""
        try:
            # Create simple conversation
            turn = ConversationTurn(
                speaker=Speaker.SALES_REP,
                text="Hello, thanks for joining our call today. How can I help you?",
                timestamp=datetime.now(),
                confidence=0.95
            )
            
            coaching_system.add_conversation_turn(turn)
            response = coaching_system.force_analysis()
            
            return response and response.primary_advice
            
        except Exception as e:
            print(f"      Error in coaching test: {str(e)[:30]}...")
            return False
    
    def test_sustained_coaching(self):
        """Test sustained coaching with multiple turns."""
        print("\n🔄 Testing Sustained Coaching (10 turns)")
        print("-" * 40)
        
        try:
            coaching_system = create_coaching_system(self.config.models, self.config.coaching)
            
            if not coaching_system:
                print("❌ Failed to load coaching system")
                return False
            
            print("✅ Coaching system loaded")
            
            # Test conversations
            test_conversations = [
                ("SALES_REP", "Hello, thanks for taking the time to speak with me today."),
                ("CUSTOMER", "Sure, what's this about?"),
                ("SALES_REP", "I wanted to discuss how our automation tools could help your business."),
                ("CUSTOMER", "We're pretty happy with our current setup."),
                ("SALES_REP", "I understand. What challenges are you currently facing with data processing?"),
                ("CUSTOMER", "Well, manual data entry takes up a lot of our time."),
                ("SALES_REP", "That's exactly what our solution addresses. Can you tell me more about your current process?"),
                ("CUSTOMER", "We have to input everything manually from different sources."),
                ("SALES_REP", "How many hours per week would you say that takes?"),
                ("CUSTOMER", "Probably around 20 hours across the team.")
            ]
            
            successful_coaching = 0
            
            for i, (speaker, text) in enumerate(test_conversations, 1):
                print(f"\nTurn {i}: {speaker}: {text[:50]}...")
                
                turn = ConversationTurn(
                    speaker=Speaker.SALES_REP if speaker == "SALES_REP" else Speaker.CUSTOMER,
                    text=text,
                    timestamp=datetime.now(),
                    confidence=0.9
                )
                
                coaching_system.add_conversation_turn(turn)
                
                # Get coaching every 2 turns
                if i % 2 == 0:
                    try:
                        response = coaching_system.force_analysis()
                        
                        if response and response.primary_advice:
                            successful_coaching += 1
                            advice = response.primary_advice
                            print(f"   🧠 COACHING: [{advice.priority.value}] {advice.category.value}")
                            print(f"      💡 {advice.insight[:50]}...")
                            print(f"      ▶️  {advice.suggested_action[:50]}...")
                        else:
                            print(f"   ❌ No coaching generated")
                            
                    except Exception as e:
                        print(f"   ❌ Coaching error: {str(e)[:50]}...")
                
                # Memory cleanup every 5 turns
                if i % 5 == 0:
                    gc.collect()
                    time.sleep(0.1)
            
            print(f"\n📊 Results: {successful_coaching}/5 coaching responses successful")
            return successful_coaching >= 3
            
        except Exception as e:
            print(f"❌ Sustained test error: {e}")
            return False
    
    def test_memory_management(self):
        """Test memory usage and cleanup."""
        print("\n🧠 Testing Memory Management")
        print("-" * 40)
        
        try:
            import psutil
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            print(f"Initial memory: {initial_memory:.1f} MB")
            
            coaching_system = create_coaching_system(self.config.models, self.config.coaching)
            
            if not coaching_system:
                print("❌ Failed to load coaching system")
                return False
            
            load_memory = process.memory_info().rss / 1024 / 1024
            print(f"After LLM load: {load_memory:.1f} MB (+{load_memory - initial_memory:.1f} MB)")
            
            # Run multiple coaching cycles
            for cycle in range(5):
                turn = ConversationTurn(
                    speaker=Speaker.CUSTOMER,
                    text=f"This is test message number {cycle + 1} to check memory usage.",
                    timestamp=datetime.now(),
                    confidence=0.9
                )
                
                coaching_system.add_conversation_turn(turn)
                response = coaching_system.force_analysis()
                
                current_memory = process.memory_info().rss / 1024 / 1024
                print(f"Cycle {cycle + 1}: {current_memory:.1f} MB")
                
                # Force cleanup
                gc.collect()
            
            # Final cleanup
            del coaching_system
            gc.collect()
            final_memory = process.memory_info().rss / 1024 / 1024
            print(f"After cleanup: {final_memory:.1f} MB")
            
            return True
            
        except ImportError:
            print("⚠️  psutil not available, skipping memory test")
            return True
        except Exception as e:
            print(f"❌ Memory test error: {e}")
            return False
    
    def run_all_tests(self):
        """Run all LLM tests."""
        print("Starting comprehensive LLM testing...\n")
        
        results = {}
        
        # Test 1: Context sizes
        try:
            self.test_context_sizes()
            results['context_sizes'] = True
        except Exception as e:
            print(f"❌ Context size test failed: {e}")
            results['context_sizes'] = False
        
        # Test 2: Sustained coaching
        try:
            results['sustained_coaching'] = self.test_sustained_coaching()
        except Exception as e:
            print(f"❌ Sustained coaching test failed: {e}")
            results['sustained_coaching'] = False
        
        # Test 3: Memory management
        try:
            results['memory_management'] = self.test_memory_management()
        except Exception as e:
            print(f"❌ Memory management test failed: {e}")
            results['memory_management'] = False
        
        # Summary
        print("\n" + "=" * 50)
        print("LLM STANDALONE TEST RESULTS")
        print("=" * 50)
        
        for test_name, success in results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
        
        overall_success = all(results.values())
        print(f"\nOverall Result: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
        
        if not overall_success:
            print("\nRecommendations:")
            if not results.get('context_sizes'):
                print("- Try reducing LLM context size to 2048 or lower")
            if not results.get('sustained_coaching'):
                print("- Implement LLM restart mechanism for long sessions")
            if not results.get('memory_management'):
                print("- Add more aggressive memory cleanup")
        
        return overall_success

def main():
    tester = StandaloneLLMTest()
    tester.run_all_tests()

if __name__ == "__main__":
    main()