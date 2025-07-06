#!/usr/bin/env python3
"""
Test script to verify document title uniqueness per user
"""

import requests
import json

API_BASE = "http://localhost:8001"

def test_title_uniqueness():
    """Test that documents with same title for same user are updated, not duplicated"""
    
    print("🧪 Testing Document Title Uniqueness per User")
    print("=" * 50)
    
    # Test data
    user_id = "test_user_123"
    title = "Test Document"
    url = "https://example.com/test"
    
    # First document
    doc1 = {
        "url": url,
        "title": title,
        "content": "This is the first version of the document.",
        "user_id": user_id
    }
    
    # Second document with same title
    doc2 = {
        "url": url,
        "title": title,
        "content": "This is the updated version of the document.",
        "user_id": user_id
    }
    
    try:
        # Add first document
        print(f"📝 Adding first document: '{title}' for user: {user_id}")
        response1 = requests.post(f"{API_BASE}/add-document", json=doc1)
        result1 = response1.json()
        
        if result1.get("success"):
            print(f"✅ {result1['message']}")
            print(f"   Action: {result1.get('action', 'unknown')}")
            print(f"   Document ID: {result1['doc_id']}")
        else:
            print(f"❌ Failed to add first document: {result1.get('message', 'Unknown error')}")
            return
        
        # Add second document with same title
        print(f"\n📝 Adding second document with same title: '{title}' for user: {user_id}")
        response2 = requests.post(f"{API_BASE}/add-document", json=doc2)
        result2 = response2.json()
        
        if result2.get("success"):
            print(f"✅ {result2['message']}")
            print(f"   Action: {result2.get('action', 'unknown')}")
            print(f"   Document ID: {result2['doc_id']}")
        else:
            print(f"❌ Failed to add second document: {result2.get('message', 'Unknown error')}")
            return
        
        # Check if documents are unique
        print(f"\n🔍 Checking document count for user: {user_id}")
        response3 = requests.get(f"{API_BASE}/documents?user_id={user_id}")
        documents = response3.json()
        
        print(f"📊 Total documents for user: {len(documents)}")
        
        # Count documents with the test title
        title_count = sum(1 for doc in documents if doc['title'] == title)
        print(f"📊 Documents with title '{title}': {title_count}")
        
        if title_count == 1:
            print("✅ SUCCESS: Only one document with the same title exists!")
        else:
            print(f"❌ FAILURE: Found {title_count} documents with the same title (expected 1)")
        
        # Show the final document content
        test_docs = [doc for doc in documents if doc['title'] == title]
        if test_docs:
            final_doc = test_docs[0]
            print(f"\n📄 Final document content: '{final_doc['content']}'")
        
        # Test with different user (should create new document)
        print(f"\n🧪 Testing with different user...")
        doc3 = {
            "url": url,
            "title": title,
            "content": "This is a document for a different user.",
            "user_id": "different_user_456"
        }
        
        response4 = requests.post(f"{API_BASE}/add-document", json=doc3)
        result4 = response4.json()
        
        if result4.get("success"):
            print(f"✅ {result4['message']}")
            print(f"   Action: {result4.get('action', 'unknown')}")
        
        # Check total documents
        response5 = requests.get(f"{API_BASE}/documents")
        all_documents = response5.json()
        print(f"\n📊 Total documents in system: {len(all_documents)}")
        
        # Count documents with the test title across all users
        all_title_count = sum(1 for doc in all_documents if doc['title'] == title)
        print(f"📊 Documents with title '{title}' across all users: {all_title_count}")
        
        if all_title_count == 2:
            print("✅ SUCCESS: Different users can have documents with the same title!")
        else:
            print(f"❌ FAILURE: Expected 2 documents with title '{title}', found {all_title_count}")
        
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to the RAG server. Make sure it's running on localhost:8001")
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    test_title_uniqueness() 