#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Start the Prisma-based RAG Chatbot Backend
.DESCRIPTION
    Starts the new RAG server that uses Prisma for unified database management
#>

Write-Host "🚀 Starting RAG Chatbot Backend with Prisma Storage..." -ForegroundColor Cyan
Write-Host "📊 Database: Unified Prisma SQLite" -ForegroundColor Yellow
Write-Host "🧠 Model: all-MiniLM-L6-v2" -ForegroundColor Yellow
Write-Host "🔗 API: http://localhost:8001" -ForegroundColor Yellow
Write-Host "📚 Health: http://localhost:8001/health" -ForegroundColor Yellow
Write-Host "=" * 50 -ForegroundColor Gray

# Check if Ollama is running
Write-Host "🔍 Checking Ollama status..." -ForegroundColor Yellow
try {
    $ollamaResponse = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 5
    Write-Host "✅ Ollama is running with models: $($ollamaResponse.models.Count)" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Ollama is not running or not accessible" -ForegroundColor Yellow
    Write-Host "   You can start Ollama with: ollama serve" -ForegroundColor White
    Write-Host "   The RAG system will still work but LLM responses will be limited" -ForegroundColor White
}

Write-Host "`n🔄 Starting server..." -ForegroundColor Yellow

# Start the Prisma-based server
try {
    cd backend
    python rag_server_prisma.py
} catch {
    Write-Host "❌ Failed to start server: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "`n🔧 Troubleshooting:" -ForegroundColor Cyan
    Write-Host "   1. Make sure Python dependencies are installed: pip install -r requirements.txt" -ForegroundColor White
    Write-Host "   2. Check if port 8001 is available" -ForegroundColor White
    Write-Host "   3. Ensure Prisma client is generated: npx prisma generate" -ForegroundColor White
    Write-Host "   4. Verify database is set up: npx prisma db push" -ForegroundColor White
} 