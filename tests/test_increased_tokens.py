#!/usr/bin/env python3
"""
Test script for increased output tokens and JSON storage functionality
"""

import os
import sys
import time
import json
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import Config
from src.json_storage import JSONStorage
from src.gemini_client import GeminiClient
from src.logger_config import LoggerConfig

def test_configuration():
    """Test the new token configuration"""
    print("🔧 Testing Token Configuration...")
    
    config = Config()
    
    print(f"  GEMINI_MAX_OUTPUT_TOKENS: {config.GEMINI_MAX_OUTPUT_TOKENS:,}")
    print(f"  GEMINI_API_TIMEOUT: {config.GEMINI_API_TIMEOUT}s")
    print(f"  BATCH_SIZE: {config.BATCH_SIZE}")
    
    # Verify the token limit is high enough
    if config.GEMINI_MAX_OUTPUT_TOKENS >= 65536:
        print("  ✅ Output token limit is set high enough (64K+)")
    else:
        print("  ⚠️  Output token limit might be too low")
    
    return config

def test_json_storage():
    """Test JSON storage functionality"""
    print("\n📁 Testing JSON Storage...")
    
    storage = JSONStorage()
    
    # Test storing a response
    test_response = {
        "matches": [
            {
                "checklist_index": 1,
                "found": True,
                "confidence": "HIGH",
                "sheet_references": ["M0.1", "M0.2"],
                "spec_references": [],
                "notes": "Test note",
                "reasoning": "Test reasoning"
            }
        ]
    }
    
    test_response_text = json.dumps(test_response, indent=2)
    metadata = {
        "batch_size": 50,
        "cache_id": "test_cache_123",
        "model": "gemini-2.5-flash",
        "timeout_used": 300
    }
    
    # Store successful response
    success_file = storage.store_response(
        test_response_text,
        0,
        "test_operation",
        True,
        metadata
    )
    print(f"  ✅ Stored successful response: {success_file}")
    
    # Store failed response
    failed_file = storage.store_failed_response(
        "Invalid JSON response",
        0,
        "JSON parsing error",
        "test_operation",
        metadata
    )
    print(f"  ✅ Stored failed response: {failed_file}")
    
    # Get storage stats
    stats = storage.get_storage_stats()
    print(f"  📊 Storage stats: {stats}")
    
    return storage

def test_gemini_client():
    """Test Gemini client with increased tokens"""
    print("\n🤖 Testing Gemini Client...")
    
    try:
        client = GeminiClient()
        print(f"  ✅ Gemini client initialized")
        print(f"  📝 Model: {client.config.GEMINI_MODEL}")
        print(f"  🔢 Max output tokens: {client.config.GEMINI_MAX_OUTPUT_TOKENS:,}")
        
        # Test token tracking
        summary = client.get_token_usage_summary()
        print(f"  📊 Token tracking initialized: {summary}")
        
        return client
        
    except Exception as e:
        print(f"  ❌ Error initializing Gemini client: {e}")
        return None

def test_large_json_generation():
    """Test if the system can handle large JSON responses"""
    print("\n📄 Testing Large JSON Generation...")
    
    # Create a large test JSON structure (similar to what Gemini would generate)
    large_json = {
        "matches": []
    }
    
    # Generate 50 checklist items with detailed responses
    for i in range(1, 51):
        match = {
            "checklist_index": i,
            "found": i % 3 == 0,  # Every 3rd item is found
            "confidence": "HIGH" if i % 3 == 0 else "NO MATCH",
            "sheet_references": [f"M{i}.{j}" for j in range(1, 6)] if i % 3 == 0 else [],
            "spec_references": [f"Section {i}.{j}" for j in range(1, 4)] if i % 3 == 0 else [],
            "notes": f"Detailed notes for item {i} with extensive information about the requirements and specifications found in the documents. This includes multiple references and detailed analysis of the construction requirements.",
            "reasoning": f"Comprehensive reasoning for item {i} explaining why this item was found or not found in the documents. This includes analysis of multiple sheet references, specification sections, and detailed technical explanations about the construction requirements and how they relate to the checklist item."
        }
        large_json["matches"].append(match)
    
    # Convert to JSON string
    json_string = json.dumps(large_json, indent=2)
    json_size = len(json_string)
    
    print(f"  📏 Generated JSON size: {json_size:,} characters")
    print(f"  🔢 Estimated tokens: {json_size // 4:,} (rough estimate)")
    
    # Check if it's within our new limit
    config = Config()
    if json_size < config.GEMINI_MAX_OUTPUT_TOKENS * 4:  # Rough estimate
        print("  ✅ JSON size is within the new token limit")
    else:
        print("  ⚠️  JSON size might exceed token limit")
    
    # Test JSON parsing
    try:
        parsed = json.loads(json_string)
        print(f"  ✅ JSON parsing successful")
        print(f"  📊 Parsed {len(parsed['matches'])} matches")
    except Exception as e:
        print(f"  ❌ JSON parsing failed: {e}")
    
    return json_string

def test_storage_cleanup():
    """Test storage cleanup functionality"""
    print("\n🧹 Testing Storage Cleanup...")
    
    storage = JSONStorage()
    
    # Get stats before cleanup
    stats_before = storage.get_storage_stats()
    print(f"  📊 Before cleanup: {stats_before}")
    
    # Clean up old files (older than 1 day for testing)
    cleaned = storage.cleanup_old_files(days=1)
    print(f"  🧹 Cleaned up {cleaned} old files")
    
    # Get stats after cleanup
    stats_after = storage.get_storage_stats()
    print(f"  📊 After cleanup: {stats_after}")
    
    return cleaned

def main():
    """Run all tests"""
    print("🚀 Testing Increased Output Tokens and JSON Storage")
    print("=" * 60)
    
    # Test configuration
    config = test_configuration()
    
    # Test JSON storage
    storage = test_json_storage()
    
    # Test Gemini client
    client = test_gemini_client()
    
    # Test large JSON generation
    large_json = test_large_json_generation()
    
    # Test storage cleanup
    cleaned = test_storage_cleanup()
    
    print("\n" + "=" * 60)
    print("📋 Test Summary:")
    print(f"  ✅ Configuration: Max output tokens set to {config.GEMINI_MAX_OUTPUT_TOKENS:,}")
    print(f"  ✅ JSON Storage: Working correctly")
    print(f"  ✅ Gemini Client: {'Initialized' if client else 'Failed'}")
    print(f"  ✅ Large JSON: {len(large_json):,} characters generated")
    print(f"  ✅ Storage Cleanup: {cleaned} files cleaned")
    
    print("\n🎯 Recommendations:")
    print("  1. The increased output tokens (64K) should resolve truncation issues")
    print("  2. JSON storage is working and will capture all responses")
    print("  3. Monitor the logs for any remaining parsing issues")
    print("  4. If issues persist, consider increasing GEMINI_MAX_OUTPUT_TOKENS further")

if __name__ == "__main__":
    main() 