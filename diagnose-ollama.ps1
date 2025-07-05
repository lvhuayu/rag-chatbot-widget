#!/usr/bin/env pwsh

Write-Host "🔍 Ollama Connection Diagnostic Tool" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

# Function to test Ollama connection
function Test-OllamaConnection {
    param(
        [string]$Url = "http://localhost:11434",
        [int]$Timeout = 10
    )
    
    try {
        Write-Host "Testing connection to $Url..." -ForegroundColor Yellow
        
        # Test basic connectivity
        $response = Invoke-RestMethod -Uri "$Url/api/tags" -Method Get -TimeoutSec $Timeout -ErrorAction Stop
        Write-Host "✅ Ollama is running and accessible" -ForegroundColor Green
        
        # Check available models
        if ($response.models) {
            Write-Host "📋 Available models:" -ForegroundColor Green
            foreach ($model in $response.models) {
                Write-Host "  - $($model.name) (Size: $($model.size))" -ForegroundColor White
            }
        } else {
            Write-Host "⚠️  No models found or models list is empty" -ForegroundColor Yellow
        }
        
        return $true
    }
    catch {
        Write-Host "❌ Connection failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Function to test model generation
function Test-ModelGeneration {
    param(
        [string]$Model = "mistral",
        [string]$Url = "http://localhost:11434"
    )
    
    try {
        Write-Host "Testing model generation with $Model..." -ForegroundColor Yellow
        
        $payload = @{
            model = $Model
            prompt = "Hello, this is a test. Please respond with 'Test successful'."
            stream = $false
        } | ConvertTo-Json
        
        $response = Invoke-RestMethod -Uri "$Url/api/generate" -Method Post -Body $payload -ContentType "application/json" -TimeoutSec 30 -ErrorAction Stop
        
        Write-Host "✅ Model generation successful" -ForegroundColor Green
        Write-Host "Response: $($response.response)" -ForegroundColor White
        
        return $true
    }
    catch {
        Write-Host "❌ Model generation failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Function to check Ollama process
function Get-OllamaProcess {
    Write-Host "Checking Ollama process..." -ForegroundColor Yellow
    
    $process = Get-Process -Name "ollama" -ErrorAction SilentlyContinue
    if ($process) {
        Write-Host "✅ Ollama process is running (PID: $($process.Id))" -ForegroundColor Green
        Write-Host "  Memory usage: $([math]::Round($process.WorkingSet64 / 1MB, 2)) MB" -ForegroundColor White
        Write-Host "  CPU time: $($process.TotalProcessorTime)" -ForegroundColor White
        return $process
    } else {
        Write-Host "❌ Ollama process not found" -ForegroundColor Red
        return $null
    }
}

# Function to check port availability
function Test-Port {
    param([int]$Port = 11434)
    
    try {
        $connection = New-Object System.Net.Sockets.TcpClient
        $connection.ConnectAsync("localhost", $Port).Wait(5000) | Out-Null
        
        if ($connection.Connected) {
            Write-Host "✅ Port $Port is open and accessible" -ForegroundColor Green
            $connection.Close()
            return $true
        } else {
            Write-Host "❌ Port $Port is not accessible" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "❌ Port $Port test failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Function to provide solutions
function Show-Solutions {
    Write-Host "`n💡 Solutions:" -ForegroundColor Cyan
    Write-Host "=============" -ForegroundColor Cyan
    
    Write-Host "1. Start Ollama:" -ForegroundColor Yellow
    Write-Host "   ollama serve" -ForegroundColor White
    
    Write-Host "`n2. Pull a model (if none available):" -ForegroundColor Yellow
    Write-Host "   ollama pull mistral" -ForegroundColor White
    
    Write-Host "`n3. Check Ollama logs:" -ForegroundColor Yellow
    Write-Host "   ollama logs" -ForegroundColor White
    
    Write-Host "`n4. Restart Ollama service:" -ForegroundColor Yellow
    Write-Host "   # Stop current process" -ForegroundColor Gray
    Write-Host "   taskkill /f /im ollama.exe" -ForegroundColor White
    Write-Host "   # Start again" -ForegroundColor Gray
    Write-Host "   ollama serve" -ForegroundColor White
    
    Write-Host "`n5. Increase timeout in your application:" -ForegroundColor Yellow
    Write-Host "   # In rag_server_simple.py, line 416:" -ForegroundColor Gray
    Write-Host "   ollama_response = requests.post(ollama_url, json=ollama_payload, timeout=60)" -ForegroundColor White
    
    Write-Host "`n6. Check system resources:" -ForegroundColor Yellow
    Write-Host "   # Ensure you have enough RAM and CPU for the model" -ForegroundColor Gray
    Write-Host "   Get-Process | Where-Object {$_.ProcessName -like '*ollama*'}" -ForegroundColor White
}

# Main diagnostic flow
Write-Host "`nStep 1: Checking Ollama process..." -ForegroundColor Magenta
$ollamaProcess = Get-OllamaProcess

Write-Host "`nStep 2: Testing port connectivity..." -ForegroundColor Magenta
$portOk = Test-Port 11434

Write-Host "`nStep 3: Testing Ollama API connection..." -ForegroundColor Magenta
$connectionOk = Test-OllamaConnection

if ($connectionOk) {
    Write-Host "`nStep 4: Testing model generation..." -ForegroundColor Magenta
    $generationOk = Test-ModelGeneration
}

Write-Host "`nStep 5: System information..." -ForegroundColor Magenta
Write-Host "OS: $($PSVersionTable.OS)" -ForegroundColor White
Write-Host "PowerShell: $($PSVersionTable.PSVersion)" -ForegroundColor White
Write-Host "Current time: $(Get-Date)" -ForegroundColor White

# Show solutions if there are issues
if (-not $ollamaProcess -or -not $portOk -or -not $connectionOk) {
    Show-Solutions
} else {
    Write-Host "`n🎉 All tests passed! Ollama should be working correctly." -ForegroundColor Green
    Write-Host "If you're still experiencing timeouts, try increasing the timeout value in your application." -ForegroundColor Yellow
}

Write-Host "`nDiagnostic complete." -ForegroundColor Cyan 