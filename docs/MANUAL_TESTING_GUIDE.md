# Manual Testing Guide for RAG Uploader with Multi-Tenant Support

## 🚀 Quick Start Testing

### Prerequisites
1. **RAG Backend**: Running on port 8001 ✅ (Confirmed running)
2. **Uploader Backend**: Running on port 5000 ✅ (Confirmed running)
3. **Admin User**: Created with password "admin123" ✅

## 📋 Step-by-Step Testing

### 1. Test RAG Backend Health
```bash
# Test RAG backend directly
curl http://localhost:8001/health
```

**Expected Result**: JSON response with status, model, and database info

### 2. Test Uploader Backend Health
```bash
# Test uploader backend
curl http://localhost:5000/health
```

**Expected Result**: `{"status": "OK", "message": "Server is running"}`

### 3. Test RAG Availability from Uploader
```bash
# Test if uploader can reach RAG backend
curl http://localhost:5000/api/upload/rag-available
```

**Expected Result**: `{"available": true}`

### 4. Test Authentication
```bash
# Test admin login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

**Expected Result**: JSON with JWT token

### 5. Test RAG Endpoints (with authentication)
```bash
# Get auth token first
TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.token')

# Test RAG documents endpoint
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/api/upload/rag-documents

# Test RAG stats endpoint
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/api/upload/rag-stats

# Test RAG health endpoint
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/api/upload/rag-health
```

## 🌐 Web Interface Testing

### 1. Start the React Client
```bash
cd upload_portal/rag-document-uploader/client
npm install
npm start
```

### 2. Access the Application
- **Main URL**: http://localhost:3000
- **Login**: Use admin/admin123
- **RAG Management**: http://localhost:3000/rag

### 3. Test Upload Functionality
1. Navigate to Upload page
2. Select a text file (PDF, TXT, or DOCX)
3. Add a description
4. Upload the file
5. Check that it appears in both Documents and RAG Management pages

### 4. Test RAG Management Interface
1. Go to RAG Management page
2. Check the Documents tab for indexed documents
3. Use the Search tab to test semantic search
4. View Statistics tab for user and system stats

### 5. Test Multi-Tenant Isolation
1. Create a new user account
2. Login with the new user
3. Upload documents
4. Verify that users can only see their own documents
5. Test search isolation between users

## 🔧 API Testing with PowerShell

### Test Script 1: Basic Health Checks
```powershell
# Test RAG backend
Invoke-RestMethod -Uri "http://localhost:8001/health" -Method Get

# Test uploader backend
Invoke-RestMethod -Uri "http://localhost:5000/health" -Method Get

# Test RAG availability
Invoke-RestMethod -Uri "http://localhost:5000/api/upload/rag-available" -Method Get
```

### Test Script 2: Authentication and RAG Operations
```powershell
# Login and get token
$loginBody = @{
    username = "admin"
    password = "admin123"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:5000/api/auth/login" -Method Post -Body $loginBody -ContentType "application/json"
$token = $response.token

# Test RAG endpoints
$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

# Get RAG documents
Invoke-RestMethod -Uri "http://localhost:5000/api/upload/rag-documents" -Method Get -Headers $headers

# Get RAG stats
Invoke-RestMethod -Uri "http://localhost:5000/api/upload/rag-stats" -Method Get -Headers $headers

# Test search
$searchBody = @{
    query = "travel"
    top_k = 5
    threshold = 0.7
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:5000/api/upload/search" -Method Post -Body $searchBody -Headers $headers
```

## 🧪 Multi-Tenant Testing

### Test User Isolation
```powershell
# Test with different users
$users = @("user1", "user2", "admin")

foreach ($user in $users) {
    Write-Host "Testing user: $user"
    
    # Get user-specific stats
    $stats = Invoke-RestMethod -Uri "http://localhost:8001/stats?user_id=$user" -Method Get
    Write-Host "  Documents: $($stats.document_count)"
    
    # Get user-specific documents
    $docs = Invoke-RestMethod -Uri "http://localhost:8001/documents?user_id=$user" -Method Get
    Write-Host "  Document count: $($docs.Count)"
}
```

### Test Search Isolation
```powershell
# Test search for each user
$searchQuery = "travel"

foreach ($user in $users) {
    Write-Host "Searching for user: $user"
    
    $searchBody = @{
        query = $searchQuery
        user_id = $user
        top_k = 3
    } | ConvertTo-Json
    
    $results = Invoke-RestMethod -Uri "http://localhost:8001/search" -Method Post -Body $searchBody -ContentType "application/json"
    Write-Host "  Results: $($results.documents.Count)"
}
```

## 📊 Expected Results

### RAG Backend
- **Health**: Status "healthy", model "all-MiniLM-L6-v2"
- **Documents**: Total documents > 0, multiple users
- **Multi-tenant**: Enabled = true

### Uploader Backend
- **Health**: Status "OK"
- **RAG Available**: true
- **Authentication**: JWT token returned
- **RAG Endpoints**: All accessible with auth

### Multi-Tenant Features
- **User Isolation**: Users only see their own documents
- **Search Isolation**: Search results scoped to user
- **Statistics**: User-specific and system-wide stats

## 🚨 Troubleshooting

### Common Issues

1. **Authentication Fails**
   - Restart the uploader server after creating admin user
   - Check if admin user exists in database
   - Verify password is correct

2. **RAG Endpoints Not Accessible**
   - Ensure RAG backend is running on port 8001
   - Check network connectivity
   - Verify CORS settings

3. **File Upload Fails**
   - Check file size (max 10MB)
   - Verify file format (PDF, TXT, DOCX)
   - Check RAG backend is available

4. **Search Returns No Results**
   - Ensure documents are properly indexed
   - Check similarity threshold
   - Verify user has documents

### Debug Commands
```bash
# Check server logs
# RAG Backend: Look for Python console output
# Uploader Backend: Check Node.js console output

# Check database
sqlite3 upload_portal/rag-document-uploader/server/prisma/dev.db "SELECT * FROM User;"
sqlite3 backend/rag_database.db "SELECT COUNT(*) FROM documents;"
```

## ✅ Success Criteria

The system is working correctly if:

1. ✅ Both servers are running and healthy
2. ✅ Authentication works with admin user
3. ✅ RAG endpoints are accessible with auth
4. ✅ File uploads are indexed in RAG system
5. ✅ Multi-tenant isolation is maintained
6. ✅ Search functionality works per user
7. ✅ Web interface is accessible and functional

## 🎯 Next Steps After Testing

1. **Start React Client**: `cd upload_portal/rag-document-uploader/client && npm start`
2. **Access Web Interface**: http://localhost:3000
3. **Upload Test Documents**: Try different file types
4. **Test Search**: Use the RAG Management interface
5. **Verify Multi-Tenant**: Create multiple users and test isolation

---

**Note**: This manual testing guide provides comprehensive coverage of all RAG uploader features. Follow the steps in order to ensure all functionality is working correctly. 