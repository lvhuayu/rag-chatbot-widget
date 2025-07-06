#!/usr/bin/env python3
"""
Prisma-based RAG Storage Module
Replaces SQLite storage with Prisma ORM for unified database management
"""

import json
import numpy as np
import pickle
import os
import uuid
import re
import base64
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import logging
import subprocess
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _escape_js_string(s: str) -> str:
    """Escape a string for safe use in JavaScript"""
    if not s:
        return ""
    # Escape backslashes first, then quotes, then other problematic characters
    escaped = s.replace("\\", "\\\\")
    escaped = escaped.replace("'", "\\'")
    escaped = escaped.replace('"', '\\"')
    escaped = escaped.replace("\n", "\\n")
    escaped = escaped.replace("\r", "\\r")
    escaped = escaped.replace("\t", "\\t")
    return escaped

class PrismaRAGStorage:
    """Prisma-based storage for RAG documents and embeddings"""
    
    def __init__(self, prisma_schema_path: str = "../prisma/schema.prisma"):
        """Initialize the storage with Prisma"""
        self.prisma_schema_path = prisma_schema_path
        self._ensure_prisma_client()
        logger.info(f"Prisma RAG Storage initialized with schema: {prisma_schema_path}")
    
    def _ensure_prisma_client(self):
        """Ensure Prisma client is generated"""
        try:
            # Check if Prisma client exists in node_modules
            client_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "node_modules", "@prisma", "client"))
            if os.path.exists(client_path):
                logger.info("Prisma client already exists, skipping generation")
                return
            
            logger.info("Generating Prisma client...")
            # Get the absolute path to the prisma directory
            prisma_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "prisma"))
            subprocess.run(["npx", "prisma", "generate"], 
                         cwd=prisma_dir, 
                         check=True, capture_output=True)
        except Exception as e:
            logger.error(f"Error ensuring Prisma client: {e}")
            # Don't raise the error, just log it and continue
            logger.warning("Continuing without Prisma client generation")
    
    def _run_prisma_query(self, query: str, params: Dict[str, Any] = None) -> Any:
        """Run a Prisma query using Node.js"""
        script_path = None
        try:
            # Create a temporary Node.js script to run the query
            script_content = f"""
const {{ PrismaClient }} = require('@prisma/client');

const prisma = new PrismaClient();

async function runQuery() {{
    try {{
        const result = {query};
        console.log(JSON.stringify({{ success: true, data: result }}));
    }} catch (error) {{
        console.log(JSON.stringify({{ success: false, error: error.message }}));
    }} finally {{
        await prisma.$disconnect();
    }}
}}

runQuery();
"""
            
            # Write script to the prisma directory
            prisma_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "prisma"))
            script_path = os.path.join(prisma_dir, "temp_prisma_query.js")
            
            # 确保 prisma 目录存在
            os.makedirs(prisma_dir, exist_ok=True)
            
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            # 确保文件写入完成
            if not os.path.exists(script_path):
                raise Exception(f"Failed to create temporary script at {script_path}")
            
            # Run the script
            result = subprocess.run(["node", "temp_prisma_query.js"], 
                                  cwd=prisma_dir,
                                  capture_output=True,
                                  timeout=30)  # 添加超时
            
            # Decode output manually
            stdout = result.stdout.decode('utf-8', errors='ignore')
            stderr = result.stderr.decode('utf-8', errors='ignore')
            
            # Log stdout and stderr for debugging
            if result.returncode != 0:
                logger.error(f"Node.js subprocess failed!\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}")
                raise Exception(f"Node.js subprocess failed: {stderr}")
            
            # Parse result
            if not stdout.strip():
                raise Exception("Empty output from Node.js subprocess")
                
            output = json.loads(stdout.strip())
            if not output.get('success'):
                logger.error(f"Prisma query error: {output.get('error')}\nFull output: {stdout}")
                raise Exception(output.get('error', 'Unknown error'))
            
            return output.get('data')
            
        except Exception as e:
            logger.error(f"Error running Prisma query: {e}")
            raise
        finally:
            # Clean up - 确保在 finally 块中删除文件
            if script_path and os.path.exists(script_path):
                try:
                    os.remove(script_path)
                except Exception as cleanup_error:
                    logger.warning(f"Failed to cleanup temporary script: {cleanup_error}")
    
    def add_document_with_uniqueness(self, doc_id: Optional[str], url: str, title: str, content: str, 
                                   user_id: str, embedding: List[float], timestamp: Optional[str] = None) -> Dict[str, Any]:
        """Add a document and its embedding to storage. Returns result with action type and document ID."""
        try:
            if timestamp is None:
                timestamp = datetime.now().isoformat()
            
            # First, find or create user
            user_query = f"""
                await prisma.user.upsert({{
                    where: {{ username: '{_escape_js_string(user_id)}' }},
                    update: {{}},
                    create: {{
                        username: '{_escape_js_string(user_id)}',
                        password: 'migrated_user',
                        publicKey: null,
                        privateKey: null
                    }}
                }})
            """
            
            user = self._run_prisma_query(user_query)
            
            # Check if document with same title exists for this user
            existing_query = f"""
                await prisma.rAGDocument.findFirst({{
                    where: {{
                        title: '{_escape_js_string(title)}',
                        userId: '{user["id"]}'
                    }}
                }})
            """
            
            existing_doc = self._run_prisma_query(existing_query)
            
            if existing_doc:
                # Update existing document
                update_query = f"""
                    await prisma.rAGDocument.update({{
                        where: {{ id: '{existing_doc["id"]}' }},
                        data: {{
                            url: '{_escape_js_string(url)}',
                            content: '{_escape_js_string(content)}',
                            timestamp: new Date('{timestamp}')
                        }}
                    }})
                """
                
                updated_doc = self._run_prisma_query(update_query)
                
                # Update embedding
                embedding_blob = pickle.dumps(np.array(embedding))
                embedding_b64 = base64.b64encode(embedding_blob).decode('utf-8')
                embedding_query = f"""
                    await prisma.rAGEmbedding.upsert({{
                        where: {{ documentId: '{existing_doc["id"]}' }},
                        update: {{
                            embeddingData: Buffer.from('{embedding_b64}', 'base64'),
                            embeddingDimension: {len(embedding)}
                        }},
                        create: {{
                            documentId: '{existing_doc["id"]}',
                            embeddingData: Buffer.from('{embedding_b64}', 'base64'),
                            embeddingDimension: {len(embedding)}
                        }}
                    }})
                """
                
                self._run_prisma_query(embedding_query)
                
                logger.info(f"Updated existing document: {title} (User: {user_id}, ID: {existing_doc['id']})")
                return {
                    "success": True,
                    "action": "updated",
                    "doc_id": existing_doc["id"]
                }
            else:
                # Generate new ID if not provided
                if doc_id is None:
                    doc_id = str(uuid.uuid4())
                
                # Insert new document
                create_query = f"""
                    await prisma.rAGDocument.create({{
                        data: {{
                            id: '{doc_id}',
                            userId: '{user["id"]}',
                            url: '{_escape_js_string(url)}',
                            title: '{_escape_js_string(title)}',
                            content: '{_escape_js_string(content)}',
                            timestamp: new Date('{timestamp}'),
                            createdAt: new Date('{timestamp}')
                        }}
                    }})
                """
                
                new_doc = self._run_prisma_query(create_query)
                
                # Insert embedding
                embedding_blob = pickle.dumps(np.array(embedding))
                embedding_b64 = base64.b64encode(embedding_blob).decode('utf-8')
                embedding_query = f"""
                    await prisma.rAGEmbedding.create({{
                        data: {{
                            documentId: '{doc_id}',
                            embeddingData: Buffer.from('{embedding_b64}', 'base64'),
                            embeddingDimension: {len(embedding)}
                        }}
                    }})
                """
                
                self._run_prisma_query(embedding_query)
                
                logger.info(f"Added new document: {title} (User: {user_id}, ID: {doc_id})")
                return {
                    "success": True,
                    "action": "added",
                    "doc_id": doc_id
                }
                
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            return {
                "success": False,
                "action": "error",
                "doc_id": None,
                "error": str(e)
            }
    
    def get_documents_by_user(self, user_id: str) -> Tuple[List[Dict[str, Any]], List[np.ndarray]]:
        """Get all documents and embeddings for a specific user"""
        try:
            query = f"""
                await prisma.rAGDocument.findMany({{
                    where: {{
                        user: {{
                            username: '{_escape_js_string(user_id)}'
                        }}
                    }},
                    include: {{
                        embedding: true
                    }},
                    orderBy: {{
                        timestamp: 'desc'
                    }}
                }})
            """
            
            documents_data = self._run_prisma_query(query)
            
            documents = []
            embeddings = []
            
            for doc_data in documents_data:
                doc = {
                    "id": doc_data["id"],
                    "url": doc_data["url"],
                    "title": doc_data["title"],
                    "content": doc_data["content"],
                    "timestamp": doc_data["timestamp"],
                    "user_id": user_id
                }
                documents.append(doc)
                
                if doc_data.get("embedding"):
                    try:
                        # The embedding data might be stored as base64 string, Buffer object, or JS object
                        embedding_data = doc_data["embedding"]["embeddingData"]
                        if isinstance(embedding_data, str):
                            # If it's a string, it might be base64 encoded
                            embedding_blob = base64.b64decode(embedding_data)
                        elif isinstance(embedding_data, dict):
                            # If it's a dict, it's a JS object representation of bytes
                            max_key = max(int(k) for k in embedding_data.keys())
                            embedding_blob = bytearray(max_key + 1)
                            for key, value in embedding_data.items():
                                embedding_blob[int(key)] = value
                            embedding_blob = bytes(embedding_blob)
                        else:
                            # If it's already bytes, use it directly
                            embedding_blob = embedding_data
                        embedding = pickle.loads(embedding_blob)
                        embeddings.append(embedding)
                    except Exception as e:
                        logger.warning(f"Error loading embedding for document {doc_data['id']}: {e}")
                        embeddings.append(np.array([]))
                else:
                    embeddings.append(np.array([]))
            
            logger.info(f"Retrieved {len(documents)} documents for user: {user_id}")
            return documents, embeddings
            
        except Exception as e:
            logger.error(f"Error getting documents for user {user_id}: {e}")
            return [], []
    
    def get_all_documents(self) -> Tuple[List[Dict[str, Any]], List[np.ndarray]]:
        """Get all documents and embeddings"""
        try:
            query = """
                await prisma.rAGDocument.findMany({
                    include: {
                        embedding: true,
                        user: true
                    },
                    orderBy: {
                        timestamp: 'desc'
                    }
                })
            """
            
            documents_data = self._run_prisma_query(query)
            
            documents = []
            embeddings = []
            
            for doc_data in documents_data:
                doc = {
                    "id": doc_data["id"],
                    "url": doc_data["url"],
                    "title": doc_data["title"],
                    "content": doc_data["content"],
                    "timestamp": doc_data["timestamp"],
                    "user_id": doc_data["user"]["username"]
                }
                documents.append(doc)
                
                if doc_data.get("embedding"):
                    try:
                        # The embedding data might be stored as base64 string, Buffer object, or JS object
                        embedding_data = doc_data["embedding"]["embeddingData"]
                        if isinstance(embedding_data, str):
                            # If it's a string, it might be base64 encoded
                            embedding_blob = base64.b64decode(embedding_data)
                        elif isinstance(embedding_data, dict):
                            # If it's a dict, it's a JS object representation of bytes
                            max_key = max(int(k) for k in embedding_data.keys())
                            embedding_blob = bytearray(max_key + 1)
                            for key, value in embedding_data.items():
                                embedding_blob[int(key)] = value
                            embedding_blob = bytes(embedding_blob)
                        else:
                            # If it's already bytes, use it directly
                            embedding_blob = embedding_data
                        embedding = pickle.loads(embedding_blob)
                        embeddings.append(embedding)
                    except Exception as e:
                        logger.warning(f"Error loading embedding for document {doc_data['id']}: {e}")
                        embeddings.append(np.array([]))
                else:
                    embeddings.append(np.array([]))
            
            logger.info(f"Retrieved {len(documents)} total documents")
            return documents, embeddings
            
        except Exception as e:
            logger.error(f"Error getting all documents: {e}")
            return [], []
    
    def get_user_documents_list(self, user_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get list of documents for a user or all users"""
        try:
            if user_id:
                query = f"""
                    await prisma.rAGDocument.findMany({{
                        where: {{
                            user: {{
                                username: '{_escape_js_string(user_id)}'
                            }}
                        }},
                        include: {{
                            user: true
                        }},
                        orderBy: {{
                            timestamp: 'desc'
                        }},
                        take: {limit}
                    }})
                """
            else:
                query = f"""
                    await prisma.rAGDocument.findMany({{
                        include: {{
                            user: true
                        }},
                        orderBy: {{
                            timestamp: 'desc'
                        }},
                        take: {limit}
                    }})
                """
            
            documents_data = self._run_prisma_query(query)
            
            documents = []
            for doc_data in documents_data:
                doc = {
                    "id": doc_data["id"],
                    "url": doc_data["url"],
                    "title": doc_data["title"],
                    "content": doc_data["content"],
                    "timestamp": doc_data["timestamp"],
                    "user_id": doc_data["user"]["username"]
                }
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            logger.error(f"Error getting documents list: {e}")
            return []
    
    def get_user_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics for a specific user or overall"""
        try:
            if user_id:
                query = f"""
                    await Promise.all([
                        prisma.rAGDocument.count({{
                            where: {{
                                user: {{
                                    username: '{_escape_js_string(user_id)}'
                                }}
                            }}
                        }}),
                        prisma.rAGDocument.count()
                    ])
                """
                
                results = self._run_prisma_query(query)
                user_count = results[0]
                total_count = results[1]
                
                return {
                    "user_id": user_id,
                    "document_count": user_count,
                    "total_documents": total_count
                }
            else:
                query = """
                    await Promise.all([
                        prisma.rAGDocument.count(),
                        prisma.user.count()
                    ])
                """
                
                results = self._run_prisma_query(query)
                total_docs = results[0]
                total_users = results[1]
                
                return {
                    "user_id": "all_users",
                    "document_count": total_docs,
                    "total_documents": total_docs,
                    "unique_users": total_users
                }
                
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"error": str(e)}
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get database information"""
        try:
            query = """
                await Promise.all([
                    prisma.rAGDocument.count(),
                    prisma.rAGEmbedding.count(),
                    prisma.user.count()
                ])
            """
            
            results = self._run_prisma_query(query)
            
            # 计算数据库文件大小
            import os
            db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "rag_database.db"))
            db_size_mb = 0
            if os.path.exists(db_path):
                db_size_mb = round(os.path.getsize(db_path) / (1024 * 1024), 2)
            
            # 获取 embedding 维度（从第一个 embedding 记录）
            embedding_dimension = "N/A"
            try:
                dim_query = """
                    await prisma.rAGEmbedding.findFirst({
                        select: {
                            embeddingDimension: true
                        }
                    })
                """
                dim_result = self._run_prisma_query(dim_query)
                if dim_result:
                    embedding_dimension = dim_result.get("embeddingDimension", "N/A")
            except:
                pass
            
            return {
                "database_path": db_path,
                "database_size_mb": db_size_mb,
                "total_documents": results[0],
                "unique_users": results[2],
                "embedding_dimension": embedding_dimension,
                "type": "Prisma SQLite",
                "documents": results[0],
                "embeddings": results[1],
                "users": results[2],
                "schema": "Unified (User Management + RAG)"
            }
            
        except Exception as e:
            logger.error(f"Error getting database info: {e}")
            return {"error": str(e)}
    
    def clear_documents_by_user(self, user_id: str) -> bool:
        """Clear all documents and embeddings for a specific user"""
        try:
            # First get the user ID
            user_query = f"""
                await prisma.user.findUnique({{
                    where: {{ username: '{_escape_js_string(user_id)}' }}
                }})
            """
            
            user = self._run_prisma_query(user_query)
            if not user:
                logger.warning(f"User {user_id} not found")
                return False
            
            # Delete embeddings and documents for this user
            query = f"""
                await prisma.rAGEmbedding.deleteMany({{
                    where: {{
                        document: {{
                            userId: '{user["id"]}'
                        }}
                    }}
                }});
                await prisma.rAGDocument.deleteMany({{
                    where: {{
                        userId: '{user["id"]}'
                    }}
                }});
            """
            
            self._run_prisma_query(query)
            
            logger.info(f"Cleared all documents and embeddings for user: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing documents for user {user_id}: {e}")
            return False
    
    def clear_all_documents(self) -> bool:
        """Clear all documents and embeddings"""
        try:
            query = """
                await prisma.rAGEmbedding.deleteMany({});
                await prisma.rAGDocument.deleteMany({});
            """
            
            self._run_prisma_query(query)
            
            logger.info("Cleared all documents and embeddings")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing all documents: {e}")
            return False

# Factory function for backward compatibility
def get_prisma_storage() -> PrismaRAGStorage:
    """Get Prisma-based RAG storage instance"""
    return PrismaRAGStorage()

def init_prisma_storage() -> PrismaRAGStorage:
    """Initialize Prisma-based RAG storage"""
    return PrismaRAGStorage() 