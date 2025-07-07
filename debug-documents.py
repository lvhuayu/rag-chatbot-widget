#!/usr/bin/env python3
"""
Debug script to view documents and analyze similarity calculations
"""

import requests
import json
from typing import List, Dict, Any

def get_documents(user_id: str = "main_page_user") -> List[Dict[str, Any]]:
    """获取指定用户的文档"""
    try:
        response = requests.get(f"http://localhost:8001/documents?user_id={user_id}", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error getting documents: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error: {e}")
        return []

def test_similarity_for_query(query: str, user_id: str = "main_page_user", threshold: float = 0.1):
    """测试特定查询的相似度计算"""
    try:
        response = requests.post("http://localhost:8001/search", 
                               json={
                                   "query": query,
                                   "user_id": user_id,
                                   "threshold": threshold,
                                   "top_k": 10
                               },
                               timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n🔍 Query: '{query}'")
            print(f"📊 Found {len(data.get('documents', []))} documents")
            
            for i, doc in enumerate(data.get('documents', []), 1):
                similarity = doc.get('similarity', 0)
                title = doc.get('document', {}).get('title', 'No title')
                content = doc.get('document', {}).get('content', 'No content')
                
                print(f"\n📄 Document {i}:")
                print(f"   Title: {title}")
                print(f"   Similarity: {similarity:.3f} ({similarity*100:.1f}%)")
                print(f"   Content: {content[:200]}{'...' if len(content) > 200 else ''}")
                
        else:
            print(f"Error: {response.status_code}")
            
    except Exception as e:
        print(f"Error testing similarity: {e}")

def analyze_documents():
    """分析文档内容"""
    print("🔍 Analyzing all document segments for main_page_user...")
    
    # 获取所有文档
    documents = get_documents("main_page_user")
    
    if not documents:
        print("❌ No documents found")
        return
    
    print(f"📚 Found {len(documents)} segments")
    
    # 输出所有分段内容
    for i, doc in enumerate(documents, 1):
        title = doc.get('title', 'No title')
        content = doc.get('content', 'No content')
        print(f"\n{'='*60}")
        print(f"Segment {i} | Title: {title}")
        print(f"Content:\n{content}")
        print(f"{'='*60}")

if __name__ == "__main__":
    analyze_documents() 