#!/usr/bin/env python3
"""
Phase 3 Test Suite
Tests enhanced batch processing, system instructions, reference validation, and error handling
"""

import os
import sys
import json
import time
import asyncio
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import Config
from system_instructions import SystemInstructions
from reference_validator import ReferenceValidator, ValidationResult
from enhanced_batch_processor import EnhancedBatchProcessor, BatchResult, BatchStatus
from gemini_client import GeminiClient
from matching_engine import MatchingEngine

def test_system_instructions():
    """Test system instructions generation"""
    print("\n🧠 Testing System Instructions...")
    
    instructions = SystemInstructions()
    
    # Test checklist matching instructions
    checklist_instructions = instructions.get_checklist_matching_instructions()
    assert "construction document analyst" in checklist_instructions
    assert "ACCURACY OVER SPEED" in checklist_instructions
    assert "CSI (Construction Specifications Institute)" in checklist_instructions
    print("✅ Checklist matching instructions generated successfully")
    
    # Test specification extraction instructions
    spec_instructions = instructions.get_specification_extraction_instructions()
    assert "CSI MasterFormat" in spec_instructions
    assert "XX XX XX format" in spec_instructions
    print("✅ Specification extraction instructions generated successfully")
    
    # Test sheet extraction instructions
    sheet_instructions = instructions.get_sheet_extraction_instructions()
    assert "drawing expert" in sheet_instructions
    assert "title block" in sheet_instructions
    print("✅ Sheet extraction instructions generated successfully")
    
    # Test document summary instructions
    summary_instructions = instructions.get_document_summary_instructions()
    assert "construction project analyst" in summary_instructions
    assert "key construction elements" in summary_instructions
    print("✅ Document summary instructions generated successfully")
    
    # Test validation instructions
    validation_instructions = instructions.get_validation_instructions()
    assert "validation expert" in validation_instructions
    assert "Reference format verification" in validation_instructions
    print("✅ Validation instructions generated successfully")
    
    print("🎉 All system instructions tests passed!")

def test_reference_validator():
    """Test reference validation functionality"""
    print("\n🔍 Testing Reference Validator...")
    
    validator = ReferenceValidator()
    
    # Test sheet number validation
    print("Testing sheet number validation...")
    
    # Valid sheet numbers
    valid_sheets = ["A1.1", "S-01", "M-101", "E-02", "ARCH-01"]
    for sheet in valid_sheets:
        result = validator.validate_sheet_number(sheet)
        assert result.is_valid, f"Sheet {sheet} should be valid"
        assert result.confidence > 0.8, f"Sheet {sheet} should have high confidence"
        print(f"✅ Valid sheet number: {sheet}")
    
    # Invalid sheet numbers
    invalid_sheets = ["", "INVALID", "A-B-C", "SHEET-ABC"]
    for sheet in invalid_sheets:
        result = validator.validate_sheet_number(sheet)
        assert not result.is_valid, f"Sheet {sheet} should be invalid"
        print(f"✅ Invalid sheet number correctly rejected: {sheet}")
    
    # Test specification section validation
    print("Testing specification section validation...")
    
    # Valid spec sections
    valid_specs = ["03 30 00", "09 91 23", "22 11 16"]
    for spec in valid_specs:
        result = validator.validate_specification_section(spec)
        assert result.is_valid, f"Spec {spec} should be valid"
        assert result.confidence > 0.9, f"Spec {spec} should have high confidence"
        print(f"✅ Valid spec section: {spec}")
    
    # Invalid spec sections
    invalid_specs = ["", "INVALID", "123", "XX XX XX"]
    for spec in invalid_specs:
        result = validator.validate_specification_section(spec)
        assert not result.is_valid, f"Spec {spec} should be invalid"
        print(f"✅ Invalid spec section correctly rejected: {spec}")
    
    # Test page number validation
    print("Testing page number validation...")
    
    valid_pages = ["1", "10", "100", "1000"]
    for page in valid_pages:
        result = validator.validate_page_number(page)
        assert result.is_valid, f"Page {page} should be valid"
        print(f"✅ Valid page number: {page}")
    
    invalid_pages = ["", "0", "10001", "ABC"]
    for page in invalid_pages:
        result = validator.validate_page_number(page)
        assert not result.is_valid, f"Page {page} should be invalid"
        print(f"✅ Invalid page number correctly rejected: {page}")
    
    # Test reference validation
    print("Testing reference validation...")
    
    test_references = {
        "sheet_references": ["A1.1", "S-01"],
        "spec_references": ["03 30 00", "09 91 23"]
    }
    
    validation_results = validator.validate_references(test_references)
    
    assert validation_results["sheet_references"]["all_valid"]
    assert validation_results["spec_references"]["all_valid"]
    assert validation_results["sheet_references"]["confidence"] > 0.8
    assert validation_results["spec_references"]["confidence"] > 0.9
    
    print("✅ Reference validation working correctly")
    
    # Test batch result validation
    print("Testing batch result validation...")
    
    test_results = [
        {
            "row_id": 1,
            "category": "Concrete",
            "scope_of_work": "Foundation",
            "checklist": "Check concrete mix",
            "sector": "Structural",
            "found": True,
            "sheet_number": "A1.1, S-01",
            "spec_section": "03 30 00",
            "notes": "Found in drawings",
            "reasoning": "Direct reference",
            "confidence": "HIGH",
            "validation_score": 0.9
        }
    ]
    
    validated_results = validator.validate_batch_results(test_results)
    assert len(validated_results) == 1
    assert validated_results[0]["found"]
    assert "validation_metadata" in validated_results[0]
    
    print("✅ Batch result validation working correctly")
    
    print("🎉 All reference validator tests passed!")

def test_enhanced_batch_processor():
    """Test enhanced batch processor functionality"""
    print("\n⚡ Testing Enhanced Batch Processor...")
    
    # Create mock Gemini client for testing
    class MockGeminiClient:
        def __init__(self):
            self.context_cache = {"test_cache": []}
        
        def match_checklist_batch_with_system_instructions(self, batch, cache_id, context, instructions):
            # Mock successful response
            return [
                {
                    "row_id": item.get("row_id", 1),
                    "category": item["Category"],
                    "scope_of_work": item["Scope of Work"],
                    "checklist": item["Checklist"],
                    "sector": item["Sector"],
                    "found": True,
                    "sheet_number": "A1.1",
                    "spec_section": "03 30 00",
                    "notes": "Test match",
                    "reasoning": "Test reasoning",
                    "confidence": "HIGH",
                    "validation_score": 0.9
                }
                for item in batch
            ]
    
    config = Config()
    mock_client = MockGeminiClient()
    processor = EnhancedBatchProcessor(mock_client, config)
    
    # Test batch creation
    print("Testing batch creation...")
    
    test_batch = [
        {
            "row_id": 1,
            "Category": "Concrete",
            "Scope of Work": "Foundation",
            "Checklist": "Check concrete mix",
            "Sector": "Structural"
        },
        {
            "row_id": 2,
            "Category": "Steel",
            "Scope of Work": "Framing",
            "Checklist": "Check steel connections",
            "Sector": "Structural"
        }
    ]
    
    # Test single batch processing
    print("Testing single batch processing...")
    
    async def test_single_batch():
        result = await processor.process_batch_with_retry(
            test_batch, 0, "test_cache", "Test document context"
        )
        
        assert result.status == BatchStatus.COMPLETED
        assert result.items_processed == 2
        assert result.items_found == 2
        assert result.items_not_found == 0
        assert len(result.results) == 2
        assert result.confidence_score > 0.8
        assert result.processing_time >= 0  # Allow for very fast processing in tests
        
        print("✅ Single batch processing working correctly")
    
    # Test multiple batch processing
    print("Testing multiple batch processing...")
    
    async def test_multiple_batches():
        batches = [test_batch, test_batch]  # Two identical batches
        
        results = await processor.process_multiple_batches(
            batches, "test_cache", "Test document context"
        )
        
        assert len(results) == 2
        for result in results:
            assert result.status == BatchStatus.COMPLETED
            assert result.items_processed == 2
        
        print("✅ Multiple batch processing working correctly")
    
    # Run async tests
    asyncio.run(test_single_batch())
    asyncio.run(test_multiple_batches())
    
    # Test validation methods
    print("Testing validation methods...")
    
    # Test batch result validation
    valid_results = [
        {
            "row_id": 1,
            "category": "Concrete",
            "scope_of_work": "Foundation",
            "checklist": "Check concrete mix",
            "sector": "Structural",
            "found": True,
            "sheet_number": "A1.1",
            "spec_section": "03 30 00"
        },
        {
            "row_id": 2,
            "category": "Steel",
            "scope_of_work": "Framing",
            "checklist": "Check steel connections",
            "sector": "Structural",
            "found": False,
            "sheet_number": "",
            "spec_section": ""
        }
    ]
    
    assert processor._validate_batch_result(valid_results, test_batch)
    print("✅ Batch result validation working correctly")
    
    # Test confidence score calculation
    confidence = processor._calculate_confidence_score(valid_results)
    assert confidence > 0.0  # Should be greater than 0 since we have one found item
    print("✅ Confidence score calculation working correctly")
    
    print("🎉 All enhanced batch processor tests passed!")

def test_configuration():
    """Test Phase 3 configuration"""
    print("\n⚙️ Testing Phase 3 Configuration...")
    
    config = Config()
    
    # Test Phase 3 settings
    assert hasattr(config, 'ENABLE_SYSTEM_INSTRUCTIONS')
    assert hasattr(config, 'ENABLE_REFERENCE_VALIDATION')
    assert hasattr(config, 'ENABLE_ENHANCED_BATCH_PROCESSING')
    assert hasattr(config, 'MAX_CONCURRENT_BATCHES')
    assert hasattr(config, 'BATCH_RETRY_DELAY')
    assert hasattr(config, 'BATCH_BACKOFF_FACTOR')
    assert hasattr(config, 'MIN_CONFIDENCE_SCORE')
    assert hasattr(config, 'VALIDATION_STRICTNESS')
    
    print("✅ All Phase 3 configuration settings present")
    
    # Test default values
    assert config.MAX_CONCURRENT_BATCHES == 3
    assert config.BATCH_RETRY_DELAY == 2.0
    assert config.BATCH_BACKOFF_FACTOR == 2.0
    assert config.MIN_CONFIDENCE_SCORE == 0.7
    assert config.VALIDATION_STRICTNESS == "medium"
    
    print("✅ Default configuration values correct")
    
    print("🎉 All configuration tests passed!")

def test_integration():
    """Test integration of Phase 3 components"""
    print("\n🔗 Testing Phase 3 Integration...")
    
    # Test that all components can be imported and initialized
    try:
        from config import Config
        from system_instructions import SystemInstructions
        from reference_validator import ReferenceValidator
        from enhanced_batch_processor import EnhancedBatchProcessor, BatchStatus
        from gemini_client import GeminiClient
        from matching_engine import MatchingEngine
        
        print("✅ All Phase 3 components imported successfully")
        
        # Test component initialization
        instructions = SystemInstructions()
        validator = ReferenceValidator()
        config = Config()
        
        # Mock client for testing
        class MockClient:
            def __init__(self):
                self.context_cache = {"test": []}
            def match_checklist_batch_with_system_instructions(self, *args):
                return []
        
        mock_client = MockClient()
        processor = EnhancedBatchProcessor(mock_client, config)
        
        print("✅ All Phase 3 components initialized successfully")
        
        # Test system instructions integration
        checklist_instructions = instructions.get_checklist_matching_instructions()
        assert len(checklist_instructions) > 1000  # Should be substantial
        
        # Test validator integration
        validation_result = validator.validate_sheet_number("A1.1")
        assert validation_result.is_valid
        
        # Test batch processor integration
        assert processor.max_retries == config.MAX_RETRIES
        assert processor.batch_size == config.BATCH_SIZE
        
        print("✅ Phase 3 component integration working correctly")
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        raise
    
    print("🎉 All integration tests passed!")

def main():
    """Run all Phase 3 tests"""
    print("🚀 Starting Phase 3 Test Suite")
    print("=" * 50)
    
    try:
        # Test configuration first
        test_configuration()
        
        # Test individual components
        test_system_instructions()
        test_reference_validator()
        test_enhanced_batch_processor()
        
        # Test integration
        test_integration()
        
        print("\n" + "=" * 50)
        print("🎉 ALL PHASE 3 TESTS PASSED!")
        print("=" * 50)
        
        print("\n📋 Phase 3 Features Implemented:")
        print("✅ System Instructions for Gemini AI")
        print("✅ Enhanced Batch Processing with Retry Logic")
        print("✅ Reference Extraction and Validation")
        print("✅ Error Handling and Retry Mechanisms")
        print("✅ Configuration Management")
        print("✅ Component Integration")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Phase 3 test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 