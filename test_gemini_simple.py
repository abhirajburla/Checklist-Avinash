#!/usr/bin/env python3
"""
Simple test to check if Gemini API is working
"""

import os
import sys
import time
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from gemini_client import GeminiClient

def test_gemini_basic():
    """Test basic Gemini API functionality"""
    print("=== TESTING GEMINI API BASIC FUNCTIONALITY ===")
    
    try:
        # Initialize client
        print("1. Initializing Gemini client...")
        client = GeminiClient()
        print("✅ Gemini client initialized successfully")
        
        # Test simple text generation
        print("\n2. Testing simple text generation...")
        start_time = time.time()
        
        # Simple prompt
        simple_prompt = "Hello, can you respond with 'Gemini API is working' if you can see this message?"
        
        print(f"Sending simple prompt: {simple_prompt}")
        
        # Use ThreadPoolExecutor with timeout
        import concurrent.futures
        
        def send_simple_message():
            try:
                import google.generativeai as genai
                genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
                model = genai.GenerativeModel('gemini-2.5-pro')
                response = model.generate_content(simple_prompt)
                return response.text
            except Exception as e:
                return f"Error: {e}"
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(send_simple_message)
            try:
                result = future.result(timeout=30)  # 30 second timeout
                elapsed_time = time.time() - start_time
                print(f"✅ Gemini API responded in {elapsed_time:.2f} seconds")
                print(f"Response: {result}")
                return True
            except concurrent.futures.TimeoutError:
                print("❌ Gemini API call timed out after 30 seconds")
                return False
            except Exception as e:
                print(f"❌ Error calling Gemini API: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Error initializing Gemini client: {e}")
        return False

def test_gemini_file_upload():
    """Test Gemini file upload functionality"""
    print("\n=== TESTING GEMINI FILE UPLOAD ===")
    
    try:
        # Initialize client
        print("1. Initializing Gemini client...")
        client = GeminiClient()
        print("✅ Gemini client initialized successfully")
        
        # Search for PDF files in current directory and uploads/
        test_files = []
        # Check root
        for file in os.listdir("."):
            if file.endswith(".pdf"):
                test_files.append(file)
        # Check uploads/
        uploads_dir = "uploads"
        if os.path.isdir(uploads_dir):
            for subdir, _, files in os.walk(uploads_dir):
                for file in files:
                    if file.endswith(".pdf"):
                        test_files.append(os.path.join(subdir, file))
        
        if not test_files:
            print("❌ No PDF files found in current directory or uploads/")
            print("Available files:", [f for f in os.listdir(".") if os.path.isfile(f)])
            if os.path.isdir(uploads_dir):
                print("Files in uploads/:", [os.path.join(dp, f) for dp, dn, filenames in os.walk(uploads_dir) for f in filenames])
            return False
            
        test_file = test_files[0]  # Use first PDF file found
        print(f"2. Testing file upload with {test_file}...")
        start_time = time.time()
        
        # Test file upload
        result = client.upload_documents([test_file])
        
        elapsed_time = time.time() - start_time
        print(f"✅ File upload completed in {elapsed_time:.2f} seconds")
        print(f"Upload result: {result}")
        
        if result.get("success"):
            cache_id = result.get("cache_id")
            print(f"Cache ID: {cache_id}")
            return True
        else:
            print(f"❌ File upload failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing file upload: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("Starting Gemini API tests...")
    print(f"GEMINI_API_KEY set: {'Yes' if os.getenv('GEMINI_API_KEY') else 'No'}")
    
    # Test 1: Basic API functionality
    basic_works = test_gemini_basic()
    
    # Test 2: File upload functionality
    upload_works = test_gemini_file_upload()
    
    # Summary
    print("\n=== TEST SUMMARY ===")
    print(f"Basic API functionality: {'✅ PASS' if basic_works else '❌ FAIL'}")
    print(f"File upload functionality: {'✅ PASS' if upload_works else '❌ FAIL'}")
    
    if basic_works and upload_works:
        print("\n🎉 All tests passed! Gemini API is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main() 