#!/usr/bin/env python3
"""
Test script for JSONL to Embeddings Import API
"""

import requests
import json
import base64
import os
from pathlib import Path

# Configuration
API_BASE_URL = "http://localhost:8001"
JSONL_FILE_PATH = "rag_scraper/playwright_langchain_loader/output/rag_chunks.jsonl"

# Test data (you can replace this with actual authentication)
TEST_TOKEN = "your-test-token-here"  # Replace with actual JWT token
TEST_SITE_ID = "test-site-123"  # Replace with actual site ID

def test_health_check():
    """Test API health check"""
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        print("✅ Health check:", response.json())
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_import_jsonl_file():
    """Test importing JSONL file"""
    if not os.path.exists(JSONL_FILE_PATH):
        print(f"❌ JSONL file not found: {JSONL_FILE_PATH}")
        return False
    
    try:
        # Read JSONL file
        with open(JSONL_FILE_PATH, 'r', encoding='utf-8') as f:
            jsonl_content = f.read()
        
        # Prepare headers with authentication
        headers = {
            "Authorization": f"Bearer {TEST_TOKEN}"
        }
        
        # Prepare form data
        files = {
            'file': ('rag_chunks.jsonl', jsonl_content, 'application/json')
        }
        data = {
            'site_id': TEST_SITE_ID
        }
        
        # Make request
        response = requests.post(
            f"{API_BASE_URL}/import-jsonl-file",
            headers=headers,
            files=files,
            data=data
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Import successful:")
            print(f"   Imported: {result['imported_count']} documents")
            print(f"   Errors: {len(result['errors'])}")
            print(f"   Message: {result['message']}")
            
            if result['errors']:
                print("   Error details:")
                for error in result['errors'][:5]:  # Show first 5 errors
                    print(f"     - {error}")
            
            return True
        else:
            print(f"❌ Import failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def test_import_jsonl_content():
    """Test importing JSONL content directly"""
    try:
        # Sample JSONL content
        sample_jsonl = """{"text": "This is a test document about RAG systems.", "metadata": {"url": "https://example.com/test1", "title": "Test Document 1", "source": "test"}}
{"text": "Another test document about embeddings and vector search.", "metadata": {"url": "https://example.com/test2", "title": "Test Document 2", "source": "test"}}"""
        
        # Encode to base64
        jsonl_b64 = base64.b64encode(sample_jsonl.encode('utf-8')).decode('utf-8')
        
        # Prepare request
        headers = {
            "Authorization": f"Bearer {TEST_TOKEN}",
            "Content-Type": "application/json"
        }
        
        data = {
            "site_id": TEST_SITE_ID,
            "jsonl_content": jsonl_b64
        }
        
        # Make request
        response = requests.post(
            f"{API_BASE_URL}/import-jsonl",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Content import successful:")
            print(f"   Imported: {result['imported_count']} documents")
            print(f"   Errors: {len(result['errors'])}")
            return True
        else:
            print(f"❌ Content import failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Content import test failed: {e}")
        return False

def test_get_stats():
    """Test getting import statistics"""
    try:
        headers = {
            "Authorization": f"Bearer {TEST_TOKEN}"
        }
        
        response = requests.get(
            f"{API_BASE_URL}/stats/{TEST_SITE_ID}",
            headers=headers
        )
        
        if response.status_code == 200:
            stats = response.json()
            print("✅ Stats retrieved:")
            print(f"   Site ID: {stats['site_id']}")
            print(f"   Stats: {json.dumps(stats['stats'], indent=2)}")
            return True
        else:
            print(f"❌ Stats failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Stats test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing JSONL to Embeddings Import API")
    print("=" * 50)
    
    # Check if API is running
    if not test_health_check():
        print("❌ API is not running. Please start the server first:")
        print("   cd backend")
        print("   python import_jsonl_to_embeddings.py")
        return
    
    print("\n📁 Testing file import...")
    test_import_jsonl_file()
    
    print("\n📝 Testing content import...")
    test_import_jsonl_content()
    
    print("\n📊 Testing stats...")
    test_get_stats()
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    main() 