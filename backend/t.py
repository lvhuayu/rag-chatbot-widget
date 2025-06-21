from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import chromadb
from sentence_transformers import SentenceTransformer
import uuid
from datetime import datetime
import json
import jwt
from functools import wraps

app = FastAPI(title="RAG Chatbot Backend", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT Configuration
JWT_SECRET = "your-secret-key"  # In production, use environment variable
JWT_ALGORITHM = "HS256"

# Security scheme
security = HTTPBearer()

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
    user_id: Optional[str] = None  # Add user_id field

class SearchRequest(BaseModel):
    query: str
    top_k: int = 3
    threshold: Optional[float] = 0.0

class SearchResult(BaseModel):
    document: Document
    similarity: float

class RAGResponse(BaseModel):
    context: Optional[str]
    documents: List[SearchResult]

class User(BaseModel):
    id: str
    username: str

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Verify JWT token and return user information"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("id")
        username = payload.get("username")
        
        if user_id is None or username is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
            
        return User(id=user_id, username=username)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication error: {str(e)}")

@app.get("/")
async def root():
    return {"message": "RAG Chatbot Backend API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "model": "all-MiniLM-L6-v2"}

@app.post("/add-document", response_model=Dict[str, Any])
async def add_document(document: Document, user: User = Depends(verify_token)):
    """Add a document to the RAG system (requires authentication)"""
    try:
        # Generate embedding
        embedding = embedding_model.encode(document.content).tolist()
        
        # Add to ChromaDB with user_id in metadata
        doc_id = str(uuid.uuid4())
        collection.add(
            embeddings=[embedding],
            documents=[document.content],
            metadatas=[{
                "url": document.url,
                "title": document.title,
                "timestamp": document.timestamp or datetime.now().isoformat(),
                "user_id": user.id  # Store user_id in metadata
            }],
            ids=[doc_id]
        )
        
        return {
            "success": True,
            "doc_id": doc_id,
            "message": f"Document '{document.title}' added successfully for user {user.username}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding document: {str(e)}")

@app.post("/search", response_model=RAGResponse)
async def search_documents(request: SearchRequest, user: User = Depends(verify_token)):
    """Search for relevant documents (requires authentication, user-scoped)"""
    try:
        # Generate query embedding
        query_embedding = embedding_model.encode(request.query).tolist()
        
        # Search in ChromaDB with user filter
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=request.top_k,
            where={"user_id": user.id}  # Filter by user_id
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
                
                # Apply threshold filter
                if similarity < request.threshold:
                    continue
                
                document = Document(
                    url=metadata['url'],
                    title=metadata['title'],
                    content=doc_content,
                    timestamp=metadata['timestamp'],
                    user_id=metadata.get('user_id')
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
        
        print(f"[RAG SEARCH] User: {user.username}, Query: '{request.query}', Found: {len(search_results)} documents")
        
        return RAGResponse(
            context=context,
            documents=search_results
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching documents: {str(e)}")

@app.get("/documents", response_model=List[Document])
async def list_documents(user: User = Depends(verify_token)):
    """List all documents for the authenticated user"""
    try:
        # Get documents filtered by user_id
        results = collection.get(
            where={"user_id": user.id}
        )
        
        documents = []
        if results['documents']:
            for doc_content, metadata in zip(results['documents'], results['metadatas']):
                document = Document(
                    url=metadata['url'],
                    title=metadata['title'],
                    content=doc_content[:200] + "..." if len(doc_content) > 200 else doc_content,
                    timestamp=metadata['timestamp'],
                    user_id=metadata.get('user_id')
                )
                documents.append(document)
        
        return documents
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")

@app.delete("/clear-documents")
async def clear_documents(user: User = Depends(verify_token)):
    """Clear all documents for the authenticated user"""
    try:
        # Get all documents for the user
        results = collection.get(
            where={"user_id": user.id}
        )
        
        if results['ids']:
            # Delete user's documents
            collection.delete(ids=results['ids'])
            return {"success": True, "message": f"Cleared {len(results['ids'])} documents for user {user.username}"}
        else:
            return {"success": True, "message": "No documents to clear"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing documents: {str(e)}")

@app.get("/stats")
async def get_stats(user: User = Depends(verify_token)):
    """Get system statistics for the authenticated user"""
    try:
        # Get user's documents
        results = collection.get(
            where={"user_id": user.id}
        )
        doc_count = len(results['documents']) if results['documents'] else 0
        
        return {
            "user_id": user.id,
            "username": user.username,
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