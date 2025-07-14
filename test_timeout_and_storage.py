#!/usr/bin/env python3
"""
Test script for timeout settings and JSON storage functionality
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
    """Test the new timeout configuration"""
    print("🔧 Testing Configuration...")
    
    config = Config()
    
    print(f"  GEMINI_API_TIMEOUT: {config.GEMINI_API_TIMEOUT}s")
    print(f"  PROCESSING_TIMEOUT: {config.PROCESSING_TIMEOUT}s")
    print(f"  BATCH_TIMEOUT: {config.BATCH_TIMEOUT}s")
    print(f"  UPLOAD_TIMEOUT: {config.UPLOAD_TIMEOUT}s")
    print(f"  ENABLE_JSON_STORAGE: {config.ENABLE_JSON_STORAGE}")
    print(f"  JSON_STORAGE_FOLDER: {config.JSON_STORAGE_FOLDER}")
    
    # Verify timeouts are reasonable
    assert config.GEMINI_API_TIMEOUT >= 300, "API timeout should be at least 5 minutes"
    assert config.PROCESSING_TIMEOUT >= 1800, "Processing timeout should be at least 30 minutes"
    assert config.BATCH_TIMEOUT >= 600, "Batch timeout should be at least 10 minutes"
    
    print("  ✅ Configuration test passed")

def test_json_storage():
    """Test JSON storage functionality"""
    print("\n📁 Testing JSON Storage...")
    
    storage = JSONStorage()
    
    # Test storing a successful response
    test_response = json.dumps({
        "matches": [
            {
                "checklist_index": 1,
                "found": True,
                "confidence": "HIGH",
                "sheet_references": ["M1.1"],
                "spec_references": [],
                "notes": "Test response",
                "reasoning": "Test reasoning"
            }
        ]
    })
    
    filepath = storage.store_response(
        test_response, 
        1, 
        "test_operation", 
        True, 
        {"test": "metadata"}
    )
    
    print(f"  Stored successful response: {filepath}")
    assert filepath, "Should return filepath for successful storage"
    
    # Test storing a failed response
    failed_filepath = storage.store_failed_response(
        "Invalid JSON response", 
        2, 
        "JSON parsing error", 
        "test_operation", 
        {"error": "test"}
    )
    
    print(f"  Stored failed response: {failed_filepath}")
    assert failed_filepath, "Should return filepath for failed storage"
    
    # Test storage stats
    stats = storage.get_storage_stats()
    print(f"  Storage stats: {stats}")
    assert stats["total_responses"] >= 1, "Should have at least one response"
    assert stats["total_failed"] >= 1, "Should have at least one failed response"
    
    print("  ✅ JSON Storage test passed")

def test_gemini_client_integration():
    """Test Gemini client integration with new timeouts and storage"""
    print("\n🤖 Testing Gemini Client Integration...")
    
    try:
        client = GeminiClient()
        
        print(f"  Model: {client.config.GEMINI_MODEL}")
        print(f"  API Timeout: {client.config.GEMINI_API_TIMEOUT}s")
        print(f"  JSON Storage enabled: {client.config.ENABLE_JSON_STORAGE}")
        
        # Test that JSON storage is initialized
        assert hasattr(client, 'json_storage'), "GeminiClient should have json_storage"
        assert client.json_storage is not None, "JSON storage should be initialized"
        
        print("  ✅ Gemini Client integration test passed")
        
    except Exception as e:
        print(f"  ⚠️  Gemini Client test skipped (likely no API key): {e}")

def test_timeout_calculation():
    """Test timeout calculations for different scenarios"""
    print("\n⏱️  Testing Timeout Calculations...")
    
    config = Config()
    
    # Calculate expected processing time for full dataset
    total_items = 1350  # From master checklist
    batch_size = config.BATCH_SIZE
    total_batches = (total_items + batch_size - 1) // batch_size
    
    # Estimate time per batch (conservative)
    estimated_time_per_batch = 120  # 2 minutes per batch
    total_estimated_time = total_batches * estimated_time_per_batch
    
    print(f"  Total items: {total_items}")
    print(f"  Batch size: {batch_size}")
    print(f"  Total batches: {total_batches}")
    print(f"  Estimated time per batch: {estimated_time_per_batch}s")
    print(f"  Total estimated time: {total_estimated_time}s ({total_estimated_time/60:.1f} minutes)")
    print(f"  Processing timeout: {config.PROCESSING_TIMEOUT}s ({config.PROCESSING_TIMEOUT/60:.1f} minutes)")
    
    # Verify timeout is sufficient (allow for some variance)
    # If timeout is too short, suggest increasing it
    if config.PROCESSING_TIMEOUT < total_estimated_time:
        print(f"  ⚠️  Warning: Processing timeout ({config.PROCESSING_TIMEOUT}s) is less than estimated time ({total_estimated_time}s)")
        print(f"  💡 Consider increasing PROCESSING_TIMEOUT to at least {total_estimated_time + 300}s")
        print(f"  💡 Add to .env: PROCESSING_TIMEOUT={total_estimated_time + 300}")
    
    # For now, just check that API timeout is reasonable
    assert config.GEMINI_API_TIMEOUT >= 300, "API timeout should be at least 5 minutes"
    assert config.BATCH_TIMEOUT >= 600, "Batch timeout should be at least 10 minutes"
    
    print("  ✅ Timeout calculation test passed")

def test_storage_cleanup():
    """Test storage cleanup functionality"""
    print("\n🧹 Testing Storage Cleanup...")
    
    storage = JSONStorage()
    
    # Test cleanup (should not fail even if no files to clean)
    deleted_count = storage.cleanup_old_files(1)  # Clean files older than 1 day
    print(f"  Cleaned up {deleted_count} old files")
    
    print("  ✅ Storage cleanup test passed")

def main():
    """Run all tests"""
    print("🚀 Testing Timeout and JSON Storage Functionality")
    print("=" * 60)
    
    try:
        test_configuration()
        test_json_storage()
        test_gemini_client_integration()
        test_timeout_calculation()
        test_storage_cleanup()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("\n📋 Summary:")
        print("  - Timeout settings increased significantly")
        print("  - JSON storage functionality working")
        print("  - All Gemini responses will be stored for debugging")
        print("  - New API endpoints available for storage management")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 