#!/usr/bin/env python3
"""
Minimal RAG Server - No sentence_transformers dependency
This is a temporary solution to get the integration working while we fix the PyTorch issues
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import json
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="RAG Chatbot Backend (Minimal)", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for documents (temporary)
documents = {}  # {doc_id: {url, title, content, user_id, timestamp}}
embeddings = {}  # {doc_id: [embedding_values]}

class Document(BaseModel):
    url: str
    title: str
    content: str
    timestamp: Optional[str] = None
    user_id: Optional[str] = None

class SearchRequest(BaseModel):
    query: str
    top_k: int = 3
    threshold: Optional[float] = 0.0
    user_id: Optional[str] = None

class SearchResult(BaseModel):
    document: Document
    similarity: float

class RAGResponse(BaseModel):
    context: Optional[str]
    documents: List[SearchResult]

def generate_simple_embedding(text: str) -> List[float]:
    """Generate a simple embedding using character frequency (temporary)"""
    # This is a very basic embedding - just for testing
    import string
    freq = {}
    for char in string.ascii_lowercase:
        freq[char] = 0
    
    text_lower = text.lower()
    for char in text_lower:
        if char in freq:
            freq[char] += 1
    
    # Normalize
    total = sum(freq.values()) or 1
    embedding = [freq[char] / total for char in string.ascii_lowercase]
    
    # Pad to 384 dimensions (like all-MiniLM-L6-v2)
    while len(embedding) < 384:
        embedding.append(0.0)
    return embedding[:384]

def calculate_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """Calculate cosine similarity between two embeddings"""
    import math
    
    dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
    magnitude1 = math.sqrt(sum(a * a for a in embedding1))
    magnitude2 = math.sqrt(sum(a * a for a in embedding2))
    
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    
    return dot_product / (magnitude1 * magnitude2)

@app.get("/")
async def root():
    return {"message": "RAG Chatbot Backend API (Minimal)", "status": "running"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "model": "simple-character-frequency", 
        "storage": "in-memory",
        "database_info": {
            "database_path": "in-memory",
            "database_size_mb": 0,
            "total_documents": len(documents),
            "unique_users": len(set(doc.get("user_id", "default") for doc in documents.values())),
            "embedding_dimension": 384,
            "storage_type": "in-memory"
        }
    }

@app.post("/add-document", response_model=Dict[str, Any])
async def add_document(document: Document):
    """Add a document to the RAG system with multi-tenant support"""
    try:
        # Generate simple embedding
        embedding = generate_simple_embedding(document.content)
        
        # Add to storage with user_id
        user_id = document.user_id or "default_user"
        
        # Check if document with same title exists for this user
        existing_doc_id = None
        for doc_id, doc in documents.items():
            if doc["title"] == document.title and doc["user_id"] == user_id:
                existing_doc_id = doc_id
                break
        
        if existing_doc_id:
            # Update existing document
            documents[existing_doc_id].update({
                "url": document.url,
                "content": document.content,
                "timestamp": document.timestamp or datetime.now().isoformat()
            })
            embeddings[existing_doc_id] = embedding
            
            logger.info(f"Updated existing document: {document.title} (User: {user_id}, ID: {existing_doc_id})")
            return {
                "success": True,
                "doc_id": existing_doc_id,
                "message": f"Document '{document.title}' updated successfully for user: {user_id}",
                "action": "updated"
            }
        else:
            # Create new document
            doc_id = str(uuid.uuid4())
            documents[doc_id] = {
                "url": document.url,
                "title": document.title,
                "content": document.content,
                "user_id": user_id,
                "timestamp": document.timestamp or datetime.now().isoformat()
            }
            embeddings[doc_id] = embedding
            
            logger.info(f"Added new document: {document.title} (User: {user_id}, ID: {doc_id})")
            return {
                "success": True,
                "doc_id": doc_id,
                "message": f"Document '{document.title}' added successfully for user: {user_id}",
                "action": "added"
            }
            
    except Exception as e:
        import traceback
        logger.error(f"Error in /add-document endpoint: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error adding document: {str(e)}")

@app.post("/search", response_model=RAGResponse)
async def search_documents(request: SearchRequest):
    """Search for relevant documents with multi-tenant support"""
    try:
        # Get documents for specific user
        user_documents = []
        user_embeddings = []
        
        for doc_id, doc in documents.items():
            if doc["user_id"] == request.user_id:
                user_documents.append({
                    "id": doc_id,
                    "url": doc["url"],
                    "title": doc["title"],
                    "content": doc["content"],
                    "timestamp": doc["timestamp"],
                    "user_id": doc["user_id"]
                })
                user_embeddings.append(embeddings[doc_id])
        
        if not user_documents:
            logger.info(f"No documents available for user: {request.user_id}")
            return RAGResponse(
                context="I don't have any information in my knowledge base to answer your question. Please contact support or check our documentation for more details.",
                documents=[]
            )
        
        # Generate query embedding
        query_embedding = generate_simple_embedding(request.query)
        
        # Calculate similarities
        similarities = []
        for embedding in user_embeddings:
            similarity = calculate_similarity(query_embedding, embedding)
            similarities.append(similarity)
        
        # Get top k results
        indexed_similarities = list(enumerate(similarities))
        indexed_similarities.sort(key=lambda x: x[1], reverse=True)
        top_indices = [idx for idx, sim in indexed_similarities[:request.top_k] if sim >= request.threshold]
        
        search_results = []
        for idx in top_indices:
            similarity = similarities[idx]
            doc = user_documents[idx]
            document = Document(
                url=doc["url"],
                title=doc["title"],
                content=doc["content"],
                timestamp=doc["timestamp"],
                user_id=doc["user_id"]
            )
            search_results.append(SearchResult(
                document=document,
                similarity=float(similarity)
            ))
        
        # Build context
        context = None
        if search_results:
            context_parts = []
            for result in search_results:
                context_parts.append(
                    f"[Document: {result.document.title} (similarity: {result.similarity:.3f})]\n"
                    f"{result.document.content}\n"
                )
            context = "\n".join(context_parts)
        
        # Log the search results for debugging
        logger.info(f"Query: '{request.query}', Found: {len(search_results)} documents")
        for r in search_results:
            logger.info(f"  - Title: {r.document.title}, Similarity: {r.similarity:.3f}")
        
        # --- OLLAMA INTEGRATION ---
        ollama_url = "http://localhost:11434/api/generate"
        
        if context and search_results:
            # Use context from relevant documents
            prompt = """
You are a helpful assistant. Use the following context to answer the user's question. If the context is not sufficient, say so.

Context:
"""
            prompt += context + "\n"
            prompt += f"\nUser question: {request.query}\nAnswer:"
        else:
            # No relevant documents found
            prompt = f"""
You are a helpful assistant for a specific business. The user has asked: {request.query}

IMPORTANT: You do not have any relevant information in your knowledge base to answer this question accurately. 

Please respond by saying that you don't have information about this topic, or that this service/feature is not available, rather than making assumptions or providing generic information.

Answer:"""
        
        ollama_payload = {
            "model": "mistral",
            "prompt": prompt,
            "stream": False
        }
        llm_answer = None
        try:
            ollama_response = requests.post(ollama_url, json=ollama_payload, timeout=60)
            ollama_response.raise_for_status()
            llm_data = ollama_response.json()
            llm_answer = llm_data.get("response", "[No answer from LLM]")
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            llm_answer = "[Error: Could not get response from local LLM]"
        
        return RAGResponse(
            context=llm_answer,
            documents=search_results
        )
    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching documents: {str(e)}")

@app.get("/documents", response_model=List[Document])
async def list_documents(user_id: Optional[str] = None):
    """List documents with optional user filtering"""
    try:
        result_documents = []
        for doc in documents.values():
            if user_id is None or doc["user_id"] == user_id:
                document = Document(
                    url=doc["url"],
                    title=doc["title"],
                    content=doc["content"],
                    timestamp=doc["timestamp"],
                    user_id=doc["user_id"]
                )
                result_documents.append(document)
        
        logger.info(f"Returning {len(result_documents)} documents for user: {user_id or 'all'}")
        return result_documents
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")

@app.delete("/clear-documents")
async def clear_documents():
    """Clear all documents"""
    try:
        documents.clear()
        embeddings.clear()
        logger.info("Cleared all documents")
        return {"message": "All documents cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing documents: {e}")
        raise HTTPException(status_code=500, detail=f"Error clearing documents: {str(e)}")

@app.get("/stats")
async def get_stats(user_id: Optional[str] = None):
    """Get statistics for a specific user or overall"""
    try:
        if user_id:
            # User-specific stats
            user_docs = [doc for doc in documents.values() if doc["user_id"] == user_id]
            return {
                "user_id": user_id,
                "document_count": len(user_docs),
                "total_documents": len(documents),
                "embedding_model": "simple-character-frequency",
                "vector_db": "in-memory",
                "status": "healthy",
                "multi_tenant": True
            }
        else:
            # Overall stats
            unique_users = len(set(doc["user_id"] for doc in documents.values()))
            return {
                "user_id": "all",
                "document_count": len(documents),
                "total_documents": len(documents),
                "unique_users": unique_users,
                "embedding_model": "simple-character-frequency",
                "vector_db": "in-memory",
                "status": "healthy",
                "multi_tenant": True
            }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting RAG Chatbot Backend (Minimal)...")
    print("📊 Database: In-Memory")
    print("🧠 Model: Simple Character Frequency")
    print("🔗 API: http://localhost:8001")
    print("📚 Health: http://localhost:8001/health")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8001) 