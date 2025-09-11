#!/usr/bin/env python3
"""
Phase 2: Display/CLI Test with Mock Coaching Responses
Test terminal UI without real AI processing to isolate display issues.
"""

import time
import random
from datetime import datetime
from enum import Enum

class MockCoachingPriority(Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class MockCoachingCategory(Enum):
    QUESTIONING = "QUESTIONING"
    LISTENING = "LISTENING"
    OBJECTION_HANDLING = "OBJECTION_HANDLING"
    VALUE_PROPOSITION = "VALUE_PROPOSITION"
    CLOSING = "CLOSING"
    RAPPORT_BUILDING = "RAPPORT_BUILDING"

class MockCoachingAdvice:
    def __init__(self, priority, category, insight, suggested_action):
        self.priority = priority
        self.category = category
        self.insight = insight
        self.suggested_action = suggested_action

class MockDisplayTest:
    def __init__(self):
        print("🎨 DISPLAY/CLI MOCK TEST")
        print("=" * 50)
        
        self.session_start = datetime.now()
        self.chunk_count = 0
        self.transcription_count = 0
        self.coaching_count = 0
        
        # Mock data for testing
        self.mock_transcriptions = [
            "Hello, thanks for joining our call today.",
            "I wanted to discuss our automation tools.",
            "What challenges are you currently facing?",
            "Our solution could save you significant time.",
            "How does your current process work?",
            "I understand that manual data entry is time-consuming.",
            "Let me show you how we can help with that.",
            "What's your timeline for implementing a solution?",
            "I'd like to schedule a follow-up demonstration.",
            "Thank you for your time today."
        ]
        
        self.mock_coaching_responses = [
            MockCoachingAdvice(
                MockCoachingPriority.HIGH,
                MockCoachingCategory.QUESTIONING,
                "Customer hasn't shared specific pain points yet",
                "Ask open-ended questions to uncover their main challenges"
            ),
            MockCoachingAdvice(
                MockCoachingPriority.MEDIUM,
                MockCoachingCategory.LISTENING,
                "Customer is providing valuable information about their process",
                "Listen actively and take notes to reference later"
            ),
            MockCoachingAdvice(
                MockCoachingPriority.HIGH,
                MockCoachingCategory.VALUE_PROPOSITION,
                "Good opportunity to connect your solution to their pain",
                "Clearly explain how your features address their specific needs"
            ),
            MockCoachingAdvice(
                MockCoachingPriority.LOW,
                MockCoachingCategory.RAPPORT_BUILDING,
                "Conversation flow is natural",
                "Continue building rapport while moving toward discovery"
            ),
            MockCoachingAdvice(
                MockCoachingPriority.HIGH,
                MockCoachingCategory.CLOSING,
                "Customer seems interested in next steps",
                "Propose a specific next action with timeline"
            )
        ]
    
    def test_simple_print_output(self):
        """Test basic print-based output without any fancy formatting."""
        print("\n🖨️  Testing Simple Print Output")
        print("-" * 30)
        
        for i in range(5):
            chunk_num = i + 1
            transcription = self.mock_transcriptions[i]
            coaching = self.mock_coaching_responses[i]
            
            # Simulate audio processing delay
            print(f"Chunk #{chunk_num}: Processing audio...")
            time.sleep(0.5)
            
            # Mock transcription
            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f"[{timestamp}] Transcription: \"{transcription}\"")
            
            # Mock coaching
            print(f"COACHING [{coaching.priority.value}] {coaching.category.value}:")
            print(f"  Insight: {coaching.insight}")
            print(f"  Action: {coaching.suggested_action}")
            print("-" * 50)
            
            time.sleep(0.3)
        
        print("✅ Simple print output test completed")
    
    def test_rich_console_output(self):
        """Test Rich console output if available."""
        print("\n🎨 Testing Rich Console Output")
        print("-" * 30)
        
        try:
            from rich.console import Console
            from rich.panel import Panel
            from rich.table import Table
            from rich.text import Text
            
            console = Console()
            
            console.print("✅ Rich library available", style="green")
            
            # Test Rich panels and tables
            for i in range(3):
                chunk_num = i + 1
                transcription = self.mock_transcriptions[i]
                coaching = self.mock_coaching_responses[i]
                
                # Create conversation panel
                conversation_text = Text()
                conversation_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] ", style="dim")
                conversation_text.append(f'"{transcription}"', style="cyan")
                
                conversation_panel = Panel(
                    conversation_text,
                    title=f"Conversation Chunk #{chunk_num}",
                    border_style="blue"
                )
                
                # Create coaching panel
                coaching_text = Text()
                coaching_text.append(f"Priority: {coaching.priority.value}\n", style="bold red" if coaching.priority == MockCoachingPriority.HIGH else "yellow")
                coaching_text.append(f"Category: {coaching.category.value}\n", style="bold")
                coaching_text.append(f"💡 {coaching.insight}\n", style="italic")
                coaching_text.append(f"▶️  {coaching.suggested_action}", style="green")
                
                coaching_panel = Panel(
                    coaching_text,
                    title="AI Coaching",
                    border_style="green"
                )
                
                console.print(conversation_panel)
                console.print(coaching_panel)
                console.print()
                
                time.sleep(0.5)
            
            # Test summary table
            table = Table(title="Session Summary")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="magenta")
            
            table.add_row("Chunks Processed", "3")
            table.add_row("Transcriptions", "3")
            table.add_row("Coaching Responses", "3")
            table.add_row("Session Duration", "45 seconds")
            
            console.print(table)
            
            print("✅ Rich console output test completed")
            return True
            
        except ImportError:
            print("⚠️  Rich library not available, skipping fancy display test")
            return False
        except Exception as e:
            print(f"❌ Rich console test failed: {e}")
            return False
    
    def test_real_time_updates(self):
        """Test real-time display updates."""
        print("\n⏱️  Testing Real-time Updates")
        print("-" * 30)
        
        print("Simulating continuous audio processing...")
        
        for i in range(8):
            chunk_num = i + 1
            
            # Simulate various audio levels
            rms = random.uniform(0.0001, 0.05)
            print(f"🎙️  Chunk #{chunk_num} (3s)... RMS:{rms:.4f}", end="", flush=True)
            
            time.sleep(0.8)  # Simulate audio recording
            
            if rms > 0.001:  # Above threshold
                print(" - Processing...")
                time.sleep(0.3)  # Simulate processing delay
                
                # Random chance of successful transcription
                if random.random() > 0.3:
                    transcription = random.choice(self.mock_transcriptions)
                    print(f"   📝 \"{transcription[:40]}...\"")
                    
                    # Random chance of coaching
                    if random.random() > 0.4:
                        coaching = random.choice(self.mock_coaching_responses)
                        print(f"   🧠 [{coaching.priority.value}] {coaching.category.value}")
                        print(f"      💡 {coaching.insight[:50]}...")
                        self.coaching_count += 1
                    else:
                        print("   🤔 No coaching advice generated")
                    
                    self.transcription_count += 1
                else:
                    print("   🔇 Transcription unclear")
            else:
                print(" - Below threshold")
            
            print()  # Blank line
            self.chunk_count += 1
            
            # Status update every 4 chunks
            if chunk_num % 4 == 0:
                elapsed = (datetime.now() - self.session_start).total_seconds()
                print(f"   📊 Status: {self.transcription_count} transcriptions, {self.coaching_count} coaching ({elapsed:.0f}s)")
                print()
        
        print("✅ Real-time updates test completed")
    
    def test_error_handling_display(self):
        """Test display during error conditions."""
        print("\n⚠️  Testing Error Handling Display")
        print("-" * 30)
        
        error_scenarios = [
            ("LLM timeout", "llama_decode returned -1"),
            ("Memory error", "Out of memory during inference"),
            ("Audio device error", "Failed to initialize audio device"),
            ("Transcription error", "Whisper model failed to load"),
            ("Context overflow", "Token limit exceeded")
        ]
        
        for i, (error_type, error_msg) in enumerate(error_scenarios, 1):
            print(f"Chunk #{i}: Processing audio...")
            time.sleep(0.2)
            
            print(f"   ❌ {error_type}: {error_msg}")
            print(f"   🔄 Attempting recovery...")
            time.sleep(0.3)
            
            # Show recovery or fallback
            if "LLM" in error_type:
                print(f"   💡 Using fallback rule-based coaching")
            elif "Audio" in error_type:
                print(f"   🎙️  Switching to default audio device")
            else:
                print(f"   ✅ System recovered")
            
            print()
        
        print("✅ Error handling display test completed")
    
    def run_all_display_tests(self):
        """Run all display tests."""
        print("Starting comprehensive display testing...\n")
        
        results = {}
        
        # Test 1: Simple print output
        try:
            self.test_simple_print_output()
            results['simple_print'] = True
        except Exception as e:
            print(f"❌ Simple print test failed: {e}")
            results['simple_print'] = False
        
        # Test 2: Rich console output
        try:
            results['rich_console'] = self.test_rich_console_output()
        except Exception as e:
            print(f"❌ Rich console test failed: {e}")
            results['rich_console'] = False
        
        # Test 3: Real-time updates
        try:
            self.test_real_time_updates()
            results['real_time'] = True
        except Exception as e:
            print(f"❌ Real-time updates test failed: {e}")
            results['real_time'] = False
        
        # Test 4: Error handling display
        try:
            self.test_error_handling_display()
            results['error_handling'] = True
        except Exception as e:
            print(f"❌ Error handling display test failed: {e}")
            results['error_handling'] = False
        
        # Summary
        print("\n" + "=" * 50)
        print("DISPLAY/CLI TEST RESULTS")
        print("=" * 50)
        
        for test_name, success in results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
        
        overall_success = sum(results.values()) >= 3  # At least 3/4 tests pass
        print(f"\nOverall Result: {'✅ DISPLAY SYSTEM WORKING' if overall_success else '❌ DISPLAY ISSUES DETECTED'}")
        
        if not overall_success:
            print("\nRecommendations:")
            if not results.get('simple_print'):
                print("- Terminal output has fundamental issues")
            if not results.get('rich_console'):
                print("- Use simple print output instead of Rich console")
            if not results.get('real_time'):
                print("- Check for threading or buffering issues")
            if not results.get('error_handling'):
                print("- Improve error message formatting")
        
        return overall_success

def main():
    tester = MockDisplayTest()
    tester.run_all_display_tests()

if __name__ == "__main__":
    main()