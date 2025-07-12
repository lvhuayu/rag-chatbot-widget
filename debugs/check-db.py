#!/usr/bin/env python3
"""
Check Database Contents
Directly query the SQLite database to see what's stored
"""

import sqlite3
import json
from datetime import datetime
import os

def check_database():
    """Check the contents of the RAG database"""
    
    db_path = "backend/rag_database.db"
    
    if not os.path.exists(db_path):
        print(f'File not found: {db_path}')
        exit(1)
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🗄️ RAG Database Contents")
        print("=" * 50)
        
        # Get database info
        cursor.execute("SELECT COUNT(*) FROM documents")
        doc_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM embeddings")
        emb_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT user_id) FROM documents")
        user_count = cursor.fetchone()[0]
        
        print(f"📊 Database Statistics:")
        print(f"   Total Documents: {doc_count}")
        print(f"   Total Embeddings: {emb_count}")
        print(f"   Unique Users: {user_count}")
        print()
        
        # Get users
        cursor.execute("SELECT DISTINCT user_id FROM documents ORDER BY user_id")
        users = [row[0] for row in cursor.fetchall()]
        
        print(f"👥 Users in Database:")
        for user in users:
            cursor.execute("SELECT COUNT(*) FROM documents WHERE user_id = ?", (user,))
            user_doc_count = cursor.fetchone()[0]
            print(f"   {user}: {user_doc_count} documents")
        print()
        
        # Show recent documents
        print("📄 Recent Documents:")
        cursor.execute("""
            SELECT id, title, user_id, timestamp, LENGTH(content) as content_length
            FROM documents 
            ORDER BY timestamp DESC 
            LIMIT 10
        """)
        
        documents = cursor.fetchall()
        for i, (doc_id, title, user_id, timestamp, content_length) in enumerate(documents, 1):
            print(f"   {i}. {title}")
            print(f"      User: {user_id}")
            print(f"      Content Length: {content_length} characters")
            print(f"      Timestamp: {timestamp}")
            print()
        
        # Show embedding info
        print("🔢 Embedding Information:")
        cursor.execute("SELECT DISTINCT embedding_dimension FROM embeddings")
        dimensions = [row[0] for row in cursor.fetchall()]
        
        if dimensions:
            print(f"   Embedding Dimensions: {dimensions}")
        else:
            print("   No embeddings found")
        
        # Check for any orphaned records
        cursor.execute("""
            SELECT COUNT(*) FROM documents d 
            LEFT JOIN embeddings e ON d.id = e.document_id 
            WHERE e.document_id IS NULL
        """)
        orphaned_docs = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM embeddings e 
            LEFT JOIN documents d ON e.document_id = d.id 
            WHERE d.id IS NULL
        """)
        orphaned_embs = cursor.fetchone()[0]
        
        print(f"   Orphaned Documents: {orphaned_docs}")
        print(f"   Orphaned Embeddings: {orphaned_embs}")
        
        # 输出所有表名
        tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        print('Tables:')
        for t in tables:
            print('  -', t[0])
        
        # 输出每个表的前几行内容
        for t in tables:
            print(f'\nTable: {t[0]}')
            try:
                rows = cursor.execute(f'SELECT * FROM {t[0]} LIMIT 3').fetchall()
                for row in rows:
                    print('   ', row)
            except Exception as e:
                print('   (error reading table)', e)
        
        conn.close()
        
        print()
        print("✅ Database check complete!")
        
    except sqlite3.OperationalError as e:
        print(f"❌ Database error: {e}")
        print("Make sure the database file exists and is accessible")
    except Exception as e:
        print(f"❌ Error checking database: {e}")

def show_user_documents(user_id):
    """Show documents for a specific user"""
    
    db_path = "backend/rag_database.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"📄 Documents for User: {user_id}")
        print("=" * 50)
        
        cursor.execute("""
            SELECT title, url, timestamp, LENGTH(content) as content_length
            FROM documents 
            WHERE user_id = ?
            ORDER BY timestamp DESC
        """, (user_id,))
        
        documents = cursor.fetchall()
        
        if not documents:
            print(f"No documents found for user: {user_id}")
            return
        
        for i, (title, url, timestamp, content_length) in enumerate(documents, 1):
            print(f"{i}. {title}")
            print(f"   URL: {url}")
            print(f"   Content Length: {content_length} characters")
            print(f"   Timestamp: {timestamp}")
            print()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error showing user documents: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Show documents for specific user
        user_id = sys.argv[1]
        show_user_documents(user_id)
    else:
        # Show general database info
        check_database() 