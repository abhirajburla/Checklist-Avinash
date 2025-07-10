#!/usr/bin/env python3
"""
Test script to see exactly what content Gemini extracts from uploaded PDF files
"""

import os
import sys
import logging
from pathlib import Path

# Add the src directory to the path
sys.path.append(str(Path(__file__).parent / "src"))

from gemini_client import GeminiClient
from config import Config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_document_content():
    """Test what content Gemini extracts from uploaded documents"""
    
    print("=== TESTING GEMINI DOCUMENT CONTENT EXTRACTION ===\n")
    
    # Initialize Gemini client
    client = GeminiClient()
    
    # Check if uploads directory exists
    uploads_dir = Path("uploads")
    if not uploads_dir.exists():
        print("❌ Uploads directory not found!")
        return
    
    # Find PDF files in uploads subdirectories
    pdf_files = []
    for subdir in uploads_dir.iterdir():
        if subdir.is_dir():
            subdir_pdfs = list(subdir.glob("*.pdf"))
            pdf_files.extend(subdir_pdfs)
    
    if not pdf_files:
        print("❌ No PDF files found in uploads subdirectories!")
        return
    
    print(f"📁 Found {len(pdf_files)} PDF files:")
    for pdf_file in pdf_files:
        print(f"   - {pdf_file.name}")
    
    print(f"\n📤 Uploading {len(pdf_files)} files to Gemini...")
    
    # Upload files to Gemini
    file_paths = [str(f) for f in pdf_files]
    upload_result = client.upload_documents(file_paths)
    
    if not upload_result.get("success"):
        print(f"❌ Upload failed: {upload_result.get('error')}")
        return
    
    cache_id = upload_result["cache_id"]
    print(f"✅ Files uploaded successfully with cache ID: {cache_id}")
    
    # Test 1: Ask Gemini to describe what it sees in the documents
    print(f"\n🔍 TEST 1: Asking Gemini to describe the documents...")
    
    try:
        # Create a simple prompt to extract document content
        prompt = """
Please analyze the uploaded documents and provide a detailed description of what you can see and read.

For each document, please include:
1. Document type (drawing, specification, etc.)
2. Any text content you can read
3. Any sheet numbers, titles, or identifiers
4. Any specification codes or section numbers
5. Any technical details or requirements
6. Any drawings, diagrams, or visual elements you can describe

Be very specific and include exact text, numbers, and details that you can see in the documents.
"""
        
        # Get the model
        import google.generativeai as genai
        genai.configure(api_key=Config().GEMINI_API_KEY)
        model = genai.GenerativeModel(model_name=Config().GEMINI_MODEL)
        
        # Create contents array with files and prompt
        uploaded_files = client.context_cache[cache_id]
        contents = []
        
        # Add all uploaded files to contents
        for file_info in uploaded_files:
            print(f"   📄 Processing: {file_info['file_name']}")
            contents.append(file_info['gemini_file'])
        
        # Add the prompt as the last element
        contents.append(prompt)
        
        # Send the analysis prompt
        print("   🤖 Sending analysis prompt to Gemini...")
        response = model.generate_content(contents)
        
        print(f"\n📋 GEMINI'S RESPONSE:")
        print("=" * 80)
        print(response.text)
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Error in Test 1: {e}")
    
    # Test 2: Ask Gemini to extract specific information
    print(f"\n🔍 TEST 2: Asking Gemini to extract specific document information...")
    
    try:
        specific_prompt = """
Please extract the following specific information from the uploaded documents:

1. SHEET NUMBERS: List any sheet numbers you can find (e.g., A-1, S-01, etc.)
2. SPECIFICATION CODES: List any specification section codes (e.g., 03 30 00, etc.)
3. DOCUMENT TITLES: List any document titles or names
4. PROJECT INFORMATION: Any project name, location, or identification
5. TECHNICAL SPECIFICATIONS: Any specific technical requirements or details
6. DRAWING ELEMENTS: Any architectural, structural, or technical elements shown

Please be extremely precise and only include information that is actually visible in the documents. If you cannot find specific information, say "NOT FOUND" rather than making assumptions.
"""
        
        # Create contents array with files and specific prompt
        contents = []
        for file_info in uploaded_files:
            contents.append(file_info['gemini_file'])
        contents.append(specific_prompt)
        
        response2 = model.generate_content(contents)
        
        print(f"\n📋 SPECIFIC INFORMATION EXTRACTION:")
        print("=" * 80)
        print(response2.text)
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Error in Test 2: {e}")
    
    # Test 3: Ask Gemini to list all text content
    print(f"\n🔍 TEST 3: Asking Gemini to list all readable text content...")
    
    try:
        text_prompt = """
Please list ALL the text content you can read from the uploaded documents. 

Include:
- Every word, number, and symbol you can see
- Any labels, notes, or annotations
- Any specifications or requirements
- Any drawing titles or sheet information
- Any technical details or measurements

Please format this as a simple list of all readable text, organized by document if possible. Be as comprehensive as possible and include exact text as it appears.
"""
        
        # Create contents array with files and text prompt
        contents = []
        for file_info in uploaded_files:
            contents.append(file_info['gemini_file'])
        contents.append(text_prompt)
        
        response3 = model.generate_content(contents)
        
        print(f"\n📋 ALL READABLE TEXT CONTENT:")
        print("=" * 80)
        print(response3.text)
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Error in Test 3: {e}")
    
    print(f"\n✅ Document content extraction test completed!")
    print(f"💡 This will help us understand what Gemini actually sees vs. what it hallucinates")

if __name__ == "__main__":
    test_document_content() 