#!/usr/bin/env python3
"""
Debug script for Phase 4 tests
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

try:
    from output_generator import OutputGenerator, ChecklistItem, FinalOutput
    from config import Config
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

def test_checklist_item_debug():
    """Debug checklist item formatting"""
    print("=== DEBUG: Checklist Item Formatting ===")
    
    try:
        generator = OutputGenerator()
        print("✓ OutputGenerator created")
        
        # Test valid item
        raw_item = {
            "item_id": "TEST-001",
            "category": "Structural",
            "description": "Concrete foundation requirements",
            "found": True,
            "confidence_score": 0.85,
            "sheet_references": ["A-101", "A-102"],
            "sheet_reasoning": "Found in foundation plan drawings A-101 and A-102 showing concrete specifications",
            "spec_references": ["03 30 00", "03 31 00"],
            "spec_reasoning": "Referenced in concrete specifications sections 03 30 00 and 03 31 00",
            "notes": "Found in foundation plans",
            "processing_time": 2.5
        }
        
        print("Raw item:", raw_item)
        formatted_item = generator.format_checklist_item(raw_item)
        print("Formatted item:", formatted_item)
        print("Type:", type(formatted_item))
        
        # Test error handling
        print("\n--- Testing error handling ---")
        invalid_item = {"item_id": "INVALID"}
        formatted_invalid = generator.format_checklist_item(invalid_item)
        print("Invalid formatted item:", formatted_invalid)
        
        print("✅ Checklist item debug completed")
        return True
        
    except Exception as e:
        print(f"❌ Checklist item debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_final_output_debug():
    """Debug final output compilation"""
    print("\n=== DEBUG: Final Output Compilation ===")
    
    try:
        generator = OutputGenerator()
        print("✓ OutputGenerator created")
        
        # Create a tracker
        process_id = "test-compilation-123"
        tracker_id = generator.create_progress_tracker(process_id, 3, 150)
        print(f"✓ Tracker created: {tracker_id}")
        
        # Simulate some progress
        batch_results = [
            {"item_id": "1", "found": True, "confidence_score": 0.8},
            {"item_id": "2", "found": False, "confidence_score": 0.3}
        ]
        generator.update_progress(tracker_id, 0, batch_results, "processing")
        generator.update_progress(tracker_id, 1, batch_results, "processing")
        generator.update_progress(tracker_id, 2, batch_results, "completed")
        print("✓ Progress updates completed")
        
        # Raw results
        raw_results = {
            "upload_id": "upload-123",
            "checklist_results": [
                {
                    "item_id": "1", 
                    "category": "Structural", 
                    "found": True, 
                    "confidence_score": 0.8,
                    "sheet_references": ["A-101"],
                    "sheet_reasoning": "Found in structural drawing A-101",
                    "spec_references": ["03 30 00"],
                    "spec_reasoning": "Referenced in concrete specifications"
                },
                {
                    "item_id": "2", 
                    "category": "Mechanical", 
                    "found": False, 
                    "confidence_score": 0.3,
                    "sheet_references": [],
                    "sheet_reasoning": "No mechanical drawings found",
                    "spec_references": [],
                    "spec_reasoning": "No mechanical specifications found"
                },
                {
                    "item_id": "3", 
                    "category": "Electrical", 
                    "found": True, 
                    "confidence_score": 0.9,
                    "sheet_references": ["E-101"],
                    "sheet_reasoning": "Found in electrical drawing E-101",
                    "spec_references": ["26 00 00"],
                    "spec_reasoning": "Referenced in electrical specifications"
                }
            ]
        }
        
        # Document info
        document_info = [
            {
                "type": "drawing",
                "filename": "A-101.pdf",
                "file_size": 1024000,
                "upload_timestamp": "2024-01-15T10:30:00"
            },
            {
                "type": "specification",
                "filename": "Specs.pdf",
                "file_size": 2048000,
                "upload_timestamp": "2024-01-15T10:35:00"
            }
        ]
        
        print("Raw results:", raw_results)
        print("Document info:", document_info)
        
        # Compile final output
        final_output = generator.compile_final_output(process_id, tracker_id, raw_results, document_info)
        print("Final output:", final_output)
        print("Type:", type(final_output))
        
        print("✅ Final output debug completed")
        return True
        
    except Exception as e:
        print(f"❌ Final output debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting Phase 4 Debug Tests...")
    
    # Validate configuration
    try:
        Config.validate_config()
        print("✅ Configuration validated")
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)
    
    # Run debug tests
    test1 = test_checklist_item_debug()
    test2 = test_final_output_debug()
    
    print(f"\nDebug Results: Checklist={test1}, Final Output={test2}") 