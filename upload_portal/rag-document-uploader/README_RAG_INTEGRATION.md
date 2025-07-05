# RAG Document Uploader with Multi-Tenant Support

This document describes the enhanced RAG Document Uploader that now interfaces with the local RAG database and supports multi-tenant functionality.

## 🚀 Overview

The RAG Document Uploader has been upgraded to:

- **Integrate with Local RAG Database**: Direct connection to the SQLite-based RAG backend
- **Multi-Tenant Support**: Complete user isolation for documents and searches
- **Enhanced UI**: New RAG Management interface for document exploration and search
- **Real-time Indexing**: Documents are automatically indexed in the RAG system upon upload
- **Comprehensive API**: Full REST API for RAG operations with user authentication

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   React Client  │    │  Uploader API    │    │   RAG Backend   │
│   (Port 3000)   │◄──►│   (Port 5000)    │◄──►│   (Port 8001)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   User Auth     │    │   Document DB    │    │   SQLite DB     │
│   (Prisma)      │    │   (Prisma)       │    │   (rag_storage) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🔧 Features

### Multi-Tenant Document Management
- **User Isolation**: Each user can only access their own documents
- **Secure Uploads**: Documents are automatically tagged with user ID
- **Isolated Search**: Search results are scoped to the authenticated user
- **User Statistics**: Individual document counts and system-wide stats

### RAG Integration
- **Automatic Indexing**: Documents are indexed in the RAG system upon upload
- **Vector Search**: Full-text search with semantic similarity
- **Document Retrieval**: Access to indexed documents with metadata
- **Health Monitoring**: System health and database statistics

### Enhanced User Interface
- **RAG Management Page**: Dedicated interface for RAG operations
- **Document Browser**: View all indexed documents for the user
- **Search Interface**: Real-time semantic search with similarity scores
- **Statistics Dashboard**: User and system statistics
- **Status Indicators**: Visual indicators for RAG indexing status

## 📋 Prerequisites

1. **RAG Backend Running**: Ensure the RAG server is running on port 8001
2. **Node.js**: Version 16 or higher
3. **Database**: SQLite database for user management
4. **Dependencies**: All required npm packages installed

## 🚀 Quick Start

### 1. Start the RAG Backend
```bash
cd backend
python rag_server_simple.py
```

### 2. Start the Uploader Backend
```bash
cd upload_portal/rag-document-uploader/server
npm install
npm start
```

### 3. Start the Uploader Client
```bash
cd upload_portal/rag-document-uploader/client
npm install
npm start
```

### 4. Access the Application
- **Main Application**: http://localhost:3000
- **RAG Management**: http://localhost:3000/rag
- **Upload Interface**: http://localhost:3000/upload

## 🔌 API Endpoints

### Authentication Required Endpoints

#### Document Management
- `GET /api/upload/documents` - Get user's uploaded documents
- `POST /api/upload/` - Upload and index documents
- `DELETE /api/upload/documents/:id` - Delete a document

#### RAG Operations
- `GET /api/upload/rag-documents` - Get user's RAG documents
- `POST /api/upload/search` - Search RAG documents
- `GET /api/upload/rag-stats` - Get user's RAG statistics
- `GET /api/upload/rag-health` - Get RAG system health

#### Admin Operations
- `GET /api/upload/rag-stats/all` - Get system-wide statistics (admin only)

### Public Endpoints
- `GET /api/upload/rag-available` - Check RAG backend availability

## 🧠 RAG Management Interface

### Documents Tab
- **View Indexed Documents**: See all documents indexed in the RAG system
- **Document Metadata**: Title, content preview, timestamp
- **Refresh Functionality**: Update document list in real-time

### Search Tab
- **Semantic Search**: Search documents using natural language
- **Similarity Scores**: See how well documents match your query
- **AI Responses**: Get AI-generated responses based on search results
- **Configurable Parameters**: Adjust top_k and similarity threshold

### Statistics Tab
- **User Statistics**: Your document count and user information
- **System Information**: Total documents, embedding model, storage type
- **Multi-Tenant Status**: Confirmation of multi-tenant functionality

## 🔒 Multi-Tenant Security

### User Isolation
- **Document Ownership**: Each document is tagged with user_id
- **Access Control**: Users can only access their own documents
- **Search Scoping**: Search results are filtered by user_id
- **API Protection**: All endpoints require authentication

### Data Privacy
- **No Cross-User Access**: Users cannot see other users' documents
- **Secure Storage**: Documents stored with user isolation in database
- **Audit Trail**: Document creation and modification tracking

## 📊 Database Schema

### Uploader Database (Prisma)
```sql
-- Users table
CREATE TABLE User (
  id TEXT PRIMARY KEY,
  username TEXT UNIQUE,
  password TEXT,
  publicKey TEXT,
  privateKey TEXT,
  createdAt DATETIME
);

-- Documents table (enhanced)
CREATE TABLE Document (
  id TEXT PRIMARY KEY,
  userId TEXT,
  originalName TEXT,
  fileSize INTEGER,
  description TEXT,
  status TEXT,
  ragDocId TEXT,  -- Reference to RAG backend document
  createdAt DATETIME,
  FOREIGN KEY (userId) REFERENCES User(id)
);
```

### RAG Database (SQLite)
```sql
-- Documents table
CREATE TABLE documents (
  id INTEGER PRIMARY KEY,
  url TEXT,
  title TEXT,
  content TEXT,
  user_id TEXT,
  timestamp TEXT,
  embedding BLOB
);
```

## 🧪 Testing

### Automated Testing
Run the comprehensive test script:
```powershell
.\test-rag-uploader.ps1
```

### Manual Testing
1. **Upload Documents**: Upload files through the web interface
2. **Verify Indexing**: Check RAG Management page for indexed documents
3. **Test Search**: Use the search interface to find documents
4. **Verify Isolation**: Create multiple users and verify data isolation

### API Testing
```bash
# Test RAG availability
curl http://localhost:5000/api/upload/rag-available

# Test user statistics (requires auth token)
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:5000/api/upload/rag-stats

# Test document search (requires auth token)
curl -X POST -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"query": "travel", "top_k": 5}' \
     http://localhost:5000/api/upload/search
```

## 🔧 Configuration

### Environment Variables
```bash
# Uploader Server (.env)
DATABASE_URL="file:./dev.db"
PORT=5000

# RAG Backend
RAG_SERVER_URL="http://localhost:8001"
```

### RAG Service Configuration
```typescript
// Default configuration in ragService.ts
const ragService = new RAGService('http://localhost:8001');
```

## 🚨 Troubleshooting

### Common Issues

1. **RAG Backend Not Available**
   - Ensure RAG server is running on port 8001
   - Check firewall settings
   - Verify network connectivity

2. **Document Not Indexed**
   - Check RAG backend logs for errors
   - Verify document format is supported
   - Check user authentication

3. **Search Not Working**
   - Ensure documents are properly indexed
   - Check similarity threshold settings
   - Verify user has documents in the system

4. **Multi-Tenant Issues**
   - Verify user authentication is working
   - Check user_id is being passed correctly
   - Ensure database schema is updated

### Debug Mode
Enable debug logging in the uploader server:
```typescript
// In app.ts
app.use(morgan('combined'));
```

## 📈 Performance

### Optimization Tips
- **Batch Uploads**: Upload multiple documents at once
- **Document Size**: Keep documents under 10MB for optimal processing
- **Search Parameters**: Adjust top_k and threshold for better results
- **Database Indexing**: Ensure proper database indexes for user_id

### Monitoring
- **Health Checks**: Regular health check endpoints
- **Statistics**: Monitor document counts and system usage
- **Error Logging**: Comprehensive error tracking and logging

## 🔮 Future Enhancements

### Planned Features
- **Document Versioning**: Track document changes over time
- **Advanced Search**: Filters, date ranges, document types
- **Bulk Operations**: Mass document operations
- **Analytics Dashboard**: Advanced usage analytics
- **API Rate Limiting**: Protect against abuse
- **Document Sharing**: Controlled document sharing between users

### Integration Opportunities
- **External RAG Systems**: Support for other RAG backends
- **Cloud Storage**: Integration with cloud storage providers
- **Advanced Authentication**: OAuth, SSO integration
- **Webhook Support**: Real-time notifications

## 📚 Additional Resources

- [RAG Backend Documentation](../README.md)
- [Multi-Tenant Implementation Guide](../README_multi_tenant.md)
- [API Reference Documentation](../README_api.md)
- [Database Management Guide](../README_database.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Note**: This RAG integration provides a complete multi-tenant document management system with semantic search capabilities. The system ensures data isolation while providing powerful search and retrieval functionality. 