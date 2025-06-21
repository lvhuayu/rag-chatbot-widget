from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sentence_transformers import SentenceTransformer
import uuid
from datetime import datetime, timedelta
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import json
import requests
import jwt
import secrets
import hashlib
import base64
from functools import wraps

app = FastAPI(title="RAG Chatbot Backend (Simple)", version="1.0.0")

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

# In-memory storage for challenges and public keys
challenges = {}  # {challenge_id: {"challenge": str, "public_key": str, "timestamp": datetime}}
public_keys = {}  # {user_id: public_key}
user_sessions = {}  # {user_id: {"username": str, "public_key": str}}

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

class ChallengeRequest(BaseModel):
    public_key: str
    username: Optional[str] = None

class ChallengeResponse(BaseModel):
    challenge_id: str
    challenge: str
    expires_in: int

class VerifyChallengeRequest(BaseModel):
    challenge_id: str
    public_key: str
    signature: str

class VerifyChallengeResponse(BaseModel):
    token: str
    user_id: str
    username: str
    expires_in: int

# Add new model for registered key authentication
class RegisteredKeyAuthRequest(BaseModel):
    public_key: str
    username: str

class RegisteredKeyAuthResponse(BaseModel):
    token: str
    user_id: str
    username: str
    expires_in: int

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

def verify_signature(public_key: str, challenge: str, signature: str) -> bool:
    """Verify signature using public key (simplified implementation)"""
    try:
        # In a real implementation, you would use cryptography library
        # For now, we'll use a simple hash-based verification
        expected_signature = hashlib.sha256(f"{public_key}:{challenge}".encode()).hexdigest()
        return signature == expected_signature
    except Exception:
        return False

@app.get("/")
async def root():
    return {"message": "RAG Chatbot Backend API (Simple)", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "model": "all-MiniLM-L6-v2", "storage": "in-memory"}

@app.post("/auth/request-challenge", response_model=ChallengeResponse)
async def request_challenge(request: ChallengeRequest):
    """Request a challenge for public key authentication"""
    try:
        # Generate a random challenge
        challenge = secrets.token_urlsafe(32)
        challenge_id = str(uuid.uuid4())
        
        # Store challenge with expiration (5 minutes)
        challenges[challenge_id] = {
            "challenge": challenge,
            "public_key": request.public_key,
            "username": request.username,
            "timestamp": datetime.now()
        }
        
        # Clean up expired challenges
        expired_challenges = [
            cid for cid, data in challenges.items()
            if datetime.now() - data["timestamp"] > timedelta(minutes=5)
        ]
        for cid in expired_challenges:
            del challenges[cid]
        
        return ChallengeResponse(
            challenge_id=challenge_id,
            challenge=challenge,
            expires_in=300  # 5 minutes
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating challenge: {str(e)}")

@app.post("/auth/verify-challenge", response_model=VerifyChallengeResponse)
async def verify_challenge(request: VerifyChallengeRequest):
    """Verify challenge signature and issue JWT token"""
    try:
        # Get challenge data
        challenge_data = challenges.get(request.challenge_id)
        if not challenge_data:
            raise HTTPException(status_code=400, detail="Invalid or expired challenge")
        
        # Check if challenge is expired
        if datetime.now() - challenge_data["timestamp"] > timedelta(minutes=5):
            del challenges[request.challenge_id]
            raise HTTPException(status_code=400, detail="Challenge expired")
        
        # Verify public key matches
        if challenge_data["public_key"] != request.public_key:
            raise HTTPException(status_code=400, detail="Public key mismatch")
        
        # Verify signature
        if not verify_signature(request.public_key, challenge_data["challenge"], request.signature):
            raise HTTPException(status_code=400, detail="Invalid signature")
        
        # Generate user ID and store public key
        user_id = str(uuid.uuid4())
        username = challenge_data.get("username", f"user_{user_id[:8]}")
        
        public_keys[user_id] = request.public_key
        user_sessions[user_id] = {
            "username": username,
            "public_key": request.public_key
        }
        
        # Generate JWT token
        token_payload = {
            "id": user_id,
            "username": username,
            "exp": datetime.utcnow() + timedelta(hours=24)
        }
        token = jwt.encode(token_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        # Clean up challenge
        del challenges[request.challenge_id]
        
        print(f"[AUTH] New user authenticated: {username} (ID: {user_id})")
        
        return VerifyChallengeResponse(
            token=token,
            user_id=user_id,
            username=username,
            expires_in=86400  # 24 hours
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error verifying challenge: {str(e)}")

@app.post("/auth/register-key", response_model=RegisteredKeyAuthResponse)
async def authenticate_with_registered_key(request: RegisteredKeyAuthRequest):
    """Authenticate using a registered public key (simplified authentication)"""
    try:
        # For registered keys, we trust the public key as authentication
        # In a real implementation, you might want to verify this against a database
        
        # Generate user ID
        user_id = str(uuid.uuid4())
        username = request.username
        
        # Store public key
        public_keys[user_id] = request.public_key
        user_sessions[user_id] = {
            "username": username,
            "public_key": request.public_key
        }
        
        # Generate JWT token
        token_payload = {
            "id": user_id,
            "username": username,
            "exp": datetime.utcnow() + timedelta(hours=24)
        }
        token = jwt.encode(token_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        print(f"[AUTH] Registered key authentication: {username} (ID: {user_id})")
        
        return RegisteredKeyAuthResponse(
            token=token,
            user_id=user_id,
            username=username,
            expires_in=86400  # 24 hours
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error authenticating with registered key: {str(e)}")

@app.get("/auth/me")
async def get_current_user(user: User = Depends(verify_token)):
    """Get current user information"""
    return {
        "user_id": user.id,
        "username": user.username,
        "public_key": public_keys.get(user.id, "Not found")
    }

@app.post("/add-document", response_model=Dict[str, Any])
async def add_document(document: Document, user: User = Depends(verify_token)):
    """Add a document to the RAG system (requires authentication)"""
    try:
        # Generate embedding
        embedding = embedding_model.encode(document.content).tolist()
        
        # Add to in-memory storage with user_id
        doc_id = str(uuid.uuid4())
        documents.append({
            "id": doc_id,
            "url": document.url,
            "title": document.title,
            "content": document.content,
            "timestamp": document.timestamp or datetime.now().isoformat(),
            "user_id": user.id  # Store user_id
        })
        embeddings.append(embedding)
        
        return {
            "success": True,
            "doc_id": doc_id,
            "message": f"Document '{document.title}' added successfully for user {user.username}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding document: {str(e)}")

@app.post("/search", response_model=RAGResponse)
async def search_documents(request: SearchRequest):
    """Search for relevant documents (no authentication, not user-scoped)"""
    try:
        # Use all documents for search
        if not documents:
            # No documents found, but still provide LLM response
            print(f"[RAG SEARCH] Query: '{request.query}', No documents available")
            
            # --- OLLAMA INTEGRATION ---
            ollama_url = "http://localhost:11434/api/generate"
            prompt = f"""
You are a helpful assistant. The user has asked: {request.query}

Please provide a helpful response to their question. If you don't have enough information to answer accurately, say so and provide what you can.

Answer:"""
            
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
                documents=[]
            )
        
        # Generate query embedding
        query_embedding = embedding_model.encode(request.query).reshape(1, -1)
        
        # Calculate similarities
        doc_embeddings = np.array(embeddings)
        similarities = cosine_similarity(query_embedding, doc_embeddings)[0]
        
        # Get top k results
        top_indices = np.argsort(similarities)[::-1][:request.top_k]
        
        search_results = []
        for idx in top_indices:
            similarity = similarities[idx]
            # Apply threshold filter
            if similarity < request.threshold:
                continue
            if similarity > 0:  # Only include relevant results
                doc = documents[idx]
                document = Document(
                    url=doc["url"],
                    title=doc["title"],
                    content=doc["content"],
                    timestamp=doc["timestamp"],
                    user_id=doc.get("user_id")
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
        print(f"[RAG SEARCH] Query: '{request.query}', Found: {len(search_results)} documents")
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
async def list_documents(user: User = Depends(verify_token)):
    """List all documents for the authenticated user"""
    try:
        # Filter documents by user_id
        user_documents = [doc for doc in documents if doc.get("user_id") == user.id]
        
        return [
            Document(
                url=doc["url"],
                title=doc["title"],
                content=doc["content"][:200] + "..." if len(doc["content"]) > 200 else doc["content"],
                timestamp=doc["timestamp"],
                user_id=doc.get("user_id")
            )
            for doc in user_documents
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")

@app.delete("/clear-documents")
async def clear_documents(user: User = Depends(verify_token)):
    """Clear all documents for the authenticated user"""
    try:
        global documents, embeddings
        
        # Find indices of user's documents
        user_indices = [i for i, doc in enumerate(documents) if doc.get("user_id") == user.id]
        
        # Remove user's documents and embeddings (in reverse order to maintain indices)
        for idx in reversed(user_indices):
            documents.pop(idx)
            embeddings.pop(idx)
        
        return {"success": True, "message": f"Cleared {len(user_indices)} documents for user {user.username}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing documents: {str(e)}")

@app.get("/stats")
async def get_stats(user: User = Depends(verify_token)):
    """Get system statistics for the authenticated user"""
    try:
        # Count user's documents
        user_document_count = len([doc for doc in documents if doc.get("user_id") == user.id])
        
        return {
            "user_id": user.id,
            "username": user.username,
            "document_count": user_document_count,
            "total_documents": len(documents),
            "embedding_model": "all-MiniLM-L6-v2",
            "vector_db": "In-Memory (NumPy + scikit-learn)",
            "status": "running"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 