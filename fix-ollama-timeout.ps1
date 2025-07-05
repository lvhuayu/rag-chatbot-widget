#!/usr/bin/env pwsh

Write-Host "🔧 Fixing Ollama Timeout Issue" -ForegroundColor Cyan
Write-Host "=============================" -ForegroundColor Cyan

$ragServerFile = "backend/rag_server_simple.py"

# Check if file exists
if (-not (Test-Path $ragServerFile)) {
    Write-Host "❌ RAG server file not found: $ragServerFile" -ForegroundColor Red
    exit 1
}

Write-Host "📁 Found RAG server file: $ragServerFile" -ForegroundColor Green

# Read the current content
$content = Get-Content $ragServerFile -Raw

# Check current timeout value
if ($content -match "timeout=(\d+)") {
    $currentTimeout = $matches[1]
    Write-Host "Current timeout: $currentTimeout seconds" -ForegroundColor Yellow
} else {
    Write-Host "⚠️  Could not find timeout setting" -ForegroundColor Yellow
}

# Increase timeout to 60 seconds
$newContent = $content -replace "timeout=30", "timeout=60"

# Check if the replacement was successful
if ($newContent -eq $content) {
    Write-Host "⚠️  No changes made - timeout=30 not found" -ForegroundColor Yellow
    
    # Try alternative pattern
    $newContent = $content -replace "timeout=(\d+)", "timeout=60"
    
    if ($newContent -eq $content) {
        Write-Host "❌ Could not find timeout setting to modify" -ForegroundColor Red
        Write-Host "Please manually edit line 416 in $ragServerFile" -ForegroundColor Yellow
        exit 1
    }
}

# Create backup
$backupFile = "$ragServerFile.backup.$(Get-Date -Format 'yyyyMMdd-HHmmss')"
Copy-Item $ragServerFile $backupFile
Write-Host "📋 Created backup: $backupFile" -ForegroundColor Green

# Write the modified content
Set-Content $ragServerFile $newContent -Encoding UTF8

Write-Host "✅ Successfully increased timeout to 60 seconds" -ForegroundColor Green

# Verify the change
$verifyContent = Get-Content $ragServerFile -Raw
if ($verifyContent -match "timeout=60") {
    Write-Host "✅ Verification: Timeout is now set to 60 seconds" -ForegroundColor Green
} else {
    Write-Host "⚠️  Verification failed - please check the file manually" -ForegroundColor Yellow
}

Write-Host "`n🔄 Next steps:" -ForegroundColor Cyan
Write-Host "1. Restart your RAG server" -ForegroundColor White
Write-Host "2. Run the diagnostic script: .\diagnose-ollama.ps1" -ForegroundColor White
Write-Host "3. Test your application again" -ForegroundColor White

Write-Host "`nFix complete!" -ForegroundColor Green 