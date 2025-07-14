#!/usr/bin/env python3
"""
Combine all Gemini response files for a given session or process.
Trims unnecessary metadata and outputs a clean combined JSON and summary report.
Usage:
    python combine_session_responses.py --session-id <SESSION_ID>
    python combine_session_responses.py --process-id <PROCESS_ID>
"""

import json
import os
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

def parse_args():
    parser = argparse.ArgumentParser(description="Combine Gemini responses for a session or process.")
    parser.add_argument('--session-id', type=str, help='Session ID to match (UUID or timestamp-based)')
    parser.add_argument('--process-id', type=str, help='Process ID to match (if available)')
    return parser.parse_args()

def matches_criteria(metadata: Dict[str, Any], session_id: Optional[str] = None, process_id: Optional[str] = None) -> bool:
    if session_id and session_id in str(metadata.get('session_id', '')):
        return True
    if process_id and process_id in str(metadata.get('process_id', '')):
        return True
    return False

def combine_session_responses(session_id: str = None, process_id: str = None):
    responses_dir = Path("json_outputs/responses")
    failed_dir = Path("json_outputs/failed")
    output_dir = Path("json_outputs/combined")
    output_dir.mkdir(exist_ok=True)

    print(f"🔍 Scanning for response files matching session_id={session_id} process_id={process_id}")
    all_files = []
    for folder, status in [(responses_dir, "successful"), (failed_dir, "failed")]:
        if folder.exists():
            for file_path in folder.glob("*.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    metadata = data.get("metadata", {})
                    match = False
                    if session_id is not None:
                        match = matches_criteria(metadata, session_id=session_id)
                    if not match and process_id is not None:
                        match = matches_criteria(metadata, process_id=process_id)
                    if match:
                        all_files.append((file_path, status, data))
                except Exception as e:
                    print(f"❌ Error reading {file_path.name}: {e}")

    if not all_files:
        print("❌ No matching response files found!")
        return None, None

    # Sort by batch number
    def get_sort_key(file_info):
        file_path, _, data = file_info
        return data.get("metadata", {}).get("batch_index", 0)
    all_files.sort(key=get_sort_key)

    print(f"Found {len(all_files)} matching response files.")

    # Combine and trim
    combined_data = {
        "metadata": {
            "combined_at": datetime.now().isoformat(),
            "session_id": session_id,
            "process_id": process_id,
            "total_files": len(all_files),
            "successful_files": len([1 for _, status, _ in all_files if status == "successful"]),
            "failed_files": len([1 for _, status, _ in all_files if status == "failed"]),
            "total_batches": len(set([get_sort_key(f) for f in all_files]))
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

    for file_path, status, data in all_files:
        clean_response = {
            "file_name": file_path.name,
            "status": status,
            "batch_index": data.get("metadata", {}).get("batch_index", 0),
            "timestamp": data.get("metadata", {}).get("timestamp", ""),
            "operation": data.get("metadata", {}).get("operation", "unknown")
        }
        response_text = data.get("response_text", "")
        try:
            cleaned_text = response_text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            cleaned_text = cleaned_text.strip()
            gemini_response = json.loads(cleaned_text)
            matches = gemini_response.get("matches", [])
            total_items = gemini_response.get("total_items", len(matches))
            found_count = gemini_response.get("found_count", 0)
            not_found_count = gemini_response.get("not_found_count", 0)
            total_items_processed += total_items
            total_items_found += found_count
            total_items_not_found += not_found_count
            clean_response.update({
                "total_items": total_items,
                "found_count": found_count,
                "not_found_count": not_found_count,
                "matches": matches,
                "parsed_successfully": True
            })
        except Exception as e:
            clean_response.update({
                "raw_response": response_text,
                "parse_error": str(e),
                "parsed_successfully": False
            })
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

    combined_data["summary"].update({
        "total_tokens_used": total_tokens,
        "total_cost": total_cost,
        "total_items_processed": total_items_processed,
        "total_items_found": total_items_found,
        "total_items_not_found": total_items_not_found,
        "success_rate": (total_items_found / total_items_processed * 100) if total_items_processed > 0 else 0.0
    })

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"session_responses_combined_{timestamp}.json"
    output_path = output_dir / output_filename
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(combined_data, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Combined JSON saved to: {output_path}")

    # Optionally, create a summary report
    summary_path = output_dir / f"session_summary_report_{timestamp}.txt"
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(f"Session: {session_id}\nProcess: {process_id}\n")
        f.write(f"Generated: {combined_data['metadata']['combined_at']}\n")
        f.write(f"Total files processed: {combined_data['metadata']['total_files']}\n")
        f.write(f"Successful files: {combined_data['metadata']['successful_files']}\n")
        f.write(f"Failed files: {combined_data['metadata']['failed_files']}\n")
        f.write(f"Total batches: {combined_data['metadata']['total_batches']}\n\n")
        f.write(f"Total tokens used: {combined_data['summary']['total_tokens_used']:,}\n")
        f.write(f"Total cost: ${combined_data['summary']['total_cost']:.6f}\n")
        f.write(f"Total items processed: {combined_data['summary']['total_items_processed']}\n")
        f.write(f"Items found: {combined_data['summary']['total_items_found']}\n")
        f.write(f"Items not found: {combined_data['summary']['total_items_not_found']}\n")
        f.write(f"Success rate: {combined_data['summary']['success_rate']:.2f}%\n\n")
        f.write("BATCH DETAILS:\n")
        for response in combined_data['responses']:
            f.write(f"Batch {response.get('batch_index', 'N/A')}: ")
            f.write(f"{response.get('found_count', 0)} found, ")
            f.write(f"{response.get('not_found_count', 0)} not found")
            if 'token_usage' in response:
                usage = response['token_usage']
                f.write(f" | Tokens: {usage.get('input_tokens', 0)}+{usage.get('output_tokens', 0)}")
                f.write(f" | Cost: ${usage.get('total_cost', 0):.6f}")
            f.write(f" | Status: {response.get('status', 'unknown')}\n")
    print(f"📄 Summary report saved to: {summary_path}")
    return output_path, summary_path

if __name__ == "__main__":
    args = parse_args()
    if not args.session_id and not args.process_id:
        print("❌ Please provide --session-id or --process-id.")
    else:
        combine_session_responses(session_id=args.session_id, process_id=args.process_id) 