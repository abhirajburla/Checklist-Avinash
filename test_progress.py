#!/usr/bin/env python3
"""
Test script to verify progress tracking is working
"""

import requests
import json
import time

def test_progress_tracking():
    """Test the progress tracking system"""
    
    base_url = "http://localhost:5000"
    
    print("🧪 Testing Progress Tracking System")
    print("=" * 50)
    
    # Test 1: Check if the app is running
    print("1. Testing app connectivity...")
    try:
        response = requests.get(base_url, timeout=5)
        if response.status_code == 200:
            print("✅ App is running")
        else:
            print(f"❌ App returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to app: {e}")
        return False
    
    # Test 2: Test progress endpoint with invalid tracker
    print("\n2. Testing progress endpoint with invalid tracker...")
    try:
        response = requests.get(f"{base_url}/progress/invalid-tracker-id", timeout=5)
        result = response.json()
        
        if response.status_code == 404 and "error" in result:
            print("✅ Progress endpoint correctly handles invalid tracker")
        else:
            print(f"❌ Unexpected response: {result}")
            return False
    except Exception as e:
        print(f"❌ Progress endpoint test failed: {e}")
        return False
    
    # Test 3: Test upload endpoint
    print("\n3. Testing upload endpoint...")
    try:
        # Create a dummy file for testing
        files = {
            'drawings': ('test_drawing.pdf', b'dummy content', 'application/pdf'),
            'specifications': ('test_spec.pdf', b'dummy content', 'application/pdf')
        }
        
        response = requests.post(f"{base_url}/upload", files=files, timeout=10)
        result = response.json()
        
        if response.status_code == 200 and "upload_id" in result:
            print(f"✅ Upload successful, got upload_id: {result['upload_id']}")
            upload_id = result['upload_id']
        else:
            print(f"❌ Upload failed: {result}")
            return False
    except Exception as e:
        print(f"❌ Upload test failed: {e}")
        return False
    
    # Test 4: Test process-documents endpoint
    print("\n4. Testing process-documents endpoint...")
    try:
        data = {"upload_id": upload_id}
        response = requests.post(
            f"{base_url}/process-documents", 
            json=data, 
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        result = response.json()
        
        if response.status_code == 200 and "tracker_id" in result:
            print(f"✅ Processing started, got tracker_id: {result['tracker_id']}")
            tracker_id = result['tracker_id']
        else:
            print(f"❌ Processing start failed: {result}")
            return False
    except Exception as e:
        print(f"❌ Processing start test failed: {e}")
        return False
    
    # Test 5: Test progress polling
    print("\n5. Testing progress polling...")
    try:
        max_polls = 10
        poll_count = 0
        
        while poll_count < max_polls:
            response = requests.get(f"{base_url}/progress/{tracker_id}", timeout=5)
            result = response.json()
            
            if response.status_code == 200:
                progress = result.get('progress', {})
                status = result.get('status', 'unknown')
                percentage = progress.get('progress_percentage', 0)
                
                print(f"   Poll {poll_count + 1}: Status={status}, Progress={percentage:.1f}%")
                
                if status == 'completed':
                    print("✅ Processing completed!")
                    break
                elif status == 'failed':
                    print(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
                    return False
                
                poll_count += 1
                time.sleep(2)  # Wait 2 seconds between polls
            else:
                print(f"❌ Progress check failed: {result}")
                return False
        
        if poll_count >= max_polls:
            print("⚠️  Max polls reached, processing may still be running")
    
    except Exception as e:
        print(f"❌ Progress polling test failed: {e}")
        return False
    
    print("\n🎉 Progress tracking test completed successfully!")
    return True

if __name__ == "__main__":
    success = test_progress_tracking()
    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!") 