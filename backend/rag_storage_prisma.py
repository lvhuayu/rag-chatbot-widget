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
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import logging
import subprocess
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            
            # Write script to temporary file
            script_path = "temp_prisma_query.js"
            with open(script_path, 'w') as f:
                f.write(script_content)
            
            # Run the script
            prisma_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "prisma"))
            result = subprocess.run(["node", script_path], 
                                  cwd=prisma_dir,
                                  capture_output=True, text=True, check=True)
            
            # Clean up
            os.remove(script_path)
            
            # Parse result
            output = json.loads(result.stdout.strip())
            if not output.get('success'):
                raise Exception(output.get('error', 'Unknown error'))
            
            return output.get('data')
            
        except Exception as e:
            logger.error(f"Error running Prisma query: {e}")
            raise
    
    def add_document_with_uniqueness(self, doc_id: Optional[str], url: str, title: str, content: str, 
                                   user_id: str, embedding: List[float], timestamp: Optional[str] = None) -> Dict[str, Any]:
        """Add a document and its embedding to storage. Returns result with action type and document ID."""
        try:
            if timestamp is None:
                timestamp = datetime.now().isoformat()
            
            # First, find or create user
            user_query = f"""
                await prisma.user.upsert({{
                    where: {{ username: '{user_id}' }},
                    update: {{}},
                    create: {{
                        username: '{user_id}',
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
                        title: '{title}',
                        userId: '{user.id}'
                    }}
                }})
            """
            
            existing_doc = self._run_prisma_query(existing_query)
            
            if existing_doc:
                # Update existing document
                update_query = f"""
                    await prisma.rAGDocument.update({{
                        where: {{ id: '{existing_doc.id}' }},
                        data: {{
                            url: '{url}',
                            content: '{content.replace("'", "\\'")}',
                            timestamp: new Date('{timestamp}')
                        }}
                    }})
                """
                
                updated_doc = self._run_prisma_query(update_query)
                
                # Update embedding
                embedding_blob = pickle.dumps(np.array(embedding))
                embedding_query = f"""
                    await prisma.rAGEmbedding.upsert({{
                        where: {{ documentId: '{existing_doc.id}' }},
                        update: {{
                            embeddingData: Buffer.from({embedding_blob}),
                            embeddingDimension: {len(embedding)}
                        }},
                        create: {{
                            documentId: '{existing_doc.id}',
                            embeddingData: Buffer.from({embedding_blob}),
                            embeddingDimension: {len(embedding)}
                        }}
                    }})
                """
                
                self._run_prisma_query(embedding_query)
                
                logger.info(f"Updated existing document: {title} (User: {user_id}, ID: {existing_doc.id})")
                return {
                    "success": True,
                    "action": "updated",
                    "doc_id": existing_doc.id
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
                            userId: '{user.id}',
                            url: '{url}',
                            title: '{title}',
                            content: '{content.replace("'", "\\'")}',
                            timestamp: new Date('{timestamp}'),
                            createdAt: new Date('{timestamp}')
                        }}
                    }})
                """
                
                new_doc = self._run_prisma_query(create_query)
                
                # Insert embedding
                embedding_blob = pickle.dumps(np.array(embedding))
                embedding_query = f"""
                    await prisma.rAGEmbedding.create({{
                        data: {{
                            documentId: '{doc_id}',
                            embeddingData: Buffer.from({embedding_blob}),
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
                            username: '{user_id}'
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
                    embedding = pickle.loads(doc_data["embedding"]["embeddingData"])
                    embeddings.append(embedding)
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
                    embedding = pickle.loads(doc_data["embedding"]["embeddingData"])
                    embeddings.append(embedding)
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
                                username: '{user_id}'
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
                                    username: '{user_id}'
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
            
            return {
                "type": "Prisma SQLite",
                "documents": results[0],
                "embeddings": results[1],
                "users": results[2],
                "schema": "Unified (User Management + RAG)"
            }
            
        except Exception as e:
            logger.error(f"Error getting database info: {e}")
            return {"error": str(e)}
    
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