#!/usr/bin/env python3
"""
RAG Storage Module - Persistent Local Storage using SQLite
Replaces in-memory storage with persistent database storage
"""

import sqlite3
import json
import numpy as np
import pickle
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGStorage:
    """Persistent storage for RAG documents and embeddings using SQLite"""
    
    def __init__(self, db_path: str = "rag_database.db"):
        """Initialize the storage with SQLite database"""
        self.db_path = db_path
        self.init_database()
        logger.info(f"RAG Storage initialized with database: {db_path}")
    
    def init_database(self):
        """Initialize the database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create documents table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS documents (
                        id TEXT PRIMARY KEY,
                        url TEXT NOT NULL,
                        title TEXT NOT NULL,
                        content TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create embeddings table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS embeddings (
                        id TEXT PRIMARY KEY,
                        document_id TEXT NOT NULL,
                        embedding_data BLOB NOT NULL,
                        embedding_dimension INTEGER NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE
                    )
                ''')
                
                # Create indexes for better performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_documents_timestamp ON documents(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_embeddings_document_id ON embeddings(document_id)')
                
                conn.commit()
                logger.info("Database tables initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def add_document(self, doc_id: str, url: str, title: str, content: str, 
                    user_id: str, embedding: List[float], timestamp: Optional[str] = None) -> bool:
        """Add a document and its embedding to storage"""
        try:
            if timestamp is None:
                timestamp = datetime.now().isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insert document
                cursor.execute('''
                    INSERT OR REPLACE INTO documents (id, url, title, content, timestamp, user_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (doc_id, url, title, content, timestamp, user_id))
                
                # Insert embedding
                embedding_blob = pickle.dumps(np.array(embedding))
                embedding_dim = len(embedding)
                
                cursor.execute('''
                    INSERT OR REPLACE INTO embeddings (id, document_id, embedding_data, embedding_dimension)
                    VALUES (?, ?, ?, ?)
                ''', (f"emb_{doc_id}", doc_id, embedding_blob, embedding_dim))
                
                conn.commit()
                logger.info(f"Added document: {title} (User: {user_id})")
                return True
                
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            return False
    
    def get_documents_by_user(self, user_id: str) -> Tuple[List[Dict[str, Any]], List[np.ndarray]]:
        """Get all documents and embeddings for a specific user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get documents for user
                cursor.execute('''
                    SELECT id, url, title, content, timestamp, user_id
                    FROM documents 
                    WHERE user_id = ?
                    ORDER BY timestamp DESC
                ''', (user_id,))
                
                documents = []
                embeddings = []
                
                for row in cursor.fetchall():
                    doc = {
                        "id": row[0],
                        "url": row[1],
                        "title": row[2],
                        "content": row[3],
                        "timestamp": row[4],
                        "user_id": row[5]
                    }
                    documents.append(doc)
                    
                    # Get corresponding embedding
                    cursor.execute('''
                        SELECT embedding_data 
                        FROM embeddings 
                        WHERE document_id = ?
                    ''', (row[0],))
                    
                    embedding_row = cursor.fetchone()
                    if embedding_row:
                        embedding = pickle.loads(embedding_row[0])
                        embeddings.append(embedding)
                
                logger.info(f"Retrieved {len(documents)} documents for user: {user_id}")
                return documents, embeddings
                
        except Exception as e:
            logger.error(f"Error getting documents for user {user_id}: {e}")
            return [], []
    
    def get_all_documents(self) -> Tuple[List[Dict[str, Any]], List[np.ndarray]]:
        """Get all documents and embeddings"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get all documents
                cursor.execute('''
                    SELECT id, url, title, content, timestamp, user_id
                    FROM documents 
                    ORDER BY timestamp DESC
                ''')
                
                documents = []
                embeddings = []
                
                for row in cursor.fetchall():
                    doc = {
                        "id": row[0],
                        "url": row[1],
                        "title": row[2],
                        "content": row[3],
                        "timestamp": row[4],
                        "user_id": row[5]
                    }
                    documents.append(doc)
                    
                    # Get corresponding embedding
                    cursor.execute('''
                        SELECT embedding_data 
                        FROM embeddings 
                        WHERE document_id = ?
                    ''', (row[0],))
                    
                    embedding_row = cursor.fetchone()
                    if embedding_row:
                        embedding = pickle.loads(embedding_row[0])
                        embeddings.append(embedding)
                
                logger.info(f"Retrieved {len(documents)} total documents")
                return documents, embeddings
                
        except Exception as e:
            logger.error(f"Error getting all documents: {e}")
            return [], []
    
    def delete_documents_by_user(self, user_id: str) -> bool:
        """Delete all documents for a specific user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Delete documents (embeddings will be deleted automatically due to CASCADE)
                cursor.execute('DELETE FROM documents WHERE user_id = ?', (user_id,))
                deleted_count = cursor.rowcount
                
                conn.commit()
                logger.info(f"Deleted {deleted_count} documents for user: {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting documents for user {user_id}: {e}")
            return False
    
    def clear_all_documents(self) -> bool:
        """Clear all documents and embeddings"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Clear all data
                cursor.execute('DELETE FROM documents')
                cursor.execute('DELETE FROM embeddings')
                
                conn.commit()
                logger.info("Cleared all documents and embeddings")
                return True
                
        except Exception as e:
            logger.error(f"Error clearing all documents: {e}")
            return False
    
    def get_user_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics for a specific user or overall"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if user_id:
                    # Get stats for specific user
                    cursor.execute('''
                        SELECT COUNT(*) FROM documents WHERE user_id = ?
                    ''', (user_id,))
                    user_count = cursor.fetchone()[0]
                    
                    cursor.execute('SELECT COUNT(*) FROM documents')
                    total_count = cursor.fetchone()[0]
                    
                    return {
                        "user_id": user_id,
                        "document_count": user_count,
                        "total_documents": total_count
                    }
                else:
                    # Get overall stats
                    cursor.execute('SELECT COUNT(*) FROM documents')
                    total_count = cursor.fetchone()[0]
                    
                    cursor.execute('SELECT COUNT(DISTINCT user_id) FROM documents')
                    user_count = cursor.fetchone()[0]
                    
                    return {
                        "user_id": "all_users",
                        "document_count": total_count,
                        "total_documents": total_count,
                        "unique_users": user_count
                    }
                
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"error": str(e)}
    
    def get_user_documents_list(self, user_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get a list of documents (with truncated content) for a user or all users"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if user_id:
                    cursor.execute('''
                        SELECT id, url, title, content, timestamp, user_id
                        FROM documents 
                        WHERE user_id = ?
                        ORDER BY timestamp DESC
                        LIMIT ?
                    ''', (user_id, limit))
                else:
                    cursor.execute('''
                        SELECT id, url, title, content, timestamp, user_id
                        FROM documents 
                        ORDER BY timestamp DESC
                        LIMIT ?
                    ''', (limit,))
                
                documents = []
                for row in cursor.fetchall():
                    content = row[3]
                    if len(content) > 200:
                        content = content[:200] + "..."
                    
                    doc = {
                        "id": row[0],
                        "url": row[1],
                        "title": row[2],
                        "content": content,
                        "timestamp": row[4],
                        "user_id": row[5]
                    }
                    documents.append(doc)
                
                return documents
                
        except Exception as e:
            logger.error(f"Error getting documents list: {e}")
            return []
    
    def backup_database(self, backup_path: str) -> bool:
        """Create a backup of the database"""
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Database backed up to: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Error backing up database: {e}")
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get database information and statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get database size
                db_size = os.path.getsize(self.db_path)
                
                # Get table counts
                cursor.execute('SELECT COUNT(*) FROM documents')
                doc_count = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM embeddings')
                emb_count = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(DISTINCT user_id) FROM documents')
                user_count = cursor.fetchone()[0]
                
                # Get embedding dimensions
                cursor.execute('SELECT DISTINCT embedding_dimension FROM embeddings LIMIT 1')
                emb_dim_row = cursor.fetchone()
                emb_dim = emb_dim_row[0] if emb_dim_row else 0
                
                return {
                    "database_path": self.db_path,
                    "database_size_bytes": db_size,
                    "database_size_mb": round(db_size / (1024 * 1024), 2),
                    "total_documents": doc_count,
                    "total_embeddings": emb_count,
                    "unique_users": user_count,
                    "embedding_dimension": emb_dim,
                    "storage_type": "SQLite Persistent"
                }
                
        except Exception as e:
            logger.error(f"Error getting database info: {e}")
            return {"error": str(e)}

# Global storage instance
_storage_instance = None

def get_storage() -> RAGStorage:
    """Get the global storage instance"""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = RAGStorage()
    return _storage_instance

def init_storage(db_path: str = "rag_database.db") -> RAGStorage:
    """Initialize the global storage instance"""
    global _storage_instance
    _storage_instance = RAGStorage(db_path)
    return _storage_instance 