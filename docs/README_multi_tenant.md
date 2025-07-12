# 🔑 Multi-Tenant RAG Chatbot

This document explains how to use the multi-tenant functionality in the RAG Chatbot, which allows different users/websites to have their own isolated knowledge bases.

## 🎯 Overview

The multi-tenant feature ensures that:
- Each user gets their own isolated knowledge base
- No data mixing between different users
- Secure search that only returns relevant documents for the specific user
- Easy integration with just one line of code

## 🚀 Quick Start

### 1. Method 1: Data Attribute (Recommended)

```html
<script src="chatbot.js" data-user-id="your_unique_user_id"></script>
<script>
    initRAGChatbot({
        backendUrl: "http://localhost:8001"
    });
</script>
```

### 2. Method 2: Configuration Object

```html
<script src="chatbot.js"></script>
<script>
    initRAGChatbot({
        userId: "your_unique_user_id",
        backendUrl: "http://localhost:8001"
    });
</script>
```

### 3. Method 3: Global Configuration

```html
<script>
    window.__RAG_CHATBOT_CONFIG__ = {
        userId: "your_unique_user_id"
    };
</script>
<script src="chatbot.js"></script>
<script>
    initRAGChatbot({
        backendUrl: "http://localhost:8001"
    });
</script>
```

### 4. Method 4: Element Attribute

```html
<div data-rag-user-id="your_unique_user_id"></div>
<script src="chatbot.js"></script>
<script>
    initRAGChatbot({
        backendUrl: "http://localhost:8001"
    });
</script>
```

## 🔧 Configuration Options

### User ID Priority Order

The system checks for userId in the following order:
1. Configuration object (`config.userId`)
2. Global config (`window.__RAG_CHATBOT_CONFIG__.userId`)
3. Script data attribute (`data-user-id`)
4. Any script tag with chatbot.js (`data-user-id`)
5. Element with `data-rag-user-id` attribute

### Full Configuration Example

```javascript
initRAGChatbot({
    // Multi-tenant configuration
    userId: "company_abc_123",
    
    // Backend configuration
    backendUrl: "http://localhost:8001",
    enableRAG: true,
    ragThreshold: 0.7,
    maxRAGResults: 3,
    
    // UI configuration
    selector: "#chatbot-container", // Optional: attach to specific element
    theme: {
        primaryColor: "#007bff"
    },
    welcomeMessage: "Hello! I'm your AI assistant. How can I help you today?",
    
    // Content ingestion
    enableContentIngestion: true,
    
    // Authentication (optional)
    auth: {
        useKeyAuth: true,
        // ... other auth options
    }
});
```

## 🏗️ Backend API Changes

### Search Endpoint

The search endpoint now supports user-specific filtering:

```bash
POST /search
{
    "query": "What services do you offer?",
    "top_k": 3,
    "threshold": 0.7,
    "user_id": "company_abc_123"  # New field for multi-tenant support
}
```

### Add Document Endpoint

Documents are now associated with specific users:

```bash
POST /add-document
{
    "url": "https://example.com",
    "title": "Company Information",
    "content": "We are a software company...",
    "user_id": "company_abc_123"  # New field for multi-tenant support
}
```

### List Documents Endpoint

Filter documents by user:

```bash
GET /documents?user_id=company_abc_123
```

### Statistics Endpoint

Get user-specific statistics:

```bash
GET /stats?user_id=company_abc_123
```

## 🧪 Testing Multi-Tenant Functionality

### Run the Test Script

```powershell
# Windows PowerShell
.\test-multi-tenant.ps1
```

This script will:
1. Start the backend server
2. Add test documents for 3 different users
3. Test search isolation
4. Verify data isolation
5. Test user-specific statistics

### Manual Testing

1. **Start the backend server:**
   ```bash
   python backend/rag_server_simple.py
   ```

2. **Add documents for different users:**
   ```bash
   # User 1
   curl -X POST "http://localhost:8001/add-document" \
        -H "Content-Type: application/json" \
        -d '{"url":"https://user1.com","title":"User 1 Info","content":"Software company","user_id":"user1"}'
   
   # User 2
   curl -X POST "http://localhost:8001/add-document" \
        -H "Content-Type: application/json" \
        -d '{"url":"https://user2.com","title":"User 2 Info","content":"Restaurant business","user_id":"user2"}'
   ```

3. **Test search isolation:**
   ```bash
   # Search for User 1
   curl -X POST "http://localhost:8001/search" \
        -H "Content-Type: application/json" \
        -d '{"query":"software","user_id":"user1"}'
   
   # Search for User 2
   curl -X POST "http://localhost:8001/search" \
        -H "Content-Type: application/json" \
        -d '{"query":"restaurant","user_id":"user2"}'
   ```

## 📊 Frontend Demo

Open `public/multi-tenant-example.html` in your browser to see an interactive demo of the multi-tenant functionality.

## 🔒 Security Considerations

### User ID Validation

- User IDs should be unique and consistent
- Consider using UUIDs or domain-based identifiers
- Avoid using sensitive information in user IDs

### Data Isolation

- Each user's documents are completely isolated
- Search results only include documents from the specified user
- No cross-user data leakage

### Authentication Integration

The multi-tenant system works with existing authentication:
- JWT tokens can include user information
- Public/private key authentication is supported
- Registered key authentication from upload portal works

## 🔄 Backward Compatibility

The multi-tenant feature is designed to be backward compatible:
- Existing implementations without userId continue to work
- All documents are accessible when no userId is specified
- No breaking changes to existing APIs

## 📈 Use Cases

### 1. Multiple Company Websites

```html
<!-- Company A -->
<script src="chatbot.js" data-user-id="company_a"></script>

<!-- Company B -->
<script src="chatbot.js" data-user-id="company_b"></script>
```

### 2. Different Departments

```html
<!-- Sales Department -->
<script src="chatbot.js" data-user-id="sales_dept"></script>

<!-- Support Department -->
<script src="chatbot.js" data-user-id="support_dept"></script>
```

### 3. Different Products

```html
<!-- Product A -->
<script src="chatbot.js" data-user-id="product_a"></script>

<!-- Product B -->
<script src="chatbot.js" data-user-id="product_b"></script>
```

### 4. Different Languages/Regions

```html
<!-- English Version -->
<script src="chatbot.js" data-user-id="en_us"></script>

<!-- Spanish Version -->
<script src="chatbot.js" data-user-id="es_mx"></script>
```

## 🛠️ Troubleshooting

### Common Issues

1. **No documents found for user**
   - Check if documents were added with the correct user_id
   - Verify the userId in the frontend matches the backend

2. **Documents mixing between users**
   - Ensure userId is being passed correctly in search requests
   - Check backend logs for user filtering

3. **Backward compatibility issues**
   - Old implementations without userId will see all documents
   - This is expected behavior for backward compatibility

### Debug Mode

Enable debug logging in the browser console:

```javascript
// Check userId extraction
console.log('Extracted userId:', userId);

// Check search requests
// Look for logs like: "Found X relevant documents for query: '...' (User: user123)"
```

## 📝 API Reference

### Frontend Functions

- `initRAGChatbot(config)` - Initialize chatbot with multi-tenant support
- `extractUserId(config)` - Extract userId from various sources

### Backend Endpoints

- `POST /search` - Search with user filtering
- `POST /add-document` - Add document with user association
- `GET /documents` - List documents with optional user filtering
- `GET /stats` - Get statistics with optional user filtering

## 🤝 Contributing

When contributing to the multi-tenant functionality:

1. Maintain backward compatibility
2. Test with multiple user IDs
3. Verify data isolation
4. Update documentation for new features

## 📄 License

This multi-tenant functionality is part of the RAG Chatbot project and follows the same license terms. 