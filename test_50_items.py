#!/usr/bin/env python3
"""
Test 50-Item Checklist
Tests the system with the reduced 50-item checklist for faster testing
"""

import pandas as pd
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from checklist_processor import ChecklistProcessor

def test_50_item_checklist():
    """Test the system with 50-item checklist"""
    print("🧪 TESTING 50-ITEM CHECKLIST")
    print("=" * 50)
    
    # Load the test checklist
    test_file = "MASTER CHECKLIST_TEST_50.csv"
    
    try:
        # Read the CSV
        df = pd.read_csv(test_file)
        print(f"✅ Successfully loaded {len(df)} items from {test_file}")
        
        # Display sample items
        print("\n📋 SAMPLE ITEMS:")
        print("-" * 30)
        for i, row in df.head(5).iterrows():
            print(f"{i+1}. {row['Checklist'][:80]}...")
            print(f"   Category: {row['Category']}")
            print(f"   Scope: {row['Scope of Work']}")
            print()
        
        # Test the processor
        processor = ChecklistProcessor()
        
        # Convert to list of dicts
        checklist_items = []
        for i, row in df.iterrows():
            item = {
                "row_id": f"test_{i+1:03d}",
                "Category": row["Category"],
                "Scope of Work": row["Scope of Work"],
                "Checklist": row["Checklist"],
                "Sector": row["Sector"]
            }
            checklist_items.append(item)
        
        print(f"📊 PROCESSOR TEST:")
        print(f"   Total items: {len(checklist_items)}")
        print(f"   Categories: {len(set(item['Category'] for item in checklist_items))}")
        print(f"   Sectors: {len(set(item['Sector'] for item in checklist_items))}")
        
        # Test batch processing
        batch_size = 10
        total_batches = (len(checklist_items) + batch_size - 1) // batch_size
        
        print(f"\n🔄 BATCH PROCESSING INFO:")
        print(f"   Batch size: {batch_size}")
        print(f"   Total batches: {total_batches}")
        print(f"   Items per batch: {batch_size} (last batch may be smaller)")
        
        # Show first batch
        first_batch = checklist_items[:batch_size]
        print(f"\n📦 FIRST BATCH PREVIEW:")
        for i, item in enumerate(first_batch, 1):
            print(f"   {i}. {item['Checklist'][:60]}...")
        
        print(f"\n✅ 50-ITEM CHECKLIST TEST COMPLETED!")
        print(f"   Ready for testing with documents!")
        
        return checklist_items
        
    except Exception as e:
        print(f"❌ Error testing 50-item checklist: {e}")
        return None

if __name__ == "__main__":
    test_50_item_checklist() 