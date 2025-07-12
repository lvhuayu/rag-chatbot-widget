# Simple Integration Test - Skip registration, test login and upload
Write-Host "🧪 Simple Integration Test" -ForegroundColor Cyan
Write-Host "=========================" -ForegroundColor Cyan

# Configuration
$UPLOAD_PORTAL_URL = "http://localhost:5000"
$RAG_BACKEND_URL = "http://localhost:8001"
$TEST_USER_USERNAME = "testuser"
$TEST_USER_PASSWORD = "testpass123"

# Colors for output
$Green = "Green"
$Red = "Red"
$Yellow = "Yellow"
$Cyan = "Cyan"

function Write-Status {
    param($Message, $Status, $Color = $Green)
    $icon = if ($Status -eq "PASS") { "✅" } elseif ($Status -eq "FAIL") { "❌" } else { "⚠️" }
    Write-Host "$icon $Message" -ForegroundColor $Color
}

function Test-Health {
    param($Url, $Service)
    try {
        $response = Invoke-RestMethod -Uri "$Url/health" -Method GET -TimeoutSec 10
        Write-Status "$Service is healthy" "PASS"
        return $true
    } catch {
        Write-Status "$Service health check failed: $($_.Exception.Message)" "FAIL" $Red
        return $false
    }
}

function Test-Login {
    try {
        $loginData = @{
            username = $TEST_USER_USERNAME
            password = $TEST_USER_PASSWORD
        } | ConvertTo-Json

        $response = Invoke-RestMethod -Uri "$UPLOAD_PORTAL_URL/api/auth/login" -Method POST -Body $loginData -ContentType "application/json" -TimeoutSec 10
        
        if ($response.token) {
            Write-Status "Login successful" "PASS"
            return $response.token
        } else {
            Write-Status "Login failed: No token received" "FAIL" $Red
            return $null
        }
    } catch {
        Write-Status "Login failed: $($_.Exception.Message)" "FAIL" $Red
        return $null
    }
}

function Test-DocumentUpload {
    param($Token)
    try {
        # Create a temporary test file
        $tempFile = [System.IO.Path]::GetTempFileName() + ".txt"
        "This is a test document about artificial intelligence and machine learning." | Out-File -FilePath $tempFile -Encoding UTF8

        # Prepare form data
        $boundary = [System.Guid]::NewGuid().ToString()
        $LF = "`r`n"
        $bodyLines = @(
            "--$boundary",
            "Content-Disposition: form-data; name=`"files`"; filename=`"test-document.txt`"",
            "Content-Type: text/plain",
            "",
            [System.IO.File]::ReadAllText($tempFile),
            "--$boundary",
            "Content-Disposition: form-data; name=`"descriptions`"",
            "",
            "Test document for integration testing",
            "--$boundary--"
        )
        $body = $bodyLines -join $LF

        $headers = @{
            "Authorization" = "Bearer $Token"
            "Content-Type" = "multipart/form-data; boundary=$boundary"
        }

        $response = Invoke-RestMethod -Uri "$UPLOAD_PORTAL_URL/api/upload" -Method POST -Body $body -Headers $headers -TimeoutSec 30
        
        # Clean up temp file
        if (Test-Path $tempFile) { Remove-Item $tempFile }

        if ($response.successful) {
            Write-Status "Document upload successful" "PASS"
            return $response.successful[0].ragDocId
        } else {
            Write-Status "Document upload failed: $($response.message)" "FAIL" $Red
            return $null
        }
    } catch {
        # Clean up temp file
        if (Test-Path $tempFile) { Remove-Item $tempFile }
        Write-Status "Document upload failed: $($_.Exception.Message)" "FAIL" $Red
        return $null
    }
}

function Test-RAGSearch {
    param($UserId)
    try {
        $searchData = @{
            query = "artificial intelligence machine learning"
            user_id = $UserId
            top_k = 5
        } | ConvertTo-Json

        $response = Invoke-RestMethod -Uri "$RAG_BACKEND_URL/search" -Method POST -Body $searchData -ContentType "application/json" -TimeoutSec 30
        
        if ($response.documents -and $response.documents.Count -gt 0) {
            Write-Status "RAG search successful - found $($response.documents.Count) documents" "PASS"
            return $true
        } else {
            Write-Status "RAG search returned no documents" "FAIL" $Red
            return $false
        }
    } catch {
        Write-Status "RAG search failed: $($_.Exception.Message)" "FAIL" $Red
        return $false
    }
}

# Main test execution
Write-Host "`n🔍 Step 1: Checking service health..." -ForegroundColor $Cyan
$ragHealthy = Test-Health $RAG_BACKEND_URL "RAG Backend"
$uploadHealthy = Test-Health $UPLOAD_PORTAL_URL "Upload Portal"

if (-not $ragHealthy -or -not $uploadHealthy) {
    Write-Host "`n❌ Service health checks failed. Please ensure both services are running:" -ForegroundColor $Red
    Write-Host "   - RAG Backend: $RAG_BACKEND_URL" -ForegroundColor $Yellow
    Write-Host "   - Upload Portal: $UPLOAD_PORTAL_URL" -ForegroundColor $Yellow
    exit 1
}

Write-Host "`n👤 Step 2: User login..." -ForegroundColor $Cyan
$token = Test-Login
if (-not $token) {
    Write-Host "`n❌ User login failed. Cannot proceed with tests." -ForegroundColor $Red
    exit 1
}

# Extract user ID from JWT token (simple base64 decode)
$tokenParts = $token.Split('.')
if ($tokenParts.Length -eq 3) {
    $payload = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($tokenParts[1]))
    $userData = $payload | ConvertFrom-Json
    $userId = $userData.id
} else {
    Write-Host "`n❌ Invalid token format. Cannot extract user ID." -ForegroundColor $Red
    exit 1
}

Write-Host "`n📄 Step 3: Document upload and RAG indexing..." -ForegroundColor $Cyan
$ragDocId = Test-DocumentUpload $token
if (-not $ragDocId) {
    Write-Host "`n❌ Document upload failed. Cannot proceed with search tests." -ForegroundColor $Red
    exit 1
}

Write-Host "`n🔍 Step 4: RAG search test..." -ForegroundColor $Cyan
$searchSuccess = Test-RAGSearch $userId
if (-not $searchSuccess) {
    Write-Host "`n❌ RAG search failed. Integration may not be working correctly." -ForegroundColor $Red
    exit 1
}

Write-Host "`n🎉 Integration Test Summary:" -ForegroundColor $Cyan
Write-Host "=========================" -ForegroundColor $Cyan
Write-Status "Service Health" "PASS"
Write-Status "User Login" "PASS"
Write-Status "Document Upload & RAG Indexing" "PASS"
Write-Status "RAG Search" "PASS"

Write-Host "`n✅ End-to-end integration test completed successfully!" -ForegroundColor $Green
Write-Host "`n🎯 The integration is now working!" -ForegroundColor $Cyan
Write-Host "   - Upload Portal: http://localhost:5000" -ForegroundColor $Yellow
Write-Host "   - RAG Backend: http://localhost:8001" -ForegroundColor $Yellow
Write-Host "   - Documents uploaded through the portal are now searchable via the RAG widget" -ForegroundColor $Yellow 