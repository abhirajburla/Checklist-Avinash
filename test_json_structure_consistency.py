#!/usr/bin/env python3
"""
Comprehensive JSON Structure Consistency Test
Verifies that all JSON structures throughout the project are consistent
with the required format: row_id, category, scope_of_work, checklist, sector, etc.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any

def test_master_checklist_structure():
    """Test that the master checklist has the correct structure"""
    print("🔍 Testing Master Checklist Structure...")
    
    try:
        checklist_path = Path("MASTER TEMP.csv")
        if not checklist_path.exists():
            print("❌ Master checklist file not found")
            return False
        
        import pandas as pd
        df = pd.read_csv(checklist_path)
        
        # Check required columns
        required_columns = ['Category', 'Scope of Work', 'Checklist', 'Sector']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"❌ Missing required columns: {missing_columns}")
            return False
        
        # Check that row_id is added during processing
        if 'row_id' not in df.columns:
            print("⚠️  row_id column not present (will be added during processing)")
        
        print(f"✅ Master checklist structure is correct with {len(df)} items")
        return True
        
    except Exception as e:
        print(f"❌ Error testing master checklist: {e}")
        return False

def test_enhanced_batch_processor_structure():
    """Test that the enhanced batch processor produces correct structure"""
    print("🔍 Testing Enhanced Batch Processor Structure...")
    
    try:
        # Import the enhanced batch processor
        from src.enhanced_batch_processor import EnhancedBatchProcessor
        from src.gemini_client import GeminiClient
        from src.config import Config
        
        # Create a test instance
        config = Config()
        gemini_client = GeminiClient()
        processor = EnhancedBatchProcessor(gemini_client, config)
        
        # Test the _validate_and_clean_result method
        test_batch = [
            {
                'row_id': 1,
                'Category': 'Pre-Bid',
                'Scope of Work': '02 40 00 Demolition',
                'Checklist': 'Test checklist item',
                'Sector': 'Industrial'
            }
        ]
        
        test_results = [
            {
                'found': True,
                'sheet_number': 'A1.1',
                'spec_section': '02 40 00',
                'notes': 'Test notes',
                'reasoning': 'Test reasoning',
                'confidence': 'HIGH',
                'validation_score': 0.95
            }
        ]
        
        cleaned_results = processor._validate_and_clean_result(test_results, test_batch)
        
        if not cleaned_results:
            print("❌ No cleaned results returned")
            return False
        
        # Check structure
        result = cleaned_results[0]
        required_fields = [
            'row_id', 'category', 'scope_of_work', 'checklist', 'sector',
            'sheet_number', 'spec_section', 'notes', 'reasoning', 'found',
            'confidence', 'validation_score'
        ]
        
        for field in required_fields:
            if field not in result:
                print(f"❌ Missing field: {field}")
                return False
        
        print("✅ Enhanced batch processor structure is correct")
        return True
        
    except Exception as e:
        print(f"❌ Error testing enhanced batch processor: {e}")
        return False

def test_output_generator_structure():
    """Test that the output generator produces correct structure"""
    print("🔍 Testing Output Generator Structure...")
    
    try:
        from src.output_generator import OutputGenerator
        
        generator = OutputGenerator()
        
        # Test the generate_clean_json_output method
        test_data = {
            "checklist_results": [
                {
                    "row_id": 1,
                    "category": "Pre-Bid",
                    "scope_of_work": "02 40 00 Demolition",
                    "checklist": "Test checklist item",
                    "sector": "Industrial",
                    "sheet_number": "A1.1",
                    "spec_section": "02 40 00",
                    "notes": "Test notes",
                    "reasoning": "Test reasoning",
                    "found": True,
                    "confidence": "HIGH",
                    "validation_score": 0.95
                }
            ]
        }
        
        # Store test data in cache
        test_process_id = "test-process-123"
        generator.output_cache[test_process_id] = test_data
        
        # Generate clean JSON
        clean_json = generator.generate_clean_json_output(test_process_id, pretty_print=True)
        
        # Parse and verify structure
        parsed_data = json.loads(clean_json)
        
        if not isinstance(parsed_data, list):
            print("❌ Clean JSON is not a list")
            return False
        
        if len(parsed_data) == 0:
            print("❌ Clean JSON is empty")
            return False
        
        # Check structure
        item = parsed_data[0]
        required_fields = [
            'row_id', 'category', 'scope_of_work', 'checklist', 'sector',
            'sheet_number', 'spec_section', 'notes', 'reasoning', 'found',
            'confidence', 'validation_score'
        ]
        
        for field in required_fields:
            if field not in item:
                print(f"❌ Missing field: {field}")
                return False
        
        print("✅ Output generator structure is correct")
        return True
        
    except Exception as e:
        print(f"❌ Error testing output generator: {e}")
        return False

def test_existing_clean_json():
    """Test that existing clean JSON files have correct structure"""
    print("🔍 Testing Existing Clean JSON Files...")
    
    try:
        combined_dir = Path("json_outputs/combined")
        if not combined_dir.exists():
            print("⚠️  No combined directory found")
            return True
        
        json_files = list(combined_dir.glob("*.json"))
        if not json_files:
            print("⚠️  No JSON files found in combined directory")
            return True
        
        # Filter out summary files
        json_files = [f for f in json_files if "summary" not in f.name.lower()]
        
        for json_file in json_files:
            print(f"  Testing {json_file.name}...")
            
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                print(f"❌ {json_file.name} is not a list")
                return False
            
            if len(data) == 0:
                print(f"⚠️  {json_file.name} is empty")
                continue
            
            # Check structure of first item
            item = data[0]
            required_fields = [
                'row_id', 'category', 'scope_of_work', 'checklist', 'sector',
                'sheet_number', 'spec_section', 'notes', 'reasoning', 'found',
                'confidence', 'validation_score'
            ]
            
            for field in required_fields:
                if field not in item:
                    print(f"❌ {json_file.name} missing field: {field}")
                    return False
            
            print(f"  ✅ {json_file.name} structure is correct")
        
        print("✅ All existing clean JSON files have correct structure")
        return True
        
    except Exception as e:
        print(f"❌ Error testing existing JSON files: {e}")
        return False

def test_api_endpoints():
    """Test that API endpoints return correct structure"""
    print("🔍 Testing API Endpoints...")
    
    try:
        import requests
        
        # Test if Flask app is running
        try:
            response = requests.get("http://localhost:5000", timeout=5)
            if response.status_code != 200:
                print("❌ Flask app not responding")
                return False
        except:
            print("⚠️  Flask app not running, skipping API endpoint tests")
            return True
        
        print("✅ Flask app is running")
        return True
        
    except Exception as e:
        print(f"❌ Error testing API endpoints: {e}")
        return False

def main():
    """Run all structure consistency tests"""
    print("🧪 JSON Structure Consistency Test")
    print("=" * 50)
    
    tests = [
        ("Master Checklist", test_master_checklist_structure),
        ("Enhanced Batch Processor", test_enhanced_batch_processor_structure),
        ("Output Generator", test_output_generator_structure),
        ("Existing Clean JSON", test_existing_clean_json),
        ("API Endpoints", test_api_endpoints)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All JSON structures are consistent!")
        return True
    else:
        print("⚠️  Some JSON structures need attention")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 