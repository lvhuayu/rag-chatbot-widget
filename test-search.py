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
    
    # 测试多个查询
    test_queries = [
        {"query": "资费", "user_id": "main_page_user", "threshold": 0.1, "top_k": 5},
        {"query": "收费方案", "user_id": "main_page_user", "threshold": 0.1, "top_k": 5},
        {"query": "价格", "user_id": "main_page_user", "threshold": 0.1, "top_k": 5},
        {"query": "月费", "user_id": "main_page_user", "threshold": 0.1, "top_k": 5}
    ]
    
    for i, test_case in enumerate(test_queries, 1):
        query = test_case["query"]
        user_id = test_case["user_id"]
        threshold = test_case["threshold"]
        top_k = test_case["top_k"]
        
        print(f"\n🔍 Test {i}: {query}")
        print(f"  {{")
        print(f"    \"query\": \"{query}\",")
        print(f"    \"user_id\": \"{user_id}\",")
        print(f"    \"threshold\": {threshold},")
        print(f"    \"top_k\": {top_k}")
        print(f"  }}")
        
        try:
            response = requests.post(url, headers=headers, json=test_case, timeout=10)
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                documents = data.get('documents', [])
                context = data.get('context', '')
                
                print(f"Documents found: {len(documents)}")
                
                if context:
                    print(f"\n📝 Full Context:")
                    print(context)
                else:
                    print("❌ No context found")
                    
                for j, doc in enumerate(documents, 1):
                    similarity = doc.get('similarity', 0)
                    title = doc.get('document', {}).get('title', 'No title')
                    print(f"  {j}. {title} (相似度: {similarity:.3f})")
                    
            else:
                print(f"Error: {response.status_code}")
                print(f"Response: {response.text}")
                
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