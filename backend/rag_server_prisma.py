#!/usr/bin/env python3
"""
RAG Chatbot Backend with Prisma Storage (Simple Embeddings)
Unified database using Prisma ORM for both user management and RAG documents
Uses simple character frequency embeddings to avoid PyTorch dependency issues
"""

import os
import sys
import json
import uuid
import secrets
import hashlib
import requests
import logging
import string
import math
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import jwt

# Add the parent directory to the path to import the Prisma storage
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.rag_storage_prisma import PrismaRAGStorage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="RAG Chatbot Backend (Prisma)", version="2.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()
JWT_SECRET = "your-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"

# Initialize storage
storage = PrismaRAGStorage()

# In-memory storage for challenges and sessions (in production, use Redis)
challenges = {}
public_keys = {}
user_sessions = {}

# Pydantic models
class Document(BaseModel):
    url: str
    title: str
    content: str
    timestamp: Optional[str] = None
    user_id: Optional[str] = None

class SearchRequest(BaseModel):
    query: str
    top_k: int = 3
    threshold: Optional[float] = 0.3  # Increased default threshold
    user_id: Optional[str] = None

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

class RegisteredKeyAuthRequest(BaseModel):
    public_key: str
    username: str

class RegisteredKeyAuthResponse(BaseModel):
    token: str
    user_id: str
    username: str
    expires_in: int

def generate_simple_embedding(text: str) -> List[float]:
    """Generate a simple embedding using character frequency (temporary)"""
    # This is a very basic embedding - just for testing
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
    dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
    magnitude1 = math.sqrt(sum(a * a for a in embedding1))
    magnitude2 = math.sqrt(sum(a * a for a in embedding2))
    
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    
    return dot_product / (magnitude1 * magnitude2)

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
    return {"message": "RAG Chatbot Backend API (Prisma)", "status": "running"}

@app.get("/health")
async def health_check():
    db_info = storage.get_database_info()
    return {
        "status": "healthy", 
        "model": "simple-character-frequency", 
        "storage": "Prisma Unified Database",
        "database_info": db_info
    }

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
        
        # Generate user ID from public key
        user_id = hashlib.sha256(request.public_key.encode()).hexdigest()[:24]
        username = challenge_data.get("username", f"user_{user_id[:8]}")
        
        # Generate JWT token
        payload = {
            "id": user_id,
            "username": username,
            "exp": datetime.utcnow() + timedelta(hours=24)
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        # Clean up challenge
        del challenges[request.challenge_id]
        
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
    """Authenticate using a registered public key"""
    try:
        # In a real implementation, you would check against a database of registered keys
        # For now, we'll accept any key and generate a user ID from it
        user_id = hashlib.sha256(request.public_key.encode()).hexdigest()[:24]
        
        # Generate JWT token
        payload = {
            "id": user_id,
            "username": request.username,
            "exp": datetime.utcnow() + timedelta(hours=24)
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        return RegisteredKeyAuthResponse(
            token=token,
            user_id=user_id,
            username=request.username,
            expires_in=86400  # 24 hours
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error authenticating: {str(e)}")

@app.get("/auth/me")
async def get_current_user(current_user: User = Depends(verify_token)):
    """Get current user information"""
    return current_user

@app.post("/add-document", response_model=Dict[str, Any])
async def add_document(document: Document):
    """Add a document to the RAG system with multi-tenant support"""
    try:
        # Generate simple embedding
        embedding = generate_simple_embedding(document.content)
        
        # Add to storage with user_id
        user_id = document.user_id or "default_user"
        
        # Use the storage layer's add_document_with_uniqueness method
        result = storage.add_document_with_uniqueness(
            doc_id=None,  # Let storage generate ID
            url=document.url,
            title=document.title,
            content=document.content,
            user_id=user_id,
            embedding=embedding,
            timestamp=document.timestamp or datetime.now().isoformat()
        )
        
        if not result.get("success"):
            logger.error(f"Prisma storage error: {result.get('error')}")
            raise HTTPException(status_code=500, detail=f"Prisma storage error: {result.get('error')}")
        
        action = result.get("action", "unknown")
        doc_id = result.get("doc_id")
        
        if action == "updated":
            message = f"Updated existing document: {document.title}"
            logger.info(f"Updated existing document: {document.title} (User: {user_id}, ID: {doc_id})")
        else:
            message = f"Added new document: {document.title}"
            logger.info(f"Added new document: {document.title} (User: {user_id}, ID: {doc_id})")
        
        return {
            "success": True,
            "doc_id": doc_id,
            "message": message,
            "action": action
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
        # Get documents for specific user from storage
        user_documents, user_embeddings = storage.get_documents_by_user(request.user_id)
        
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
        for i, doc in enumerate(user_documents):
            if i < len(user_embeddings) and len(user_embeddings[i]) > 0:
                embedding_list = user_embeddings[i].tolist() if hasattr(user_embeddings[i], 'tolist') else user_embeddings[i]
                similarity = calculate_similarity(query_embedding, embedding_list)
                similarities.append((doc, similarity))
        
        # Sort by similarity and filter by threshold
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Check if the best match is too low quality
        best_similarity = similarities[0][1] if similarities else 0.0
        quality_threshold = 0.45  # Increased quality threshold to reject nonsense queries
        
        if best_similarity < quality_threshold:
            logger.info(f"Query: '{request.query}', Best similarity {best_similarity:.3f} below quality threshold {quality_threshold}")
            return RAGResponse(
                context="I don't have enough relevant information to answer your question. Please try rephrasing your query or ask about a different topic.",
                documents=[]
            )
        
        # Filter by user-specified threshold
        filtered_results = [
            (doc, sim) for doc, sim in similarities 
            if sim >= request.threshold
        ][:request.top_k]
        
        # Log results
        logger.info(f"Query: '{request.query}', Found: {len(filtered_results)} documents (best: {best_similarity:.3f})")
        for doc, sim in filtered_results:
            logger.info(f"  - Title: {doc['title']}, Similarity: {sim:.3f}")
        
        # Convert to response format
        search_results = []
        for doc, similarity in filtered_results:
            search_results.append(SearchResult(
                document=Document(
                    url=doc["url"],
                    title=doc["title"],
                    content=doc["content"],
                    timestamp=doc["timestamp"],
                    user_id=doc["user_id"]
                ),
                similarity=similarity
            ))
        
        # Generate context from top results
        context = None
        if search_results:
            context_parts = []
            for result in search_results[:2]:  # Use top 2 results for context
                context_parts.append(f"From '{result.document.title}': {result.document.content[:200]}...")
            context = " ".join(context_parts)
        
        return RAGResponse(
            context=context,
            documents=search_results
        )
        
    except Exception as e:
        import traceback
        logger.error(f"Error in /search endpoint: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error searching documents: {str(e)}")

@app.get("/documents", response_model=List[Document])
async def list_documents(user_id: Optional[str] = None):
    """List all documents for a user or all documents if no user specified"""
    try:
        if user_id:
            documents, _ = storage.get_documents_by_user(user_id)
        else:
            documents, _ = storage.get_all_documents()
        
        logger.info(f"Returning {len(documents)} documents for user: {user_id or 'all'}")
        
        return [
            Document(
                url=doc["url"],
                title=doc["title"],
                content=doc["content"],
                timestamp=doc["timestamp"],
                user_id=doc["user_id"]
            )
            for doc in documents
        ]
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")

@app.delete("/clear-documents")
async def clear_documents(user_id: Optional[str] = None):
    """Clear all documents for a user or all documents if no user specified"""
    try:
        if user_id:
            storage.clear_documents_by_user(user_id)
            return {"message": f"Cleared all documents for user: {user_id}"}
        else:
            storage.clear_all_documents()
            return {"message": "Cleared all documents"}
    except Exception as e:
        logger.error(f"Error clearing documents: {e}")
        raise HTTPException(status_code=500, detail=f"Error clearing documents: {str(e)}")

@app.get("/stats")
async def get_stats(user_id: Optional[str] = None):
    """Get statistics about documents"""
    try:
        stats = storage.get_user_stats(user_id)
        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting RAG Chatbot Backend with Prisma Storage...")
    print("📊 Database: Unified Prisma SQLite")
    print("🧠 Model: Simple Character Frequency")
    print("🔗 API: http://localhost:8001")
    print("📚 Health: http://localhost:8001/health")
    print("=" * 50)
    
    # Check Ollama status
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            print(f"✅ Ollama is running with models: {len(models)}")
        else:
            print("⚠️  Ollama not responding properly")
    except Exception as e:
        print(f"⚠️  Ollama not accessible: {e}")
    
    print("🔄 Starting server...")
    uvicorn.run(app, host="0.0.0.0", port=8001) 