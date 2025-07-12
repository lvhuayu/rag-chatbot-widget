# RAG Chatbot - Persistent Storage Implementation

## Overview

This document describes the implementation of persistent local storage for the RAG chatbot system, replacing the previous in-memory storage with SQLite database storage. This ensures data persistence across server restarts and provides better scalability.

## Key Features

- **Persistent Storage**: Data survives server restarts
- **Multi-tenant Support**: User data isolation maintained
- **SQLite Database**: Lightweight, reliable local storage
- **Automatic Migration**: Tools to migrate from in-memory storage
- **Backup Support**: Database backup functionality
- **Performance Optimized**: Indexed queries for fast retrieval

## Architecture

### Storage Layer

The new storage system consists of:

1. **RAGStorage Class** (`backend/rag_storage.py`)
   - SQLite database management
   - Document and embedding storage
   - User isolation and filtering
   - Backup and maintenance functions

2. **Database Schema**
   ```sql
   -- Documents table
   CREATE TABLE documents (
       id TEXT PRIMARY KEY,
       url TEXT NOT NULL,
       title TEXT NOT NULL,
       content TEXT NOT NULL,
       timestamp TEXT NOT NULL,
       user_id TEXT NOT NULL,
       created_at TEXT DEFAULT CURRENT_TIMESTAMP
   );

   -- Embeddings table
   CREATE TABLE embeddings (
       id TEXT PRIMARY KEY,
       document_id TEXT NOT NULL,
       embedding_data BLOB NOT NULL,
       embedding_dimension INTEGER NOT NULL,
       created_at TEXT DEFAULT CURRENT_TIMESTAMP,
       FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE
   );
   ```

3. **Indexes for Performance**
   - `idx_documents_user_id` - Fast user filtering
   - `idx_documents_timestamp` - Time-based queries
   - `idx_embeddings_document_id` - Embedding retrieval

## Files Modified

### New Files
- `backend/rag_storage.py` - Core storage implementation
- `backend/migrate_to_persistent.py` - Migration tool
- `test-persistent-storage.ps1` - PowerShell test script
- `README_persistent_storage.md` - This documentation

### Modified Files
- `backend/rag_server_simple.py` - Updated to use persistent storage

## Installation and Setup

### 1. Install Dependencies

The persistent storage uses standard Python libraries:
- `sqlite3` (built-in)
- `numpy` (for embeddings)
- `pickle` (for serialization)

### 2. Initialize Storage

The storage is automatically initialized when the server starts:

```python
from rag_storage import init_storage
storage = init_storage("rag_database.db")
```

### 3. Database Location

The SQLite database file (`rag_database.db`) is created in the backend directory by default.

## Migration from In-Memory Storage

### Automatic Migration

Use the migration script to transfer existing data:

```bash
cd backend
python migrate_to_persistent.py
```

The migration tool provides:
1. **Data Migration** - Transfer documents from in-memory to persistent storage
2. **Database Backup** - Create backups before migration
3. **Database Info** - View current storage statistics

### Manual Migration

If you prefer manual migration:

1. **Export from in-memory**:
   ```bash
   curl http://localhost:8001/documents > documents.json
   ```

2. **Import to persistent**:
   ```bash
   # Use the migration script or add documents via API
   ```

## API Changes

### Health Endpoint

The `/health` endpoint now includes database information:

```json
{
  "status": "healthy",
  "model": "all-MiniLM-L6-v2",
  "storage": "SQLite Persistent",
  "database_info": {
    "database_path": "rag_database.db",
    "database_size_mb": 2.5,
    "total_documents": 15,
    "unique_users": 3,
    "embedding_dimension": 384
  }
}
```

### Stats Endpoint

The `/stats` endpoint provides detailed storage statistics:

```json
{
  "user_id": "all_users",
  "document_count": 15,
  "total_documents": 15,
  "unique_users": 3,
  "embedding_model": "all-MiniLM-L6-v2",
  "vector_db": "SQLite Persistent",
  "status": "running",
  "multi_tenant": true
}
```

## Testing

### Automated Testing

Run the PowerShell test script:

```powershell
.\test-persistent-storage.ps1
```

This script tests:
- Server health and storage type
- Document addition and retrieval
- Multi-tenant user isolation
- Search functionality
- Data persistence across restarts

### Manual Testing

1. **Start the server**:
   ```bash
   cd backend
   python rag_server_simple.py
   ```

2. **Add test documents**:
   ```bash
   curl -X POST http://localhost:8001/add-document \
     -H "Content-Type: application/json" \
     -d '{
       "url": "https://example.com/test",
       "title": "Test Document",
       "content": "This is a test document",
       "user_id": "test_user"
     }'
   ```

3. **Test search**:
   ```bash
   curl -X POST http://localhost:8001/search \
     -H "Content-Type: application/json" \
     -d '{
       "query": "test document",
       "user_id": "test_user"
     }'
   ```

4. **Restart server and verify persistence**:
   ```bash
   # Stop server (Ctrl+C)
   # Start server again
   python rag_server_simple.py
   # Verify data is still there
   curl http://localhost:8001/stats
   ```

## Database Management

### Backup

Create database backups:

```python
from rag_storage import get_storage
storage = get_storage()
storage.backup_database("backup_20241201.db")
```

### Maintenance

The storage system includes automatic maintenance:

- **Automatic indexing** for performance
- **Cascade deletes** for data integrity
- **Connection pooling** for efficiency

### Monitoring

Monitor database health:

```python
db_info = storage.get_database_info()
print(f"Database size: {db_info['database_size_mb']} MB")
print(f"Total documents: {db_info['total_documents']}")
print(f"Unique users: {db_info['unique_users']}")
```

## Performance Considerations

### Storage Efficiency

- **Embeddings stored as BLOB**: Efficient binary storage
- **Indexed queries**: Fast user filtering
- **Lazy loading**: Embeddings loaded only when needed

### Memory Usage

- **Reduced memory footprint**: No in-memory document storage
- **Streaming queries**: Large result sets handled efficiently
- **Connection management**: Proper SQLite connection handling

### Scalability

- **User isolation**: Each user's data is separate
- **Efficient queries**: Indexed lookups by user_id
- **Modular design**: Easy to extend or replace storage backend

## Troubleshooting

### Common Issues

1. **Database locked errors**:
   - Ensure only one server instance is running
   - Check for file permissions

2. **Migration failures**:
   - Verify server is running on port 8001
   - Check network connectivity

3. **Performance issues**:
   - Monitor database size
   - Consider archiving old documents
   - Check for proper indexing

### Debug Commands

```bash
# Check database file
ls -la rag_database.db

# View database info
curl http://localhost:8001/health

# Check user stats
curl http://localhost:8001/stats?user_id=your_user_id

# List user documents
curl http://localhost:8001/documents?user_id=your_user_id
```

## Future Enhancements

### Planned Features

1. **Database compression** for large datasets
2. **Automatic backups** with scheduling
3. **Document versioning** and history
4. **Advanced indexing** for better search performance
5. **Storage analytics** and monitoring

### Migration Path

The current implementation maintains backward compatibility:
- All existing API endpoints work unchanged
- Multi-tenant functionality preserved
- Gradual migration supported

## Security Considerations

### Data Protection

- **Local storage**: Data stays on your server
- **User isolation**: No cross-user data access
- **Input validation**: All inputs sanitized

### Access Control

- **API authentication**: Maintains existing auth system
- **User filtering**: Server-side user validation
- **Audit logging**: Document access tracking

## Conclusion

The persistent storage implementation provides:

✅ **Data persistence** across server restarts  
✅ **Multi-tenant isolation** maintained  
✅ **Backward compatibility** with existing APIs  
✅ **Performance optimization** with indexing  
✅ **Easy migration** from in-memory storage  
✅ **Comprehensive testing** and monitoring  

This upgrade significantly improves the reliability and scalability of the RAG chatbot system while maintaining all existing functionality. 