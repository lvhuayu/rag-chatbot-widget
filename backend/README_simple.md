# Simple RAG Backend with Authentication

This is a simplified version of the RAG backend that uses in-memory storage instead of ChromaDB. It includes full authentication support and user-scoped document search.

## Features

- ✅ **JWT Authentication**: All endpoints require valid JWT tokens
- ✅ **User-Scoped Documents**: Users can only access their own documents
- ✅ **In-Memory Storage**: Simple storage using NumPy and scikit-learn
- ✅ **Ollama Integration**: Uses local Ollama for LLM responses
- ✅ **Similarity Search**: Cosine similarity-based document retrieval
- ✅ **Threshold Filtering**: Configurable similarity thresholds

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements_simple.txt
   ```

2. **Start the Server**:
   ```bash
   python rag_server_simple.py
   ```

3. **Server will run on**: `http://localhost:8001`

## API Endpoints

### Authentication Required Endpoints

All endpoints require a valid JWT token in the Authorization header:
```
Authorization: Bearer your-jwt-token
```

#### `POST /add-document`
Add a document to the user's collection.

**Request Body**:
```json
{
    "url": "document-url",
    "title": "Document Title",
    "content": "Document content...",
    "timestamp": "2024-01-01T00:00:00Z"
}
```

**Response**:
```json
{
    "success": true,
    "doc_id": "uuid",
    "message": "Document 'Document Title' added successfully for user username"
}
```

#### `POST /search`
Search for relevant documents (user-scoped).

**Request Body**:
```json
{
    "query": "user question",
    "top_k": 3,
    "threshold": 0.5
}
```

**Response**:
```json
{
    "context": "LLM response based on found documents",
    "documents": [
        {
            "document": {
                "url": "doc-url",
                "title": "Document Title",
                "content": "Document content...",
                "timestamp": "2024-01-01T00:00:00Z",
                "user_id": "user-id"
            },
            "similarity": 0.85
        }
    ]
}
```

#### `GET /documents`
List all documents for the authenticated user.

**Response**:
```json
[
    {
        "url": "doc-url",
        "title": "Document Title",
        "content": "Document content...",
        "timestamp": "2024-01-01T00:00:00Z",
        "user_id": "user-id"
    }
]
```

#### `DELETE /clear-documents`
Clear all documents for the authenticated user.

**Response**:
```json
{
    "success": true,
    "message": "Cleared 5 documents for user username"
}
```

#### `GET /stats`
Get statistics for the authenticated user.

**Response**:
```json
{
    "user_id": "user-id",
    "username": "username",
    "document_count": 5,
    "total_documents": 10,
    "embedding_model": "all-MiniLM-L6-v2",
    "vector_db": "In-Memory (NumPy + scikit-learn)",
    "status": "running"
}
```

### Public Endpoints

#### `GET /`
Health check and API info.

#### `GET /health`
Detailed health status.

## Authentication

The backend expects JWT tokens from your Node.js authentication system. Make sure the JWT secret matches between your Node.js and Python backends.

**JWT Secret**: `your-secret-key` (change this in production!)

## Integration with Upload Portal

The Node.js upload portal should send documents with the user_id field:

```javascript
await axios.post('http://localhost:8001/add-document', {
    url: file.originalname,
    title: file.originalname,
    content: extractedContent,
    user_id: userId  // Include user_id
}, {
    headers: {
        'Authorization': `Bearer ${token}`
    }
});
```

## Testing

Use the test page: `public/test-authenticated-chatbot.html`

1. Start your Node.js backend (upload portal)
2. Start this Python backend
3. Open the test page
4. Register/Login
5. Upload documents through the portal
6. Test the chatbot

## Configuration

- **Port**: 8001 (change in `rag_server_simple.py`)
- **JWT Secret**: Change `JWT_SECRET` in the code
- **Ollama URL**: Change `ollama_url` if needed
- **Model**: Change `model` in Ollama payload if needed

## Security Notes

- ✅ User isolation: Users only see their own documents
- ✅ JWT validation: All requests validated
- ✅ Token expiration: Handled automatically
- ⚠️ In-memory storage: Data lost on restart
- ⚠️ JWT secret: Change in production

## Differences from ChromaDB Version

- **Storage**: In-memory vs ChromaDB
- **Performance**: Slower for large datasets
- **Persistence**: Data lost on restart
- **Simplicity**: Easier to understand and debug
- **Dependencies**: Fewer external dependencies 