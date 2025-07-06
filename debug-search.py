#!/usr/bin/env python3
"""
Debug script to test search functionality step by step
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from rag_storage_prisma import PrismaRAGStorage
from rag_server_prisma import generate_simple_embedding, calculate_similarity

def debug_search():
    """Debug the search functionality step by step"""
    
    print("🔍 Debugging search functionality...")
    
    # Initialize storage
    storage = PrismaRAGStorage()
    user_id = "cmcr0plai0006ufg8pmqchjyt"
    query = "Hi"
    
    try:
        # Step 1: Get documents for user
        print(f"\n📄 Step 1: Getting documents for user '{user_id}'")
        user_documents, user_embeddings = storage.get_documents_by_user(user_id)
        print(f"  Retrieved {len(user_documents)} documents")
        print(f"  Retrieved {len(user_embeddings)} embeddings")
        
        if not user_documents:
            print("  ❌ No documents found for user!")
            return
        
        # Step 2: Show document details
        print(f"\n📋 Step 2: Document details")
        for i, doc in enumerate(user_documents[:3]):  # Show first 3
            print(f"  Document {i+1}:")
            print(f"    Title: {doc['title']}")
            print(f"    Content length: {len(doc['content'])}")
            print(f"    Content preview: {doc['content'][:100]}...")
            print(f"    Embedding available: {i < len(user_embeddings) and len(user_embeddings[i]) > 0}")
        
        # Step 3: Generate query embedding
        print(f"\n🧠 Step 3: Generating query embedding for '{query}'")
        query_embedding = generate_simple_embedding(query)
        print(f"  Query embedding length: {len(query_embedding)}")
        print(f"  Query embedding preview: {query_embedding[:5]}...")
        
        # Step 4: Calculate similarities
        print(f"\n🔍 Step 4: Calculating similarities")
        similarities = []
        for i, doc in enumerate(user_documents):
            print(f"  Document {i+1} ({doc['title']}):")
            
            if i < len(user_embeddings) and len(user_embeddings[i]) > 0:
                try:
                    embedding_list = user_embeddings[i].tolist() if hasattr(user_embeddings[i], 'tolist') else user_embeddings[i]
                    similarity = calculate_similarity(query_embedding, embedding_list)
                    similarities.append((doc, similarity))
                    print(f"    Similarity: {similarity:.3f}")
                except Exception as e:
                    print(f"    ❌ Error calculating similarity: {e}")
            else:
                print(f"    ❌ No embedding available")
        
        # Step 5: Filter and sort results
        print(f"\n📊 Step 5: Filtering and sorting results")
        print(f"  Total similarities calculated: {len(similarities)}")
        
        if similarities:
            similarities.sort(key=lambda x: x[1], reverse=True)
            print(f"  Top similarities:")
            for i, (doc, sim) in enumerate(similarities[:3]):
                print(f"    {i+1}. {doc['title']}: {sim:.3f}")
            
            # Test with different thresholds
            thresholds = [0.0, 0.1, 0.2, 0.3]
            for threshold in thresholds:
                filtered = [(doc, sim) for doc, sim in similarities if sim >= threshold]
                print(f"  With threshold {threshold}: {len(filtered)} documents")
        else:
            print("  ❌ No similarities calculated!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_search() 