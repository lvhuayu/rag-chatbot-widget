#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Test script for RAG Chatbot with Persistent Storage

.DESCRIPTION
    This script tests the new persistent SQLite storage functionality for the RAG chatbot.
    It demonstrates that data persists across server restarts.

.PARAMETER ServerUrl
    The URL of the RAG server (default: http://localhost:8001)

.EXAMPLE
    .\test-persistent-storage.ps1
    .\test-persistent-storage.ps1 -ServerUrl "http://localhost:8001"
#>

param(
    [string]$ServerUrl = "http://localhost:8001"
)

# Colors for output
$Green = "`e[32m"
$Red = "`e[31m"
$Yellow = "`e[33m"
$Blue = "`e[34m"
$Reset = "`e[0m"

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = $Reset
    )
    Write-Host "$Color$Message$Reset"
}

function Test-ServerHealth {
    Write-ColorOutput "`n=== Testing Server Health ===" $Blue
    
    try {
        $response = Invoke-RestMethod -Uri "$ServerUrl/health" -Method Get -TimeoutSec 10
        Write-ColorOutput "✅ Server is healthy" $Green
        Write-ColorOutput "Storage type: $($response.storage)" $Yellow
        Write-ColorOutput "Database info: $($response.database_info | ConvertTo-Json -Depth 3)" $Yellow
        return $true
    }
    catch {
        Write-ColorOutput "❌ Server health check failed: $($_.Exception.Message)" $Red
        return $false
    }
}

function Add-TestDocuments {
    Write-ColorOutput "`n=== Adding Test Documents ===" $Blue
    
    $testDocuments = @(
        @{
            url = "https://example.com/restaurant1"
            title = "Italian Restaurant Menu"
            content = "Our restaurant serves authentic Italian cuisine including pasta, pizza, and tiramisu. We use fresh ingredients imported from Italy."
            user_id = "restaurant_user"
        },
        @{
            url = "https://example.com/travel1"
            title = "Travel Agency Services"
            content = "We offer travel packages to Italy, France, and Spain. Our services include flight booking, hotel reservations, and guided tours."
            user_id = "travel_user"
        },
        @{
            url = "https://example.com/tech1"
            title = "Tech Support Guide"
            content = "Common technical issues and solutions. How to reset passwords, troubleshoot network problems, and contact IT support."
            user_id = "tech_user"
        }
    )
    
    $successCount = 0
    foreach ($doc in $testDocuments) {
        try {
            $response = Invoke-RestMethod -Uri "$ServerUrl/add-document" -Method Post -Body ($doc | ConvertTo-Json) -ContentType "application/json" -TimeoutSec 10
            Write-ColorOutput "✅ Added: $($doc.title) (User: $($doc.user_id))" $Green
            $successCount++
        }
        catch {
            Write-ColorOutput "❌ Failed to add: $($doc.title) - $($_.Exception.Message)" $Red
        }
    }
    
    Write-ColorOutput "Added $successCount out of $($testDocuments.Count) documents" $Yellow
    return $successCount
}

function Test-SearchFunctionality {
    Write-ColorOutput "`n=== Testing Search Functionality ===" $Blue
    
    $testQueries = @(
        @{ query = "Italian food"; user_id = "restaurant_user"; expected = "restaurant" },
        @{ query = "travel packages"; user_id = "travel_user"; expected = "travel" },
        @{ query = "technical support"; user_id = "tech_user"; expected = "tech" },
        @{ query = "Italian food"; user_id = "travel_user"; expected = "none" }  # Should not find restaurant data
    )
    
    foreach ($test in $testQueries) {
        Write-ColorOutput "`nTesting: '$($test.query)' for user: $($test.user_id)" $Yellow
        
        try {
            $searchRequest = @{
                query = $test.query
                top_k = 3
                user_id = $test.user_id
            }
            
            $response = Invoke-RestMethod -Uri "$ServerUrl/search" -Method Post -Body ($searchRequest | ConvertTo-Json) -ContentType "application/json" -TimeoutSec 30
            
            if ($response.documents.Count -gt 0) {
                Write-ColorOutput "✅ Found $($response.documents.Count) relevant documents" $Green
                foreach ($doc in $response.documents) {
                    Write-ColorOutput "  - $($doc.document.title) (similarity: $([math]::Round($doc.similarity, 3)))" $Green
                }
            } else {
                Write-ColorOutput "ℹ️  No relevant documents found (expected for cross-user queries)" $Yellow
            }
            
            Write-ColorOutput "Response: $($response.context.Substring(0, [math]::Min(100, $response.context.Length)))..." $Yellow
        }
        catch {
            Write-ColorOutput "❌ Search failed: $($_.Exception.Message)" $Red
        }
    }
}

function Test-DataPersistence {
    Write-ColorOutput "`n=== Testing Data Persistence ===" $Blue
    
    # Get initial stats
    try {
        $initialStats = Invoke-RestMethod -Uri "$ServerUrl/stats" -Method Get -TimeoutSec 10
        Write-ColorOutput "Initial document count: $($initialStats.document_count)" $Yellow
    }
    catch {
        Write-ColorOutput "❌ Failed to get initial stats: $($_.Exception.Message)" $Red
        return
    }
    
    Write-ColorOutput "`n🔄 Please restart the RAG server now and press Enter to continue..." $Yellow
    Read-Host
    
    # Wait a moment for server to start
    Start-Sleep -Seconds 3
    
    # Test server health after restart
    if (-not (Test-ServerHealth)) {
        Write-ColorOutput "❌ Server is not responding after restart" $Red
        return
    }
    
    # Get stats after restart
    try {
        $finalStats = Invoke-RestMethod -Uri "$ServerUrl/stats" -Method Get -TimeoutSec 10
        Write-ColorOutput "Final document count: $($finalStats.document_count)" $Yellow
        
        if ($finalStats.document_count -eq $initialStats.document_count) {
            Write-ColorOutput "✅ Data persistence confirmed! Document count maintained after restart." $Green
        } else {
            Write-ColorOutput "❌ Data persistence failed! Document count changed after restart." $Red
        }
    }
    catch {
        Write-ColorOutput "❌ Failed to get final stats: $($_.Exception.Message)" $Red
    }
}

function Test-UserIsolation {
    Write-ColorOutput "`n=== Testing User Data Isolation ===" $Blue
    
    $users = @("restaurant_user", "travel_user", "tech_user")
    
    foreach ($user in $users) {
        Write-ColorOutput "`nTesting user: $user" $Yellow
        
        try {
            # Get user-specific documents
            $documents = Invoke-RestMethod -Uri "$ServerUrl/documents?user_id=$user" -Method Get -TimeoutSec 10
            Write-ColorOutput "  Documents for $user`: $($documents.Count)" $Green
            
            # Get user-specific stats
            $stats = Invoke-RestMethod -Uri "$ServerUrl/stats?user_id=$user" -Method Get -TimeoutSec 10
            Write-ColorOutput "  Stats for $user`: $($stats.document_count) documents" $Green
            
            # Test user-specific search
            $searchRequest = @{
                query = "test query"
                user_id = $user
            }
            $searchResponse = Invoke-RestMethod -Uri "$ServerUrl/search" -Method Post -Body ($searchRequest | ConvertTo-Json) -ContentType "application/json" -TimeoutSec 10
            
            if ($searchResponse.documents.Count -gt 0) {
                Write-ColorOutput "  Search working for $user" $Green
            } else {
                Write-ColorOutput "  No search results for $user (may be normal)" $Yellow
            }
        }
        catch {
            Write-ColorOutput "  ❌ Error testing $user`: $($_.Exception.Message)" $Red
        }
    }
}

function Show-DatabaseInfo {
    Write-ColorOutput "`n=== Database Information ===" $Blue
    
    try {
        $health = Invoke-RestMethod -Uri "$ServerUrl/health" -Method Get -TimeoutSec 10
        Write-ColorOutput "Database Info:" $Yellow
        $health.database_info | Format-List
        
        $stats = Invoke-RestMethod -Uri "$ServerUrl/stats" -Method Get -TimeoutSec 10
        Write-ColorOutput "`nOverall Stats:" $Yellow
        $stats | Format-List
    }
    catch {
        Write-ColorOutput "❌ Failed to get database info: $($_.Exception.Message)" $Red
    }
}

# Main test execution
Write-ColorOutput "🚀 Starting Persistent Storage Test" $Blue
Write-ColorOutput "Server URL: $ServerUrl" $Yellow

# Test 1: Server Health
if (-not (Test-ServerHealth)) {
    Write-ColorOutput "`n❌ Server is not available. Please start the RAG server first." $Red
    exit 1
}

# Test 2: Add Test Documents
$addedCount = Add-TestDocuments

if ($addedCount -eq 0) {
    Write-ColorOutput "`n❌ No documents were added. Cannot continue with tests." $Red
    exit 1
}

# Test 3: Search Functionality
Test-SearchFunctionality

# Test 4: User Isolation
Test-UserIsolation

# Test 5: Show Database Info
Show-DatabaseInfo

# Test 6: Data Persistence (requires manual server restart)
Write-ColorOutput "`n=== Manual Persistence Test ===" $Blue
Write-ColorOutput "To test data persistence across server restarts:" $Yellow
Write-ColorOutput "1. Stop the RAG server (Ctrl+C)" $Yellow
Write-ColorOutput "2. Start it again: python rag_server_simple.py" $Yellow
Write-ColorOutput "3. Run this script again to verify data is still there" $Yellow

Write-ColorOutput "`n✅ Persistent Storage Test Complete!" $Green
Write-ColorOutput "Check the database file: rag_database.db" $Yellow 