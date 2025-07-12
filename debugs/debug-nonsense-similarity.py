#!/usr/bin/env python3
"""
Debug nonsense query similarity scores
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from rag_storage_prisma import PrismaRAGStorage
from rag_server_prisma import generate_simple_embedding, calculate_similarity

def debug_nonsense_similarity():
    """Debug similarity scores for nonsense queries"""
    
    print("🔍 Debugging nonsense query similarity scores...")
    
    # Initialize storage
    storage = PrismaRAGStorage()
    user_id = "cmcr0plai0006ufg8pmqchjyt"
    nonsense_query = "adsfadf"
    
    try:
        # Get documents for user
        user_documents, user_embeddings = storage.get_documents_by_user(user_id)
        print(f"Retrieved {len(user_documents)} documents")
        
        # Generate query embedding
        query_embedding = generate_simple_embedding(nonsense_query)
        print(f"Query embedding for '{nonsense_query}': {query_embedding[:10]}...")
        
        # Calculate similarities
        similarities = []
        for i, doc in enumerate(user_documents):
            if i < len(user_embeddings) and len(user_embeddings[i]) > 0:
                embedding_list = user_embeddings[i].tolist() if hasattr(user_embeddings[i], 'tolist') else user_embeddings[i]
                similarity = calculate_similarity(query_embedding, embedding_list)
                similarities.append((doc['title'], similarity))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        print(f"\n📊 Similarity scores for '{nonsense_query}':")
        for i, (title, sim) in enumerate(similarities):
            print(f"  {i+1}. {title}: {sim:.3f}")
        
        best_similarity = similarities[0][1] if similarities else 0.0
        print(f"\n🎯 Best similarity: {best_similarity:.3f}")
        print(f"🔧 Current quality threshold: 0.25")
        print(f"📈 Recommended quality threshold: {best_similarity + 0.05:.3f}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_nonsense_similarity() 