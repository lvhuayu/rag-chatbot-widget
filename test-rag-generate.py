#!/usr/bin/env python3
import requests
import json

def test_rag_generate():
    url = "http://localhost:8001/rag-generate"
    payload = {
        "query": "收费方案",
        "user_id": "main_page_user",
        "top_k": 3
    }
    
    try:
        print("🔗 Sending request to RAG generate endpoint...")
        response = requests.post(url, json=payload, timeout=60)  # 增加超时时间到60秒
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ RAG Generate Response:")
            print(f"Context: {data.get('context', 'No context')[:200]}...")  # 只显示前200个字符
            print(f"Documents found: {len(data.get('documents', []))}")
            
            for i, doc in enumerate(data.get('documents', [])):
                print(f"  Document {i+1}: {doc['document']['title']} (similarity: {doc['similarity']:.3f})")
        else:
            print(f"❌ Error: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out (60 seconds)")
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_rag_generate() 