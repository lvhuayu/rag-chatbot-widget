#!/usr/bin/env python3
"""
Test nonsense query rejection
"""

import requests
import json

def test_nonsense_query():
    """Test if nonsense queries are properly rejected"""
    
    url = "http://localhost:8001/search"
    headers = {"Content-Type": "application/json"}
    data = {
        "query": "adsfadf",
        "user_id": "cmcr0plai0006ufg8pmqchjyt",
        "threshold": 0.3
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        result = response.json()
        
        print(f"Status: {response.status_code}")
        print(f"Documents returned: {len(result.get('documents', []))}")
        print(f"Context: {result.get('context', 'No context')}")
        
        if result.get('documents'):
            print("❌ Nonsense query returned results (should be rejected)")
        else:
            print("✅ Nonsense query properly rejected")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_nonsense_query() 