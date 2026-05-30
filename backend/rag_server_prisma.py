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
from fastapi import FastAPI, HTTPException, Depends, status, Request, Header, Body
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
import sqlite3
from openai import OpenAI, AzureOpenAI
from fastapi.responses import StreamingResponse
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import aioredis

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
    # Widget (chatbot.js) embeds on arbitrary customer sites, so any Origin must be
    # allowed at the CORS layer. Real tenant control happens in /auth/token, which
    # validates the apiKey against its registered allowed_origins.
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Security
security = HTTPBearer()
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"

# Initialize storage
storage = PrismaRAGStorage()

# ===== 套餐每日对话限额（按 plan_id；None = 不限）=====
import redis as _redis_lib
_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rag_database.db")
_quota_redis = _redis_lib.Redis(host="localhost", port=6379, db=0, decode_responses=True)
PLAN_DAILY_CHATS = {"free": 100, "pro": 2000, "enterprise": None}

def _resolve_plan_id(site_id: str) -> str:
    try:
        now_ms = int(datetime.utcnow().timestamp() * 1000)
        conn = sqlite3.connect(_DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "SELECT plan_id FROM site_subscriptions WHERE site_id=? AND (expire_date IS NULL OR expire_date > ?) ORDER BY start_date DESC LIMIT 1",
            (site_id, now_ms),
        )
        row = cur.fetchone()
        conn.close()
        return row[0] if row else "free"
    except Exception:
        return "free"

def check_daily_quota(site_id: str):
    """返回 (allowed, limit, count)；allowed 时把今日计数 +1。Redis 故障时放行。"""
    plan_id = _resolve_plan_id(site_id)
    limit = PLAN_DAILY_CHATS.get(plan_id, 100)
    if limit is None:
        return True, None, 0
    try:
        key = "chatquota:%s:%s" % (site_id, datetime.utcnow().strftime("%Y%m%d"))
        cnt = _quota_redis.incr(key)
        if cnt == 1:
            _quota_redis.expire(key, 90000)  # ~25h
        return cnt <= limit, limit, cnt
    except Exception:
        return True, limit, 0

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
    site_id: Optional[str] = None

class SearchRequest(BaseModel):
    query: str
    top_k: int = 3
    threshold: Optional[float] = 0.2  # Adjusted for better recall with BGE model
    site_id: Optional[str] = None
    history: Optional[List[Dict[str, str]]] = None  # 新增多轮对话历史

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

class SiteTokenRequest(BaseModel):
    siteId: str

class SiteTokenResponse(BaseModel):
    token: str
    siteId: str
    expires_in: int

# 加载中文/多语言 SOTA embedding 模型（如 BAAI/bge-large-zh-v1.5）
# 你可以根据需要更换为其他模型，如 all-MiniLM-L6-v2
embedding_model = SentenceTransformer('BAAI/bge-large-zh-v1.5')
# embedding_model = SentenceTransformer(os.path.join(os.path.dirname(__file__), 'bge-large-zh-v1.5'))

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

# --- Admin Authentication ---
class AdminLoginRequest(BaseModel):
    username: str
    password: str

class AdminLoginResponse(BaseModel):
    token: str
    expires_in: int

# Admin credentials (from env; do NOT hardcode in production)
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# Admin JWT verification
def verify_admin_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if not payload.get("is_admin"):
            raise HTTPException(status_code=403, detail="Admin privileges required")
        return User(id=payload.get("id", "admin"), username=payload.get("username", "admin"))
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication error: {str(e)}")

@app.post("/admin/login", response_model=AdminLoginResponse)
async def admin_login(request: AdminLoginRequest):
    if request.username == ADMIN_USERNAME and request.password == ADMIN_PASSWORD:
        payload = {
            "id": "admin",
            "username": ADMIN_USERNAME,
            "is_admin": True,
            "exp": datetime.utcnow() + timedelta(hours=8)
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return AdminLoginResponse(token=token, expires_in=8*3600)
    else:
        raise HTTPException(status_code=401, detail="Invalid admin credentials")

@app.post("/admin/token", response_model=AdminLoginResponse)
async def admin_token_from_basic(authorization: Optional[str] = Header(None)):
    """单次登录辅助：此接口位于 nginx Basic 认证保护的 /rag/ 之后，浏览器会自动带上
    已缓存的 Basic 凭据。若凭据有效即直接签发与 /admin/login 相同的管理员 JWT，
    从而免去 dashboard 的第二次表单登录。"""
    if not authorization or not authorization.lower().startswith("basic "):
        raise HTTPException(status_code=401, detail="Basic credentials required")
    try:
        decoded = base64.b64decode(authorization.split(" ", 1)[1]).decode("utf-8")
        user, _, pw = decoded.partition(":")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid Basic header")
    if user == ADMIN_USERNAME and pw == ADMIN_PASSWORD:
        payload = {
            "id": "admin",
            "username": ADMIN_USERNAME,
            "is_admin": True,
            "exp": datetime.utcnow() + timedelta(hours=8)
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return AdminLoginResponse(token=token, expires_in=8*3600)
    raise HTTPException(status_code=401, detail="Invalid admin credentials")

# --- User Management Endpoints (admin only) ---
@app.get("/users")
async def list_users(credentials: HTTPAuthorizationCredentials = Depends(security)):
    user = verify_admin_token(credentials)
    users = storage.get_all_users()
    return users

@app.put("/users/{user_id}")
async def edit_user(user_id: str, data: dict = Body(...), credentials: HTTPAuthorizationCredentials = Depends(security)):
    user = verify_admin_token(credentials)
    ok = storage.update_user(user_id, data)
    return {"success": ok, "user_id": user_id, "updated": data}

@app.delete("/users/{user_id}")
async def delete_user(user_id: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    user = verify_admin_token(credentials)
    try:
        ok = storage.delete_user(user_id)
        if ok:
            return {"success": True, "user_id": user_id}
        else:
            return {"success": False, "user_id": user_id, "error": "Failed to delete user. See backend logs for details."}
    except Exception as e:
        return {"success": False, "user_id": user_id, "error": str(e)}

# --- Logs Endpoint (admin only) ---
@app.get("/logs")
async def get_logs(credentials: HTTPAuthorizationCredentials = Depends(security)):
    user = verify_admin_token(credentials)
    logs = storage.get_logs()
    return logs

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

@app.post("/auth/token", response_model=SiteTokenResponse)
async def get_token_by_apikey(request: Request):
    """通过apiKey换取JWT token，后端查siteId签发token，不信任前端siteId"""
    try:
        data = await request.json()
        api_key = data.get('apiKey') or data.get('api_key')
        if not api_key:
            raise HTTPException(status_code=400, detail="apiKey is required")
        DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "rag_database.db"))
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT site_id, allowed_origins FROM api_keys WHERE api_key = ? AND is_active = 1", (api_key,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            raise HTTPException(status_code=401, detail="Invalid or inactive apiKey")
        site_id, allowed_origins = row
        payload = {
            "siteId": site_id,
            # "origin": origin,  # 不再校验 origin
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return SiteTokenResponse(token=token, siteId=site_id, expires_in=3600)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating token: {str(e)}")

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
    # 合并过短的段
    merged = []
    for c in chunks:
        if merged and len(merged[-1]) < 100:
            merged[-1] += c
        else:
            merged.append(c)
    return [c for c in merged if c.strip()]

@app.post("/add-documents", response_model=Dict[str, Any])
async def add_documents(documents: List[Document]):
    """批量上传多个文档，每个文档自动分段批量入库"""
    all_results = []
    for doc in documents:
        site_id = doc.site_id or "default_site"
        url = doc.url
        title = doc.title
        timestamp = doc.timestamp or datetime.now().isoformat()
        content = doc.content
        segments = split_text(content, max_length=300)
        # Create the document entry ONCE (with full content)
        document_id = storage.add_document_entry(
            url=url,
            title=title,
            content=content,
            site_id=site_id,
            timestamp=timestamp
        )
        results = []
        for idx, chunk in enumerate(segments):
            embedding = generate_simple_embedding(chunk)
            embedding_id = storage.add_embedding(
                document_id=document_id,
                site_id=site_id,
                embedding=embedding,
                timestamp=timestamp
            )
            results.append({
                "embedding_id": embedding_id,
                "chunk_index": idx,
                "chunk_length": len(chunk)
            })
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

# 新增：直接接收爬取数据的 API
class ScrapedDocument(BaseModel):
    text: str
    metadata: Dict[str, Any]

class ScrapedDataRequest(BaseModel):
    site_id: str
    documents: List[ScrapedDocument]

@app.post("/add-scraped-data", response_model=Dict[str, Any])
async def add_scraped_data(request: ScrapedDataRequest):
    """直接接收爬虫数据并存储到向量数据库"""
    try:
        logger.info(f"开始处理爬取数据，站点: {request.site_id}, 文档数: {len(request.documents)}")
        
        all_results = []
        total_chunks = 0
        
        for doc in request.documents:
            try:
                # 提取文档信息
                text = doc.text
                metadata = doc.metadata
                url = metadata.get('url', '')
                title = metadata.get('title', 'No title')
                source = metadata.get('source', url)
                
                # 文本切块
                segments = split_text(text, max_length=300)
                
                # 创建文档条目
                document_id = storage.add_document_entry(
                    url=url,
                    title=title,
                    content=text,
                    site_id=request.site_id,
                    timestamp=datetime.now().isoformat()
                )
                
                # 为每个切块生成 embedding 并存储
                chunk_results = []
                for idx, chunk in enumerate(segments):
                    embedding = generate_simple_embedding(chunk)
                    embedding_id = storage.add_embedding(
                        document_id=document_id,
                        site_id=request.site_id,
                        embedding=embedding,
                        timestamp=datetime.now().isoformat()
                    )
                    chunk_results.append({
                        "embedding_id": embedding_id,
                        "chunk_index": idx,
                        "chunk_length": len(chunk)
                    })
                    total_chunks += 1
                
                all_results.append({
                    "title": title,
                    "url": url,
                    "segments": len(chunk_results),
                    "results": chunk_results
                })
                
                logger.info(f"✅ 处理文档: {title} -> {len(chunk_results)} 个切块")
                
            except Exception as e:
                logger.error(f"❌ 处理文档失败: {str(e)}")
                all_results.append({
                    "title": "Error",
                    "error": str(e),
                    "segments": 0,
                    "results": []
                })
        
        return {
            "success": True,
            "site_id": request.site_id,
            "total_documents": len(request.documents),
            "total_chunks": total_chunks,
            "processed_documents": len(all_results),
            "message": f"成功处理 {len(request.documents)} 个文档，生成 {total_chunks} 个向量",
            "documents": all_results
        }
        
    except Exception as e:
        logger.error(f"❌ 处理爬取数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"处理爬取数据失败: {str(e)}")

CHITCHAT_KEYWORDS = [
    "hi", "hello", "你好", "哈喽", "嗨", "在吗", "您好", "hey", "早上好", "下午好", "晚上好"
]

def is_chitchat(query: str) -> bool:
    q = query.lower().strip()
    return any(kw in q for kw in CHITCHAT_KEYWORDS)

@app.post("/search", response_model=RAGResponse)
async def search_documents(request: SearchRequest):
    # 闲聊意图识别
    if is_chitchat(request.query):
        return RAGResponse(
            context="你好！我是智能助手，有什么可以帮您？",
            documents=[]
        )
    """Search for relevant document segments with multi-tenant support, 返回 context 来源信息"""
    try:
        user_documents, user_embeddings = storage.get_documents_by_site(request.site_id)
        if not user_documents:
            logger.info(f"No documents available for site: {request.site_id}")
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
                    timestamp=doc.get("timestamp") or doc.get("created_at"),
                    site_id=doc["site_id"]
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
async def list_documents(site_id: Optional[str] = None):
    """List all documents for a site or all documents if no site specified"""
    try:
        if site_id:
            documents, _ = storage.get_documents_by_site(site_id)
        else:
            documents, _ = storage.get_all_documents()
        logger.info(f"Returning {len(documents)} documents for site: {site_id or 'all'}")
        return [
            Document(
                url=doc["url"],
                title=doc["title"],
                content=doc["content"],
                timestamp=doc.get("timestamp") or doc.get("created_at"),
                site_id=doc["site_id"]
            )
            for doc in documents
        ]
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")

@app.delete("/clear-documents")
async def clear_documents(site_id: Optional[str] = None):
    """Clear all documents for a site or all documents if no site specified"""
    try:
        if site_id:
            storage.clear_documents_by_user(site_id)
            return {"message": f"Cleared all documents for site: {site_id}"}
        else:
            storage.clear_all_documents()
            return {"message": "Cleared all documents"}
    except Exception as e:
        logger.error(f"Error clearing documents: {e}")
        raise HTTPException(status_code=500, detail=f"Error clearing documents: {str(e)}")

@app.get("/stats")
async def get_stats(site_id: Optional[str] = None):
    """Get statistics about documents"""
    try:
        stats = storage.get_user_stats(site_id)
        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")

import random
from fastapi import HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials

@app.post("/rag-generate")
async def rag_generate(request: SearchRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    # 闲聊意图识别
    if is_chitchat(request.query):
        def chitchat_stream():
            yield f"data: 你好！我是智能助手，有什么可以帮您？\n\n"
        return StreamingResponse(chitchat_stream(), media_type="text/event-stream")

    def get_friendly_fallback_response(query: str) -> str:
        suggestions = {
            "退货": ["如何退货？", "退货流程是怎样的？"],
            "发票": ["如何开具发票？", "电子发票支持吗？"],
            "客服": ["客服电话是多少？", "如何联系人工客服？"],
        }
        fallback_templates = [
            "这个问题我还不太了解，但我正在努力学习中 😊",
            "我暂时没有找到确切答案，也许我们可以换个方式问问？",
            "目前我的知识库中没有明确的信息，您可以联系客服进一步了解。",
        ]
        matched_suggestions = []
        for keyword, guesses in suggestions.items():
            if keyword in query:
                matched_suggestions = guesses
                break
        hint_block = ""
        if matched_suggestions:
            hint_block = "\n\n您可能想问：\n" + "\n".join(f"- {s}" for s in matched_suggestions)
        return random.choice(fallback_templates) + hint_block

    async def event_stream():
        try:
            # Step 0: 校验token并提取siteId
            try:
                payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
                site_id = payload.get("siteId")
                if not site_id:
                    yield f"data: [ERROR] Invalid token: missing siteId\n\n"
                    return
            except Exception as e:
                yield f"data: [ERROR] Invalid or expired token: {str(e)}\n\n"
                return

            # Step 0.5: 每日对话次数限额（按套餐）
            allowed, qlimit, qcount = check_daily_quota(site_id)
            if not allowed:
                yield f"data: 今日对话次数已达上限（{qlimit} 次/天），请升级套餐后继续使用。\n\n"
                return

            # Step 1: Search for relevant documents
            user_documents, user_embeddings = storage.get_documents_by_site(site_id)
            if not user_documents:
                yield f"data: 我的知识库中没有相关信息来回答您的问题。请联系客服或查看我们的文档获取更多详情。\n\n"
                return

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
                yield f"data: {get_friendly_fallback_response(request.query)}\n\n"
                return

            filtered_results = [
                (doc, sim, idx) for doc, sim, idx in similarities 
                if sim >= request.threshold
            ][:max(request.top_k, 10)]

            def query_terms_match(text, query):
                query_terms = query.split()
                return any(term in text for term in query_terms)

            context_parts = []
            priority_snippets = []
            other_snippets = []
            for doc, similarity, idx in filtered_results:
                content = doc["content"]
                if query_terms_match(content, request.query):
                    priority_snippets.append((content, similarity))
                else:
                    other_snippets.append((content, similarity))
            priority_snippets.sort(key=lambda x: x[1], reverse=True)
            other_snippets.sort(key=lambda x: x[1], reverse=True)
            context_parts.extend([content for content, _ in priority_snippets[:3]])
            if len(context_parts) < request.top_k:
                context_parts.extend([content for content, _ in other_snippets[:request.top_k - len(context_parts)]])
            context = "\n\n".join(context_parts)

            # Step 2: LLM流式生成 (Azure OpenAI)
            client = AzureOpenAI(
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview"),
            )
            prompt = f"""
                         你是一位专业的中文 AI 客服助手，专门基于提供的知识内容，准确、清晰地回答用户提出的问题。
                        
                        【上下文信息】
                         {context}

                        【用户问题】
                         {request.query}

                        【回答要求】
                         1. 仅根据上述上下文信息和历史对话作答，不能编造或推测。
                         2. 若上下文信息中包含电话号码、时间、地点等，请直接引用并明确告知用户。
                         3. 若上下文中没有足够信息，请根据情况， 自行回答，尽量不要虚构内容。
                         4. 回答应尽量简洁明了，语气自然亲切，使用中文。
                         5. 若内容复杂，可适当使用换行、编号等格式提升可读性。编号尽量少一些，可以通过描述来补充。

                         现在请开始回答：
                    """             
            response = client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1"),
                messages=[
                    {"role": "system", "content": "你是一个专业的AI助手。"},
                    {"role": "user", "content": prompt},
                ],
                stream=True,
                temperature=0.3,
                max_tokens=500,
                top_p=0.8,
            )
            
            # 逐字流式推送
            for chunk in response:
                # Azure OpenAI 的首个 chunk 可能 choices 为空(内容过滤元数据)，需跳过
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta.content
                if delta:
                    # 将大段文本拆分成更小的片段
                    import re
                    # 按标点符号和空格拆分，确保每个片段都不太大
                    segments = re.split(r'([。！？，；：\s])', delta)
                    for segment in segments:
                        if segment.strip():  # 跳过空片段
                            yield f"data: {segment}\n\n"
                            # 添加小延迟，模拟真实的打字效果
                            import asyncio
                            await asyncio.sleep(0.05)  # 50ms 延迟
        except Exception as e:
            yield f"data: [ERROR] {str(e)}\n\n"
    return StreamingResponse(event_stream(), media_type="text/event-stream")

import os
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

async def generate_with_ollama(query: str, context: str, history: Optional[List[Dict[str, str]]] = None) -> str:
    """Generate answer using Azure OpenAI with RAG context"""
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("AZURE_OPENAI_API_KEY not set in environment")

    try:
        # 拼接历史对话
        history_text = ""
        if history:
            for turn in history[-6:]:  # 只取最近6条
                role = "用户" if turn.get("role") == "user" else "AI"
                history_text += f"{role}：{turn.get('content', '')}\n"
        prompt = f"""你是一位专业的中文 AI 客服助手，专门基于提供的知识内容，准确、清晰地回答用户提出的问题。

【历史对话】
{history_text}

【上下文信息】
{context}

【用户问题】
{query}

【回答要求】
1. 仅根据上述上下文信息和历史对话作答，不能编造或推测。
2. 若上下文信息中包含电话号码、时间、地点等，请直接引用并明确告知用户。
3. 若上下文中没有足够信息，请根据情况， 自行回答，尽量不要虚构内容。
4. 回答应尽量简洁明了，语气自然亲切，使用中文。
5. 若内容复杂，可适当使用换行、编号等格式提升可读性。

现在请开始回答：
"""


        client = AzureOpenAI(
            api_key=api_key,
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview"),
        )
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1"),
            messages=[
                {"role": "system", "content": "你是一个专业的AI助手。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=500,
            top_p=0.8,
            # extra_body={"enable_thinking": False},  # 若使用Qwen开源版本可加
        )

        return response.choices[0].message.content.strip()

    except Exception:
        logger.exception("Error calling DashScope")
        raise

import asyncio

@app.on_event("startup")
async def startup():
    redis = await aioredis.from_url("redis://localhost:6379", encoding="utf8", decode_responses=True)
    await FastAPILimiter.init(redis)

# Add a global dependency for rate limiting (60 req/min per IP)
app_dependency = [Depends(RateLimiter(times=60, seconds=60))]

# Patch all endpoints to use the global rate limiter
def patch_routes_with_limiter(app):
    for route in app.routes:
        if hasattr(route, "dependencies") and getattr(route, "include_in_schema", False):
            if not any(getattr(dep, 'dependency', None) == RateLimiter for dep in route.dependencies):
                route.dependencies.append(Depends(RateLimiter(times=60, seconds=60)))

patch_routes_with_limiter(app)

if __name__ == "__main__":
    import uvicorn
    
    # print("🚀 Starting RAG Chatbot Backend with Prisma Storage...")
    # print("📊 Database: Unified Prisma SQLite")
    # print("🧠 Model: Simple Character Frequency")
    # print("🔗 API: http://localhost:8001")
    # print("📚 Health: http://localhost:8001/health")
    # print("=" * 50)
    
    # # Check Ollama status
    # try:
    #     response = requests.get("http://localhost:11434/api/tags", timeout=5)
    #     if response.status_code == 200:
    #         models = response.json().get("models", [])
    #         print(f"✅ Ollama is running with models: {len(models)}")
    #     else:
    #         print("⚠️  Ollama not responding properly")
    # except Exception as e:
    #     print(f"⚠️  Ollama not accessible: {e}")
    
    print("🔄 Starting server...")
    uvicorn.run(app, host="0.0.0.0", port=8001) 