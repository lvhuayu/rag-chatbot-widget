#!/usr/bin/env python3
"""
Test script to verify improved search functionality
"""

import requests
import json

def test_search_queries():
    """Test various search queries to verify the improvements"""
    
    base_url = "http://localhost:8001/search"
    headers = {"Content-Type": "application/json"}
    user_id = "cmcr0plai0006ufg8pmqchjyt"
    
    # Test cases
    test_cases = [
        {
            "name": "Nonsense query (should be rejected)",
            "query": "adsfadf",
            "expected": "no results due to low quality"
        },
        {
            "name": "Relevant query about API",
            "query": "API usage",
            "expected": "should find relevant documents"
        },
        {
            "name": "Query about authorization",
            "query": "authorization design",
            "expected": "should find authorization document"
        },
        {
            "name": "Very short query",
            "query": "hi",
            "expected": "might be rejected due to low quality"
        }
    ]
    
    print("🧪 Testing Improved Search Functionality")
    print("=" * 50)
    
    for test_case in test_cases:
        print(f"\n📝 Test: {test_case['name']}")
        print(f"   Query: '{test_case['query']}'")
        print(f"   Expected: {test_case['expected']}")
        
        data = {
            "query": test_case['query'],
            "user_id": user_id,
            "threshold": 0.3  # Use the new default threshold
        }
        
        try:
            response = requests.post(base_url, headers=headers, json=data, timeout=10)
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                documents = result.get('documents', [])
                context = result.get('context', 'No context')
                
                print(f"   Results: {len(documents)} documents")
                print(f"   Context: {context[:100]}...")
                
                if documents:
                    for i, doc in enumerate(documents[:2]):  # Show top 2
                        print(f"     {i+1}. {doc['document']['title']} ({doc['similarity']:.3f})")
                else:
                    print("     No documents returned (likely rejected due to low quality)")
            else:
                print(f"   Error: {response.text}")
                
        except Exception as e:
            print(f"   Error: {e}")
        
        print("-" * 30)

if __name__ == "__main__":
    test_search_queries() 