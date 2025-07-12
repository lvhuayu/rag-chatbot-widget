#!/usr/bin/env python3
"""
Test script for Unicode character handling in Prisma backend
"""

import requests
import json

def test_unicode_upload():
    """Test uploading a document with Unicode characters"""
    
    # Test data with Unicode characters
    test_data = [{
        "url": "test://unicode-test",
        "title": "Unicode Test Document",
        "content": "This document contains Unicode characters like → ← ↑ ↓ and emojis 🚀 📚 🔍",
        "site_id": "cmcu4th0h0004woufa9gh58wn"
    }]
    
    try:
        # Send POST request to add document
        response = requests.post(
            "http://localhost:8001/add-documents",
            headers={"Content-Type": "application/json"},
            json=test_data,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success! Document ID: {result.get('doc_id')}")
            print(f"Action: {result.get('action')}")
            print(f"Message: {result.get('message')}")
        else:
            print(f"❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_search():
    """Test searching for the uploaded document"""
    
    search_data = {
        "query": "Unicode characters",
        "user_id": "testuser",
        "top_k": 3,
        "threshold": 0.0
    }
    
    try:
        response = requests.post(
            "http://localhost:8001/search",
            headers={"Content-Type": "application/json"},
            json=search_data,
            timeout=30
        )
        
        print(f"\nSearch Status Code: {response.status_code}")
        print(f"Search Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Search successful!")
            print(f"Context: {result.get('context', 'No context')}")
            print(f"Documents found: {len(result.get('documents', []))}")
        else:
            print(f"❌ Search error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Search exception: {e}")

if __name__ == "__main__":
    print("🧪 Testing Unicode character handling in Prisma backend...")
    print("=" * 60)
    
    test_unicode_upload()
    test_search()
    
    print("\n" + "=" * 60)
    print("✅ Test completed!") 