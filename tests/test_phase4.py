#!/usr/bin/env python3
"""
Phase 4 Test Suite - Output Generation and Progress Tracking
Tests JSON formatting, progress tracking, status updates, and download functionality
"""

import sys
import os
import json
import time
import tempfile
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

try:
    from output_generator import OutputGenerator, ProcessingStatus, ProgressUpdate, ChecklistItem, DocumentReference, ProcessingMetadata, FinalOutput
    from config import Config
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

def test_output_generator_initialization():
    """Test OutputGenerator initialization"""
    print("Testing OutputGenerator initialization...")
    
    try:
        generator = OutputGenerator()
        assert generator is not None
        assert hasattr(generator, 'progress_trackers')
        assert hasattr(generator, 'output_cache')
        assert hasattr(generator, 'config')
        
        # Check if results directory was created
        results_dir = Path(Config.RESULTS_FOLDER)
        assert results_dir.exists()
        
        print("✅ OutputGenerator initialization passed")
        return True
    except Exception as e:
        print(f"❌ OutputGenerator initialization failed: {e}")
        return False

def test_progress_tracker_creation():
    """Test progress tracker creation"""
    print("Testing progress tracker creation...")
    
    try:
        generator = OutputGenerator()
        
        # Create a progress tracker
        process_id = "test-process-123"
        total_batches = 5
        total_items = 250
        
        tracker_id = generator.create_progress_tracker(process_id, total_batches, total_items)
        
        assert tracker_id is not None
        assert len(tracker_id) > 0
        assert tracker_id in generator.progress_trackers
        
        tracker = generator.progress_trackers[tracker_id]
        assert tracker["process_id"] == process_id
        assert tracker["total_batches"] == total_batches
        assert tracker["total_items"] == total_items
        assert tracker["status"] == ProcessingStatus.PENDING.value
        assert tracker["current_batch"] == 0
        assert tracker["items_processed"] == 0
        
        print("✅ Progress tracker creation passed")
        return tracker_id
    except Exception as e:
        print(f"❌ Progress tracker creation failed: {e}")
        return None

def test_progress_updates():
    """Test progress updates"""
    print("Testing progress updates...")
    
    try:
        generator = OutputGenerator()
        
        # Create a progress tracker directly in this test
        process_id = "test-progress-123"
        total_batches = 5
        total_items = 250
        
        tracker_id = generator.create_progress_tracker(process_id, total_batches, total_items)
        
        if not tracker_id:
            return False
        
        # Simulate batch results
        batch_results = [
            {"item_id": "1", "found": True, "confidence_score": 0.8},
            {"item_id": "2", "found": False, "confidence_score": 0.3},
            {"item_id": "3", "found": True, "confidence_score": 0.9}
        ]
        
        # Update progress
        success = generator.update_progress(tracker_id, 0, batch_results, "processing")
        assert success == True
        
        # Check progress
        progress = generator.get_progress(tracker_id)
        assert progress is not None
        assert progress["current_batch"] == 1
        assert progress["items_processed"] == 3
        assert progress["found_items"] == 2
        assert progress["not_found_items"] == 1
        assert progress["progress_percentage"] == 20.0  # 1/5 batches
        
        # Test error update
        success = generator.update_progress(tracker_id, 1, [], "failed", "Test error")
        assert success == True
        
        progress = generator.get_progress(tracker_id)
        assert progress["status"] == "failed"
        assert progress["error"] == "Test error"
        
        print("✅ Progress updates passed")
        return True
    except Exception as e:
        print(f"❌ Progress updates failed: {e}")
        return False

def test_checklist_item_formatting():
    """Test checklist item formatting"""
    print("Testing checklist item formatting...")
    
    try:
        generator = OutputGenerator()
        
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
        
        formatted_item = generator.format_checklist_item(raw_item)
        print("Formatted item:", formatted_item)
        print("Type:", type(formatted_item))
        print("ChecklistItem type:", ChecklistItem)
        
        assert isinstance(formatted_item, ChecklistItem), f"Type mismatch: {type(formatted_item)} != {ChecklistItem}"
        assert formatted_item.item_id == "TEST-001"
        assert formatted_item.category == "Structural"
        assert formatted_item.found == True
        assert formatted_item.confidence_score == 0.85
        assert len(formatted_item.sheet_references) == 2
        assert len(formatted_item.spec_references) == 2
        assert "foundation plan drawings" in formatted_item.sheet_reasoning
        assert "concrete specifications" in formatted_item.spec_reasoning
        
        # Test error handling
        print("Testing error handling...")
        invalid_item = {"item_id": "INVALID"}
        formatted_invalid = generator.format_checklist_item(invalid_item)
        print("Invalid formatted item:", formatted_invalid)
        
        print("Checking error handling assertions...")
        assert isinstance(formatted_invalid, ChecklistItem), f"Invalid item type: {type(formatted_invalid)}"
        print("✓ Type check passed")
        
        assert formatted_invalid.category == "error", f"Category: {formatted_invalid.category}"
        print("✓ Category check passed")
        
        assert "Formatting error" in formatted_invalid.notes, f"Notes: {formatted_invalid.notes}"
        print("✓ Notes check passed")
        
        assert "Error occurred during formatting" in formatted_invalid.sheet_reasoning, f"Sheet reasoning: {formatted_invalid.sheet_reasoning}"
        print("✓ Sheet reasoning check passed")
        
        assert "Error occurred during formatting" in formatted_invalid.spec_reasoning, f"Spec reasoning: {formatted_invalid.spec_reasoning}"
        print("✓ Spec reasoning check passed")
        
        print("✅ Checklist item formatting passed")
        return True
    except Exception as e:
        print(f"❌ Checklist item formatting failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_document_reference_formatting():
    """Test document reference formatting"""
    print("Testing document reference formatting...")
    
    try:
        generator = OutputGenerator()
        
        # Test valid document
        raw_doc = {
            "type": "drawing",
            "filename": "A-101_Floor_Plan.pdf",
            "sheet_number": "A-101",
            "section_number": None,
            "page_count": 1,
            "file_size": 2048576,
            "upload_timestamp": "2024-01-15T10:30:00"
        }
        
        formatted_doc = generator.format_document_reference(raw_doc)
        
        assert isinstance(formatted_doc, DocumentReference)
        assert formatted_doc.document_type == "drawing"
        assert formatted_doc.filename == "A-101_Floor_Plan.pdf"
        assert formatted_doc.sheet_number == "A-101"
        assert formatted_doc.page_count == 1
        assert formatted_doc.file_size == 2048576
        
        # Test specification document
        raw_spec = {
            "type": "specification",
            "filename": "Specifications.pdf",
            "sheet_number": None,
            "section_number": "03 30 00",
            "page_count": 50,
            "file_size": 10485760,
            "upload_timestamp": "2024-01-15T10:35:00"
        }
        
        formatted_spec = generator.format_document_reference(raw_spec)
        
        assert formatted_spec.document_type == "specification"
        assert formatted_spec.section_number == "03 30 00"
        assert formatted_spec.page_count == 50
        
        print("✅ Document reference formatting passed")
        return True
    except Exception as e:
        print(f"❌ Document reference formatting failed: {e}")
        return False

def test_final_output_compilation(generator=None):
    """Test final output compilation"""
    print("Testing final output compilation...")
    
    try:
        if generator is None:
            generator = OutputGenerator()
        print("✓ OutputGenerator created")
        
        # Create a tracker
        process_id = "test-compilation-123"
        tracker_id = generator.create_progress_tracker(process_id, 3, 150)
        print(f"✓ Tracker created: {tracker_id}")
        
        if not tracker_id:
            print("❌ Failed to create tracker")
            return None, None
        
        # Simulate some progress
        print("Simulating progress updates...")
        batch_results = [
            {"item_id": "1", "found": True, "confidence_score": 0.8},
            {"item_id": "2", "found": False, "confidence_score": 0.3}
        ]
        generator.update_progress(tracker_id, 0, batch_results, "processing")
        print("✓ Batch 0 progress updated")
        generator.update_progress(tracker_id, 1, batch_results, "processing")
        print("✓ Batch 1 progress updated")
        generator.update_progress(tracker_id, 2, batch_results, "completed")
        print("✓ Batch 2 progress updated")
        
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
        
        # Compile final output
        print("Compiling final output...")
        clean_results = generator.compile_final_output(process_id, tracker_id, raw_results, document_info)
        print(f"✓ Final output compiled: {type(clean_results)}")
        
        print("Checking final output assertions...")
        assert isinstance(clean_results, list), f"Type: {type(clean_results)}"
        print("✓ Type check passed")
        
        assert len(clean_results) == 3, f"Results count: {len(clean_results)}"
        print("✓ Results count check passed")
        
        # Check that all required fields are present
        required_fields = ["row_id", "category", "scope_of_work", "checklist", "sector", "sheet_number", "spec_section", "notes", "reasoning", "found", "confidence", "validation_score"]
        for field in required_fields:
            assert field in clean_results[0], f"Missing field: {field}"
        print("✓ Required fields check passed")
        
        # Check that row_id is properly set
        assert clean_results[0]["row_id"] == 1, f"Row ID: {clean_results[0]['row_id']}"
        print("✓ Row ID check passed")
        
        # Check that found items are properly marked
        found_count = sum(1 for item in clean_results if item.get("found", False))
        assert found_count == 3, f"Found count: {found_count}"
        print("✓ Found count check passed")
        
        print("✅ Final output compilation passed")
        return generator, process_id
    except Exception as e:
        print(f"❌ Final output compilation failed: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def test_json_output_generation():
    """Test JSON output generation"""
    print("Testing JSON output generation...")
    
    try:
        generator, process_id = test_final_output_compilation()
        if not process_id:
            return False
        
        # Generate clean JSON output
        json_output = generator.generate_clean_json_output(process_id, pretty_print=True)
        
        assert json_output is not None
        assert len(json_output) > 0
        
        # Parse JSON to verify structure
        parsed_output = json.loads(json_output)
        
        # Check that it's a list of checklist items
        assert isinstance(parsed_output, list)
        assert len(parsed_output) > 0
        
        # Check that each item has the required fields
        required_fields = ["row_id", "category", "scope_of_work", "checklist", "sector", "sheet_number", "spec_section", "notes", "reasoning", "found", "confidence", "validation_score"]
        for item in parsed_output:
            for field in required_fields:
                assert field in item, f"Missing field {field} in item"
        
        print("✅ JSON output generation passed")
        return True
    except Exception as e:
        print(f"❌ JSON output generation failed: {e}")
        return False

def test_file_saving():
    """Test file saving functionality"""
    print("Testing file saving functionality...")
    
    try:
        generator, process_id = test_final_output_compilation()
        if not process_id:
            return False
        
        # Save to file
        filepath = generator.save_clean_output_to_file(process_id)
        
        assert filepath is not None
        assert Path(filepath).exists()
        
        # Check file content
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert len(content) > 0
        
        # Parse to verify it's valid JSON
        parsed_content = json.loads(content)
        assert isinstance(parsed_content, list)
        assert len(parsed_content) > 0
        
        # Test custom filename
        custom_filename = "custom_results.json"
        custom_filepath = generator.save_clean_output_to_file(process_id, custom_filename)
        
        assert Path(custom_filepath).name == custom_filename
        assert Path(custom_filepath).exists()
        
        # Cleanup
        Path(filepath).unlink(missing_ok=True)
        Path(custom_filepath).unlink(missing_ok=True)
        
        print("✅ File saving functionality passed")
        return True
    except Exception as e:
        print(f"❌ File saving functionality failed: {e}")
        return False

def test_cleanup_functionality():
    """Test cleanup functionality"""
    print("Testing cleanup functionality...")
    
    try:
        generator, process_id = test_final_output_compilation()
        
        # Test tracker cleanup
        tracker_id = generator.create_progress_tracker("test-cleanup", 2, 100)
        success = generator.cleanup_tracker(tracker_id)
        assert success == True
        assert tracker_id not in generator.progress_trackers
        
        # Test output cleanup
        if process_id:
            success = generator.cleanup_output(process_id)
            assert success == True
            assert process_id not in generator.output_cache
        
        # Test cleanup of non-existent items
        success = generator.cleanup_tracker("non-existent")
        assert success == False
        
        success = generator.cleanup_output("non-existent")
        assert success == False
        
        print("✅ Cleanup functionality passed")
        return True
    except Exception as e:
        print(f"❌ Cleanup functionality failed: {e}")
        return False

def test_system_status():
    """Test system status functionality"""
    print("Testing system status functionality...")
    
    try:
        generator = OutputGenerator()
        
        # Create some test data
        generator.create_progress_tracker("test-status-1", 2, 100)
        generator.create_progress_tracker("test-status-2", 3, 150)
        
        # Get system status
        status = generator.get_system_status()
        
        assert "active_trackers" in status
        assert "cached_outputs" in status
        assert "results_folder" in status
        assert "system_version" in status
        
        assert status["active_trackers"] >= 2
        assert status["system_version"] == "1.0.0"
        assert status["results_folder"] == Config.RESULTS_FOLDER
        
        print("✅ System status functionality passed")
        return True
    except Exception as e:
        print(f"❌ System status functionality failed: {e}")
        return False

def run_phase4_tests():
    """Run all Phase 4 tests"""
    print("=" * 60)
    print("PHASE 4 TEST SUITE - OUTPUT GENERATION & PROGRESS TRACKING")
    print("=" * 60)
    
    tests = [
        ("OutputGenerator Initialization", test_output_generator_initialization),
        ("Progress Tracker Creation", lambda: test_progress_tracker_creation() is not None),
        ("Progress Updates", test_progress_updates),
        ("Checklist Item Formatting", test_checklist_item_formatting),
        ("Document Reference Formatting", test_document_reference_formatting),
        ("Final Output Compilation", lambda: test_final_output_compilation() is not None),
        ("JSON Output Generation", test_json_output_generation),
        ("File Saving Functionality", test_file_saving),
        ("Cleanup Functionality", test_cleanup_functionality),
        ("System Status Functionality", test_system_status)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"PHASE 4 TEST RESULTS: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("🎉 ALL PHASE 4 TESTS PASSED!")
        return True
    else:
        print("⚠️  Some tests failed. Please review the output above.")
        return False

if __name__ == "__main__":
    # Validate configuration
    try:
        Config.validate_config()
        print("✅ Configuration validated")
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)
    
    # Run tests
    success = run_phase4_tests()
    if success:
        print("🎉 ALL PHASE 4 TESTS PASSED!")
    else:
        print("❌ Some tests failed. See output above.")
    sys.exit(0 if success else 1) 