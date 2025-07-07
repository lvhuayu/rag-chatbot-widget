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
from sentence_transformers import SentenceTransformer
import numpy as np
import hmac
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
import rag_storage_prisma as storage

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
    threshold: Optional[float] = 0.2  # Adjusted for better recall with BGE model
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

# 加载中文/多语言 SOTA embedding 模型（如 BAAI/bge-large-zh-v1.5）
# 你可以根据需要更换为其他模型，如 all-MiniLM-L6-v2
embedding_model = SentenceTransformer('BAAI/bge-large-zh-v1.5')

def generate_simple_embedding(text: str) -> list:
    """用 SOTA embedding 生成文本向量，支持中文和多语言"""
    emb = embedding_model.encode(text, normalize_embeddings=True)
    return emb.tolist() if isinstance(emb, np.ndarray) else list(emb)

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

def split_text(text, max_length=300):
    """按结构（表格、标题、空行等）和标点切分长文本为段落，保证每个分段都不丢失"""
    import re
    # 先按空行、表格、标题、列表等结构分段
    blocks = re.split(r'\n\s*\n', text)
    chunks = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        # 再按标点和长度切分
        sentences = re.split(r'(。|！|!|\.|？|\?)', block)
        chunk = ''
        for s in sentences:
            if not s: continue
            if len(chunk) + len(s) > max_length:
                chunks.append(chunk)
                chunk = s
            else:
                chunk += s
        if chunk:
            chunks.append(chunk)
    return [c for c in chunks if c.strip()]

@app.post("/add-documents", response_model=Dict[str, Any])
async def add_documents(documents: List[Document]):
    """批量上传多个文档，每个文档自动分段批量入库"""
    all_results = []
    for doc in documents:
        user_id = doc.user_id or "default_user"
        url = doc.url
        title = doc.title
        timestamp = doc.timestamp or datetime.now().isoformat()
        content = doc.content
        segments = split_text(content, max_length=300)
        results = []
        for idx, chunk in enumerate(segments):
            embedding = generate_simple_embedding(chunk)
            # 为每个分段生成唯一标题，避免唯一约束冲突
            segment_title = f"{title} - 段落{idx+1}"
            result = storage.add_document_with_uniqueness(
                doc_id=None,
                url=url,
                title=segment_title,
                content=chunk,
                user_id=user_id,
                embedding=embedding,
                timestamp=timestamp
            )
            results.append(result)
        all_results.append({
            "title": title,
            "segments": len(results),
            "results": results
        })
    return {
        "success": True,
        "message": f"Batch added {len(documents)} documents.",
        "documents": all_results
    }

@app.post("/search", response_model=RAGResponse)
async def search_documents(request: SearchRequest):
    """Search for relevant document segments with multi-tenant support, 返回 context 来源信息"""
    try:
        user_documents, user_embeddings = storage.get_documents_by_user(request.user_id)
        if not user_documents:
            logger.info(f"No documents available for user: {request.user_id}")
            return RAGResponse(
                context="I don't have any information in my knowledge base to answer your question. Please contact support or check our documentation for more details.",
                documents=[]
            )
        query_embedding = generate_simple_embedding(request.query)
        similarities = []
        for i, doc in enumerate(user_documents):
            if i < len(user_embeddings) and len(user_embeddings[i]) > 0:
                embedding_list = user_embeddings[i].tolist() if hasattr(user_embeddings[i], 'tolist') else user_embeddings[i]
                similarity = calculate_similarity(query_embedding, embedding_list)
                similarities.append((doc, similarity, i))  # i为段号
        similarities.sort(key=lambda x: x[1], reverse=True)
        best_similarity = similarities[0][1] if similarities else 0.0
        quality_threshold = 0.25
        if best_similarity < quality_threshold:
            logger.info(f"Query: '{request.query}', Best similarity {best_similarity:.3f} below quality threshold {quality_threshold}")
            return RAGResponse(
                context="I don't have enough relevant information to answer your question. Please try rephrasing your query or ask about a different topic.",
                documents=[]
            )
        filtered_results = [
            (doc, sim, idx) for doc, sim, idx in similarities 
            if sim >= request.threshold
        ][:request.top_k]
        logger.info(f"Query: '{request.query}', Found: {len(filtered_results)} segments (best: {best_similarity:.3f})")
        for doc, sim, idx in filtered_results:
            logger.info(f"  - Title: {doc['title']}, Segment: {idx}, Similarity: {sim:.3f}")
        search_results = []
        for doc, similarity, idx in filtered_results:
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
        # context 拼接top_k条最相关段内容，不带来源信息
        context = None
        if search_results:
            context_parts = []
            for i, result in enumerate(search_results[:request.top_k]):
                context_parts.append(result.document.content[:1000])
            context = "\n".join(context_parts)
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

@app.post("/rag-generate", response_model=RAGResponse)
async def rag_generate(request: SearchRequest):
    """RAG: Search for relevant documents and generate answer using Ollama"""
    try:
        # Step 1: Search for relevant documents
        user_documents, user_embeddings = storage.get_documents_by_user(request.user_id)
        if not user_documents:
            logger.info(f"No documents available for user: {request.user_id}")
            return RAGResponse(
                context="我的知识库中没有相关信息来回答您的问题。请联系客服或查看我们的文档获取更多详情。",
                documents=[]
            )
        
        query_embedding = generate_simple_embedding(request.query)
        similarities = []
        for i, doc in enumerate(user_documents):
            if i < len(user_embeddings) and len(user_embeddings[i]) > 0:
                embedding_list = user_embeddings[i].tolist() if hasattr(user_embeddings[i], 'tolist') else user_embeddings[i]
                similarity = calculate_similarity(query_embedding, embedding_list)
                similarities.append((doc, similarity, i))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        best_similarity = similarities[0][1] if similarities else 0.0
        quality_threshold = 0.25
        
        if best_similarity < quality_threshold:
            logger.info(f"Query: '{request.query}', Best similarity {best_similarity:.3f} below quality threshold {quality_threshold}")
            return RAGResponse(
                context="我没有足够的相关信息来回答您的问题。请尝试重新表述您的问题或询问其他话题。",
                documents=[]
            )
        
        filtered_results = [
            (doc, sim, idx) for doc, sim, idx in similarities 
            if sim >= request.threshold
        ][:request.top_k]
        
        logger.info(f"Query: '{request.query}', Found: {len(filtered_results)} segments (best: {best_similarity:.3f})")
        for doc, sim, idx in filtered_results:
            logger.info(f"  - Title: {doc['title']}, Segment: {idx}, Similarity: {sim:.3f}")
        
        # Step 2: Prepare context for LLM
        context_parts = []
        search_results = []
        for doc, similarity, idx in filtered_results:
            context_parts.append(doc["content"])
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
        
        context = "\n\n".join(context_parts)
        
        # Step 3: Generate answer using Ollama
        try:
            ollama_response = await generate_with_ollama(request.query, context)
            generated_answer = ollama_response
        except Exception as e:
            logger.error(f"Error generating with Ollama: {e}")
            # Fallback to context if Ollama fails
            generated_answer = f"根据可用的信息：\n\n{context}"
        
        return RAGResponse(
            context=generated_answer,
            documents=search_results
        )
        
    except Exception as e:
        import traceback
        logger.error(f"Error in /rag-generate endpoint: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating answer: {str(e)}")

async def generate_with_ollama(query: str, context: str) -> str:
    """Generate answer using Ollama with RAG context"""
    try:
        # Prepare prompt for RAG
        prompt = f"""你是一个有用的AI助手。请使用以下上下文来回答用户的问题。
如果上下文中的信息不足以回答问题，请说明这一点。

上下文：
{context}

用户问题：{query}

请根据上述上下文提供有用且准确的回答（请用中文回答）："""

        # Call Ollama API
        ollama_url = "http://localhost:11434/api/generate"
        payload = {
            "model": "mistral:latest",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 1000
            }
        }
        
        response = requests.post(ollama_url, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            return result.get("response", "Sorry, I couldn't generate a response.")
        else:
            logger.error(f"Ollama API error: {response.status_code} - {response.text}")
            raise Exception(f"Ollama API returned status {response.status_code}")
            
    except requests.exceptions.Timeout:
        logger.error("Ollama request timed out")
        raise Exception("Request to Ollama timed out")
    except requests.exceptions.ConnectionError:
        logger.error("Cannot connect to Ollama")
        raise Exception("Cannot connect to Ollama. Please make sure Ollama is running.")
    except Exception as e:
        logger.error(f"Error calling Ollama: {e}")
        raise e

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