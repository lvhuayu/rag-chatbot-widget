#!/usr/bin/env python3
"""
Debug script to inspect embedding data structure
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from rag_storage_prisma import PrismaRAGStorage

def debug_embedding_data():
    """Debug the embedding data structure"""
    
    print("🔍 Debugging embedding data structure...")
    
    # Initialize storage
    storage = PrismaRAGStorage()
    user_id = "cmcr0plai0006ufg8pmqchjyt"
    
    try:
        # Get documents with embeddings
        print(f"\n📄 Getting documents for user '{user_id}'")
        user_documents, user_embeddings = storage.get_documents_by_user(user_id)
        print(f"  Retrieved {len(user_documents)} documents")
        print(f"  Retrieved {len(user_embeddings)} embeddings")
        
        # Inspect the first document's embedding data
        if user_documents and len(user_embeddings) > 0:
            print(f"\n🔍 Inspecting embedding data for first document:")
            print(f"  Document: {user_documents[0]['title']}")
            
            # Let's look at the raw embedding data from the database
            print(f"\n📊 Raw embedding data inspection:")
            
            # We need to get the raw data from the database
            query = f"""
                await prisma.rAGDocument.findFirst({{
                    where: {{
                        user: {{
                            username: '{user_id}'
                        }}
                    }},
                    include: {{
                        embedding: true
                    }}
                }})
            """
            
            result = storage._run_prisma_query(query)
            if result:
                print(f"  Document ID: {result['id']}")
                print(f"  Document Title: {result['title']}")
                
                if result.get('embedding'):
                    embedding_data = result['embedding']['embeddingData']
                    print(f"  Embedding data type: {type(embedding_data)}")
                    print(f"  Embedding data length: {len(str(embedding_data))}")
                    print(f"  Embedding data preview: {str(embedding_data)[:200]}...")
                    
                    # Try to understand the structure
                    if isinstance(embedding_data, dict):
                        print(f"  Embedding data keys: {list(embedding_data.keys())}")
                    elif isinstance(embedding_data, str):
                        print(f"  Embedding data is a string")
                        # Check if it's base64
                        import base64
                        try:
                            decoded = base64.b64decode(embedding_data)
                            print(f"  Base64 decoded length: {len(decoded)}")
                        except:
                            print(f"  Not valid base64")
                else:
                    print(f"  No embedding found for this document")
            else:
                print(f"  No document found")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_embedding_data() 