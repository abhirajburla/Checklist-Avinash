#!/usr/bin/env python3
"""
Sample Output Demonstration
Shows what the structured output looks like for checklist matching
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from schemas import (
    BatchMatchResult,
    ChecklistMatch,
    ConfidenceLevel,
    Discipline
)

def show_sample_output():
    """Show sample structured output"""
    print("🎯 SAMPLE STRUCTURED OUTPUT")
    print("=" * 60)
    
    # Sample checklist batch
    sample_checklist = [
        {
            "row_id": "001",
            "Category": "Demolition",
            "Scope of Work": "Site Preparation",
            "Checklist": "Review demolition requirements and permits",
            "Sector": "Commercial"
        },
        {
            "row_id": "002", 
            "Category": "Foundation",
            "Scope of Work": "Concrete Work",
            "Checklist": "Verify foundation specifications and reinforcement",
            "Sector": "Commercial"
        },
        {
            "row_id": "003",
            "Category": "Electrical",
            "Scope of Work": "Power Systems",
            "Checklist": "Check electrical panel specifications and load calculations",
            "Sector": "Commercial"
        }
    ]
    
    # Sample structured output result
    sample_result = BatchMatchResult(
        matches=[
            ChecklistMatch(
                checklist_index=1,
                checklist_item=sample_checklist[0],
                found=True,
                confidence=ConfidenceLevel.HIGH,
                validation_score=0.95,
                sheet_references=["A1.1", "A1.2"],
                spec_references=["02 41 00", "02 42 00"],
                notes="Demolition requirements clearly specified in drawings A1.1 and A1.2. Permits and safety requirements detailed in specifications.",
                reasoning="The checklist item matches demolition scope shown in floor plan drawings and demolition specifications. High confidence due to clear documentation."
            ),
            ChecklistMatch(
                checklist_index=2,
                checklist_item=sample_checklist[1],
                found=True,
                confidence=ConfidenceLevel.MEDIUM,
                validation_score=0.78,
                sheet_references=["S1.1", "S1.2"],
                spec_references=["03 30 00", "03 31 00"],
                notes="Foundation details shown in structural drawings. Concrete specifications available but reinforcement details need verification.",
                reasoning="Foundation specifications found in structural drawings and concrete specs. Medium confidence as some details require additional verification."
            ),
            ChecklistMatch(
                checklist_index=3,
                checklist_item=sample_checklist[2],
                found=False,
                confidence=ConfidenceLevel.LOW,
                validation_score=0.0,
                sheet_references=[],
                spec_references=[],
                notes="Electrical panel specifications not found in provided documents.",
                reasoning="No electrical drawings or specifications found in the uploaded documents. Item not found."
            )
        ],
        total_items=3,
        found_count=2,
        not_found_count=1,
        processing_time=2.45,
        model_used="gemini-2.5-flash"
    )
    
    print("📋 INPUT CHECKLIST BATCH:")
    print("-" * 40)
    for i, item in enumerate(sample_checklist, 1):
        print(f"{i}. {item['Checklist']}")
        print(f"   Category: {item['Category']}")
        print(f"   Scope: {item['Scope of Work']}")
        print()
    
    print("🎯 STRUCTURED OUTPUT RESULT:")
    print("-" * 40)
    print(f"Total Items: {sample_result.total_items}")
    print(f"Found: {sample_result.found_count}")
    print(f"Not Found: {sample_result.not_found_count}")
    print(f"Processing Time: {sample_result.processing_time}s")
    print(f"Model: {sample_result.model_used}")
    print()
    
    print("📊 DETAILED MATCHES:")
    print("-" * 40)
    for match in sample_result.matches:
        print(f"Item {match.checklist_index}: {match.checklist_item['Checklist']}")
        print(f"  Found: {'✅ YES' if match.found else '❌ NO'}")
        print(f"  Confidence: {match.confidence.value}")
        print(f"  Validation Score: {match.validation_score:.2f}")
        
        if match.found:
            print(f"  Sheet References: {', '.join(match.sheet_references) if match.sheet_references else 'None'}")
            print(f"  Spec References: {', '.join(match.spec_references) if match.spec_references else 'None'}")
            print(f"  Notes: {match.notes}")
            print(f"  Reasoning: {match.reasoning}")
        else:
            print(f"  Notes: {match.notes}")
            print(f"  Reasoning: {match.reasoning}")
        print()
    
    print("🔧 JSON OUTPUT FORMAT:")
    print("-" * 40)
    json_output = sample_result.model_dump_json(indent=2)
    print(json_output)
    
    print("\n" + "=" * 60)
    print("✅ STRUCTURED OUTPUT BENEFITS:")
    print("• Consistent JSON format every time")
    print("• Type-safe with Pydantic validation")
    print("• Includes checklist_index and full checklist_item")
    print("• Standardized confidence levels and validation scores")
    print("• Easy to integrate with other systems")
    print("• Reliable parsing with fallback handling")

if __name__ == "__main__":
    show_sample_output() 