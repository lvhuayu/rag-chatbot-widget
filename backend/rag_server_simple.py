from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sentence_transformers import SentenceTransformer
import uuid
from datetime import datetime
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import json
import requests

app = FastAPI(title="RAG Chatbot Backend (Simple)", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize embedding model and in-memory storage
print("Loading embedding model...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

print("Initializing in-memory vector storage...")
documents = []
embeddings = []

class Document(BaseModel):
    url: str
    title: str
    content: str
    timestamp: Optional[str] = None

class SearchRequest(BaseModel):
    query: str
    top_k: int = 3

class SearchResult(BaseModel):
    document: Document
    similarity: float

class RAGResponse(BaseModel):
    context: Optional[str]
    documents: List[SearchResult]

@app.get("/")
async def root():
    return {"message": "RAG Chatbot Backend API (Simple)", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "model": "all-MiniLM-L6-v2", "storage": "in-memory"}

@app.post("/add-document", response_model=Dict[str, Any])
async def add_document(document: Document):
    """Add a document to the RAG system"""
    try:
        # Generate embedding
        embedding = embedding_model.encode(document.content).tolist()
        
        # Add to in-memory storage
        doc_id = str(uuid.uuid4())
        documents.append({
            "id": doc_id,
            "url": document.url,
            "title": document.title,
            "content": document.content,
            "timestamp": document.timestamp or datetime.now().isoformat()
        })
        embeddings.append(embedding)
        
        return {
            "success": True,
            "doc_id": doc_id,
            "message": f"Document '{document.title}' added successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding document: {str(e)}")

@app.post("/search", response_model=RAGResponse)
async def search_documents(request: SearchRequest):
    """Search for relevant documents"""
    try:
        # if not documents:
        #     return RAGResponse(context=None, documents=[])
        
        # Generate query embedding
        print(SearchRequest)
        query_embedding = embedding_model.encode(request.query).reshape(1, -1)
        print(query_embedding)
        
        # Calculate similarities
        doc_embeddings = np.array(embeddings)
        similarities = cosine_similarity(query_embedding, doc_embeddings)[0]
        
        # Get top k results
        top_indices = np.argsort(similarities)[::-1][:request.top_k]
        
        search_results = []
        for idx in top_indices:
            if similarities[idx] > 0:  # Only include relevant results
                doc = documents[idx]
                document = Document(
                    url=doc["url"],
                    title=doc["title"],
                    content=doc["content"],
                    timestamp=doc["timestamp"]
                )
                
                search_results.append(SearchResult(
                    document=document,
                    similarity=float(similarities[idx])
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
        print("[RAG SEARCH RESULTS] Query:", request.query)
        for r in search_results:
            print(f"  - Title: {r.document.title}, Similarity: {r.similarity:.3f}")
        if not search_results:
            print("  - No relevant documents found.")
        
        # --- OLLAMA INTEGRATION ---
        ollama_url = "http://localhost:11434/api/generate"
        prompt = """
You are a helpful assistant. Use the following context to answer the user's question. If the context is not sufficient, say so.

Context:
"""
        if context:
            prompt += context + "\n"
        prompt += f"\nUser question: {request.query}\nAnswer:"
        ollama_payload = {
            "model": "mistral",  # You can change this to your preferred model
            "prompt": prompt,
            "stream": False
        }
        llm_answer = None
        try:
            ollama_response = requests.post(ollama_url, json=ollama_payload, timeout=30)
            ollama_response.raise_for_status()
            llm_data = ollama_response.json()
            llm_answer = llm_data.get("response", "[No answer from LLM]")
        except Exception as e:
            print(f"[OLLAMA ERROR] {e}")
            llm_answer = "[Error: Could not get response from local LLM]"
        
        return RAGResponse(
            context=llm_answer,
            documents=search_results
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching documents: {str(e)}")

@app.get("/documents", response_model=List[Document])
async def list_documents():
    """List all documents in the system"""
    try:
        return [
            Document(
                url=doc["url"],
                title=doc["title"],
                content=doc["content"][:200] + "..." if len(doc["content"]) > 200 else doc["content"],
                timestamp=doc["timestamp"]
            )
            for doc in documents
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")

@app.delete("/clear-documents")
async def clear_documents():
    """Clear all documents from the system"""
    try:
        global documents, embeddings
        documents.clear()
        embeddings.clear()
        return {"success": True, "message": "All documents cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing documents: {str(e)}")

@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    try:
        return {
            "document_count": len(documents),
            "embedding_model": "all-MiniLM-L6-v2",
            "vector_db": "In-Memory (NumPy + scikit-learn)",
            "status": "running"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 