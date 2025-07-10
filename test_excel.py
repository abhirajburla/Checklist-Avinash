#!/usr/bin/env python3
"""
Test script for Excel generation functionality
"""

import json
import tempfile
import os
from pathlib import Path

# Import our modules
from src.config import Config
from src.logger_config import LoggerConfig
from src.output_generator import OutputGenerator

# Setup logging
LoggerConfig.setup_from_config(Config)
logger = LoggerConfig.get_logger(__name__)

def test_excel_generation():
    """Test the Excel generation functionality"""
    
    # Create test data that matches the actual structure from matching engine
    test_data = {
        "checklist_results": [
            {
                "row_id": 1,
                "category": "Structural",
                "scope_of_work": "Foundation and Concrete",
                "checklist": "Foundation inspection requirements",
                "sector": "Industrial",
                "found": True,
                "sheet_number": "A-101, A-102",
                "spec_section": "03 30 00, 03 31 00",
                "notes": "Standard foundation inspection checklist",
                "reasoning": "Found in foundation drawings A-101 and A-102",
                "confidence": "HIGH",
                "validation_score": 0.85
            },
            {
                "row_id": 2,
                "category": "Mechanical",
                "scope_of_work": "HVAC Systems",
                "checklist": "HVAC system installation checklist",
                "sector": "Commercial",
                "found": False,
                "sheet_number": "",
                "spec_section": "",
                "notes": "HVAC system not included in current scope",
                "reasoning": "No HVAC drawings found in uploaded documents",
                "confidence": "LOW",
                "validation_score": 0.0
            },
            {
                "row_id": 3,
                "category": "Electrical",
                "scope_of_work": "Electrical Systems",
                "checklist": "Electrical panel installation",
                "sector": "Industrial",
                "found": True,
                "sheet_number": "E-201, E-202, E-203",
                "spec_section": "26 05 00, 26 20 00",
                "notes": "Main electrical panel and sub-panels included",
                "reasoning": "Electrical panel details found in sheets E-201 through E-203",
                "confidence": "HIGH",
                "validation_score": 0.92
            }
        ]
    }
    
    # Initialize output generator
    output_generator = OutputGenerator()
    
    # Create a test process ID
    test_process_id = "test-process-123"
    
    # Cache the test data
    output_generator.output_cache[test_process_id] = test_data
    
    try:
        # Generate Excel file
        excel_filepath = output_generator.generate_excel_output(test_process_id, "test_results.xlsx")
        
        print(f"✅ Excel file generated successfully: {excel_filepath}")
        
        # Check if file exists
        if os.path.exists(excel_filepath):
            file_size = os.path.getsize(excel_filepath)
            print(f"✅ File exists with size: {file_size} bytes")
            
            # Read the Excel file to verify content
            import pandas as pd
            df = pd.read_excel(excel_filepath)
            
            print(f"✅ Excel file contains {len(df)} rows and {len(df.columns)} columns")
            print("📊 Column headers:")
            for col in df.columns:
                print(f"   - {col}")
            
            print("\n📋 Sample data:")
            print(df.head())
            
            return True
        else:
            print("❌ Excel file was not created")
            return False
            
    except Exception as e:
        print(f"❌ Error generating Excel file: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== Testing Excel Generation ===")
    success = test_excel_generation()
    
    if success:
        print("\n✅ Excel generation test passed!")
    else:
        print("\n❌ Excel generation test failed!") 