#!/usr/bin/env python3
"""
Debug script to test document retrieval
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from rag_storage_prisma import PrismaRAGStorage

def test_document_retrieval():
    """Test document retrieval methods"""
    
    print("🔍 Testing document retrieval...")
    
    # Initialize storage
    storage = PrismaRAGStorage()
    
    try:
        # Test database info
        print("\n📊 Database Info:")
        db_info = storage.get_database_info()
        print(f"  Documents: {db_info.get('documents', 0)}")
        print(f"  Embeddings: {db_info.get('embeddings', 0)}")
        print(f"  Users: {db_info.get('users', 0)}")
        
        # Test stats
        print("\n📈 Stats:")
        stats = storage.get_user_stats()
        print(f"  Total documents: {stats.get('total_documents', 0)}")
        print(f"  Unique users: {stats.get('unique_users', 0)}")
        
        # Test get_all_documents
        print("\n📄 Testing get_all_documents:")
        documents, embeddings = storage.get_all_documents()
        print(f"  Retrieved {len(documents)} documents")
        print(f"  Retrieved {len(embeddings)} embeddings")
        
        if documents:
            print("  First document:")
            doc = documents[0]
            print(f"    ID: {doc.get('id')}")
            print(f"    Title: {doc.get('title')}")
            print(f"    User: {doc.get('user_id')}")
            print(f"    Content length: {len(doc.get('content', ''))}")
        else:
            print("  No documents returned!")
        
        # Test get_user_documents_list
        print("\n📋 Testing get_user_documents_list:")
        doc_list = storage.get_user_documents_list(limit=5)
        print(f"  Retrieved {len(doc_list)} documents from list method")
        
        if doc_list:
            print("  First document from list:")
            doc = doc_list[0]
            print(f"    ID: {doc.get('id')}")
            print(f"    Title: {doc.get('title')}")
            print(f"    User: {doc.get('user_id')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_document_retrieval() 