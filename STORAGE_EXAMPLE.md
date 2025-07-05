# 📊 Storage Structure Example - Multi-Tenant RAG Chatbot

This document shows what the user IDs and related documents look like in the in-memory storage.

## 🏗️ Storage Architecture

The system uses **in-memory storage** with two main arrays:
- `documents[]` - Array of document objects
- `embeddings[]` - Array of vector embeddings (same index as documents)

## 📋 Document Structure

Each document in the `documents[]` array has this structure:

```python
{
    "id": "uuid-string",
    "url": "https://example.com/page",
    "title": "Document Title",
    "content": "Document content text...",
    "timestamp": "2025-01-27T10:30:00",
    "user_id": "company_abc_123"  # Multi-tenant identifier
}
```

## 🔍 Visual Storage Example

Here's what the actual storage looks like with multiple users:

### In-Memory Storage Arrays

```python
# documents[] array
documents = [
    # User: company_abc_123
    {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "url": "https://company-abc.com/about",
        "title": "About Company ABC",
        "content": "Company ABC is a software development company specializing in web applications...",
        "timestamp": "2025-01-27T10:30:00",
        "user_id": "company_abc_123"
    },
    {
        "id": "550e8400-e29b-41d4-a716-446655440002",
        "url": "https://company-abc.com/services",
        "title": "Our Services",
        "content": "We offer web development, mobile apps, and cloud solutions...",
        "timestamp": "2025-01-27T10:31:00",
        "user_id": "company_abc_123"
    },
    
    # User: restaurant_xyz
    {
        "id": "550e8400-e29b-41d4-a716-446655440003",
        "url": "https://restaurant-xyz.com/menu",
        "title": "Restaurant XYZ Menu",
        "content": "We serve Italian cuisine including pasta carbonara, risotto, and tiramisu...",
        "timestamp": "2025-01-27T10:32:00",
        "user_id": "restaurant_xyz"
    },
    {
        "id": "550e8400-e29b-41d4-a716-446655440004",
        "url": "https://restaurant-xyz.com/location",
        "title": "Our Location",
        "content": "Located in downtown area, we offer both indoor and outdoor seating...",
        "timestamp": "2025-01-27T10:33:00",
        "user_id": "restaurant_xyz"
    },
    
    # User: fitness_center_456
    {
        "id": "550e8400-e29b-41d4-a716-446655440005",
        "url": "https://fitness-center-456.com/facilities",
        "title": "Fitness Center Facilities",
        "content": "We are a premium fitness center with state-of-the-art equipment...",
        "timestamp": "2025-01-27T10:34:00",
        "user_id": "fitness_center_456"
    },
    {
        "id": "550e8400-e29b-41d4-a716-446655440006",
        "url": "https://fitness-center-456.com/classes",
        "title": "Group Classes",
        "content": "Our services include yoga classes, strength training, cardio equipment...",
        "timestamp": "2025-01-27T10:35:00",
        "user_id": "fitness_center_456"
    }
]

# embeddings[] array (simplified - actual vectors are 384-dimensional)
embeddings = [
    [0.123, 0.456, 0.789, ...],  # Vector for document 0 (company_abc_123)
    [0.234, 0.567, 0.890, ...],  # Vector for document 1 (company_abc_123)
    [0.345, 0.678, 0.901, ...],  # Vector for document 2 (restaurant_xyz)
    [0.456, 0.789, 0.012, ...],  # Vector for document 3 (restaurant_xyz)
    [0.567, 0.890, 0.123, ...],  # Vector for document 4 (fitness_center_456)
    [0.678, 0.901, 0.234, ...]   # Vector for document 5 (fitness_center_456)
]
```

## 🔍 Search Process Example

When a user searches, here's what happens:

### 1. User Search Request
```json
{
    "query": "What services do you offer?",
    "top_k": 3,
    "threshold": 0.7,
    "user_id": "company_abc_123"
}
```

### 2. Document Filtering
```python
# Filter documents for specific user
user_documents = []
user_embeddings = []

for i, doc in enumerate(documents):
    if doc.get("user_id") == "company_abc_123":
        user_documents.append(doc)        # Only company_abc_123 docs
        user_embeddings.append(embeddings[i])  # Corresponding vectors

# Result: Only 2 documents for company_abc_123
user_documents = [
    {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "title": "About Company ABC",
        "content": "Company ABC is a software development company...",
        "user_id": "company_abc_123"
    },
    {
        "id": "550e8400-e29b-41d4-a716-446655440002", 
        "title": "Our Services",
        "content": "We offer web development, mobile apps, and cloud solutions...",
        "user_id": "company_abc_123"
    }
]
```

### 3. Vector Search
```python
# Only search within user's documents
query_embedding = embedding_model.encode("What services do you offer?")
similarities = cosine_similarity(query_embedding, user_embeddings)

# Results only include company_abc_123 documents
# No access to restaurant_xyz or fitness_center_456 data
```

## 📊 User ID Examples

### Common User ID Patterns

```python
# Company-based IDs
"company_abc_123"
"enterprise_xyz"
"startup_tech_456"

# Domain-based IDs  
"example.com"
"mywebsite.org"
"business.net"

# UUID-based IDs
"550e8400-e29b-41d4-a716-446655440000"
"a1b2c3d4-e5f6-7890-abcd-ef1234567890"

# Department-based IDs
"sales_dept"
"support_team"
"marketing_group"

# Product-based IDs
"product_a"
"service_b"
"solution_c"

# Language/Region-based IDs
"en_us"
"es_mx"
"fr_ca"
```

## 🔧 API Examples

### Adding Documents for Different Users

```bash
# Add document for company_abc_123
curl -X POST "http://localhost:8001/add-document" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://company-abc.com/about",
    "title": "About Company ABC", 
    "content": "Company ABC is a software development company...",
    "user_id": "company_abc_123"
  }'

# Add document for restaurant_xyz
curl -X POST "http://localhost:8001/add-document" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://restaurant-xyz.com/menu",
    "title": "Restaurant Menu",
    "content": "We serve Italian cuisine...",
    "user_id": "restaurant_xyz"
  }'
```

### Searching User-Specific Documents

```bash
# Search for company_abc_123
curl -X POST "http://localhost:8001/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "software development",
    "user_id": "company_abc_123"
  }'
# Returns: Only company_abc_123 documents

# Search for restaurant_xyz  
curl -X POST "http://localhost:8001/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Italian food",
    "user_id": "restaurant_xyz"
  }'
# Returns: Only restaurant_xyz documents
```

### Getting User-Specific Statistics

```bash
# Stats for company_abc_123
curl "http://localhost:8001/stats?user_id=company_abc_123"
# Returns: {"document_count": 2, "user_id": "company_abc_123", ...}

# Stats for restaurant_xyz
curl "http://localhost:8001/stats?user_id=restaurant_xyz"  
# Returns: {"document_count": 2, "user_id": "restaurant_xyz", ...}

# Overall stats
curl "http://localhost:8001/stats"
# Returns: {"document_count": 6, "user_id": "all_users", ...}
```

## 🔒 Data Isolation Guarantee

### What Each User Sees

```python
# User: company_abc_123
GET /documents?user_id=company_abc_123
# Returns: Only 2 documents about software development

# User: restaurant_xyz  
GET /documents?user_id=restaurant_xyz
# Returns: Only 2 documents about Italian restaurant

# User: fitness_center_456
GET /documents?user_id=fitness_center_456  
# Returns: Only 2 documents about fitness facilities

# No user_id specified (backward compatibility)
GET /documents
# Returns: All 6 documents (for admin/debug purposes)
```

## 📈 Storage Statistics

### Current Storage Layout
```
Total Documents: 6
Total Users: 3

User Breakdown:
├── company_abc_123: 2 documents
├── restaurant_xyz: 2 documents  
└── fitness_center_456: 2 documents

Vector Dimensions: 384 (all-MiniLM-L6-v2)
Storage Type: In-memory arrays
Index Alignment: documents[i] ↔ embeddings[i]
```

## 🚨 Important Notes

1. **In-Memory Storage**: Data is lost when server restarts
2. **Index Alignment**: `documents[i]` corresponds to `embeddings[i]`
3. **User Isolation**: Complete data separation by `user_id`
4. **Backward Compatibility**: No `user_id` = access to all documents
5. **Vector Dimensions**: 384-dimensional embeddings for each document

This storage structure ensures complete data isolation between different users while maintaining efficient vector search capabilities. 