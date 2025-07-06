# List Users PowerShell Script
# This script lists all registered users via the API endpoint

$baseUrl = "http://localhost:5000"

Write-Host "Listing registered users via API..." -ForegroundColor Green

try {
    # First, try to get users without authentication (admin endpoint)
    $response = Invoke-RestMethod -Uri "$baseUrl/api/auth/admin/users" -Method GET -ContentType "application/json"
    
    Write-Host "`nFound $($response.total) user(s):" -ForegroundColor Yellow
    
    foreach ($user in $response.users) {
        Write-Host "`nUsername: $($user.username)" -ForegroundColor Cyan
        Write-Host "  ID: $($user.id)" -ForegroundColor Gray
        Write-Host "  Created: $($user.createdAt)" -ForegroundColor Gray
        Write-Host "  Documents: $($user.documentCount)" -ForegroundColor Gray
        Write-Host "  Public Key: $($user.publicKey.Substring(0, [Math]::Min(50, $user.publicKey.Length)))..." -ForegroundColor Gray
    }
    
} catch {
    Write-Host "Error accessing API: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "`nAlternative: Use the Node.js script directly:" -ForegroundColor Yellow
    Write-Host "node list-users.js" -ForegroundColor White
} 