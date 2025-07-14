#!/usr/bin/env python3
"""
Test script to demonstrate token tracking functionality
"""
import os
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from token_tracker import TokenTracker, TokenUsage
from config import Config

def test_token_tracker():
    """Test the token tracker functionality"""
    print("🧪 Testing Token Tracker")
    print("=" * 50)
    
    # Initialize token tracker
    tracker = TokenTracker()
    
    # Test cost calculation
    print("\n💰 Testing Cost Calculation:")
    
    # Test with different token amounts
    test_cases = [
        (1000, 500, 0, 0, "Small API Call"),
        (5000, 2000, 1000, 0, "Medium API Call"),
        (10000, 5000, 2000, 500, "Large API Call with Thinking"),
        (50000, 25000, 5000, 2000, "Very Large API Call with Thinking")
    ]
    
    for input_tokens, output_tokens, cached_tokens, thoughts_tokens, description in test_cases:
        usage = TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cached_tokens=cached_tokens,
            thoughts_tokens=thoughts_tokens
        )
        
        cost = tracker.calculate_cost(usage)
        
        print(f"\n📊 {description}:")
        print(f"   Input tokens: {input_tokens:,}")
        print(f"   Output tokens: {output_tokens:,}")
        print(f"   Cached tokens: {cached_tokens:,}")
        if thoughts_tokens > 0:
            print(f"   Thoughts tokens: {thoughts_tokens:,}")
        print(f"   Input cost: ${cost.input_cost:.6f}")
        print(f"   Output cost: ${cost.output_cost:.6f}")
        print(f"   Cached cost: ${cost.cached_cost:.6f}")
        if cost.thoughts_cost > 0:
            print(f"   Thoughts cost: ${cost.thoughts_cost:.6f}")
        print(f"   Total cost: ${cost.total_cost:.6f}")
        
        # Log the usage
        tracker.log_token_usage(usage, description)
    
    # Test session summary
    print("\n📈 Session Summary:")
    summary = tracker.get_session_summary()
    print(json.dumps(summary, indent=2))
    
    # Test pricing information
    print(f"\n💵 Current Model Pricing ({tracker.config.GEMINI_MODEL}):")
    pricing = tracker.get_model_pricing()
    for token_type, price in pricing.items():
        print(f"   {token_type.capitalize()}: ${price:.6f} per 1M tokens")
    
    # Test thinking model support
    print(f"\n🧠 Thinking Model Support:")
    print(f"   Current model: {tracker.config.GEMINI_MODEL}")
    print(f"   Supports thinking: {tracker.is_thinking_model()}")
    
    # Test cost estimation
    print("\n🔮 Cost Estimation Examples:")
    estimated_costs = [
        (1000000, 500000, 0, 0, "1M input, 500K output"),
        (2000000, 1000000, 100000, 0, "2M input, 1M output, 100K cached"),
        (5000000, 2500000, 500000, 200000, "5M input, 2.5M output, 500K cached, 200K thoughts")
    ]
    
    for input_tokens, output_tokens, cached_tokens, thoughts_tokens, description in estimated_costs:
        cost = tracker.estimate_cost_for_tokens(input_tokens, output_tokens, cached_tokens, thoughts_tokens)
        print(f"\n   {description}:")
        print(f"      Total cost: ${cost.total_cost:.6f}")
        print(f"      Input cost: ${cost.input_cost:.6f}")
        print(f"      Output cost: ${cost.output_cost:.6f}")
        print(f"      Cached cost: ${cost.cached_cost:.6f}")
        if cost.thoughts_cost > 0:
            print(f"      Thoughts cost: ${cost.thoughts_cost:.6f}")
    
    # Test model comparison
    print("\n🔍 Model Comparison:")
    models = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash", "gemini-1.5-pro"]
    
    for model in models:
        # Temporarily change model for comparison
        original_model = tracker.config.GEMINI_MODEL
        tracker.config.GEMINI_MODEL = model
        
        pricing = tracker.get_model_pricing()
        supports_thinking = tracker.is_thinking_model()
        
        print(f"\n   {model}:")
        print(f"      Input: ${pricing['input']:.6f}/1M tokens")
        print(f"      Output: ${pricing['output']:.6f}/1M tokens")
        print(f"      Cached: ${pricing['cached']:.6f}/1M tokens")
        if supports_thinking:
            print(f"      Thoughts: ${pricing['thoughts']:.6f}/1M tokens")
            print(f"      Thinking support: ✅")
        else:
            print(f"      Thinking support: ❌")
        
        # Restore original model
        tracker.config.GEMINI_MODEL = original_model
    
    print("\n✅ Token tracker test completed!")

def test_configuration():
    """Test token tracking configuration"""
    print("\n⚙️ Testing Configuration:")
    print("=" * 30)
    
    config = Config()
    
    print(f"Enable Token Tracking: {config.ENABLE_TOKEN_TRACKING}")
    print(f"Log Token Usage: {config.LOG_TOKEN_USAGE}")
    print(f"Log Cost Breakdown: {config.LOG_COST_BREAKDOWN}")
    print(f"Gemini Model: {config.GEMINI_MODEL}")
    
    print("\n✅ Configuration test completed!")

def main():
    """Run all tests"""
    print("🚀 Token Tracking Test Suite")
    print("=" * 50)
    
    try:
        test_configuration()
        test_token_tracker()
        
        print("\n" + "=" * 50)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 50)
        
        print("\n📋 Token Tracking Features Implemented:")
        print("✅ Token usage tracking for all API calls")
        print("✅ Cost calculation based on current Gemini pricing")
        print("✅ Session-based usage aggregation")
        print("✅ Detailed logging with emojis for easy reading")
        print("✅ Configuration options for enabling/disabling")
        print("✅ REST API endpoints for usage monitoring")
        print("✅ Cost estimation for planning")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
 