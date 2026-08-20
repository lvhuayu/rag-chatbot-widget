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
import time
import asyncio
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
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import aioredis

# Add the parent directory to the path to import the Prisma storage
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.rag_storage_prisma import PrismaRAGStorage
from backend.rag_context import build_context
from backend.rag_contract import (
    build_grounded_context,
    citation_metrics,
    estimate_tokens,
    sse_event,
)
from backend.tenant_auth import (
    SiteIdentity,
    TenantAuthError,
    authenticate_site_token,
    issue_api_key_token,
    resolve_site_id,
)

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
    # 鉴权走 Authorization: Bearer（非 cookie），无需带凭据；置为 False 可消除
    # “反射任意 Origin + 允许携带凭据”这一危险组合。
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Security
security = HTTPBearer()
ingestion_security = HTTPBearer(auto_error=False)
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
EMBEDDING_MODEL_NAME = "BAAI/bge-large-zh-v1.5"
RAG_CONTEXT_TOKEN_BUDGET = int(os.getenv("RAG_CONTEXT_TOKEN_BUDGET", "2000"))

# Initialize storage
storage = PrismaRAGStorage()


def verify_ingestion_identity(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(ingestion_security),
) -> SiteIdentity:
    token = credentials.credentials if credentials else None
    try:
        return authenticate_site_token(
            storage.database_path,
            token,
            request.headers.get("origin"),
            JWT_SECRET,
            JWT_ALGORITHM,
        )
    except TenantAuthError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error

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
    has_payqr: Optional[bool] = False  # 本站点是否配置了收款码（由前端告知），用于让模型决定是否展示

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
embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
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
    return {"status": "healthy"}


@app.get("/health/live")
async def liveness_check():
    return {"status": "alive"}


def _probe_llm_dependency() -> None:
    required_settings = (
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_DEPLOYMENT",
    )
    missing = [name for name in required_settings if not os.getenv(name)]
    if missing:
        raise RuntimeError("Azure OpenAI configuration is incomplete")

    client = AzureOpenAI(
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview"),
        max_retries=0,
        timeout=5.0,
    )
    client.models.list()


@app.get("/health/ready")
async def readiness_check():
    checks: Dict[str, Dict[str, str]] = {}

    try:
        with sqlite3.connect(storage.database_path, timeout=5) as connection:
            connection.execute("SELECT 1").fetchone()
        checks["database"] = {"status": "ok"}
    except Exception as error:
        logger.warning("Database readiness probe failed: %s", type(error).__name__)
        checks["database"] = {"status": "error"}

    try:
        redis_client = getattr(app.state, "redis", None)
        if redis_client is None or not await redis_client.ping():
            raise RuntimeError("Redis is unavailable")
        checks["redis"] = {"status": "ok"}
    except Exception as error:
        logger.warning("Redis readiness probe failed: %s", type(error).__name__)
        checks["redis"] = {"status": "error"}

    try:
        if embedding_model.get_sentence_embedding_dimension() <= 0:
            raise RuntimeError("Embedding model has no output dimension")
        checks["embedding_model"] = {"status": "ok"}
    except Exception as error:
        logger.warning("Embedding readiness probe failed: %s", type(error).__name__)
        checks["embedding_model"] = {"status": "error"}

    try:
        await asyncio.to_thread(_probe_llm_dependency)
        checks["llm_provider"] = {"status": "ok"}
    except Exception as error:
        logger.warning("LLM readiness probe failed: %s", type(error).__name__)
        checks["llm_provider"] = {"status": "error"}

    ready = all(check["status"] == "ok" for check in checks.values())
    return JSONResponse(
        status_code=200 if ready else 503,
        content={"status": "ready" if ready else "not_ready", "checks": checks},
    )

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
        token, site_id = issue_api_key_token(
            storage.database_path,
            api_key,
            request.headers.get("origin"),
            JWT_SECRET,
            JWT_ALGORITHM,
        )
        return SiteTokenResponse(token=token, siteId=site_id, expires_in=3600)
    except TenantAuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e
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
async def add_documents(
    documents: List[Document],
    identity: SiteIdentity = Depends(verify_ingestion_identity),
):
    """批量上传多个文档，每个文档自动分段批量入库"""
    for doc in documents:
        try:
            resolve_site_id(identity, doc.site_id)
        except TenantAuthError as error:
            raise HTTPException(
                status_code=error.status_code, detail=error.detail
            ) from error
    all_results = []
    for doc in documents:
        site_id = identity.site_id
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
                timestamp=timestamp,
                chunk_text=chunk,
                chunk_index=idx,
                embedding_model=EMBEDDING_MODEL_NAME,
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
    site_id: Optional[str] = None
    documents: List[ScrapedDocument]

@app.post("/add-scraped-data", response_model=Dict[str, Any])
async def add_scraped_data(
    request: ScrapedDataRequest,
    identity: SiteIdentity = Depends(verify_ingestion_identity),
):
    """直接接收爬虫数据并存储到向量数据库"""
    try:
        try:
            site_id = resolve_site_id(identity, request.site_id)
        except TenantAuthError as error:
            raise HTTPException(
                status_code=error.status_code, detail=error.detail
            ) from error
        logger.info(f"开始处理爬取数据，站点: {site_id}, 文档数: {len(request.documents)}")
        
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
                    site_id=site_id,
                    timestamp=datetime.now().isoformat()
                )
                
                # 为每个切块生成 embedding 并存储
                chunk_results = []
                for idx, chunk in enumerate(segments):
                    embedding = generate_simple_embedding(chunk)
                    embedding_id = storage.add_embedding(
                        document_id=document_id,
                        site_id=site_id,
                        embedding=embedding,
                        timestamp=datetime.now().isoformat(),
                        chunk_text=chunk,
                        chunk_index=idx,
                        embedding_model=EMBEDDING_MODEL_NAME,
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
            "site_id": site_id,
            "total_documents": len(request.documents),
            "total_chunks": total_chunks,
            "processed_documents": len(all_results),
            "message": f"成功处理 {len(request.documents)} 个文档，生成 {total_chunks} 个向量",
            "documents": all_results
        }
        
    except HTTPException:
        raise
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
async def search_documents(request: SearchRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    # 鉴权：site_id 一律从 token 解析，忽略请求体里的 site_id，防止任何人传别人的 site_id 读取其知识库
    try:
        _payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        token_site_id = _payload.get("siteId")
    except Exception:
        raise HTTPException(status_code=403, detail="Invalid or expired token")
    if not token_site_id:
        raise HTTPException(status_code=403, detail="Invalid token: missing siteId")
    # 闲聊意图识别
    if is_chitchat(request.query):
        return RAGResponse(
            context="你好！我是智能助手，有什么可以帮您？",
            documents=[]
        )
    """Search for relevant document segments with multi-tenant support, 返回 context 来源信息"""
    try:
        user_documents, user_embeddings = storage.get_documents_by_site(token_site_id)
        if not user_documents:
            logger.info(f"No documents available for site: {token_site_id}")
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
            logger.info(f"Query: '{request.query}', Best similarity {best_similarity:.3f} below quality threshold {quality_threshold} (/search)")
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
        context = build_context(
            [result.document.content for result in search_results[:request.top_k]],
            RAG_CONTEXT_TOKEN_BUDGET,
        ) or None
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
async def list_documents(site_id: Optional[str] = None, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """List all documents for a site or all documents if no site specified (admin only)"""
    verify_admin_token(credentials)
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
async def clear_documents(site_id: Optional[str] = None, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Clear all documents for a site or all documents if no site specified (admin only)"""
    verify_admin_token(credentials)
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
async def get_stats(site_id: Optional[str] = None, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get statistics about documents (admin only)"""
    verify_admin_token(credentials)
    try:
        stats = storage.get_user_stats(site_id)
        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")


@app.get("/rag-metrics")
async def get_rag_metrics(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Return tenant-tier and model-level RAG latency and token metrics."""
    verify_admin_token(credentials)
    return {"metrics": storage.get_rag_metrics()}


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
        return random.choice(fallback_templates) + hint_block + "\n\n如需人工帮助，您可以点右上角「✍️ 留言」留下联系方式，我们会尽快联系您。"

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
            retrieval_started = time.perf_counter()
            user_documents, user_embeddings = storage.get_documents_by_site(site_id)
            if not user_documents:
                yield f"data: 我的知识库中没有相关信息来回答您的问题。您可以点右上角「✍️ 留言」留下联系方式，我们会尽快联系您。\n\n"
                return

            # 跨语言检索：知识库多为中文。若用户用非中文提问，先把问题翻译成中文再做向量检索，
            # 否则英文 query 与中文文档向量相似度过低会检索不到。最终回答仍用用户原始语言。
            retrieval_query = request.query
            if not any('一' <= ch <= '鿿' for ch in request.query):
                try:
                    _tc = AzureOpenAI(
                        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview"),
                    )
                    _tr = _tc.chat.completions.create(
                        model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1"),
                        messages=[
                            {"role": "system", "content": "你是翻译助手。把用户输入翻译成简体中文，只输出译文本身，不要加任何解释或引号。"},
                            {"role": "user", "content": request.query},
                        ],
                        temperature=0,
                        max_tokens=200,
                    )
                    _zh = (_tr.choices[0].message.content or "").strip()
                    if _zh:
                        retrieval_query = _zh
                except Exception:
                    retrieval_query = request.query

            query_embedding = generate_simple_embedding(retrieval_query)
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
                _fb = get_friendly_fallback_response(request.query).replace('\r', '').replace('\n', '\\n')
                yield f"data: {_fb}\n\n"
                return

            filtered_results = [
                (doc, sim, idx) for doc, sim, idx in similarities 
                if sim >= request.threshold
            ][:max(request.top_k, 10)]

            def query_terms_match(text, query):
                query_terms = query.split()
                return any(term in text for term in query_terms)

            priority_snippets = []
            other_snippets = []
            for doc, similarity, idx in filtered_results:
                content = doc["content"]
                if query_terms_match(content, retrieval_query):
                    priority_snippets.append((doc, similarity))
                else:
                    other_snippets.append((doc, similarity))
            priority_snippets.sort(key=lambda x: x[1], reverse=True)
            other_snippets.sort(key=lambda x: x[1], reverse=True)
            selected_documents = [
                document for document, _ in priority_snippets[:3]
            ]
            if len(selected_documents) < request.top_k:
                selected_documents.extend(
                    document
                    for document, _ in other_snippets[
                        : request.top_k - len(selected_documents)
                    ]
                )
            context, sources = build_grounded_context(
                selected_documents, RAG_CONTEXT_TOKEN_BUDGET
            )
            retrieval_latency_ms = int(
                (time.perf_counter() - retrieval_started) * 1000
            )
            yield sse_event("sources", {"sources": sources})

            # Step 2: LLM流式生成 (Azure OpenAI)
            client = AzureOpenAI(
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview"),
            )
            prompt = f"""
                         你是一位专业的 AI 客服助手，专门基于提供的知识内容，准确、清晰地回答用户提出的问题。请使用与用户提问相同的语言作答（用户用中文就用中文，用英文就用英文）。
                        
                        【上下文信息】
                         {context}

                        【用户问题】
                         {request.query}

                        【回答要求】
                         1. 仅根据上述上下文信息作答，不能使用外部知识、编造或推测。
                         2. 每个事实性句子末尾必须使用 [编号] 引用对应来源。
                         3. 若上下文不足，必须回答“无法根据现有知识库回答该问题”，不得自行补充答案。
                         4. 回答应尽量简洁明了，语气自然亲切，并与用户提问的语言保持一致。
                         5. 若内容复杂，可适当使用换行、编号等格式提升可读性。编号尽量少一些，可以通过描述来补充。

                         现在请开始回答：
                    """             
            if getattr(request, "has_payqr", False):
                prompt += "\n\n【特别指令·最高优先级】本店已配置收款码。如果用户【本条】消息是想要付款/支付/扫码付钱/结账，你必须在回答的最末尾另起一行、原样输出标记 [[SHOW_PAYQR]]（只输出这串标记本身，不要加引号、不要解释、不要翻译）。如果用户只是说已经付过款、询问是否到账、要求退款，或与付款无关，则绝对不要输出该标记。"
            # 基础版多轮记忆：system + 最近历史轮次 + 当前问题(含检索上下文)
            sys_content = "你是一个专业的AI助手。"
            if getattr(request, "has_payqr", False):
                sys_content += (
                    "\n本店已配置收款码（付款二维码）。当且仅当顾客明确表达想要付款/支付/扫码付钱时，"
                    "在你的回复正文之后另起一行单独输出标记 [[SHOW_PAYQR]]。"
                    "若顾客只是表示已经付过款、询问是否到账、要求退款，或与付款无关，则不要输出该标记。"
                    "不要向顾客解释这个标记的含义。"
                )
            chat_messages = [{"role": "system", "content": sys_content}]
            if request.history:
                for turn in request.history[-6:]:
                    role = turn.get("role")
                    content = (turn.get("content") or "").strip()
                    if role in ("user", "assistant") and content:
                        chat_messages.append({"role": role, "content": content})
            chat_messages.append({"role": "user", "content": prompt})
            model_name = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1")
            llm_started = time.perf_counter()
            response = client.chat.completions.create(
                model=model_name,
                messages=chat_messages,
                stream=True,
                temperature=0.3,
                max_tokens=500,
                top_p=0.8,
            )
            
            # 逐字流式推送
            answer_parts = []
            for chunk in response:
                # Azure OpenAI 的首个 chunk 可能 choices 为空(内容过滤元数据)，需跳过
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta.content
                if delta:
                    # 将大段文本拆分成更小的片段以模拟打字效果
                    import re, asyncio
                    # 按标点/空白拆分；保留普通空格（英文词间空格不能丢），仅跳过换行/制表符
                    segments = re.split(r'([。！？，；：\s])', delta)
                    for segment in segments:
                        if segment in ('', '\r', '\t'):
                            continue
                        # 保留换行：转义为 \n 以兼容 SSE 分帧，前端 fixMarkdownList 会还原成真换行，
                        # 保证 markdown 的有序/无序列表、分段能正确渲染（不能整段丢换行）。
                        out = segment.replace('\n', '\\n')
                        answer_parts.append(segment)
                        yield sse_event("message", out)
                        await asyncio.sleep(0.02)
            llm_latency_ms = int((time.perf_counter() - llm_started) * 1000)
            answer = "".join(answer_parts)
            input_tokens = estimate_tokens(json.dumps(chat_messages, ensure_ascii=False))
            output_tokens = estimate_tokens(answer)
            contract = citation_metrics(answer, sources)
            tenant_tier = _resolve_plan_id(site_id)
            try:
                storage.record_rag_telemetry(
                    site_id=site_id,
                    model=model_name,
                    tenant_tier=tenant_tier,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    retrieval_latency_ms=retrieval_latency_ms,
                    llm_latency_ms=llm_latency_ms,
                )
            except Exception as telemetry_error:
                logger.error("Failed to record RAG telemetry: %s", telemetry_error)
            yield sse_event("contract", contract)
            yield sse_event(
                "usage",
                {
                    "model": model_name,
                    "tenant_tier": tenant_tier,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "retrieval_latency_ms": retrieval_latency_ms,
                    "llm_latency_ms": llm_latency_ms,
                },
            )
        except Exception as e:
            yield sse_event("message", f"[ERROR] {str(e)}")
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
        prompt = f"""你是一位专业的 AI 客服助手，专门基于提供的知识内容，准确、清晰地回答用户提出的问题。请使用与用户提问相同的语言作答（用户用中文就用中文，用英文就用英文）。

【历史对话】
{history_text}

【上下文信息】
{context}

【用户问题】
{query}

【回答要求】
1. 仅根据上述上下文信息作答，不能使用外部知识、编造或推测。
2. 每个事实性句子末尾必须使用 [编号] 引用对应来源。
3. 若上下文不足，必须回答“无法根据现有知识库回答该问题”，不得自行补充答案。
4. 回答应尽量简洁明了，语气自然亲切，并与用户提问的语言保持一致。
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

@app.on_event("startup")
async def startup():
    app.state.redis = None
    try:
        redis = await aioredis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379"),
            encoding="utf8",
            decode_responses=True,
        )
        await redis.ping()
        await FastAPILimiter.init(redis)
        app.state.redis = redis
    except Exception as error:
        logger.error("Redis initialization failed: %s", type(error).__name__)

# Add a global dependency for rate limiting (60 req/min per IP)
app_dependency = [Depends(RateLimiter(times=60, seconds=60))]

# Patch all endpoints to use the global rate limiter
def patch_routes_with_limiter(app):
    for route in app.routes:
        if getattr(route, "path", "") in {"/health", "/health/live", "/health/ready"}:
            continue
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