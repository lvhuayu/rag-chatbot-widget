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
        {"query": "资费", "site_id": "cmctxu8p90002l0ufb1894lfi", "threshold": 0.1, "top_k": 5},
        {"query": "收费方案", "site_id": "cmctxu8p90002l0ufb1894lfi", "threshold": 0.1, "top_k": 5},
        {"query": "价格", "site_id": "cmctxu8p90002l0ufb1894lfi", "threshold": 0.1, "top_k": 5},
        {"query": "月费", "site_id": "cmctxu8p90002l0ufb1894lfi", "threshold": 0.1, "top_k": 5}
    ]
    
    for i, test_case in enumerate(test_queries, 1):
        query = test_case["query"]
        site_id = test_case["site_id"]
        threshold = test_case["threshold"]
        top_k = test_case["top_k"]
        
        print(f"\n🔍 Test {i}: {query}")
        print(f"  {{")
        print(f"    \"query\": \"{query}\",")
        print(f"    \"site_id\": \"{site_id}\",")
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

API_KEY = "cmctxu8p90002l0ufb1894lfi"

# 获取 JWT token
def get_token(api_key):
    url = "http://localhost:8001/auth/token"
    headers = {"Content-Type": "application/json"}
    data = {"apiKey": api_key}
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=5)
        if resp.status_code == 200:
            token = resp.json().get("token")
            print(f"[Token] Got JWT token: {token[:20]}...\n")
            return token
        else:
            print(f"[Token] Failed to get token: {resp.status_code} {resp.text}")
            return None
    except Exception as e:
        print(f"[Token] Exception: {e}")
        return None

def test_rag_generate(token):
    url = "http://localhost:8001/rag-generate"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    test_queries = [
        {"query": "资费", "top_k": 5, "threshold": 0.1},
        {"query": "收费方案", "top_k": 5, "threshold": 0.1},
        {"query": "价格", "top_k": 5, "threshold": 0.1},
        {"query": "月费", "top_k": 5, "threshold": 0.1}
    ]
    for i, test_case in enumerate(test_queries, 1):
        print(f"\n🔍 Test {i}: {test_case['query']}")
        print(f"  {{")
        for k, v in test_case.items():
            print(f"    \"{k}\": {json.dumps(v)}")
        print(f"  }}")
        try:
            resp = requests.post(url, headers=headers, json=test_case, timeout=20)
            print(f"Status Code: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
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
                print(f"Error: {resp.status_code}")
                print(f"Response: {resp.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    print("🔍 Testing backend endpoints...")
    test_health()
    print("\n" + "="*50)
    token = get_token(API_KEY)
    if token:
        test_rag_generate(token)
    else:
        print("❌ Failed to get token, cannot test /rag-generate endpoint.") 