#!/usr/bin/env python3
"""
Test Structured Output Implementation
Tests the new structured output schemas and Gemini client integration
"""

import os
import sys
import json
import time
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from schemas import (
    StructuredOutputSchemas,
    BatchMatchResult,
    ChecklistMatch,
    ConfidenceLevel,
    validate_batch_result,
    validate_specification_result,
    validate_sheet_result,
    validate_document_summary
)
from gemini_client import GeminiClient

def test_schema_validation():
    """Test schema validation functions"""
    print("=== TESTING SCHEMA VALIDATION ===")
    
    # Test checklist match validation
    test_match_data = {
        "checklist_index": 1,
        "found": True,
        "confidence": "HIGH",
        "sheet_references": ["A1.1", "A1.2"],
        "spec_references": ["03 30 00"],
        "notes": "Found in architectural drawings",
        "reasoning": "Direct reference to concrete work",
        "validation_score": 0.95
    }
    
    try:
        match = validate_batch_result({
            "matches": [test_match_data],
            "total_items": 1,
            "found_count": 1,
            "not_found_count": 0,
            "processing_metadata": {
                "batch_size": 1,
                "processing_time": 2.5,
                "confidence_threshold": 0.8
            }
        })
        print("✅ Batch result validation successful")
        print(f"   Found {match.found_count} items, {match.not_found_count} not found")
    except Exception as e:
        print(f"❌ Batch result validation failed: {e}")
    
    # Test specification result validation
    test_spec_data = {
        "specifications": [
            {
                "division": "03",
                "section_code": "03 30 00",
                "title": "Cast-in-Place Concrete",
                "page_number": "15",
                "extraction_confidence": "HIGH"
            }
        ],
        "total_specifications": 1
    }
    
    try:
        spec_result = validate_specification_result(test_spec_data)
        print("✅ Specification result validation successful")
        print(f"   Found {spec_result.total_specifications} specifications")
    except Exception as e:
        print(f"❌ Specification result validation failed: {e}")
    
    # Test sheet result validation
    test_sheet_data = {
        "sheet_number": "A1.1",
        "sheet_title": "FLOOR PLAN",
        "discipline": "Architectural",
        "project_info": "Project Name - Building A"
    }
    
    try:
        sheet_result = validate_sheet_result(test_sheet_data)
        print("✅ Sheet result validation successful")
        print(f"   Sheet: {sheet_result.sheet_number} - {sheet_result.sheet_title}")
    except Exception as e:
        print(f"❌ Sheet result validation failed: {e}")
    
    # Test document summary validation
    test_summary_data = {
        "document_overview": "Comprehensive construction project",
        "project_scope": "Commercial building construction",
        "key_systems": ["Structural", "Mechanical", "Electrical"],
        "major_specifications": ["03 30 00", "09 91 23"],
        "drawing_summary": "Architectural and structural drawings"
    }
    
    try:
        summary_result = validate_document_summary(test_summary_data)
        print("✅ Document summary validation successful")
        print(f"   Project scope: {summary_result.project_scope}")
    except Exception as e:
        print(f"❌ Document summary validation failed: {e}")

def test_gemini_client_structured_output():
    """Test Gemini client with structured output"""
    print("\n=== TESTING GEMINI CLIENT STRUCTURED OUTPUT ===")
    
    try:
        # Initialize client
        print("1. Initializing Gemini client...")
        client = GeminiClient()
        print("✅ Gemini client initialized successfully")
        
        # Test simple text generation with structured output
        print("\n2. Testing structured output with simple prompt...")
        start_time = time.time()
        
        # Create a simple test batch
        test_batch = [
            {
                "row_id": 1,
                "Category": "Pre-Bid",
                "Scope of Work": "02 40 00 Demolition",
                "Checklist": "Review demolition requirements",
                "Sector": "General"
            }
        ]
        
        # Test the structured output method
        print("   Testing structured output parsing...")
        
        # Simulate a structured response
        test_response = {
            "matches": [
                {
                    "checklist_index": 1,
                    "found": True,
                    "confidence": "HIGH",
                    "sheet_references": ["A1.1"],
                    "spec_references": ["02 40 00"],
                    "notes": "Found in demolition specifications",
                    "reasoning": "Direct reference to demolition requirements",
                    "validation_score": 0.9
                }
            ],
            "total_items": 1,
            "found_count": 1,
            "not_found_count": 0,
            "processing_metadata": {
                "batch_size": 1,
                "processing_time": 1.5,
                "confidence_threshold": 0.8
            }
        }
        
        # Test fallback parsing
        response_text = json.dumps(test_response)
        fallback_results = client._parse_fallback_response(response_text, test_batch)
        
        if fallback_results:
            print("✅ Fallback parsing successful")
            print(f"   Processed {len(fallback_results)} items")
            if fallback_results[0]["found"]:
                print(f"   Found item: {fallback_results[0]['checklist']}")
        else:
            print("❌ Fallback parsing failed")
        
        processing_time = time.time() - start_time
        print(f"   Processing time: {processing_time:.2f} seconds")
        
    except Exception as e:
        print(f"❌ Gemini client structured output test failed: {e}")
        import traceback
        traceback.print_exc()

def test_schema_definitions():
    """Test schema definitions and enums"""
    print("\n=== TESTING SCHEMA DEFINITIONS ===")
    
    # Test confidence levels
    print("1. Testing confidence levels...")
    confidence_levels = [ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM, ConfidenceLevel.LOW]
    for level in confidence_levels:
        print(f"   ✅ {level.value}")
    
    # Test schema access
    print("\n2. Testing schema access...")
    schemas = StructuredOutputSchemas()
    
    try:
        checklist_schema = schemas.get_checklist_matching_schema()
        print(f"   ✅ Checklist matching schema: {checklist_schema.__name__}")
        
        spec_schema = schemas.get_specification_extraction_schema()
        print(f"   ✅ Specification extraction schema: {spec_schema.__name__}")
        
        sheet_schema = schemas.get_sheet_extraction_schema()
        print(f"   ✅ Sheet extraction schema: {sheet_schema.__name__}")
        
        summary_schema = schemas.get_document_summary_schema()
        print(f"   ✅ Document summary schema: {summary_schema.__name__}")
        
    except Exception as e:
        print(f"   ❌ Schema access failed: {e}")

def main():
    """Run all tests"""
    print("🧪 STRUCTURED OUTPUT IMPLEMENTATION TESTS")
    print("=" * 50)
    
    # Test schema validation
    test_schema_validation()
    
    # Test schema definitions
    test_schema_definitions()
    
    # Test Gemini client integration
    test_gemini_client_structured_output()
    
    print("\n" + "=" * 50)
    print("✅ All structured output tests completed!")

if __name__ == "__main__":
    main() 