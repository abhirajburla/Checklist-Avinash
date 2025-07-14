#!/usr/bin/env python3
"""
Test script to demonstrate JSON combiner functionality
"""
import os
import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from json_combiner import JSONCombiner
from config import Config

def create_test_json_files():
    """Create test JSON files for demonstration"""
    config = Config()
    json_storage = Path(config.JSON_STORAGE_FOLDER)
    
    # Create directories
    responses_dir = json_storage / "responses"
    failed_dir = json_storage / "failed"
    responses_dir.mkdir(parents=True, exist_ok=True)
    failed_dir.mkdir(parents=True, exist_ok=True)
    
    session_id = "test_session_123"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create successful response files
    successful_responses = [
        {
            "batch_number": 0,
            "results": [
                {
                    "row_id": 1,
                    "category": "Pre-Bid",
                    "scope_of_work": "02 40 00 Demolition",
                    "checklist": "Backfill any remaining holes with approved structural fill",
                    "found": True,
                    "sheet_number": "S-01",
                    "spec_section": "02 40 00",
                    "confidence": "HIGH"
                }
            ],
            "token_usage": {
                "input_tokens": 15000,
                "output_tokens": 8000,
                "cached_tokens": 2000,
                "thoughts_tokens": 500,
                "total_cost": 0.0038
            },
            "response_time": 45.2
        },
        {
            "batch_number": 1,
            "results": [
                {
                    "row_id": 2,
                    "category": "Pre-Bid",
                    "scope_of_work": "03 20 00 Concrete",
                    "checklist": "Verify concrete mix design",
                    "found": False,
                    "sheet_number": "",
                    "spec_section": "",
                    "confidence": "LOW"
                }
            ],
            "token_usage": {
                "input_tokens": 12000,
                "output_tokens": 6000,
                "cached_tokens": 1500,
                "thoughts_tokens": 300,
                "total_cost": 0.0029
            },
            "response_time": 38.7
        }
    ]
    
    # Create failed response files
    failed_responses = [
        {
            "batch_number": 2,
            "error_type": "timeout",
            "error_message": "Request timed out after 300 seconds",
            "attempted_items": [
                {
                    "row_id": 3,
                    "category": "Pre-Bid",
                    "scope_of_work": "04 20 00 Masonry",
                    "checklist": "Verify masonry units"
                }
            ]
        }
    ]
    
    # Save successful responses
    for i, response in enumerate(successful_responses):
        filename = f"checklist_matching_batch_{i:03d}_session_{session_id}_{timestamp}.json"
        file_path = responses_dir / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(response, f, indent=2)
        
        print(f"Created successful response: {file_path}")
    
    # Save failed responses
    for i, response in enumerate(failed_responses):
        filename = f"failed_checklist_matching_batch_{i:03d}_session_{session_id}_{timestamp}.json"
        file_path = failed_dir / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(response, f, indent=2)
        
        print(f"Created failed response: {file_path}")
    
    return session_id

def test_json_combiner():
    """Test the JSON combiner functionality"""
    print("🧪 Testing JSON Combiner")
    print("=" * 50)
    
    # Create test files
    print("\n📁 Creating test JSON files...")
    session_id = create_test_json_files()
    process_id = "test_process_456"
    
    # Initialize JSON combiner
    print("\n🔧 Initializing JSON Combiner...")
    combiner = JSONCombiner()
    
    # Test combining JSON outputs
    print(f"\n🔄 Combining JSON outputs for session: {session_id}, process: {process_id}")
    combined_data = combiner.combine_all_json_outputs(session_id, process_id)
    
    # Display combined data structure
    print("\n📊 Combined Data Structure:")
    print(f"   Metadata:")
    print(f"     Session ID: {combined_data['metadata']['session_id']}")
    print(f"     Process ID: {combined_data['metadata']['process_id']}")
    print(f"     Combined at: {combined_data['metadata']['combined_at']}")
    print(f"     Total responses: {combined_data['metadata']['total_responses']}")
    print(f"     Successful responses: {combined_data['metadata']['successful_responses']}")
    print(f"     Failed responses: {combined_data['metadata']['failed_responses']}")
    print(f"     Total batches: {combined_data['metadata']['total_batches']}")
    
    print(f"\n   Summary:")
    print(f"     Total tokens used: {combined_data['summary']['total_tokens_used']:,}")
    print(f"     Total cost: ${combined_data['summary']['total_cost']:.6f}")
    print(f"     Average response time: {combined_data['summary']['average_response_time']:.2f}s")
    print(f"     Success rate: {combined_data['summary']['success_rate']:.2f}%")
    
    print(f"\n   Successful responses: {len(combined_data['successful_responses'])}")
    print(f"   Failed responses: {len(combined_data['failed_responses'])}")
    
    # Test saving combined JSON
    print(f"\n💾 Saving combined JSON...")
    combined_file_path = combiner.save_combined_json(combined_data, session_id, process_id)
    print(f"   Saved to: {combined_file_path}")
    
    # Test getting combined JSON path
    print(f"\n🔍 Testing path retrieval...")
    retrieved_path = combiner.get_combined_json_path(session_id, process_id)
    print(f"   Retrieved path: {retrieved_path}")
    print(f"   Paths match: {combined_file_path == retrieved_path}")
    
    # Test batch info extraction
    print(f"\n📋 Testing batch info extraction...")
    test_filename = "checklist_matching_batch_000_session_test_123_20250714_140241.json"
    batch_info = combiner._extract_batch_info(test_filename)
    print(f"   Filename: {test_filename}")
    print(f"   Batch number: {batch_info.get('batch_number')}")
    print(f"   Timestamp: {batch_info.get('timestamp')}")
    
    # Test cleanup
    print(f"\n🧹 Testing cleanup...")
    deleted_count = combiner.cleanup_old_combined_files(max_age_hours=0)  # Clean up immediately
    print(f"   Deleted {deleted_count} old files")
    
    print("\n✅ JSON combiner test completed!")

def test_enhanced_batch_processor_integration():
    """Test integration with enhanced batch processor"""
    print("\n🔗 Testing Enhanced Batch Processor Integration")
    print("=" * 50)
    
    try:
        from enhanced_batch_processor import EnhancedBatchProcessor
        from gemini_client import GeminiClient
        
        # Initialize components
        config = Config()
        gemini_client = GeminiClient()
        enhanced_processor = EnhancedBatchProcessor(gemini_client, config)
        
        # Test combined JSON creation
        session_id = "test_session_789"
        process_id = "test_process_999"
        
        print(f"Testing combined JSON creation for session: {session_id}, process: {process_id}")
        
        # This will create the combined JSON
        combined_file_path = enhanced_processor.create_combined_json(session_id, process_id)
        print(f"Combined JSON created: {combined_file_path}")
        
        # Test path retrieval
        retrieved_path = enhanced_processor.get_combined_json_path(session_id, process_id)
        print(f"Retrieved path: {retrieved_path}")
        
        print("✅ Enhanced batch processor integration test completed!")
        
    except Exception as e:
        print(f"❌ Enhanced batch processor integration test failed: {e}")

if __name__ == "__main__":
    test_json_combiner()
    test_enhanced_batch_processor_integration() 