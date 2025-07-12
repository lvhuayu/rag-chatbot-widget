# Database Consolidation Plan

## 🎯 Goal
Consolidate the two databases (Uploader + RAG) into a single database for simplified architecture and better data consistency.

## 📊 Current State
- **Uploader DB**: User management, document metadata
- **RAG DB**: Document content, vector embeddings
- **Sync**: ragDocId references between databases

## 🚀 Target State
- **Single DB**: All data in one SQLite database
- **Unified Schema**: Users and documents in same database
- **Direct Relations**: Foreign keys instead of ragDocId references

## 📋 Migration Steps

### Step 1: Create Unified Schema
```sql
-- New unified database schema
CREATE TABLE users (
  id TEXT PRIMARY KEY,
  username TEXT UNIQUE,
  password TEXT,
  publicKey TEXT,
  privateKey TEXT,
  createdAt DATETIME
);

CREATE TABLE documents (
  id INTEGER PRIMARY KEY,
  userId TEXT,
  originalName TEXT,
  fileSize INTEGER,
  description TEXT,
  status TEXT,
  url TEXT,
  title TEXT,
  content TEXT,
  embedding BLOB,
  timestamp TEXT,
  createdAt DATETIME,
  FOREIGN KEY (userId) REFERENCES users(id)
);

CREATE INDEX idx_documents_user_id ON documents(userId);
CREATE INDEX idx_documents_status ON documents(status);
```

### Step 2: Data Migration Script
```python
# migration_script.py
import sqlite3
from pathlib import Path

def migrate_data():
    # Connect to both databases
    uploader_db = sqlite3.connect('upload_portal/rag-document-uploader/server/prisma/dev.db')
    rag_db = sqlite3.connect('backend/rag_database.db')
    
    # Create new unified database
    unified_db = sqlite3.connect('unified_database.db')
    
    # Migrate users
    users = uploader_db.execute("SELECT * FROM User").fetchall()
    for user in users:
        unified_db.execute("""
            INSERT INTO users (id, username, password, publicKey, privateKey, createdAt)
            VALUES (?, ?, ?, ?, ?, ?)
        """, user)
    
    # Migrate documents with content
    documents = rag_db.execute("SELECT * FROM documents").fetchall()
    for doc in documents:
        unified_db.execute("""
            INSERT INTO documents (id, userId, url, title, content, embedding, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, doc)
    
    # Update document metadata from uploader DB
    uploader_docs = uploader_db.execute("SELECT * FROM Document").fetchall()
    for doc in uploader_docs:
        unified_db.execute("""
            UPDATE documents 
            SET originalName = ?, fileSize = ?, description = ?, status = ?
            WHERE userId = ? AND url = ?
        """, (doc[2], doc[3], doc[4], doc[5], doc[1], doc[2]))
    
    unified_db.commit()
    unified_db.close()
```

### Step 3: Update RAG Backend
```python
# rag_storage.py - Updated for unified database
class UnifiedRAGStorage:
    def __init__(self, db_path="unified_database.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY,
                    userId TEXT,
                    originalName TEXT,
                    fileSize INTEGER,
                    description TEXT,
                    status TEXT,
                    url TEXT,
                    title TEXT,
                    content TEXT,
                    embedding BLOB,
                    timestamp TEXT,
                    createdAt DATETIME,
                    FOREIGN KEY (userId) REFERENCES users(id)
                )
            """)
    
    def add_document(self, url, title, content, user_id):
        # Generate embedding
        embedding = self.model.encode(content)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO documents (userId, url, title, content, embedding, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, url, title, content, embedding, datetime.now().isoformat()))
            return cursor.lastrowid
    
    def search_documents(self, query, user_id, top_k=5, threshold=0.7):
        query_embedding = self.model.encode(query)
        
        with sqlite3.connect(self.db_path) as conn:
            # Get all documents for user
            documents = conn.execute("""
                SELECT id, url, title, content, embedding, timestamp
                FROM documents 
                WHERE userId = ?
            """, (user_id,)).fetchall()
            
            # Calculate similarities
            similarities = []
            for doc in documents:
                doc_embedding = np.frombuffer(doc[4], dtype=np.float32)
                similarity = cosine_similarity([query_embedding], [doc_embedding])[0][0]
                if similarity >= threshold:
                    similarities.append((similarity, doc))
            
            # Sort by similarity and return top_k
            similarities.sort(key=lambda x: x[0], reverse=True)
            return similarities[:top_k]
```

### Step 4: Update Uploader Backend
```typescript
// Remove Prisma dependency, use direct SQLite
import sqlite3 from 'sqlite3';

class UnifiedDatabase {
    private db: sqlite3.Database;
    
    constructor(dbPath: string = 'unified_database.db') {
        this.db = new sqlite3.Database(dbPath);
    }
    
    async createUser(username: string, password: string): Promise<string> {
        const userId = generateId();
        return new Promise((resolve, reject) => {
            this.db.run(
                'INSERT INTO users (id, username, password, createdAt) VALUES (?, ?, ?, ?)',
                [userId, username, password, new Date().toISOString()],
                (err) => {
                    if (err) reject(err);
                    else resolve(userId);
                }
            );
        });
    }
    
    async getUserDocuments(userId: string): Promise<any[]> {
        return new Promise((resolve, reject) => {
            this.db.all(
                'SELECT * FROM documents WHERE userId = ? ORDER BY createdAt DESC',
                [userId],
                (err, rows) => {
                    if (err) reject(err);
                    else resolve(rows);
                }
            );
        });
    }
}
```

### Step 5: Update Frontend
```typescript
// Remove ragDocId references, use direct document IDs
interface Document {
    id: number;
    userId: string;
    originalName: string;
    fileSize: number;
    description?: string;
    status: string;
    url: string;
    title: string;
    content: string;
    timestamp: string;
    createdAt: string;
}
```

## 🎯 Benefits After Consolidation

### 1. **Simplified Architecture**
- Single database to manage and backup
- No synchronization complexity
- Direct foreign key relationships

### 2. **Better Performance**
- Single connection pool
- Direct joins without network calls
- Reduced latency for queries

### 3. **Improved Consistency**
- ACID transactions across all operations
- No risk of orphaned records
- Atomic operations for upload + indexing

### 4. **Easier Maintenance**
- One database to monitor and backup
- Simpler deployment process
- Reduced operational overhead

### 5. **Better Development Experience**
- Single schema to understand
- Easier debugging and testing
- Simpler data migration scripts

## 🚨 Migration Risks & Mitigation

### Risks
1. **Data Loss**: During migration process
2. **Downtime**: System unavailable during migration
3. **Rollback Complexity**: If migration fails

### Mitigation
1. **Backup Both Databases**: Before starting migration
2. **Test Migration**: On copy of production data
3. **Gradual Rollout**: Migrate users in batches
4. **Rollback Plan**: Keep old databases until confirmed working

## 📅 Implementation Timeline

1. **Week 1**: Create unified schema and migration script
2. **Week 2**: Update RAG backend for unified database
3. **Week 3**: Update uploader backend for unified database
4. **Week 4**: Test migration on development data
5. **Week 5**: Deploy to production with rollback plan

## ✅ Conclusion

**Recommendation: Consolidate to single database**

The benefits of simplified architecture, better performance, and improved consistency outweigh the initial migration effort. The current two-database setup adds unnecessary complexity for this scale of application. 