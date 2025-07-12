#!/usr/bin/env python3
"""
Test context length and content
"""

import requests
import json

def test_context_length():
    """测试context的完整长度和内容"""
    print("🔍 Testing context length and content...")
    
    # 测试查询
    test_query = {
        "query": "收费方案",
        "user_id": "main_page_user",
        "threshold": 0.1,
        "top_k": 5
    }
    
    try:
        response = requests.post("http://localhost:8001/search", 
                               json=test_query,
                               timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            context = result.get('context', '')
            documents = result.get('documents', [])
            
            print(f"📊 Query: {test_query['query']}")
            print(f"📏 Context length: {len(context)} characters")
            print(f"📄 Number of documents: {len(documents)}")
            
            print(f"\n📝 Full context content:")
            print("="*60)
            print(context)
            print("="*60)
            
            # 显示每个文档的内容
            for i, doc in enumerate(documents):
                print(f"\n📄 Document {i+1}:")
                print(f"Title: {doc['document']['title']}")
                print(f"Similarity: {doc['similarity']:.3f}")
                print(f"Content length: {len(doc['document']['content'])}")
                print(f"Content: {doc['document']['content'][:200]}...")
                
        else:
            print(f"❌ Search failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_context_length() 