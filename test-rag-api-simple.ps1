# Simple RAG API Test - Direct API calls to isolate the issue
Write-Host "🔍 Testing RAG Backend API Directly" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan

$RAG_BACKEND_URL = "http://localhost:8001"

# Test 1: Health check
Write-Host "`n📊 Test 1: Health Check" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$RAG_BACKEND_URL/health" -Method GET -TimeoutSec 10
    Write-Host "✅ Health check passed: $($response | ConvertTo-Json)" -ForegroundColor Green
} catch {
    Write-Host "❌ Health check failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test 2: Direct document add
Write-Host "`n📄 Test 2: Direct Document Add" -ForegroundColor Yellow
$testDocument = @{
    url = "test-document.txt"
    title = "Test Document"
    content = "This is a test document for debugging the RAG backend."
    user_id = "testuser"
    timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss")
} | ConvertTo-Json

try {
    Write-Host "Sending document to RAG backend..." -ForegroundColor Gray
    $response = Invoke-RestMethod -Uri "$RAG_BACKEND_URL/add-document" -Method POST -Body $testDocument -ContentType "application/json" -TimeoutSec 30
    Write-Host "✅ Document add successful: $($response | ConvertTo-Json)" -ForegroundColor Green
} catch {
    Write-Host "❌ Document add failed:" -ForegroundColor Red
    Write-Host "   Status Code: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
    Write-Host "   Error Message: $($_.Exception.Message)" -ForegroundColor Red
    
    # Try to get the response body for more details
    try {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "   Response Body: $responseBody" -ForegroundColor Red
    } catch {
        Write-Host "   Could not read response body" -ForegroundColor Red
    }
}

# Test 3: Search test
Write-Host "`n🔍 Test 3: Search Test" -ForegroundColor Yellow
$searchRequest = @{
    query = "test document"
    user_id = "testuser"
    top_k = 5
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$RAG_BACKEND_URL/search" -Method POST -Body $searchRequest -ContentType "application/json" -TimeoutSec 30
    Write-Host "✅ Search successful: Found $($response.documents.Count) documents" -ForegroundColor Green
} catch {
    Write-Host "❌ Search failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n🎯 Test completed!" -ForegroundColor Cyan 