#!/usr/bin/env python3
"""
Check full document content
"""

import requests
import json

def get_full_documents(user_id: str = "main_page_user"):
    """获取完整的文档内容"""
    try:
        response = requests.get(f"http://localhost:8001/documents?user_id={user_id}", timeout=10)
        if response.status_code == 200:
            documents = response.json()
            print(f"📚 Found {len(documents)} documents")
            
            for i, doc in enumerate(documents, 1):
                title = doc.get('title', 'No title')
                content = doc.get('content', 'No content')
                url = doc.get('url', 'No URL')
                
                print(f"\n{'='*80}")
                print(f"📄 Document {i}: {title}")
                print(f"🔗 URL: {url}")
                print(f"📏 Content Length: {len(content)} characters")
                print(f"{'='*80}")
                print("📝 Full Content:")
                print(content)
                print(f"{'='*80}")
                
        else:
            print(f"Error getting documents: {response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_full_documents("main_page_user") 