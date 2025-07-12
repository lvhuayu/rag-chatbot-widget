# Demo Integration Flow: Upload Portal -> RAG Backend -> Widget
# This script demonstrates the complete integration with real examples

Write-Host "🎯 RAG Integration Demo" -ForegroundColor Cyan
Write-Host "=====================" -ForegroundColor Cyan

# Configuration
$UPLOAD_PORTAL_URL = "http://localhost:5000"
$RAG_BACKEND_URL = "http://localhost:8001"
$WIDGET_URL = "http://localhost:3000"

Write-Host "`n📋 Integration Overview:" -ForegroundColor Yellow
Write-Host "1. Upload Portal (Port 5000) - User authentication and document upload" -ForegroundColor White
Write-Host "2. RAG Backend (Port 8001) - Document processing and search" -ForegroundColor White
Write-Host "3. RAG Widget (Port 3000) - Chat interface for document queries" -ForegroundColor White
Write-Host "4. Unified Prisma Database - Shared storage for all components" -ForegroundColor White

Write-Host "`n🔄 Integration Flow:" -ForegroundColor Yellow
Write-Host "┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐" -ForegroundColor Gray
Write-Host "│   Upload Portal │───▶│   RAG Backend   │───▶│  RAG Widget     │" -ForegroundColor Gray
Write-Host "│   (Port 5000)   │    │   (Port 8001)   │    │  (Port 3000)    │" -ForegroundColor Gray
Write-Host "└─────────────────┘    └─────────────────┘    └─────────────────┘" -ForegroundColor Gray
Write-Host "         │                       │                       │" -ForegroundColor Gray
Write-Host "         ▼                       ▼                       ▼" -ForegroundColor Gray
Write-Host "┌─────────────────────────────────────────────────────────────────┐" -ForegroundColor Gray
Write-Host "│                    Unified Prisma Database                      │" -ForegroundColor Gray
Write-Host "└─────────────────────────────────────────────────────────────────┘" -ForegroundColor Gray

Write-Host "`n📝 Step-by-Step Process:" -ForegroundColor Yellow
Write-Host "1. User registers/logs in to Upload Portal" -ForegroundColor White
Write-Host "2. User uploads documents (PDF, TXT, DOCX)" -ForegroundColor White
Write-Host "3. Upload Portal extracts text and sends to RAG Backend" -ForegroundColor White
Write-Host "4. RAG Backend creates embeddings and stores in database" -ForegroundColor White
Write-Host "5. User can immediately search documents via RAG Widget" -ForegroundColor White

Write-Host "`n🔧 Technical Implementation:" -ForegroundColor Yellow
Write-Host "• Upload Portal: React + Express + Prisma" -ForegroundColor White
Write-Host "• RAG Backend: FastAPI + Sentence Transformers + Prisma" -ForegroundColor White
Write-Host "• RAG Widget: HTML/JS + Direct API calls" -ForegroundColor White
Write-Host "• Database: SQLite with Prisma ORM" -ForegroundColor White

Write-Host "`n🚀 How to Use:" -ForegroundColor Yellow
Write-Host "1. Start the services:" -ForegroundColor White
Write-Host "   • Upload Portal: cd upload_portal/rag-document-uploader/server && npm start" -ForegroundColor Gray
Write-Host "   • RAG Backend: .\start-prisma-server.ps1" -ForegroundColor Gray
Write-Host "   • RAG Widget: Open public/chat-ui.html in browser" -ForegroundColor Gray

Write-Host "`n2. Upload documents:" -ForegroundColor White
Write-Host "   • Go to http://localhost:5000" -ForegroundColor Gray
Write-Host "   • Register/login and upload your documents" -ForegroundColor Gray
Write-Host "   • Documents are automatically indexed and searchable" -ForegroundColor Gray

Write-Host "`n3. Use the RAG widget:" -ForegroundColor White
Write-Host "   • Open the chat widget on any page" -ForegroundColor Gray
Write-Host "   • Ask questions about your uploaded documents" -ForegroundColor Gray
Write-Host "   • Get AI-powered answers based on your content" -ForegroundColor Gray

Write-Host "`n💡 Key Features:" -ForegroundColor Yellow
Write-Host "✅ Multi-tenant: Each user sees only their own documents" -ForegroundColor Green
Write-Host "✅ Real-time: Documents available immediately after upload" -ForegroundColor Green
Write-Host "✅ Unified: Single database shared across all components" -ForegroundColor Green
Write-Host "✅ Secure: JWT authentication and user isolation" -ForegroundColor Green
Write-Host "✅ Scalable: Prisma ORM with proper indexing" -ForegroundColor Green

Write-Host "`n🔍 API Endpoints:" -ForegroundColor Yellow
Write-Host "Upload Portal:" -ForegroundColor White
Write-Host "  POST /auth/register - User registration" -ForegroundColor Gray
Write-Host "  POST /auth/login - User authentication" -ForegroundColor Gray
Write-Host "  POST /upload - Document upload and indexing" -ForegroundColor Gray
Write-Host "  GET  /upload/documents - Get user's documents" -ForegroundColor Gray

Write-Host "`nRAG Backend:" -ForegroundColor White
Write-Host "  POST /add-document - Add document to RAG system" -ForegroundColor Gray
Write-Host "  POST /search - Search documents with user context" -ForegroundColor Gray
Write-Host "  GET  /documents - Get documents for user" -ForegroundColor Gray
Write-Host "  GET  /health - Service health check" -ForegroundColor Gray

Write-Host "`n🎯 Ready to test? Run: .\test-end-to-end-integration.ps1" -ForegroundColor Cyan 