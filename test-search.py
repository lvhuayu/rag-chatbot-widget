#!/usr/bin/env python3
"""
Test script to debug the search endpoint
"""

import requests
import json

def test_search():
    """Test the search endpoint"""
    
    url = "http://localhost:8001/search"
    headers = {"Content-Type": "application/json"}
    data = {
        "query": "网站功能",
        "user_id": "main_page_user",
        "threshold": 0.05
    }
    
    try:
        print(f"Testing search endpoint: {url}")
        print(f"Data: {json.dumps(data, indent=2)}")
        
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
        else:
            print(f"Error Response: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

def test_health():
    """Test the health endpoint"""
    
    try:
        response = requests.get("http://localhost:8001/health", timeout=5)
        print(f"Health Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Health Response: {response.json()}")
    except Exception as e:
        print(f"Health Error: {e}")

if __name__ == "__main__":
    print("🔍 Testing backend endpoints...")
    test_health()
    print("\n" + "="*50)
    test_search() 