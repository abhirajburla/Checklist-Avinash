#!/usr/bin/env python3
"""
Test script to verify the JSON parsing fix
"""

import requests
import json
import time

def test_upload_and_process():
    """Test the upload and processing workflow"""
    
    base_url = "http://localhost:5000"
    
    print("=== Testing Upload and Processing ===")
    
    # Test 1: Upload files
    print("\n1. Uploading files...")
    upload_url = f"{base_url}/upload"
    
    # Use the test files in uploads directory
    files = {
        'drawings': ('drawing.pdf', open('uploads/0ed232ce-47fa-42df-ad00-551f3167afe1/Input - Construction Drawing one page.pdf', 'rb')),
        'specifications': ('spec.pdf', open('uploads/0ed232ce-47fa-42df-ad00-551f3167afe1/Input - Specifications few pages.pdf', 'rb'))
    }
    
    try:
        response = requests.post(upload_url, files=files)
        response.raise_for_status()
        upload_result = response.json()
        upload_id = upload_result['upload_id']
        print(f"✅ Upload successful - Upload ID: {upload_id}")
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return
    
    # Test 2: Process documents
    print("\n2. Processing documents...")
    process_url = f"{base_url}/process-documents"
    process_data = {"upload_id": upload_id}
    
    try:
        response = requests.post(process_url, json=process_data)
        response.raise_for_status()
        process_result = response.json()
        tracker_id = process_result['tracker_id']
        process_id = process_result['process_id']
        print(f"✅ Processing started - Tracker ID: {tracker_id}")
        print(f"   Process ID: {process_id}")
        print(f"   Total items: {process_result['total_items']}")
    except Exception as e:
        print(f"❌ Processing failed: {e}")
        return
    
    # Test 3: Monitor progress
    print("\n3. Monitoring progress...")
    progress_url = f"{base_url}/progress/{tracker_id}"
    
    max_wait = 120  # 2 minutes
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(progress_url)
            response.raise_for_status()
            progress_result = response.json()
            
            status = progress_result['status']
            progress = progress_result['progress']
            
            print(f"   Status: {status}, Progress: {progress['progress_percentage']}% ({progress['items_processed']}/{progress['total_items']})")
            
            if status == 'completed':
                print("✅ Processing completed!")
                break
            elif status == 'failed':
                error = progress_result.get('error', 'Unknown error')
                print(f"❌ Processing failed: {error}")
                return
            
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ Progress check failed: {e}")
            return
    
    if time.time() - start_time >= max_wait:
        print("❌ Processing timed out")
        return
    
    # Test 4: Get results
    print("\n4. Getting results...")
    results_url = f"{base_url}/results/{process_id}"
    
    try:
        response = requests.get(results_url)
        response.raise_for_status()
        results = response.json()
        
        print(f"✅ Results retrieved successfully!")
        print(f"   Total items: {results['total_items']}")
        print(f"   Found items: {results['found_items']}")
        print(f"   Not found items: {results['not_found_items']}")
        
        # Check if we have the expected results
        if results['found_items'] > 0:
            print("✅ SUCCESS: Found items are now showing in results!")
            
            # Show first few found items
            found_items = [item for item in results['results'] if item.get('found', False)]
            print(f"\n   First found item:")
            if found_items:
                item = found_items[0]
                print(f"   - Checklist: {item['checklist'][:100]}...")
                print(f"   - Spec Section: {item['spec_section']}")
                print(f"   - Notes: {item['notes'][:100]}...")
        else:
            print("❌ FAILURE: No found items in results")
            
    except Exception as e:
        print(f"❌ Results retrieval failed: {e}")

if __name__ == "__main__":
    test_upload_and_process() 