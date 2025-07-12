#!/usr/bin/env python3
"""
Debug database content directly
"""

import requests
import json

def check_database_content():
    """直接检查数据库内容"""
    print("🔍 Checking database content directly...")
    
    # 1. 检查健康状态和数据库信息
    try:
        response = requests.get("http://localhost:8001/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print(f"📊 Database Info: {health_data.get('database_info', {})}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return
    
    # 2. 获取所有文档
    try:
        response = requests.get("http://localhost:8001/documents?user_id=main_page_user", timeout=10)
        if response.status_code == 200:
            documents = response.json()
            print(f"\n📚 Total documents in database: {len(documents)}")
            
            if len(documents) > 0:
                print(f"\n📄 First document content preview:")
                first_doc = documents[0]
                print(f"Title: {first_doc.get('title', 'No title')}")
                print(f"Content length: {len(first_doc.get('content', ''))}")
                print(f"Content preview: {first_doc.get('content', '')[:200]}...")
                
                if len(documents) > 1:
                    print(f"\n📄 Second document content preview:")
                    second_doc = documents[1]
                    print(f"Title: {second_doc.get('title', 'No title')}")
                    print(f"Content length: {len(second_doc.get('content', ''))}")
                    print(f"Content preview: {second_doc.get('content', '')[:200]}...")
            else:
                print("❌ No documents found in database")
                
        else:
            print(f"❌ Failed to get documents: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error getting documents: {e}")

if __name__ == "__main__":
    check_database_content() 