#!/usr/bin/env python3
"""
Import JSONL data to embeddings table API
Supports importing scraped documents from Playwright + LangChain scraper
"""

import os
import sys
import json
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import jwt
import numpy as np
import pickle
import base64
from sentence_transformers import SentenceTransformer

# Add the parent directory to the path to import the Prisma storage
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.rag_storage_prisma import PrismaRAGStorage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="JSONL to Embeddings Import API", version="1.0.0")

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

# Initialize embedding model
embedding_model = SentenceTransformer('BAAI/bge-large-zh-v1.5')

# Pydantic models
class ImportRequest(BaseModel):
    site_id: str
    jsonl_content: str  # Base64 encoded JSONL content

class ImportResponse(BaseModel):
    success: bool
    imported_count: int
    errors: List[str]
    message: str

def generate_embedding(text: str) -> List[float]:
    """Generate embedding for text using the SOTA model"""
    try:
        emb = embedding_model.encode(text, normalize_embeddings=True)
        return emb.tolist() if isinstance(emb, np.ndarray) else list(emb)
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        raise

@app.get("/")
async def root():
    return {"message": "JSONL to Embeddings Import API", "status": "running"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "model": "BAAI/bge-large-zh-v1.5",
        "storage": "Prisma Unified Database"
    }

@app.post("/import-jsonl", response_model=ImportResponse)
async def import_jsonl_to_embeddings(
    request: ImportRequest
):
    """
    Import JSONL data to embeddings table
    
    Expected JSONL format:
    {"text": "document content", "metadata": {"url": "...", "title": "...", "source": "..."}}
    """
    try:
        # Decode base64 content
        try:
            jsonl_content = base64.b64decode(request.jsonl_content).decode('utf-8')
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid base64 content: {str(e)}")
        
        imported_count = 0
        errors = []
        
        # Process each line in JSONL
        for line_num, line in enumerate(jsonl_content.strip().split('\n'), 1):
            try:
                if not line.strip():
                    continue
                    
                # Parse JSON line
                data = json.loads(line.strip())
                
                # Extract text and metadata
                text = data.get('text', '')
                metadata = data.get('metadata', {})
                
                if not text:
                    errors.append(f"Line {line_num}: Empty text content")
                    continue
                
                # Extract metadata fields
                url = metadata.get('url', '')
                title = metadata.get('title', 'No title')
                source = metadata.get('source', url)
                
                # Generate embedding
                embedding = generate_embedding(text)
                
                # Add document entry
                document_id = storage.add_document_entry(
                    url=url,
                    title=title,
                    content=text,
                    site_id=request.site_id,
                    timestamp=datetime.now().isoformat()
                )
                
                # Add embedding
                storage.add_embedding(
                    document_id=document_id,
                    site_id=request.site_id,
                    embedding=embedding,
                    timestamp=datetime.now().isoformat()
                )
                
                imported_count += 1
                logger.info(f"Imported document {imported_count}: {title}")
                
            except json.JSONDecodeError as e:
                errors.append(f"Line {line_num}: Invalid JSON - {str(e)}")
            except Exception as e:
                errors.append(f"Line {line_num}: {str(e)}")
        
        return ImportResponse(
            success=True,
            imported_count=imported_count,
            errors=errors,
            message=f"Successfully imported {imported_count} documents with {len(errors)} errors"
        )
        
    except Exception as e:
        logger.error(f"Import error: {e}")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

@app.post("/import-jsonl-file")
async def import_jsonl_file(
    file: UploadFile = File(...),
    site_id: str = Form(...)
):
    """
    Import JSONL file to embeddings table
    
    Upload a JSONL file directly
    """
    try:
        if not file.filename.endswith('.jsonl'):
            raise HTTPException(status_code=400, detail="File must be a .jsonl file")
        
        # Read file content
        content = await file.read()
        jsonl_content = content.decode('utf-8')
        
        imported_count = 0
        errors = []
        
        # Process each line in JSONL
        for line_num, line in enumerate(jsonl_content.strip().split('\n'), 1):
            try:
                if not line.strip():
                    continue
                    
                # Parse JSON line
                data = json.loads(line.strip())
                
                # Extract text and metadata
                text = data.get('text', '')
                metadata = data.get('metadata', {})
                
                if not text:
                    errors.append(f"Line {line_num}: Empty text content")
                    continue
                
                # Extract metadata fields
                url = metadata.get('url', '')
                title = metadata.get('title', 'No title')
                source = metadata.get('source', url)
                
                # Generate embedding
                embedding = generate_embedding(text)
                
                # Add document entry
                document_id = storage.add_document_entry(
                    url=url,
                    title=title,
                    content=text,
                    site_id=site_id,
                    timestamp=datetime.now().isoformat()
                )
                
                # Add embedding
                storage.add_embedding(
                    document_id=document_id,
                    site_id=site_id,
                    embedding=embedding,
                    timestamp=datetime.now().isoformat()
                )
                
                imported_count += 1
                logger.info(f"Imported document {imported_count}: {title}")
                
            except json.JSONDecodeError as e:
                errors.append(f"Line {line_num}: Invalid JSON - {str(e)}")
            except Exception as e:
                errors.append(f"Line {line_num}: {str(e)}")
        
        return {
            "success": True,
            "imported_count": imported_count,
            "errors": errors,
            "message": f"Successfully imported {imported_count} documents with {len(errors)} errors"
        }
        
    except Exception as e:
        logger.error(f"Import error: {e}")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

@app.get("/stats/{site_id}")
async def get_import_stats(
    site_id: str
):
    """Get import statistics for a site"""
    try:
        stats = storage.get_user_stats(site_id)
        return {
            "site_id": site_id,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 