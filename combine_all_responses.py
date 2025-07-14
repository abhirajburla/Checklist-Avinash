#!/usr/bin/env python3
"""
Temporary script to combine all JSON responses from Gemini
Trims unnecessary metadata and creates a clean, well-formatted output
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

def combine_all_responses():
    """Combine all JSON responses from Gemini with trimmed metadata"""
    
    # Paths
    responses_dir = Path("json_outputs/responses")
    failed_dir = Path("json_outputs/failed")
    output_dir = Path("json_outputs/combined")
    output_dir.mkdir(exist_ok=True)
    
    print("🔍 Scanning for JSON response files...")
    
    # Collect all response files
    all_files = []
    
    if responses_dir.exists():
        response_files = list(responses_dir.glob("*.json"))
        print(f"Found {len(response_files)} successful response files")
        all_files.extend([(f, "successful") for f in response_files])
    
    if failed_dir.exists():
        failed_files = list(failed_dir.glob("*.json"))
        print(f"Found {len(failed_files)} failed response files")
        all_files.extend([(f, "failed") for f in failed_files])
    
    if not all_files:
        print("❌ No response files found!")
        return
    
    # Sort files by batch number and timestamp
    def get_sort_key(file_info):
        file_path, _ = file_info
        try:
            # Extract batch number from filename
            filename = file_path.stem
            if "batch_" in filename:
                batch_part = filename.split("batch_")[1]
                batch_num = int(batch_part.split("_")[0])
                return batch_num
            return 0
        except:
            return 0
    
    all_files.sort(key=get_sort_key)
    
    # Process all files
    print("\n📊 Processing response files...")
    
    combined_data = {
        "metadata": {
            "combined_at": datetime.now().isoformat(),
            "total_files": len(all_files),
            "successful_files": len([f for f, status in all_files if status == "successful"]),
            "failed_files": len([f for f, status in all_files if status == "failed"]),
            "total_batches": len(set([get_sort_key((f, status)) for f, status in all_files]))
        },
        "responses": [],
        "summary": {
            "total_tokens_used": 0,
            "total_cost": 0.0,
            "total_items_processed": 0,
            "total_items_found": 0,
            "total_items_not_found": 0,
            "success_rate": 0.0
        }
    }
    
    total_tokens = 0
    total_cost = 0.0
    total_items_processed = 0
    total_items_found = 0
    total_items_not_found = 0
    
    for file_path, status in all_files:
        try:
            print(f"Processing: {file_path.name}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract clean response data
            clean_response = {
                "file_name": file_path.name,
                "status": status,
                "batch_index": data.get("metadata", {}).get("batch_index", 0),
                "timestamp": data.get("metadata", {}).get("timestamp", ""),
                "operation": data.get("metadata", {}).get("operation", "unknown")
            }
            
            # Extract the actual Gemini response content
            response_text = data.get("response_text", "")
            
            # Try to parse the JSON response from Gemini
            try:
                # Clean the response text (remove markdown if present)
                cleaned_text = response_text.strip()
                if cleaned_text.startswith("```json"):
                    cleaned_text = cleaned_text[7:]
                if cleaned_text.endswith("```"):
                    cleaned_text = cleaned_text[:-3]
                cleaned_text = cleaned_text.strip()
                
                # Parse the JSON response
                gemini_response = json.loads(cleaned_text)
                
                # Extract matches and statistics
                matches = gemini_response.get("matches", [])
                total_items = gemini_response.get("total_items", len(matches))
                found_count = gemini_response.get("found_count", 0)
                not_found_count = gemini_response.get("not_found_count", 0)
                
                # Update summary statistics
                total_items_processed += total_items
                total_items_found += found_count
                total_items_not_found += not_found_count
                
                # Add clean response data
                clean_response.update({
                    "total_items": total_items,
                    "found_count": found_count,
                    "not_found_count": not_found_count,
                    "matches": matches,
                    "parsed_successfully": True
                })
                
            except json.JSONDecodeError as e:
                # If JSON parsing fails, store the raw response
                clean_response.update({
                    "raw_response": response_text,
                    "parse_error": str(e),
                    "parsed_successfully": False
                })
            
            # Extract token usage if available
            custom_metadata = data.get("custom_metadata", {})
            if "token_usage" in custom_metadata:
                token_usage = custom_metadata["token_usage"]
                input_tokens = token_usage.get("input_tokens", 0)
                output_tokens = token_usage.get("output_tokens", 0)
                cached_tokens = token_usage.get("cached_tokens", 0)
                total_cost += token_usage.get("total_cost", 0.0)
                
                total_tokens += input_tokens + output_tokens + cached_tokens
                
                clean_response["token_usage"] = {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cached_tokens": cached_tokens,
                    "total_cost": token_usage.get("total_cost", 0.0)
                }
            
            combined_data["responses"].append(clean_response)
            
        except Exception as e:
            print(f"❌ Error processing {file_path.name}: {e}")
            # Add error entry
            combined_data["responses"].append({
                "file_name": file_path.name,
                "status": "error",
                "error": str(e),
                "parsed_successfully": False
            })
    
    # Update summary
    combined_data["summary"].update({
        "total_tokens_used": total_tokens,
        "total_cost": total_cost,
        "total_items_processed": total_items_processed,
        "total_items_found": total_items_found,
        "total_items_not_found": total_items_not_found,
        "success_rate": (total_items_found / total_items_processed * 100) if total_items_processed > 0 else 0.0
    })
    
    # Save the combined file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"all_responses_combined_{timestamp}.json"
    output_path = output_dir / output_filename
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(combined_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Combined JSON saved to: {output_path}")
    print(f"\n📊 Summary:")
    print(f"   Total files processed: {combined_data['metadata']['total_files']}")
    print(f"   Successful files: {combined_data['metadata']['successful_files']}")
    print(f"   Failed files: {combined_data['metadata']['failed_files']}")
    print(f"   Total batches: {combined_data['metadata']['total_batches']}")
    print(f"   Total tokens used: {combined_data['summary']['total_tokens_used']:,}")
    print(f"   Total cost: ${combined_data['summary']['total_cost']:.6f}")
    print(f"   Total items processed: {combined_data['summary']['total_items_processed']}")
    print(f"   Items found: {combined_data['summary']['total_items_found']}")
    print(f"   Items not found: {combined_data['summary']['total_items_not_found']}")
    print(f"   Success rate: {combined_data['summary']['success_rate']:.2f}%")
    
    return output_path

def create_summary_report(combined_file_path):
    """Create a human-readable summary report"""
    
    with open(combined_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    summary_path = combined_file_path.parent / f"summary_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("GEMINI RESPONSES SUMMARY REPORT\n")
        f.write("=" * 60 + "\n\n")
        
        f.write(f"Generated: {data['metadata']['combined_at']}\n")
        f.write(f"Total files processed: {data['metadata']['total_files']}\n")
        f.write(f"Successful files: {data['metadata']['successful_files']}\n")
        f.write(f"Failed files: {data['metadata']['failed_files']}\n")
        f.write(f"Total batches: {data['metadata']['total_batches']}\n\n")
        
        f.write("SUMMARY STATISTICS:\n")
        f.write("-" * 30 + "\n")
        f.write(f"Total tokens used: {data['summary']['total_tokens_used']:,}\n")
        f.write(f"Total cost: ${data['summary']['total_cost']:.6f}\n")
        f.write(f"Total items processed: {data['summary']['total_items_processed']}\n")
        f.write(f"Items found: {data['summary']['total_items_found']}\n")
        f.write(f"Items not found: {data['summary']['total_items_not_found']}\n")
        f.write(f"Success rate: {data['summary']['success_rate']:.2f}%\n\n")
        
        f.write("BATCH DETAILS:\n")
        f.write("-" * 30 + "\n")
        
        for response in data['responses']:
            f.write(f"Batch {response.get('batch_index', 'N/A')}: ")
            f.write(f"{response.get('found_count', 0)} found, ")
            f.write(f"{response.get('not_found_count', 0)} not found")
            
            if 'token_usage' in response:
                usage = response['token_usage']
                f.write(f" | Tokens: {usage.get('input_tokens', 0)}+{usage.get('output_tokens', 0)}")
                f.write(f" | Cost: ${usage.get('total_cost', 0):.6f}")
            
            f.write(f" | Status: {response.get('status', 'unknown')}\n")
    
    print(f"📄 Summary report saved to: {summary_path}")
    return summary_path

if __name__ == "__main__":
    print("🚀 Starting Response Combination Script")
    print("=" * 50)
    
    # Combine all responses
    combined_file = combine_all_responses()
    
    if combined_file:
        # Create summary report
        summary_file = create_summary_report(combined_file)
        
        print("\n" + "=" * 50)
        print("✅ All done! Files created:")
        print(f"   Combined JSON: {combined_file}")
        print(f"   Summary Report: {summary_file}")
        print("\n🎯 You can now:")
        print("   1. Open the combined JSON file to see all responses")
        print("   2. Check the summary report for quick overview")
        print("   3. Use the combined JSON for further analysis")
    else:
        print("\n❌ Failed to create combined file") 