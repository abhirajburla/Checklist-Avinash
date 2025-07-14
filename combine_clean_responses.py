#!/usr/bin/env python3
"""
Clean Response Combiner - Enhanced Version
Combines all Gemini API response files into a single clean JSON output
with proper mapping to original checklist data.
"""

import json
import os
import glob
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
import pandas as pd

def load_master_checklist() -> Dict[int, Dict[str, str]]:
    """Load master checklist and create index mapping"""
    try:
        # Load the master checklist CSV
        checklist_path = Path("MASTER TEMP.csv")
        if not checklist_path.exists():
            print(f"❌ Master checklist file not found: {checklist_path}")
            return {}
        
        df = pd.read_csv(checklist_path)
        
        # Validate required columns
        required_columns = ['Category', 'Scope of Work', 'Checklist', 'Sector']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"❌ Missing required columns in master checklist: {missing_columns}")
            return {}
        
        # Clean the data
        df = df.dropna(subset=['Category', 'Scope of Work', 'Checklist'])
        df['Category'] = df['Category'].str.strip()
        df['Scope of Work'] = df['Scope of Work'].str.strip()
        df['Checklist'] = df['Checklist'].str.strip()
        df['Sector'] = df['Sector'].str.strip()
        df = df.drop_duplicates(subset=['Category', 'Scope of Work', 'Checklist'])
        df = df.reset_index(drop=True)
        df['row_id'] = df.index + 1
        
        # Create mapping from checklist_index (1-based) to original data
        checklist_mapping = {}
        for i, (_, row) in enumerate(df.iterrows()):
            checklist_index = i + 1  # 1-based index
            checklist_mapping[checklist_index] = {
                'row_id': row['row_id'],
                'Category': row['Category'],
                'Scope of Work': row['Scope of Work'],
                'Checklist': row['Checklist'],
                'Sector': row['Sector']
            }
        
        print(f"✅ Loaded master checklist with {len(checklist_mapping)} items")
        return checklist_mapping
        
    except Exception as e:
        print(f"❌ Error loading master checklist: {e}")
        return {}

def combine_clean_responses(session_id: Optional[str] = None, process_id: Optional[str] = None, combine_all: bool = False):
    """
    Combine all Gemini API response files into a single clean JSON output.
    
    Args:
        session_id: Specific session ID to combine
        process_id: Specific process ID to combine  
        combine_all: Combine all available responses
    """
    
    print("🔧 Clean Response Combiner - Enhanced Version")
    print("=" * 50)
    
    # Load master checklist mapping
    checklist_mapping = load_master_checklist()
    if not checklist_mapping:
        print("❌ Cannot proceed without master checklist data")
        return
    
    # Find response files
    response_dir = Path("json_outputs/responses")
    if not response_dir.exists():
        print(f"❌ Response directory not found: {response_dir}")
        return
    
    # Get all JSON response files
    pattern = "checklist_matching_batch_*.json"
    response_files = list(response_dir.glob(pattern))
    
    if not response_files:
        print(f"❌ No response files found matching pattern: {pattern}")
        return
    
    print(f"📁 Found {len(response_files)} response files")
    
    # Filter files based on parameters
    if session_id:
        response_files = [f for f in response_files if f"session_{session_id}" in f.name]
        print(f"🔍 Filtered to {len(response_files)} files for session {session_id}")
    elif process_id:
        response_files = [f for f in response_files if process_id in f.name]
        print(f"🔍 Filtered to {len(response_files)} files for process {process_id}")
    
    if not response_files:
        print("❌ No matching response files found")
        return
    
    # Process all response files
    all_matches = []
    total_files_processed = 0
    total_matches_found = 0
    
    for file_path in sorted(response_files):
        try:
            print(f"📄 Processing: {file_path.name}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract matches from response
            response_text = data.get('response_text', '')
            
            # Parse the JSON from response_text (remove markdown code blocks)
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            response_data = json.loads(response_text.strip())
            matches = response_data.get('matches', [])
            
            print(f"   Found {len(matches)} matches in this file")
            
            # Convert matches to clean format with original checklist data
            for match in matches:
                checklist_index = match.get("checklist_index", 0)
                
                # Get original checklist data
                original_data = checklist_mapping.get(checklist_index, {})
                
                # Create clean result with all required fields
                clean_result = {
                    "row_id": original_data.get('row_id', checklist_index),
                    "category": original_data.get('Category', ''),
                    "scope_of_work": original_data.get('Scope of Work', ''),
                    "checklist": original_data.get('Checklist', ''),
                    "sector": original_data.get('Sector', ''),
                    "sheet_number": ", ".join(match.get("sheet_references", [])),
                    "spec_section": ", ".join(match.get("spec_references", [])),
                    "notes": match.get("notes", ""),
                    "reasoning": match.get("reasoning", ""),
                    "found": match.get("found", False),
                    "confidence": match.get("confidence", "LOW"),
                    "validation_score": match.get("validation_score", 0.0)
                }
                
                all_matches.append(clean_result)
                total_matches_found += 1
            
            total_files_processed += 1
            
        except Exception as e:
            print(f"❌ Error processing {file_path.name}: {e}")
            continue
    
    if not all_matches:
        print("❌ No matches found in any response files")
        return
    
    # Sort by row_id to maintain checklist order
    all_matches.sort(key=lambda x: x.get('row_id', 0))
    
    # Create output
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create combined directory if it doesn't exist
    combined_dir = Path("json_outputs/combined")
    combined_dir.mkdir(parents=True, exist_ok=True)
    
    # Save clean combined JSON
    output_filename = f"all_responses_clean_{timestamp}.json"
    output_path = combined_dir / output_filename
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_matches, f, indent=2, ensure_ascii=False)
    
    # Generate summary report
    summary = {
        "processing_summary": {
            "timestamp": timestamp,
            "files_processed": total_files_processed,
            "total_matches": total_matches_found,
            "unique_checklist_items": len(set(match.get('row_id') for match in all_matches)),
            "found_count": sum(1 for match in all_matches if match.get('found', False)),
            "not_found_count": sum(1 for match in all_matches if not match.get('found', False))
        },
        "data_structure": {
            "fields": ["row_id", "category", "scope_of_work", "checklist", "sector", "sheet_number", "spec_section", "notes", "reasoning", "found", "confidence", "validation_score"],
            "total_items": len(all_matches)
        },
        "file_info": {
            "output_file": str(output_path),
            "file_size_mb": round(output_path.stat().st_size / (1024 * 1024), 2)
        }
    }
    
    # Save summary report
    summary_filename = f"processing_summary_{timestamp}.json"
    summary_path = combined_dir / summary_filename
    
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    # Print results
    print("\n" + "=" * 50)
    print("✅ COMBINATION COMPLETED SUCCESSFULLY")
    print("=" * 50)
    print(f"📊 Processing Summary:")
    print(f"   Files processed: {total_files_processed}")
    print(f"   Total matches: {total_matches_found}")
    print(f"   Unique checklist items: {summary['processing_summary']['unique_checklist_items']}")
    print(f"   Items found: {summary['processing_summary']['found_count']}")
    print(f"   Items not found: {summary['processing_summary']['not_found_count']}")
    print(f"   Output file: {output_path}")
    print(f"   File size: {summary['file_info']['file_size_mb']} MB")
    print(f"   Summary report: {summary_path}")
    
    # Show sample of first few items
    print(f"\n📋 Sample Data (first 3 items):")
    for i, item in enumerate(all_matches[:3]):
        print(f"   Item {i+1}:")
        print(f"     row_id: {item.get('row_id')}")
        print(f"     category: {item.get('category')}")
        print(f"     scope_of_work: {item.get('scope_of_work')}")
        print(f"     checklist: {item.get('checklist')[:100]}...")
        print(f"     sector: {item.get('sector')}")
        print(f"     found: {item.get('found')}")
        print()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--all":
            combine_clean_responses(combine_all=True)
        elif sys.argv[1].startswith("session_"):
            combine_clean_responses(session_id=sys.argv[1])
        else:
            combine_clean_responses(process_id=sys.argv[1])
    else:
        print("Usage:")
        print("  python combine_clean_responses.py --all                    # Combine all responses")
        print("  python combine_clean_responses.py session_1234567890       # Combine specific session")
        print("  python combine_clean_responses.py process_uuid_12345       # Combine specific process")
        print("\nRunning with --all to combine all available responses...")
        combine_clean_responses(combine_all=True) 