#!/usr/bin/env python3
"""
LLM Test Script - Debug the Phi-3.5-mini model to understand why it's returning empty responses.
"""

import logging
from pathlib import Path
from llama_cpp import Llama

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_model_loading():
    """Test if the model loads correctly."""
    print("=" * 50)
    print("TESTING MODEL LOADING")
    print("=" * 50)
    
    model_path = Path("models_cache/Phi-3.5-mini-instruct-Q4_K_M.gguf")
    
    if not model_path.exists():
        print(f"❌ Model file not found: {model_path}")
        return None
    
    print(f"✅ Model file found: {model_path}")
    print(f"📊 File size: {model_path.stat().st_size / 1024 / 1024:.1f} MB")
    
    try:
        print("Loading model...")
        model = Llama(
            model_path=str(model_path),
            n_ctx=512,  # Small context for testing
            n_threads=2,
            n_gpu_layers=-1,
            use_mmap=True,
            use_mlock=False,
            verbose=True
        )
        print("✅ Model loaded successfully!")
        return model
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        return None

def test_simple_prompts(model):
    """Test with very simple prompts."""
    print("\n" + "=" * 50)
    print("TESTING SIMPLE PROMPTS")
    print("=" * 50)
    
    simple_prompts = [
        "Hello",
        "What is 2+2?",
        "Say yes or no: Is this working?",
        "Complete this sentence: The weather is",
    ]
    
    for i, prompt in enumerate(simple_prompts, 1):
        print(f"\n--- Test {i} ---")
        print(f"Prompt: '{prompt}'")
        
        try:
            response = model(
                prompt,
                max_tokens=20,
                temperature=0.1,
                stop=["\\n"],
                echo=False
            )
            
            response_text = response['choices'][0]['text'].strip()
            print(f"Response: '{response_text}'")
            print(f"Length: {len(response_text)}")
            
            if not response_text:
                print("⚠️  Empty response!")
            else:
                print("✅ Got response!")
                
        except Exception as e:
            print(f"❌ Error: {e}")

def test_sales_coaching_prompts(model):
    """Test sales coaching style prompts."""
    print("\n" + "=" * 50)
    print("TESTING SALES COACHING PROMPTS")  
    print("=" * 50)
    
    # Current complex prompt (simplified)
    complex_prompt = """You are an expert sales coach analyzing a live sales conversation. Provide structured coaching advice.

CONVERSATION CONTEXT:
- Current stage: DISCOVERY
- Talk ratio: 1.5 (balanced)
- Duration: 2.1 minutes
- Total turns: 6

RECENT CONVERSATION:
SALES_REP: Hello, can you hear me now?
UNKNOWN: Great chin second to me and transcribe.

OUTPUT FORMAT (JSON only):
{
    "analysis": {
        "customer_concern": "primary customer concern or null",
        "conversation_stage": "DISCOVERY"
    },
    "primary_advice": {
        "priority": "HIGH",
        "insight": "brief insight",
        "suggested_action": "specific action"
    },
    "confidence": 0.8
}

Return ONLY valid JSON. No additional text or explanation."""

    # Simplified prompt
    simple_prompt = """Analyze this sales conversation:
SALES_REP: Hello, can you hear me now?  
CUSTOMER: Great chin second to me and transcribe.

Give one coaching tip in 20 words or less:"""

    # Very simple prompt
    basic_prompt = """The sales rep said "Hello, can you hear me now?" 
Give coaching advice:"""

    prompts = [
        ("Complex JSON Prompt", complex_prompt),
        ("Simplified Prompt", simple_prompt), 
        ("Basic Prompt", basic_prompt)
    ]
    
    for name, prompt in prompts:
        print(f"\n--- {name} ---")
        print(f"Prompt length: {len(prompt)} chars")
        
        try:
            response = model(
                prompt,
                max_tokens=200,
                temperature=0.3,
                stop=["```", "\\n\\n\\n"],
                echo=False
            )
            
            response_text = response['choices'][0]['text'].strip()
            print(f"Response: '{response_text}'")
            print(f"Length: {len(response_text)}")
            
            if not response_text:
                print("⚠️  Empty response!")
            else:
                print("✅ Got response!")
                
        except Exception as e:
            print(f"❌ Error: {e}")

def test_with_instruction_format(model):
    """Test with proper Phi-3.5 instruction format."""
    print("\n" + "=" * 50)
    print("TESTING PHI-3.5 INSTRUCTION FORMAT")
    print("=" * 50)
    
    # Proper Phi-3.5 format: <|system|>\n<|user|>\n<|assistant|>
    phi_prompt = """<|system|>
You are a helpful sales coach.<|end|>
<|user|>
The sales rep said "Hello, can you hear me now?" to a customer.
Give one short coaching tip.<|end|>
<|assistant|>"""

    print(f"Prompt: '{phi_prompt}'")
    
    try:
        response = model(
            phi_prompt,
            max_tokens=50,
            temperature=0.3,
            stop=["<|end|>", "<|user|>"],
            echo=False
        )
        
        response_text = response['choices'][0]['text'].strip()
        print(f"Response: '{response_text}'")
        print(f"Length: {len(response_text)}")
        
        if not response_text:
            print("⚠️  Empty response!")
        else:
            print("✅ Got response!")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Run all tests."""
    print("🔍 LLM Debugging Script")
    print("Testing Phi-3.5-mini model to diagnose empty responses\n")
    
    # Test 1: Model Loading
    model = test_model_loading()
    if not model:
        print("❌ Cannot proceed without model")
        return
    
    # Test 2: Simple prompts
    test_simple_prompts(model)
    
    # Test 3: Sales coaching prompts
    test_sales_coaching_prompts(model)
    
    # Test 4: Proper instruction format
    test_with_instruction_format(model)
    
    print("\n" + "=" * 50)
    print("TEST COMPLETE")
    print("=" * 50)
    print("If all tests show empty responses, the issue is with:")
    print("1. Model file corruption")
    print("2. Incompatible llama.cpp version") 
    print("3. Wrong model parameters")
    print("4. Context window issues")

if __name__ == "__main__":
    main()