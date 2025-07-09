#!/usr/bin/env python3
"""
Test script for the Python backend /documents endpoint with site_id
"""
import requests
import json

# First, let's get the site_id for user lvhuayu02 by checking the database
# We'll use the same site_id that was used in the upload test
SITE_ID = "cmctk4mpt000290ufe1"  # This was from the log message you showed
PYTHON_BACKEND_URL = "http://localhost:8001"

def test_documents_endpoint():
    """Test the Python backend /documents endpoint with site_id"""
    
    try:
        # Test with site_id parameter
        response = requests.get(
            f"{PYTHON_BACKEND_URL}/documents?site_id={SITE_ID}",
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success! Found {len(result)} documents")
            for i, doc in enumerate(result, 1):
                print(f"  {i}. {doc.get('title', 'No title')}")
        else:
            print(f"❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_documents_with_user_id():
    """Test the Python backend /documents endpoint with user_id (old way)"""
    
    try:
        # Test with user_id parameter (old way)
        response = requests.get(
            f"{PYTHON_BACKEND_URL}/documents?user_id={SITE_ID}",
            timeout=30
        )
        
        print(f"\nStatus Code (user_id): {response.status_code}")
        print(f"Response (user_id): {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success with user_id! Found {len(result)} documents")
        else:
            print(f"❌ Error with user_id: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exception with user_id: {e}")

if __name__ == "__main__":
    print("🧪 Testing Python backend /documents endpoint...")
    print("=" * 60)
    
    test_documents_endpoint()
    test_documents_with_user_id()
    
    print("\n" + "=" * 60)
    print("✅ Test completed!") 