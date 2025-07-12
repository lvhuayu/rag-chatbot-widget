#!/usr/bin/env python3
"""
Demo script showing the multi-tenant storage structure
Run this to see how user IDs and documents are stored and filtered
"""

import json
from datetime import datetime
import uuid

def demo_storage_structure():
    """Demonstrate the multi-tenant storage structure"""
    
    print("🔑 Multi-Tenant RAG Chatbot - Storage Demo")
    print("=" * 50)
    
    # Simulate the in-memory storage arrays
    documents = []
    embeddings = []
    
    # Add documents for different users
    print("\n📝 Adding documents for different users...")
    
    # User 1: Software Company
    company_docs = [
        {
            "id": str(uuid.uuid4()),
            "url": "https://company-abc.com/about",
            "title": "About Company ABC",
            "content": "Company ABC is a software development company specializing in web applications and mobile apps. We have 50 employees and focus on modern technologies.",
            "timestamp": datetime.now().isoformat(),
            "user_id": "company_abc_123"
        },
        {
            "id": str(uuid.uuid4()),
            "url": "https://company-abc.com/services",
            "title": "Our Services",
            "content": "We offer CRM systems, e-commerce platforms, and project management tools. Our clients are primarily in the technology sector.",
            "timestamp": datetime.now().isoformat(),
            "user_id": "company_abc_123"
        }
    ]
    
    # User 2: Restaurant
    restaurant_docs = [
        {
            "id": str(uuid.uuid4()),
            "url": "https://restaurant-xyz.com/menu",
            "title": "Restaurant XYZ Menu",
            "content": "We are a fine dining restaurant serving Italian cuisine. Our signature dishes include pasta carbonara, risotto, and tiramisu.",
            "timestamp": datetime.now().isoformat(),
            "user_id": "restaurant_xyz"
        },
        {
            "id": str(uuid.uuid4()),
            "url": "https://restaurant-xyz.com/location",
            "title": "Our Location",
            "content": "Located in downtown area, we offer both indoor and outdoor seating. Reservations are recommended for dinner service.",
            "timestamp": datetime.now().isoformat(),
            "user_id": "restaurant_xyz"
        }
    ]
    
    # User 3: Fitness Center
    fitness_docs = [
        {
            "id": str(uuid.uuid4()),
            "url": "https://fitness-center-456.com/facilities",
            "title": "Fitness Center Facilities",
            "content": "We are a premium fitness center with state-of-the-art equipment. We offer personal training, group classes, and nutrition counseling.",
            "timestamp": datetime.now().isoformat(),
            "user_id": "fitness_center_456"
        },
        {
            "id": str(uuid.uuid4()),
            "url": "https://fitness-center-456.com/classes",
            "title": "Group Classes",
            "content": "Our services include yoga classes, strength training, cardio equipment, swimming pool, and spa facilities.",
            "timestamp": datetime.now().isoformat(),
            "user_id": "fitness_center_456"
        }
    ]
    
    # Add all documents to storage
    all_docs = company_docs + restaurant_docs + fitness_docs
    documents.extend(all_docs)
    
    # Simulate embeddings (in real system, these would be 384-dimensional vectors)
    for i, doc in enumerate(documents):
        # Simulate embedding vector (simplified)
        embedding = [0.1 * (i + 1), 0.2 * (i + 1), 0.3 * (i + 1)] + [0.0] * 381  # 384 dimensions
        embeddings.append(embedding)
    
    print(f"✅ Added {len(documents)} documents to storage")
    
    # Show storage structure
    print("\n📊 Storage Structure:")
    print(f"Total documents: {len(documents)}")
    print(f"Total embeddings: {len(embeddings)}")
    print(f"Index alignment: documents[i] ↔ embeddings[i]")
    
    # Show user breakdown
    print("\n👥 User Breakdown:")
    user_counts = {}
    for doc in documents:
        user_id = doc["user_id"]
        user_counts[user_id] = user_counts.get(user_id, 0) + 1
    
    for user_id, count in user_counts.items():
        print(f"  {user_id}: {count} documents")
    
    # Demonstrate document filtering
    print("\n🔍 Document Filtering Demo:")
    
    def filter_documents_by_user(user_id):
        """Filter documents for a specific user"""
        user_documents = []
        user_embeddings = []
        
        for i, doc in enumerate(documents):
            if doc.get("user_id") == user_id:
                user_documents.append(doc)
                user_embeddings.append(embeddings[i])
        
        return user_documents, user_embeddings
    
    # Test filtering for each user
    users = ["company_abc_123", "restaurant_xyz", "fitness_center_456"]
    
    for user_id in users:
        user_docs, user_embeds = filter_documents_by_user(user_id)
        print(f"\n  User: {user_id}")
        print(f"  Documents found: {len(user_docs)}")
        print(f"  Embeddings found: {len(user_embeds)}")
        
        for doc in user_docs:
            print(f"    - {doc['title']} (ID: {doc['id'][:8]}...)")
    
    # Demonstrate search simulation
    print("\n🔎 Search Simulation:")
    
    def simulate_search(query, user_id):
        """Simulate a search for a specific user"""
        user_docs, user_embeds = filter_documents_by_user(user_id)
        
        print(f"\n  Query: '{query}' for user: {user_id}")
        print(f"  Searching in {len(user_docs)} documents...")
        
        # Simulate finding relevant documents (in real system, this would use vector similarity)
        relevant_docs = []
        for doc in user_docs:
            if any(keyword in doc["content"].lower() for keyword in query.lower().split()):
                relevant_docs.append(doc)
        
        print(f"  Relevant documents found: {len(relevant_docs)}")
        for doc in relevant_docs:
            print(f"    - {doc['title']}")
        
        return relevant_docs
    
    # Test searches
    searches = [
        ("software development", "company_abc_123"),
        ("Italian food", "restaurant_xyz"),
        ("fitness equipment", "fitness_center_456"),
        ("restaurant", "company_abc_123"),  # Should find nothing
        ("software", "restaurant_xyz")      # Should find nothing
    ]
    
    for query, user_id in searches:
        simulate_search(query, user_id)
    
    # Show complete storage dump
    print("\n📋 Complete Storage Dump:")
    print("Documents array:")
    for i, doc in enumerate(documents):
        print(f"  [{i}] {doc['user_id']}: {doc['title']}")
    
    print("\nEmbeddings array (first 3 dimensions):")
    for i, embedding in enumerate(embeddings):
        print(f"  [{i}] {embedding[:3]}... (384 dimensions total)")
    
    # Demonstrate API responses
    print("\n🌐 API Response Examples:")
    
    def get_user_stats(user_id):
        """Get statistics for a specific user"""
        user_docs, _ = filter_documents_by_user(user_id)
        return {
            "user_id": user_id,
            "document_count": len(user_docs),
            "total_documents": len(documents),
            "embedding_model": "all-MiniLM-L6-v2",
            "vector_db": "In-Memory (NumPy + scikit-learn)",
            "status": "running",
            "multi_tenant": True
        }
    
    # Show stats for each user
    for user_id in users:
        stats = get_user_stats(user_id)
        print(f"\n  GET /stats?user_id={user_id}")
        print(f"  Response: {json.dumps(stats, indent=2)}")
    
    # Show overall stats
    overall_stats = {
        "user_id": "all_users",
        "document_count": len(documents),
        "total_documents": len(documents),
        "embedding_model": "all-MiniLM-L6-v2",
        "vector_db": "In-Memory (NumPy + scikit-learn)",
        "status": "running",
        "multi_tenant": True
    }
    print(f"\n  GET /stats")
    print(f"  Response: {json.dumps(overall_stats, indent=2)}")
    
    print("\n✅ Storage demo completed!")
    print("\nKey Points:")
    print("1. Each document has a user_id field for isolation")
    print("2. Search only looks at documents for the specified user")
    print("3. Embeddings array maintains index alignment with documents")
    print("4. Complete data isolation between different users")
    print("5. Backward compatibility: no user_id = access to all documents")

if __name__ == "__main__":
    demo_storage_structure() 