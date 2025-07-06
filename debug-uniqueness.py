#!/usr/bin/env python3
"""
Debug script to understand why title uniqueness is not working
"""

import requests
import json
import sqlite3

API_BASE = "http://localhost:8001"
DB_PATH = "backend/rag_database.db"

def debug_database():
    """Debug the database directly to see what's happening"""
    print("🔍 Debugging Database Directly")
    print("=" * 40)
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Check the database schema
            cursor.execute("PRAGMA table_info(documents)")
            columns = cursor.fetchall()
            print("📋 Documents table schema:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
            
            # Check for unique constraints
            cursor.execute("PRAGMA index_list(documents)")
            indexes = cursor.fetchall()
            print(f"\n📋 Indexes on documents table:")
            for idx in indexes:
                print(f"  - {idx[1]} (unique: {idx[2]})")
            
            # Check all documents with test title
            cursor.execute('''
                SELECT id, title, user_id, content, timestamp 
                FROM documents 
                WHERE title = 'Test Document'
                ORDER BY timestamp DESC
            ''')
            
            test_docs = cursor.fetchall()
            print(f"\n📄 Documents with title 'Test Document': {len(test_docs)}")
            for i, doc in enumerate(test_docs):
                print(f"  {i+1}. ID: {doc[0]}")
                print(f"     User: {doc[2]}")
                print(f"     Content: {doc[3][:50]}...")
                print(f"     Timestamp: {doc[4]}")
                print()
            
            # Check documents for specific user
            cursor.execute('''
                SELECT id, title, user_id, content, timestamp 
                FROM documents 
                WHERE user_id = 'test_user_123'
                ORDER BY timestamp DESC
            ''')
            
            user_docs = cursor.fetchall()
            print(f"📄 Documents for user 'test_user_123': {len(user_docs)}")
            for i, doc in enumerate(user_docs):
                print(f"  {i+1}. ID: {doc[0]}")
                print(f"     Title: {doc[1]}")
                print(f"     Content: {doc[3][:50]}...")
                print(f"     Timestamp: {doc[4]}")
                print()
                
    except Exception as e:
        print(f"❌ Error accessing database: {e}")

def debug_api_call():
    """Debug the API call to see what's happening"""
    print("\n🔍 Debugging API Call")
    print("=" * 40)
    
    # Test data
    user_id = "debug_user_123"
    title = "Debug Document"
    url = "https://example.com/debug"
    
    # First document
    doc1 = {
        "url": url,
        "title": title,
        "content": "First version of debug document.",
        "user_id": user_id
    }
    
    try:
        print(f"📝 Adding first document: '{title}' for user: {user_id}")
        response1 = requests.post(f"{API_BASE}/add-document", json=doc1)
        result1 = response1.json()
        
        print(f"Response: {json.dumps(result1, indent=2)}")
        
        # Check database immediately after
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, title, user_id, content, timestamp 
                FROM documents 
                WHERE title = ? AND user_id = ?
            ''', (title, user_id))
            
            docs = cursor.fetchall()
            print(f"📊 Documents in DB after first add: {len(docs)}")
            for doc in docs:
                print(f"  - ID: {doc[0]}, Content: {doc[3][:30]}...")
        
        # Second document with same title
        doc2 = {
            "url": url,
            "title": title,
            "content": "Updated version of debug document.",
            "user_id": user_id
        }
        
        print(f"\n📝 Adding second document with same title: '{title}' for user: {user_id}")
        response2 = requests.post(f"{API_BASE}/add-document", json=doc2)
        result2 = response2.json()
        
        print(f"Response: {json.dumps(result2, indent=2)}")
        
        # Check database immediately after
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, title, user_id, content, timestamp 
                FROM documents 
                WHERE title = ? AND user_id = ?
            ''', (title, user_id))
            
            docs = cursor.fetchall()
            print(f"📊 Documents in DB after second add: {len(docs)}")
            for doc in docs:
                print(f"  - ID: {doc[0]}, Content: {doc[3][:30]}...")
        
    except Exception as e:
        print(f"❌ Error in API call: {e}")

def check_storage_method():
    """Test the storage method directly"""
    print("\n🔍 Testing Storage Method Directly")
    print("=" * 40)
    
    try:
        # Import the storage class
        import sys
        sys.path.append('backend')
        from rag_storage import RAGStorage
        
        storage = RAGStorage(DB_PATH)
        
        # Test data
        user_id = "storage_test_user"
        title = "Storage Test Document"
        
        # First call
        print(f"📝 First call to add_document_with_uniqueness")
        result1 = storage.add_document_with_uniqueness(
            doc_id="test_id_1",
            url="https://example.com/test1",
            title=title,
            content="First version",
            user_id=user_id,
            embedding=[0.1, 0.2, 0.3] * 128  # Mock embedding
        )
        print(f"Result: {result1}")
        
        # Second call with same title
        print(f"\n📝 Second call to add_document_with_uniqueness (same title)")
        result2 = storage.add_document_with_uniqueness(
            doc_id="test_id_2",
            url="https://example.com/test2",
            title=title,
            content="Updated version",
            user_id=user_id,
            embedding=[0.4, 0.5, 0.6] * 128  # Mock embedding
        )
        print(f"Result: {result2}")
        
        # Check database
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, title, user_id, content, timestamp 
                FROM documents 
                WHERE title = ? AND user_id = ?
            ''', (title, user_id))
            
            docs = cursor.fetchall()
            print(f"\n📊 Documents in DB after storage test: {len(docs)}")
            for doc in docs:
                print(f"  - ID: {doc[0]}, Content: {doc[3][:30]}...")
        
    except Exception as e:
        print(f"❌ Error in storage test: {e}")

if __name__ == "__main__":
    debug_database()
    debug_api_call()
    check_storage_method() 