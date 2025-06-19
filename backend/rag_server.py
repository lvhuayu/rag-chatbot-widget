from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import chromadb
from sentence_transformers import SentenceTransformer
import uuid
from datetime import datetime
import json

app = FastAPI(title="RAG Chatbot Backend", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize embedding model and vector database
print("Loading embedding model...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

print("Initializing ChromaDB...")
chroma_client = chromadb.Client()
collection = chroma_client.create_collection(
    name="rag_documents",
    metadata={"hnsw:space": "cosine"}
)

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
    return {"message": "RAG Chatbot Backend API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "model": "all-MiniLM-L6-v2"}

@app.post("/add-document", response_model=Dict[str, Any])
async def add_document(document: Document):
    """Add a document to the RAG system"""
    try:
        # Generate embedding
        embedding = embedding_model.encode(document.content).tolist()
        
        # Add to ChromaDB
        doc_id = str(uuid.uuid4())
        collection.add(
            embeddings=[embedding],
            documents=[document.content],
            metadatas=[{
                "url": document.url,
                "title": document.title,
                "timestamp": document.timestamp or datetime.now().isoformat()
            }],
            ids=[doc_id]
        )
        
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
        # Generate query embedding
        query_embedding = embedding_model.encode(request.query).tolist()
        
        # Search in ChromaDB
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=request.top_k
        )
        
        # Format results
        search_results = []
        if results['documents'] and results['documents'][0]:
            for i, (doc_content, metadata, distance) in enumerate(zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            )):
                # Convert distance to similarity (ChromaDB returns distance, we want similarity)
                similarity = 1 - distance
                
                document = Document(
                    url=metadata['url'],
                    title=metadata['title'],
                    content=doc_content,
                    timestamp=metadata['timestamp']
                )
                
                search_results.append(SearchResult(
                    document=document,
                    similarity=similarity
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
        
        return RAGResponse(
            context=context,
            documents=search_results
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching documents: {str(e)}")

@app.get("/documents", response_model=List[Document])
async def list_documents():
    """List all documents in the system"""
    try:
        results = collection.get()
        
        documents = []
        if results['documents']:
            for doc_content, metadata in zip(results['documents'], results['metadatas']):
                document = Document(
                    url=metadata['url'],
                    title=metadata['title'],
                    content=doc_content[:200] + "..." if len(doc_content) > 200 else doc_content,
                    timestamp=metadata['timestamp']
                )
                documents.append(document)
        
        return documents
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")

@app.delete("/clear-documents")
async def clear_documents():
    """Clear all documents from the system"""
    try:
        global collection
        chroma_client.delete_collection("rag_documents")
        collection = chroma_client.create_collection(
            name="rag_documents",
            metadata={"hnsw:space": "cosine"}
        )
        return {"success": True, "message": "All documents cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing documents: {str(e)}")

@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    try:
        results = collection.get()
        doc_count = len(results['documents']) if results['documents'] else 0
        
        return {
            "document_count": doc_count,
            "embedding_model": "all-MiniLM-L6-v2",
            "vector_db": "ChromaDB",
            "status": "running"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 