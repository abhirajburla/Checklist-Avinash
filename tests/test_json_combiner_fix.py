#!/usr/bin/env python3
"""
Test script to verify JSON combiner fix
"""

import sys
import os
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from json_combiner import JSONCombiner

def test_json_combiner_fix():
    """Test that the JSON combiner can find and combine files correctly"""
    print("🔍 Testing JSON Combiner Fix...")
    
    # Create JSON combiner instance
    combiner = JSONCombiner()
    
    # Test with the actual session ID from the logs
    session_id = "4e0f2957-82e6-404b-9967-5ee05be024de"
    process_id = "97226ef2-8f72-42ce-9b9b-5fa6dc809053"
    
    print(f"Session ID: {session_id}")
    print(f"Process ID: {process_id}")
    
    # Check if response files exist
    responses_dir = Path(combiner.json_storage) / "responses"
    failed_dir = Path(combiner.json_storage) / "failed"
    
    print(f"\n📁 Checking response directories:")
    print(f"Responses directory: {responses_dir}")
    print(f"Failed directory: {failed_dir}")
    
    if responses_dir.exists():
        all_response_files = list(responses_dir.glob("*.json"))
        print(f"Total response files found: {len(all_response_files)}")
        
        # Check which files would match our session ID
        matching_files = []
        for file_path in all_response_files:
            if session_id in file_path.name or f"session_{session_id}" in file_path.name:
                matching_files.append(file_path)
        
        print(f"Files matching session ID: {len(matching_files)}")
        
        if matching_files:
            print("Matching files:")
            for file_path in matching_files[:5]:  # Show first 5
                print(f"  - {file_path.name}")
            if len(matching_files) > 5:
                print(f"  ... and {len(matching_files) - 5} more")
        else:
            print("No files match the session ID pattern")
            
            # Show some example files to understand the pattern
            print("\nExample files in responses directory:")
            for file_path in all_response_files[:3]:
                print(f"  - {file_path.name}")
    
    if failed_dir.exists():
        all_failed_files = list(failed_dir.glob("*.json"))
        print(f"Total failed files found: {len(all_failed_files)}")
    
    # Try to combine JSON outputs
    print(f"\n🔄 Testing JSON combination...")
    try:
        combined_data = combiner.combine_all_json_outputs(session_id, process_id)
        
        print(f"✅ JSON combination successful!")
        print(f"Total responses: {combined_data['metadata']['total_responses']}")
        print(f"Successful responses: {combined_data['metadata']['successful_responses']}")
        print(f"Failed responses: {combined_data['metadata']['failed_responses']}")
        print(f"Success rate: {combined_data['summary']['success_rate']:.2f}%")
        print(f"Total tokens used: {combined_data['summary']['total_tokens_used']:,}")
        print(f"Total cost: ${combined_data['summary']['total_cost']:.6f}")
        
        # Save the combined JSON
        combined_file_path = combiner.save_combined_json(combined_data, session_id, process_id)
        print(f"Combined JSON saved to: {combined_file_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ JSON combination failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def test_batch_info_extraction():
    """Test batch info extraction from filenames"""
    print("\n🔍 Testing Batch Info Extraction...")
    
    combiner = JSONCombiner()
    
    # Test with actual filename patterns
    test_filenames = [
        "checklist_matching_batch_000_20250714_155535_session_1752488735.json",
        "checklist_matching_batch_001_20250714_155620_session_1752488780.json",
        "failed_checklist_matching_batch_005_20250714_160009_session_1752489009.json"
    ]
    
    for filename in test_filenames:
        batch_info = combiner._extract_batch_info(filename)
        print(f"Filename: {filename}")
        print(f"  Batch number: {batch_info.get('batch_number')}")
        print(f"  Timestamp: {batch_info.get('timestamp')}")
        print()

if __name__ == "__main__":
    print("🚀 Starting JSON Combiner Fix Test")
    print("=" * 50)
    
    # Test batch info extraction
    test_batch_info_extraction()
    
    # Test JSON combination
    success = test_json_combiner_fix()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All tests passed! JSON combiner fix is working correctly.")
    else:
        print("❌ Tests failed. JSON combiner fix needs more work.")
    
    print("\n🎯 Next steps:")
    print("1. If tests passed, the combined JSON should now work correctly")
    print("2. You can download the combined JSON from the /download endpoint")
    print("3. The combined JSON will contain all successful and failed responses") 