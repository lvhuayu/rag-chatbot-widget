#!/usr/bin/env python3
"""
Test script to verify widget integration with Prisma database
"""

import requests
import json
import time

API_BASE = "http://localhost:8001"

def test_prisma_integration():
    """Test the Prisma-based RAG system"""
    print("🧪 Testing Prisma Database Integration")
    print("=" * 50)
    
    # Test 1: Health check
    print("\n1️⃣ Testing health endpoint...")
    try:
        response = requests.get(f"{API_BASE}/health")
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Health check passed")
            print(f"   Status: {health_data.get('status')}")
            print(f"   Storage: {health_data.get('storage')}")
            print(f"   Database: {health_data.get('database_info', {}).get('type', 'Unknown')}")
            print(f"   Documents: {health_data.get('database_info', {}).get('documents', 0)}")
            print(f"   Users: {health_data.get('database_info', {}).get('users', 0)}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    # Test 2: Add document to Prisma
    print("\n2️⃣ Testing document addition...")
    test_doc = {
        "url": "https://example.com/prisma-test",
        "title": "Prisma Integration Test",
        "content": "This is a test document to verify Prisma database integration is working correctly.",
        "user_id": "prisma_test_user"
    }
    
    try:
        response = requests.post(f"{API_BASE}/add-document", json=test_doc)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Document added successfully")
            print(f"   Action: {result.get('action')}")
            print(f"   Message: {result.get('message')}")
        else:
            print(f"❌ Document addition failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Document addition error: {e}")
        return False
    
    # Test 3: Search documents
    print("\n3️⃣ Testing document search...")
    search_query = {
        "query": "Prisma integration test",
        "user_id": "prisma_test_user",
        "top_k": 3
    }
    
    try:
        response = requests.post(f"{API_BASE}/search", json=search_query)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Search completed successfully")
            print(f"   Documents found: {len(result.get('documents', []))}")
            print(f"   Context available: {'Yes' if result.get('context') else 'No'}")
            
            for i, doc in enumerate(result.get('documents', [])):
                print(f"   {i+1}. {doc['document']['title']} (similarity: {doc['similarity']:.3f})")
        else:
            print(f"❌ Search failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Search error: {e}")
        return False
    
    # Test 4: List documents
    print("\n4️⃣ Testing document listing...")
    try:
        response = requests.get(f"{API_BASE}/documents?user_id=prisma_test_user")
        if response.status_code == 200:
            documents = response.json()
            print(f"✅ Document listing successful")
            print(f"   Documents for user: {len(documents)}")
            
            for i, doc in enumerate(documents[:3]):  # Show first 3
                print(f"   {i+1}. {doc['title']} ({doc['user_id']})")
        else:
            print(f"❌ Document listing failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Document listing error: {e}")
        return False
    
    # Test 5: Test title uniqueness
    print("\n5️⃣ Testing title uniqueness...")
    duplicate_doc = {
        "url": "https://example.com/prisma-test-updated",
        "title": "Prisma Integration Test",  # Same title
        "content": "This is an updated version of the test document.",
        "user_id": "prisma_test_user"
    }
    
    try:
        response = requests.post(f"{API_BASE}/add-document", json=duplicate_doc)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Uniqueness test completed")
            print(f"   Action: {result.get('action')}")
            print(f"   Message: {result.get('message')}")
            
            if result.get('action') == 'updated':
                print("   ✅ Document was updated (uniqueness working)")
            else:
                print("   ⚠️  Document was added (uniqueness may not be working)")
        else:
            print(f"❌ Uniqueness test failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Uniqueness test error: {e}")
        return False
    
    # Test 6: Get stats
    print("\n6️⃣ Testing statistics...")
    try:
        response = requests.get(f"{API_BASE}/stats?user_id=prisma_test_user")
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Statistics retrieved")
            print(f"   User documents: {stats.get('document_count', 0)}")
            print(f"   Total documents: {stats.get('total_documents', 0)}")
        else:
            print(f"❌ Statistics failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Statistics error: {e}")
        return False
    
    print("\n🎉 All tests completed successfully!")
    print("✅ The widget is now talking to the Prisma database!")
    return True

def test_widget_frontend():
    """Test the frontend widget with Prisma backend"""
    print("\n🌐 Testing Frontend Widget Integration")
    print("=" * 50)
    
    print("📋 To test the frontend widget:")
    print("   1. Open http://localhost:8001 in your browser")
    print("   2. Or use one of the test HTML files in the public/ directory")
    print("   3. Try uploading documents and asking questions")
    print("   4. Check that responses come from the Prisma database")
    
    print("\n🔗 Test URLs:")
    print("   - Health: http://localhost:8001/health")
    print("   - Documents: http://localhost:8001/documents")
    print("   - Stats: http://localhost:8001/stats")

if __name__ == "__main__":
    print("🚀 Prisma Integration Test")
    print("=" * 50)
    
    # Wait a moment for server to be ready
    print("⏳ Waiting for server to be ready...")
    time.sleep(2)
    
    # Run tests
    success = test_prisma_integration()
    
    if success:
        test_widget_frontend()
    else:
        print("\n❌ Integration test failed!")
        print("🔧 Make sure the Prisma server is running:")
        print("   .\\start-prisma-server.ps1") 