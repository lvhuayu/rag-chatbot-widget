# Start JSONL to Embeddings Import API Server
# This script starts the new API server for importing JSONL data to embeddings table

Write-Host "🚀 Starting JSONL to Embeddings Import API Server..." -ForegroundColor Green

# Check if we're in the right directory
if (-not (Test-Path "backend/import_jsonl_to_embeddings.py")) {
    Write-Host "❌ Error: import_jsonl_to_embeddings.py not found in backend directory" -ForegroundColor Red
    Write-Host "Please run this script from the project root directory" -ForegroundColor Yellow
    exit 1
}

# Check if virtual environment exists
if (-not (Test-Path "backend/venv")) {
    Write-Host "📦 Creating virtual environment..." -ForegroundColor Yellow
    Set-Location backend
    python -m venv venv
    Set-Location ..
}

# Activate virtual environment
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Yellow
Set-Location backend
.\venv\Scripts\Activate.ps1

# Install dependencies if needed
Write-Host "📚 Installing dependencies..." -ForegroundColor Yellow
pip install fastapi uvicorn sentence-transformers pydantic python-multipart

# Check if Prisma is set up
if (-not (Test-Path "rag_database.db")) {
    Write-Host "⚠️  Warning: rag_database.db not found. Make sure Prisma is properly set up." -ForegroundColor Yellow
    Write-Host "You may need to run: npx prisma db push" -ForegroundColor Yellow
}

# Start the API server
Write-Host "🌐 Starting API server on http://localhost:8001..." -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

try {
    python import_jsonl_to_embeddings.py
} catch {
    Write-Host "❌ Error starting server: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "1. Make sure all dependencies are installed" -ForegroundColor White
    Write-Host "2. Check if port 8001 is available" -ForegroundColor White
    Write-Host "3. Verify Prisma database is set up correctly" -ForegroundColor White
    Write-Host "4. Check the logs above for specific error messages" -ForegroundColor White
}

# Return to original directory
Set-Location .. 